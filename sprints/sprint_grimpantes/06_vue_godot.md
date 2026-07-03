# ⑥ — Vue Godot (supports + accroche + vrilles) + pont + banc d'observation

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + CE fichier. Conception :
> `docs/conception/CONCEPTION_GRIMPANTES.md` §8/§10 + `CONCEPTION_RENDU_FEUILLAGE
> §7/E6`. **Golden INTACT** (vue pure + banc jamais monté pour smoke/full).
> Filet de compilation C# : `dotnet build Symbiose.csproj` sur la VM (F5 = Nico).

## Objectif
Rendre visible la grimpe : dessiner les supports posables, l'accroche, le détail
des vrilles ; exposer les supports au pont ; et monter le **banc d'essai
`grimpantes`** (demande Nico 2026-07-03) pour observer au F5.

## A. Pont Python → vue (bump ENGINE_VERSION)
- `tools/simserver/serialize.py` : ajouter au snapshot, par tuile, la liste des
  `Support` (type, x_cm, y_cm, height_cm) et, par plante grimpante, son état
  d'**accroche** (`support` : none / type + position d'appui). Patron des blocs
  existants (structures bac/pile, plantes).
- `plants/base/instance.py` : inclure `support` dans la sérialisation d'état si
  pertinent (déjà posé en ①).
- `tools/simserver/version.py` : **bump `ENGINE_VERSION`** + changelog. Recaler
  l'assert de version des tests `simserver/*`.

## B. Rendu C# (bonus décision A : la grimpe est quasi gratuite)
Comme la hauteur émerge de la VRAIE géométrie des segments, une grimpante qui
grimpe a déjà ses segments montés le long du support DANS le snapshot, et une
affalée a ses segments au sol → `visuals/PlantRenderer.cs` les dessine
correctement **sans code spécifique**. Il reste :
- `visuals/` (nouveau `SupportRenderer.cs` ou dans `WorldView`) : placeholders
  procéduraux des supports (tuteur = pieu, treillis = grille, pergola = portique
  qui projette une ombre), patron des placeholders bac/pile/maison
  (`Polygon2D`, projection déléguée à `WorldView.WorldToScreen`).
- `visuals/PlantRenderer.Organs.cs` : détail esthétique des **vrilles** (spirales)
  au point d'accroche — c'est le rendu différé de `CONCEPTION_RENDU_FEUILLAGE §7`
  (E6), désormais débloqué par la mécanique ①→③.
- Indice d'accroche discret (facultatif) là où la plante tient son support.

## C. Banc d'essai `grimpantes` (Python — instrument d'observation F5)
- `bancs/` : nouvelle fabrique `grimpantes()` (fichier thématique adéquat, ex.
  `bancs/biotique.py`), enregistrée dans `bancs/__init__.py` (`BANCS["grimpantes"]`).
  Patron `bancs/base.py` (`build_banc_tile` / `monde`). Composition :
  - **Haricot planté JUSTE À CÔTÉ d'un tournesol** (plots adjacents) → exerce
    l'accroche sur hôte vivant (③) : le haricot grimpe le tournesol.
  - **Tuile de Solanaceae au SUD** (`origin_y_cm` grand) : tomates + basilic +
    poivrons — secteur ensoleillé/chaud (frileuses favorisées).
  - Un **tuteur/treillis** posé près d'un haricot (montre l'accroche structure),
    un **lierre au pied du mur sud** (crampon), un **jasmin palissé** (⑤).
  - **Départ début printemps = AUTOMATIQUE** : `cmd_init` pose `week=1` →
    `week_in_year=1` → `SAISONS["printemps"]=range(1,14)` = début du printemps.
    Rien à coder pour ça.
- Vérifier au lancement : `init config="grimpantes"` monte le banc (patron
  `cmd_init`, branché APRÈS smoke/full).

## Golden
**INTACT** — hash inchangé vs ①. La vue et le pont ne touchent pas les grandeurs
du digest ; le banc n'est JAMAIS monté pour `smoke`/`full` (cf. `cmd_init`).
1. `python3 -m tests.test_golden` → **inchangé** vs hash ①.
2. Tests `simserver/*` : recaler l'assert `ENGINE_VERSION` + un check de présence
   du bloc `supports`.
3. `dotnet build Symbiose.csproj` → vert.

## Ce qu'il NE faut PAS faire
- Ne pas ré-implémenter la grimpe côté C# (Godot est une VUE — Option B) : la
  géométrie vient du snapshot.
- Ne pas monter le banc pour smoke/full (golden).

## F5 (Nico)
- Banc `grimpantes` : haricot grimpant le tournesol puis l'ombrageant ; haricot
  tuteuré droit ; lierre au mur ; jasmin palissé ; champ Solanaceae au sud qui
  lève au printemps. Calibrage à l'œil (hauteurs supports, vrilles).
