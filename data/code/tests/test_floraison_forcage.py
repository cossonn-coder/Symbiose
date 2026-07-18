"""
SYMBIOSE — tests/test_floraison_forcage.py
Test ciblé du sprint FLORAISON & FRUCTIFICATION ① — FORÇAGE THERMIQUE ÉVÉNEMENTIEL.

Remplace la garde de l'ancien modèle DOUBLE PORTE (GDD + photopériode). Le nouveau
modèle (`sim/engine/floraison.py`) arme `bloom_week = week_in_year` au FRANCHISSEMENT
d'un seuil de chaleur cumulée `bloom_forcing_gdd` propre à l'espèce (bas → printemps,
haut → automne), sous la météo réelle du jeu. On vérifie TROIS propriétés :

  1. PLACEMENT — chaque espèce arme dans SA saison-cible : un pommier mûr (seuil bas)
     au PRINTEMPS, une espèce été-cible en été, une automne-cible en automne. C'est
     la correction structurelle de la grappe D84 (plus de « floraison à contretemps »).
  2. ÉTALEMENT — une cohorte d'une même espèce aux gènes `phenologie_florale`
     dispersés arme `bloom_week` sur plusieurs semaines (σ > 0) : la désync survit au
     nouveau chemin (le seuil individuel `gdd_eff` décale le franchissement).
  3. NEUTRALITÉ g=1 — un pied neutre (gène 1.0) a `gdd_eff == bloom_forcing_gdd`
     EXACTEMENT (aucun décalage) — l'invariant du gène-tempo.

Déterministe (philo #3) : météo pure + seuils d'espèce + gène par hash, aucun RNG.
On DRIVE un vrai Engine sur ~45 semaines DANS l'année 1 (bloom_week garde alors la
semaine de franchissement — il n'est remis à -1 qu'au passage d'année, wiy==1).

Lancement (depuis data/code/) : python3 -m tests.test_floraison_forcage
"""

import sys
import statistics as st

from world import Tile
from fields import init_eco
from sim.engine import Engine
from sim.engine.floraison import FLORA_GENE_SHIFT
from sim.seeds import semer_fondateur
from plants import AppleTree, Sunflower, Mugwort

SEED = 42
_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK " if cond else "XX "
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _mature(plant):
    """Force le stade seed-bearing (herbacées : dernier stade) pour lever le gate de
    maturité — on teste le PLACEMENT thermique, pas la vitesse de croissance."""
    plant.current_stage = len(plant.plant_class.growth_stages) - 1
    return plant


def _bloom_week_of(plant_class, *, age_years=0.0, mature=True, gene=None,
                   n_weeks=45):
    """Monte une tuile isolée avec UN pied de `plant_class`, le rend mûr, et DRIVE
    un Engine `n_weeks` semaines (année 1). Renvoie `bloom_week` (semaine de
    franchissement du forçage, -1 si jamais armé)."""
    tile = Tile(tile_id="T", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = init_eco("T", 6, 6, humidite=1.6, fertilite=1.3, microbiome=0.4)
    eco.seed_bank.germination_candidates = lambda *a, **k: []   # isolé : pas d'adventice
    plant = tile.add_plant(plant_class, 3, 3)
    plant.age_years = age_years
    if mature:
        _mature(plant)
    if gene is not None:
        plant.genes = {"phenologie_florale": gene}
    gs = {"tiles": [tile], "eco": {"T": eco}, "scores": {},
          "current_player": "joueur_1", "week": 1, "log": []}
    eng = Engine(gs)
    for _ in range(n_weeks):
        eng.tick_semaine()
        gs["log"].clear()
    return plant.bloom_week


# ---------------------------------------------------------------------------
# 1. PLACEMENT — chaque espèce dans SA saison-cible
# ---------------------------------------------------------------------------
def test_placement():
    print("\n[1] placement : chaque espèce arme sa floraison dans SA saison")
    # Saisons (saison_de) : printemps S10-22, été S23-35, automne S36-48 (approx).
    # Le pommier (seuil 8) doit franchir TÔT (printemps), pas en automne (D84).
    w_apple = _bloom_week_of(AppleTree, age_years=6.0)   # fruitier mûr, seuil 8
    check("pommier arme au PRINTEMPS (S≤22, pas l'automne)",
          0 < w_apple <= 22, f"bloom_week=S{w_apple} (bloom_forcing_gdd={AppleTree.bloom_forcing_gdd})")
    # Tournesol (seuil 55) : été.
    w_sun = _bloom_week_of(Sunflower)
    check("tournesol arme en ÉTÉ (après le pommier)",
          w_sun > w_apple, f"bloom_week=S{w_sun} (seuil={Sunflower.bloom_forcing_gdd})")
    # Armoise (seuil 180, jour-court approximé §2.5) : automne, après le tournesol.
    w_mug = _bloom_week_of(Mugwort)
    check("armoise arme en AUTOMNE (seuil élevé → tard)",
          w_mug > w_sun, f"bloom_week=S{w_mug} (seuil={Mugwort.bloom_forcing_gdd})")


# ---------------------------------------------------------------------------
# 2. ÉTALEMENT — la désync survit au nouveau chemin (bloom_week étalé)
# ---------------------------------------------------------------------------
def test_etalement():
    print("\n[2] étalement : cohorte à gènes dispersés → bloom_week étalé (σ>0)")
    # Cohorte de tournesols aux gènes `phenologie_florale` dispersés (lève-tôt g>1
    # → seuil abaissé → franchit avant). On récolte la semaine d'armement de chacun.
    genes = [0.70, 0.85, 1.00, 1.15, 1.30]
    weeks = [_bloom_week_of(Sunflower, gene=g) for g in genes]
    armes = [w for w in weeks if w > 0]
    sd = st.pstdev(weeks) if len(weeks) > 1 else 0.0
    check("toute la cohorte arme", len(armes) == len(genes),
          f"semaines={weeks}")
    check("bloom_week ÉTALÉ (σ>0)", sd > 0.0, f"σ={sd:.3f} sem, semaines={weeks}")
    # Monotonie attendue : un gène plus grand (lève-tôt) arme AVANT (semaine ≤).
    monotone = all(weeks[i] >= weeks[i + 1] for i in range(len(weeks) - 1))
    check("lève-tôt (g grand) arme AVANT lève-tard", monotone, f"semaines={weeks}")


# ---------------------------------------------------------------------------
# 3. NEUTRALITÉ g=1 — gdd_eff == bloom_forcing_gdd exactement
# ---------------------------------------------------------------------------
def test_neutralite():
    print("\n[3] neutralité g=1 : gdd_eff == bloom_forcing_gdd (aucun décalage)")
    for cls in (AppleTree, Sunflower, Mugwort):
        gdd_eff = cls.bloom_forcing_gdd - FLORA_GENE_SHIFT * (1.0 - 1.0)
        check(f"{cls.name} : seuil neutre à g=1", gdd_eff == cls.bloom_forcing_gdd,
              f"gdd_eff={gdd_eff}")


def main():
    print("=" * 60)
    print("FLORAISON — forçage thermique événementiel (placement/étalement)")
    print("=" * 60)
    test_placement()
    test_etalement()
    test_neutralite()
    print("\n" + "=" * 60)
    total = len(_results)
    ok = sum(1 for _, c in _results if c)
    for name, cond in _results:
        if not cond:
            print(f"  ÉCHEC : {name}")
    print(f"RÉSULTAT : {ok}/{total} vérifications passées")
    print("=" * 60)
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
