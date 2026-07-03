"""
SYMBIOSE — tests/test_grimpe.py
Test CIBLÉ du tronçon ③ (D49 volet A, CONCEPTION_GRIMPANTES §5) : la PLANTE-HÔTE
vivante comme support de grimpe. Prouve HORS golden (le smoke n'a aucune haute à
portée d'une grimpante) les quatre comportements de ③ :

  1. ACCROCHE — une grimpante libre au-dessus de sa hauteur autoportante s'accroche
     à une voisine vivante plus haute et compatible, dans le rayon borné ;
  2. SUIVI — la hauteur d'appui est RELUE chaque tick : l'hôte grandit, la grimpante
     suit (le plancher d'apex renforcé montera d'autant, cf. geometrie._apex_z_floor) ;
  3. DÉTACHEMENT — l'hôte meurt → la grimpante se détache (redevient libre) ;
  4. ÉTRANGLEMENT ÉMERGENT — une grimpante qui DÉPASSE son hôte l'ombrage dans le
     `LightField` (ombre normale d'une canopée plus haute), SANS aucune règle de
     malus dédiée (philo #2 : flux → contrainte → réponse).

⚠️ Bean/Sunflower ne sont PAS `procedural_growth` : leur `current_height` dérive du
stade × growth_factor × gène. On pilote donc la hauteur de l'HÔTE par les stades.
Le gate d'accroche de la GRIMPANTE, lui, lit le `max_z` de ses SEGMENTS (②) — on lui
pose donc un segment vertical réel au-dessus de sa hauteur autoportante.

Non inclus dans le golden smoke test : couverture ciblée et rapide.
Lancement (depuis data/code/) : python3 -m tests.test_grimpe
"""

import sys

from world import Tile
from plants import Bean, Sunflower
from plants.base.instance import Segment
from fields.light import LightField
from sim.grimpe import chercher_support


def _tile() -> Tile:
    return Tile(tile_id="G", soil_type="terre", grid_rows=10, grid_cols=10)


def _grimpante_dressee(tile: Tile, row: int, col: int, hauteur_seg: float):
    """Pose un haricot (vrille_volubile, autoportante 35 cm) avec un unique segment
    vertical de `hauteur_seg` cm → son `max_z` dépasse sa hauteur autoportante, ce
    qui arme la recherche d'accroche (②)."""
    b = tile.add_plant(Bean, row, col)
    b.segments = [Segment(parent=None, base=(b.x_cm, b.y_cm, 0.0), dir=(0.0, 0.0, 1.0),
                          length_cm=hauteur_seg, thickness_cm=1.0, age_weeks=1,
                          auxin=1.0, is_apex=True)]
    b.footprint = None
    return b


def _hote_haut(tile: Tile, row: int, col: int, stades: int = 3):
    """Pose un tournesol et l'avance de `stades` stades → hôte vivant nettement plus
    haut que la hauteur autoportante du haricot."""
    s = tile.add_plant(Sunflower, row, col)
    for _ in range(stades):
        s.advance_stage()
    return s


def test_accroche_hote_vivant():
    """Grimpante dressée + hôte plus haut à un plot de distance → accroche à l'hôte."""
    t = _tile()
    hote = _hote_haut(t, 4, 5)               # (275, 225), ~250 cm
    b = _grimpante_dressee(t, 4, 4, 60.0)    # (225, 225), max_z 60 > 35
    chercher_support(b, t, None)
    assert b.support is not None, "la grimpante aurait dû s'accrocher à l'hôte"
    assert b.support[0] is hote, "l'appui doit être l'hôte vivant lui-même"
    assert b.support[1] == hote.current_height, "hauteur d'appui = hauteur de l'hôte"
    print(f"  [accroche] appui sur {hote.name} à {b.support[1]:.0f} cm ✓")


def test_suivi_croissance_hote():
    """L'hôte grandit → la hauteur d'appui relue par la grimpante suit (chaque tick)."""
    t = _tile()
    hote = _hote_haut(t, 4, 5)
    b = _grimpante_dressee(t, 4, 4, 60.0)
    chercher_support(b, t, None)
    h0 = b.support[1]
    hote.growth_factor = 1.3                  # l'hôte grossit (hauteur ∝ growth_factor)
    chercher_support(b, t, None)              # tick suivant : entretien de l'accroche
    h1 = b.support[1]
    print(f"  [suivi] appui {h0:.0f} → {h1:.0f} cm (l'hôte a grandi)")
    assert h1 > h0, "la hauteur d'appui doit suivre la croissance de l'hôte"
    assert b.support[0] is hote, "toujours accrochée au même hôte"


def test_detachement_mort_hote():
    """L'hôte meurt → la grimpante se détache (redevient libre)."""
    t = _tile()
    hote = _hote_haut(t, 4, 5)
    b = _grimpante_dressee(t, 4, 4, 60.0)
    chercher_support(b, t, None)
    assert b.support is not None
    hote.health = 0                            # l'hôte meurt (is_alive → False)
    chercher_support(b, t, None)
    print("  [détachement] hôte mort → grimpante libre ✓")
    assert b.support is None, "la grimpante doit se détacher à la mort de l'hôte"


def test_detachement_hote_disparu():
    """L'hôte quitte la tuile (retiré) → détachement au tick suivant."""
    t = _tile()
    hote = _hote_haut(t, 4, 5)
    b = _grimpante_dressee(t, 4, 4, 60.0)
    chercher_support(b, t, None)
    assert b.support is not None
    t.remove_plant(hote)                       # disparaît de la tuile
    chercher_support(b, t, None)
    assert b.support is None, "détachement si l'hôte n'est plus dans la tuile"
    print("  [détachement] hôte parti → grimpante libre ✓")


def test_hors_rayon_pas_accroche():
    """Un hôte hors du rayon d'accroche (plusieurs plots) n'est pas saisi."""
    t = _tile()
    _hote_haut(t, 4, 8)                        # loin (col 8 vs 4 → ~200 cm)
    b = _grimpante_dressee(t, 4, 4, 60.0)
    chercher_support(b, t, None)
    assert b.support is None, "un hôte trop loin ne doit pas être saisi"
    print("  [rayon] hôte hors rayon → pas d'accroche ✓")


def test_hote_trop_court_ignore():
    """Un voisin plus BAS que la hauteur autoportante n'est pas un support valide."""
    t = _tile()
    bas = t.add_plant(Sunflower, 4, 5)         # stade semis (~5 cm) < 35 cm
    b = _grimpante_dressee(t, 4, 4, 60.0)
    chercher_support(b, t, None)
    assert b.support is None, "un hôte trop court ne porte pas la grimpante"
    print(f"  [seuil] hôte à {bas.current_height:.0f} cm ignoré ✓")


def test_etranglement_emergent():
    """La grimpante qui DÉPASSE son hôte l'ombrage dans le LightField — émergent, sans
    règle dédiée : l'hôte reçoit moins de lumière qu'isolé."""
    # Hôte + grimpante qui le dépasse, superposés (la grimpante grimpe l'hôte).
    t = _tile()
    hote = _hote_haut(t, 4, 4, stades=2)       # tournesol ~180 cm
    grimp = t.add_plant(Bean, 4, 4)
    for _ in range(3):
        grimp.advance_stage()                  # haricot ~200 cm > 180
    lf = LightField(10, 10)
    lf.compute(t.plants, "ete")
    recu_avec = lf.light_received(hote)
    # Même hôte, seul.
    t2 = _tile()
    hote2 = _hote_haut(t2, 4, 4, stades=2)
    lf2 = LightField(10, 10)
    lf2.compute(t2.plants, "ete")
    recu_seul = lf2.light_received(hote2)
    print(f"  [étranglement] hôte {hote.current_height:.0f} cm sous grimpante "
          f"{grimp.current_height:.0f} cm : lumière {recu_avec:.3f} vs seul {recu_seul:.3f}")
    assert grimp.current_height > hote.current_height, "la grimpante doit dépasser l'hôte"
    assert recu_avec < recu_seul, "l'hôte dépassé doit recevoir moins de lumière (ombre émergente)"


def main() -> int:
    tests = [test_accroche_hote_vivant, test_suivi_croissance_hote,
             test_detachement_mort_hote, test_detachement_hote_disparu,
             test_hors_rayon_pas_accroche, test_hote_trop_court_ignore,
             test_etranglement_emergent]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"[grimpe] PASS — {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"[grimpe] FAIL — {t.__name__} : {e}")
    if failed:
        print(f"\n[grimpe] {failed}/{len(tests)} test(s) en échec")
        return 1
    print(f"\n[grimpe] OK — {len(tests)} tests verts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
