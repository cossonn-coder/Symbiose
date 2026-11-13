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

## §REPRISE
Lire `CLAUDE.md`, ce fichier, le doc de conception §5, puis le premier kickoff « à faire ».
**Prochain : ② `02_les_icones.md`.** ① n'est pas committé par le sous-agent (l'orchestrateur commit).
