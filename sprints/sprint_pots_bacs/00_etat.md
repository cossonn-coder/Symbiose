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
| ② | Conteneur `EcoFields` miniature + tick chimique isolé + boucle | `02_conteneur.md` | **FAIT** (golden bit-identique) |
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

## DÉCISION TRANCHÉE en ② — cinétique du tissu `substrat`
Le tissu `substrat` (recette `mycelium_use`) était dans `FAIM_N_TISSUS` mais ABSENT
de `TISSU`/`TISSU_ORDER` → un mini-sol qui ticke la décompo aurait planté
(`ValueError TISSU_ORDER.index` + `KeyError TISSU["substrat"]`).

**Choix : on lui DONNE une cinétique de décompo** (option « décompose », pas
« écarté »). Justification — le §2 dit explicitement « faim d'azote initiale forte
**PUIS libération** » : pour se libérer, `substrat` DOIT se minéraliser, donc il lui
faut une cinétique. L'écarter du balayage l'aurait laissé inerte → faim d'azote
éternelle, en contradiction avec le §2.

Implémentation (3 ajouts dans `fields/ecofields/constants.py`) :
- `TISSU["substrat"] = (0.04, 0.45, 0.20)` — C-riche pré-digéré : décompo LENTE
  (entre bois 0.02 et herbacé 0.15), déjà bien humifiée.
- `TISSU_ORDER` += `"substrat"` **EN FIN** (après `bois`) — n'apparaît que dans les
  mini-sols de conteneur, jamais sur une tuile → ordre des tissus tuile inchangé.
- `NPK_RELEASE["substrat"] = {N:0.20,P:0.25,K:0.25}` — pauvre (somme 0.70, capte
  peu, cohérent avec la faim d'azote).
**Golden NEUTRE garanti** : aucune parcelle `substrat` n'existe dans le smoke (seul
un conteneur `mycelium_use` en pose, et le smoke n'en pose aucun) → hash inchangé.

## Tronçon ② — état
**FAIT** (golden bit-identique). Acquis :
- `world/container.py` (NOUVEAU, 83 LDC) — `@dataclass Container` (champs §1 +
  méthode `tick_chimie`), fabrique `make_container(kind, substrat, volume, x, y, *,
  rows, cols, tile_eco, tile_rc, container_id)`, helpers `_appliquer_recette`
  (remplit struct/ph/npk/micro + dépose `litiere_precharge`) et `_heriter_tuile`
  (copie PROFONDE du plot tuile pour `terre_jardin`, isolation des `Parcelle`).
  `tick_chimie` = ordre boucle ALLÉGÉ (lumière à la position+ombre maison →
  thermique → hydrologie `drainage_override=recette.drainage` → décompo → structures
  no-op → pH(0) → structure → diffusion → soil_memory). PAS d'uptake/plante (③).
- `world/__init__.py` — ré-exporte `Container, make_container`.
- `sim/engine/boucle.py` — étape 17b « tick conteneurs » : itère
  `game_state.get("containers", [])` (DÉFAUT `[]` → no-op strict → golden NEUTRE),
  après la boucle tuiles, avant Vigueur/snapshot ; passe `house` + `nebul` du tick.
- `tests/test_conteneur.py` — 7/7 OK (init recette, bac immobile N×M, lasagnes se
  décompose [om_fresh↓, om_active↑, NPK libéré au pic], mycelium faim d'azote levée,
  terre_jardin copie profonde, drainage drainant<terreau, déterminisme h1==h2).

Couches VÉRIFIÉES : `world→fields` OK, `grep` confirme zéro `import world` dans
`fields/` → pas de cycle.

## Golden re-vérifié après ② (bit-identique)
- smoke : `2ab026ad2b3f484777a2a29f804e1a4785ecffd6976fc0058fe0a33dd1498646` ✅
- population : `6056713d4dd1e2a79964411961909545433f8513a530a2b39151cbe6aabe471b` ✅
- test_substrat 17/17 ✅ · test_structures 65/65 ✅ · test_fruits 24/24 ✅ ·
  test_eau 20/20 ✅ · test_signes 8/8 ✅ · test_sim_server 185/186 (baseline
  inchangée, le check rouge « pommier pré-âgé » préexiste, sans rapport).

## REPRISE (démarrage à froid)
Tronçons ① + ② **FAITS** (golden bit-identique). Le conteneur existe (`world/
container.py`), sa chimie isolée ticke, la boucle l'itère (liste vide par défaut).
Le tissu `substrat` a sa cinétique de décompo (voir décision ci-dessus).

PROCHAIN : `03_confinement.md` (plante en pot + confinement racinaire hybride =
effet nain : `volume_factor` sur uptake + plafond racinaire + signal root-bound).
