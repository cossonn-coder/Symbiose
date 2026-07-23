# Sprint HYDROLOGIE DE RELIEF & MARÉCAGES — état de conception

> Carnet de bord VIVANT (skill `/conception`, §0bis). Reprise à froid : lire
> `CLAUDE.md` + CE fichier. Rien n'est FIGÉ tant que Nico n'a pas validé (phase B).

## Sujet (Nico, 2026-07-03, F5 post-D57)
1. L'eau s'écoule des plots HAUTS vers les BAS (ruissellement latéral).
2. Plot saturé → **FLAQUE** (eau stagnante de surface).
3. Flaque persistante → **MARÉCAGE** (état de milieu persistant).
4. Espèces marécageuses avec leurs **5 voix** : **AULNE**, **PLANTES
   CARNIVORES**, **MOUSSES** (sphaigne).

## Phase
**A — challenge (dialogue).** Rien de figé. 1er lot de 3 questions posé.

## Invariants du code VÉRIFIÉS (source de vérité `data/code/`)
- `humidite` = scalaire/plot ∈ **[0,3]**, 3 = saturation. `tick_hydrology`
  (`fields/ecofields/hydrologie.py`) : évap → pluie infiltrée ∝ structure →
  rétention (soil_memory + épaisseur D57) → **drainage VERTICAL par sol**
  (`DRAINAGE_PAR_SOL`). **AUCUN transfert LATÉRAL entre plots aujourd'hui.**
- `tick_hydrology` **retourne déjà** `pertes=[(r,c,perte)]` = eau qui s'écoule du
  fond de chaque plot — aujourd'hui JETÉE (sauf conteneurs fond ouvert). Point de
  greffe naturel du ruissellement.
- **Asphyxie DÉJÀ modélisée** (D39) : `HUM_EXCES=2.3` (uptake↓ réversible),
  `HUM_NOYE=2.6` (« noyé »), `asphyxie_memory` intégration lente 0.05/sem →
  santé au-delà de 0.10. → un plot gorgé longtemps BLESSE déjà les non-adaptés.
- **Gène `tolerance_asphyxie` EXISTE** (↔ `asphyxie_memory`) → réutilisable pour
  aulne/sphaigne, PAS de gène neuf à créer.
- **`epaisseur_sol`** (D57) = relief visible = Σ pondérée des `om_*` (humus).
  ⚠️ **PAS une altitude topographique** : un sol épais est riche en HUMUS, pas
  forcément « haut » au sens hydraulique. **Aucun champ `altitude`/topo n'existe.**
- Vie macro `fields/population/registry.py` = data-driven (`TrophicSpec` :
  `resource_fn`/`habitat_fn`/`predators`/fenêtre photopériode). 1 espèce = 1
  entrée. Détritivores humides (limace/cloporte) aiment déjà `rosee_humide_litiere`.
- Fixation N : archétype `nitrogen_fixer` (Medicago, Fabaceae) existe → patron
  pour l'aulne actinorhizien (Frankia). Catalogue pérennes = Figuier/Pommier/
  Cerisier/Noyer/Chêne (`plants/perennials.py`) — **aulne À CRÉER**.
- pH : `fields/ecofields/ph.py` existe (tourbière acide = couplage).
- Décompo : anaérobie ralentit la minéralisation → accumulation = TOURBE
  (couplage `matiere_organique.py` + mycélium saprophyte aérobie qui recule).

## Décisions ARRÊTÉES (lot 1, Nico 2026-07-03)
- **D1 — Écoulement sur un champ `altitude` déterministe NEUF** (micro-relief
  topographique par bruit spatial `noise.py`, FIXE, hétérogène par terrain, philo
  #3/#7). L'eau ruisselle dessus ; `epaisseur_sol` D57 s'ajoute en appoint (surface
  hydraulique = altitude + épaisseur). Évite la boucle instable humus↔eau.
- **D2 — Champ `eau_surface` NEUF** (lame d'eau, distincte de `humidite` des
  pores). Reçoit l'excédent de saturation, ruisselle vers les plots plus bas,
  s'infiltre si le sol peut boire, s'évapore. **Flaque = eau_surface > seuil**.
- **D3 — 3 espèces, mécanismes signature validés** (chacune un FLUX, pas un bonus) :
  - **Aulne** (Betulaceae NEUVE, pérenne) = fixe l'azote (actinorhizien Frankia,
    patron `nitrogen_fixer`) + `tolerance_asphyxie` élevé.
  - **Carnivore** = PRÉLÈVE réellement de la vie macro (D31) → 1er végétal
    prédateur ; le flux insectes→N l'affranchit de la faim d'azote (prospère sur
    tourbe acide pauvre).
  - **Sphaigne** (mousse, strate basse) = INGÉNIEUR : acidifie le pH + rétention
    d'eau énorme + nécromasse quasi-indécomposable → TOURBE (épaisseur↑, anaérobie).

## Décisions ARRÊTÉES (lot 2, Nico 2026-07-03)
- **D4 — Marécage = mémoire `marais_memory` + HYSTÉRÈSE** (entrée haute, sortie
  basse, pas de clignotement ; persistant philo #4). Intègre `eau_surface > seuil`.
  Effets quand marais : décompo `speed` ↓ (anaérobie, couple D40) → MO s'accumule =
  **tourbe** (épaisseur↑ émergent, pas de code neuf) ; pH ↓ (acidification) ; niche
  ouverte (humide+acide) pour les 3 espèces. Émergent, jamais scripté (#2/#6).
- **D5 — Faune de mare DÉDIÉE neuve** : guilde `moustique` (proie, prolifère sur
  `eau_surface`/marais) + `libellule` (auxiliaire, prédateur du moustique) →
  mini-chaîne aquatique. La **carnivore = PUITS** sur le champ `moustique` (sur ses
  `foliar_plots`) → flux insectes→azote, pas de faim d'azote. Couplage plante→faune
  INÉDIT (à spécifier au kickoff : plus délicat).
- **D6 — Gestes joueur `creuser` + `drainer`** (sur le milieu, philo #1, coûteux
  Vigueur). `creuser` abaisse `altitude` localement (cuvette → accumule l'eau) ;
  `drainer` évacue `eau_surface` + abaisse `marais_memory` (assèchement forcé).
  `altitude` devient donc modifiable par le JOUEUR (event-driven hors tick →
  golden neutre pour les gestes), sinon fixe déterministe.

## Phase B — FIGÉE le 2026-07-03 (GO Nico « vas-y »)
Doc de conception : `docs/champs/eau/conception_hydrologie_marecage.md`.
Kickoffs `01`→`08` écrits, autosuffisants. Prêt pour `/sprint-auto`.

## Carte des tronçons (8, perf-first)
| # | Kickoff | Cœur | Golden |
|---|---------|------|--------|
| ① | `01_altitude.md` | Champ `altitude` déterministe + expo snapshot | NEUTRE ✅ FAIT |
| ② | `02_eau_surface_ruissellement.md` | `eau_surface` + `tick_ruissellement` (double-buffer) | RE-FIGÉ LARGE ✅ FAIT (`284a3dc`) + test `284a3dc`… golden courant `eb46b49d…` |
| ③ | `03_marecage.md` | `marais_memory` + hystérèse + effets décompo/pH + banc `tourbiere` | NEUTRE ✅ FAIT (golden `eb46b49d…` INTACT, pont 0.5.27) |
| ④ | `04_faune_de_mare.md` | Moustique + libellule (data-driven) + 5 voix | pop NEUTRE/maîtrisé annoncé |
| ⑤ | `05_aulne_sphaigne.md` | Aulne (Betulaceae fixe-N) + Sphaigne (ingénieur) + voix | NEUTRE hors smoke |
| ⑥ | `06_carnivore.md` | Drosera + PUITS→`moustique` (1er végétal-prédateur) + voix | NEUTRE hors smoke |
| ⑦ | `07_gestes_creuser_drainer.md` | Gestes `creuser`/`drainer` (actions + pont) | NEUTRE (event-driven) ✅ FAIT (golden INTACT `57c166d8…`, pont **0.5.35**) |
| ⑧ | `08_vue_godot.md` | Vue : relief+altitude, flaque, marais, guilde, gestes | pur-vue, F5 |

**Ordre imposé** : ① avant ② (ruissellement lit altitude) ; ② avant ③ (marais lit
eau_surface) ; ④ avant ⑥ (carnivore-puits lit le champ moustique).

## Dettes croisées
D57 (relief/épaisseur = base du rendu ⑧), D40 (speed décompo sensible au milieu =
malus anaérobie ③), D39 (asphyxie — non-régression au ②), D31 (vie macro = patron
faune ④), D41 (faim d'azote — la carnivore y échappe ⑥), D55 (palette de gestes ⑦/⑧).

## Coût perf (estimé)
Ruissellement 4-voisins/plot/tick = O(plots×4) ≈ 6400 ops sur 1600 plots —
trivial vs LightField. ⚠️ déterminisme : balayer sur un DOUBLE BUFFER (snapshot
humidité) pour éviter le biais d'ordre de parcours (sinon direction privilégiée).

## Avancement ① (altitude) — FAIT le 2026-07-03
- Champ `altitude` (GridField, cm) déclaré dans `container.py` : init PLAT (0) en
  `__post_init__` (mini-sols conteneur = plats), posé HÉTÉROGÈNE dans `init_eco` sur
  le canal de hash `stable_str_hash(tile_id + "_alt")` (décorrélé de l'humus, philo
  #3/#7) = `ALT_BASE ± ALT_AMPLITUDE·(2·bruit−1)`, borné ≥ 0. FIXE (aucun tick).
- Constantes `ALT_BASE=20`, `ALT_AMPLITUDE=20` (dénivelé ~0–40 cm, placeholder) dans
  `constants.py`. Exposé au registre `get_field` (overlay F6, introspection auto) +
  au snapshot (bloc `altitude` par tuile, grille 2D dense cm). Pont bumpé **0.5.17**.
- Golden **INCHANGÉ** `a6c2f651…` (rien ne lit `altitude`). Suite pont 244/244 verte
  (3 asserts version recalés à 0.5.17 + check présence bloc `altitude` en conteneurs).
- Fichiers : `fields/ecofields/constants.py`, `fields/ecofields/container.py`,
  `tools/simserver/serialize.py`, `tools/simserver/version.py`,
  `tests/simserver/{structures,voix,conteneurs}.py`.
- **NON commit** (Nico commit). C# non touché (relief altitude = vue ⑧).

## Avancement ② (eau_surface + ruissellement) — FAIT
- **⚠️ ÉTAT RÉEL rattrapé le 2026-07-13.** Le cœur de ② était DÉJÀ implémenté et
  committé en `284a3dc` « feat(hydrologie) : ruissellement latéral + lame d'eau de
  surface (②) », lancé par un `/sprint-auto` antérieur — pas repéré ici car
  `00_etat.md` n'avait pas été mis à jour. Déjà en place et committé :
  - champ `eau_surface: GridField` (`container.py`, borné [0, HUM_CAP]) + registre
    `get_field` + init au repos NEUTRE ;
  - capture du surplus dans `tick_hydrology` (si `h > HUM_CAP` → `eau_surface +=
    h−HUM_CAP`, `h = HUM_CAP`) ;
  - mixin NEUF `fields/ecofields/ruissellement.py` (`RuissellementMixin.
    tick_ruissellement`) : double-buffer `src`/`dst`, redistribution multiple-flow
    ∝ pente von Neumann sur `S = altitude + epaisseur_sol`, exutoire aux bords,
    infiltration ∝ `structure_sol` bornée par `HUM_CAP − humidite`, évaporation de
    surface. Zéro RNG, déterministe (philo #3) ;
  - constantes `HUM_CAP=3.0`, `RUISSELLEMENT_FRACTION=0.5`, `INFILTRATION_SURFACE=
    0.15`, `EVAP_SURFACE=0.20`, `SEUIL_FLAQUE=0.10` (`constants.py`) ;
  - appel `eco.tick_ruissellement()` dans `boucle.py` (l.236) APRÈS `tick_hydrology`,
    AVANT `tick_decomposition` ;
  - bloc creux `eau_surface` (liste `[r,c,lame]`, filtré `> SEUIL_FLAQUE`) au
    snapshot (`serialize.py`) ; pont bumpé (ENGINE_VERSION `0.5.26` aujourd'hui).
  - **Golden RE-FIGÉ LARGE au moment de `284a3dc`** (l'eau circule → bilan hydrique
    par plot changé, cuvettes gorgées / bosses sèches). Depuis, plusieurs sprints
    ont fait évoluer le golden ; hash COURANT = `eb46b49d…` (PASSE).
- **CE SESSION (2026-07-13)** : SEUL livrable ② manquant = le test dédié. Ajouté
  `tests/test_ruissellement.py` (12 checks, PASS) — conservation de masse (cuvette
  fermée + sol saturé → seule l'évaporation ôte), déterminisme double-buffer
  (symétrie par transposition), cuvette à minimum INTÉRIEUR accumule / bosse
  s'assèche / flaque > SEUIL_FLAQUE, repos NEUTRE (lame nulle = no-op), infiltration
  (sol non saturé boit ∝ structure), anti-emballement 2000 ticks (lame bornée
  [0,HUM_CAP], aucun NaN/inf).
- **Golden INCHANGÉ ce session** `eb46b49d…` (ajout d'un fichier de TEST seul,
  aucune touche moteur). Pont 269/269 vert. C# non concerné (relief = vue ⑧).
- **Non-régression** : `test_senescence` **ÉCHOUE DÉJÀ sur HEAD `e7c015d`** (pommier
  meurt à 4.5 ans, cause « autre », pas sénescence ~59.8 ans) — vérifié par
  `git stash` : régression PRÉEXISTANTE, introduite par un sprint intercalaire,
  **INDÉPENDANTE de ②**. À investiguer hors de ce sprint (signaler à Nico).
  `test_epaisseur_500ans` NON lancé (interdit).
- **Fichiers touchés ce session** : `tests/test_ruissellement.py` (NEUF) +
  `sprints/champs/eau/sprint_hydrologie_marecage/00_etat.md`. Non commit (Nico commit).

## Avancement ③ (marécage : marais_memory + hystérèse + effets) — FAIT le 2026-07-13
- Champ STOCKÉ `marais_memory: GridField(max_val=1.0)` (init 0) + grille d'état
  `marais_etat` (bool) déclarés dans `container.py`, init au repos NEUTRE, exposés
  au registre `get_field` (overlay F6) — `marais_memory` seul (l'état bool n'est pas
  un GridField).
- Mixin NEUF `fields/ecofields/marais.py` (`MaraisMixin`, 20 LDC) : `tick_marais()`
  intègre `marais_memory += (cible − mem)·MARAIS_LERP` (cible=1 si `eau_surface >
  SEUIL_FLAQUE`, sinon 0) PUIS met à jour `marais_etat` par HYSTÉRÈSE (entrée
  MARAIS_ON=0.60, sortie MARAIS_OFF=0.30, zone morte = conserve l'état). Helper
  `est_marais(r,c)` lit l'état. Zéro RNG, no-op strict au repos.
- EFFETS émergents (facteur neutre à marais=0) : décompo `speed *= (1 −
  MARAIS_DECOMP_MALUS·marais_memory)` dans `tick_decomposition` ET `decomp_speed`
  (anaérobie → litière s'accumule → tourbe via `tick_epaisseur`, aucun code neuf) ;
  pH tiré vers `PH_TOURBE=4.5` ∝ `marais_memory` dans `ph.py` (interpolation bornée).
- Câblage boucle : `eco.tick_marais()` en 3c, APRÈS `tick_ruissellement`, AVANT
  `tick_decomposition`/`tick_ph` (qui lisent la mémoire du tick).
- Constantes (`constants.py`) : `MARAIS_LERP=0.05`, `MARAIS_ON=0.60`,
  `MARAIS_OFF=0.30`, `MARAIS_DECOMP_MALUS=0.6`, `PH_TOURBE=4.5`, `PH_MARAIS_LERP=1.0`
  (PLACEHOLDERS, calibrage F5).
- Snapshot : bloc CREUX `marais` par tuile `[[r,c,marais,etat],…]` (plots où
  `marais_memory > MARAIS_OFF`), inséré au dict de sortie. Pont bumpé **0.5.27**.
- Banc `tourbiere` (`bancs/hydrologie.py`) : cuvette gorgée (altitude basse, sol
  saturé, flaque, marais pré-installé) vs témoin sec → registre `BANCS`. Oracle
  `tests/bancs/test_hydrologie.py` (5/5 : marais persiste, décompo ralentie, pH
  acidifié vs témoin).
- **Golden INCHANGÉ** `eb46b49d…` (marais=0 au smoke ⇒ tous facteurs neutres). Test
  dédié `tests/test_marais.py` 13/13 (entrée/hystérèse/lenteur/repos neutre/décompo/
  pH). Pont **271/271** (3 asserts version recalés 0.5.26→0.5.27 + 2 checks présence
  bloc `marais` en conteneurs). Bancs climatique 20/20, succession 6/6.
- **Non-régression** : `test_senescence` reste ROUGE CONNU (pommier mort 4.5 ans,
  cause « autre » — préexistant, orthogonal). Banc édaphique 6/7 = FAIL `carence`
  (163.7 vs 147.5) PRÉEXISTANT (vérifié `git stash` : identique sans mes changements),
  indépendant de ③. `test_epaisseur_500ans` NON lancé (interdit).
- **Fichiers touchés** : `fields/ecofields/{constants.py, container.py,
  matiere_organique.py, ph.py}`, `fields/ecofields/marais.py` (NEUF), `sim/engine/
  boucle.py`, `bancs/{__init__.py, hydrologie.py (NEUF)}`, `tools/simserver/
  {serialize.py, version.py}`, `tests/{test_marais.py (NEUF), bancs/test_hydrologie.py
  (NEUF), simserver/{voix.py, structures.py, conteneurs.py}}`. NON commit (Nico commit).
- C# non touché (vue marais = ⑧).

## Avancement ④ (faune de mare : moustique + libellule) — FAIT le 2026-07-22
- **Deux espèces data-driven** ajoutées au registre `TrophicSpec` (`fields/
  population/registry.py`), en FIN de `build_population_specs()` :
  - `moustique` (proie, `category="aquatique"`, `salt=0x2B2001`) : `resource_fn=
    _eau_stagnante_grid` (lame `eau_surface` dominante + `marais_memory` plancher),
    `habitat_fn=_mare_habitat_grid`, `predators=("libellule",)`, fenêtre
    photopériode `11.0/13.5`.
  - `libellule` (auxiliaire, `salt=0x2B3001`) : `resource_fn=_espece_grid(
    "moustique")` (prédateur qui broute la densité moustique), même habitat de mare,
    `predators=()`, fenêtre `11.5/14.0`. Ordre de tick proie→prédateur déjà garanti
    par le registre (boom-bust décalé).
- **Grilles de ressource/habitat NEUVES** dans `fields/population/resources.py` :
  `_eau_stagnante_grid` (`MOUSTIQUE_SURFACE_W=1.0`·lame + `MOUSTIQUE_MARAIS_W=0.6`·
  marais, clampé [0,1], robuste au getattr → grille nulle si `eau_surface` absent) et
  `_mare_habitat_grid` (`MARE_HABITAT_W=0.8`·max(lame,marais)). Lecture PURE de `eco`
  par getattr (couche `population` ne dépend jamais de `ecofields`). Zéro RNG,
  positions sprites par hash de sel (philo #3).
- **5 voix** : encyclopédie (`fields/faune_encyclo.py` : blurbs + interconnexions
  `("libellule"/"moustique","eau","marais")`, symétrie du sous-graphe nommé
  préservée) ; carnet (concept `eau`/`marais` existant, pas de concept neuf) ;
  page secrète **P34** « Ne comble pas la flaque » (`sim/pages_corpus.py`, voix C,
  concept `eau`, robinet `hasard`) ; magazine (n/a faune, pas d'offre) ; événements
  (observabilité par le graphe d'interconnexions — PAS de marqueur de tick neuf, par
  cohérence avec campagnol/rapace, golden-sûr).
- **Golden écolo INCHANGÉ** `57c166d8…` (ni `eau_surface` ni `marais_memory` ≠ 0 au
  smoke ⇒ moustique/libellule densité 0.0 partout ⇒ rien n'entre dans le hash écolo).
- **Golden POPULATION RE-FIGÉ MAÎTRISÉ** (annoncé « pop NEUTRE/maîtrisé » au kickoff) :
  ancien `5824ee3f…` → nouveau `cc886bdd…` (`tests/population_hash.txt`). Cause =
  PUREMENT ADDITIVE : le digest privé des 2 nouvelles espèces == ancienne réf
  `5824ee3f…` (moustique/libellule = 0.0 partout au smoke, aucune flaque). Recapturé
  `python3 -m tests.test_population --capture`.
- **Tests ciblés VERTS** : `test_population` (dont 4 checks neufs : présence+catégorie
  faune de mare, moustique nul sans flaque, moustique monte avec `eau_surface`,
  libellule suit le moustique), `test_faune_dediee` (+ `FAUNE_MARE`, catégorie
  `aquatique`, token milieu `eau`/`marais`), `test_pages` (corpus 33→34, P01..P34),
  suite pont `simserver/macro.py` (GUILDES 18→20). Balayage complet : 41/42 verts,
  seul `test_sim_server` ROUGE (266/270).
- **`test_sim_server` ROUGE = PRÉEXISTANT** (dérive de chaîne `engine_version`
  0.5.28 attendu vs courant + test fruit pommier), vérifié `git stash` : orthogonal à
  ④. `test_encyclopedie` idem (gestes sans fiche, préexistant).
- **Fichiers touchés** : `fields/population/{resources.py, registry.py}`,
  `fields/faune_encyclo.py`, `sim/pages_corpus.py`, `tests/{test_population.py,
  test_faune_dediee.py, test_pages.py, simserver/macro.py, population_hash.txt}`.
  **NON commit** (Nico/orchestrateur commit). C# NON touché (vue faune = ⑧).
- ⚠️ **`resources.py` = 378 LDC pur** (bande vigilance 300–400, était déjà 349) —
  responsabilité unique conservée mais à SURVEILLER / candidate au `/refactor`.

## Avancement ⑤ (aulne + sphaigne + voix) — FAIT le 2026-07-22
- **AULNE** (`plants/perennials.py` `class Alder(PerennialWoody)`, catalogue
  `"aulne"`, PERENNIAL_CATALOGUE) : Betulaceae (famille DÉJÀ existante, portée à
  l'espèce par bouleau/charme — PAS recréée), anémophile (chatons), caduc, pionnier
  de berge. Deux signatures : (1) FIXATION N₂ actinorhizienne (Frankia) via
  `family_effects inject_field variable="n" amount=0.05 cible="local"` — MÊME route
  générique que l'azote ortie/minette (flux, pas bonus, philo #2), sur l'aulne SEUL
  (pas sur la classe Betulaceae → bouleau/charme ne fixent pas) ; (2) survie au sol
  gorgé via `asphyxie_tolerance_base=3.0` (cf. ci-dessous). Fenêtre pH tolérante
  (5.8/1.6), bouturable.
- **SPHAIGNE** (`plants/species/sauvages.py` `class Sphagnum(Sphagnaceae)`, catalogue
  `"sphaigne"`, PLANT_CATALOGUE) : famille NEUVE `Sphagnaceae` (INERTE au repos,
  patron Ericaceae) ajoutée à `familles.py` + exportée (`base/__init__.py`,
  `species/__init__.py`). INGÉNIEUR : 3 flux `inject_field cible="local"` :
  (a) acidification `ph` −0.03/sem — S'ACCUMULE contre la dérive lente (PH_INERTIA
  0.02), BORNÉE au plancher PH_MIN=4.0 du GridField = LE MÊME clamp que l'acidif.
  marais §3 → aucun double-comptage (les deux poussées se plafonnent ENSEMBLE à
  PH_MIN, ne s'additionnent pas sous le plancher — c'est la « bornée ensemble » du
  kickoff) ; (b) rétention `humidite` +0.05/sem (bornée [0,3]) ; (c) nécromasse-tourbe
  via `litter_tissue="mousse"` (tissu NEUF `TISSU["mousse"]=(0.008,0.60,0.05)`, decay
  le plus bas du catalogue < bois → tourbe émergente par `tick_epaisseur`, aucun code
  neuf). Acidophile stricte (ph_opt 4.2), `asphyxie_tolerance_base=4.0`.
- **NOUVEL attribut d'espèce `asphyxie_tolerance_base`** (PlantBase, défaut 1.0) :
  tolérance CONSTITUTIVE à l'hypoxie, DISTINCTE du gène per-instance
  `tolerance_asphyxie` (pas de gène neuf, cf. invariants) — les deux se MULTIPLIENT
  au dénominateur de la pression asphyxie (`mortalite.py`). Branche ARMÉE seulement si
  `asphyxie_memory > seuil` (sol durablement gorgé, JAMAIS dans le smoke) → golden
  inchangé. Nouvel attribut `litter_tissue` (défaut None) routé dans `tissu_mort`
  (`perturbations.py`).
- **5 VOIX** : encyclopédie (2 fiches 3 niveaux `aulne`/`sphaigne`,
  `encyclopedie_corpus.py`, count 43→45) ; carnet AUTO (concepts existants `eau`
  [asphyxie] + fixation via champ `n` — pas de concept neuf, `CONCEPT_DE` inchangé) ;
  page secrète **P35** « La mousse qui garde tout » (`pages_corpus.py`, voix C, concept
  `eau`, robinet `fouille` — tourbe/conservation) ; magazine AUTO (data-driven par
  famille depuis le catalogue → aulne/sphaigne offerts au palier 3 Betulaceae/
  Sphagnaceae, aucun code) ; événements = installation/tapis observables au graphe
  (cohérent avec ④, pas de marqueur de tick neuf, golden-sûr).
- **Golden écolo INCHANGÉ** `57c166d8…` (aulne/sphaigne absents du smoke ⇒ aucun flux,
  aucune parcelle `mousse`, branche asphyxie inerte). Golden POPULATION inchangé
  `cc886bdd…`.
- **Tests ciblés VERTS** : `test_pages` 62/62 (P35), `test_encyclopedie` alignement +
  count 45 verts (2 FAIL `geste` arracher/glaner/pincer = PRÉEXISTANTS, vérifiés
  `git stash`), `test_population`/`test_faune_dediee` verts, `test_marais`/
  `test_ruissellement`/`test_senescence` verts, suite `simserver.{voix,macro,
  structures,conteneurs}` verte. `test_sim_server` 266/270 = échecs BIT-IDENTIQUES
  avant/après (`diff` sur `git stash`) → 100 % préexistants (dérive version + fruit),
  aucun introduit par ⑤. `test_epaisseur_500ans` NON lancé (interdit).
- **Taille** (LDC pur, `tools/compte_ldc.py`) : sauvages.py 294, familles.py 263,
  perennials.py 246 — TOUS ≤300 🟢.
- **Fichiers touchés** : `plants/base/{familles.py, __init__.py}`,
  `plants/{perennials.py, catalogue.py}`, `plants/species/{sauvages.py, __init__.py}`,
  `fields/ecofields/constants.py` (tissu `mousse`), `sim/engine/mortalite.py`
  (médiation asphyxie ×base), `sim/effects/perturbations.py` (`tissu_mort` override),
  `sim/encyclopedie_corpus.py` (2 fiches), `sim/pages_corpus.py` (P35),
  `tests/{test_encyclopedie.py (count 45), test_pages.py (count 35)}`.
  **NON commit** (orchestrateur commit). C# NON touché (vue guilde = ⑧).

## Avancement ⑥ (drosera carnivore : puits → moustique) — FAIT le 2026-07-22
- **DROSERA** (`plants/species/sauvages.py` `class Drosera(Droseraceae)`, catalogue
  `"drosera"`, PLANT_CATALOGUE) : 1ᵉʳ végétal-prédateur. Famille NEUVE `Droseraceae`
  (INERTE au repos, `family_effects=[]`, patron Sphagnaceae) ajoutée à `familles.py`
  + exportée (`base/__init__.py`, `species/__init__.py`). Acidophile stricte (ph_opt
  4.2, comme la sphaigne), `asphyxie_tolerance_base=3.0`, rosette `tapis` strate sol,
  petite fleur entomophile faible. `archetype=None` (hors WEED_CATALOGUE).
- **Attribut d'espèce NEUF `carnivore: bool = False`** (PlantBase, `familles.py`),
  littéral seul (aucun import → règle de couches). Arme DEUX mécaniques :
- **(1) PUITS → `moustique`** : mixin NEUF `sim/engine/carnivore.py` (`CarnivoreMixin`,
  25 LDC), constante LOCALE `CARNIVORE_CAPTURE=0.20`. `_tick_carnivore` : pour chaque
  Drosera vivante, retire `CARNIVORE_CAPTURE × densité` de `moustique` sur ses
  `foliar_plots` (borné ≥ 0 par le clamp de PopulationField, zéro RNG). Câblé en
  **13b-ter** dans `boucle.py`, JUSTE APRÈS `tick_populations` (moustique du tick à
  jour) — hook DISTINCT du registre faune→faune (kickoff). No-op strict sans champ
  `moustique`. Émet 🪰 UNE fois par plante (drapeau transient `a_capture`, hors
  `_PLANT_ATTRS` → golden NEUTRE) = 1ʳᵉ capture au ledger des voix.
- **(2) FAIM D'AZOTE NEUTRALISÉE** : dans `sim/vigueur_plante.qi_local` (LECTURE,
  read-only), une espèce `carnivore` retire N de la loi de Liebig → le minimum ne
  porte que sur P/K (son azote vient des proies, pas du sol). Elle SURVIT sur tourbe
  pauvre en N là où une herbacée carence, SANS pousser plus vite (P/K restent
  limitants, philo #1). Aucun dépôt d'azote au sol (N interne → ne profite pas aux
  voisines). Défaut `carnivore=False` → minimum N/P/K inchangé (golden NEUTRE).
- **Vérif fonctionnelle** (banc jetable) : puits ⇒ moustique baisse sur les plots
  foliaires + log une seule fois ; N-escape ⇒ sur sol N=0.001/P=K=0.5, `qi_local`
  drosera=0.167 (survit) vs ortie=0.0 (carence).
- **5 VOIX** : encyclopédie (fiche 3 niveaux `drosera`, `encyclopedie_corpus.py`,
  count 45→46) ; carnet (concept NEUF `carnivorie` : `CONCEPT_DE[("carnivorie",None)]`
  + gabarits descriptif/interprétatif) ; événements (parseur `evenements.py` : regex
  `_RE_CAPTURE` sur 🪰 → `Evenement("carnivorie",…,espece="drosera")`) ; page secrète
  **P36** « Le rossolis qui chasse » (`pages_corpus.py`, voix E sorcières, concept
  `carnivorie`, robinet `fouille`) ; magazine AUTO (data-driven par famille → drosera
  offerte au palier 3 Droseraceae, aucun code).
- **Golden écolo INCHANGÉ** `57c166d8…` (aucune Drosera au smoke ⇒ hook inerte, puits
  jamais armé, branche N-escape jamais prise, `a_capture` hors digest). Golden
  POPULATION INCHANGÉ `cc886bdd…`.
- **Tests ciblés VERTS** : `test_golden` (hash identique), `test_population` (hash
  `cc886bdd…` identique + 3 checks faune de mare), `test_pages` 63/63 (P36),
  `test_carnet` 19/19, `test_evenements` 20/20, `test_maitrise_detection` 20/20 (le
  `_evenements` historique intact), `test_faune_dediee` vert, `test_encyclopedie`
  count 46 + alignement OK (2 FAIL `geste` arracher/glaner/pincer = PRÉEXISTANTS,
  vérifiés `git stash`). `test_sim_server` 266/270 = échecs BIT-IDENTIQUES avant/après
  (`git stash`) → 100 % préexistants (dérive version + fruit). `test_epaisseur_500ans`
  NON lancé (interdit).
- **Taille** (LDC pur, `tools/compte_ldc.py`) : carnivore.py 25 🟢, vigueur_plante.py
  41 🟢, evenements.py 140 🟢, carnet.py 156 🟢, familles.py 269 🟢. ⚠️ **sauvages.py
  = 338 LDC** (bande vigilance 300–400) — responsabilité unique conservée (spontanées
  sauvages), mais à SURVEILLER / candidate au `/refactor`.
- **Fichiers touchés** : `plants/base/{familles.py, __init__.py, instance.py
  (a_capture)}`, `plants/{catalogue.py}`, `plants/species/{sauvages.py, __init__.py}`,
  `sim/engine/{carnivore.py (NEUF), boucle.py}`, `sim/vigueur_plante.py`,
  `sim/evenements.py`, `sim/carnet.py`, `sim/{encyclopedie_corpus.py, pages_corpus.py}`,
  `tests/{test_encyclopedie.py (count 46), test_pages.py (count 36)}`.
  **NON commit** (orchestrateur commit). C# NON touché (vue guilde/carnivore = ⑧).

## Avancement ⑧ (vue Godot : relief/altitude, flaque, marais, guilde, gestes) — FAIT le 2026-07-23
- **PUR-VUE C#, golden Python NEUTRE** `57c166d8…` (seul du C# touché + 1 ligne
  d'export pont ADDITIVE). `dotnet build Symbiose.csproj` VERT (0 err, 0 warn).
- **Relief + altitude** (`world/WorldView.Relief.cs`) : `surface = altitude +
  epaisseur_sol` (même empilement que la surface hydraulique du moteur → les creux
  d'altitude coïncident avec les flaques). Parseur de grille dense FACTORISÉ
  (`ParseDenseGrid`, partagé altitude/épaisseur), `EpaisseurPxAt` somme les deux
  termes, accesseur public `ReliefRiseAtPlot` pour les calques de sol. `ApplyAltitude`
  lit `altitude` AVANT `ApplyEpaisseur` (qui déclenche `UpdateRelief`). Tolérant.
- **Calque `visuals/PuddleLayer.cs` (NEUF)** : flaque (bloc `eau_surface`, lame
  bleutée ∝ profondeur + liseré miroitement) + voile marais (bloc `marais`, tourbe
  brun-noir ∝ `marais_memory`), recalés sur la surface extrudée via `ReliefRiseAtPlot`.
  UN CanvasItem redessine tout en `_Draw` (patron CouvertureLayer/LitterLayer), LOD
  ≥0.5, culling, inerte entre snapshots, ZIndex 2. Câblé `WorldView.cs` (création +
  `Init(this)`) + `WorldView.Snapshot.cs` (`SetWater`, lecture tolérante).
- **Pont** : `eau_surface_by_tile` CALCULÉ mais jamais émis (le ② l'avait cru exposé)
  → ajouté au dict de sortie (`serialize.py`, 1 ligne ADDITIVE). Pont 266/270 = 4
  échecs BIT-IDENTIQUES préexistants (dérive version + fruits pommier), aucun introduit.
- **Faune de mare** (`visuals/MacroLife.cs`) : moustique (nuée fine gris-brun rapide)
  + libellule (bleu-vert iridescent, vol stationnaire lent).
- **Placeholders guilde** (`visuals/PlantRenderer.Organs.cs`) : palettes aulne
  (berge, strobiles bruns) / sphaigne (tapis vert-jaune) / drosera (rosette, glu ROUGE).
- **Gestes creuser/drainer** : verbes kind `'q'` (plot {tile,r,c}, ACK diagnostic,
  `world/WorldView.Actions.cs`) + icônes `k`/`j` (`world/GesteIcon.cs`).
- **Overlays F6** (`visuals/FieldOverlay.cs`) : palettes DÉDIÉES `eau_surface`
  (bleu d'eau [0,3]) + `marais_memory` (brun tourbe [0,1]) + moustique/libellule
  (calées MacroLife, patron « une palette/espèce » ⑥b). `altitude` déjà présente.
- **Fichiers touchés** : `world/{WorldView.cs, WorldView.Relief.cs, WorldView.Snapshot.cs,
  WorldView.Actions.cs, GesteIcon.cs}`, `visuals/{PuddleLayer.cs (NEUF), MacroLife.cs,
  PlantRenderer.Organs.cs, FieldOverlay.cs}`, `data/code/tools/simserver/serialize.py`.
- **F5 Nico** : micro-relief lisible (cuvettes/bosses) ? flaques qui brillent dans les
  creux ? marais qui « noircit » ? guilde crédible ? gestes lisibles ? Calibrage
  exagération relief + palettes.

## §REPRISE
**SPRINT CLOS le 2026-07-23** — les 8 tronçons ①→⑧ sont FAITS et committés. Reste
UNIQUEMENT le **F5 de Nico** (voir §Avancement ⑧). **① CLOS** (altitude). **② CLOS**
(eau_surface + ruissellement). **③ CLOS** (marécage). **④ CLOS** (faune de mare). **⑤ CLOS**
(aulne + sphaigne). **⑥ CLOS** (Drosera Droseraceae : PUITS `_tick_carnivore` →
`moustique` sur foliar_plots + faim d'azote neutralisée dans `qi_local` [N hors
Liebig] ; attribut `carnivore` + drapeau `a_capture` ; 5 voix dont concept NEUF
`carnivorie` + P36 ; golden écolo INTACT `57c166d8…`, population INTACT `cc886bdd…`).
**⑦ CLOS** (2026-07-23) : gestes `creuser` (abaisse `altitude` d'un cran
`CREUSER_DELTA=15 cm` → cuvette qui capte l'eau au ruissellement ② + `microbiome`
perturbé comme `becher`) / `drainer` (vide `eau_surface` + `marais_memory *=
1−DRAINER_ASSECHE=0.40` → assèchement forcé, la mémoire repasse sous `MARAIS_OFF`
au tick ③). Event-driven, tout-ou-rien gaté sur la Vigueur, `GESTES_BASE`
(rustiques, amorçables 1ᵉ avatar). Pont `action` routé (verbes `creuser`/`drainer`
au plot {tile,r,c}, message diagnostic avant/après), **ENGINE_VERSION 0.5.35**.
Golden écolo INTACT `57c166d8…`, population INTACT `cc886bdd…`, pont 266/270
(4 échecs = assertions version figées 0.5.28 + pommier floraison, PRÉEXISTANTS).
**PROCHAIN = ⑧** (`08_vue_godot.md`, DERNIER) — pur-vue C# F5 : relief/altitude,
flaque, marais, guilde de mare (aulne/sphaigne/drosera/moustique/libellule),
gestes creuser/drainer cliquables.
**⚠️ Bugs préexistants NON traités ici** : `test_sim_server` (dérive version) +
`test_senescence` + `test_encyclopedie` (gestes sans fiche) + banc édaphique `carence`
— tous orthogonaux à l'hydrologie, à trancher avec Nico hors sprint.
Tout re-figeage NON annoncé par un kickoff = bug (`/sprint-auto` refuse).

## §REPRISE_ANCIENNE (②)
**① CLOS** (altitude). **② CLOS** — cœur déjà committé en `284a3dc` (`eau_surface` +
`tick_ruissellement` double-buffer lisant `altitude`+`epaisseur_sol`, capture du
surplus, boucle, snapshot, pont), golden RE-FIGÉ LARGE au moment du commit puis
évolué à `eb46b49d…` ; test dédié `tests/test_ruissellement.py` ajouté ce session
(12/12 PASS). **PROCHAIN = ③** (`03_marecage.md`) — `marais_memory` + hystérèse +
effets décompo/pH, lit `eau_surface > SEUIL_FLAQUE`. ③→⑦ visent NEUTRE, ⑧ pur-vue.
**⚠️ AVANT ③ : élucider l'échec préexistant de `test_senescence` (pommier mort à
4.5 ans) — non causé par ce sprint, mais à trancher avec Nico.** Tout re-figeage NON
annoncé par un kickoff = bug (`/sprint-auto` refuse).
