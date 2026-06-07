"""
SYMBIOSE — tests/test_ombre_maison.py
Test CIBLÉ : la MAISON projette une ombre déterministe dans le LightField
(sprint maison, tronçon 2). Couvre :
  1. asymétrie d'ombre — un plot au NORD reçoit moins qu'au SUD (été) ; l'ombre
     est DIRECTIONNELLE (nord sombre, est ensoleillé au midi) → c'est bien un
     rectangle balayé, pas un disque symétrique ;
  2. allongement HIVERNAL — un plot loin au nord, lumineux l'été, passe à l'ombre
     l'hiver (soleil rasant) ;
  3. effet ESPALIER (albédo) — le sol au pied d'un mur ENSOLEILLÉ reçoit plus de
     lumière qu'avec `wall_albedo=0` (l'albédo s'annule bien à 0) ;
  4. DÉTERMINISME — deux calculs identiques donnent le même champ.

Non inclus dans le golden smoke test (décision Q4) : couverture fine et rapide.

⚠️ Note de conception (albédo vs plafond [0,1]) : la lumière-sol est plafonnée à
1.0 (contrat [0,1] consommé en aval : shade_memory, growth_factor, niche). En
plein soleil ouvert la lumière vaut déjà 1.0, donc l'espalier n'y est pas
*strictement* supérieur (il sature). On le démontre donc au pied du mur EST,
partiellement ombré le soir → il reste de la marge sous le plafond. Un vrai
« point chaud > 1 » relèverait d'un champ thermique distinct (hors périmètre).

Lancement (depuis data/code/) : python3 -m tests.test_ombre_maison
"""

import sys

from constants import PLOT_CM
from world import House
from fields.light import LightField

# Monde de test : un seul champ 40×40 (= 20×20 m) couvrant toute la maison
# centrée par défaut (centre 1000,1000 cm ; empreinte [600,600]→[1400,1400]).
ROWS = COLS = 40
ORIGIN = (0.0, 0.0)      # le champ EST le monde (offset nul)


def _field(saison: str, house: House) -> LightField:
    lf = LightField(ROWS, COLS)
    lf.compute([], saison, house=house, tile_origin=ORIGIN)
    return lf


def _rc(x_cm: float, y_cm: float) -> tuple[int, int]:
    """(row=y, col=x) du plot contenant le point monde (x_cm, y_cm)."""
    return int(y_cm // PLOT_CM), int(x_cm // PLOT_CM)


def test_nord_plus_sombre_que_sud():
    """Été : plot au Nord de la maison nettement plus sombre qu'au Sud ; et ombre
    DIRECTIONNELLE (nord sombre, est ensoleillé) → rectangle balayé, pas disque."""
    lf = _field("ete", House())
    nord = lf.at_plot(*_rc(1000, 400))    # 200 cm au nord du mur (ombre de midi)
    sud  = lf.at_plot(*_rc(1000, 1600))   # plein sud, ensoleillé
    est  = lf.at_plot(*_rc(1600, 1000))   # plein est, ensoleillé au midi
    print(f"  [N/S] nord={nord:.3f} sud={sud:.3f} est={est:.3f}")
    assert nord < sud,  f"Nord ({nord:.3f}) devrait être < Sud ({sud:.3f})"
    assert nord < est,  f"ombre directionnelle : Nord ({nord:.3f}) < Est ({est:.3f})"
    assert sud > 0.9,   f"Sud devrait rester en plein soleil ({sud:.3f})"


def test_ombre_plus_longue_en_hiver():
    """Un plot loin au nord (hors de portée de l'ombre d'été) tombe à l'ombre en
    hiver, quand le soleil rasant allonge fortement l'ombre."""
    far = _rc(1000, 150)                   # ~450 cm au nord du mur
    ete   = _field("ete", House()).at_plot(*far)
    hiver = _field("hiver", House()).at_plot(*far)
    print(f"  [saison] far-nord été={ete:.3f} hiver={hiver:.3f}")
    assert hiver < ete, f"hiver ({hiver:.3f}) devrait être plus sombre qu'été ({ete:.3f})"


def test_albedo_espalier():
    """Au pied d'un mur ensoleillé (face EST, frappée le matin), l'albédo ajoute
    de la lumière réfléchie ; `wall_albedo=0` annule l'effet."""
    base = _rc(1450, 1000)                 # 50 cm à l'est du mur est
    avec  = _field("ete", House(wall_albedo=0.35)).at_plot(*base)
    sans  = _field("ete", House(wall_albedo=0.0)).at_plot(*base)
    print(f"  [albédo] pied mur est : avec={avec:.3f} sans={sans:.3f}")
    assert avec > sans, f"l'albédo ({avec:.3f}) devrait dépasser sans ({sans:.3f})"


def test_determinisme():
    """Deux calculs identiques → champ identique (zéro RNG)."""
    a = _field("ete", House())
    b = _field("ete", House())
    assert a.data == b.data, "le LightField doit être déterministe"
    print("  [déterminisme] deux calculs identiques ✓")


def main() -> int:
    tests = [test_nord_plus_sombre_que_sud, test_ombre_plus_longue_en_hiver,
             test_albedo_espalier, test_determinisme]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"[ombre] PASS — {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"[ombre] FAIL — {t.__name__} : {e}")
    if failed:
        print(f"\n[ombre] {failed}/{len(tests)} test(s) en échec")
        return 1
    print(f"\n[ombre] OK — {len(tests)} tests verts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
