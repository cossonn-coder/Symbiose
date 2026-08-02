"""Dette 2 (revue 2026-08-02, 2e passe) — médiane + quartiles HORS TRANSITOIRE des 3
séries de saturation. La grandeur qui décide vs capacite.py (0,68 grande tuile) est la
MÉDIANE du plateau, PAS le max. Transitoire = années 1-10 (montée), on garde 11-30.
Données = séries brutes de mesure_review_C_satur.py (pl/plot). Aucune re-simulation."""
import statistics

# pl/plot par année (1..30), recopiées de la sortie de mesure_review_C_satur.py
SERIES = {
    12345:  [0.301,0.364,0.295,0.295,0.312,0.307,0.341,0.432,0.466,0.528,
             0.580,0.562,0.608,0.807,0.642,0.750,0.773,0.562,0.676,0.812,
             0.545,0.756,0.648,0.682,0.699,0.131,0.767,0.506,0.665,0.761],
    271828: [0.301,0.381,0.341,0.358,0.398,0.477,0.449,0.778,0.790,0.676,
             0.693,0.773,0.659,0.688,0.716,0.625,0.545,0.670,0.267,0.716,
             0.795,0.682,0.767,0.631,0.392,0.648,0.528,0.597,0.682,0.562],
    987654: [0.267,0.392,0.290,0.312,0.318,0.381,0.409,0.494,0.574,0.648,
             0.608,0.625,0.619,0.756,0.511,0.659,0.778,0.710,0.665,0.580,
             0.727,0.438,0.608,0.591,0.477,0.716,0.392,0.716,0.477,0.648],
}

print("# Dette 2 — plateau HORS TRANSITOIRE (années 11-30) vs capacite.py 'grande=0,68'")
allmed = []
for seed, s in SERIES.items():
    plateau = s[10:]                        # années 11..30
    q = statistics.quantiles(plateau, n=4)  # [Q1, médiane, Q3]
    med = statistics.median(plateau)
    allmed.append(med)
    print(f"  seed {seed:>6} : médiane={med:.3f}  Q1={q[0]:.3f}  Q3={q[2]:.3f}  "
          f"min={min(plateau):.3f}  max={max(plateau):.3f}")
print(f"  → médianes de plateau : {[f'{m:.3f}' for m in allmed]} "
      f"(≈ {min(allmed):.2f}-{max(allmed):.2f})")
print(f"  → capacite.py annonce 0,68 pour grande tuile → à COMPARER À LA MÉDIANE, pas au max.")

# fréquence des effondrements ≥25 % (dette 2, 2e point)
print("\n# Fréquence des effondrements ≥25 % (yoy) sur les 3 séries")
tot_years, tot_crash = 0, 0
for seed, s in SERIES.items():
    crashes = sum(1 for i in range(1, len(s)) if (s[i]-s[i-1])/s[i-1] <= -0.25)
    tot_years += len(s) - 1
    tot_crash += crashes
    print(f"  seed {seed:>6} : {crashes} chutes / {len(s)-1} transitions")
print(f"  → {tot_crash} chutes / {tot_years} années-tuile = 1 tous les {tot_years/tot_crash:.1f} ans")
print(f"  → partie 500-1000 sem (~10-20 ans) : le joueur en traverse ~{10/(tot_years/tot_crash):.0f}-{20/(tot_years/tot_crash):.0f}")
