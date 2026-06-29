"""
SYMBIOSE — tests/test_rosee.py
Tests ciblés du cycle thermo-hydrique nocturne (sprint météo→champs ②, §3) :
rosée liquide, gelée blanche + fonte différée, et les régimes de TENSION voulus.

Le helper `rosee.tick_rosee` est PUR (zéro RNG) : on l'exerce hors golden sur des
EcoFields à conditions forcées (humidité/litière/neige, T_air et nébulosité passées
en argument). Le golden écologique reste l'autorité du déterminisme.

Couvre la définition de done du kickoff :
  1. nuit CLAIRE + sol HUMIDE + sol NU + T_air > 0 → rosée déposée (humidité ↑).
  2. nuit COUVERTE → ~rien (peu de refroidissement → t_min ≈ T_air → cond ≈ 0).
  3. sol PAILLÉ (litière) → moins de rosée qu'un sol nu (couvert isole, t_min haut).
  4. sol SEC → peu de rosée (point de rosée bas).
  5. régime GELÉE BLANCHE (T_air ≤ 0) → givre accumulé, humidité INCHANGÉE ce tick ;
     puis FONTE différée au réchauffement → l'eau gelée est restituée à l'humidité.
  6. déterminisme : deux runs identiques → mêmes valeurs.

Usage (depuis data/code/) :
  python3 -m tests.test_rosee
"""
import sys

from fields import init_eco
from fields.ecofields.constants import (ECART_ROSEE_SEC, GAIN_HUM_ROSEE,
                                        ROSEE_PAR_DEGRE, RAYONNEMENT_NOCTURNE)

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK " if cond else "XX "
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _eco(humidite=1.5):
    """Mini-sol 3×3 à humidité uniforme, sol terre, sans litière ni neige."""
    return init_eco("R", 3, 3, humidite=humidite, microbiome=0.0, soil_type="terre")


def _hum_moy(eco):
    return eco.humidite.average()


# ---------------------------------------------------------------------------
# 1 + 4. Sol humide vs sol sec sous nuit claire chaude (> 0 °C)
# ---------------------------------------------------------------------------

def test_rosee_humide_vs_sec():
    print("\n[1/4] rosée : sol nu humide capte > sol nu sec ; les deux > 0")
    # T_air > 0, ciel clair (neb=0) : t_min = T_air − RAYONNEMENT_NOCTURNE (sol nu).
    t_air, neb = 8.0, 0.0
    eco_humide = _eco(humidite=2.0)
    eco_sec    = _eco(humidite=0.2)
    h0_humide, h0_sec = _hum_moy(eco_humide), _hum_moy(eco_sec)
    eco_humide.tick_rosee(t_air, neb)
    eco_sec.tick_rosee(t_air, neb)
    d_humide = _hum_moy(eco_humide) - h0_humide
    d_sec    = _hum_moy(eco_sec) - h0_sec
    check("rosée déposée sur sol humide (humidité ↑)", d_humide > 0,
          f"+{d_humide:.4f}")
    check("sol sec : peu/pas de rosée (point de rosée bas)", d_sec < d_humide,
          f"sec +{d_sec:.4f} < humide +{d_humide:.4f}")


# ---------------------------------------------------------------------------
# 2. Nuit couverte → ~rien
# ---------------------------------------------------------------------------

def test_nuit_couverte():
    print("\n[2] nuit couverte : peu de refroidissement → ~pas de rosée")
    t_air = 8.0
    eco_clair = _eco(humidite=2.0)
    eco_couvert = _eco(humidite=2.0)
    eco_clair.tick_rosee(t_air, 0.0)     # ciel clair
    eco_couvert.tick_rosee(t_air, 0.95)  # ciel couvert
    d_clair = _hum_moy(eco_clair) - 2.0
    d_couvert = _hum_moy(eco_couvert) - 2.0
    check("ciel couvert dépose bien MOINS que ciel clair", d_couvert < d_clair,
          f"couvert +{d_couvert:.4f} < clair +{d_clair:.4f}")
    check("ciel couvert : dépôt quasi nul", d_couvert < 0.5 * d_clair)


# ---------------------------------------------------------------------------
# 3. Sol paillé (litière) isole → moins de rosée qu'un sol nu
# ---------------------------------------------------------------------------

def test_paille_vs_nu():
    print("\n[3] sol paillé (litière) se refroidit moins → moins de rosée")
    t_air, neb = 8.0, 0.0
    eco_nu = _eco(humidite=2.0)
    eco_paille = _eco(humidite=2.0)
    # Litière dense sur chaque plot du sol paillé → couvert haut dans t_min_nuit.
    for r in range(eco_paille.rows):
        for c in range(eco_paille.cols):
            eco_paille.deposer_litiere(r, c, "feuille", 3.0)
    eco_nu.tick_rosee(t_air, neb)
    eco_paille.tick_rosee(t_air, neb)
    d_nu = _hum_moy(eco_nu) - 2.0
    d_paille = _hum_moy(eco_paille) - 2.0
    check("sol paillé dépose moins que sol nu", d_paille < d_nu,
          f"paillé +{d_paille:.4f} < nu +{d_nu:.4f}")


# ---------------------------------------------------------------------------
# 5. Gelée blanche : givre accumulé puis FONTE différée
# ---------------------------------------------------------------------------

def test_givre_puis_fonte():
    print("\n[5] gelée blanche : givre accumulé (humidité figée) puis fonte différée")
    # T_air < 0, ciel clair → t_min = T_air − RAYONNEMENT_NOCTURNE < 0 → régime givre.
    # Le point de rosée doit rester > t_min pour qu'il y ait condensation : avec
    # humidité 2.0, t_rosee = T_air − 6 + 5·(2/3) ≈ T_air − 2.67 > T_air − 5 = t_min.
    eco = _eco(humidite=2.0)
    h0 = _hum_moy(eco)
    eco.tick_rosee(-1.0, 0.0)   # nuit givrante
    h_apres_gel = _hum_moy(eco)
    givre_moy = eco.givre.average()
    check("humidité INCHANGÉE la nuit de gel (pas d'eau liquide)",
          abs(h_apres_gel - h0) < 1e-12, f"Δhum={h_apres_gel - h0:.2e}")
    check("givre accumulé sur les plots", givre_moy > 0, f"givre={givre_moy:.4f}")
    # Réchauffement : nuit claire DOUCE → t_min > 0 → fonte différée + rosée.
    eco.tick_rosee(8.0, 0.0)
    check("fonte : l'eau gelée est restituée à l'humidité",
          _hum_moy(eco) > h_apres_gel, f"hum {h_apres_gel:.4f}→{_hum_moy(eco):.4f}")
    check("givre remis à zéro après la fonte", eco.givre.average() == 0.0)


# ---------------------------------------------------------------------------
# 6. Déterminisme
# ---------------------------------------------------------------------------

def test_determinisme():
    print("\n[6] déterminisme : deux runs identiques → mêmes valeurs")
    def run():
        e = _eco(humidite=1.5)
        log = e.tick_rosee(7.0, 0.1)
        return round(_hum_moy(e), 12), round(e.givre.average(), 12), tuple(log)
    check("rejoué = identique", run() == run())


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Tests rosée & gelée blanche (météo→champs ②)")
    print("=" * 60)
    test_rosee_humide_vs_sec()
    test_nuit_couverte()
    test_paille_vs_nu()
    test_givre_puis_fonte()
    test_determinisme()

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    sys.exit(0 if passed == total else 1)
