# Après ③ : combien de trèfles à quatre feuilles ?

`mesure_quatre_feuilles.py`, monde `full`, seed 42, automate curatif, 5 ans, lecture chaque semaine. Personne ne cueille pendant la mesure : l'automate écarte ces pieds.

**Retenu : `PROBA_QUATRE_FEUILLES` = 0,005.**

| An | Trèfles adultes fin d'année | Pieds à quatre feuilles vus dans l'année | À la fois, moyenne | À la fois, min à max |
|---|---|---|---|---|
| 1 | 94 | 0 [n=1 graine, VM] | 0,00 | 0 à 0 |
| 2 | 413 | 1 [n=1 graine, VM] | 0,52 | 0 à 1 |
| 3 | 464 | 2 [n=1 graine, VM] | 1,98 | 1 à 2 |
| 4 | 380 | 3 [n=1 graine, VM] | 2,52 | 1 à 3 |
| 5 | 266 | 1 [n=1 graine, VM] | 1,00 | 1 à 1 |

Un pied vivant sur deux années compte dans les deux lignes. Cible du kickoff, 1 à 3 pieds à la fois en an 3 : tenue [n=1 graine, VM].

## Autres probabilités, même run

À la fois en an 3, moyenne [n=1 graine, VM, automate réglé sur 0,005] :

| Probabilité | 0,002 | 0,003 | 0,005 | 0,008 | 0,01 |
|---|---|---|---|---|---|
| Pieds | 0,00 | 1,00 | 1,98 | 2,98 | 6,00 |

0,008 tient aussi la cible, mais vise le haut de la fourchette. 0,01 la dépasse.

## Limites

- Une seule graine et de petits comptes : l'écart entre deux probabilités voisines n'est pas interprétable. Le test `test_rarete` vérifie la fréquence sur 40 000 positions et 20 000 `form_seed`.
- Le nombre suit celui des trèfles. Si l'arbitrage sur les critères ratés de ② change le tapis, il faudra remesurer.
- An 1 : aucun pied [n=1 graine, VM]. Le premier se voit en an 2.
