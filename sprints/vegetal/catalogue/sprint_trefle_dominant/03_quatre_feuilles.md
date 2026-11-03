# ③ Trèfle à quatre feuilles — golden INTACT

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, conception §3.

## Objectif

Quelques pieds rares ont quatre feuilles ; les récolter récompense le joueur, une fois par pied.

## À faire

1. **Module neuf** `sim/quatre_feuilles.py` : `est_quatre_feuilles(plant, seed)`, pure, hash de l'identité du pied (`form_seed`, position), jamais de RNG vivant ; vrai seulement pour un trèfle adulte vivant non encore cueilli.
   Probabilité à calibrer par la mesure : environ 1 à 3 pieds à la fois sur le jardin `full` en an 3. Ne pas la lier au `form_seed` seul : les ramets héritent du `form_seed` de la mère et toute la colonie serait à quatre feuilles.
2. **Récolte** : dans `recolter` (`sim/actions/gestes.py`), après le gain normal, si le pied est à quatre feuilles : Vigueur pleine, pied marqué cueilli (champ de `PlantInstance`, hors `_PLANT_ATTRS` du digest : vérifier dans `tests/test_golden.py`),
   prochaine page secrète due (robinet récompense existant, `sim/pages_corpus.py` et son appelant : vérifier), ligne au carnet. Le bonus n'est jamais versé à la plante. Vérifier que le trèfle est récoltable (`maturite`, palette de `sim/actions/palette.py`) et que `recolter` est bien le geste du clic.
   L'automate ne doit pas cueillir ces pieds par hasard : vérifier `tools/jardinier_auto/`.
3. **Voix** : niveau 3 de la fiche du trèfle dans l'encyclopédie, page P34 sur le folklore (voix paysanne), marqueur d'événement au ledger.
4. **Pont** : hint `quatre_feuilles` seulement quand il est vrai. `serialize.py` est à 398 LDC : passer par un module voisin. Version 0.6.5 dans `tools/simserver/version.py`, adapter les tests de version.
5. **Tests** `tests/test_quatre_feuilles.py` : déterminisme ; rareté ; un ramet n'hérite pas du statut ; bonus unique ; Vigueur au plafond ; rien hors récolte ; bloc pont.
6. **Mesure** `mesures/apres_quatre_feuilles.md`, `full`, seed 42, 5 ans : combien de pieds par an `[n=1 graine, VM]`.

## Golden

**INTACT** : pure lecture hors geste, et le smoke ne récolte pas ces pieds. S'il bouge, c'est un bug : ne pas figer.

## NE PAS

Afficher le trèfle à quatre feuilles au HUD. Donner un bonus de croissance. Toucher au C#. Lancer `tests/test_epaisseur_500ans.py`.
