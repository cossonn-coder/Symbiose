# Mesures APRÈS tapis et chute — sprint AUTOMNE VISIBLE ⑤

Monde `full`, seed 42, un seul run sur la VM. Semaine lue = la prochaine à simuler.

## Masses et âges de la litière de feuilles

Bloc `litiere` du snapshot, plots à masse de feuilles ≥ 0,01 [n=1 run, VM].

| sem. | plots | masse médiane | p90 | âge `age_sem` médian | âge hors bois médian |
|---|---|---|---|---|---|
| 33 | 230 | 0.133 | 0.188 | 56.9 | 0.4 |
| 37 | 363 | 0.145 | 0.201 | 53.8 | 2.3 |
| 41 | 363 | 0.111 | 0.215 | 54.9 | 6.3 |
| 45 | 363 | 0.063 | 0.127 | 71.5 | 10.2 |
| 50 | 363 | 0.032 | 0.065 | 88.4 | 15.0 |
| 55 | 330 | 0.015 | 0.033 | 104.8 | 19.5 |
| 60 | 129 | 0.014 | 0.032 | 108.0 | 21.3 |
| 65 | 28 | 0.015 | 0.136 | 115.1 | 26.7 |
| 70 | 9 | 0.078 | 0.103 | 105.6 | 31.5 |

## Lecture

- **`MasseRef` = 0,20, pas 0,30** : `FEUILLE_PAR_PLOT` (0,30) se dépose sur 4 semaines pendant que la litière se
  décompose ; le p90 plafonne vers 0,20 [n=1 run, VM]. À 0,30 le tapis n'aurait jamais été plein.
- **`age_sem` inutilisable tel quel** : le bois mort tire la moyenne vers 54 semaines dès s37 [n=1 run, VM], le tapis
  sortait humus dès sa chute. La vue retire la part du bois (index 5-6). Reste une moyenne feuilles + herbacées.
- **Disparition** : captures ×1 en s37, s56, s66. Tapis dense, puis grains sombres clairsemés, puis plus rien
  [n=1 run, VM]. Les 9 plots restants de s70 sont sous MasseMin ou peu visibles : non vérifié plot par plot.

## Perf en pleine chute (s34, ×1 et ×4, centré sur le cerisier)

`tools/perf_vm.sh -w 33`, 8 relevés de 1 s par run, charge 2-4.

| zoom | avec chute | sans chute (`-x LeafFall`) |
|---|---|---|
| ×1 | 101 draw calls, 140 ms ; 99, 137 ms | 94, 129 ms ; 98, 141 ms |
| ×4 | 69 draw calls, 112 ms | 68, 113 ms |

Soit +1 à +7 draw calls à ×1 [n=2 runs par côté, VM], +1 à ×4 [n=1 run par côté, VM] ; l'écart de temps est dans le
bruit entre deux runs identiques. Un premier relevé en s37 donnait +31 draw calls à ×1 [n=1 run, VM, charge 3-4,
gels 3], non reproduit en s34 ; à ×4, aucune chute à l'écran en s37. Le tapis seul en s37 à ×1 : +5 draw calls, +32 500
primitives [n=1 run par côté, VM].
