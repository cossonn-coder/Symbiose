# ② Animations du curseur précuites

> Lire d'abord : `CLAUDE.md`, `00_etat.md`, `docs/joueur/gestes/conception_gestes_lisibles.md`
> §4, puis l'état du sprint précédent `sprints/joueur/gestes/sprint_icones_curseur/00_etat.md`
> (outillage : alphabet, `IconeGeste`, planches, points chauds, `AnimationGeste`).
> DA : `docs/rendu/pixelart/etude_brief_da_16bits.md`. Golden : **INTACT** (pure vue C#).

## Objectif
Remplacer les animations « icône décalée de 1 à 3 px » par des **suites d'images qui
décomposent le geste**, cuites une fois, jouées une fois à `applied`. Chaque geste doit
se lire à ×2 sur l'écran.

## À faire
1. **Moteur d'images** (`visuals/AnimationGeste.cs`, à faire évoluer, pas à jeter) :
   une animation = liste d'images ; chaque image est soit une **grille dessinée** 16×16
   (alphabet existant), soit une **transformation** de l'icône : rotation autour d'un
   **pivot** (pixel par pixel, voisin le plus proche, déterministe ; ex. arrosoir incliné
   de 30-45°), décalage **≥ 3 px de grille**, pixels d'effet. Le point chaud ne bouge pas.
   Les grilles d'images vivent dans des fichiers de données, un par famille (patron
   `visuals/icones/`). La table `IconesMouvements.cs` peut rester comme repli, mais chaque
   geste reçoit sa propre suite.
2. **Les décompositions** (§4) — prioritaires : `arroser` (s'incline, l'eau coule de la
   pomme), `ecraser` (le pied monte haut puis descend franchement), `deraciner` (traction
   vers le haut, la motte suit), `arracher` (la main se ferme sur une touffe et tire),
   `favoriser_auxiliaire` (la coccinelle ouvre les ailes), `pincer`, `glaner`, `drainer`,
   `bouturer`, `couper`, `tailler`, `retourner`. Puis **tous les autres gestes** au même
   standard (4 à 6 images, mouvement visible).
3. **Icônes** : inverser les outils — sécateur = `tailler`, scie = `couper` (échanger les
   grilles ET revoir points chauds) ; redessiner `pincer` et `glaner` pour qu'ils se
   comprennent.
4. **Refus** : secousse ±2 px de grille (au lieu de ±1).
5. **Usage hors curseur** : exposer une API qui rend les images d'un geste sous forme de
   textures pour un sprite du MONDE (utilisée au ⑤ pour les gestes de l'automate). Pas de
   branchement monde ici.
6. **Vérification** : `IconeGeste.Defauts` (ou équivalent) exige une animation par geste.
   Planche d'animations (`tools/capture_vm.sh -W`, `visuals/PlancheAnimations.cs`) mise à
   jour ; **regarder les PNG** (outil Read) à ×4 et ×2, itérer jusqu'à ce que chaque
   décomposition se lise. Planche finale versionnée dans `planche/` du sprint.

## Ne PAS faire
- Ne pas toucher au moteur Python. Aucune couleur brute (tout par `Palette16`).
- Ne pas changer le déclenchement (bloc 1b de `WorldView.cs`, déjà à 300 LDC : n'y rien
  ajouter). Ne supprimer aucun code. > 300 LDC → scinder. GDScript interdit.
- Ne jamais lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.

## Fin de tronçon
`dotnet build Symbiose.csproj` vert, golden intact, planche regardée. `00_etat.md` :
API pour le monde (nom, signature), gestes encore faibles à la planche, écarts.
