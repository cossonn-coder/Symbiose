# Mesure AVANT (tronçon ①) — calendrier tel qu'il est, climat non décalé

- **Commande** : `cd data/code && python3 -m bancs.mesure_calendrier 3`
- **Commit** : `7add72f` (+ banc `bancs/mesure_calendrier.py` non commité au moment du run)
- **Durée du run** : 22 s [VM, 1 run]
- **Mondes** : smoke = monde du golden (tomate, T_air, neige, humidité, carpophores,
  abscission) ; `floraison_saisons` (pommier : celui du smoke ne fleurit pas en 3 ans) ;
  `tourbiere` (glace : seul monde avec lame d'eau). Seed moteur par défaut `0x5AB1057E`.
- **Limites de lecture** : « gel » = T_air hebdomadaire < 0 (pas la T min de nuit, qui
  pilote la glace) ; carpophores = échantillons cumulés semaine par semaine (un même
  champignon visible 2 semaines compte 2) ; tomates = disparition (mort ou retrait) des
  individus vivants, quelle que soit la cause.

## Calendrier — monde smoke (seed moteur 0x5AB1057E) + banc floraison_saisons (pommier) + banc tourbière (glace), 3 an(s)

Jour le plus long (`daylength`, pur) : s25 (ete), 16.0 h — identique chaque année.

### Par année

| an | T min | T max | pommier bloom_week | recouvrement fleur×butineurs | fruits noués pommier | tomates disparues (semaine) | tomates vivantes fin | 1ʳᵉ abscission (T) |
|---|---|---|---|---|---|---|---|---|
| 1 | +3.6 °C s51 (hiver) | +17.6 °C s29 (automne) | s14 (ete) | 0/2 sem. | 0 | s23 (ete), s23 (ete) | 0 | s35 (+12.5 °C) |
| 2 | +1.6 °C s9 (printemps) | +22.7 °C s26 (ete) | s15 (ete) | 2/2 sem. | 2 | aucune | 0 | s35 (+15.9 °C) |
| 3 | +2.6 °C s1 (printemps) | +17.6 °C s29 (automne) | s15 (ete) | 2/2 sem. | 1 | aucune | 0 | s35 (+14.4 °C) |

### Par année × saison étiquetée

| an | saison | sem. gel (T_air<0) | sem. neige | sem. glace (tourbière) | humidité sol médiane | carpophores (échantillons cumulés, par espèce) |
|---|---|---|---|---|---|---|
| 1 | printemps | 0 | 0 | 10 | 1.765 | — |
| 1 | ete | 0 | 0 | 0 | 1.695 | — |
| 1 | automne | 0 | 0 | 0 | 1.551 | — |
| 1 | hiver | 0 | 0 | 1 | 1.834 | — |
| 2 | printemps | 0 | 0 | 11 | 2.361 | — |
| 2 | ete | 0 | 0 | 0 | 2.111 | coprin 6 |
| 2 | automne | 0 | 0 | 0 | 1.574 | coprin 11 |
| 2 | hiver | 0 | 1 | 0 | 1.514 | coprin 5 |
| 3 | printemps | 0 | 0 | 1 | 2.006 | — |
| 3 | ete | 0 | 0 | 0 | 2.228 | coprin 12 |
| 3 | automne | 0 | 0 | 0 | 1.545 | coprin 12 |
| 3 | hiver | 0 | 0 | 0 | 1.430 | — |
