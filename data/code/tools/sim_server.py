"""
SYMBIOSE — tools/sim_server.py
Serveur de simulation : le moteur Python derrière un pont JSON stdin/stdout.

Sprint Intégration Godot ↔ Python, tranche 1 (Option B actée : Python = moteur,
Godot = vue). Godot lance ce script en SOUS-PROCESS et lui parle par les pipes —
schéma UART logiciel : stdin = Godot→Python, stdout = Python→Godot, framing par
délimiteur `\n` (1 ligne = 1 message JSON complet, JSON compact n'émet jamais de
`\n` littéral). Maître/esclave strict : Godot envoie une commande, ce serveur
répond UNE ligne, jamais de message spontané → pas de concurrence, déterminisme
préservé.

ADAPTATEUR, pas moteur : on importe le moteur comme le font main.py et
tests/test_golden.py, on ne modifie RIEN de sa logique → golden intact par
construction. Si Godot a besoin d'une donnée absente, on l'ajoute au SNAPSHOT
(lecture seule), jamais au tick.

Protocole v1 (requête → réponse, champ `cmd` obligatoire) :
  → {"cmd": "init", "seed": 42, "config": "smoke"}   # ou "full" (monde 20×20 m)
  ← {"ok": true, "engine_version": "...", "world": {tuiles + maison, statique}}
  → {"cmd": "step_week"}
  ← {"ok": true, "snapshot": {...}}
  → {"cmd": "snapshot"}
  ← {"ok": true, "snapshot": {...}}
  → {"cmd": "action", "verb": "manger", "target": {...}, "params": {...}}
  ← {"ok": true, "result": {"applied": bool, "cost": x, "gain": x,
                            "vigueur": x, "vigueur_max": x, "message": "..."},
     "snapshot": {...}}     # snapshot frais TOUJOURS joint (effet visible en 1 aller-retour)
  → {"cmd": "fields"}                                # mode debug (t6·C)
  ← {"ok": true, "fields": [noms…]}                  # registre découvert
  → {"cmd": "fields", "field": "microbiome"}
  ← {"ok": true, "field": "...", "tiles": {tid: {rows, cols, values}}}
     # values = liste row-major ; le snapshot hebdo n'embarque PAS les
     # grilles (volume) — la vue ne les demande que si l'overlay est ON.
  → {"cmd": "quit"}
  ← {"ok": true}
Cibles d'action (tranche 4, décision kickoff : désignation NON-AMBIGUË, le
serveur fait foi — Godot transmet l'INTENTION, Python possède les RÈGLES) :
  plante : {"tile": "T3", "x_cm": …, "y_cm": …}   # position LOCALE tuile, ±0.1 cm
           (le snapshot n'expose pas d'id moteur et les plantes ne bougent
            jamais : la position EST l'identité — déjà la clé du diff t3)
           + pour `tailler` (tranche 5) : champ OPTIONNEL "segment": i =
           l'index dans `segments` du snapshot (= ordre structure_to_dict(),
           stable et déterministe) — la branche cliquée. Validé ICI (bornes,
           collet protégé) AVANT d'appeler la façade : un segment invalide est
           un refus métier qui ne coûte RIEN. Absent → repli params.cible.
  plot   : {"tile": "T3", "r": 2, "c": 5}          # becher, ecraser
  tuile  : {"tile": "T3"}                          # favoriser_auxiliaire
  rien   : {}                                      # grelinette
  params : {"cible": "apex"|"branche"} (tailler) ; {"urgence": bool} (ecraser —
           true si phase Saison côté vue : la couture préparation/réaction §3.1)
Refus métier (verbe inconnu, cible introuvable, Vigueur insuffisante) →
{"ok": true, "result": {"applied": false, "message": …}} : le geste a échoué
mais le PROTOCOLE a réussi. {"ok": false} reste réservé aux commandes
malformées — même règle v0, le serveur ne crashe jamais et répond toujours.
EOF sur stdin (Godot mort sans `quit`) → sortie propre.

Usage (depuis data/code/, ou n'importe où — bootstrap sys.path ci-dessous) :
  python3 tools/sim_server.py     # puis taper les commandes JSON à la main
  python3 -m tools.sim_server
Test : python3 -m tests.test_sim_server
"""
from __future__ import annotations
import contextlib
import json
import os
import sys

# Bootstrap : lancé en script direct (`python3 tools/sim_server.py`), sys.path[0]
# est tools/ → les imports absolus du moteur (plants, sim, …) échoueraient. On
# remonte à data/code/ comme racine d'import (sans effet en mode -m).
_CODE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from world import House
from sim.engine import Engine, saison_de
from sim import actions as A      # les 8 gestes joueur (façades, sprint Vigueur/D31.3)
from sim import vigueur as V      # état Vigueur joueur (ensure/spend/gain, D11)
# Échantillonneur de vie macro (tranche 6·B) : fonction PURE et déterministe
# densité → entités (fields/population.py §3). L'échantillonnage se fait CÔTÉ
# SERVEUR — la vue n'a pas besoin de _hash_noise (kickoff t6 §4).
from fields.population import sample_sprites
# Type de base des champs écologiques (tranche 6·C) : le registre de la
# commande `fields` se DÉCOUVRE par introspection (tout attribut GridField
# d'EcoFields) — un champ ajouté au moteur apparaît tout seul dans l'overlay.
from fields.grids import GridField
# Table « stade reproducteur visible par saison » du prototype SVG (tranche 6,
# volet A) : import OUTIL → OUTIL (render_structure est un outil, pas le
# moteur), zéro duplication — la table validée visuellement au sprint
# Croissance reste la source unique du proxy saisonnier.
from tools.render_structure import REPRO_BY_SEASON

# Version du protocole/moteur exposée dès le v0 (même philosophie que le futur
# save JSON : casse explicite si schéma incompatible). Locale au serveur pour
# l'instant — le « sprint save global » décidera où la centraliser.
# 0.2.0 (tranche 4) : commande `action` + bloc `player` dans le snapshot.
# 0.2.1 (tranche 5) : `target.segment` optionnel sur `tailler` (taille au clic).
# 0.2.2 (tranche 6·A) : 3 hints d'organes par plante au snapshot
#       (foliage_density, organ, organ_site) — pur rendu, lecture seule.
# 0.2.3 (tranche 6·B) : bloc `sprites` au snapshot (vie macro, D31 côté vue) —
#       par tuile et par guilde, tableaux COMPACTS [r, c, x_frac, y_frac,
#       activite]. Compact d'emblée : mesuré 705 Ko/snapshot en format objet
#       verbeux au pic d'automne du monde full (~8600 sprites) vs 210 Ko en
#       tableaux — la mitigation prévue au kickoff §4 s'impose à la mesure.
# 0.3.0 (tranche 6·C, fin de tranche) : commande `fields` (mode debug champs
#       écologiques) — registre par introspection + grilles par tuile à la
#       demande, HORS snapshot (volume : la vue ne paie que l'overlay ouvert).
# 0.3.1 (post-intégration) : `target.guilde` optionnel sur `ecraser` (écraser le
#       sprite cliqué quelle que soit sa guilde — défaut `ravageur` = compat).
ENGINE_VERSION = "0.3.1"

# Repli pour une espèce absente de REPRO_BY_SEASON (kickoff t6 : « fleur au
# printemps, fruit mûr en été/automne, rien l'hiver ») — raisonnable pour les
# herbacées du catalogue en attendant le VRAI état reproducteur (D19/D33).
DEFAULT_REPRO = {"printemps": "flower", "ete": "fruit_ripe",
                 "automne": "fruit_ripe", "hiver": None}

# Tolérance du match plante-par-position (kickoff t4 §8) : les positions du
# snapshot reviennent telles quelles dans la cible → l'epsilon n'absorbe que le
# bruit de sérialisation JSON (float64 round-trip, en pratique exact).
PLANT_EPSILON_CM = 0.1


class SimServer:
    """État du serveur : un Engine (ou None avant `init`). Dispatch des commandes."""

    def __init__(self):
        self.engine = None

    # ------------------------------------------------------------------ cmds

    def cmd_init(self, msg: dict) -> dict:
        seed = msg.get("seed", 0x5AB1057E)
        config = msg.get("config", "smoke")
        if not isinstance(seed, int):
            return {"ok": False, "error": f"seed doit être un entier (reçu {seed!r})"}
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
        else:
            return {"ok": False,
                    "error": f"config inconnue : {config!r} ('smoke' ou 'full')"}
        game_state = {
            "tiles": tiles, "eco": ecos, "scores": {},
            "current_player": "joueur_1", "week": 1, "log": [],
            "house": house, "seed": seed,
        }
        self.engine = Engine(game_state)
        # Brancher la Vigueur joueur (tranche 4) : l'OPT-IN se fait ICI, pas
        # dans le moteur. Dès que la clé `vigueur` existe, le tick existant
        # (engine.py, gardé par `if "vigueur" in game_state`) fait seul la
        # régen hebdo + le plein au passage de saison — rien d'autre à câbler.
        # Le golden écolo reste intact : il n'init jamais via ce serveur.
        V.ensure_player(game_state, game_state["current_player"])
        return {"ok": True, "engine_version": ENGINE_VERSION,
                "world": self._world_static()}

    def cmd_step_week(self, msg: dict) -> dict:
        if self.engine is None:
            return {"ok": False, "error": "step_week avant init"}
        # stdout est RÉSERVÉ au protocole : tick_semaine() ne print pas (vérifié
        # — seul run_years(verbose=True) le fait), mais on blinde contre une
        # évolution future du moteur en déviant tout print vers stderr.
        with contextlib.redirect_stdout(sys.stderr):
            self.engine.tick_semaine()
        self.engine.game_state["log"].clear()   # borne la mémoire (cf. golden)
        return {"ok": True, "snapshot": self._snapshot()}

    def cmd_snapshot(self, msg: dict) -> dict:
        if self.engine is None:
            return {"ok": False, "error": "snapshot avant init"}
        return {"ok": True, "snapshot": self._snapshot()}

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
            return {"ok": True,
                    "fields": direct + list(eco0.populations.keys())}
        tiles_out = {}
        for tile in gs["tiles"]:
            eco = gs["eco"][tile.tile_id]
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

    # ------------------------------------------------------------- actions
    # Le serveur APPELLE les façades de sim/actions.py (sprint Vigueur +
    # D31.3) — il ne réimplémente AUCUNE règle : validité, coût (maîtrise ×
    # urgence), effet et plafonds restent côté moteur. Rôle de l'adaptateur :
    # résoudre la DÉSIGNATION (tile/plot/plante par position) et traduire le
    # retour en JSON. Maître/esclave : Godot envoie l'intention, ici on
    # répond ACK/NAK + données — jamais la vue n'écrit dans le moteur.

    def cmd_action(self, msg: dict) -> dict:
        if self.engine is None:
            return {"ok": False, "error": "action avant init"}
        verb = msg.get("verb")
        target = msg.get("target") or {}
        params = msg.get("params") or {}
        if not isinstance(target, dict) or not isinstance(params, dict):
            return {"ok": False, "error": "target/params doivent être des objets"}
        result = self._do_action(verb, target, params)
        # Snapshot frais TOUJOURS joint : l'effet (plante disparue, etc.) est
        # visible en un seul aller-retour — pas de 2e requête à inventer.
        return {"ok": True, "result": result, "snapshot": self._snapshot()}

    def _do_action(self, verb: str, target: dict, params: dict) -> dict:
        gs = self.engine.game_state
        player = gs["current_player"]

        def bilan(applied: bool, cost: float, gain_v: float, message: str) -> dict:
            """État Vigueur APRÈS le geste — y compris sur refus : un échec
            binaire à vide a quand même drainé (contrat de spend, philo #1)."""
            st = V.ensure_player(gs, player)
            return {"applied": applied, "cost": cost, "gain": gain_v,
                    "vigueur": st["courante"],
                    "vigueur_max": V.vigueur_max(gs, player),
                    "message": message}

        # --- résolution de la cible, selon la famille du verbe ------------
        tiles = {t.tile_id: t for t in gs["tiles"]}

        def tile_cible():
            tile = tiles.get(target.get("tile"))
            return tile, (None if tile is None else gs["eco"][tile.tile_id])

        if verb in ("manger", "recolter", "deraciner", "tailler"):
            tile, eco = tile_cible()
            if tile is None:
                return bilan(False, 0.0, 0.0,
                             f"tuile introuvable : {target.get('tile')!r}")
            plant = self._plant_at(tile, target.get("x_cm"), target.get("y_cm"))
            if plant is None:
                return bilan(False, 0.0, 0.0,
                             "aucune plante vivante à cette position")
            # Coût nominal AVANT le geste (cout_action est une lecture pure —
            # le geste recalcule le même en interne) : pour l'affichage HUD.
            cost = A.cout_action(gs, player, verb, A._objets_action(verb, plant))
            if verb == "manger":
                g = A.manger(gs, player, plant, eco)
                # Gain nominal DANS le message (retour F5 Nico : « rien ne se
                # passe » = organe immature, gain ≈ 0 — qu'on le LISE).
                return bilan(True, 0.0, g,
                             f"mangé : {plant.name} (+{g:.1f} Vigueur — "
                             f"gain ∝ maturité de l'organe)")
            if verb == "recolter":
                ratio = A.recolter(gs, player, plant, eco)
                msg = ("récolté : " + plant.name if ratio >= 1.0
                       else f"récolte partielle ({ratio:.0%}) : {plant.name}")
                return bilan(ratio > 0.0, cost, 0.0, msg)
            if verb == "deraciner":
                ok = A.deraciner(gs, player, plant, eco)
                return bilan(ok, cost, 0.0,
                             "déraciné : " + plant.name if ok
                             else "Vigueur insuffisante — rien déraciné")
            # tailler
            cible = params.get("cible", "apex")
            if cible not in ("apex", "branche"):
                return bilan(False, 0.0, 0.0,
                             f"cible de taille inconnue : {cible!r}")
            # Segment explicite (tranche 5, la branche cliquée) : validé AVANT
            # la façade — un refus de désignation ne draine pas la Vigueur.
            # NB : bool est un sous-type d'int en Python → exclu explicitement.
            seg = target.get("segment")
            if seg is not None:
                if not isinstance(seg, int) or isinstance(seg, bool):
                    return bilan(False, 0.0, 0.0,
                                 f"segment non entier : {seg!r}")
                if not 0 <= seg < len(plant.segments):
                    return bilan(False, 0.0, 0.0,
                                 f"segment hors structure : {seg} "
                                 f"(plante à {len(plant.segments)} segments)")
                if plant.segments[seg].parent is None:
                    return bilan(False, 0.0, 0.0,
                                 "le collet est protégé — rien à couper ici")
            ok = A.tailler(gs, player, plant, eco, cible=cible, segment_id=seg)
            quoi = f"segment {seg}" if seg is not None else cible
            return bilan(ok, cost, 0.0,
                         f"taillé ({quoi}) : {plant.name}" if ok
                         else "Vigueur insuffisante — rien taillé")

        if verb in ("ecraser", "becher"):
            tile, eco = tile_cible()
            if tile is None:
                return bilan(False, 0.0, 0.0,
                             f"tuile introuvable : {target.get('tile')!r}")
            r, c = target.get("r"), target.get("c")
            if (not isinstance(r, int) or not isinstance(c, int)
                    or not (0 <= r < tile.grid_rows)
                    or not (0 <= c < tile.grid_cols)):
                return bilan(False, 0.0, 0.0,
                             f"plot hors tuile : r={r!r}, c={c!r}")
            if verb == "ecraser":
                urgence = bool(params.get("urgence", False))
                # Guilde du SPRITE cliqué (protocole 0.3.1) : on écrase ce qui
                # est sous la souris, quelle que soit sa nature. Défaut ravageur
                # = compat des clients < 0.3.1 (Godot passe désormais la guilde).
                guilde = target.get("guilde", "ravageur")
                if guilde not in eco.populations:
                    return bilan(False, 0.0, 0.0,
                                 f"guilde inconnue : {guilde!r}")
                cost = (A.cout_action(gs, player, "ecraser")
                        * (A.URGENCE_MULT if urgence else 1.0))
                # Densité de la guilde ciblée avant/après DANS le message (la vue
                # confirme l'effet en un aller-retour). Lecture pure, zéro règle.
                avant = eco.populations[guilde].get(r, c)
                ok = A.ecraser(gs, player, eco, r, c, guilde=guilde, urgence=urgence)
                apres = eco.populations[guilde].get(r, c)
                return bilan(ok, cost, 0.0,
                             f"écrasé un {guilde} en ({r},{c})"
                             + (" [urgence]" if urgence else "")
                             + f" — {guilde} {avant:.2f} → {apres:.2f}" if ok
                             else "Vigueur insuffisante — rien écrasé")
            cost = A.cout_action(gs, player, "becher", A.OBJETS_TOUCHES["becher"])
            ok = A.becher(gs, player, eco, r, c)
            return bilan(ok, cost, 0.0,
                         f"bêché en ({r},{c})" if ok
                         else "Vigueur insuffisante — rien bêché")

        if verb == "favoriser_auxiliaire":
            tile, _eco = tile_cible()
            if tile is None:
                return bilan(False, 0.0, 0.0,
                             f"tuile introuvable : {target.get('tile')!r}")
            cost = A.cout_action(gs, player, "favoriser_auxiliaire",
                                 A.OBJETS_TOUCHES["favoriser_auxiliaire"])
            ok = A.favoriser_auxiliaire(gs, player, tile)
            return bilan(ok, cost, 0.0,
                         f"habitat auxiliaire posé sur {tile.tile_id}" if ok
                         else "échec (Vigueur insuffisante ou tiges saturées)")

        if verb == "grelinette":
            cost = A.cout_action(gs, player, "grelinette",
                                 A.OBJETS_TOUCHES["grelinette"])
            ok = A.grelinette(gs, player)
            return bilan(ok, cost, 0.0,
                         "sol ameubli à la grelinette" if ok
                         else "Vigueur insuffisante")

        return bilan(False, 0.0, 0.0, f"verbe inconnu : {verb!r}")

    @staticmethod
    def _plant_at(tile, x_cm, y_cm, eps: float = PLANT_EPSILON_CM):
        """La plante VIVANTE de la tuile à ±eps de (x_cm, y_cm) locale, ou None.
        La position est l'identité (kickoff §8) : pas d'id inventé."""
        if not isinstance(x_cm, (int, float)) or not isinstance(y_cm, (int, float)):
            return None
        for p in tile.plants:
            if (p.is_alive and p.x_cm is not None
                    and abs(p.x_cm - x_cm) <= eps
                    and abs(p.y_cm - y_cm) <= eps):
                return p
        return None

    # ------------------------------------------------------- sérialisation

    def _world_static(self) -> dict:
        """Partie STATIQUE du monde (renvoyée une fois, au init) : layout des
        tuiles + maison. Tout ce qui bouge chaque semaine va dans le snapshot."""
        gs = self.engine.game_state
        house = gs["house"]
        hx0, hy0, hx1, hy1 = house.footprint_bounds
        return {
            "tiles": [
                {"id": t.tile_id, "soil": t.soil_type,
                 "rows": t.grid_rows, "cols": t.grid_cols,
                 "origin_x_cm": t.origin_x_cm, "origin_y_cm": t.origin_y_cm}
                for t in gs["tiles"]
            ],
            "house": {"footprint_cm": [hx0, hy0, hx1, hy1],
                      "height_cm": house.height_cm},
        }

    def _snapshot(self) -> dict:
        """Snapshot v0 minimal (kickoff tranche 1) : horloge + plantes vivantes.
        `week` = compteur moteur (prochaine semaine à simuler, 1 = rien simulé) ;
        year/season en sont dérivés. Par plante : position continue LOCALE à sa
        tuile (x_cm/y_cm + tile pour replacer en monde via origin_*_cm) et la
        structure de segments via structure_to_dict() (format Croissance·6, le
        même que tools/export_structure.py → PlantStructure.cs sait déjà lire)."""
        gs = self.engine.game_state
        week = gs["week"]
        week_in_year = ((week - 1) % 52) + 1
        saison = saison_de(week_in_year)
        plants = []
        for tile in gs["tiles"]:
            for p in tile.plants:
                if not p.is_alive:
                    continue
                cls = p.plant_class
                # Hints d'organes (tranche 6·A, kickoff §1) : les organes ne
                # sont PAS un état moteur (§J : reconstructibles à la volée) —
                # on expose le proxy SAISONNIER du prototype SVG, la vue
                # dessine. Le vrai état reproducteur (maturité réelle,
                # déplétion par `manger`) = D19/D33, sprints moteur dédiés.
                repro = REPRO_BY_SEASON.get(cls.__name__, DEFAULT_REPRO)
                plants.append({
                    "tile": tile.tile_id,
                    "species": cls.__name__,
                    "name": p.name,
                    "x_cm": p.x_cm, "y_cm": p.y_cm,
                    "stage": p.current_stage,
                    "stage_name": p.stage.name,
                    "height_cm": p.current_height,
                    "foliage_density": cls.foliage_density_at(p, saison),
                    "organ": repro.get(saison),
                    "organ_site": cls.organ_site,
                    "segments": p.structure_to_dict(),
                })
        # Vie macro (tranche 6·B, kickoff §4) : sprites échantillonnés depuis
        # les 4 champs de population — PURE lecture (sample_sprites ne modifie
        # rien, positions par hash indépendantes de la semaine : un slot vit
        # toujours au même point, il apparaît/disparaît quand la densité
        # franchit son seuil). Format compact par guilde, cf. ENGINE_VERSION.
        # Arrondis : x/y_frac 3 déc. (= 0,05 cm dans le plot), activite 2 —
        # et round() est déterministe, la clé de diff côté vue reste stable.
        sprites = {}
        for tile in gs["tiles"]:
            eco = gs["eco"][tile.tile_id]
            sprites[tile.tile_id] = {
                f.spec.name: [
                    [s.row, s.col, round(s.x_frac, 3), round(s.y_frac, 3),
                     round(s.activite, 2)]
                    for s in sample_sprites(f, gs["seed"])]
                for f in eco.populations.values()}
        # Bloc joueur (tranche 4, lecture seule) : la vue affiche la Vigueur
        # au HUD. vigueur_max passe par la façade (bonus maîtrise compris).
        player = gs["current_player"]
        st = V.ensure_player(gs, player)
        return {"week": week, "week_in_year": week_in_year,
                "year": (week - 1) // 52 + 1, "season": saison,
                "player": {"vigueur": st["courante"],
                           "vigueur_max": V.vigueur_max(gs, player)},
                "plants": plants, "sprites": sprites}


def main() -> int:
    server = SimServer()
    dispatch = {"init": server.cmd_init,
                "step_week": server.cmd_step_week,
                "snapshot": server.cmd_snapshot,
                "action": server.cmd_action,
                "fields": server.cmd_fields}
    # 1 ligne lue = 1 réponse écrite. EOF (Godot mort sans quit) → fin de boucle.
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        quit_after = False
        try:
            msg = json.loads(line)
            if not isinstance(msg, dict):
                resp = {"ok": False, "error": "message JSON non-objet"}
            else:
                cmd = msg.get("cmd")
                if cmd == "quit":
                    resp, quit_after = {"ok": True}, True
                elif cmd in dispatch:
                    resp = dispatch[cmd](msg)
                else:
                    resp = {"ok": False, "error": f"commande inconnue : {cmd!r}"}
        except Exception as e:                       # le serveur survit à tout
            resp = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        # Compact (1 ligne) + sort_keys (stable entre runs → déterminisme
        # vérifiable byte-à-byte). flush OBLIGATOIRE : sans lui la réponse
        # reste dans le buffer et Godot attend indéfiniment (piège n°1 des pipes).
        print(json.dumps(resp, sort_keys=True, separators=(",", ":")), flush=True)
        if quit_after:
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
