"""
SYMBIOSE — tests/bancs/test_climatique.py
Oracles des bancs CLIMATIQUES. Tronçon ① : `secheresse_sable`. Tronçon ③ :
`acclimatation` (durcissement plastique) et `ombre_dense` (carence lumineuse).

Usage (depuis data/code/) : python3 -m tests.bancs.test_climatique
"""
from .oracle import (run_banc, run_banc_trace, premiere_plante, signes_du_plot,
                     champs_climat, SEED)
from sim.weather import weather_at

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


# Fenêtre déterministe (seed serveur) où une averse-état `Pluie prolongée` tombe :
# w=33 sous pluie, encadrée de calme (w=32 avant, w=34 calme). On trace 38 semaines
# et on lit l'état APRÈS chaque tick (l'indice 0 = état après le tick de la semaine 1).
W_PLUIE = 33    # `weather_at(SEED, 33).kind == "Pluie prolongée"` (vérifié dans l'oracle)


def test_pluie_thermique():
    """Couplage amont pluie → air → sol (correctif sprint germination thermique ①).
    Sous une averse, l'air REFROIDIT (delta froid neuf, le trou comblé), le sol suit
    (T_sol baisse), et la baisse d'humidité est FREINÉE par l'apport d'eau. Sens des
    couplages en tendance/borne, pas d'égalité fragile."""
    assert weather_at(SEED, W_PLUIE).kind == "Pluie prolongée", \
        "fenêtre de pluie déplacée — le seed serveur a changé ?"

    def observe(gs, _engine):
        # `gs["week"]` a déjà été incrémenté en fin de tick → semaine OBSERVÉE = week-1.
        return {"week": gs["week"] - 1, **champs_climat(gs)}

    _, _, traces = run_banc_trace("pluie_thermique", semaines=38, observe=observe)
    par_sem = {t["week"]: t for t in traces}
    avant, pluie, apres = par_sem[W_PLUIE - 1], par_sem[W_PLUIE], par_sem[W_PLUIE + 1]

    # 1. T_air plus BAS sous l'averse que la semaine calme précédente (delta froid).
    check("pluie — T_air baisse sous l'averse",
          pluie["temperature_air"] < avant["temperature_air"],
          f"avant={avant['temperature_air']:.2f} pluie={pluie['temperature_air']:.2f}")
    # 2. T_sol baisse aussi (l'air froid + nébulosité refroidissent le microclimat).
    check("pluie — T_sol baisse sous l'averse",
          pluie["temperature_sol"] < avant["temperature_sol"],
          f"avant={avant['temperature_sol']:.2f} pluie={pluie['temperature_sol']:.2f}")
    # 3. Apport d'eau : le DELTA d'humidité du tick de pluie (signé, current − prev) est
    #    plus ÉLEVÉ (moins négatif) que celui du tick calme précédent — l'averse compense
    #    en partie le drainage estival qui, lui, fait baisser chaque semaine calme.
    dhum_calme = avant["humidite"] - par_sem[W_PLUIE - 2]["humidite"]
    dhum_pluie = pluie["humidite"] - avant["humidite"]
    check("pluie — l'averse FREINE la baisse d'humidité",
          dhum_pluie > dhum_calme,
          f"dhum_calme={dhum_calme:+.4f} dhum_pluie={dhum_pluie:+.4f}")
    # 4. Au tick SUIVANT (calme), l'air se réchauffe : le froid était bien TRANSITOIRE.
    check("pluie — T_air remonte au retour du calme",
          apres["temperature_air"] > pluie["temperature_air"],
          f"pluie={pluie['temperature_air']:.2f} apres={apres['temperature_air']:.2f}")


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Oracles bancs climatiques (tronçons ①③)")
    print("=" * 60)
    test_secheresse_sable()
    test_acclimatation()
    test_ombre_dense()
    test_pluie_thermique()
    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
