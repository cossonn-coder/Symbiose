# Mesure APRÈS DÉCALAGE (tronçon ②) — calendrier unique, climat décalé de 11 semaines

- **Commande** : `cd data/code && python3 -m bancs.mesure_calendrier 3`
- **Base** : `e38ae8a` + tronçon ② non commité (`calendrier.py`, `W_T_MIN = 45`, `W_SOLSTICE_ETE = 14`)
- **Mondes / limites de lecture** : identiques à `avant.md` (même banc, même seed `0x5AB1057E`).
- Aucune fenêtre ni seuil recalibré (c'est ③).

## Calendrier — monde smoke (seed moteur 0x5AB1057E) + banc floraison_saisons (pommier) + banc tourbière (glace), 3 an(s)

Jour le plus long (`daylength`, pur) : s14 (ete), 16.0 h — identique chaque année.

### Par année

| an | T min | T max | pommier bloom_week | recouvrement fleur×butineurs | fruits noués pommier | tomates disparues (semaine) | tomates vivantes fin | 1ʳᵉ abscission (T) |
|---|---|---|---|---|---|---|---|---|
| 1 | +1.9 °C s43 (hiver) | +18.7 °C s18 (ete) | s4 (printemps) | 0/2 sem. | 0 | s5 (printemps), s5 (printemps) | 0 | s35 (+4.2 °C) |
| 2 | +0.3 °C s44 (hiver) | +27.1 °C s19 (ete) | s5 (printemps) | 2/2 sem. | 1 | aucune | 0 | s35 (+7.7 °C) |
| 3 | +1.9 °C s43 (hiver) | +18.7 °C s19 (ete) | s4 (printemps) | 2/2 sem. | 1 | aucune | 0 | s35 (+6.2 °C) |

### Par année × saison étiquetée

| an | saison | sem. gel (T_air<0) | sem. neige | sem. glace (tourbière) | humidité sol médiane | carpophores (échantillons cumulés, par espèce) |
|---|---|---|---|---|---|---|
| 1 | printemps | 0 | 0 | 0 | 1.682 | — |
| 1 | ete | 0 | 0 | 0 | 1.472 | — |
| 1 | automne | 0 | 0 | 0 | 1.545 | — |
| 1 | hiver | 0 | 0 | 9 | 2.038 | — |
| 2 | printemps | 0 | 0 | 2 | 2.406 | — |
| 2 | ete | 0 | 0 | 0 | 1.938 | rose_des_pres 2 |
| 2 | automne | 0 | 0 | 0 | 1.577 | — |
| 2 | hiver | 0 | 1 | 0 | 1.683 | — |
| 3 | printemps | 0 | 0 | 0 | 2.021 | — |
| 3 | ete | 0 | 0 | 0 | 1.868 | — |
| 3 | automne | 0 | 0 | 0 | 1.411 | — |
| 3 | hiver | 0 | 0 | 0 | 1.465 | — |
