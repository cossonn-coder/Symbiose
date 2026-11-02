"""
SYMBIOSE — tests/test_feuilles_automne.py
Le largage d'automne sous la couronne et le hint `feuillage` (sprint AUTOMNE VISIBLE ③).

Couvre : conservation du total sur la chute, tuile jamais dépassée, masse par plot
stable pour un arbre au bord de la tuile, une seule ligne 🍂 par an (le carnet en fait
un événement par ligne), fenêtre de l'appelant couvrant la dernière chute possible,
`feuillage` monotone, persistant toujours à 1.

Lancement (depuis data/code/) : python3 -m tests.test_feuilles_automne
"""
import sys

from fields import init_eco, ABSCISSION_MAX, CHUTE_SEMAINES
from plants import AppleTree, PlantInstance
from plants.catalogue import PERENNIAL_CATALOGUE
from sim.engine.calendrier import saison_de
from sim.engine.decompo import DecompoMixin, masse_feuillage, semaine_abscission
from sim.engine.transpiration import feuillage_visible
from sim.precroissance import pre_croitre
from world import Tile

SEED = 42
ROWS, COLS = 16, 11
_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'✅' if cond else '❌'} {name}" + (f" — {detail}" if detail else ""))


def _arbre(r, c, tid):
    """Un pommier de 11 ans sur une tuile neuve, sans autre plante."""
    tile = Tile(tile_id=tid, soil_type="terre", origin_x_cm=0.0, origin_y_cm=0.0,
                grid_rows=ROWS, grid_cols=COLS)
    eco = init_eco(tid, ROWS, COLS, humidite=1.5, fertilite=1.0, microbiome=0.3,
                   soil_type="terre", heterogene=False)
    plante = PlantInstance(plant_class=AppleTree, position=(r, c))
    pre_croitre(plante, SEED, 11)
    tile.plants.append(plante)
    return tile, eco, plante


def _feuilles(eco):
    """{(r, c): masse de feuilles} des plots qui en portent."""
    return {(r, c): p.masse for r in range(ROWS) for c in range(COLS)
            for p in eco.litiere[r][c] if p.tissu == "feuille"}


def _chute(tile, eco):
    """Déroule toutes les semaines de la fenêtre d'abscission. Renvoie le log."""
    moteur = DecompoMixin()
    log = []
    for semaine in range(1, 53):
        log += moteur._abscission(tile, eco, semaine)
    return log


def test_conservation():
    print("\n[1] conservation du total")
    tile, eco, plante = _arbre(8, 5, "T1")
    plots = [rc for rc in plante.foliar_plots if tile.is_valid_plot(*rc)]
    attendu = masse_feuillage(plante, plots)
    log = _chute(tile, eco)
    total = sum(_feuilles(eco).values())
    check("couronne de plusieurs plots", len(plots) > 9, f"{len(plots)} plots")
    check("total déposé = masse annuelle", abs(total - attendu) < 1e-9,
          f"{total:.6f} / {attendu:.6f}")
    check("une seule ligne 🍂 sur l'année", len(log) == 1, log)
    check("tous les plots de la couronne reçoivent",
          set(_feuilles(eco)) == set(plots))


def test_bord_de_tuile():
    print("\n[2] tuile non dépassée, bord sans surcharge")
    tile_c, eco_c, centre = _arbre(8, 5, "T2")
    tile_b, eco_b, bord = _arbre(0, 0, "T3")
    _chute(tile_c, eco_c)
    _chute(tile_b, eco_b)
    dedans = [rc for rc in bord.foliar_plots if tile_b.is_valid_plot(*rc)]
    masses_b = _feuilles(eco_b)
    check("la couronne du coin déborde", len(dedans) < len(bord.foliar_plots))
    check("aucun dépôt hors de la couronne dans la tuile", set(masses_b) == set(dedans))
    par_plot_c = max(_feuilles(eco_c).values())
    check("masse par plot du coin du même ordre qu'au centre (±50 %)",
          0.5 * par_plot_c <= max(masses_b.values()) <= 1.5 * par_plot_c,
          f"coin {max(masses_b.values()):.3f}, centre {par_plot_c:.3f}")


def test_fenetre():
    print("\n[3] fenêtre de l'appelant")
    derniere = ABSCISSION_MAX + CHUTE_SEMAINES - 1
    check("le dernier largage possible reste en automne",
          saison_de(derniere) == "automne", f"s{derniere}")


def test_feuillage():
    print("\n[4] hint `feuillage`")
    _, _, plante = _arbre(8, 5, "T4")
    w = semaine_abscission(plante)
    valeurs = [feuillage_visible(plante, saison_de(s), s) for s in range(9, 53)]
    check("monotone décroissant de l'été à l'hiver",
          all(a >= b for a, b in zip(valeurs, valeurs[1:])))
    check("1 à la semaine d'abscission (rien n'est encore tombé)",
          feuillage_visible(plante, saison_de(w), w) == 1.0)
    fin = w + CHUTE_SEMAINES
    check("0 une fois la chute finie", feuillage_visible(plante, saison_de(fin), fin) == 0.0)
    check("0 en hiver", feuillage_visible(plante, "hiver", 45) == 0.0)
    check("reprend au débourrement",
          0.0 < feuillage_visible(plante, "printemps", 2) < 1.0
          and feuillage_visible(plante, "printemps", 8) == 1.0)
    sapin = PlantInstance(plant_class=PERENNIAL_CATALOGUE["sapin"], position=(2, 2))
    check("persistant toujours à 1",
          all(feuillage_visible(sapin, saison_de(s), s) == 1.0 for s in range(1, 53)))


def main():
    test_conservation()
    test_bord_de_tuile()
    test_fenetre()
    test_feuillage()
    ok = sum(1 for _, c in _results if c)
    print(f"\n{ok}/{len(_results)} checks OK")
    return 0 if ok == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
