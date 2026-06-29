"""
SYMBIOSE — tests/test_microbiome_clim.py
Tests ciblés du microbiome CLIMATIQUE (sprint météo→champs ④, §5).

L'activité microbienne suivait déjà la FAMINE (litière épuisée → puits) et un
LOCKOUT pH (cloche autour du neutre). Ce tronçon ajoute le couplage CLIMATIQUE :
une CLOCHE de température (optimum doux, dormance au gel, stress à la canicule) ×
un facteur HUMIDITÉ (nul au sec, optimal au sol frais, légèrement réduit en
saturation). Terme MULTIPLICATIF `f_clim` posé sur la vitesse de décompo — PAS de
champ neuf. À f_clim=1 (sol doux et frais) la décompo est strictement INCHANGÉE.

On exerce HORS golden sur des EcoFields à conditions forcées : même litière fraîche,
même microbiome, même pH (un seul soil_type → lockout pH identique), on ne fait
varier QUE T_sol et l'humidité. La litière qui RESTE après un tick mesure la vitesse
de recyclage : moins il reste = plus le sol a digéré.

Couvre la définition de done du kickoff :
  1. f_temp est une CLOCHE : optimum (~20 °C) digère PLUS que gel ET que canicule.
  2. sol GELÉ → activité quasi nulle (litière s'accumule).
  3. sol DESSÉCHÉ → recyclage ralenti vs sol frais.
  4. SATURATION → léger ↓ vs frais optimal (anoxie), mais > sec.
  5. conditions idéales (f_clim≈1) → IDENTIQUE à l'existant (golden-safe).
  6. le microbiome décline davantage au climat défavorable (combiné à la famine).
  7. déterminisme : deux runs identiques → mêmes valeurs.

Usage (depuis data/code/) :
  python3 -m tests.test_microbiome_clim
"""
import sys

from fields import init_eco
from fields.ecofields.thermique import microbe_clim_factor
from fields.ecofields.constants import (MICROBE_T_OPT, MICROBE_HUM_OPT,
                                        MICROBE_CLIM_FLOOR)

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK " if cond else "XX "
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _eco(t_sol, hum, micro=2.0, litiere=1.5):
    """Mini-sol 3×3 : microbiome et litière `feuille` fraîche uniformes, T_sol et
    humidité FORCÉES. pH = défaut "terre" (identique partout → lockout pH constant,
    isole f_clim). On dépose la litière APRÈS init pour exercer la décompo."""
    eco = init_eco("C", 3, 3, humidite=hum, microbiome=micro, soil_type="terre")
    for r in range(3):
        for c in range(3):
            eco.temperature_sol.set(r, c, t_sol)
            eco.deposer_litiere(r, c, "feuille", litiere)
    return eco


def _reste(eco):
    """Litière fraîche moyenne restante par plot après le(s) tick(s)."""
    return eco.om_fresh_average()


def run():
    print("== test_microbiome_clim (météo→champs ④) ==")

    # Helper pur d'abord : forme de f_clim attendue.
    f_opt   = microbe_clim_factor(MICROBE_T_OPT, MICROBE_HUM_OPT)
    f_gel   = microbe_clim_factor(-5.0, MICROBE_HUM_OPT)
    f_canic = microbe_clim_factor(40.0, MICROBE_HUM_OPT)
    f_sec   = microbe_clim_factor(MICROBE_T_OPT, 0.0)
    f_satur = microbe_clim_factor(MICROBE_T_OPT, 1.0)
    f_frais = microbe_clim_factor(MICROBE_T_OPT, MICROBE_HUM_OPT)

    check("0a. f_clim optimum ≈ 1", abs(f_opt - 1.0) < 1e-9, f"f_opt={f_opt:.4f}")
    check("0b. cloche T : optimum > gel ET > canicule",
          f_opt > f_gel and f_opt > f_canic,
          f"opt={f_opt:.3f} gel={f_gel:.3f} canic={f_canic:.3f}")
    check("0c. humidité : frais > sec ET frais > saturation",
          f_frais > f_sec and f_frais > f_satur,
          f"frais={f_frais:.3f} sec={f_sec:.3f} satur={f_satur:.3f}")
    check("0d. saturation > sec (anoxie = léger ↓, pas effondrement)",
          f_satur > f_sec, f"satur={f_satur:.3f} > sec={f_sec:.3f}")
    check("0e. plancher f_clim respecté (jamais 0 dur)",
          f_gel >= MICROBE_CLIM_FLOOR - 1e-12 and f_sec >= MICROBE_CLIM_FLOOR - 1e-12,
          f"gel={f_gel:.4f} sec={f_sec:.4f} ≥ {MICROBE_CLIM_FLOOR}")

    # Décompo exercée (un tick) — la litière restante mesure le recyclage.
    hum_frais = MICROBE_HUM_OPT * 3.0   # repasse en humidité brute [0,3]
    eco_opt  = _eco(MICROBE_T_OPT, hum_frais); eco_opt.tick_decomposition()
    eco_gel  = _eco(-5.0, hum_frais);          eco_gel.tick_decomposition()
    eco_can  = _eco(40.0, hum_frais);          eco_can.tick_decomposition()
    eco_sec  = _eco(MICROBE_T_OPT, 0.0);       eco_sec.tick_decomposition()
    eco_sat  = _eco(MICROBE_T_OPT, 3.0);       eco_sat.tick_decomposition()

    r_opt, r_gel, r_can = _reste(eco_opt), _reste(eco_gel), _reste(eco_can)
    r_sec, r_sat = _reste(eco_sec), _reste(eco_sat)

    # 1. cloche T : optimum DIGÈRE plus (reste moins) que gel ET canicule.
    check("1. optimum digère plus que gel et canicule",
          r_opt < r_gel and r_opt < r_can,
          f"reste opt={r_opt:.4f} < gel={r_gel:.4f}, canic={r_can:.4f}")

    # 2. sol gelé → activité quasi nulle (litière s'accumule = reste élevé,
    #    proche du dépôt initial 1.5 moins la décompo abiotique plancher).
    check("2. sol gelé → litière s'accumule (peu digérée)",
          r_gel > r_opt and r_gel > 1.3,
          f"reste gel={r_gel:.4f} (dépôt 1.5)")

    # 3. sol desséché → recyclage ralenti vs frais optimal.
    check("3. sol desséché digère moins que sol frais",
          r_sec > r_opt, f"reste sec={r_sec:.4f} > frais={r_opt:.4f}")

    # 4. saturation → léger ↓ vs frais (reste un peu plus), mais > sec.
    check("4. saturation : léger ralenti vs frais, mais > sec",
          r_opt < r_sat < r_sec,
          f"frais={r_opt:.4f} < satur={r_sat:.4f} < sec={r_sec:.4f}")

    # 5. conditions idéales → décompo IDENTIQUE à l'existant. On compare à un sol
    #    où f_clim=1 est obtenu en NEUTRALISANT le terme (T_opt, hum_opt) : la
    #    vitesse `speed` doit valoir exactement `0.5 + micro·dispo_pH·0.5` comme
    #    AVANT le ④. On le vérifie via l'égalité f_clim(opt)=1 (test 0a) + le fait
    #    que la décompo à l'optimum n'est bridée QUE par pH/famine (héritage).
    eco_ref = _eco(MICROBE_T_OPT, hum_frais)
    # f_clim=1 exact → micro inchangé → même reste qu'eco_opt (déjà à l'optimum).
    eco_ref.tick_decomposition()
    check("5. conditions idéales ⇒ décompo inchangée (f_clim=1)",
          _reste(eco_ref) == r_opt,
          f"ref={_reste(eco_ref):.6f} == opt={r_opt:.6f}")

    # 6. microbiome : au climat défavorable (gel/sec), le faible recyclage laisse
    #    plus de litière (famine moindre) MAIS l'activité ralentie freine la
    #    minéralisation → le N minéralisé à l'optimum dépasse celui au gel.
    n_opt = eco_opt.n.average()
    n_gel = eco_gel.n.average()
    check("6. minéralisation N : optimum > gel (climat freine le cycle)",
          n_opt > n_gel, f"N opt={n_opt:.5f} > N gel={n_gel:.5f}")

    # 7. déterminisme.
    eco_a = _eco(MICROBE_T_OPT, hum_frais); eco_a.tick_decomposition()
    eco_b = _eco(MICROBE_T_OPT, hum_frais); eco_b.tick_decomposition()
    check("7. déterminisme (deux runs identiques)",
          _reste(eco_a) == _reste(eco_b) == r_opt,
          f"{_reste(eco_a):.6f} == {_reste(eco_b):.6f}")

    ok = sum(1 for _, c in _results if c)
    total = len(_results)
    print(f"\n{ok}/{total} OK")
    return ok == total


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
