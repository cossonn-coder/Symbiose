"""
SYMBIOSE — fields/population/mulot.py
Ressource et habitat du MULOT (*Apodemus sylvaticus*, zoochorie ⑥, D42) : petit
rongeur nocturne des sous-bois et des lisières, mangeur de graines. Ici, seulement
ce qui dit OÙ il vit et DE QUOI ; sa prédation sur les grains sauvages (et ses
caches) vit dans `sim/mulot.py`.

Il ferme deux boucles :
  - la SATIATION : une glandée offre plus de graines qu'il n'en peut manger, le
    surplus lève (la satiation elle-même est dans `sim/mulot.py`) ;
  - la chaîne GRAINE → MULOT → RAPACE / COULEUVRE : il est leur proie (registre).

Catégorie `disperseur` (registre) : lue par personne d'autre. Le mulot NE ronge PAS
les racines (≠ campagnol, `herbivore_vertebre`) — aucun dégât végétal direct.

Couche `fields` : lit les plantes, la litière, la banque-sol et les grains en
attente de la tuile, jamais `sim`.
"""
from fields.population.constants import _zero_grid, _clamp01
from fields.population.resources import (
    _fruit_litter, _avec_abri_paillage, FRUIT_SIGNAL_REF, PILE_HABITAT_W,
)

# Poids des trois sources de nourriture dans la ressource (placeholders, calibrage
# ⑦). Les GRAINS SAUVAGES au sol sont sa proie préférée (gland, faîne, noisette,
# noyau) ; le fruit tombé (frais ou pourri : il en grignote les pépins) vient
# ensuite ; la banque-sol (graines fines enfouies) est un fond diffus.
GRAINS_W = 1.0
FRUIT_W = 0.5
BANQUE_W = 0.3
# Grains sauvages sur un plot qui saturent la ressource (= plafond par plot ①).
GRAINS_REF = 3.0
# Densité de banque-sol (somme des archétypes) qui sature le fond diffus.
BANQUE_REF = 1.0
# Habitat sous la couronne d'un ligneux vivant (litière, racines, abri des
# rapaces) — le mulot est un animal de sous-bois.
COURONNE_HABITAT = 0.30


def _mulot_food_grid(eco, tile, plants) -> list[list[float]]:
    """Nourriture du mulot : grains SAUVAGES au sol (comptés, normalisés par
    `GRAINS_REF` ; les grains plantés par le joueur ne comptent pas — il ne les
    touche pas) + fruit tombé (litière `fruit`, tout âge) + banque-sol LUE (jamais
    consommée : la granivorie sur la banque-sol reste en dette). Borné [0,1]."""
    g = _zero_grid(eco.rows, eco.cols)
    grains = getattr(tile, "grains_en_attente", None) or {}
    banque = eco.seed_bank
    for r in range(eco.rows):
        for c in range(eco.cols):
            n = sum(1 for gr in grains.get((r, c), ()) if gr.origine != "joueur")
            masse, _age = _fruit_litter(eco, r, c)
            fond = banque.total_density(r, c) if banque is not None else 0.0
            g[r][c] = _clamp01(GRAINS_W * min(1.0, n / GRAINS_REF)
                               + FRUIT_W * min(1.0, masse / FRUIT_SIGNAL_REF)
                               + BANQUE_W * min(1.0, fond / BANQUE_REF))
    return g


def _couvert_grid(eco, tile, plants) -> list[list[float]]:
    """Couvert « ligneux et bois mort » : sous la couronne d'un ligneux vivant +
    bump des structures `pile`. Le paillage s'ajoute par `_avec_abri_paillage`."""
    g = _zero_grid(eco.rows, eco.cols)
    for p in plants:
        if not p.is_alive or not getattr(p.plant_class, "ligneux", False):
            continue
        for r, c in p.foliar_plots:
            if 0 <= r < eco.rows and 0 <= c < eco.cols:
                g[r][c] = max(g[r][c], COURONNE_HABITAT)
    for st in getattr(eco, "structures", ()):
        if getattr(st, "kind", None) == "pile":
            r, c = st.plot
            if 0 <= r < eco.rows and 0 <= c < eco.cols:
                g[r][c] = _clamp01(g[r][c] + PILE_HABITAT_W)
    return g


# Habitat = couvert ligneux + piles + paillage (la lisière s'ajoute par `lisiere_w`
# au registre). C'est aussi la grille où il CACHE ses graines (`sim/mulot.py`).
_mulot_habitat_grid = _avec_abri_paillage(_couvert_grid)
