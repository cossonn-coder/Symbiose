"""
SYMBIOSE — tests/bancs/test_climatique.py
Oracles des bancs CLIMATIQUES. Tronçon ① : `secheresse_sable`. Tronçon ③ :
`acclimatation` (durcissement plastique) et `ombre_dense` (carence lumineuse).

Usage (depuis data/code/) : python3 -m tests.bancs.test_climatique
"""
from .oracle import run_banc, premiere_plante, signes_du_plot

# Signes de DÉGÂT (souffrance ACTUELLE) — par opposition à `acclimatation`, qui est
# une RÉPONSE (durcissement). Le banc `acclimatation` doit n'en montrer AUCUN, sinon
# le stress a blessé et masque le durcissement (cf. priorités de sim/semiologie).
SIGNES_DEGAT = {"secheresse", "ombre", "asphyxie", "chlorose", "ravageurs",
                "senescence", "maladie", "gel", "grele"}

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK  " if cond else "FAIL"
    print(f"  [{flag}] {name}" + (f" — {detail}" if detail else ""))


def test_secheresse_sable():
    """Après quelques semaines sur sable sec sans arrosage, le basilic montre le
    signe `secheresse` (et reste vivant — c'est un stress, pas une mort)."""
    # 6 semaines : le signe est présent dès la sem. 1 (drought_memory pré-chargé) ;
    # on en simule plusieurs pour vérifier qu'il PERSISTE (le sol drainant maintient
    # le déficit), pas un flash d'init. Banc rapide à observer au F5 (< 15 sem).
    game_state, _ = run_banc("secheresse_sable", semaines=6)
    plante = premiere_plante(game_state)
    signes = signes_du_plot(game_state, plante)
    check("plante vivante", plante.is_alive, f"alive={plante.is_alive}")
    check("signe `secheresse` présent", "secheresse" in signes,
          f"signes={sorted(signes)}")


def test_acclimatation():
    """Basilic sous déficit hydrique DOUX et prolongé : il s'endurcit (sur-expression
    plastique → feuillage glauque) SANS souffrir. Le signe `acclimatation` est
    présent ET seul — aucun signe de dégât concurrent ne le masque."""
    game_state, _ = run_banc("acclimatation", semaines=6)
    plante = premiere_plante(game_state)
    signes = signes_du_plot(game_state, plante)
    check("acclimatation — plante vivante", plante.is_alive, f"alive={plante.is_alive}")
    check("acclimatation — signe `acclimatation` présent", "acclimatation" in signes,
          f"signes={sorted(signes)}")
    check("acclimatation — aucun signe de dégât concurrent",
          not (signes & SIGNES_DEGAT), f"signes={sorted(signes)}")


def test_ombre_dense():
    """Basilic héliophile sous l'ombre INSTALLÉE d'une maison haute : étiolement →
    signe `ombre`. ⚠️ Rendu C# manquant (dette 0.5.2) : oracle vert + écran muet au
    F5 = bug RENDU confirmé (cas-école du tri D47, à rappeler au bilan ⑤)."""
    game_state, _ = run_banc("ombre_dense", semaines=6)
    plante = premiere_plante(game_state)
    signes = signes_du_plot(game_state, plante)
    check("ombre — plante vivante", plante.is_alive, f"alive={plante.is_alive}")
    check("ombre — signe `ombre` présent", "ombre" in signes,
          f"signes={sorted(signes)}")


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Oracles bancs climatiques (tronçons ①③)")
    print("=" * 60)
    test_secheresse_sable()
    test_acclimatation()
    test_ombre_dense()
    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
