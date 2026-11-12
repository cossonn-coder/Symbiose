# ④ Animations d'exécution et de refus, clôture

**Lire avant** : `CLAUDE.md`, `00_etat.md`, doc de conception §5.
**Nature** : C#. **Golden : INTACT**.

## Objectif
Quand un geste s'exécute, le curseur s'anime d'une façon propre au geste ; quand il
est refusé, il le dit sans texte.

## Modèle
- Sept **mouvements**, chaque geste en a un (table verbe → mouvement, à côté des
  grilles) :
  - **verser** : arroser ;
  - **couper** : pincer, couper, tailler, bouturer, greffer ;
  - **frapper** : becher, grelinette, creuser, drainer, deraciner, arracher,
    entailler, abattre, receper, eteter, endiguer, deriver ;
  - **poser** : tous les `poser_*`, planter, planter_conteneur, deplacer_pot,
    palisser ;
  - **ramasser** : recolter, manger, glaner, recolter_miel, favoriser_auxiliaire ;
  - **remuer** : composter, retourner, epandre, empiler_bois, pailler, broyer ;
  - **écraser** : ecraser.
- Une animation = 3 ou 4 images de curseur, ~80 ms chacune, jouée **une fois**.
  Deux façons de produire les images, au choix selon le rendu à la planche :
  transformer la grille de l'icône (rotation de quart, décalage, bascule) et
  ajouter 1 à 3 pixels d'effet (gouttes, éclat, terre, copeau) ; ou dessiner des
  grilles d'images dédiées pour les mouvements où la transformation est laide.
  Le point chaud ne bouge pas : c'est le dessin qui bouge.
- **Refus** : secousse horizontale de 2 images (±1 pixel de dessin), commune à tous.

## État du code (à relire)
- Le retour d'un geste arrive dans `world/WorldView.ActionDispatch.cs`
  (`result.applied`, message). Les gestes à deux temps (épandre, déplacer un pot,
  bouturer, greffer) n'envoient qu'au second clic : le premier clic ne joue aucune
  animation d'exécution (un simple tap suffit).
- `UpdateCurseur()` gère déjà une échéance en millisecondes (`_tapFinMs`) : étendre
  ce mécanisme à une petite file d'images, sans `_Process` supplémentaire.

## À faire
1. Table verbe → mouvement + cuisson des images d'animation (cache, libération).
2. Jouer l'animation à la réponse `applied` ; la secousse au refus. Si un nouveau
   clic arrive pendant une animation, elle repart du début.
3. Étendre la planche : toutes les images de chaque mouvement, sur une icône témoin
   par mouvement. Regarder, corriger.
4. Retirer le tap de la main quand un geste est armé (remplacé par l'animation).
5. **Clôture du sprint et de la refonte** : `DETTE.md` (retirer (d) et (e) de
   D118 pour la palette ; noter ce qui reste hors DA), `BACKLOG.md` +
   `docs/joueur/gestes/backlog_gestes.md`, entrée `journal/` + index,
   `00_etat.md` avec la **recette F5** (liste des gestes à essayer, un par
   mouvement, plus un refus).

## Vérification
`dotnet build` vert ; planche des animations regardée ; golden inchangé.

## À ne pas faire
- Aucune animation en boucle ni au repos.
- Pas de son, pas de texte, pas de particules dans le monde (hors périmètre).
