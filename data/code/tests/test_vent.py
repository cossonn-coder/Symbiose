"""
SYMBIOSE — tests/test_vent.py
Test de la MASSE D'AIR pure (sprint VENT & ÉVAPOTRANSPIRATION, tronçon ①).
Spec : `docs/conception/CONCEPTION_VENT_EVAPOTRANSPIRATION.md` §2 + kickoff
`sprints/sprint_vent_evapotranspiration/t1_vent_masse_air.md`.

Vérifie que `sim/wind.py` est :
  A. DÉTERMINISTE  — même (seed, week) → même état, runs répétés identiques ;
  B. BORNÉ         — force ≥ 0, direction ∈ [0, 2π), nébulosité ∈ [0, 1],
                     profil de risées de longueur SUBTICKS ;
  C. SAISONNIER    — la force moyenne de l'HIVER > celle de l'ÉTÉ (automne/hiver
                     plus venteux, §2.1) ;
  D. RÉACTIF À LA MÉTÉO — une Tempête force une force HAUTE ;
  E. GOLDEN-NEUTRE — aucun symbole de `sim.wind` n'est lu par l'engine/boucle
                     (preuve que le calcul est isolé, non câblé).

Déterminisme total (fonctions pures, aucun RNG live).
Usage (depuis data/code/) :
  python3 -m tests.test_vent
"""
import math

from sim.weather import weather_at
from sim.wind import (
    wind_at, gust_profile, nebulosite_dynamique, WindState, SUBTICKS,
)

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


SEED = 12345


# --- A. Déterminisme -------------------------------------------------------
def test_determinisme():
    for week in (1, 7, 52, 53, 137, 999):
        a = wind_at(SEED, week)
        b = wind_at(SEED, week)
        check(f"wind_at reproductible s{week}", a == b, f"{a}")
    check("gust_profile reproductible",
          gust_profile(SEED, 40) == gust_profile(SEED, 40))
    check("nebulosite_dynamique reproductible",
          nebulosite_dynamique(SEED, 40) == nebulosite_dynamique(SEED, 40))
    # Deux seeds différents → régimes de vent dominants différents (terrains uniques).
    d1 = wind_at(SEED, 10).direction
    d2 = wind_at(SEED + 1, 10).direction
    check("seed différent → direction différente", d1 != d2, f"{d1} vs {d2}")


# --- B. Bornes -------------------------------------------------------------
def test_bornes():
    ok_force = ok_dir = ok_neb = True
    for week in range(1, 261):   # 5 ans
        w = wind_at(SEED, week)
        if not (isinstance(w, WindState) and w.force >= 0.0):
            ok_force = False
        if not (0.0 <= w.direction < 2.0 * math.pi):
            ok_dir = False
        neb = nebulosite_dynamique(SEED, week)
        if not (0.0 <= neb <= 1.0):
            ok_neb = False
    check("force ≥ 0 sur 5 ans", ok_force)
    check("direction ∈ [0, 2π) sur 5 ans", ok_dir)
    check("nébulosité ∈ [0, 1] sur 5 ans", ok_neb)
    prof = gust_profile(SEED, 40)
    check("profil de risées = SUBTICKS facteurs", len(prof) == SUBTICKS, f"{prof}")
    check("profil de risées > 0", all(f > 0 for f in prof))


# --- C. Saisonnalité (hiver plus venteux que l'été) ------------------------
def _force_moyenne_fond(seed, semaines):
    # Force de FOND seule (on évite les semaines à événement venteux qui écraseraient
    # le signal saisonnier). On échantillonne et on moyenne.
    vals = []
    for w in semaines:
        ev = weather_at(seed, w)
        if ev.kind in ("Tempête", "Orage"):
            continue
        vals.append(wind_at(seed, w).force)
    return sum(vals) / len(vals)


def test_saisonnalite():
    # Hiver ≈ semaines 40-52, été ≈ semaines 14-26, sur plusieurs années.
    hiver = [y * 52 + w for y in range(8) for w in range(40, 53)]
    ete = [y * 52 + w for y in range(8) for w in range(14, 27)]
    f_hiver = _force_moyenne_fond(SEED, hiver)
    f_ete = _force_moyenne_fond(SEED, ete)
    check("hiver plus venteux que l'été", f_hiver > f_ete,
          f"hiver={f_hiver:.3f} > été={f_ete:.3f}")


# --- D. Réactivité à la météo ----------------------------------------------
def test_evenement_venteux():
    # On cherche une vraie Tempête dans le flux et on vérifie une force HAUTE.
    tempete_week = next(
        (w for w in range(1, 5000) if weather_at(SEED, w).kind == "Tempête"),
        None,
    )
    check("une Tempête existe dans le flux", tempete_week is not None)
    if tempete_week is not None:
        f = wind_at(SEED, tempete_week).force
        check("Tempête → force haute (> 0.7)", f > 0.7, f"force={f:.3f}")


# --- E. Golden-neutre : module non câblé -----------------------------------
def test_non_cable():
    # Preuve d'isolement : ni la boucle moteur (qui porte l'hydrologie) ni le
    # sérialiseur de snapshot (qui lit weather_state) n'importent sim.wind.
    import sim.engine.boucle as boucle
    src_b = open(boucle.__file__).read()
    check("boucle.py (hydrologie) n'importe pas sim.wind", "sim.wind" not in src_b)


def main():
    print("=== test_vent (tronçon ① masse d'air) ===")
    test_determinisme()
    test_bornes()
    test_saisonnalite()
    test_evenement_venteux()
    test_non_cable()
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"\n[test_vent] {passed}/{total} OK")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
