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
| ① | `01_moteur_icones_planche.md` — format de grille, cuisson, planche de contrôle, `GesteIcon` branché | à faire |
| ② | `02_les_icones.md` — les 45 icônes, par familles, vérifiées à la planche | à faire |
| ③ | `03_curseur_geste.md` — curseur à l'icône du geste, point chaud, silhouettes | à faire |
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

## Constats d'exécution
(à remplir)

## §REPRISE
Lire `CLAUDE.md`, ce fichier, le doc de conception §5, puis le premier kickoff « à faire ».
