"""
SYMBIOSE — tests/bancs/test_edaphique.py
Oracles des bancs ÉDAPHIQUES (tronçon ②) : chlorose pH / asphyxie / carence NPK.

Chaque oracle monte le banc via SA fabrique, simule quelques semaines, puis lit
les signes EXACTEMENT comme la vue (`semiologie.leaf_symptoms` via oracle.py).
Vert + écran muet ⇒ bug rendu C# (tri D47).

Usage (depuis data/code/) : python3 -m tests.bancs.test_edaphique
"""
from .oracle import run_banc, premiere_plante, signes_du_plot

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK  " if cond else "FAIL"
    print(f"  [{flag}] {name}" + (f" — {detail}" if detail else ""))


def test_chlorose_acidophile():
    """Myrtille acidophile sur sol alcalin (pH ≈ 8.2) : le signe `chlorose`
    apparaît, la plante reste vivante (carence fonctionnelle, pas mort)."""
    game_state, _ = run_banc("chlorose_acidophile", semaines=6)
    plante = premiere_plante(game_state)
    signes = signes_du_plot(game_state, plante)
    check("chlorose — plante vivante", plante.is_alive, f"alive={plante.is_alive}")
    check("chlorose — signe `chlorose` présent", "chlorose" in signes,
          f"signes={sorted(signes)}")


def test_asphyxie_argile():
    """Basilic sur argile gorgée d'eau : le signe `asphyxie` apparaît et persiste
    (l'argile retient l'excès). Tranche D47-C2 : le moteur SAIT émettre le signe
    quand l'excès d'eau est SOUTENU."""
    game_state, _ = run_banc("asphyxie_argile", semaines=6)
    plante = premiere_plante(game_state)
    signes = signes_du_plot(game_state, plante)
    check("asphyxie — plante vivante", plante.is_alive, f"alive={plante.is_alive}")
    check("asphyxie — signe `asphyxie` présent", "asphyxie" in signes,
          f"signes={sorted(signes)}")


def test_carence_npk():
    """Deux tournesols jumeaux ; le carencé (n=p=k≈0.05) reste sur un sol pauvre et
    croît MOINS que le témoin riche. Tranche D47-C6 : NPK uniformément pauvres =
    symptôme normal d'un sol épuisé, pas un bug de la carte. PAS de mort (D41)."""
    game_state, _ = run_banc("carence_npk", semaines=12)
    tiles = game_state["tiles"]
    carence, temoin = tiles[0], tiles[1]
    plante_c, plante_t = carence.plants[0], temoin.plants[0]
    eco_c = game_state["eco"][carence.tile_id]

    n_carence = eco_c.n.at_plot(4, 4)
    check("carence — n du sol reste BAS (heatmap pauvre normale)", n_carence < 0.3,
          f"n={n_carence:.3f}")
    h_c, h_t = plante_c.current_height, plante_t.current_height
    check("carence — croissance bridée vs témoin", h_c < h_t,
          f"h_carence={h_c:.1f} < h_temoin={h_t:.1f}")
    check("carence — plante vivante (pas de mort édaphique, D41)",
          plante_c.is_alive, f"alive={plante_c.is_alive}")


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Oracles bancs édaphiques (tronçon ②)")
    print("=" * 60)
    test_chlorose_acidophile()
    test_asphyxie_argile()
    test_carence_npk()
    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
