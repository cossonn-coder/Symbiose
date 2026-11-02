# Mesures APRÈS port — sprint AUTOMNE VISIBLE ②

Même banc que `avant.md` : `cd data/code && python3 -m bancs.mesure_arbres`. Pied unique par arbre et par âge,
plot (3,3), patrimoine fondateur, sans lumière ni concurrence. La hauteur inclut le gène `hauteur` du pied.

## Banc

| arbre | âge | segments [seed 42, sans lumière, VM] | hauteur cm [seed 42, sans lumière, VM] | rayon cm [seed 42, sans lumière, VM] | apex [seed 42, sans lumière, VM] | % feuillés [seed 42, sans lumière, VM] | gène hauteur du pied |
|---|---|---|---|---|---|---|---|
| figuier | 5 | 5 | 198 | 91 | 2 | 40% | 0.991 |
| figuier | 10 | 24 | 394 | 260 | 10 | 62% | 0.991 |
| figuier | 15 | 88 | 512 | 407 | 23 | 75% | 0.991 |
| figuier | 25 | 84 | 546 | 390 | 27 | 60% | 0.991 |
| pommier | 5 | 6 | 179 | 71 | 2 | 33% | 1.018 |
| pommier | 10 | 65 | 357 | 229 | 30 | 71% | 1.018 |
| pommier | 15 | 70 | 367 | 265 | 26 | 56% | 1.018 |
| pommier | 25 | 70 | 367 | 259 | 27 | 54% | 1.018 |
| cerisier | 5 | 8 | 290 | 94 | 4 | 62% | 1.168 |
| cerisier | 10 | 70 | 575 | 276 | 29 | 77% | 1.168 |
| cerisier | 15 | 70 | 735 | 321 | 22 | 60% | 1.168 |
| cerisier | 25 | 70 | 735 | 325 | 22 | 43% | 1.168 |
| noyer | 5 | 8 | 272 | 68 | 4 | 50% | 0.918 |
| noyer | 10 | 55 | 543 | 343 | 21 | 62% | 0.918 |
| noyer | 15 | 70 | 771 | 373 | 19 | 36% | 0.918 |
| noyer | 25 | 70 | 771 | 410 | 22 | 44% | 0.918 |
| chene | 5 | 6 | 177 | 93 | 3 | 50% | 0.884 |
| chene | 10 | 44 | 352 | 281 | 17 | 39% | 0.884 |
| chene | 15 | 70 | 527 | 295 | 22 | 31% | 0.884 |
| chene | 25 | 70 | 530 | 292 | 22 | 37% | 0.884 |
| sapin | 5 | 5 | 267 | 50 | 1 | 20% | 1.188 |
| sapin | 10 | 17 | 533 | 134 | 7 | 47% | 1.188 |
| sapin | 15 | 70 | 798 | 300 | 24 | 56% | 1.188 |
| sapin | 25 | 69 | 832 | 290 | 25 | 43% | 1.188 |
| hetre | 5 | 5 | 201 | 61 | 2 | 40% | 1.008 |
| hetre | 10 | 59 | 401 | 226 | 28 | 47% | 1.008 |
| hetre | 15 | 70 | 559 | 291 | 29 | 44% | 1.008 |
| hetre | 25 | 70 | 562 | 303 | 25 | 37% | 1.008 |
| bouleau | 5 | 8 | 363 | 50 | 1 | 25% | 0.977 |
| bouleau | 10 | 29 | 726 | 203 | 7 | 62% | 0.977 |
| bouleau | 15 | 70 | 880 | 240 | 21 | 70% | 0.977 |
| bouleau | 25 | 70 | 880 | 256 | 19 | 43% | 0.977 |
| charme | 5 | 6 | 204 | 61 | 2 | 33% | 0.906 |
| charme | 10 | 70 | 407 | 244 | 33 | 73% | 0.906 |
| charme | 15 | 70 | 408 | 317 | 28 | 60% | 0.906 |
| charme | 25 | 66 | 408 | 266 | 21 | 52% | 0.906 |
| aulne | 5 | 7 | 256 | 55 | 1 | 14% | 0.799 |
| aulne | 10 | 25 | 511 | 161 | 7 | 60% | 0.799 |
| aulne | 15 | 70 | 639 | 255 | 25 | 63% | 0.799 |
| aulne | 25 | 70 | 639 | 274 | 23 | 47% | 0.799 |
| saule | 5 | 15 | 401 | 146 | 7 | 60% | 1.023 |
| saule | 10 | 70 | 614 | 320 | 23 | 57% | 1.023 |
| saule | 15 | 70 | 614 | 358 | 22 | 57% | 1.023 |
| saule | 25 | 70 | 614 | 339 | 20 | 53% | 1.023 |


## Comparaison avec `avant.md`

| arbre | H 10 ans cible fiche → obtenu/gène `[seed 42, 1 pied, VM]` | rayon 10 ans cible → obtenu `[seed 42, 1 pied, VM]` | H 25 ans avant → après `[seed 42, 1 pied, VM]` | apex à 5 ans avant → après `[seed 42, 1 pied, VM]` |
|---|---|---|---|---|
| pommier | 350 → 351 | 200 → 229 | 247 → 367 | 1 → 2 |
| cerisier | 500 → 492 | 250 → 276 | 549 → 735 | 1 → 4 |
| noyer | 600 → 591 | 350 → 343 | 66 → 771 | 1 → 4 |
| chêne | 400 → 398 | 280 → 281 | 274 → 530 | 1 → 3 |
| hêtre | 400 → 398 | 220 → 226 | 313 → 562 | 1 → 2 |
| bouleau | 750 → 743 | 180 → 203 | 262 → 880 | 1 → 1 |
| charme | 450 → 449 | 220 → 244 | 394 → 408 | 1 → 2 |
| aulne | 650 → 640 | 170 → 161 | 52 → 639 | 1 → 1 |
| saule | 800 → 600 | 300 → 320 | 240 → 614 | 1 → 7 |
| figuier | 400 → 398 | 250 → 260 | 496 → 546 | 1 → 2 |
| sapin | 450 → 449 | 130 → 134 | 380 → 832 | 1 → 1 |

- **Hauteur non décroissante** de 5 à 25 ans pour les 11 arbres, et plus aucun effondrement total
  [seed 42, 1 pied par âge, sans lumière, VM].
- **Ce qui cède encore** : bouleau, aulne et sapin restent d'un seul axe à 5 ans [seed 42, 1 pied, VM]. À leur
  vitesse, des latéraux plus précoces dépassent le rayon de la fiche. Ils ont leur couronne à 10 ans, âge de la démo.
- **Saule** sous sa cible (600 pour 800) [seed 42, 1 pied, VM] : il atteint le plafond avant 10 ans. L'autre pied
  testé atteint ~970 cm [plot (5,2), seed 42, VM], la grille n'a pas su resserrer. Il n'est semé nulle part.
- **La hauteur plafonne** : charme à ~410 cm et pommier à ~370 cm dès 15 ans [seed 42, 1 pied, VM]. Sous 70 segments,
  la croissance adulte reste limitée et les fiches à 30 ans ne sont pas atteintes.
- **Part feuillée à 25 ans** en baisse : 37-60 % contre 36-75 % avant, sur des arbres qui ne s'effondrent plus
  [seed 42, 1 pied, VM]. Sans le bourgeon réveillé sous la coupe, le hêtre tombait à 3 % [même mesure].

## Monde de démo (`full`, seed 42, 3 ans, n=1 run, VM)

6 arbres à 11 ans, tous vivants à la semaine 156, `drought_memory` 0. Vitalité 1,0 sauf le cerisier (tuile O)
à 0,73 en fin de run [n=1 run], cause non recherchée. Bouleau sur sable : vivant, vitalité 1,0 [n=1 run].

## Coût (`tools/banc_cadence`, 104 semaines, graine par défaut, automate OFF, VM)

| | tick moyen an 2 ms `[n=2 runs, charge 1-3]` | pire semaine an 2 ms `[n=2 runs]` | plantes max an 2 `[n=1 graine]` |
|---|---|---|---|
| avant | 868 ; 828 | 1079 ; 1088 | 885 |
| après | 767 ; 831 | 991 ; 1201 | 717 |

Budget +10 % tenu sur le tick absolu [n=2 runs, écart entre runs ~8 %]. **Mais la population baisse de 19 % en
an 2** [n=1 graine] : le coût par plante monte, et le tick reste plat parce qu'il y a moins de plantes. La cause de
cette baisse n'est pas isolée (arbres plus grands dès le départ, donc ombre et prélèvement plus forts : hypothèse).

## Golden

`bfe6f889…` → `82d522c8…`. Cause directe : le pommier du smoke change de structure (dominance, entre-nœud, largeur
de feuillage). Les voisins répondent par la lumière et l'eau (`growth_factor`, santé du trèfle, phacélie). Même
population finale : 55 plantes vivantes, mêmes effectifs par espèce [seed golden, 2 ans]. La protection de la flèche
seule laisse le golden intact (vérifié avant de toucher aux paramètres).
