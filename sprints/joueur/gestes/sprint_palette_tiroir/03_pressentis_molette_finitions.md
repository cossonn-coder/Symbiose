# ③ Pressentis, Ctrl+molette, finitions D118, clôture

**Lire avant** : `CLAUDE.md`, `00_etat.md`, doc de conception §3.4 et §4.
**Nature** : C# (+ banc). **Golden : INTACT**.

## À faire
1. **Silhouettes** : dans le tiroir, chaque geste de `player.gestes_pressentis`
   apparaît dans sa famille en silhouette (icône d'une seule teinte sombre, non
   cliquable). Au survol : la phrase d'ambiance du pont, rien d'autre (pas de nom
   du geste, pas de condition). `GesteIcon` a déjà un état `Verrouille` : le
   réutiliser ou ajouter un état `Pressenti`.
2. **Signal** : quand un geste s'ouvre (`debloques_recents` / `result.debloques`) ou
   qu'un pressenti neuf apparaît, le bouton du tiroir bat quelques secondes
   (animation = signal ; immobile sinon). Le flash existant de la barre reste.
3. **Ctrl+molette** : dans `WorldView.Controls.cs` (la molette est lue vers la
   ligne 153 pour le zoom), si Ctrl est tenu, la molette fait défiler le geste
   actif parmi les cases occupées (`CycleSlots(±1)`) et ne zoome pas.
4. **D118 (b)** : un geste choisi dans un menu clic droit (barre ou tiroir) devient
   aussitôt le geste actif (`OnEditMenuChoisi` range sans sélectionner aujourd'hui).
5. **D118 (c)** : une plante au premier plan contre la maison doit recevoir le
   clic. `WorldView.Controls.cs:173` teste `!PointeUnePlante(canvas) &&
   ClicSurMaison(canvas)` ; la cause exacte n'est pas isolée (hypothèses : 
   `ContientCurseur` trop strict sur une plante cuite, nœud non visible à ce
   palier, ordre de profondeur). **Reproduire d'abord** sur un banc avec une
   plante collée au mur (`verger_mur` ou équivalent), puis corriger la cause, pas
   le symptôme.
6. **Macros** : débrancher `Key.K` et `Key.J` dans `Controls.cs` et retirer leur
   mention de l'aide ; laisser `WorldView.Macros.cs` et le code Python en place,
   avec un commentaire daté « débranché le 2026-11, R8 ».
7. **Banc et captures** : tiroir avec silhouettes, phrase au survol (`-s X,Y`).
8. **Clôture du sprint** : `DETTE.md` (retirer (b) et (c) de D118 ; solder ce qui
   reste de D80 si concerné), `BACKLOG.md` + `docs/joueur/gestes/backlog_gestes.md`,
   entrée `journal/` + index, `00_etat.md` avec la **recette F5**.

## Vérification
`dotnet build` vert ; golden inchangé ; captures regardées.

## À ne pas faire
- Aucun texte qui révèle comment ouvrir un geste.
- Ne pas refaire les icônes ni le curseur (sprint suivant).
