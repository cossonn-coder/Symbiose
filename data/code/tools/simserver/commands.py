"""
SYMBIOSE — tools/simserver/commands.py
Handlers des commandes de protocole hors action : init, step_week, snapshot,
fields. Mixin de `SimServer` (Sprint refactor global, SS⑤) — la classe assemblée
hérite de ce mixin, donc `self.engine` / `self._world_static()` / `self._snapshot()`
sont fournis par les autres mixins. Aucune logique de simulation ici : on appelle
le moteur exactement comme main.py et tests/test_golden.py → golden intact.
"""
from __future__ import annotations
import contextlib
import sys
import time

from world import House
from sim.engine import Engine
from sim import vigueur as V      # état Vigueur joueur (ensure/spend/gain, D11)
from sim import journal as J      # ledger d'événements hors tick (voix narratives ②)
from sim.seeds import PlayerSeedBank, Seed  # banque-joueur (source de planter, remplie à la récolte)
# Type de base des champs écologiques (tranche 6·C) : le registre de la
# commande `fields` se DÉCOUVRE par introspection (tout attribut GridField
# d'EcoFields) — un champ ajouté au moteur apparaît tout seul dans l'overlay.
from fields.grids import GridField
# Registre des bancs d'essai (sprint dédié) : mondes paramétrés montés par
# `init config="<banc>"` pour forcer/observer un signe. Import au niveau module
# (paquet `bancs/` au sommet, peut tout importer) ; jamais monté pour smoke/full.
from bancs import BANCS, BANC_WEEK_DEPART, BANC_POST_INIT

from .version import ENGINE_VERSION
from .maitrise_pont import observer_apres_tick  # chaîne de maîtrise après tick (voix ①)
from . import perf   # capture des pires ticks + dump diagnostique (demande Nico 2026-07-05)

# Kit de démarrage déposé dans la banque-joueur, UNIQUEMENT en config "full" (le
# monde de jeu réel, celui du F5) : une graine de chaque, pour tester `planter`
# dès le lancement sans attendre une récolte d'automne. La config "smoke"
# (fixture de test déterministe) garde une banque VIDE → le flux empty→récolte
# reste exercé tel quel par tests/simserver/planter.py.
BANQUE_DEPART = ("tournesol", "tomate", "basilic")


def _vider_seedbank_ferale(sb) -> None:
    """Vide la banque de graines FÉRALE d'un `EcoField` (banc « monde propre », ①).
    Met à 0 les densités d'archétypes de chaque plot ET purge le pool espèce/
    génétique (D22) — plus aucune graine spontanée en réserve. On ne touche PAS
    aux `grains_en_attente` de la tuile (graines PLANTÉES, qui doivent lever).
    Hors tick (init) → aucun impact sur le golden (jamais appelé pour smoke/full)."""
    for r in range(sb.rows):
        for c in range(sb.cols):
            for a in sb.data[r][c]:
                sb.data[r][c][a] = 0.0
            sb.species[r][c].clear()


def _banque_initiale(config: str) -> PlayerSeedBank:
    bank = PlayerSeedBank()
    if config == "full":
        for sp in BANQUE_DEPART:
            bank.add(Seed(species=sp))   # gènes neutres (défaut)
    return bank


class CommandsMixin:
    """Les commandes de protocole hors `action` (cf. ActionsMixin)."""

    # ------------------------------------------------------------------ cmds

    def cmd_init(self, msg: dict) -> dict:
        seed = msg.get("seed", 0x5AB1057E)
        config = msg.get("config", "smoke")
        if not isinstance(seed, int):
            return {"ok": False, "error": f"seed doit être un entier (reçu {seed!r})"}
        banque = None   # renseignée par une fabrique de banc ; sinon helper plus bas
        if config == "smoke":
            # Réutilise la fabrique du golden smoke test (2 tuiles terre/argile +
            # maison centrée) — même monde, même déterminisme, zéro duplication.
            from tests.test_golden import build_world
            tiles, ecos = build_world()
            house = House()
        elif config == "full":
            # Monde COMPLET 20×20 m (tranche 2) : fabrique de main.py (8 tuiles
            # SECTORS plantées + maison) — import, pas de copie, même principe.
            from main import build_world_full
            tiles, ecos, _aux_tiles, house = build_world_full()
            # Démo/F5 (vue·rattrapage 02) : pré-vieillir le(s) fruitier(s) du
            # verger à leur âge de maturité (`maturity_years`) pour qu'ils NOUENT
            # des fruits dès le 1er début d'été (semaine 14) au lieu de l'an 6 —
            # on teste fruits + `manger` sans dérouler 5 ans en Turbo. PUR réglage
            # d'init côté serveur, config "full" SEULEMENT : la démo 500 ans de
            # main.py et le golden smoke (config "smoke") ne le voient jamais.
            # `age_years` n'altère que la courbe d'âge et la grille de nouaison ;
            # déterministe (constante), monde toujours 53 plantes (on vieillit, on
            # n'ajoute pas).
            for _t in tiles:
                for _p in _t.plants:
                    if getattr(_p.plant_class, "fruitier", False):
                        _p.age_years = float(_p.plant_class.maturity_years)
        elif config == "propre":
            # Banc « monde propre » (sprint équilibre invasion ①, D69) : MÊME monde
            # que "full" (mêmes 8 tuiles + maison + cultivées + pré-vieillissement
            # des fruitiers), MAIS sans pression férale — pour observer les cultivées
            # SEULES (F5) et isoler la perf à N maîtrisé (mesure onset/plateau ②).
            # Deux coupures, toutes deux HORS TICK (config d'init) :
            #   1. seedbank férale VIDÉE (densités d'archétypes + pool espèce à 0) →
            #      plus aucune graine spontanée en réserve ;
            #   2. flag `feral_off` posé dans game_state → `sim/succession.py` coupe
            #      la germination férale ET l'auto-enrichissement de la banque, tout
            #      en laissant lever les grains PLANTÉS.
            # "full"/"smoke"/bancs n'ont pas le flag (absent → False) → intacts.
            from main import build_world_full
            tiles, ecos, _aux_tiles, house = build_world_full()
            for _t in tiles:
                for _p in _t.plants:
                    if getattr(_p.plant_class, "fruitier", False):
                        _p.age_years = float(_p.plant_class.maturity_years)
            for _eco in ecos.values():
                _vider_seedbank_ferale(_eco.seed_bank)
        elif config in BANCS:
            # Bancs d'essai (sprint dédié) : mondes paramétrés qui FORCENT une
            # condition observable (sécheresse, chlorose, ombre dense…) pour le tri
            # diagnostique des signes (bug rendu C# vs artefact de carte, D47). La
            # fabrique renvoie le tuple standard (tiles, ecos, house, banque). Branché
            # APRÈS smoke/full → ces deux configs ne montent jamais un banc, golden
            # NEUTRE. Banque vide de la fabrique → repli sur la banque smoke (helper).
            tiles, ecos, house, banque = BANCS[config]()
        else:
            return {"ok": False,
                    "error": f"config inconnue : {config!r} "
                             f"('smoke', 'full', 'propre' ou un banc : {', '.join(sorted(BANCS))})"}
        # Semaine de départ : `week=1` par défaut (début printemps). Un banc peut
        # démarrer plus tard via `BANC_WEEK_DEPART` (retour F5 : `grimpantes` observe
        # des frileuses → départ mi-printemps). Override explicite `msg["week"]`
        # prioritaire (oracle/tests). smoke/full absents du registre → 1 (inchangé).
        start_week = msg.get("week", BANC_WEEK_DEPART.get(config, 1))
        game_state = {
            "tiles": tiles, "eco": ecos, "scores": {},
            "current_player": "joueur_1", "week": start_week, "log": [],
            "house": house, "seed": seed,
            # Banque-joueur (sprint planter·arroser) : source des graines de
            # `planter`. Le tick de récolte (engine.py, gardé par
            # `if player_seed_bank is not None`) y dépose les graines sélectionnées
            # (D17) au fil des automnes. Le golden écolo n'init jamais via ce
            # serveur → intact. Sérialisable JSON (futur save par profil).
            # Kit de démarrage en config "full" seulement (retour F5 Nico) : 1
            # graine de chaque espèce potagère emblématique pour tester `planter`
            # sans attendre un automne. "smoke" reste à banque vide (cf. helper).
            # Un banc peut fournir SA banque (fabrique) ; sinon repli sur le helper.
            "player_seed_bank": banque if banque is not None else _banque_initiale(config),
        }
        # Banc « monde propre » (①) : coupe la germination férale spontanée et
        # l'auto-enrichissement de la banque au tick (lu par sim/succession.py).
        # Clé posée UNIQUEMENT en config "propre" → absente ailleurs → False →
        # comportement inchangé pour smoke/full/bancs (golden intact).
        if config == "propre":
            game_state["feral_off"] = True
        self.engine = Engine(game_state)
        # Traqueur des pires ticks (demande Nico) : mémoire des K ticks les plus
        # longs + dump diagnostique sur disque au record. Neuf à chaque init.
        self._worst = perf.WorstTicks()
        # Brancher la Vigueur joueur (tranche 4) : l'OPT-IN se fait ICI, pas
        # dans le moteur. Dès que la clé `vigueur` existe, le tick existant
        # (engine.py, gardé par `if "vigueur" in game_state`) fait seul la
        # régen hebdo + le plein au passage de saison — rien d'autre à câbler.
        # Le golden écolo reste intact : il n'init jamais via ce serveur.
        V.ensure_player(game_state, game_state["current_player"])
        # Hook POST-INIT du banc (palette de gestes ⑤) : APRÈS l'opt-in Vigueur —
        # premier moment où l'état JOUEUR existe. Le banc « palette » y ouvre d'emblée
        # les gestes savants (bouturer/greffer) en forçant la maîtrise (la fabrique ne
        # renvoie que le monde, pas game_state). Banc sans hook → absent → sauté.
        # smoke/full ne sont pas des bancs → jamais de hook → golden intact.
        post = BANC_POST_INIT.get(config)
        if post is not None:
            post(game_state, game_state["current_player"])
        return {"ok": True, "engine_version": ENGINE_VERSION,
                "world": self._world_static()}

    def cmd_list_bancs(self, msg: dict) -> dict:
        """Liste des bancs d'essai montables par `init config="<nom>"` (sprint
        dédié). Source UNIQUE = le registre Python `BANCS` (principe #1 : Python
        source de vérité) — le sélecteur Godot la LIT au lieu de dupliquer les
        noms en C#, qui se périmeraient en silence à l'ajout d'un banc (un menu
        qui ment = le piège même que ce sprint élimine, cf. D47). Lecture du
        registre, pas du moteur → appelable AVANT `init` (pour peupler le menu)."""
        return {"ok": True, "bancs": sorted(BANCS)}

    def cmd_step_week(self, msg: dict) -> dict:
        if self.engine is None:
            return {"ok": False, "error": "step_week avant init"}
        # stdout est RÉSERVÉ au protocole : tick_semaine() ne print pas (vérifié
        # — seul run_years(verbose=True) le fait), mais on blinde contre une
        # évolution future du moteur en déviant tout print vers stderr.
        #
        # Banc d'observation perf (sprint « run éternel » ④) : on chronomètre
        # AUTOUR du tick, jamais DEDANS — le moteur n'est pas instrumenté, on
        # mesure ce que le serveur voit (règle d'or : on ajoute au SNAPSHOT, pas
        # au tick → golden intact par construction). `perf_counter` = horloge
        # monotone haute résolution, immune aux sauts d'heure système. La valeur
        # est simplement STOCKÉE sur self ; `_snapshot()` (serialize.py) la
        # relit pour composer le bloc `perf`. Aucune écriture moteur.
        _t0 = time.perf_counter()
        with contextlib.redirect_stdout(sys.stderr):
            self.engine.tick_semaine()
        self._last_ms_tick = (time.perf_counter() - _t0) * 1000.0
        # Capture des pires ticks (demande Nico) : soumet la durée mesurée ; le
        # traqueur ne construit un dump QUE si ce tick entre dans le top-K → coût
        # nul sur les ticks ordinaires. Hors tick moteur → golden intact.
        self._worst.consider(self._last_ms_tick, self.engine)
        # Voix narratives ② : consigner le `log` du tick au ledger AVANT de le
        # vider — hors tick, après la simulation, exactement comme un hook
        # `detecter()`/`tick_player_vigueur()`. L'OPT-IN se fait ici (le serveur
        # a un joueur) ; le golden tourne hors serveur → aucune clé `journal` →
        # no-op strict, golden intact (miroir du câblage Vigueur de cmd_init).
        gs = self.engine.game_state
        # `week` est DÉJÀ incrémenté par tick_semaine() (boucle.py:422) → la
        # semaine qu'on vient de simuler est `week - 1` ; le log consigné lui
        # appartient.
        J.consigner(gs, gs["current_player"], gs["log"], gs["week"] - 1)
        # Chaîne de MAÎTRISE (sprint UI voix ①) : hooks A (observer, découverte) +
        # B (detecter, crédit de palier) + révélation d'une page au palier 3. Lit
        # le MÊME `log` en lecture seule (ordre indifférent vs `consigner`), AVANT
        # de le vider. Opt-in joueur ici (même principe que `consigner`/Vigueur) →
        # golden intact (le moteur tourne sans serveur, ces hooks jamais appelés).
        observer_apres_tick(gs, gs["current_player"], gs["log"])
        gs["log"].clear()   # borne la mémoire (cf. golden)
        return {"ok": True, "snapshot": self._snapshot()}

    def cmd_snapshot(self, msg: dict) -> dict:
        if self.engine is None:
            return {"ok": False, "error": "snapshot avant init"}
        return {"ok": True, "snapshot": self._snapshot()}

    def cmd_perf_report(self, msg: dict) -> dict:
        """Rapport perf enrichi (demande Nico) : les K pires ticks accumulés (avec
        leur dump : répartition par tuile / par espèce / segments) + l'état
        courant. Lu par le presse-papier Godot (touche C). PURE lecture d'un état
        déjà traqué → golden NEUTRE."""
        if self.engine is None:
            return {"ok": False, "error": "perf_report avant init"}
        return {"ok": True,
                "worst": self._worst.dumps,
                "current": perf.diagnostic(
                    self.engine, getattr(self, "_last_ms_tick", None) or 0.0)}

    def cmd_fields(self, msg: dict) -> dict:
        """Mode debug champs écologiques (tranche 6·C, kickoff §8). Sans
        `field` : le REGISTRE, découvert par introspection (attributs GridField
        d'EcoFields, triés) + les 4 guildes de population (ordre trophique du
        dict). Avec `field` : les grilles par tuile, row-major. PURE lecture —
        l'overlay est un instrument, jamais une règle."""
        if self.engine is None:
            return {"ok": False, "error": "fields avant init"}
        gs = self.engine.game_state
        eco0 = next(iter(gs["eco"].values()))
        field = msg.get("field")
        if field is None:
            direct = sorted(k for k, v in vars(eco0).items()
                            if isinstance(v, GridField))
            # "vitalite" : synthèse DÉRIVÉE (méthode, pas un GridField) — ajoutée
            # explicitement au registre pour que l'overlay F6 la propose (§7③).
            return {"ok": True,
                    "fields": direct + list(eco0.populations.keys())
                              + ["vitalite"]}
        tiles_out = {}
        for tile in gs["tiles"]:
            eco = gs["eco"][tile.tile_id]
            if field == "vitalite":
                # Cas spécial : materialise la métrique dérivée en grille
                # row-major, à la demande. PURE lecture, aucun état stocké.
                tiles_out[tile.tile_id] = {
                    "rows": eco.rows, "cols": eco.cols,
                    "values": [round(eco.vitalite(r, c), 4)
                               for r in range(eco.rows)
                               for c in range(eco.cols)]}
                continue
            obj = vars(eco).get(field)
            if not isinstance(obj, GridField):
                obj = eco.populations.get(field) if isinstance(field, str) else None
            if not isinstance(obj, GridField):
                return {"ok": False, "error": f"champ inconnu : {field!r}"}
            # round(4) : précision d'instrument, et déterministe (cf. sprites).
            tiles_out[tile.tile_id] = {
                "rows": obj.rows, "cols": obj.cols,
                "values": [round(v, 4) for row in obj.data for v in row]}
        return {"ok": True, "field": field, "tiles": tiles_out}
