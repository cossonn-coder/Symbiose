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
from sim import maitrise as M     # amorçage encyclopédie de démarrage (option d'init T2)
from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE  # clés d'espèces (encyclo fournie)
from sim import journal as J      # ledger d'événements hors tick (voix narratives ②)
from sim.seeds import PlayerSeedBank, Seed  # banque-joueur (source de planter, remplie à la récolte)
# Type de base des champs écologiques (tranche 6·C) : le registre de la
# commande `fields` se DÉCOUVRE par introspection (tout attribut GridField
# d'EcoFields) — un champ ajouté au moteur apparaît tout seul dans l'overlay.
from fields.grids import GridField
# Ceinture périphérique (PÉRIPHÉRIE ⑦, D73) : génération déterministe des 4 secteurs
# depuis le seed du terrain — posée dans `game_state` pour les mondes de JEU (voir
# `cmd_init`). C'est ce branchement qui fait de la vue une CONSOMMATRICE (D92).
from fields.peripherie import generer_ceinture
from sim.bois_initial import poser_bois_initial   # D111 ②bis : bois mort dès la semaine 0
from sim.precroissance import pre_croitre         # D111 ②ter : structure des pré-vieillis
# Registre des bancs d'essai (sprint dédié) : mondes paramétrés montés par
# `init config="<banc>"` pour forcer/observer un signe. Import au niveau module
# (paquet `bancs/` au sommet, peut tout importer) ; jamais monté pour smoke/full.
from bancs import (BANCS, BANC_WEEK_DEPART, BANC_SEED, BANC_POST_INIT,
                   banc_categorie)

from .version import ENGINE_VERSION
from .maitrise_pont import observer_apres_tick  # chaîne de maîtrise après tick (voix ①)
from . import perf   # capture des pires ticks + dump diagnostique (demande Nico 2026-07-05)

# Kit de démarrage déposé dans la banque-joueur, UNIQUEMENT en config "full" (le
# monde de jeu réel, celui du F5) : une graine de chaque, pour tester `planter`
# dès le lancement sans attendre une récolte d'automne. La config "smoke"
# (fixture de test déterministe) garde une banque VIDE → le flux empty→récolte
# reste exercé tel quel par tests/simserver/planter.py.
# `ble`/`chanvre` = graines à PAILLE au départ (moyens d'agir ③, canal 2, cycle
# INTERNE cultivé) : les cultiver puis `recolter_paille` alimente le stock de mulch
# `paille` — une source de ravitaillement amorçable tôt, sans passer par l'Atelier.
BANQUE_DEPART = ("tournesol", "tomate", "basilic", "ble", "chanvre")


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


def _amorcer_encyclo(game_state: dict, player: str, mode: str) -> None:
    """Amorce l'encyclopédie de démarrage (option d'init T2, réglage d'aide CLAUDE.md).
    L'encyclopédie DÉRIVE des paliers de maîtrise (une fiche niveau 1 existe SSI
    palier ≥ 1, cf. sim/encyclopedie._decouverte) → « amorcer » = poser des
    DÉCOUVERTES (palier 1) via le mécanisme EXISTANT `maitrise.decouvrir`, jamais un
    état neuf. Palier 1 = fiche niveau 1 SEULE ; le carnet interprétatif (seuil 3)
    ne bascule PAS. Modes :
      - "amorcee" → petit lot curé (les cultivées de départ, `BANQUE_DEPART`) ;
      - "fournie" → toutes les espèces du catalogue (annuelles + pérennes) ;
      - autre / "vierge" → rien (état actuel).
    Hors tick (init) → aucun impact golden (smoke/full ne passent jamais l'option)."""
    if mode == "amorcee":
        cles = BANQUE_DEPART
    elif mode == "fournie":
        cles = tuple(PLANT_CATALOGUE) + tuple(PERENNIAL_CATALOGUE)
    else:
        return
    for cle in cles:
        M.decouvrir(game_state, player, cle)


def _pre_vieillir_fruitiers(tiles: list, seed: int) -> None:
    """Démo/F5 (`full`/`propre`) : les fruitiers du verger démarrent à leur âge de
    maturité (`maturity_years`) pour NOUER dès le 1er été — et, depuis D111 ②ter
    (ferme D105), avec la STRUCTURE de cet âge (morphogénèse déroulée hors tick).
    Déterministe ; le monde garde ses plantes (on vieillit, on n'ajoute pas)."""
    for _t in tiles:
        for _p in _t.plants:
            if getattr(_p.plant_class, "fruitier", False):
                ans = float(_p.plant_class.maturity_years)
                pre_croitre(_p, seed, ans)
                _p.age_years = ans


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
        config = msg.get("config", "smoke")
        # Seed : `msg["seed"]` explicite prioritaire (oracle/tests) ; sinon un banc
        # peut IMPOSER son seed (effondrement météo ④ : le collapse déterministe du
        # seed 12345) via `BANC_SEED` ; sinon le défaut serveur. smoke/full absents
        # du registre → défaut inchangé (golden NEUTRE).
        seed = msg.get("seed", BANC_SEED.get(config, 0x5AB1057E))
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
            # D111 ②ter (ferme D105) : on PRÉ-CROÎT aussi la structure sur ces
            # années (`sim/precroissance.py`, hors tick) → un arbre de son âge, plus
            # une pousse de 22 cm. No-op pour les fruitiers non procéduraux.
            _pre_vieillir_fruitiers(tiles, seed)
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
            _pre_vieillir_fruitiers(tiles, seed)
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
        # Ceinture périphérique (PÉRIPHÉRIE ⑦, D73) : les mondes de JEU portent une
        # périphérie tirée du SEED — c'est ici que « le jardin n'est pas une île »
        # devient vrai, et que **D92 se referme** (le tirage vient de Python, plus du
        # hash mal brassé de `DecorLayer`). Réservé à `full`/`propre` :
        #   · `smoke` est la FIXTURE du golden au pont (2 tuiles, mêmes valeurs que
        #     `tests/test_golden.py`) — lui poser une ceinture le ferait dériver de son
        #     jumeau hors serveur, ce qui n'est pas un tronçon de vue ;
        #   · un BANC force UNE condition et rien d'autre : une ceinture non demandée
        #     y ajouterait de l'ombre, de l'eau et des graines dans le dos de l'oracle.
        #     Le banc `peripherie` pose la sienne (contrastée) dans son `post_init`.
        # Absente ⇒ tous les couplages de ceinture sont des no-op strictes (⇒ golden
        # et bancs existants inchangés au bit près).
        if config in ("full", "propre"):
            game_state["ceinture"] = generer_ceinture(seed)
            # D111 ②bis : bois mort dès la semaine 0 (sous les ligneux + souches et
            # branches isolées, âges variés). Mêmes configs que la ceinture → smoke
            # (golden) et bancs intacts.
            poser_bois_initial(tiles, ecos, seed)
        # Option d'init « carnet interprétatif anticipé » (T2, réglage d'aide
        # CLAUDE.md, défaut NON). Champ OPTIONNEL du message : absent → aucune clé
        # `options` → `sim/carnet._reglage_anticipe` renvoie False → seuil normal
        # (comportement actuel, golden intact). Présent → pose le flag lu au tick.
        carnet_anticipe = msg.get("carnet_anticipe")
        if carnet_anticipe is not None:
            player = game_state["current_player"]
            game_state.setdefault("options", {}).setdefault(player, {})[
                "carnet_anticipe"] = bool(carnet_anticipe)
        # Option d'init « Vigueur infinie » (réglage de TEST, 0.5.49) : même patron.
        # Absent → aucun effet ; présent → `sim/vigueur.spend` ne débite plus rien.
        vigueur_infinie = msg.get("vigueur_infinie")
        if vigueur_infinie is not None:
            player = game_state["current_player"]
            game_state.setdefault("options", {}).setdefault(player, {})[
                "vigueur_infinie"] = bool(vigueur_infinie)
        self.engine = Engine(game_state)
        # Un nouvel `init` repart d'un monde neuf : tout automate actif d'une
        # session précédente pointait l'ancien engine → on le démonte (opt-in :
        # la vue le ré-arme via `automate on` si elle le veut). Golden intact.
        self._automate = None
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
        # Option d'init « encyclopédie de démarrage » (T2). APRÈS l'opt-in Vigueur
        # et le hook de banc, comme `BANC_POST_INIT` : l'état maîtrise est prêt.
        # Champ OPTIONNEL : absent → pas d'amorçage (encyclo vierge, comportement
        # actuel, golden intact). smoke/full ne le passent jamais.
        encyclo = msg.get("encyclo_demarrage")
        if encyclo:
            _amorcer_encyclo(game_state, game_state["current_player"], encyclo)
        return {"ok": True, "engine_version": ENGINE_VERSION,
                "world": self._world_static()}

    def cmd_list_bancs(self, msg: dict) -> dict:
        """Liste des bancs d'essai montables par `init config="<nom>"` (sprint
        dédié). Source UNIQUE = le registre Python `BANCS` (principe #1 : Python
        source de vérité) — le sélecteur Godot la LIT au lieu de dupliquer les
        noms en C#, qui se périmeraient en silence à l'ajout d'un banc (un menu
        qui ment = le piège même que ce sprint élimine, cf. D47). Lecture du
        registre, pas du moteur → appelable AVANT `init` (pour peupler le menu).

        Chaque entrée porte sa CATÉGORIE (module thématique d'origine, dérivée)
        pour que le sélecteur Godot filtre par thème sans dupliquer une table de
        classement (fenêtrage UI T1). Trié par nom → affichage déterministe."""
        return {"ok": True,
                "bancs": [{"nom": n, "categorie": banc_categorie(n)}
                          for n in sorted(BANCS)]}

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
        # DRIVER des quêtes (D79 ⑤) : HORS tick, après la simulation — arrivée des
        # lettres mûres, clôture des quêtes d'état comblées, versement des récompenses.
        # Opt-in strict (aucune lettre mûre → no-op) ; le golden tourne hors serveur →
        # jamais appelé → golden intact. Les quêtes CUMULÉES, elles, se closent au hook
        # geste (plante_route), pas ici. Câblé APRÈS `consigner` (le ledger ✉ des quêtes
        # accomplies sera consigné au tick suivant, comme tout marqueur du log).
        self.avancer_quetes(gs, gs["current_player"])
        gs["log"].clear()   # borne la mémoire (cf. golden)
        # Jardinier automate (sprint jardinier_auto ⑥) : SI actif, il joue ICI, APRÈS
        # le tick, côté APPELANT — invariant H2 (jamais dans tick_semaine). Opt-in
        # strict (`self._automate` None par défaut) → no-op, golden intact. Ses gestes
        # passent par les MÊMES façades `sim.actions` que le joueur (aucune API
        # privilégiée, philo #2) ; leur effet est visible au snapshot ci-dessous.
        if self._automate is not None:
            self._automate.jouer_tick(self.engine)
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
            # "inoculum" : idem (charge pathogène SPARSE par plot indexée par
            # famille, pas un GridField dense) — on matérialise `inoculum.total`
            # à la demande (mémoire d'inoculum ④) pour la heatmap F6.
            extra = ["vitalite"]
            if getattr(eco0, "inoculum", None) is not None:
                extra.append("inoculum")
            return {"ok": True,
                    "fields": direct + list(eco0.populations.keys()) + extra}
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
            if field == "inoculum":
                # Cas spécial (mémoire d'inoculum ④) : charge pathogène TOTALE
                # par plot (Σ des familles, `inoculum.total`), matérialisée en
                # grille dense row-major à la demande. Le champ moteur est SPARSE
                # (dict par plot) → un plot sain répond 0.0. PURE lecture.
                ino = getattr(eco, "inoculum", None)
                tiles_out[tile.tile_id] = {
                    "rows": eco.rows, "cols": eco.cols,
                    "values": [round(ino.total(r, c) if ino is not None else 0.0, 4)
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
