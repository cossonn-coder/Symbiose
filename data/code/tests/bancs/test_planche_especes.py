"""
SYMBIOSE — tests/bancs/test_planche_especes.py
Oracle du banc `planche_especes` (sprint FORMES DES PLANTES ①) : les 40 espèces sont
là, chacune à son emplacement, adulte, sans toucher sa voisine à l'écran, et leurs
fleurs et fruits sont posés. Sans moteur : le banc est un état posé, sans tick.

Usage (depuis data/code/) : python3 -m tests.bancs.test_planche_especes
"""
from itertools import combinations

from bancs import BANCS, BANC_WEEK_DEPART
from bancs.planche_especes import POSITIONS, ESPECES_PAR_TAILLE
from plants.catalogue import PLANT_CATALOGUE

# Projection de la vue (world/WorldView.Projection.cs), px internes par cm.
PX_CM, PX_CM_Y = 0.39, 0.195


def _plantes():
    """{espèce : (plante, x monde, y monde)} d'un banc fraîchement monté."""
    nom_de = {cls: nom for nom, cls in PLANT_CATALOGUE.items()}
    return {nom_de[p.plant_class]: (p, t.origin_x_cm + p.x_cm, t.origin_y_cm + p.y_cm)
            for t in BANCS["planche_especes"]()[0] for p in t.plants}


def _boite(plante, x, y):
    """Boîte écran d'un pied : largeur du rayon de canopée, hauteur `height_cm` (ce que
    le port dessiné doit suivre), ou du squelette tant qu'il est dessiné."""
    r = plante.plant_class.canopy_radius_at(plante)
    h = max(plante.current_height,
            max(s.base[2] + s.dir[2] * s.length_cm for s in plante.segments))
    sx, sy = (x - y) * PX_CM, (x + y) * PX_CM_Y
    return sx - r * PX_CM, sy - h * PX_CM, sx + r * PX_CM, sy + r * PX_CM_Y


def test_toutes_les_especes():
    assert set(POSITIONS) == set(PLANT_CATALOGUE) == set(ESPECES_PAR_TAILLE)
    assert len(set(POSITIONS.values())) == len(PLANT_CATALOGUE)
    plantes = _plantes()
    assert len(plantes) == len(PLANT_CATALOGUE)
    for nom, (plante, x, y) in plantes.items():
        assert (x, y) == POSITIONS[nom], nom
        assert plante.current_stage == len(plante.plant_class.growth_stages) - 1, nom


def test_rien_ne_se_touche():
    boites = {n: _boite(*v) for n, v in _plantes().items()}
    for (n1, a), (n2, b) in combinations(boites.items(), 2):
        separees = a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1]
        assert separees, f"{n1} touche {n2} : {a} {b}"


def test_hors_maison_grandes_au_nord():
    for x, y in POSITIONS.values():
        assert x >= 1400 or y >= 1400, (x, y)
    profondeur = [sum(POSITIONS[n]) for n in ESPECES_PAR_TAILLE]
    assert profondeur == sorted(profondeur)


def test_fleurs_et_fruits_poses():
    for nom, (plante, _x, _y) in _plantes().items():
        assert plante.floraison == 1.0, nom
        if plante.plant_class.fruitier:
            assert plante.fruits, nom


def test_ete():
    assert BANC_WEEK_DEPART["planche_especes"] == 20


if __name__ == "__main__":
    for fn in (test_toutes_les_especes, test_rien_ne_se_touche, test_hors_maison_grandes_au_nord,
               test_fleurs_et_fruits_poses, test_ete):
        fn()
        print(f"OK {fn.__name__}")
