# Mesure APRÈS RECALIBRAGE (tronçon ③) — calendrier unique, fenêtres au mois réel

- **Commande** : `cd data/code && python3 -m bancs.mesure_calendrier 3`
- **Base** : `e38ae8a` + ② + ③ non commités (réveil des ravageurs C5/C5bis ; aléas,
  champignons, abscission 30-36 / pivot 34).
- **Mondes / limites de lecture** : identiques à `avant.md` (même banc, même seed `0x5AB1057E`).

## Calendrier — monde smoke (seed moteur 0x5AB1057E) + banc floraison_saisons (pommier) + banc tourbière (glace), 3 an(s)

Jour le plus long (`daylength`, pur) : s14 (ete), 16.0 h — identique chaque année.

### Par année

| an | T min | T max | pommier bloom_week | recouvrement fleur×butineurs | fruits noués pommier | tomates disparues (semaine) | tomates vivantes fin | 1ʳᵉ abscission (T) |
|---|---|---|---|---|---|---|---|---|
| 1 | -0.3 °C s4 (printemps) | +21.7 °C s15 (ete) | s5 (printemps) | 0/2 sem. | 0 | s21 (ete), s21 (ete) | 0 | s31 (+11.3 °C) |
| 2 | +0.3 °C s44 (hiver) | +27.1 °C s19 (ete) | s5 (printemps) | 2/2 sem. | 1 | aucune | 0 | s31 (+11.3 °C) |
| 3 | -0.6 °C s2 (printemps) | +18.7 °C s19 (ete) | s6 (printemps) | 2/2 sem. | 1 | aucune | 0 | s31 (+11.3 °C) |

### Par année × saison étiquetée

| an | saison | sem. gel (T_air<0) | sem. neige | sem. glace (tourbière) | humidité sol médiane | carpophores (échantillons cumulés, par espèce) |
|---|---|---|---|---|---|---|
| 1 | printemps | 1 | 0 | 1 | 1.676 | — |
| 1 | ete | 0 | 0 | 0 | 1.355 | — |
| 1 | automne | 0 | 0 | 0 | 1.418 | — |
| 1 | hiver | 0 | 0 | 9 | 1.925 | — |
| 2 | printemps | 0 | 0 | 2 | 2.325 | — |
| 2 | ete | 0 | 0 | 0 | 1.888 | coprin 12 |
| 2 | automne | 0 | 0 | 0 | 1.575 | coprin 3 |
| 2 | hiver | 0 | 1 | 0 | 1.696 | — |
| 3 | printemps | 1 | 0 | 1 | 2.069 | coprin 10 |
| 3 | ete | 0 | 0 | 0 | 2.017 | coprin 36 |
| 3 | automne | 0 | 0 | 0 | 1.543 | coprin 16 |
| 3 | hiver | 0 | 0 | 0 | 1.608 | — |

## Pression ravageur (point 0) — sonde hors banc, monde smoke, 2 ans

Part des (plot planté × semaine) où `ravageur × 0,20 > 0,015` (seuil létal de
`herbivory_pressure`, non touché). « État ② » = sol nu habitable + rampe globale 3→15 °C,
rejoué par monkeypatch sur le même arbre ; « ③ » = état livré. [n=1 seed, 2 ans, VM]

| fenêtre | état ② | ③ | pmax ② → ③ | densité moy. sol nu ② → ③ |
|---|---|---|---|---|
| an 1 wiy 1-4 (avril) | 11/56 | **0/56** | 0,026 → 0,008 | 0,017 → 0,005 |
| an 1 wiy 5-8 (≈ mai) | 48/50 | 34/56 | 0,051 → 0,034 | 0,039 → 0,012 |
| an 1 wiy 13-16 (été) | 50/50 | 61/66 | 0,086 → 0,089 | 0,054 → 0,019 |
| an 2 wiy 1-4 | 56/95 | 27/97 | 0,048 → 0,029 | 0,018 → 0,006 |
| an 2 wiy 5-8 | 113/113 | 81/104 | 0,094 → 0,068 | 0,040 → 0,014 |
| an 2 wiy 13-20 (été) | 263/263 | 261/261 | 0,124 → 0,116 | 0,058 → 0,022 |

Lecture : avril épargné, mai partiel, l'été garde sa pression (boucle ravageur →
auxiliaire intacte) ; le sol nu n'entretient plus de pucerons. Les tomates du smoke ne
meurent plus en s5 mais en s21 (été) l'an 1.
