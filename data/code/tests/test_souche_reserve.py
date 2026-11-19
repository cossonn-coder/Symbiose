"""
SYMBIOSE — tests/test_souche_reserve.py
Test ciblé, lancé À LA DEMANDE (hors smoke test). Sprint PLANTE VIVANTE ④ (D140 G).

La souche ne rejette qu'avec la réserve qu'elle a mise de côté, et un rejet n'a pas
de souche propre avant `AGE_SOUCHE_PROPRE` ans (`sim/souche.py`,
`docs/vegetal/sante/conception_plante_vivante.md` §6) :
  (a) chêne mort (coupé) → ≤ N_REJETS_MAX rejets AU TOTAL sur 3 ans, même si TOUS
      les rejets meurent à mesure (plus de cascade rejet → mort → rejets) ;
  (b) un rejet de 5 ans qui meurt PEUT rejeter (il a sa souche) ;
  (c) chêne mort de faim (réserves vides) → 0 rejet ;
  (d) réserve faible → moins de rejets (N = réserve // COUT_REJET), réserve débitée ;
  (e) rejets portés par la souche : ils démarrent réserves pleines ;
  (f) perte de couronne d'un arbre vivant : la vague puise ≤ ½ de ses réserves,
      l'arbre reste vivant.

Lancement (depuis data/code/) :
  python3 -m tests.test_souche_reserve
"""

import sys

from world import Tile
from fields import init_eco
from plants import OakTree
from plants.physiologie import capacite_reserve
from sim.effects import deposer_mort
from sim.effects.perturbations import AGE_SOUCHE_PROPRE
from sim.souche import (emettre_rejets_souche, nombre_rejets, N_REJETS_MAX,
                        COUT_REJET, SEUIL_PERTE_COURONNE)

SEED = 42
S_PRINTEMPS = 5          # une semaine de printemps (wiy 5)


def _monde():
    """Un chêne mûr au centre d'une tuile 20×20, réserves pleines."""
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=20, grid_cols=20)
    eco = init_eco("T0", 20, 20, humidite=1.0, fertilite=1.0, microbiome=0.3)
    chene = tile.add_plant(OakTree, 10, 10)
    chene.age_years = OakTree.maturity_years + 20.0
    return tile, eco, chene


def _couper(plant, eco):
    """Destruction (geste, gel, vent) : `vitalite = 0` puis dépôt du mort."""
    plant.vitalite = 0.0
    deposer_mort(plant, eco)


def _vivants(tile, sauf):
    return [p for p in tile.plants if p is not sauf and p.is_alive]


def test_pas_de_cascade():
    tile, eco, chene = _monde()
    _couper(chene, eco)
    total = 0
    for wk in range(S_PRINTEMPS, S_PRINTEMPS + 3 * 52):
        avant = {id(p) for p in tile.plants}
        emettre_rejets_souche(tile, SEED, wk)
        neufs = [p for p in tile.plants if id(p) not in avant]
        total += len(neufs)
        for p in neufs:                           # chaque rejet meurt aussitôt
            p.age_years = 1.0
            _couper(p, eco)
    assert 1 <= total <= N_REJETS_MAX, f"{total} rejets au total"
    print(f"[réserve (a)] PASS — chêne coupé : {total} rejets au total en 3 ans, "
          f"tous morts jeunes, aucun n'a rejeté")


def test_rejet_etabli_rejette():
    tile, eco, chene = _monde()
    _couper(chene, eco)
    emettre_rejets_souche(tile, SEED, S_PRINTEMPS)
    rejet = _vivants(tile, chene)[0]
    rejet.age_years = 5.0
    assert rejet.age_years >= AGE_SOUCHE_PROPRE
    _couper(rejet, eco)
    assert rejet.souche_vivante and rejet.reserve_souche > 0.0, \
        f"souche {rejet.souche_vivante}, réserve {rejet.reserve_souche:.2f}"
    log = emettre_rejets_souche(tile, SEED, S_PRINTEMPS + 52)
    assert any(f"souche de @{rejet.position}" in l for l in log), log
    print(f"[réserve (b)] PASS — rejet de 5 ans coupé, il rejette : "
          f"{[l.strip() for l in log if str(rejet.position) in l][0]}")


def test_famine_sans_rejet():
    tile, eco, chene = _monde()
    chene.reserves = 0.0                          # mort de faim : rien de côté
    deposer_mort(chene, eco)
    n = sum(len(emettre_rejets_souche(tile, SEED, wk)) for wk in range(S_PRINTEMPS, 60))
    assert chene.reserve_souche == 0.0 and n == 0 and not _vivants(tile, chene)
    print("[réserve (c)] PASS — chêne mort de faim : 0 rejet")


def test_reserve_limite():
    tile, eco, chene = _monde()
    cap = capacite_reserve(chene)
    chene.reserves = 1.5 * COUT_REJET / cap       # de quoi payer UN rejet
    chene.vitalite = 0.0
    deposer_mort(chene, eco)
    emettre_rejets_souche(tile, SEED, S_PRINTEMPS)
    n = len(_vivants(tile, chene))
    assert n == 1 < nombre_rejets(OakTree), f"{n} rejet(s)"
    assert abs(chene.reserve_souche - 0.5 * COUT_REJET) < 1e-9, chene.reserve_souche
    print(f"[réserve (d)] PASS — réserve {1.5 * COUT_REJET:.1f} sem : 1 rejet "
          f"(au lieu de {nombre_rejets(OakTree)}), reste {chene.reserve_souche:.1f} sem")


def test_rejets_portes():
    tile, eco, chene = _monde()
    _couper(chene, eco)
    emettre_rejets_souche(tile, SEED, S_PRINTEMPS)
    rejets = _vivants(tile, chene)
    assert rejets and all(p.reserves == 1.0 for p in rejets), \
        [p.reserves for p in rejets]
    print(f"[réserve (e)] PASS — {len(rejets)} rejets, réserves pleines "
          f"({capacite_reserve(rejets[0]):.1f} sem chacun)")


def test_perte_couronne_puise():
    tile, eco, chene = _monde()
    chene.reserves = 0.3
    chene.perte_couronne = 1.0
    cap = capacite_reserve(chene)
    emettre_rejets_souche(tile, SEED, S_PRINTEMPS)
    n = len(_vivants(tile, chene))
    attendu = min(nombre_rejets(OakTree), int(0.5 * 0.3 * cap // COUT_REJET))
    assert n == attendu and chene.is_alive, f"{n} rejets (attendu {attendu})"
    assert abs(chene.reserves - (0.3 - n * COUT_REJET / cap)) < 1e-9
    assert chene.reserves >= 0.15 - 1e-9, "a puisé plus de la moitié"
    print(f"[réserve (f)] PASS — couronne perdue (seuil {SEUIL_PERTE_COURONNE}), "
          f"réserves 0,30 → {chene.reserves:.2f} pour {n} rejet(s), arbre vivant")


if __name__ == "__main__":
    tests = [test_pas_de_cascade, test_rejet_etabli_rejette, test_famine_sans_rejet,
             test_reserve_limite, test_rejets_portes, test_perte_couronne_puise]
    echecs = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            echecs += 1
            print(f"[réserve] FAIL {t.__name__} : {e}")
    sys.exit(1 if echecs else 0)
