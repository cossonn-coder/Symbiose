# Mesures AVANT — sprint AUTOMNE VISIBLE ①

Référence à rejouer au ② (`mesures/apres_port.md`) : `cd data/code && python3 -m bancs.mesure_arbres`.
Pied unique par arbre et par âge, plot (3,3), patrimoine fondateur, sans lumière ni concurrence : le
tableau de la conception §1 s'y reproduit au chiffre près pour 5, 10 et 15 ans. Chaque âge repart d'un semis.
La hauteur inclut le gène `hauteur` de ce pied (dernière colonne), pas le rayon.

## Banc

| arbre | âge | segments [seed 42, sans lumière, VM] | hauteur cm [seed 42, sans lumière, VM] | rayon cm [seed 42, sans lumière, VM] | apex [seed 42, sans lumière, VM] | % feuillés [seed 42, sans lumière, VM] | gène hauteur du pied |
|---|---|---|---|---|---|---|---|
| figuier | 5 | 5 | 209 | 95 | 1 | 20% | 0.991 |
| figuier | 10 | 24 | 418 | 218 | 10 | 62% | 0.991 |
| figuier | 15 | 80 | 491 | 395 | 15 | 69% | 0.991 |
| figuier | 25 | 90 | 496 | 363 | 10 | 68% | 0.991 |
| pommier | 5 | 4 | 179 | 50 | 1 | 25% | 1.018 |
| pommier | 10 | 45 | 357 | 187 | 22 | 73% | 1.018 |
| pommier | 15 | 69 | 271 | 333 | 15 | 62% | 1.018 |
| pommier | 25 | 51 | 247 | 312 | 24 | 71% | 1.018 |
| cerisier | 5 | 6 | 296 | 140 | 1 | 17% | 1.168 |
| cerisier | 10 | 45 | 588 | 280 | 22 | 80% | 1.168 |
| cerisier | 15 | 70 | 352 | 499 | 25 | 80% | 1.168 |
| cerisier | 25 | 70 | 549 | 640 | 5 | 41% | 1.168 |
| noyer | 5 | 7 | 285 | 160 | 1 | 14% | 0.918 |
| noyer | 10 | 34 | 569 | 357 | 13 | 50% | 0.918 |
| noyer | 15 | 70 | 395 | 571 | 24 | 61% | 0.918 |
| noyer | 25 | 4 | 66 | 245 | 2 | 50% | 0.918 |
| chene | 5 | 4 | 177 | 185 | 1 | 25% | 0.884 |
| chene | 10 | 25 | 352 | 286 | 12 | 48% | 0.884 |
| chene | 15 | 70 | 329 | 461 | 21 | 60% | 0.884 |
| chene | 25 | 70 | 274 | 486 | 7 | 44% | 0.884 |
| sapin | 5 | 4 | 237 | 110 | 1 | 25% | 1.188 |
| sapin | 10 | 10 | 473 | 131 | 3 | 30% | 1.188 |
| sapin | 15 | 57 | 708 | 312 | 21 | 58% | 1.188 |
| sapin | 25 | 69 | 380 | 426 | 14 | 36% | 1.188 |
| hetre | 5 | 4 | 201 | 140 | 1 | 25% | 1.008 |
| hetre | 10 | 25 | 401 | 241 | 12 | 48% | 1.008 |
| hetre | 15 | 70 | 375 | 416 | 21 | 60% | 1.008 |
| hetre | 25 | 70 | 313 | 441 | 7 | 44% | 1.008 |
| bouleau | 5 | 8 | 383 | 70 | 1 | 12% | 0.977 |
| bouleau | 10 | 37 | 765 | 271 | 9 | 73% | 0.977 |
| bouleau | 15 | 70 | 274 | 305 | 22 | 84% | 0.977 |
| bouleau | 25 | 70 | 262 | 333 | 10 | 50% | 0.977 |
| charme | 5 | 6 | 230 | 100 | 1 | 17% | 0.906 |
| charme | 10 | 46 | 457 | 240 | 23 | 78% | 0.906 |
| charme | 15 | 67 | 266 | 418 | 15 | 75% | 0.906 |
| charme | 25 | 70 | 394 | 357 | 3 | 61% | 0.906 |
| aulne | 5 | 7 | 273 | 50 | 1 | 14% | 0.799 |
| aulne | 10 | 35 | 544 | 238 | 9 | 69% | 0.799 |
| aulne | 15 | 70 | 223 | 364 | 29 | 81% | 0.799 |
| aulne | 25 | 4 | 52 | 103 | 2 | 75% | 0.799 |
| saule | 5 | 9 | 448 | 60 | 1 | 11% | 1.023 |
| saule | 10 | 67 | 896 | 362 | 15 | 72% | 1.023 |
| saule | 15 | 70 | 342 | 314 | 29 | 81% | 1.023 |
| saule | 25 | 70 | 240 | 342 | 7 | 69% | 1.023 |


## Ce que le tableau montre

- **Hauteur non monotone** : 10 arbres sur 11 sont à 25 ans sous leur hauteur de 10 ans, et 9 sur 11 dès
  15 ans [seed 42, sans lumière, VM]. Seul le figuier monte de bout en bout ; le sapin tient jusqu'à 15 ans
  (cause : `00_etat.md`).
- **Effondrement total** : noyer 4 segments/66 cm et aulne 4 segments/52 cm à 25 ans
  [seed 42, sans lumière, VM].
- **Un bâton à 5 ans** : 1 seul apex et 4 à 9 segments pour les 11 arbres [seed 42, sans lumière, VM].

## Captures de référence (monde `full`, seed 42, VM, n=1 par vue)

PNG non committés. Le HUD affiche « automne, semaine 8/13 » pour `-w 33`, soit s34.

| Commande | Ce qu'on y voit |
|---|---|
| `tools/capture_vm.sh -b full -w 33 -z 4 -c 975,1475 -n 6` | Le pommier est un mât nu de ~4 segments, sans branche ni feuille, alors que l'info-bulle dit « prend ses couleurs d'automne ». Sol nu autour du pied, aucune feuille tombée visible. |
| `tools/capture_vm.sh -b full -w 33 -z 1 -n 3` | Lisière verte et prairie d'été en plein automne. Le pommier se lit comme un poteau contre la façade. Aucune tache de couleur d'automne dans le jardin ; le potager garde son vert. |
