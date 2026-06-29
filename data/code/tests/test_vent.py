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
  E. CÂBLÉ (tronçon ②) — la boucle lit `wind_at` et injecte la masse d'air dans
                     l'évaporation enrichie (`tick_hydrology`). Au ① ce test
                     vérifiait l'ISOLEMENT (module non câblé, golden neutre) ; le ②
                     câble le vent → re-figeage golden LARGE annoncé.

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


# --- E. Câblage du vent dans l'évaporation (tronçon ②) ---------------------
def test_cable_evapotranspiration():
    # Au tronçon ① le module était GOLDEN-NEUTRE (preuve d'isolement : la boucle
    # n'importait pas sim.wind). Le tronçon ② le CÂBLE : la masse d'air pilote
    # désormais l'évaporation enrichie (§3) → ce test bascule de « non câblé » à
    # « câblé » (le golden re-fige LARGE, annoncé). On vérifie que la boucle lit
    # bien la force de masse d'air et l'injecte dans l'hydrologie.
    import sim.engine.boucle as boucle
    src_b = open(boucle.__file__).read()
    check("boucle.py câble wind_at (masse d'air)", "wind_at" in src_b)
    check("boucle.py passe vent_masse_air à tick_hydrology",
          "vent_masse_air=" in src_b)


# --- F. Champ d'abri spatial (tronçon ③) -----------------------------------
def test_abri_spatial():
    """`eco.vent` spatialisé (§4) : un obstacle (la maison) réduit le vent dans son
    SILLAGE sous le vent, et le sillage SUIT la direction du vent. CACHE : à
    (obstacles, direction) inchangés, pas de recalcul (signature stable)."""
    from fields.ecofields import init_eco
    from world.building import House
    from fields.abri import compute_abri, _signature, _obstacles

    eco = init_eco("t", 40, 40)            # tuile assez large pour loger un sillage
    house = House()
    force = 0.8

    # Vent venant du NORD (direction ≈ 0 dans le repère `wind_at`/`_direction_at`).
    compute_abri(eco, [], house, (0.0, 0.0), 0.0, force)
    vals_nord = [eco.vent.at_plot(r, c) for r in range(40) for c in range(40)]
    n_abrite_nord = sum(1 for v in vals_nord if v < force - 1e-9)
    check("un obstacle abrite des plots (vent < masse d'air)", n_abrite_nord > 0,
          f"{n_abrite_nord} plots abrités")
    check("le vent reste borné ≥ 0", all(v >= 0.0 for v in vals_nord))
    # Venturi : certains plots dépassent la masse d'air (goulet en frange de sillage).
    check("venturi : des plots accélérés (> masse d'air)",
          any(v > force + 1e-9 for v in vals_nord))

    # Le sillage SUIT la direction : tourner le vent change la carte d'abri.
    compute_abri(eco, [], house, (0.0, 0.0), math.pi / 2.0, force)
    vals_est = [eco.vent.at_plot(r, c) for r in range(40) for c in range(40)]
    check("changer la direction déplace le sillage", vals_nord != vals_est)

    # Cache : même signature à direction quasi identique (sous le pas angulaire).
    obs = _obstacles([], house, (0.0, 0.0))
    check("cache stable sous le pas angulaire",
          _signature(obs, 0.0) == _signature(obs, 0.05))
    check("cache invalidé au-delà du pas angulaire",
          _signature(obs, 0.0) != _signature(obs, 1.0))

    # Force nulle (calme) → champ NUL partout (golden-safe : évaporation inchangée).
    compute_abri(eco, [], house, (0.0, 0.0), 0.0, 0.0)
    check("vent calme → champ nul",
          all(eco.vent.at_plot(r, c) == 0.0 for r in range(40) for c in range(40)))


def main():
    print("=== test_vent (① masse d'air + ③ abri spatial) ===")
    test_determinisme()
    test_bornes()
    test_saisonnalite()
    test_evenement_venteux()
    test_cable_evapotranspiration()
    test_abri_spatial()
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"\n[test_vent] {passed}/{total} OK")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
