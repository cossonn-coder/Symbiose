# ④ Chaumes, couvre-sols, buissons, courgette — golden INTACT

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (bilans ①②③), conception §4.2, §4.5, §6 ; `fiches_herbacees.md`, socle `PlantRenderer.Ports*.cs`, `PlantRenderer.Graminees.cs` (chaumes du dactyle), `PlantRenderer.Prairie.cs` (tapis).

## Objectif

Les 13 espèces restantes des ports dessinés se reconnaissent :

- **Chaume** : blé, seigle, pâturin, bambou.
- **Couvre-sol** : fraisier, violette, minette, sphaigne.
- **Buisson ou coussin** : thym, lavande, myrtille, framboisier.
- **Grande rampante** : courgette.

## À faire

1. **Chaume** : réutiliser ce qui existe pour le dactyle sans dupliquer. Bambou : cannes à nœuds, feuillage en haut, colonie lisible. Blé contre seigle : barbes, hauteur, port de l'épi.
2. **Couvre-sol** : colonie en tapis par recouvrement des disques, comme le trèfle, poses de vent réduites. Sphaigne : coussin sans tige, vert-jaune. Stolons du fraisier visibles de près.
3. **Buisson** : masse d'aspect ligneux (coussin de thym, boule de lavande à épis, cannes arquées du framboisier). Mort : le bois sec reste lisible, en cohérence avec les squelettes ligneux du moteur.
4. **Courgette** : grandes feuilles palmées basses, grosse fleur jaune, fruit traçable récoltable au clic.
5. **Perf des colonies** : les clones de fraisier, violette, minette, bambou sont nombreux. Surveiller atlas et recuissons sur `luxuriance` et `full`.
6. **Mesure** : `mesure_silhouettes` (couples blé/seigle, thym/lavande, fraisier/violette), captures de `full`, `luxuriance`, banc à ×1, ×4, ×8, ×16, `mesure_da`, `perf_vm.sh` (conception §6). Lire les PNG.
7. `dotnet build Symbiose.csproj` vert, golden.

## Golden

**INTACT** (vue pure).

## NE PAS

Modifier le moteur. Refondre la prairie validée au F5. Lancer `tests/test_epaisseur_500ans.py`.
