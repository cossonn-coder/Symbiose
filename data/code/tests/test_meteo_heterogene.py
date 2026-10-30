"""
SYMBIOSE — tests/test_meteo_heterogene.py
Impact météo SPATIALEMENT hétérogène (sprint effondrement météo ①).

Un événement météo reste GLOBAL (un seul tirage), mais son IMPACT est désormais
hétérogène au plot : sous un même hiver catastrophe, un coin abrité tient, un coin
exposé flanche (philo #7 — le jardin ne meurt plus d'un bloc). On exerce le collapse
CONNU de la conception : seed 12345, année 5 semaine 10 (`week=218`), une grêle
d'intensité 2.0 (`scope="local"`). Avant ①, la grêle frappait les 8 secteurs à
l'identique (variance spatiale de survie nulle) ; désormais elle ne frappe qu'un
PATCH déterministe (`weather.patch_local`).

Deux propriétés vérifiées :
  1. Variance spatiale de survie > 0, CORRÉLÉE au patch (l'abrité hors patch garde
     un noyau vivant, l'exposé dans le patch s'effondre).
  2. Plancher de survie ∝ abri (Q2) : le paillage (protection médiée) remonte le
     plancher — un jardin protégé garde tous ses semis là où un jardin nu en perd.

Lancement : python3 -m tests.test_meteo_heterogene   (depuis data/code/)
"""

import statistics

from world import Tile
from plants import Basil
from fields import init_eco
from sim.engine import Engine
from sim.seeds import semer_fondateur
from sim.weather import patch_local

SEED = 12345          # seed du collapse connu (conception §0/§1.3)
WEEK = 218           # année 5, semaine 10 → Grêle i=2.0 scope="local" (D122 ③ : ex-1310)
ROWS, COLS = 16, 11   # tuile du scénario de conception


def _tuile_semee(paillage: int = 0):
    """Tuile ROWS×COLS nue, un semis de Basilic sur CHAQUE plot (tissu tendre,
    stade « semis » → cible de la grêle). `paillage` rondelles posées = abri
    homogène (protection médiée, tile-level). Renvoie (tile, eco, plants)."""
    tile = Tile(tile_id="TX", soil_type="terre",
                grid_rows=ROWS, grid_cols=COLS, origin_x_cm=0.0, origin_y_cm=0.0)
    eco = init_eco("TX", ROWS, COLS, humidite=1.5, fertilite=1.0,
                   microbiome=0.3, soil_type="terre", heterogene=True)
    plants = [semer_fondateur(tile, Basil, r, c, 42)
              for r in range(ROWS) for c in range(COLS)]
    for _ in range(paillage):
        tile.stakes[0].add("paillage")
    return tile, eco, plants


def _collapse(paillage: int = 0):
    """Joue LE tick du collapse (seed 12345, week 218) et renvoie la liste des
    instances plantées (on garde les références : un mort est retiré de la tuile
    mais son `is_alive` reste False sur l'objet)."""
    tile, eco, plants = _tuile_semee(paillage)
    game_state = {"tiles": [tile], "eco": {"TX": eco}, "scores": {},
                  "current_player": "j", "week": WEEK, "log": [], "seed": SEED}
    Engine(game_state).tick_semaine()
    return plants


def test_grele_patch_variance_spatiale():
    """La grêle locale frappe un PATCH : survie spatialement structurée."""
    plants = _collapse(paillage=0)
    dans_patch = patch_local(SEED, WEEK, ROWS, COLS)
    dedans = [p for p in plants if dans_patch(*p.position)]
    dehors = [p for p in plants if not dans_patch(*p.position)]

    # Le patch est un vrai SOUS-ensemble (ni toute la tuile, ni rien).
    assert dedans and dehors, "le patch doit partitionner la tuile"

    surv_in  = sum(p.is_alive for p in dedans) / len(dedans)
    surv_out = sum(p.is_alive for p in dehors) / len(dehors)

    # Cœur de ① : l'abrité (hors patch) survit MIEUX que l'exposé (dans patch).
    assert surv_out > surv_in, (
        f"survie hors patch {surv_out:.0%} devrait dépasser dans patch {surv_in:.0%}")
    # Un noyau vivant subsiste (récupérable, philo #4) ET des pertes existent
    # (l'effondrement est réel) → ce n'est ni « tout meurt » ni « rien ne bouge ».
    assert any(p.is_alive for p in dehors), "l'abri doit garder un noyau vivant"
    assert any(not p.is_alive for p in dedans), "l'exposé doit encaisser des pertes"

    # Variance spatiale de survie STRICTEMENT positive (avant ① : ~0, uniforme).
    survie = [1.0 if p.is_alive else 0.0 for p in plants]
    assert statistics.pvariance(survie) > 0.0

    # Déterminisme (philo #3) : rejouer donne exactement le même verdict.
    plants2 = _collapse(paillage=0)
    assert [p.is_alive for p in plants2] == [p.is_alive for p in plants]


def test_plancher_survie_proportionnel_abri():
    """Q2 — le plancher de survie ÉMERGE de l'abri : le paillage (protection
    médiée) sauve des semis qu'un sol nu perd. Aucun chiffre gravé : on vérifie
    seulement la MONOTONIE (plus d'abri → plus de survivants)."""
    nus     = sum(p.is_alive for p in _collapse(paillage=0))
    abrites = sum(p.is_alive for p in _collapse(paillage=3))
    assert abrites > nus, (
        f"le paillage devrait remonter le plancher : abrités {abrites} > nus {nus}")


def main():
    test_grele_patch_variance_spatiale()
    test_plancher_survie_proportionnel_abri()
    print("[meteo_heterogene] PASS — grêle patchée + plancher ∝ abri")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
