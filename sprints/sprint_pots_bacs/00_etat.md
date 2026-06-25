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
| ③ | Plante en pot + confinement racinaire hybride (effet nain) | `03_confinement.md` | **FAIT** (golden bit-identique) |
| ④ | Mobilité + bacs N×M immobiles + pont snapshot | `04_mobilite_bacs.md` | **FAIT** (golden bit-identique, pont 0.5.7) |
| ⑤ | Couplage fond ouvert + lasagnes (arc complet) | `05_couplage_lasagnes.md` | **FAIT** (golden bit-identique) — **sprint moteur CLOS** |
| ⑥a | Vue Godot — rendu statique conteneur + substrat (lecture seule) | `06a_rendu_conteneur.md` | **FAIT** (build C# vert, golden NEUTRE inchangé) |
| ⑥b | Vue Godot — interaction poser/déplacer/planter (outil + clic) | `06b_interaction.md` | kickoff écrit |
| ⑥c | Vue Godot — indices visuels du couplage (fond ouvert, nain, substrat) | `06c_indices_couplage.md` | kickoff écrit |

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

## Tronçon ③ — état
**FAIT** (golden bit-identique). Effet nain HYBRIDE livré, philo #2 respectée
(émergent, AUCUN malus direct sur la plante). Acquis :
- `world/container.py` (+74 LDC → 152 LDC pur, < 350 ; tool `tools/compte_ldc.py`) :
  - knobs §3 : `VOLUME_REF=75`, `VOLUME_CONF_MAX=12`, `ROOTBOUND_SEUIL=0.30`,
    `ROOTBOUND_K=1.20`, `CONF_MIN=0.25` + helper `_clamp`.
  - `Container.tick(saison, seed, week, *, house, nebulosite)` = `tick_chimie` PUIS
    uptake + croissance des plantes du conteneur (no-op si `plants==[]` → rétrocompat ②).
  - `_volume_factor()` (levier 1 = `1/volume_norm` clampé [1, VOLUME_CONF_MAX]),
    `_confinement(plant)` (levier 3 = root-bound, proxy `current_height`/volume),
    `_cellules()` (levier 2 = géométrie du mini-sol).
  - `planter_dans(container, plant_class, *, cell=(0,0))` → ajoute une `PlantInstance`
    au centre de la cellule, retournée.
- `world/container.py` imports : `+ from plants.base import PlantInstance`,
  `+ from sim.growth import grow_plant` — **PAS de cycle** (`sim.growth` n'importe ni
  `world` ni `sim.effects` ; vérifié `import world` OK).
- `fields/ecofields/container.py::plant_uptake` → param `volume_factor: float = 1.0`
  (replié dans `share`). **Défaut 1.0 = bit-identique** (prouvé : non-régression test).
- `sim/growth/phases.py::grow_plant` → param `confinement: float = 1.0` (multiplie
  `speed`). **Défaut 1.0 = croissance historique inchangée**.
- `sim/engine/boucle.py` étape 17b → `ctn.tick(saison, seed, week, …)` (au lieu de
  `tick_chimie`) ; liste vide par défaut → no-op → golden NEUTRE.
- `world/__init__.py` → ré-exporte `planter_dans`.
- `tests/test_confinement.py` (NOUVEAU) — 6/6 OK : gradient nain monotone
  (5L=19.2 < 75L=51.8 ≤ 200L=61.1 cm), levier 1 (petit pot sec+carencé plus vite),
  levier 2 (root_plots borné à la cellule), levier 3 (root-bound seuil/CONF_MIN),
  non-régression `volume_factor=1.0` bit-identique, déterminisme h1==h2.

## Golden re-vérifié après ③ (bit-identique)
- smoke : `2ab026ad2b3f484777a2a29f804e1a4785ecffd6976fc0058fe0a33dd1498646` ✅
- population : `6056713d4dd1e2a79964411961909545433f8513a530a2b39151cbe6aabe471b` ✅
- test_confinement 6/6 ✅ · test_conteneur 7/7 ✅ · test_substrat 17/17 ✅ ·
  test_eau 20/20 ✅ · test_croissance 67/67 ✅ · test_vigueur 136/136 ✅ ·
  test_sim_server 185/186 (baseline inchangée, « pommier pré-âgé » préexiste).

## DÉCISION TRANCHÉE en ④ — collision de noms `poser_bac`
Le geste `poser_bac` EXISTE DÉJÀ (sim/actions/compost.py, décompo ⑤) = poser un
**bac à COMPOST** (structure de tuile). Le kickoff ④ demandait `poser_pot`/`poser_bac`
pour les **conteneurs de CULTURE**. Pour ne RIEN casser :
- façades Python : `poser_pot`, **`poser_bac`** (dans le NOUVEAU `sim/actions/conteneurs.py`),
  `deplacer_pot`. Ré-exportées par `sim/actions/__init__.py` ; le bac de culture sous
  l'alias **`poser_bac_culture`** pour ne pas écraser `compost.poser_bac` dans `ACT.*`.
- verbes du pont : `poser_pot`, **`poser_bac_culture`**, `deplacer_pot`,
  `planter_conteneur` (≠ `poser_bac` qui reste le bac à compost).
- clés `COUTS`/`OBJETS_TOUCHES` : `poser_pot`, `poser_bac_culture`, `deplacer_pot`
  (MODÉRÉ, concept `jardinage_hors_sol` → atténuation neutre 1.0).

## DÉCISION TRANCHÉE en ④ — version de protocole 0.5.7 (≠ 0.5.4 du kickoff)
Le kickoff disait « 0.5.3 → 0.5.4 ». Le sprint a AVANCÉ depuis : `ENGINE_VERSION`
était à **0.5.6** (0.5.4 = bancs d'essai, 0.5.5/0.5.6 = rendu feuillage). On
incrémente donc à **0.5.7** (prochaine libre). Le test `engine_version` (simserver/
structures.py) est mis à jour 0.5.6 → 0.5.7.

## Tronçon ④ — état
**FAIT** (golden bit-identique, pont 0.5.7). Mobilité + bacs N×M + snapshot conteneurs.
Acquis :
- `sim/actions/conteneurs.py` (NOUVEAU, 40 LDC) — façades joueur `poser_pot` /
  `poser_bac` (bac de culture, N×M, immobile, `fond_ouvert` stocké pour ⑤) /
  `deplacer_pot`. Toutes binaires (coût payé → effet). `deplacer_pot` : refus EN
  AMONT si `not mobile` (AUCUNE Vigueur), sinon met à jour `x_cm,y_cm` SEULEMENT
  (philo #2 : zéro écriture plante → lumière recalculée au prochain `tick_chimie`).
  Liste monde via `game_state.setdefault("containers", [])`.
- `sim/actions/couts.py` — 3 clés (`poser_pot`/`poser_bac_culture`/`deplacer_pot`,
  MODÉRÉ) + `OBJETS_TOUCHES` (concept `jardinage_hors_sol`, neutre 1.0).
- `sim/actions/__init__.py` — ré-exporte `poser_pot`, `poser_bac_culture`
  (alias de `conteneurs.poser_bac`), `deplacer_pot`. **PAS de cycle** (sim.actions
  importe `world`, qui importait déjà `sim.growth` ; vérifié `import sim.actions` OK
  et `compost.poser_bac` préservé).
- `tools/simserver/serialize.py` — bloc `containers` au snapshot (méthode
  `_containers_snapshot`) : id/kind/substrat/volume/mobile/fond_ouvert/rows/cols +
  position monde + `plants` (forme compacte) + `eco_summary` (scalaires plot 0,0).
  PURE lecture, liste VIDE au smoke → golden NEUTRE.
- `tools/simserver/conteneurs_route.py` (NOUVEAU, 76 LDC) — routage des 4 verbes
  conteneurs (extrait de actions.py pour le garder < 350 : actions.py = 328 LDC).
  Validation bornes (substrat/volume/position/index/espèce) → refus SANS coût.
  `planter_conteneur` place DIRECTEMENT (pas de succession en pot) via `planter_dans`,
  consomme la banque-joueur (symétrie `planter` tuile).
- `tools/simserver/actions.py` — délègue à `route_conteneur`.
- `tools/simserver/version.py` — `ENGINE_VERSION = "0.5.7"` + note de schéma.
- `tests/test_mobilite.py` (NOUVEAU) — 7/7 : poser_pot débite Vigueur, bac immobile
  N×M, deplacer_pot recalcule la lumière (soleil 1.0 → ombre maison 0.617), philo #2
  (Vigueur joueur débitée + état plante IDENTIQUE avant/après), bac refuse (0 Vigueur),
  Vigueur insuffisante (pot non déplacé), déterminisme.
- `tests/simserver/conteneurs.py` (NOUVEAU, section 17) — 20 checks : snapshot
  `containers` vide à l'init, pose pot/bac (Vigueur + snapshot), refus substrat/volume/
  index/espèce sans coût, deplacer_pot (position au snapshot), bac refuse, serveur
  survivant. Câblé dans `tests/test_sim_server.py`.

## Golden re-vérifié après ④ (bit-identique)
- smoke : `2ab026ad2b3f484777a2a29f804e1a4785ecffd6976fc0058fe0a33dd1498646` ✅
- population : `6056713d4dd1e2a79964411961909545433f8513a530a2b39151cbe6aabe471b` ✅
- test_mobilite 7/7 ✅ · test_confinement 6/6 ✅ · test_conteneur 7/7 ✅ ·
  test_substrat 17/17 ✅ · test_vigueur 136/136 ✅ · test_croissance 67/67 ✅ ·
  test_sim_server **205/206** (baseline +20 checks conteneurs verts ; le SEUL rouge
  reste « pommier pré-âgé », préexistant, sans rapport). C# **non concerné** (aucun
  fichier C# touché : vue différée ⑥, le bloc `containers` est optionnel côté vue).

## Tronçon ⑤ — état
**FAIT** (golden bit-identique). Couplage fond ouvert + arc lasagnes complet, philo #2
respectée (tout passe par un FLUX de matière, aucun bonus direct sur la plante).
Acquis :
- `fields/ecofields/container.py::tick_hydrology` → **RETOURNE** désormais les pertes
  de drainage par cellule `[(r, c, h·(1−drainage)), …]` (au lieu de les jeter). Aucun
  appelant existant ne lit ce retour → **strictement rétrocompatible, golden NEUTRE**.
  Approche recommandée par le kickoff (« retour propre, ne pas dupliquer la boucle
  hydrologique »).
- `world/container.py` (+ ~90 LDC) — couplage conteneur↔tuile d'assise (§5) :
  - nouveaux champs `tile_eco`/`tile_rc` (l'`EcoFields` + le plot `(r,c)` sous le
    conteneur), renseignés à la pose ; `None` → conteneur DÉTACHÉ (hors-sol pur),
    aucun pont → golden NEUTRE, rétrocompat ②/③/④.
  - **point 1 drainage→tuile** (`_drainer_vers_tuile`) : l'eau du fond est INJECTÉE
    dans l'humidité du plot de tuile (bilan d'eau conservé). Vaut pour POT et BAC.
  - **point 2 racines→tuile** (dans `tick`) : quand le bac `fond_ouvert` est root-bound
    (`_confinement < 1.0`), les racines DESCENDENT → uptake AUSSI sur `tile_eco` au plot
    d'assise (`volume_factor=1.0`, sol profond non confiné) → l'effet nain est LEVÉ
    (confinement forcé à 1.0). Émergent : on ouvre un réservoir, on n'efface aucun malus.
  - **point 3 microbiome/om→tuile** (`_diffuser_vers_tuile`, bac `fond_ouvert` SEUL) :
    diffusion LENTE BIDIRECTIONNELLE (`COUPLAGE_DIFFUSION=0.04`) microbiome/om_active/
    om_stable entre cellule d'assise et tuile, masse conservée. Pot fond fermé : pas
    de diffusion (seul le drainage point 1 s'écoule).
- `make_container` mémorise `tile_eco`/`tile_rc` (assise §5) ; `terre_jardin` les exige
  toujours (héritage §6), OPTIONNELS sinon (assise de couplage ou conteneur détaché).
- `tests/test_couplage.py` (NOUVEAU) — 8/8 : drainage→tuile (humidité plot monte),
  conteneur détaché (no-op), racines→tuile (couplé 40 cm > confiné 12.9 cm = nain levé),
  microbiome bac↔tuile (diffusion bidirectionnelle), pot fond fermé (drainage OUI,
  microbiome inchangé), lasagnes (ΣNPK 1.30→pic 1.75 libération > pauvre 0.27, bois
  consommé), déterminisme, retour `tick_hydrology` sans effet sur les tuiles (bit-id).
- Pont : `fond_ouvert` était DÉJÀ exposé au snapshot depuis ④ → rien à toucher, protocole
  reste **0.5.7** (kickoff : « exposer si utile, sinon laisser à ⑥ » — déjà fait).

## Golden re-vérifié après ⑤ (bit-identique)
- smoke : `2ab026ad2b3f484777a2a29f804e1a4785ecffd6976fc0058fe0a33dd1498646` ✅
- population : `6056713d4dd1e2a79964411961909545433f8513a530a2b39151cbe6aabe471b` ✅
- test_couplage 8/8 ✅. C# **non concerné** (aucun fichier C# touché).

## REPRISE (démarrage à froid) — SPRINT MOTEUR CLOS
Tronçons ① → ⑤ **TOUS FAITS** (golden NEUTRE bit-identique sur tout le sprint, pont
0.5.7). Le moteur Python sait : composer un conteneur (pot mobile / bac N×M immobile)
avec un substrat data-driven (6 recettes), tiquer sa chimie isolée, rapetisser la
plante en petit volume (effet nain hybride émergent), déplacer un pot (Vigueur joueur
seule), exposer les conteneurs au pont, et COUPLER un bac fond ouvert à la tuile dessous
(drainage + racines qui lèvent le nain + diffusion microbiome). Arc lasagnes validé.

**RESTE** : la **vue Godot ⑥** (Option B — rendre pots/bacs/substrats visibles
côté C#), découpée en **3 sous-tronçons** (kickoffs écrits le 2026-06-25) :
⑥a rendu statique → ⑥b interaction → ⑥c indices du couplage. Aucun re-figeage
golden sur tout le sprint moteur. **La vue ne touche AUCUN fichier Python** (tout
est déjà exposé au pont 0.5.7) → golden **trivialement NEUTRE** sur ⑥ ; le filet
est `dotnet build Symbiose.csproj`, le **F5 visuel reste à Nico**.

**Reprise vue (démarrage à froid)** : lancer `06a_rendu_conteneur.md`. Tout est
prêt côté moteur — le snapshot `containers` (0.5.7) et les 4 verbes du pont
(`poser_pot`/`poser_bac_culture`/`deplacer_pot`/`planter_conteneur`) existent
depuis ④. Pattern de rendu à réutiliser : `visuals/CompostStructure.cs` +
`world/WorldView.Compost.cs` (placeholder iso procédural, un Node2D par objet en
couche YSort `_objects`, reconstruction pleine à chaque snapshot).

## Tronçon ⑥a — état
**FAIT** (vue Godot, AUCUN fichier Python touché → golden trivialement NEUTRE,
inchangé `2ab026ad…`). Build `dotnet build Symbiose.csproj` **vert** (0 erreur).
Acquis (C#, lecture seule du bloc `containers` du snapshot 0.5.7) :
- `visuals/ContainerStructure.cs` (NOUVEAU) — placeholder procédural iso, calqué
  sur `CompostStructure.cs`. **POT** = tronc-cône évasé (base étroite → lèvre large,
  hauteur ∝ √(volume/75 L), empreinte 1 plot) ; **BAC** = caisse N×M (un caisson
  par cellule du mini-sol, faces avant + dessus, tri loin→proche au sein du nœud).
  **SUBSTRAT** = teinte de la SURFACE (dessus du conteneur), `Dictionary` 6 recettes
  → couleur (terreau/compost/drainant/lasagnes/terre_jardin via `Palette16.SolTerre`/
  mycelium_use), repli neutre `Palette16.SolInconnu` si clé inconnue. Empreintes en
  OFFSET (`WorldToScreenOffset`) → cohérent sous les 4 orientations ; hauteur en Z
  vertical. Knobs `const` (calibrage post-F5).
- `world/WorldView.Conteneurs.cs` (NOUVEAU partial) — câblage lecture, calqué sur
  `WorldView.Compost.cs`. Liste `_containers` (index `target.container` ⑥b + position
  MONDE pour le picking ⑥b + nœuds). `ApplyContainers(GArray)` : reconstruction pleine
  (QueueFree anciens conteneurs + plantes, recrée), un `ContainerStructure` par conteneur
  positionné à `WorldToScreen(x_cm, y_cm)` (MONDE absolu, **pas** d'origine de tuile)
  dans `_objects` (YSort). `BuildContainerPlants` : un `PlantRenderer` par plante du
  mini-sol (même chemin que les plantes du monde, `StructureLoader.FromSnapshot` lit le
  format compact), ancré au centre du conteneur + offset cellule (local `c·50+25` −
  demi-grille, en `WorldToScreenOffset`). Squelette si `dead` (mode "seche", le snapshot
  conteneur n'expose pas `stade_mort`), symptômes foliaires si présents. Lecture TOLÉRANTE
  (snapshot sans `containers` → rien dessiné).
- `world/WorldView.Snapshot.cs` — dispatch `ApplyContainers(snap["containers"])` à côté
  de `ApplyStructures` (lecture tolérante `ContainsKey`).
- `world/WorldView.Camera.cs::RebuildWorld` — `_containers.Clear()` à la rotation
  (nœuds libérés avec `_objects`, `ApplyContainers` recrée — comme `_structs`).

Tailles : `ContainerStructure.cs` 186 l. / `WorldView.Conteneurs.cs` 126 l. (brut,
majorité de commentaires pédagogiques) — bien < 350 LDC pur.

## REPRISE (démarrage à froid) — ⑥a FAIT, RESTE ⑥b/⑥c
Moteur ①→⑤ CLOS (golden NEUTRE `2ab026ad…`, pont 0.5.7). Vue ⑥a FAITE : pots/bacs +
substrat + plantes se DESSINENT en lecture seule (placeholder iso, à VALIDER F5). RESTE :
**⑥b interaction** (poser/déplacer/planter via `TryAction`, outil + clic ; les 4 verbes
du pont existent : `poser_pot`/`poser_bac_culture`/`deplacer_pot`/`planter_conteneur` ;
`_containers` porte déjà index + position MONDE pour le picking) puis **⑥c indices du
couplage** (fond ouvert/nain/substrat, lit `eco_summary` du snapshot, étiquettes). Lancer
`06b_interaction.md`. La vue ne touche AUCUN fichier Python → golden trivialement NEUTRE.

## Points à VALIDER au F5 (Nico) — ⑥a
- Forme/échelle du POT (tronc-cône) et du BAC (caisse N×M) : knobs `const` de
  `ContainerStructure.cs` (`PotHalfCm`, `PotHeightRefCm`, `BacCellHalfCm`, `BacWallCm`)
  → calibrer si « trop gros/petit/plat ».
- Teintes de substrat (6 recettes) lisibles d'un coup d'œil les unes des autres ?
- Plante en pot bien CENTRÉE sur le conteneur, occultation YSort correcte avec maison/
  plantes du sol, et cohérente sous les 4 orientations (touche de rotation D35).
- Conteneur posé via ⑥b à venir (aucun conteneur dans la carte de démo) : le F5 ⑥a se
  fait donc en posant un pot à la main une fois ⑥b livré, OU en injectant un conteneur
  de test. À signaler : **⑥a n'est observable qu'avec un conteneur présent dans le
  snapshot** (la carte de démo n'en pose aucun → écran identique au repos).

## Décisions ⑥ tranchées (AskUserQuestion, Nico, 2026-06-25)
1. **Rendu** = placeholder procédural pixel-art (pas de PNG sur la VM, cohérent
   SS²/D34) ; substrat = teinte de la surface (`Palette16`). (sprites dédiés écartés)
2. **Interaction** = outil + clic, homogène avec tous les gestes via `TryAction`
   (`world/WorldView.Actions.cs`) ; substrat choisi par cycle à la pose.
   (drag&drop reporté à un sprint ultérieur)
3. **Découpe** = 3 sous-tronçons ⑥a/⑥b/⑥c (chacun F5-able seul, `/clear` entre
   chaque). (kickoff unique écarté)
