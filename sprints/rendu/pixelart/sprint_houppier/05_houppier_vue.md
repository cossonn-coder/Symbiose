# ⑤ Vue : houppier, fleurs et fruits sur brindilles, F5 — golden INTACT

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (bilans ①→④), conception §5, partials du ④, `PlantRenderer.Palette.cs` (`Lignification`, `WoodRamp`), `docs/vegetal/croissance/fiches_arbres.md`, `tools/capture_vm.sh`.

## Objectif

À tous les paliers, un arbre lit comme un houppier dense porté par de petites branches, plus comme des pompons sur rameaux verts. Fleurs et fruits sont sur les brindilles.

## À faire

1. **Rameaux dérivés** : table par espèce dans `RecetteArbre` (ou voisine) : rameaux par segment feuillé, longueur, angle, port (retombant, érigé). Dérivés à la cuisson, clé stable du ④, dans le rayon réel `_rayonReelCm` (le snapshot ne porte pas `CanopyRadiusCm`, `PlantRenderer.cs` l. ~619). Géométrie pure, zéro `Random`, aucun champ de pont.
2. **Paliers** : ×0,5 à ×2, gerbes denses à la place de `AjouterTouffeAutour` ; ×4, gerbes à la place de `DrawMassesFeuillage` pour les arbres ; ×8 et plus, feuilles portées par les rameaux dérivés, densité relevée. Les autres plantes ne changent pas.
3. **Bois** : chez les arbres, plus de `ApexColor` sur tout un segment de 40-50 cm ; seule l'extrémité fine reste tendre. Hiver : couche bois seule, la dentelle se lit. Respecter `DensiteVisible` à l'automne.
4. **Fleurs et fruits** : `OrganSites`, `FruitPoint` et `FindFruitNear` gardent une source unique : le clic de `manger` doit rester sur le fruit dessiné. Posés sur une brindille dérivée. Taille de fruit par espèce, en cm (pomme, cerise, figue, noix [odg], fiches), plus de grosse pomme unique au sommet. Vérifier la palette de fruit des 4 espèces (`Palettes`). Fleurs herbacées : ne pas toucher.
5. **Lianes** : captures du banc `liane_relais` à ×4, ×8, cascade lisible, relais lisible.
6. **Mesures** : sur `houppiers` et `verger_mur`, remplissage (part de pixels opaques dans le disque de couronne, sur PNG capturé) avant/après aux paliers ×1, ×2, ×4, ×8, par saison ; durée totale de cuisson contre la référence du ④ ; FPS `full` ; RAM. Si la durée de cuisson dérive fortement, le dire et réduire les rameaux par espèce avant de clore.
7. `dotnet build Symbiose.csproj`, golden, `tests/simserver`, `compte_ldc`.
8. **Clôture** : `00_etat.md` §F5 (ressenti, court : une minute par palier sur `houppiers`, `verger_mur`, `liane_relais`) ; `DETTE.md` D118 réduite, `BACKLOG` (`docs/rendu/pixelart/backlog_pixelart.md` et index) ; `journal/` + index `journal.md` ; mémoire `project_file_priorisee_20261022` à l'orchestrateur.

## Golden

**INTACT** (vue pure, pont inchangé).

## NE PAS

Modifier le moteur ou le protocole du pont. Toucher aux 33 ports, aux fleurs herbacées, aux piquants d'ortie, au pollen, aux gestes. Lancer `tests/test_epaisseur_500ans.py`.
