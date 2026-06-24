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
| ① | Substrat data-driven (registre + 6 recettes + `drainage_override`) | `01_substrat.md` | **FAIT** (golden bit-identique) |
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

## Hash golden de référence (mesurés au démarrage de ①, 2026-06-24)
- smoke `tests/test_golden.py` : `2ab026ad2b3f484777a2a29f804e1a4785ecffd6976fc0058fe0a33dd1498646`
- population `tests/test_population.py` : `6056713d4dd1e2a79964411961909545433f8513a530a2b39151cbe6aabe471b`
> Mesurés AVANT toute modif puis RE-VÉRIFIÉS après ① : les deux restent **bit-identiques**
> (golden NEUTRE prouvé). À re-vérifier identiques à chaque tronçon suivant.
>
> NB suite amont `tests/test_sim_server.py` : **185/186** verts AVANT ① déjà (1 check
> rouge préexistant « pommier pré-âgé — 0 fruits @ S52 », sans rapport avec le sprint) ;
> reste 185/186 après ① → AUCUNE régression introduite.

## REPRISE (démarrage à froid)
Tronçon ① **FAIT** (data pure, golden bit-identique). Acquis :
- `world/substrat.py` — `SubstratRecette` (`@dataclass(frozen=True)`), registre
  `SUBSTRATS` (6 recettes EXACTES du §2), `get_substrat` (KeyError explicite),
  garde-fou `_valide_registre()` à l'import (tissus de pré-charge ∈ tissus connus
  du moteur). Exporté via `world/__init__.py`.
- `fields/ecofields/container.py` : `tick_hydrology` gagne `drainage_override=None`
  (rétrocompatible → tuiles bit-identiques ; le conteneur passera le drainage de
  son substrat en ②).
- `tests/test_substrat.py` — 17/17 OK (présence, valeurs, tissus valides,
  `get_substrat`, override change le drainage, override=DRAINAGE ≡ défaut).

⚠️ **À TRANCHER en ②** (signalé à Nico) : le tissu `substrat` (recette
`mycelium_use`) est dans `FAIM_N_TISSUS` mais **PAS dans `TISSU`** (ni
`TISSU_ORDER`). Injecter tel quel une parcelle `substrat` dans un mini-sol qui
ticke la décompo planterait (`KeyError TISSU["substrat"]`). ① ne fait que déclarer
la donnée ; ② devra donner une cinétique de décompo à `substrat` OU l'écarter du
balayage décompo (tout en gardant son effet faim d'azote). Garde-fou de ① accepte
`substrat` comme tissu CONNU, conformément au §2.

PROCHAIN : `02_conteneur.md` (mini-sol `EcoFields` + tick chimique isolé + boucle).
