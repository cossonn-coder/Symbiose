# ④ Objet en main et ergonomie

> Lire d'abord : `CLAUDE.md`, `00_etat.md`, `docs/joueur/gestes/conception_gestes_lisibles.md`
> §6 en entier. Golden : **INTACT** (vue C# ; ajout au pont seulement si une donnée manque,
> lecture pure).

## Objectif
Qu'aucun geste ne soit incompris : ce qu'on tient se voit, ce qu'on peut viser se voit,
et les petites frictions de D136 (f) disparaissent.

## À faire
1. **Objet en main** pour les gestes à deux temps. Lire d'abord comment ils sont gérés
   (`world/WorldView.ActionDispatch.cs`, autour du « SAISIR le bac/pile source » et de la
   bouture ; `world/WorldView.Conteneurs.cs` pour le pot). Après le premier clic, le
   curseur porte l'objet : bouture (`bouturer`), pelletée de compost (`epandre`), brassée
   de litière (`composter` — vérifier son ordre de clics), **le pot** (`deplacer_pot`,
   le pot suit la souris). Les cibles valides sont signalées (pour `bouturer`, les plots
   de la même tuile ; ailleurs, l'objet en main se grise). Échap / clic droit lâche
   l'objet. Grilles d'objets dans l'alphabet d'`IconeGeste`.
2. **`favoriser_auxiliaire` visible** : dessiner l'habitat posé (rondelle `auxiliaire`
   sur un tuteur de la tuile) — vérifier ce que le snapshot exporte des tuteurs et
   rondelles ; ajouter au pont en lecture pure si absent.
3. **`ecraser` et les volants** : sous `ecraser`, un sprite qui vole (champ `vole` exporté
   au ①) n'est pas une cible (pas de surlignage, pas de clic).
4. **Catalogue des graines** de `planter` : trié par ordre alphabétique du nom affiché,
   il se referme au choix d'une graine.
5. **`planter_conteneur`** : lire le parcours actuel, le réduire à « graine choisie (même
   sélection que `planter`) + un clic sur le pot ».
6. **Récolter le fruit** : sous `recolter`, la désignation vise l'**organe mûr** dessiné
   (positions des organes dans `visuals/PlantRenderer.Organs.cs`) ; le clic sur un fruit
   récolte la plante qui le porte ; un clic sur le tronc ou une plante sans organe mûr ne
   récolte pas et le dit en mots.
7. **Pot hors du jardin** : si le ① a conclu « bug côté vue », le corriger ici.

## Vérification
Captures VM (`tools/capture_vm.sh`, témoin de curseur `-s X,Y`) de chaque objet en main
et du catalogue ; **regarder les PNG**. Ce qui ne se voit qu'au F5 (curseur OS, clics réels)
va dans la recette de `00_etat.md`.

## Ne PAS faire
- Ne pas toucher aux outils ni à l'Atelier (sprint `outils_atelier`).
- Ne pas modifier les règles moteur (faites au ①). Pas de chiffre à l'écran.
- Ne rien ajouter à `WorldView.cs` (300 LDC). > 300 LDC → scinder. GDScript interdit.
- Ne jamais lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.

## Fin de tronçon
`dotnet build` vert, golden intact, captures regardées. `00_etat.md` : comportement de
chaque point, ajouts au pont éventuels (+ version), points F5.
