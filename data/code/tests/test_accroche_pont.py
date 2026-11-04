"""
SYMBIOSE — tests/test_accroche_pont.py
Clé `support` du snapshot (FORMES DES PLANTES ⑥, pont 0.6.8) : l'écart du pied à son appui,
que la vue lit pour dessiner le haricot autour de son tuteur. Absente pour une plante libre,
sans écart pour le mur. Usage (depuis data/code/) : python3 -m tests.test_accroche_pont
"""
from types import SimpleNamespace

from tools.simserver.accroche_pont import marquer_accroche
from world import Support, MUR


def _plante(support):
    return SimpleNamespace(support=support, x_cm=100.0, y_cm=200.0)


def main() -> int:
    libre = {}
    marquer_accroche(libre, _plante(None))
    assert libre == {}, libre

    tuteur = Support(support_type="tuteur", x_cm=140.0, y_cm=170.0, height_cm=200.0, finesse="fin")
    posee = {}
    marquer_accroche(posee, _plante((tuteur, 200.0)))
    assert posee["support"] == {"type": "tuteur", "height_cm": 200.0, "dx_cm": 40.0, "dy_cm": -30.0}, posee

    hote = SimpleNamespace(x_cm=110.0, y_cm=200.0)
    vivant = {}
    marquer_accroche(vivant, _plante((hote, 119.0)))
    assert vivant["support"] == {"type": "hote", "height_cm": 119.0, "dx_cm": 10.0, "dy_cm": 0.0}, vivant

    mur = {}
    marquer_accroche(mur, _plante((MUR, 600.0)))
    assert mur["support"] == {"type": "mur", "height_cm": 600.0}, mur
    print("[accroche pont] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
