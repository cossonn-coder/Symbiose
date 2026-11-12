# ④ Vue minimale : tous les gestes jouables + banc F5

**Lire avant** : `CLAUDE.md`, `00_etat.md` (constats de ①②③), le doc de conception.
**Nature** : C# (vue) + un banc Python. **Golden : INTACT**.
`dotnet build Symbiose.csproj` doit rester vert (`~/.dotnet`, déjà dans le PATH).

## Objectif
Que Nico puisse, au F5, ouvrir et exécuter chaque geste du moteur avec la palette
ACTUELLE (10 cases + menu clic droit). La nouvelle palette est le sprint suivant :
ici, pas de refonte visuelle.

## État du code (vérifié le 2026-11-12)
- `world/WorldView.Actions.cs` : tableau `Gestes[]` `(Verb, Nom, Kind)`. Kinds :
  `p` plante par position, `m` point de milieu local `{tile, x_cm, y_cm}`, `q` plot
  `{tile, r, c}`, `s` structure existante, `P`/`C` conteneurs, `U` pailler, `D`
  broyer, `L` secteur de périphérie, `E`/`b`/`g` deux temps.
- Absents de `Gestes[]` : `poser_tuteur`, `poser_treillis`, `poser_pergola`,
  `palisser`, `poser_voile`, `poser_cloche`, `poser_ombriere`, `poser_ruche`,
  `recolter_miel`.
- Dispatch : `world/WorldView.ActionDispatch.cs`, `WorldView.ActionPicking.cs`.
  Icônes : `world/GesteIcon.cs` (connaît déjà une famille « supports » et « ruche »).
- Natures de mulch côté vue : `Natures = { "paille", "brf", "aiguilles" }` ; le
  moteur a aussi `feuilles` (produit par `glaner`). Vérifier `NATURES_MULCH`
  (`fields/ecofields.py`) et aligner la vue, sinon le paillis glané est inutilisable.
- Atelier : panneau alimenté par la commande `atelier` du pont (liste d'outils
  data-driven) ; vérifier qu'il affiche bien les outils neufs sans code en dur.
- Courrier : panneau alimenté par `courrier`.
- Bancs : `data/code/bancs/` (`palette_gestes.py`, `nucleation.py`, base
  `bancs/base.py`).

## À faire
1. Ajouter les 9 gestes à `Gestes[]` avec le kind qui correspond à la route du
   pont posée au ③ (supports = `m` ; couvertures = `q` ; `palisser` = `p` ;
   `poser_ruche` = `q` ; `recolter_miel` = `s` ou ce que `structures_route.py`
   attend : le lire). Une icône provisoire par geste dans `GesteIcon` (sera refaite
   au sprint ③, ne pas y passer de temps).
2. Aligner les natures de mulch sur le moteur.
3. Vérifier l'Atelier (outils neufs achetables, « possédé » affiché) et le
   courrier (lettres neuves lisibles). Corriger le strict nécessaire.
4. **Banc `acces_gestes`** : un jardin de départ ordinaire, SANS forçage de
   déblocage, avec ce qu'il faut pour franchir chaque porte en quelques minutes :
   litière à glaner, une grimpante sans appui, un merle et des fruits, de quoi
   combler vite une lettre, Vigueur suffisante pour l'Atelier. Oracle Python dans
   `tests/bancs/` : en jouant les gestes par le pont, **les 45 gestes finissent
   ouverts** (c'est le test de bout en bout de la refonte).
5. Captures au banc VM (`tools/capture_vm.sh`) : palette avant/après ouverture d'une
   technique.
6. Clôture du sprint : `DETTE.md` (D133 fermée ; D118 inchangée), `BACKLOG.md` +
   `docs/joueur/gestes/backlog_gestes.md`, entrée `journal/` + index `journal.md`,
   `00_etat.md` avec la **recette F5** pour Nico (une ligne par porte : quoi faire,
   quoi voir).

## Vérification
`dotnet build` vert ; golden inchangé ; oracle du banc vert ; captures regardées.

## À ne pas faire
- Pas de tiroir, pas de nouvelles icônes soignées, pas de curseur : sprints ② et ③.
- Ne pas supprimer les macros.
