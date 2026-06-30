"""
SYMBIOSE — tests/bancs/test_climatique.py
Oracles des bancs CLIMATIQUES. Tronçon ① : `secheresse_sable`. Tronçon ③ :
`acclimatation` (durcissement plastique) et `ombre_dense` (carence lumineuse).

Usage (depuis data/code/) : python3 -m tests.bancs.test_climatique
"""
from .oracle import (run_banc, run_banc_trace, premiere_plante, signes_du_plot,
                     champs_climat, SEED)
from sim.weather import weather_at
import plants

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


def _levees_par_tuile(game_state) -> dict:
    """Taux de levée (plantes vivantes / plots) par `tile_id`, après le tick observé.
    Chaque tuile du banc multifacteur porte GMF_ROWS×GMF_COLS grains ; le compte des
    plantes vivantes / nb de plots = proxy de la proba de la porte de niche."""
    taux = {}
    for tile in game_state["tiles"]:
        plots = tile.grid_rows * tile.grid_cols
        vivantes = sum(1 for p in tile.plants if p.is_alive)
        taux[tile.tile_id] = vivantes / plots
    return taux


def test_germination_multifacteur():
    """Banc de CALIBRAGE des portes de germination (sprint germination thermique ⑥).
    Balaye T_sol et pH toutes choses égales par ailleurs et asserte le SENS des
    taux de levée (tendances/bornes, jamais d'égalité fragile). Fenêtre = 1 tick :
    le gradient de T_sol forcée n'est net qu'avant que la thermique ne le relaxe."""
    # 1 tick : le gradient de T_sol forcée est encore distinct (relaxe ensuite).
    game_state, _ = run_banc("germination_multifacteur", semaines=1)
    taux = _levees_par_tuile(game_state)

    def t_levee(esp, t):  return taux[f"GMF_T_{t:g}_{esp}"]
    def ph_levee(ph):     return taux[f"GMF_PH_{ph:g}_carotte"]

    # a. Sous T_GERM_FLOOR (T_sol forcé 0 °C) : levée NULLE (plancher froid dur).
    check("germ — nulle sous T_GERM_FLOOR (carotte, 0 °C)", t_levee("carotte", 0.0) == 0.0,
          f"taux={t_levee('carotte', 0.0):.3f}")
    check("germ — nulle sous T_GERM_FLOOR (tomate, 0 °C)", t_levee("tomate", 0.0) == 0.0,
          f"taux={t_levee('tomate', 0.0):.3f}")

    # b. Rustique (carotte, opt 13) : la levée CROÎT du frais vers l'optimum…
    check("germ — carotte croît 5→14 °C", t_levee("carotte", 5.0) < t_levee("carotte", 14.0),
          f"5°C={t_levee('carotte', 5.0):.3f} 14°C={t_levee('carotte', 14.0):.3f}")
    # …puis DÉCROÎT au-delà (cloche : sol trop chaud pour une rustique).
    check("germ — carotte décroît 18→30 °C", t_levee("carotte", 30.0) < t_levee("carotte", 18.0),
          f"18°C={t_levee('carotte', 18.0):.3f} 30°C={t_levee('carotte', 30.0):.3f}")

    # c. Frileuse (tomate, opt 22) : la levée CROÎT vers le chaud (fenêtre étroite haute).
    check("germ — tomate croît 11→26 °C", t_levee("tomate", 11.0) < t_levee("tomate", 26.0),
          f"11°C={t_levee('tomate', 11.0):.3f} 26°C={t_levee('tomate', 26.0):.3f}")

    # d. À T_sol intermédiaire (11 °C, frais), la rustique DEVANCE NETTEMENT la frileuse.
    check("germ — au frais (11 °C) carotte > tomate", t_levee("carotte", 11.0) > t_levee("tomate", 11.0),
          f"carotte={t_levee('carotte', 11.0):.3f} tomate={t_levee('tomate', 11.0):.3f}")

    # e. Cloche pH (carotte ph_opt 6.8) : levée à l'optimum > aux extrêmes acide ET basique.
    check("germ — pH optimum (6.8) > acide (4.0)", ph_levee(6.8) > ph_levee(4.0),
          f"pH6.8={ph_levee(6.8):.3f} pH4.0={ph_levee(4.0):.3f}")
    check("germ — pH optimum (6.8) > basique (8.5)", ph_levee(6.8) > ph_levee(8.5),
          f"pH6.8={ph_levee(6.8):.3f} pH8.5={ph_levee(8.5):.3f}")

    # f. Sensibilité LUMIÈRE — la porte de niche est lue DIRECTEMENT (pure), car
    #    l'engine recalcule `eco.lumiere` chaque tick (un forçage de champ serait
    #    écrasé). niche_index ∝ lumière → levée croît avec la lumière disponible.
    sb = next(iter(game_state["eco"].values())).seed_bank
    cls = plants.PLANT_CATALOGUE["tomate"]
    n_sombre = sb.niche_index(1, 1, 0.2, 0.0, 1.0, 0.0)
    n_clair  = sb.niche_index(1, 1, 1.0, 0.0, 1.0, 0.0)
    check("germ — niche croît avec la lumière (porte directe)", n_clair > n_sombre,
          f"lum0.2={n_sombre:.3f} lum1.0={n_clair:.3f}")


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Oracles bancs climatiques (tronçons ①③⑥)")
    print("=" * 60)
    test_secheresse_sable()
    test_acclimatation()
    test_ombre_dense()
    test_pluie_thermique()
    test_germination_multifacteur()
    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
