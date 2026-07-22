"""
SYMBIOSE — tests/test_faune_dediee.py
Tronçons ④b/④c/④d/④e (catalogue enrichi) — scission des champs uniques `ravageur`,
`auxiliaire` puis `vers_de_terre` en 10 espèces NOMMÉES (modèle B,
docs/faune/vie_macro/conception_faune_dediee.md §2) + métadonnée d'encyclopédie (④e) :
  ④b ravageur     → puceron / limace / doryphore
  ④c auxiliaire   → coccinelle / chrysope / carabe / merle / hérisson
  ④d detritivore  → lombric (humus du sol) / cloporte (litière)
  ④e métadonnée   → blurb + interconnexions par espèce (donnée pure, golden NEUTRE)

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
  7. COUVERTURE COMPLÈTE (④e) — exactement 10 espèces trophiques, catégories ∈
     {ravageur, auxiliaire, detritivore} chacune peuplée ; triade complète (resource_fn
     + habitat_fn callables, predators tous résolubles) ; salts distincts ; phénologie
     hivernale nulle (puceron/doryphore) vs lombric quasi annuel.
  8. MÉTADONNÉE ENCYCLO (④e) — chaque espèce a un blurb et des interconnexions ;
     `predators ⊆ interconnexions` ; le sous-graphe entre espèces nommées est SYMÉTRIQUE.

Lancement (depuis data/code/) :
  python3 -m tests.test_faune_dediee
"""

import sys

from world import Tile
from plants import Tomato, Bean, Garlic
from fields import init_eco, build_population_specs, Structure
from fields.lifecycle import larval_field_names
from fields.population import (
    _foliage_solanaceae_grid, _solanaceae_grid,
    _limace_food_grid, _litter_grid, _foliage_grid,
    _espece_grid, _undisturbed_structure_grid, _pile_grid, _undisturbed_grid,
    _base_habitat_grid, _merle_food_grid, _osmie_habitat_grid,
    _pollinisateur_habitat_grid, _proies_grid,
    daylength, _smoothstep, build_lifecycle_bridges,
    build_pollinator_registry, build_pollinator_specs, POLLINATOR_NAMES,
    LIMACE_LITTER_W, LIMACE_FOLIAGE_W, DORY_AIL_REPULSE,
    PILE_HABITAT_W, MERLE_BASE_HABITAT,
)

ROWS, COLS = 6, 8
RAVAGEURS = ("puceron", "limace", "doryphore")
AUXILIAIRES = ("coccinelle", "chrysope", "carabe", "merle", "herisson")
DETRITIVORES = ("lombric", "cloporte")
# Herbivore vertébré (sommet trophique ①) : 11ᵉ espèce trophique, catégorie NEUVE
# `herbivore_vertebre`. Ses prédateurs (rapace/couleuvre) arrivent au tronçon ②
# (`predators=()` ici) → il est HORS du sous-graphe symétrique tant qu'ils n'existent
# pas ; on l'exclut donc des vérifs de réciprocité (elles n'itèrent que ESPECES_QUATRE).
HERBIVORES_VERTEBRES = ("campagnol",)
# Super-prédateurs (sommet trophique ②) : catégorie NEUVE `super_predateur`. Ils
# ferment la chaîne par le haut (rapace→campagnol/merle, couleuvre→campagnol/limace).
# `predators=()` (ce sont les sommets) mais ils SONT dans le sous-graphe symétrique :
# leurs interconnexions listent leurs proies, réciproques des liens campagnol/merle/
# limace → la symétrie s'étend désormais à eux (ils ne sont plus forward-declarés).
SUPER_PREDATEURS = ("rapace", "couleuvre")
# Faune de mare (hydrologie ④) : catégorie NEUVE `aquatique`, mini-chaîne greffée
# sur l'eau stagnante (moustique proie → libellule prédateur). Elles SONT dans le
# sous-graphe symétrique (moustique cite libellule, libellule cite moustique).
FAUNE_MARE = ("moustique", "libellule")
ESPECES_QUATRE = RAVAGEURS + AUXILIAIRES + DETRITIVORES   # les 10 espèces de ④
# Toutes les espèces trophiques consommatrices : ④ (10) + campagnol (①) + sommet (②)
# + faune de mare (hydrologie ④) = 15
ESPECES = ESPECES_QUATRE + HERBIVORES_VERTEBRES + SUPER_PREDATEURS + FAUNE_MARE
CATEGORIES = ("ravageur", "auxiliaire", "detritivore",
              "herbivore_vertebre", "super_predateur", "aquatique")
# Tokens du graphe §3 qui ne sont PAS des espèces trophiques nommées (éléments du
# milieu + champ larvaire du pont ⑤) — admis dans `interconnexions`. `eau`/`marais`
# = la niche hydrique de la faune de mare (hydrologie ④).
_MILIEU_TOKENS = {"fruit", "pile", "ail", "eau", "marais"}


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
    # Pose du LOMBRIC (④d : le merle mange le ver, PAS le cloporte) → nourriture monte.
    eco.populations["lombric"].set(2, 2, 0.30)
    food1 = _merle_food_grid(eco, tile, tile.plants)
    _check(food1[2][2] > 0.0, "merle : nourriture > 0 là où il y a des lombrics (omnivore)")
    # Le cloporte (autre détritivore) ne nourrit PAS le merle (proie du carabe/hérisson).
    tile2, eco2 = _eco()
    eco2.populations["cloporte"].set(2, 2, 0.30)
    food2 = _merle_food_grid(eco2, tile2, tile2.plants)
    _check(not _grid_nonzero(food2), "merle : le cloporte seul ne le nourrit pas (vise le lombric)")


def test_deux_detritivores_nommes():
    # ④d : `vers_de_terre` scindé en lombric (humus du sol) + cloporte (litière).
    specs = {s.name: s for s in build_population_specs()}
    _check("lombric" in specs and specs["lombric"].category == "detritivore",
           "lombric : champ de catégorie detritivore")
    _check("cloporte" in specs and specs["cloporte"].category == "detritivore",
           "cloporte : champ de catégorie detritivore")
    _check("vers_de_terre" not in specs, "plus de champ `vers_de_terre` après ④d")
    # Prédateurs propres : lombric = merle/hérisson ; cloporte = carabe/hérisson.
    _check(specs["lombric"].predators == ("merle", "herisson"),
           "lombric : proie du merle et du hérisson")
    _check(specs["cloporte"].predators == ("carabe", "herisson"),
           "cloporte : proie du carabe et du hérisson")
    # Ressource du cloporte = litière (nulle sans litière, montée avec).
    tile, eco = _eco()
    food0 = _litter_grid(eco, tile, tile.plants)
    _check(not _grid_nonzero(food0), "cloporte : ressource litière nulle sans litière")
    eco.deposer_litiere(3, 4, "feuille", 2.0)
    food1 = _litter_grid(eco, tile, tile.plants)
    _check(food1[3][4] > 0.0, "cloporte : ressource litière > 0 avec litière déposée")
    # Fruit pourri → cloporte (signal_fn repris de la limace, qui n'en a plus).
    _check(specs["cloporte"].signal_fn is not None, "cloporte : porte le signal fruit pourri")
    _check(specs["limace"].signal_fn is None, "limace : signal fruit pourri retiré (passé au cloporte)")


def test_decomp_speed_suit_le_lombric():
    # C6 : decomp_speed ne dépend QUE du lombric (le ver fait l'humus), pas du cloporte.
    tile, eco = _eco()
    base = eco.decomp_speed(2, 2)
    eco.populations["cloporte"].set(2, 2, 0.50)
    _check(abs(eco.decomp_speed(2, 2) - base) < 1e-9,
           "decomp_speed insensible au cloporte (litière, pas humus du sol)")
    eco.populations["lombric"].set(2, 2, 0.50)
    _check(eco.decomp_speed(2, 2) > base,
           "decomp_speed accélérée par le lombric (bioturbation)")


# ---------------------------------------------------------------------------
# 7. COUVERTURE COMPLÈTE (④e) — 10 espèces, triade, salts, fenêtres hiver
# ---------------------------------------------------------------------------

def test_couverture_dix_especes():
    specs = build_population_specs()
    noms = {s.name for s in specs}
    _check(len(specs) == len(ESPECES),
           f"exactement {len(ESPECES)} espèces trophiques (vu {len(specs)})")
    _check(noms == set(ESPECES),
           f"les {len(ESPECES)} espèces attendues (vu {sorted(noms)})")
    # Catégories valides + chacune peuplée.
    for s in specs:
        _check(s.category in CATEGORIES, f"`{s.name}` : catégorie valide ({s.category})")
    tile, eco = _eco()
    for cat in CATEGORIES:
        membres = eco.category_fields(cat)
        _check(len(membres) >= 1, f"la catégorie `{cat}` a ≥1 membre")


def test_triade_et_salts():
    specs = build_population_specs()
    known = set(ESPECES) | set(larval_field_names(build_lifecycle_bridges()))
    salts = set()
    for s in specs:
        _check(callable(s.resource_fn), f"`{s.name}` : resource_fn callable")
        _check(callable(s.habitat_fn), f"`{s.name}` : habitat_fn callable")
        for pred in s.predators:
            _check(pred in known,
                   f"`{s.name}` : prédateur `{pred}` est une espèce/larve connue")
        salts.add(s.salt)
    _check(len(salts) == len(ESPECES),
           f"les {len(ESPECES)} salts sont distincts (vu {len(salts)})")


def test_phenologie_hivernale():
    specs = {s.name: s for s in build_population_specs()}

    def phen(nom, week):
        s = specs[nom]
        return _smoothstep(daylength(week), s.daylen_min, s.daylen_full)

    # Solstice d'hiver (w=51, jour le plus court ≈ 8 h) : tout le monde dormant.
    for nom in ("puceron", "doryphore"):
        _check(phen(nom, 51) == 0.0, f"`{nom}` : phénologie NULLE au solstice d'hiver")
    # Début de printemps (w≈7, jour ≈ 9,6 h) : le lombric (fenêtre 8,5/10) s'éveille
    # déjà alors que le puceron (10/13) dort encore → « quasi annuel » vs estival.
    _check(phen("puceron", 7) == 0.0, "puceron : encore dormant au jour court de printemps")
    _check(phen("lombric", 7) > 0.0, "lombric : déjà actif au jour court (fenêtre large)")
    # Plein été (w=25, ≈ 16 h) : tout le monde au maximum.
    for nom in ESPECES:
        _check(phen(nom, 25) == 1.0, f"`{nom}` : phénologie pleine au solstice d'été")


# ---------------------------------------------------------------------------
# 8. MÉTADONNÉE ENCYCLO (④e) — blurb, interconnexions, graphe symétrique
# ---------------------------------------------------------------------------

def test_metadata_encyclo():
    specs = {s.name: s for s in build_population_specs()}
    for nom in ESPECES:
        s = specs[nom]
        _check(bool(s.blurb.strip()), f"`{nom}` : blurb d'encyclopédie non vide")
        _check(len(s.interconnexions) >= 1, f"`{nom}` : ≥1 interconnexion déclarée")
        # Tout nom lié est soit une espèce, soit un champ larvaire, soit un milieu.
        for lien in s.interconnexions:
            _check(lien in set(ESPECES) | {"syrphe_larve"} | _MILIEU_TOKENS,
                   f"`{nom}` : interconnexion `{lien}` est un nom connu")
        # Les vrais prédateurs apparaissent TOUS dans le graphe relationnel.
        for pred in s.predators:
            _check(pred in s.interconnexions,
                   f"`{nom}` : son prédateur `{pred}` figure dans interconnexions")


def test_graphe_symetrique():
    # Le sous-graphe ENTRE espèces nommées est réciproque (si A cite B, B cite A) :
    # garantit qu'aucun lien proie↔prédateur/compétition n'est déclaré à sens unique.
    specs = {s.name: s for s in build_population_specs()}
    for nom in ESPECES:
        for lien in specs[nom].interconnexions:
            if lien in ESPECES:   # on n'exige la symétrie qu'entre les 10 espèces
                _check(nom in specs[lien].interconnexions,
                       f"graphe symétrique : `{lien}` cite-t-il bien `{nom}` en retour ?")


# ---------------------------------------------------------------------------
# 8bis. SUPER-PRÉDATEURS (②) — rapace + couleuvre, sommet trophique
# ---------------------------------------------------------------------------

def test_super_predateurs_nommes():
    # Deux specs de catégorie NEUVE `super_predateur`, SANS prédateur (sommets),
    # tickés EN DERNIER (après toutes les proies) → boom-bust top-down.
    specs = build_population_specs()
    smap = {s.name: s for s in specs}
    for nom in SUPER_PREDATEURS:
        _check(nom in smap, f"le super-prédateur `{nom}` existe comme spec")
        _check(smap[nom].category == "super_predateur",
               f"`{nom}` rattaché à la catégorie super_predateur")
        _check(smap[nom].predators == (), f"`{nom}` est un sommet (predators vides)")
    # Ordre de tick : rapace/couleuvre APRÈS toutes leurs proies (position en fin).
    ordre = [s.name for s in specs]
    for proie in ("campagnol", "merle", "limace"):
        for pred in SUPER_PREDATEURS:
            _check(ordre.index(pred) > ordre.index(proie),
                   f"`{pred}` ticke après sa proie `{proie}` (lit frais)")
    # Salts distincts de TOUT le reste (positions sprites décorrélées).
    salts = {s.salt for s in specs}
    _check(len(salts) == len(ESPECES), "salts tous distincts (rapace/couleuvre inclus)")


def test_super_predateurs_puits_cables():
    # Les puits top-down sont posés sur les PROIES (§2.4) : campagnol régulé par les
    # deux, merle par le rapace, limace par la couleuvre.
    smap = {s.name: s for s in build_population_specs()}
    _check(set(smap["campagnol"].predators) == {"rapace", "couleuvre"},
           "campagnol : régulé par rapace + couleuvre")
    _check("rapace" in smap["merle"].predators, "merle : le rapace est un puits")
    _check("couleuvre" in smap["limace"].predators, "limace : la couleuvre est un puits")


def test_super_predateurs_ressource_proies():
    # `_proies_grid` = somme normalisée des densités des proies. Sans proie → nulle ;
    # proies posées → la ressource s'allume à leurs plots (le prédateur les lit frais).
    tile, eco = _eco()
    res_rap = _proies_grid(("campagnol", "merle"))
    r0 = res_rap(eco, tile, tile.plants)
    _check(not _grid_nonzero(r0), "rapace : ressource nulle sans proie (densité nulle → 0)")
    eco.populations["campagnol"].set(2, 2, 0.60)
    eco.populations["merle"].set(4, 5, 0.30)
    r1 = res_rap(eco, tile, tile.plants)
    _check(r1[2][2] > 0.0 and r1[4][5] > 0.0,
           "rapace : ressource allumée aux plots de ses proies (campagnol + merle)")
    # La couleuvre ne lit PAS le merle (proies = campagnol + limace).
    r_coul = _proies_grid(("campagnol", "limace"))(eco, tile, tile.plants)
    _check(abs(r_coul[4][5]) < 1e-9,
           "couleuvre : ne chasse pas le merle (proies = campagnol + limace)")


# ---------------------------------------------------------------------------
# 9. POLLINISATEURS B (⑤) — bourdon & osmie, registre data-driven
# ---------------------------------------------------------------------------

POLLINISATEURS_B = ("bourdon", "osmie")


def test_cinq_pollinisateurs_nommes():
    reg = {p.name: p for p in build_pollinator_registry()}
    _check(set(POLLINATOR_NAMES) == set(reg),
           f"POLLINATOR_NAMES == registre (vu {sorted(reg)})")
    _check(len(POLLINATOR_NAMES) == 5, "5 types de pollinisateurs (3 + bourdon/osmie)")
    specs = {s.name: s for s in build_population_specs()}
    # Les pollinisateurs B sont des specs trophiques générées (catégorie dédiée).
    pspecs = {s.name: s for s in build_pollinator_specs()}
    for nom in POLLINISATEURS_B:
        _check(nom in reg, f"`{nom}` existe au registre")
        _check(nom not in specs, f"`{nom}` n'est PAS une guilde trophique consommatrice")
        _check(pspecs[nom].category == "pollinisateur", f"`{nom}` catégorie pollinisateur")
        _check(pspecs[nom].predators == (), f"`{nom}` sans prédateur (pollinisateur)")
        _check(reg[nom].bridge is None, f"`{nom}` sans pont larvaire (nid hors chaîne ④)")
    # Triades PROPRES : attractivités distinctes, salts distincts.
    salts = {reg[n].salt for n in reg}
    _check(len(salts) == len(reg), "chaque type a SON salt (positions sprites décorrélées)")


def test_attractivite_bourdon_osmie():
    reg = {p.name: p for p in build_pollinator_registry()}
    bourdon, osmie, abeille = reg["bourdon"], reg["osmie"], reg["abeille"]
    # Bourdon = langue longue : Fabacées/Lamiacées au max + buzz-pollinisation Solanacées.
    _check(bourdon.attractivite["Fabaceae"] == 1.0 and bourdon.attractivite["Lamiaceae"] == 1.0,
           "bourdon : Fabacées & Lamiacées maximales")
    _check(bourdon.attractivite["Solanaceae"] > abeille.attractivite["Solanaceae"],
           "bourdon : Solanacées > abeille (buzz-pollinisation tomate/poivron)")
    # Osmie = abeille des vergers : Rosacées au max, Apiacées élevées.
    _check(osmie.attractivite["Rosaceae"] == 1.0,
           "osmie : Rosacées maximales (arbres fruitiers)")
    _check(osmie.attractivite["Rosaceae"] > abeille.attractivite["Rosaceae"] and
           osmie.attractivite["Apiaceae"] >= 0.8,
           "osmie : pollinisatrice de vergers (Rosacées > abeille, Apiacées hautes)")
    # Anémophiles ≈ nulles pour les deux (graminées/chêne/noyer).
    for n in POLLINISATEURS_B:
        _check(reg[n].attractivite["Poaceae"] == 0.0,
               f"`{n}` : graminées non visitées (anémophiles)")


def test_fenetres_pollinisateurs_b():
    reg = {p.name: p for p in build_pollinator_registry()}
    # Bourdon PRÉCOCE/frais : fenêtre s'ouvre AVANT l'abeille (jours courts tolérés).
    _check(reg["bourdon"].daylen_min == 9.5 and reg["bourdon"].daylen_full == 12.0,
           "bourdon : fenêtre précoce 9.5/12.0 (frais, jours courts)")
    _check(reg["bourdon"].daylen_min < reg["abeille"].daylen_min,
           "bourdon : démarre plus tôt que l'abeille (comble la fenêtre précoce)")
    _check(reg["osmie"].daylen_min == 10.0 and reg["osmie"].daylen_full == 12.5,
           "osmie : fenêtre printanière 10.0/12.5 (abeille des vergers)")


def test_osmie_habitat_niche_bois():
    # Osmie : abeille solitaire qui NICHE dans le bois → habitat bumpe sur une `pile`
    # (faune↔structures §5.3). Sans pile ni rondelle → identique au plancher pollinisateur.
    tile, eco = _eco()
    base = _pollinisateur_habitat_grid(eco, tile, tile.plants)
    osm0 = _osmie_habitat_grid(eco, tile, tile.plants)
    _check(all(abs(osm0[r][c] - base[r][c]) < 1e-9 for r in range(ROWS) for c in range(COLS)),
           "osmie sans pile : habitat == plancher pollinisateur (rondelle)")
    eco.structures.append(Structure(kind="pile", plot=(1, 5)))
    osm1 = _osmie_habitat_grid(eco, tile, tile.plants)
    _check(abs(osm1[1][5] - min(1.0, base[1][5] + PILE_HABITAT_W)) < 1e-9,
           f"pile posée → osmie bumpe au plot (={osm1[1][5]:.2f}, niche-bois)")
    _check(not _grid_nonzero([[osm1[r][c] if (r, c) != (1, 5) else 0.0
                               for c in range(COLS)] for r in range(ROWS)]),
           "osmie : bump LOCAL à la pile, nul ailleurs (sans rondelle)")


def test_pollinisateurs_b_dans_densite():
    # La densité pollinisatrice TOTALE (lue par pollinator_reach + Vigueur macro)
    # SOMME désormais bourdon/osmie : sans leur ajout à POLLINATOR_NAMES, le pollen
    # déposé ne nourrirait pas la nouaison. On le prouve via eco.pollinator_density.
    tile, eco = _eco()
    d0 = eco.pollinator_density(2, 2)
    eco.populations["bourdon"].set(2, 2, 0.40)
    eco.populations["osmie"].set(2, 2, 0.25)
    d1 = eco.pollinator_density(2, 2)
    _check(abs((d1 - d0) - 0.65) < 1e-9,
           f"pollinator_density somme bourdon+osmie (Δ={d1 - d0:.2f} attendu 0.65)")


# ---------------------------------------------------------------------------
# 10. ENCYCLO DES POLLINISATEURS (⑥) — blurb + graphe (donnée pure, golden NEUTRE)
# ---------------------------------------------------------------------------

POLLINISATEURS = ("abeille", "syrphe", "papillon", "bourdon", "osmie")
# Tokens NON-trophiques admis dans le graphe des pollinisateurs : floraison nouée
# (`fruit`), niches (`ruche`/`miel` sociale, `pile` maçonne), stades larvaires des
# ponts ⑤ (`chenille`, `syrphe_larve`) et la proie de la larve de syrphe (`puceron`).
_POLLINISATEUR_TOKENS = {"fruit", "ruche", "miel", "pile", "chenille",
                         "syrphe_larve", "puceron"}


def test_metadata_encyclo_pollinisateurs():
    # Les 5 pollinisateurs portent désormais un blurb + un graphe (⑥, splat dans le
    # TrophicSpec via build_pollinator_specs). DONNÉE PURE → golden NEUTRE.
    pspecs = {s.name: s for s in build_pollinator_specs()}
    for nom in POLLINISATEURS:
        s = pspecs[nom]
        _check(bool(s.blurb.strip()), f"`{nom}` : blurb d'encyclopédie non vide")
        _check(len(s.interconnexions) >= 1, f"`{nom}` : ≥1 interconnexion déclarée")
        for lien in s.interconnexions:
            _check(lien in _POLLINISATEUR_TOKENS,
                   f"`{nom}` : interconnexion `{lien}` est un token connu")
        # Hors du sous-graphe trophique symétrique : aucun pollinisateur ne se
        # déclare proie/prédateur d'un autre (predators vides, cf. section 9).
        _check(s.predators == (), f"`{nom}` : sans prédateur (pollinisateur)")


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
    test_deux_detritivores_nommes()
    test_decomp_speed_suit_le_lombric()
    test_couverture_dix_especes()
    test_triade_et_salts()
    test_phenologie_hivernale()
    test_metadata_encyclo()
    test_graphe_symetrique()
    test_super_predateurs_nommes()
    test_super_predateurs_puits_cables()
    test_super_predateurs_ressource_proies()
    test_cinq_pollinisateurs_nommes()
    test_attractivite_bourdon_osmie()
    test_fenetres_pollinisateurs_b()
    test_osmie_habitat_niche_bois()
    test_pollinisateurs_b_dans_densite()
    test_metadata_encyclo_pollinisateurs()
    print("[faune] TOUS LES TESTS PASSENT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
