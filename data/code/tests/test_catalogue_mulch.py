"""
SYMBIOSE — tests/test_catalogue_mulch.py
Catalogue enrichi, sprint équilibre invasion ⑤ (D10/D69) : les 3 espèces SOURCES
DE MULCH — Blé (Poaceae), Chanvre (Cannabaceae), Sapin (Pinaceae). On prouve que
« l'espèce sert l'idée » est bien câblée de bout en bout (règle catalogue) :

  1. SANITY CATALOGUE — les 3 clés (ble, chanvre, sapin) sont dans PLANT/PERENNIAL,
     s'instancient, germent et dépassent le semis (jumeau de test_catalogue_lot2).
  2. NATURE DE MULCH — chaque espèce déclare le bon `mulch_source` (blé/chanvre →
     "paille", sapin → "aiguilles") ; ces natures existent dans NATURES_MULCH.
  3. INTERCONNEXION RÉCOLTE→STOCK — récolter un vrai plant de blé/chanvre crédite
     le stock "paille" ; un sapin crédite "aiguilles" ; broyer un squelette de
     sapin (ligneux → `bois_restant` à sa mort) crédite du BRF.
  4. VOIX — chaque espèce a sa fiche encyclopédie 3 niveaux (les 4 autres voix —
     carnet/pages/magazine/événements — sont vérifiées par leurs propres suites :
     alignement corpus↔catalogue dans test_encyclopedie, pages dans test_pages,
     offre famille dérivée dans test_magazine, marqueurs génériques dans
     test_evenements — ce test cible ce qui est SPÉCIFIQUE aux 3 espèces).

Lancement (depuis data/code/) :
  python3 -m tests.test_catalogue_mulch
"""

import sys

from world import Tile
from plants import Wheat, Hemp, FirTree
from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE
from fields import init_eco
from fields.ecofields import NATURES_MULCH
from sim.engine import Engine
from sim import actions as ACT
from sim import vigueur as V
from sim.encyclopedie_corpus import FICHES

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK " if cond else "XX "
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _engine_with(tile, eco):
    """Engine sur une tuile, germination spontanée NEUTRALISÉE (on isole les
    plantes posées)."""
    eco.seed_bank.germination_candidates = lambda *a, **k: []
    gs = {
        "tiles": [tile], "eco": {tile.tile_id: eco}, "scores": {},
        "current_player": "joueur_1", "week": 1, "log": [],
    }
    V.ensure_player(gs, "joueur_1")
    gs["vigueur"]["joueur_1"]["courante"] = 300.0   # ample : ratio de spend = 1.0
    return gs, Engine(gs)


# ---------------------------------------------------------------------------
# 1. Sanity catalogue + germination
# ---------------------------------------------------------------------------
def test_catalogue_germination():
    print("\n[1] sanity catalogue : ble/chanvre/sapin germent et dépassent le semis")
    check("ble présent/correct dans PLANT_CATALOGUE", PLANT_CATALOGUE.get("ble") is Wheat)
    check("chanvre présent/correct dans PLANT_CATALOGUE", PLANT_CATALOGUE.get("chanvre") is Hemp)
    check("sapin présent/correct dans PERENNIAL_CATALOGUE",
          PERENNIAL_CATALOGUE.get("sapin") is FirTree)

    tile = Tile(tile_id="MU", soil_type="terre", grid_rows=6, grid_cols=10)
    eco = init_eco("MU", 6, 10, humidite=1.5, fertilite=1.2, microbiome=0.3)
    gs, engine = _engine_with(tile, eco)
    especes = {"ble": Wheat, "chanvre": Hemp, "sapin": FirTree}
    posees = {cle: tile.add_plant(klass, 1 + i, 1 + i)
              for i, (cle, klass) in enumerate(especes.items())}
    for _ in range(12):
        engine.tick_semaine()
    for cle, inst in posees.items():
        # arbre = stade unique perpétuel (current_stage reste 0) ; on vérifie la
        # VIE + une croissance (hauteur > semis) pour le sapin, le stade pour les annuelles.
        if cle == "sapin":
            check(f"{cle} vivant et grandit", inst.is_alive and inst.current_height > 5.0,
                  f"h={inst.current_height:.0f} cm")
        else:
            check(f"{cle} vivant et au-delà du semis",
                  inst.is_alive and inst.current_stage >= 1, f"stade {inst.stage.name}")


# ---------------------------------------------------------------------------
# 2. Nature de mulch déclarée + existante
# ---------------------------------------------------------------------------
def test_nature_mulch():
    print("\n[2] nature de mulch : blé/chanvre → paille, sapin → aiguilles")
    check("blé mulch_source = paille", Wheat.mulch_source == "paille")
    check("chanvre mulch_source = paille", Hemp.mulch_source == "paille")
    check("sapin mulch_source = aiguilles", FirTree.mulch_source == "aiguilles")
    check("paille est une nature connue", "paille" in NATURES_MULCH)
    check("aiguilles est une nature connue", "aiguilles" in NATURES_MULCH)
    check("aiguilles acidifie (ph_shift < 0)", NATURES_MULCH["aiguilles"]["ph_shift"] < 0.0)


# ---------------------------------------------------------------------------
# 3. Interconnexion récolte → stock ; broyage sapin → BRF
# ---------------------------------------------------------------------------
def test_recolte_et_broyage():
    print("\n[3] récolte → stock (paille/aiguilles) ; broyage du sapin mort → BRF")
    tile = Tile(tile_id="RC", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = init_eco("RC", 6, 6, humidite=1.5, fertilite=1.2, microbiome=0.3)
    gs, _ = _engine_with(tile, eco)

    ble = tile.add_plant(Wheat, 1, 1)
    ble.current_stage = len(Wheat.growth_stages) - 1     # mature
    p0 = ACT.mulch_stock(gs)["paille"]
    g_ble = ACT.recolter_paille(gs, "joueur_1", ble, eco)
    check("récolte du blé crédite la paille",
          g_ble > 0.0 and ACT.mulch_stock(gs)["paille"] > p0, f"+{g_ble:.2f}")

    chanvre = tile.add_plant(Hemp, 2, 2)
    chanvre.current_stage = len(Hemp.growth_stages) - 1
    p1 = ACT.mulch_stock(gs)["paille"]
    g_ch = ACT.recolter_paille(gs, "joueur_1", chanvre, eco)
    check("récolte du chanvre crédite la paille",
          g_ch > 0.0 and ACT.mulch_stock(gs)["paille"] > p1, f"+{g_ch:.2f}")

    sapin = tile.add_plant(FirTree, 3, 3)
    a0 = ACT.mulch_stock(gs)["aiguilles"]
    g_sa = ACT.recolter_paille(gs, "joueur_1", sapin, eco)
    check("récolte du sapin crédite les aiguilles",
          g_sa > 0.0 and ACT.mulch_stock(gs)["aiguilles"] > a0, f"+{g_sa:.2f}")

    # Broyage : le sapin est ligneux (age_curve) → sa mort réserve du `bois_restant`
    # (perturbations.deposer_mort, gate `age_curve`) → broyer le squelette → BRF.
    from sim.effects.perturbations import deposer_mort
    mort = tile.add_plant(FirTree, 4, 4)
    mort.current_stage = 0
    mort.age_years = 30.0                                # sujet établi → bois à fragmenter
    deposer_mort(mort, eco)
    check("sapin mort → réservoir de bois (ligneux)", mort.bois_restant > 0.0,
          f"bois={mort.bois_restant:.2f}")
    b0 = ACT.mulch_stock(gs)["brf"]
    g_brf = ACT.broyer(gs, "joueur_1", mort, eco)
    check("broyer le sapin mort crédite du BRF",
          g_brf > 0.0 and ACT.mulch_stock(gs)["brf"] > b0, f"+{g_brf:.2f}")


# ---------------------------------------------------------------------------
# 4. Voix encyclopédie (fiche 3 niveaux) — spécifique aux 3 espèces
# ---------------------------------------------------------------------------
def test_voix_encyclopedie():
    print("\n[4] voix encyclopédie : fiche 3 niveaux non vides pour les 3 espèces")
    for cle in ("ble", "chanvre", "sapin"):
        f = FICHES.get(cle)
        ok = f is not None and set(f) == {1, 2, 3} and all(f[n].strip() for n in (1, 2, 3))
        check(f"{cle} : fiche encyclopédie 3 niveaux non vides", ok)


def main():
    test_catalogue_germination()
    test_nature_mulch()
    test_recolte_et_broyage()
    test_voix_encyclopedie()

    print("\n" + "=" * 60)
    total = len(_results)
    ok = sum(1 for _, c in _results if c)
    for name, cond in _results:
        if not cond:
            print(f"  ÉCHEC : {name}")
    print(f"RÉSULTAT : {ok}/{total} vérifications passées")
    if ok == total:
        print("[catalogue_mulch] PASS")
        return 0
    print("[catalogue_mulch] FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
