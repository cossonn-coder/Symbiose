"""
SYMBIOSE — fields/population/disperseurs.py
Ressource et habitat des DISPERSEURS de fruits à coque (zoochorie ⑤, D42) : le
GEAI et l'ÉCUREUIL. Ils cueillent glands, faînes, noix et noisettes sur l'arbre,
les cachent, et en oublient (`sim/zoochorie.py`). Ici, seulement ce qui dit OÙ ils
vivent et DE QUOI : deux grilles par bête, au patron `_merle_food_grid` /
`_base_habitat_grid` (`resources.py`, déjà proche du garde-fou de taille → module
à part).

Catégorie `disperseur` (registre) : lue par PERSONNE d'autre — ni santé des
plantes, ni Vigueur macro, ni dégâts racinaires. Leur seul effet sur le monde passe
par la cueillette (`sim/zoochorie`). Sans fruit à coque mûr, le champ vit sur son
habitat et n'agit sur rien.

Couche `fields` : lit les plantes (`plant_class.mange_par`, cohortes de fruits),
jamais `sim`.
"""
from fields.population.constants import _zero_grid, _clamp01

# Seuil « mûr » d'une cohorte — même tolérance que `sim/zoochorie.MUR` (une
# maturation en 1/7 par semaine n'atteint pas 1,0 pile en flottant). Recopié ici
# parce que `fields` n'importe pas `sim`.
_MUR = 1.0 - 1e-9
# Hauteur minimale d'un ligneux vivant dont la couronne compte comme « cime »
# (geai qui niche, écureuil qui circule). Un pommier de 2 ans n'est pas une cime.
HAUTEUR_COURONNE_CM = 300.0
# Fruits mûrs sur un plot qui SATURENT la ressource (placeholder, calibrage ⑦) :
# une couronne de chêne en glandée en porte bien plus — la ressource sature, c'est
# la prise (Holling II) qui borne ce qui est réellement emporté.
NOIX_REF = 20.0
# Habitat de base sur une cime (placeholder) : le geai niche dans les arbres et
# vient au jardin depuis la lisière (`lisiere_w` du registre). Même ordre que le
# plancher du merle (0,20).
GEAI_HABITAT_CIME = 0.30
ECUREUIL_HABITAT_CIME = 0.40
# Goût par espèce (clé = `plant_class.name`), ∈ [0,1]. Le geai est l'oiseau du
# GLAND (chêne d'abord) ; l'écureuil préfère noisette et noix, gros fruits riches.
# Une espèce absente vaut 0 même si elle est `mange_par` : on ne force rien.
GOUT_GEAI = {"Chêne": 1.0, "Hêtre": 0.8, "Noyer": 0.6, "Noisetier": 0.6}
GOUT_ECUREUIL = {"Noisetier": 1.0, "Noyer": 1.0, "Hêtre": 0.6, "Chêne": 0.5}


def couronnes(plants, rows: int, cols: int) -> dict:
    """`{(r, c): {id des ligneux hauts dont la couronne couvre le plot}}` — ligneux
    VIVANTS d'au moins `HAUTEUR_COURONNE_CM`. Sert aux deux habitats et à l'anneau
    de lisière des couronnes (`sim/zoochorie`). Les ids ne servent qu'à COMPTER des
    couronnes distinctes le temps d'un appel (jamais stockés, jamais ordonnés)."""
    qui = {}
    for p in plants:
        if (not p.is_alive or not getattr(p.plant_class, "ligneux", False)
                or p.current_height < HAUTEUR_COURONNE_CM):
            continue
        for rc in p.foliar_plots:
            if 0 <= rc[0] < rows and 0 <= rc[1] < cols:
                qui.setdefault(rc, set()).add(id(p))
    return qui


def _noix_grid(nom: str, gout: dict):
    """Fabrique la ressource d'un disperseur : fruits MÛRS encore sur l'arbre des
    espèces qu'il mange (`nom in mange_par`), pondérés par son goût, répartis sur la
    couronne, normalisés par `NOIX_REF`. Nulle hors de la saison des fruits — le
    champ retombe alors sur son habitat (inertie)."""
    def _grid(eco, tile, plants) -> list[list[float]]:
        g = _zero_grid(eco.rows, eco.cols)
        for p in plants:
            cls = p.plant_class
            if not p.is_alive or not p.fruits or nom not in cls.mange_par:
                continue
            w = gout.get(cls.name, 0.0)
            mures = sum(f.nombre for f in p.fruits if f.maturite >= _MUR)
            if w <= 0.0 or mures <= 0:
                continue
            plots = [rc for rc in p.foliar_plots
                     if 0 <= rc[0] < eco.rows and 0 <= rc[1] < eco.cols] or [p.position]
            part = w * mures / len(plots)
            for r, c in plots:
                g[r][c] += part
        for r in range(eco.rows):
            for c in range(eco.cols):
                g[r][c] = _clamp01(g[r][c] / NOIX_REF)
        return g
    return _grid


_geai_food_grid = _noix_grid("geai", GOUT_GEAI)
_ecureuil_food_grid = _noix_grid("ecureuil", GOUT_ECUREUIL)


def _geai_habitat_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat du geai : les cimes (couronnes de ligneux hauts) où il niche. Le gros
    de sa présence au jardin vient de la LISIÈRE (`lisiere_w` fort au registre) : il
    vit en forêt et vient chercher les glands."""
    g = _zero_grid(eco.rows, eco.cols)
    for (r, c) in couronnes(plants, eco.rows, eco.cols):
        g[r][c] = GEAI_HABITAT_CIME
    return g


def _ecureuil_habitat_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat de l'écureuil : les cimes CONNEXES. L'écureuil circule d'arbre en
    arbre par les branches ; un arbre isolé au milieu d'une pelouse l'oblige à
    descendre, à découvert. Un plot de cime compte si son voisinage 3×3 est touché
    par au moins DEUX couronnes distinctes (deux arbres qui se rejoignent, ou se
    touchent presque). Un arbre seul, si grand soit-il, ne fait pas un bois."""
    qui = couronnes(plants, eco.rows, eco.cols)
    g = _zero_grid(eco.rows, eco.cols)
    for (r, c) in qui:
        voisines = set()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                voisines |= qui.get((r + dr, c + dc), set())
        if len(voisines) >= 2:
            g[r][c] = ECUREUIL_HABITAT_CIME
    return g
