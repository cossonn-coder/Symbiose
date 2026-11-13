# Sprint ICÔNES & CURSEUR — état

> Sprint ③ de la refonte de l'accès aux gestes. Conception figée le 2026-11-12 :
> `docs/joueur/gestes/conception_refonte_palette.md` §5 (à lire en entier), et la DA
> `docs/rendu/pixelart/etude_brief_da_16bits.md` + `conception_jardin_vivant.md`.
> **Prérequis : `sprint_palette_tiroir` CLOS** (barre + tiroir + silhouettes en place).

## But
Refaire toutes les icônes de gestes dans la DA, donner au curseur l'icône du geste
en main, et l'animer quand le geste s'exécute. Pure vue C#. Reprend D118 (d) et (e).

## Décisions clés (Nico, 2026-11-12)
- Icônes **dessinées par le code** : grilles de caractères 16×16 cuites en texture
  (patron de la main gantée, `world/WorldView.Curseur.cs`), couleurs de la palette
  maître (`visuals/Palette16.cs`), affichage à un multiple entier.
- **Une icône par geste** (45). Silhouette d'un pressenti = même grille, une teinte.
- **Curseur = icône du geste actif** ; sans geste, la main gantée actuelle.
- **Animation à l'exécution** : 3-4 images jouées une fois quand le pont répond
  `applied` ; un refus joue une courte secousse. Animations partagées par famille de
  mouvement (verser, couper, frapper, poser, ramasser, remuer, écraser).
- Animation = signal : immobile hors action.

## Golden
**INTACT** (aucun fichier moteur touché). Lire `tests/golden_hash.txt`.

## Tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_moteur_icones_planche.md` — format de grille, cuisson, planche de contrôle, `GesteIcon` branché | **CLOS côté code 2026-11-13** (build vert, golden intact, planche regardée) |
| ② | `02_les_icones.md` — les 45 icônes, par familles, vérifiées à la planche | **CLOS côté code 2026-11-13** (45/45, build vert, golden intact, planche regardée) |
| ③ | `03_curseur_geste.md` — curseur à l'icône du geste, point chaud, silhouettes | **CLOS côté code 2026-11-13** (build vert, golden intact, captures regardées, F5 attendu) |
| ④ | `04_animations_execution.md` — animations d'exécution et de refus, clôture | à faire |

## Interdits communs
- Ne JAMAIS lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.
- Aucune couleur brute : tout passe par `Palette16`. GDScript interdit.
- Ne supprimer aucun code ; l'ancien dessin de `GesteIcon` est gardé tant que
  toutes les icônes ne sont pas livrées (repli), puis laissé en place, inactif.
- > 300 LDC → scinder (`tools/compte_ldc.py`) ; les grilles d'icônes vivent dans
  des fichiers de données dédiés, un par famille.
- `dotnet build` vert ; **regarder les PNG** de la planche (outil Read) avant de
  conclure un tronçon.

## Outillage posé au ① (à connaître pour ②-④)
- **Alphabet** (16 lettres, en-tête de `visuals/IconeGeste.cs`) : `K` contour, `N` ombre,
  `M`/`S` métal sombre/clair, `W` blanc, `L` paille, `B`/`C` bois sombre/clair, `T` humus,
  `O` terre cuite, `G`/`V` vert sombre/clair, `E`/`A` eau/eau claire, `R` rouge, `Y` jaune,
  `.` transparent. Chaque lettre = un rang de `Palette16.Maitre`.
- **API** : `IconeGeste.Texture(verbe, echelle, silhouette)` (cache), `Grille`, `Existe`,
  `Cuire` / `CuireSilhouette` (hors cache), `Liberer` (appelée par `LibererCurseur`).
- **Registre** : `IconeGeste.Familles` liste (nom, dictionnaire) dans l'ordre du tiroir ;
  un fichier par famille dans `visuals/icones/` (`IconesEau`, `IconesTaille`,
  `IconesCompost` existent). **Toute nouvelle famille s'ajoute à `Familles`.**
- **Planche** : `tools/capture_vm.sh -I -o DOSSIER` → `frame00000002.png` ; un bloc par
  famille (×4 sur gazon, silhouette ×4, puis ×2 sur terre + silhouette ×2), 4 blocs par
  colonne d'écran, 13 gestes max par bloc. Ordre imprimé au journal `[PlancheIcones]`.
- **`GesteIcon`** : texture cuite ×2 (32 px centrés dans 44) si une grille existe, sinon
  l'ancien dessin, déplacé tel quel dans `world/GesteIcon.Repli.cs`.

## Constats d'exécution
- **① — écart au kickoff** : `GesteIcon.cs` faisait **322 LDC** (et non 269). Scindé :
  l'ancien dessin part dans le partial `GesteIcon.Repli.cs` (252 LDC), `GesteIcon.cs`
  retombe à 88. Déplacement pur, aucun code supprimé.
- **① — `CuireMain`** factorisée sur `IconeGeste.Cuire` (les 4 lettres de la main sont
  dans l'alphabet, mêmes couleurs) : l'ancien corps de la fonction a disparu du fichier,
  comme le demandait le kickoff.
- **① — silhouette** : teinte = `Palette16.Maitre[22]` (ardoise moyenne), le gris qu'avaient
  déjà les pressentis. Un pressenti à icône cuite n'a plus de `SelfModulate` (la texture
  est déjà dans sa teinte) ; seule la plaque est assombrie. Aucun des 3 témoins n'est
  pressenti au banc : cet état n'a été vu **qu'à la planche**, pas dans le tiroir.
- **① — pas de PIL sur la VM** : aucun aperçu des grilles hors Godot, la planche est le
  seul moyen de les voir (~20 s par capture avec `--no-build`).
- **① — pour ②** : le sécateur témoin (`couper`) se lit comme une croix à ×2, trop proche
  de `ecraser` ; à redessiner. L'arrosoir et le bac se lisent.

- **② — 45 icônes livrées** (+ `planter_conteneur`, qui n'est PAS dans `COUTS` mais est dans
  `Gestes[]` et `FAMILLE_GESTE` : 46 grilles, 45 gestes vérifiés côté vue). Écart au kickoff :
  `COUTS` a 45 verbes sans `planter_conteneur` ; la table des familles en a 46.
- **② — fichiers** : 5 familles neuves (`IconesMain`, `IconesSol`, `IconesSemis`,
  `IconesStructures`, `IconesPaysage`), `IconesTaille`/`IconesCompost` complétés, registre
  `IconeGeste.Familles` à 8 familles. Plus aucun geste en repli sur l'ancien dessin.
- **② — points chauds** : `visuals/icones/IconesPointsChauds.cs` (verbe → (X, Y) en pixels de
  grille), à consommer au ③. Objets posés : milieu de la base.
- **② — vérification de démarrage** : `IconeGeste.Defauts(verbes)` appelée par
  `WorldView.VerifierIcones()` dans `BuildPalette`, debug seulement (`OS.IsDebugBuild`) :
  grille présente, 16×16, alphabet, point chaud sur un pixel peint. Journal :
  `[Icones] 45 gestes vérifiés, 0 défaut(s).`
- **② — `couper` redessiné** : sécateur en diagonale, bec de métal en haut à gauche, poignées
  rouges écartées ; ne se lit plus comme une croix. `pincer` = deux doigts gantés en pince sur
  une tige ; `arracher` = poing ganté avec manche de cuir ; `tailler` = scie d'élagage.
- **② — planche finale** (×4, silhouette ×4, ×2 sur terre + silhouette ×2) :
  `sprints/joueur/gestes/sprint_icones_curseur/planche/planche_02_icones.png`.
- **② — icônes encore faibles (F5)** : `palisser` (pelote de raphia, se lit comme une balle),
  `endiguer` (digue chargée à ×2), `glaner` (feuilles + gant peu nets à ×2), `broyer` (chargé),
  `pincer` (lisible à ×4, juste à ×2). Silhouettes proches : `planter` / `planter_conteneur` /
  `bouturer` ; `poser_pot` / `palisser` / `poser_ruche` (formes rondes). La couleur départage.
- **② — outil de travail** : un aperçu PNG hors Godot (Python pur, écrit dans le scratchpad,
  non versionné) a servi d'itération rapide avant la planche Godot.
- **② — `WorldView.Palette.cs`** passe à 210 LDC (vigilance OK).

- **③ — mécanisme** (`world/WorldView.Curseur.cs`, 132 LDC) : DEUX formes de curseur système.
  `Arrow` garde la main gantée ; `Cross` (`FormeGeste`) porte l'icône du geste armé (cache
  `IconeGeste.Texture(verbe, 2)`, point chaud = `(X+½, Y+½)×2` depuis `IconesPointsChauds`).
  `Input.SetDefaultCursorShape(Cross)` quand un geste est armé, `Arrow` sinon. Sur un Control
  qui capte la souris (barre, tiroir, panneaux), Godot montre la forme du Control (Arrow) →
  **la main revient seule sur l'interface, sans test de survol**. Le conteneur du monde est
  `mouse_filter = Ignore` : il ne gêne pas.
- **③ — écart au kickoff (mieux que prévu)** : le geste actif n'est pas suivi par un crochet
  dans `SelectGeste` mais par une comparaison du verbe chaque image dans `UpdateCurseur`
  (`SuivreGesteCurseur`) ; la texture n'est reposée qu'au changement. Raison : `_gesteIndex`
  est écrit par 4 chemins (`SelectGeste`, `DrainMacro`, 2 bancs) — un seul point de suivi les
  couvre tous.
- **③ — tap** : `TapCurseur` ne fait rien quand une icône de geste est en main (image fixe ;
  l'animation viendra au ④). Sans geste, tap 150 ms inchangé.
- **③ — `LibererCurseur`** : vide aussi la forme `Cross` et remet la forme par défaut à Arrow
  avant `IconeGeste.Liberer()` (la texture du curseur vient du même cache).
- **③ — capture** : le curseur système n'apparaît PAS dans le Movie Maker. Témoin ajouté :
  `world/WorldView.CurseurTemoin.cs` (25 LDC), un `Sprite2D` dans un calque 120, créé
  seulement si `-s X,Y` est donné (1 ligne dans `WorldView.Capture.cs`). Il imite la règle :
  main si `GuiGetHoveredControl() != null`, sinon icône du geste. **Il prouve la logique C#,
  pas le rendu de l'OS** : le changement Cross/Arrow réel n'est vérifiable qu'au F5.
- **③ — captures** (×4, souris au centre ; puis souris sur la barre) : `planche/curseur_03_*.png`
  — panier (`recolter`), plantule déracinée (`deraciner`), botte (`ecraser`), et main + info-bulle
  sur la barre avec `deraciner` armé. Les trois icônes se lisent à ×2 sur le monde.
- **③ — à valider au F5** : (a) l'icône apparaît dès qu'on arme un geste, la main sans geste ;
  (b) la main revient sur la barre, le tiroir, les panneaux (et l'icône au retour sur le jardin) ;
  (c) le point chaud tombe où on vise (plante/plot choisi = sous le pixel actif) ; (d) sous
  Windows, `Cross` personnalisé n'est pas remplacé par la croix système ; (e) taille ×2 lisible
  sur l'écran de Nico (échelle d'écran Windows : le curseur OS n'est pas agrandi par Godot).

## §REPRISE
Lire `CLAUDE.md`, ce fichier, le doc de conception §5, puis le premier kickoff « à faire ».
**Prochain : ④ `04_animations_execution.md`**. Le curseur de geste vit sur la forme `Cross`
(`FormeGeste`, `WorldView.Curseur.cs`) ; l'animation remplacera l'image fixe posée par
`SuivreGesteCurseur` (et le `return` de `TapCurseur` quand `_curseurIcone`). Témoin capture :
`WorldView.CurseurTemoin.cs` (à faire suivre l'image animée). ③ n'est pas committé par le
sous-agent (l'orchestrateur commit).
