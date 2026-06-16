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

from world import House
from sim.engine import Engine
from sim import vigueur as V      # état Vigueur joueur (ensure/spend/gain, D11)
from sim.seeds import PlayerSeedBank, Seed  # banque-joueur (source de planter, remplie à la récolte)
# Type de base des champs écologiques (tranche 6·C) : le registre de la
# commande `fields` se DÉCOUVRE par introspection (tout attribut GridField
# d'EcoFields) — un champ ajouté au moteur apparaît tout seul dans l'overlay.
from fields.grids import GridField

from .version import ENGINE_VERSION

# Kit de démarrage déposé dans la banque-joueur, UNIQUEMENT en config "full" (le
# monde de jeu réel, celui du F5) : une graine de chaque, pour tester `planter`
# dès le lancement sans attendre une récolte d'automne. La config "smoke"
# (fixture de test déterministe) garde une banque VIDE → le flux empty→récolte
# reste exercé tel quel par tests/simserver/planter.py.
BANQUE_DEPART = ("tournesol", "tomate", "basilic")


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
        else:
            return {"ok": False,
                    "error": f"config inconnue : {config!r} ('smoke' ou 'full')"}
        game_state = {
            "tiles": tiles, "eco": ecos, "scores": {},
            "current_player": "joueur_1", "week": 1, "log": [],
            "house": house, "seed": seed,
            # Banque-joueur (sprint planter·arroser) : source des graines de
            # `planter`. Le tick de récolte (engine.py, gardé par
            # `if player_seed_bank is not None`) y dépose les graines sélectionnées
            # (D17) au fil des automnes. Le golden écolo n'init jamais via ce
            # serveur → intact. Sérialisable JSON (futur save par profil).
            # Kit de démarrage en config "full" seulement (retour F5 Nico) : 1
            # graine de chaque espèce potagère emblématique pour tester `planter`
            # sans attendre un automne. "smoke" reste à banque vide (cf. helper).
            "player_seed_bank": _banque_initiale(config),
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
