# Sprint pots, bacs & substrats — état partagé

> **Conception FIGÉE** → source de vérité = `docs/conception/CONCEPTION_POTS_BACS_SUBSTRATS.md`
> (la lire d'abord). Ce fichier = état léger + carte des sous-sprints. Mis à jour
> en fin de **chaque** sous-sprint. Boucle projet : `0N` → coder → vérifier/PROUVER
> golden neutre → MAJ ce fichier → commit → `/clear` → `0N+1`.

## En une phrase
Un **conteneur** (pot mobile / bac immobile) est un **`EcoFields` miniature** que
le joueur compose avec un **substrat data-driven** (terreau/compost/drainant/
lasagnes/terre/mycélium) et déplace dans le jardin ; un petit volume **rapetisse**
la plante (effet nain hybride) ; un bac à fond ouvert **communique** avec la tuile
dessous (drainage, racines, microbiome).

## Décisions structurantes (détail dans le doc de conception)
- Conteneur = `EcoFields(rows, cols)` réutilisé (pot 1×1, bac N×M). **Zéro nouveau
  modèle chimique** : tous les ticks existants marchent. Nouvel objet
  `world/Container`. Liste de conteneurs **VIDE au repos** → golden neutre.
- Substrat = registre `world/substrat.py` (6 recettes), initialise les champs +
  fixe le drainage. `tick_hydrology` gagne un `drainage_override=None`
  (rétrocompatible → tuiles bit-identiques).
- Effet nain HYBRIDE : réservoir réduit (`volume_factor` sur `plant_uptake`,
  défaut 1.0) + plafond racinaire (uptake borné aux cellules du conteneur) + léger
  signal root-bound (bride la croissance segmentaire au-delà d'un seuil). Philo #2.
- Mobilité : `deplacer_pot` coûte Vigueur JOUEUR seule, pas de choc plante.
  Lumière recalculée à la position. Bacs immobiles.
- Couplage fond ouvert (bac) : drainage→tuile, racines descendent (lève le nain),
  microbiome/om diffusent. Lasagnes = litière pré-chargée (décompo confinée, arc
  validé en ⑤).
- **Golden NEUTRE sur TOUT le sprint** (aucun conteneur dans le smoke) — à PROUVER
  bit-identique à chaque tronçon. Aucun re-figeage attendu.

## Carte des sous-sprints (5, indépendants)
| # | Sujet | Kickoff | État |
|---|-------|---------|------|
| ① | Substrat data-driven (registre + 6 recettes + `drainage_override`) | `01_substrat.md` | à faire |
| ② | Conteneur `EcoFields` miniature + tick chimique isolé + boucle | `02_conteneur.md` | à faire |
| ③ | Plante en pot + confinement racinaire hybride (effet nain) | `03_confinement.md` | à faire |
| ④ | Mobilité + bacs N×M immobiles + pont snapshot | `04_mobilite_bacs.md` | à faire |
| ⑤ | Couplage fond ouvert + lasagnes (arc complet) | `05_couplage_lasagnes.md` | à faire |
| ⑥ | Vue Godot (pots/bacs/substrats visibles) — **différé** (Option B) | à écrire | différé |

## Conventions
- Source de vérité = Python `data/code/`. Lancement depuis `data/code/`
  (`python3 main.py`, `python3 -m tests.test_golden`).
- Couches : `Container` est en `world/` (peut importer `fields` + `plants` ;
  `fields` n'importe jamais `world` → pas de cycle). Vérifier ce sens à ②.
- Golden : PROUVER la neutralité (hash bit-identique h1==h2 et == hash courant) à
  chaque tronçon qui touche la boucle. Si une dérive apparaît, l'ANALYSER avant de
  re-figer (probable bug : aucun conteneur ne doit exister dans le smoke).
- Knobs explicites (valeurs de départ, calibrage post-test) — philo #3,
  déterminisme (zéro RNG, ordre d'itération stable).
- Tout garder (scripts de mesure inclus). Un fichier à la fois sauf synchro
  cohérente avant commit.

## Hash golden de référence (à renseigner au démarrage de ①)
- smoke `tests/test_golden.py` : `<à mesurer avant toute modif>`
- population `tests/test_population.py` : `<à mesurer avant toute modif>`
> Premier geste de ① : lancer les deux suites, NOTER les hashs ici, puis vérifier
> qu'ils restent identiques à chaque tronçon.

## REPRISE (démarrage à froid)
Sprint **non commencé**. Lire le doc de conception puis `01_substrat.md`. Aucun
code écrit. État du moteur amont : sprint plasticité clos (golden `2ab026ad…`,
pont 0.5.3) — cf. `journal.md` / mémoire `project_status`.
