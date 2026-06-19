"""
SYMBIOSE — tests/test_faune_dediee.py
Tronçons ④b/④c (catalogue enrichi) — scission des champs uniques `ravageur` puis
`auxiliaire` en espèces NOMMÉES (modèle B, CONCEPTION_FAUNE_DEDIEE.md §2) :
  ④b ravageur  → puceron / limace / doryphore
  ④c auxiliaire → coccinelle / chrysope / carabe / merle / hérisson

Garde-fous de la SCISSION (indépendants du hash golden) :
  1. EXISTENCE  — les espèces sont des champs distincts, tous de la bonne catégorie,
     chacun porte SA triade (resource_fn/habitat_fn/predators non partagés).
  2. AGRÉGAT    — `category_density(cat)` == somme des densités (la guilde devient une
     VUE ; c'est ce que lisent l'herbivorie C1 et la régulation des ravageurs).
  3. FENÊTRES   — puceron/doryphore estivaux (daylen 10/13) ; limace plus précoce
     et large (9/12), car humide/frais.
  4. DORYPHORE SPÉCIALISTE — sa ressource (`_foliage_solanaceae_grid`) et son habitat
     (`_solanaceae_grid`) sont NULS sans Solanaceae, et l'habitat est RÉDUIT par l'ail
     (Amaryllidaceae répulsif, §4.4).
  5. LIMACE DÉTRITIVORE — `_limace_food_grid` répond surtout à la litière (poids
     dominant) et secondairement au feuillage tendre.
  6. AUXILIAIRES NOMMÉS (④c) — 5 espèces de catégorie `auxiliaire` ; proies propres
     (coccinelle/chrysope sur puceron, carabe/hérisson sur limace) ; habitats sur
     STRUCTURES (`pile` → carabe & hérisson montent) ; boucle proie↔prédateur active
     (les prédateurs nommés du ④b existent enfin comme champs).

Lancement (depuis data/code/) :
  python3 -m tests.test_faune_dediee
"""

import sys

from world import Tile
from plants import Tomato, Bean, Garlic
from fields import init_eco, build_population_specs, Structure
from fields.population import (
    _foliage_solanaceae_grid, _solanaceae_grid,
    _limace_food_grid, _litter_grid, _foliage_grid,
    _espece_grid, _undisturbed_structure_grid, _pile_grid, _undisturbed_grid,
    _base_habitat_grid, _merle_food_grid,
    LIMACE_LITTER_W, LIMACE_FOLIAGE_W, DORY_AIL_REPULSE,
    PILE_HABITAT_W, MERLE_BASE_HABITAT,
)

ROWS, COLS = 6, 8
RAVAGEURS = ("puceron", "limace", "doryphore")
AUXILIAIRES = ("coccinelle", "chrysope", "carabe", "merle", "herisson")


def _eco(plants_specs=()):
    """Eco + tuile, avec d'éventuelles plantes MÛRES (stade foliaire) posées."""
    tile = Tile(tile_id="TF", soil_type="terre")
    eco = init_eco("TF", ROWS, COLS, humidite=1.5, fertilite=1.0, microbiome=0.3)
    for (cls, r, c) in plants_specs:
        p = tile.add_plant(cls, r, c)
        p.current_stage = len(p.plant_class.growth_stages) - 1   # maturité
    return tile, eco


def _check(cond, label):
    print(f"[faune] {'OK' if cond else 'ÉCHEC'} : {label}")
    if not cond:
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# 1. EXISTENCE — 3 espèces, même catégorie, triades distinctes
# ---------------------------------------------------------------------------

def test_trois_ravageurs_nommes():
    specs = {s.name: s for s in build_population_specs()}
    for nom in RAVAGEURS:
        _check(nom in specs, f"l'espèce `{nom}` existe comme spec")
        _check(specs[nom].category == "ravageur",
               f"`{nom}` est rattaché à la catégorie ravageur")
    # Triades PROPRES : les resource_fn ne sont pas toutes le même objet.
    res_fns = {specs[n].resource_fn for n in RAVAGEURS}
    _check(len(res_fns) == 3, "chaque ravageur a SA resource_fn (modèle B)")
    # Prédateurs propres (puceron/limace/doryphore ≠ listes identiques).
    preds = {specs[n].predators for n in RAVAGEURS}
    _check(len(preds) == 3, "chaque ravageur a SES prédateurs nommés")

    tile, eco = _eco()
    membres = {f.spec.name for f in eco.category_fields("ravageur")}
    _check(membres == set(RAVAGEURS),
           f"category_fields('ravageur') == 3 espèces (vu {sorted(membres)})")


# ---------------------------------------------------------------------------
# 2. AGRÉGAT — la guilde devient une VUE (somme)
# ---------------------------------------------------------------------------

def test_category_density_est_la_somme():
    tile, eco = _eco()
    eco.populations["puceron"].set(2, 3, 0.20)
    eco.populations["limace"].set(2, 3, 0.10)
    eco.populations["doryphore"].set(2, 3, 0.05)
    somme = eco.category_density("ravageur", 2, 3)
    _check(abs(somme - 0.35) < 1e-9,
           f"category_density == puceron+limace+doryphore (={somme:.3f})")
    _check(abs(eco.category_density("ravageur", 0, 0)) < 1e-9,
           "category_density nulle là où aucun ravageur n'est posé")


# ---------------------------------------------------------------------------
# 3. FENÊTRES photopériodiques
# ---------------------------------------------------------------------------

def test_fenetres_par_espece():
    specs = {s.name: s for s in build_population_specs()}
    _check(specs["puceron"].daylen_min == 10.0 and specs["puceron"].daylen_full == 13.0,
           "puceron : fenêtre estivale 10/13")
    _check(specs["doryphore"].daylen_min == 10.0 and specs["doryphore"].daylen_full == 13.0,
           "doryphore : fenêtre estivale 10/13")
    _check(specs["limace"].daylen_min == 9.0 and specs["limace"].daylen_full == 12.0,
           "limace : fenêtre plus précoce/large 9/12 (humide-frais)")


# ---------------------------------------------------------------------------
# 4. DORYPHORE — spécialiste Solanaceae, réduit par l'ail
# ---------------------------------------------------------------------------

def _grid_nonzero(g):
    return any(g[r][c] > 0.0 for r in range(ROWS) for c in range(COLS))


def test_doryphore_nul_sans_solanaceae():
    # Une plante NON-Solanaceae (Bean = Fabaceae) → ressource/habitat doryphore nuls.
    tile, eco = _eco([(Bean, 2, 2)])
    res = _foliage_solanaceae_grid(eco, tile, tile.plants)
    hab = _solanaceae_grid(eco, tile, tile.plants)
    _check(not _grid_nonzero(res), "ressource doryphore NULLE sans Solanaceae")
    _check(not _grid_nonzero(hab), "habitat doryphore NUL sans Solanaceae")
    # Avec une tomate (Solanaceae) mûre → la ressource s'allume sur son feuillage.
    tile2, eco2 = _eco([(Tomato, 2, 2)])
    res2 = _foliage_solanaceae_grid(eco2, tile2, tile2.plants)
    _check(_grid_nonzero(res2), "ressource doryphore > 0 avec une Solanaceae mûre")


def test_doryphore_habitat_reduit_par_ail():
    # Tomate seule vs tomate + ail co-localisés : l'habitat doit BAISSER avec l'ail.
    tile_s, eco_s = _eco([(Tomato, 2, 2)])
    hab_s = _solanaceae_grid(eco_s, tile_s, tile_s.plants)
    tile_a, eco_a = _eco([(Tomato, 2, 2), (Garlic, 2, 2)])
    hab_a = _solanaceae_grid(eco_a, tile_a, tile_a.plants)
    pic_s = max(hab_s[r][c] for r in range(ROWS) for c in range(COLS))
    pic_a = max(hab_a[r][c] for r in range(ROWS) for c in range(COLS))
    _check(pic_s > 0.0, "habitat doryphore présent sur la tomate seule")
    _check(pic_a < pic_s, f"ail répulsif → habitat réduit ({pic_a:.3f} < {pic_s:.3f})")


# ---------------------------------------------------------------------------
# 5. LIMACE — litière dominante sur le feuillage
# ---------------------------------------------------------------------------

def test_limace_litiere_dominante():
    _check(LIMACE_LITTER_W > LIMACE_FOLIAGE_W,
           f"poids litière ({LIMACE_LITTER_W}) > poids feuillage ({LIMACE_FOLIAGE_W})")
    # Dépose de la litière (feuilles) sur un plot vide → la ressource limace monte,
    # tirée par la litière (le feuillage vivant y est nul, aucune plante).
    tile, eco = _eco()
    eco.deposer_litiere(3, 4, "feuille", 2.0)
    food = _limace_food_grid(eco, tile, tile.plants)
    litter = _litter_grid(eco, tile, tile.plants)
    _check(food[3][4] > 0.0, "ressource limace > 0 là où il y a de la litière")
    _check(litter[3][4] > 0.0, "litière comptée hors fruit (feuille)")
    _check(abs(food[3][4] - LIMACE_LITTER_W * litter[3][4]) < 1e-9,
           "sans feuillage vivant, la ressource limace == poids·litière (litière seule)")


# ---------------------------------------------------------------------------
# 6. AUXILIAIRES NOMMÉS (④c) — 5 espèces, proies propres, habitats structures
# ---------------------------------------------------------------------------

def test_cinq_auxiliaires_nommes():
    specs = {s.name: s for s in build_population_specs()}
    for nom in AUXILIAIRES:
        _check(nom in specs, f"l'espèce `{nom}` existe comme spec")
        _check(specs[nom].category == "auxiliaire",
               f"`{nom}` est rattaché à la catégorie auxiliaire")
    # Triades PROPRES : pas une seule resource_fn ni un seul habitat partagés.
    res_fns = {specs[n].resource_fn for n in AUXILIAIRES}
    hab_fns = {specs[n].habitat_fn for n in AUXILIAIRES}
    _check(len(res_fns) >= 3, "les auxiliaires ne partagent pas tous la même proie")
    _check(len(hab_fns) >= 4, "les auxiliaires ont des habitats distincts (modèle B)")

    tile, eco = _eco()
    membres = {f.spec.name for f in eco.category_fields("auxiliaire")}
    _check(membres == set(AUXILIAIRES),
           f"category_fields('auxiliaire') == 5 espèces (vu {sorted(membres)})")


def test_proies_des_predateurs():
    # coccinelle/chrysope mangent le PUCERON (`_espece_grid('puceron')`) ;
    # carabe/hérisson mangent la LIMACE. Sans proie posée → ressource NULLE ;
    # proie posée → la ressource s'allume EXACTEMENT au plot de la proie.
    tile, eco = _eco()
    food_p = _espece_grid("puceron")(eco, tile, tile.plants)
    food_l = _espece_grid("limace")(eco, tile, tile.plants)
    _check(not _grid_nonzero(food_p), "ressource coccinelle/chrysope nulle sans puceron")
    _check(not _grid_nonzero(food_l), "ressource carabe/hérisson nulle sans limace")
    eco.populations["puceron"].set(1, 1, 0.30)
    eco.populations["limace"].set(4, 5, 0.20)
    food_p = _espece_grid("puceron")(eco, tile, tile.plants)
    food_l = _espece_grid("limace")(eco, tile, tile.plants)
    _check(abs(food_p[1][1] - 0.30) < 1e-9 and abs(food_p[4][5]) < 1e-9,
           "ressource puceron-mangeur = densité de puceron, au plot du puceron")
    _check(abs(food_l[4][5] - 0.20) < 1e-9 and abs(food_l[1][1]) < 1e-9,
           "ressource limace-mangeur = densité de limace, au plot de la limace")


def test_habitats_structures_pile():
    # Le carabe (`_undisturbed_structure_grid`) et le hérisson (`_pile_grid`)
    # montent là où une STRUCTURE `pile` (bois mort, ⑤) est posée. À zéro
    # structure → carabe = sol non perturbé, hérisson = nul partout (golden NEUTRE).
    tile, eco = _eco()
    her0 = _pile_grid(eco, tile, tile.plants)
    car0 = _undisturbed_structure_grid(eco, tile, tile.plants)
    base = _undisturbed_grid(eco, tile, tile.plants)
    _check(not _grid_nonzero(her0), "hérisson : habitat NUL sans pile (dépend de l'aménagement)")
    _check(all(abs(car0[r][c] - base[r][c]) < 1e-9 for r in range(ROWS) for c in range(COLS)),
           "carabe sans pile : habitat == sol non perturbé (aucun bump)")
    eco.structures.append(Structure(kind="pile", plot=(3, 4)))
    her1 = _pile_grid(eco, tile, tile.plants)
    car1 = _undisturbed_structure_grid(eco, tile, tile.plants)
    _check(abs(her1[3][4] - PILE_HABITAT_W) < 1e-9 and not _grid_nonzero(
               [[her1[r][c] if (r, c) != (3, 4) else 0.0 for c in range(COLS)]
                for r in range(ROWS)]),
           f"pile posée → hérisson monte au plot (={her1[3][4]:.2f}), nul ailleurs")
    _check(car1[3][4] > car0[3][4] - 1e-9 and car1[3][4] >= 1.0,
           "pile posée → carabe bumpe au plot (clampé à 1 sur sol déjà stable)")


def test_merle_omnivore_fruit_et_vers():
    # Merle (④c) : habitat plancher UNIFORME, mais NOURRITURE = fruit frais + vers.
    tile, eco = _eco()
    hab = _base_habitat_grid(eco, tile, tile.plants)
    _check(all(abs(hab[r][c] - MERLE_BASE_HABITAT) < 1e-9
               for r in range(ROWS) for c in range(COLS)),
           f"merle : habitat plancher uniforme (={MERLE_BASE_HABITAT})")
    food0 = _merle_food_grid(eco, tile, tile.plants)
    _check(not _grid_nonzero(food0), "merle : nourriture nulle sans fruit ni vers")
    # Pose des vers (catégorie détritivore) → la nourriture du merle monte au plot.
    eco.populations["vers_de_terre"].set(2, 2, 0.30)
    food1 = _merle_food_grid(eco, tile, tile.plants)
    _check(food1[2][2] > 0.0, "merle : nourriture > 0 là où il y a des vers (omnivore)")


def main():
    test_trois_ravageurs_nommes()
    test_category_density_est_la_somme()
    test_fenetres_par_espece()
    test_doryphore_nul_sans_solanaceae()
    test_doryphore_habitat_reduit_par_ail()
    test_limace_litiere_dominante()
    test_cinq_auxiliaires_nommes()
    test_proies_des_predateurs()
    test_habitats_structures_pile()
    test_merle_omnivore_fruit_et_vers()
    print("[faune] TOUS LES TESTS PASSENT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
