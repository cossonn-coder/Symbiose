# ② Socle des ports, taille, rosettes — golden INTACT

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (bilan ①), conception §3, §4 ; `visuals/PlantRenderer.Prairie.cs`, `PlantRenderer.Graminees.cs`, `PlantRenderer.Bake.cs`, `PlantRenderer.Wind.cs` ; `fiches_herbacees.md`.

## Objectif

Le socle commun à tous les ports, le geste de taille, et les 7 rosettes reconnaissables : pissenlit, mâche, bourse-à-pasteur, molène, drosera, carotte, ail.

## À faire

1. **Socle C#**, partials neufs (`PlantRenderer.Ports*.cs`) : table `FichePort` par nom de classe Python (une ligne par espèce), dispatch à côté de celui de la prairie dans `DrawVector`, mesures (port, ombre, picking, vent, boîte de cuisson) sur le patron de `MesurerPrairie` et `BoitePrairie`. Réutiliser `LotTriangles`, `Ton`, `PoserDetailsPrairie` ; la prairie garde ses fonctions. Ne pas faire grossir `Prairie.cs` ni `Organs.cs` : palettes et feuilles manquantes (comparer les tables au catalogue) dans un partial neuf, si la structure statique des tables l'autorise.
2. **État de vie** : semis, croissance, floraison, fruit, automne, dormance, mort, santé, neige, vent. Chaque port les porte, comme la prairie. Vérifier une vivace herbacée en hiver.
3. **Fruits** : placés au hash de leur index, récolte par clic vérifiée.
4. **Saut de hauteur au changement de stade** : mesurer sur `planche_especes` ; si visible, lissage côté vue (conception §4.3).
5. **Recuisson** : un `SetStructure` qui ne change rien à ce que dessine un port ne doit pas cuire. Vérifier que `height_cm`, stade, hints et organes déclenchent bien une cuisson.
6. **Taille moteur** (conception §4.4) : semaine de coupe et de pincement sur `PlantInstance` (`game_state["week"]`, voir `sim/actions/gestes.py`, écrite dès que le geste est payé, sur les espèces non migrées) ; `rabattu` et `pince` au pont, espèces non migrées, si non nuls, à côté de `feuillage` ; protocole bumpé `0.6.7` (`tools/simserver/version.py` et les tests qui citent `0.6.6`). Vérifier la sérialisation de `PlantInstance` si elle existe : pas de champ perdu, pas de save cassé.
7. **Taille vue** : pour une plante à port (les 33 + les 4 de prairie), `WorldView.ActionPicking.cs` et `ActionDispatch.cs` n'envoient plus `target.segment` et ne surlignent aucun segment. Effet visible de `rabattu` et `pince` sur le port.
8. **Rosettes** : traduire les 7 fiches. Bisannuelles : rosette puis hampe selon le stade. Ail : éventail de rubans, hampe à l'an 2.
9. **Mesure** : `mesure_silhouettes` sur `planche_especes` (les 7 ne se confondent plus entre elles ni avec les autres) ; captures de `full` à ×1, ×4, ×8, ×16 ; `mesure_da` ; `perf_vm.sh` avant/après (conception §6). Lire les PNG. Tailler un pied en capture si le banc le permet ; sinon test simserver du hint.
10. `dotnet build Symbiose.csproj` vert, golden, `tests/simserver`.

## Golden

**INTACT** : `rabattu` et `pince` hors digest, n'affectent aucune loi. S'il bouge : anomalie à diagnostiquer, pas de re-figeage.

## NE PAS

Migrer une espèce en `procedural_growth`. Toucher `height_at`. Retirer les segments du pont. Écrire une fonction par espèce. Lancer `tests/test_epaisseur_500ans.py`.
