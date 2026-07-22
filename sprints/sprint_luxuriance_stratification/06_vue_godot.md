# Tronçon 6 — Vue Godot : empilement visible + couverture + silhouettes + colonies

> Kickoff autosuffisant. Lis `CLAUDE.md` (Godot = VUE, C# uniquement, F5 = Nico) +
> `00_etat.md` + `docs/vegetal/grimpantes/conception_luxuriance_stratification.md §2.3-2.4`.
> **Pré-requis : tronçons 1-5 faits.** **Golden : INTACT** (aucune modif moteur qui
> touche le tick — seulement pont read-only + rendu).
> **Règle projet : tout sprint finit par sa vue Godot.**

## Objectif
Rendre la **luxuriance visible** : l'empilement multi-strates se lit à l'écran, le
tapis de couverture se voit, chaque espèce a sa silhouette, les colonies clonales
apparaissent. Plus un **banc d'observation F5** dédié.

## A. Pont (Python, read-only, protocole → 0.5.19)
- **Bloc `couverture`** dans le snapshot : le champ `couverture_sol` par plot
  (tuile), sérialisé dans `tools/simserver/serialize.py`. Optionnel côté vue
  (tolérance pré-0.5.19).
- **Par plante** : exposer `silhouette` et `clonal_mode` dans la sérialisation
  plante. Lecture pure, hors `_PLANT_ATTRS` du golden → **golden intact**.
- Bump version + changelog dans `tools/simserver/version.py` (0.5.19, décrire les
  champs ajoutés + tolérance rétro).

## B. Rendu C# (`Symbiose`, namespace, `res://` inchangés)
- **Ordre de dessin par strate** — dessiner arrière→avant :
  `sol → basse → moyenne → haute → grimpante`, y-sort À L'INTÉRIEUR de chaque
  strate. Le couvre-sol passe SOUS la potagère, SOUS la grimpante → superposition
  lisible. Adapter la boucle de rendu des plantes (`world/WorldView.*` / partial de
  tri) sans casser la projection iso 2:1 existante.
- **Couverture au sol** — teinte/densité au sol depuis le bloc `couverture`
  (nouveau layer léger, style des layers existants `LitterLayer`/`LeafLitterLayer`).
  Sol nu ↔ sol tapissé se distingue à l'œil, sans chiffre (philo #5).
- **Silhouette par espèce** — `PlantRenderer` consomme `silhouette` pour choisir la
  forme (touffe/rosette/étalée/dressée/tapis/buisson). Étendre `PlantRenderer.*`
  (partial cohérent).
- **Colonies clonales** — les ramets sont des plantes normales du snapshot ; vérifier
  qu'ils se dessinent bien (rien de spécial, mais valider la lisibilité d'un tapis).

## C. Banc d'observation F5 `luxuriance`
Ajouter un banc d'essai (cf. mécanisme `list_bancs`, protocole 0.5.4) : une tuile
peuplée pour EXHIBER la stratification — couvre-sol trèfle/violette + potagère +
framboisier + une grimpante, laissée tourner pour voir tapisser et s'empiler.
But : Nico ouvre le banc au F5 et JUGE la luxuriance.

## Compilation (filet VM)
`dotnet build Symbiose.csproj` doit passer (SDK 8.0 local, cf. CLAUDE.md §Stack).
Le **F5 visuel reste à Nico** (Godot pas sur la VM).

## Golden — INTACT
Aucune modif du tick moteur. Le pont ajoute des champs read-only hors
`_PLANT_ATTRS`. Vérifier `python3 -m tests.test_golden` **inchangé**.

## Ce qu'il NE faut PAS faire
- Pas de GDScript (C# only).
- Pas de logique de simulation en C# (Godot = vue — Option B).
- Ne pas re-figer le golden (ce tronçon ne touche pas le tick).
- Pas de fraction de zoom (paliers entiers ×4/×8/×16/×32).

## Fin de tronçon (clôture sprint)
MAJ `00_etat.md` (§REPRISE = sprint clos, points F5 restants), commit. Puis à la
clôture : MAJ `DETTE.md` (D65 ✅, **D62 absorbée/fermée**) + `BACKLOG.md` +
`journal/` (entrée de clôture) + mémoire projet.
