# 2026-06-25 — Sprint POTS, BACS & SUBSTRATS · VUE GODOT ⑥ (a/b/c) — SPRINT TERMINÉ

> Dernier volet du sprint : la VUE Godot (Option B — Godot rend, Python reste le
> moteur). 3 sous-tronçons ⑥a/⑥b/⑥c, **couche B pure C#**, AUCUN fichier Python
> touché → golden **trivialement NEUTRE** (`2ab026ad…`) sur tout le volet vue.
> `dotnet build Symbiose.csproj` vert à chaque tronçon ; le F5 visuel reste à Nico.
> État détaillé : `sprints/sprint_pots_bacs/00_etat.md`. **Sprint pots/bacs/substrats
> intégralement CLOS (moteur ①→⑤ + vue ⑥).**

## Ce que la vue montre
Tout est LU dans le bloc `containers` du snapshot 0.5.7 (déjà exposé en ④/⑤) — la
vue ne RECALCULE rien (effet nain, couplage, décompo = faits MOTEUR, on les SIGNALE).

- **⑥a rendu statique** — `visuals/ContainerStructure.cs` (placeholder procédural iso :
  POT tronc-cône évasé, BAC caisse N×M) + `world/WorldView.Conteneurs.cs` (câblage
  lecture, un nœud par conteneur dans la couche YSort `_objects`, plantes du mini-sol
  via `PlantRenderer`). Substrat = teinte de la SURFACE (6 recettes → Palette16).
- **⑥b interaction** — `world/WorldView.Actions.cs` : 4 gestes outil+clic
  (`poser_pot`/`poser_bac_culture`/`deplacer_pot`/`planter_conteneur`), cycle de
  substrat (touche B), déplacement à 2 temps ; `FindNearestContainer` (picking),
  HUD. Pas de drag&drop (décision Nico).
- **⑥c indices diégétiques du couplage** (philo #5, mots/indices, pas de chiffres) :
  - **A. fond ouvert/fermé** — bac `fond_ouvert` → fines racines pâles débordent sous
    l'arête avant vers la tuile (`DrawOpenBottomRoots`) ; pot/bac fermé → liseré
    d'arête bas PLEIN (`DrawClosedBottom`). Le pot est toujours fermé.
  - **B. effet nain** — pot root-bound (volume ≤ 60 L, fond fermé, ≥1 plante vivante)
    → court chevelu de racines TASSÉES à la lèvre (`DrawRootBoundFringe`) ; grand
    volume / bac couplé (nain levé ⑤) → pas de marque. VUE PURE : on déduit QUAND
    dessiner l'indice de cause, on ne recalcule jamais l'effet (`height_cm` = moteur).
  - **C. étiquette de survol** — `world/WorldView.ConteneursEtiquette.cs` (nouveau
    partial) : Label NET hors SubViewport, mots SEULS — substrat lisible + taille
    (petit/grand pot, bac) + fond ouvert/fermé + humidité (sec/frais/humide) +
    fertilité (pauvre/moyen/riche, nutriment LIMITANT de Liebig). `UpdateContainerLabel`
    appelé chaque frame dans `_Process`.

## Fix d'alignement signalé
`ContainerStructure.SubstratTeinte` (⑥a) indexait `"drainant"` alors que le registre
moteur (`world/substrat.py`) nomme la recette `"drainant_mineral"` → la teinte de
surface du mélange drainant tombait sur le repli gris `SolInconnu`. Corrigé sur la
clé canonique Python (load-bearing pour l'objectif « substrat reflété » du ⑥c).

## Garde-fous tenus
- Golden **trivialement NEUTRE** (`2ab026ad…`) : aucun fichier Python touché.
- `dotnet build` vert (0 avert., 0 err.).
- Couche B pure (Godot = vue), divergence D10 non aggravée : la vue MONTRE, ne
  calcule pas. Tailles fichiers < 350 LDC pur.

## Reste — VALIDATION F5 (Nico)
Le seul filet sur la VM est le build ; le F5 visuel reste à Nico. À observer (la
carte de démo ne pose aucun conteneur → poser un pot/bac à la main via ⑥b) :
- ⑥a forme/échelle pot & bac, teintes de substrat distinctes, plante centrée + YSort.
- ⑥b déplacement à 2 temps confortable, knobs de pose (75 L / bac 2×2 / fond ouvert).
- ⑥c lisibilité des indices (racines fond ouvert vs liseré fermé, racines tassées),
  seuils qualitatifs de l'étiquette, concurrence éventuelle avec l'étiquette de plante.
Liste complète : sections « Points à VALIDER au F5 » d'⑥a/⑥b/⑥c dans `00_etat.md`.
