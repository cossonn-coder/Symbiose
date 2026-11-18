"""
SYMBIOSE — tests/test_levee_graines.py
D139 caractères vivants ①d : le stock de graines du sol décide de ce qui lève.
  1. S3 `choisir_espece` : sans pool = tirage uniforme historique (au bit près) ;
     avec un pool dominant, l'espèce correspondante sort le plus souvent.
  2. S2 ressemis : une bourrache au pool dense lève sur un plot libre favorable ;
     pas sous ombre profonde, pas hors fenêtre de pH ; pool sous le seuil → rien ;
     une vivace (recrue directe) ne lève jamais depuis son pool ; un archétype qui
     lève a la priorité.
Lancement depuis data/code/ : python3 -m tests.test_levee_graines
"""
from __future__ import annotations

import sys

from world import Tile
from fields import init_eco
from fields.seedbank import SEED_ARCHETYPES, SPECIES_POOL_MIN_DENSITY
from plants import Borage, Clover, Taraxacum
from plants.species import PlantainLanceole
from sim.succession import choisir_espece, succession

SEED = 0x5EED
ECHECS: list[str] = []


def check(libelle: str, ok: bool, detail: str = "") -> None:
    print(f"  {'OK ' if ok else 'KO '} {libelle}" + (f" ({detail})" if detail else ""))
    if not ok:
        ECHECS.append(libelle)


def test_s3() -> None:
    print("[1] S3 — espèce ∝ son pool")
    eco = init_eco("T0", 10, 10)
    vide = all(choisir_espece("competitor", 0.0, 42, w, r, c)
               == choisir_espece("competitor", 0.0, 42, w, r, c, eco.seed_bank)
               for w in range(1, 53) for r in range(10) for c in range(10))
    check("sans pool : identique au tirage uniforme", vide)
    eco.seed_bank.add_species(4, 4, PlantainLanceole, 1.0, {})
    tirs = [choisir_espece("competitor", 0.0, 42, w, 4, 4, eco.seed_bank)
            for w in range(1, 401)]
    part = tirs.count(PlantainLanceole) / len(tirs)
    check("pool dominant : le plantain sort le plus souvent", part > 0.9,
          f"part {part:.3f}, attendu ≈ 0,98")
    check("le pissenlit garde sa pluie extérieure", Taraxacum in tirs)


def _tuile(lumiere: float = 1.0, ph: float = 6.8, t_sol: float = 16.0):
    """Tuile 6×6 favorable, SANS banque d'archétype (aucun archétype ne lève)."""
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = init_eco("T0", 6, 6, humidite=1.5, fertilite=0.5, microbiome=0.3)
    eco.lumiere.fill(lumiere)
    eco.disturbance.fill(1.0)
    eco.soil_memory_deep.fill(0.0)
    eco.ph.fill(ph)
    eco.temperature_sol.fill(t_sol)
    for r in range(6):
        for c in range(6):
            for a in SEED_ARCHETYPES:
                eco.seed_bank.data[r][c][a] = 0.0
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {},
          "current_player": "joueur_1", "week": 5, "log": [], "seed": SEED}
    return gs, tile, eco


def _leve(gs, tile, eco, espece) -> tuple[bool, list[str]]:
    """Succession semaine après semaine (sol et pool figés) ; vrai dès qu'un pied
    de `espece` est debout en (3,3)."""
    log = []
    for w in range(5, 60):
        log += succession(gs, tile, eco, w)
        if any(p.is_alive and p.position == (3, 3) and p.plant_class is espece
               for p in tile.plants):
            return True, log
    return False, log


def test_s2() -> None:
    print("[2] S2 — les annuelles se ressèment depuis leur pool")
    gs, tile, eco = _tuile()
    eco.seed_bank.add_species(3, 3, Borage, 0.8, {})
    ok, log = _leve(gs, tile, eco, Borage)
    check("bourrache au pool dense : lève sur plot libre favorable", ok)
    check("ligne de log « ressemis »", any("Bourrache" in l and "ressemis" in l
                                            for l in log) if ok else False)

    gs, tile, eco = _tuile(lumiere=0.02)
    eco.seed_bank.add_species(3, 3, Borage, 0.8, {})
    check("sous ombre profonde : ne lève pas", not _leve(gs, tile, eco, Borage)[0])

    # La bourrache réelle tolère large (ph_tol 3) : fenêtre resserrée pour le test.
    class BourracheCalcicole(Borage):
        ph_tol = 0.5
    gs, tile, eco = _tuile(ph=4.5)
    eco.seed_bank.add_species(3, 3, BourracheCalcicole, 0.8, {})
    check("hors fenêtre de pH : ne lève pas",
          not _leve(gs, tile, eco, BourracheCalcicole)[0])
    gs, tile, eco = _tuile(ph=6.8)
    eco.seed_bank.add_species(3, 3, BourracheCalcicole, 0.8, {})
    check("… et lève dans sa fenêtre", _leve(gs, tile, eco, BourracheCalcicole)[0])

    gs, tile, eco = _tuile()
    eco.seed_bank.add_species(3, 3, Borage, SPECIES_POOL_MIN_DENSITY * 0.8, {})
    check("pool sous le seuil : rien", not _leve(gs, tile, eco, Borage)[0])

    gs, tile, eco = _tuile()
    eco.seed_bank.add_species(3, 3, Clover, 0.8, {})
    check("vivace à recrue directe (trèfle) : pas de double voie",
          not _leve(gs, tile, eco, Clover)[0])

    gs, tile, eco = _tuile()
    eco.seed_bank.add_species(3, 3, Borage, 0.8, {})
    for a in SEED_ARCHETYPES:
        eco.seed_bank.add(3, 3, a, 1.0)
    log = succession(gs, tile, eco, 5)
    check("un archétype qui lève passe avant le ressemis",
          not any("ressemis" in l and "@(3,3)" in l for l in log))


if __name__ == "__main__":
    test_s3()
    test_s2()
    print(f"\n{'TOUS LES TESTS PASSENT' if not ECHECS else f'ÉCHECS : {ECHECS}'}")
    sys.exit(1 if ECHECS else 0)
