"""
Mesure des températures EXTRÊMES de la semaine (sprint niche thermique, tronçon ①).

Lancer depuis `data/code/` :
    python3 ../../sprints/vegetal/genetique/sprint_niche_thermique/mesures/mesure_extremes.py

Seed 42, 8 ans (416 semaines). Plot de SOL NU SANS VENT : une `eco` factice dont
litière, neige, voile et vent valent 0 → `t_min_nuit_at` ne garde que T_air,
le rayonnement nocturne et (après ①) l'écart de la nuit la plus froide. Même calcul
que la mesure de conception du 2026-11-16 (`weather_state` = `temp_norm` +
`temperature_delta` + `nebulosite_dynamique`).

Affiche :
- nombre de semaines avec une nuit < 0 °C (total, par an) et le minimum ;
- nombre de semaines avec T_air < 0 °C (le garde historique du gel de `boucle.py`) ;
- T_air hebdo max et, si l'helper existe (après ①), le jour le plus chaud max.
"""
import os
import sys

sys.path.insert(0, os.getcwd())

from fields.ecofields import thermique           # noqa: E402
from sim.weather import weather_state            # noqa: E402

SEED, ANS = 42, 8


class _Zero:
    def at_plot(self, r, c):
        return 0.0


class _EcoNue:
    """Plot de sol nu, sans neige, sans voile, sans vent."""
    snow = 0.0
    vent = _Zero()

    def om_fresh_at(self, r, c):
        return 0.0

    def couvert_at(self, r, c):
        return 0.0


def main():
    eco = _EcoNue()
    t_max_fn = getattr(thermique, "t_max_jour", None)
    gel, gel_air, t_min, t_air_max, t_jour_max = 0, 0, 99.0, -99.0, -99.0
    par_an = [0] * ANS
    for week in range(1, 52 * ANS + 1):
        _, t_air, nebul = weather_state(SEED, week)
        nuit = thermique.t_min_nuit_at(eco, 0, 0, t_air, nebul)
        if nuit < 0.0:
            gel += 1
            par_an[(week - 1) // 52] += 1
        gel_air += t_air < 0.0
        t_min = min(t_min, nuit)
        t_air_max = max(t_air_max, t_air)
        if t_max_fn is not None:
            t_jour_max = max(t_jour_max, t_max_fn(t_air, nebul))
    print(f"seed {SEED}, {ANS} ans, sol nu sans vent")
    print(f"  semaines nuit < 0 °C : {gel} ({gel / ANS:.1f}/an) — par an {par_an}")
    print(f"  nuit la plus froide  : {t_min:.1f} °C")
    print(f"  semaines T_air < 0   : {gel_air}")
    print(f"  T_air hebdo max      : {t_air_max:.1f} °C")
    if t_max_fn is not None:
        print(f"  jour le plus chaud max : {t_jour_max:.1f} °C")


if __name__ == "__main__":
    main()
