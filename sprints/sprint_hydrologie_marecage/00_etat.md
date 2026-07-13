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
Doc de conception : `docs/conception/CONCEPTION_HYDROLOGIE_MARECAGE.md`.
Kickoffs `01`→`08` écrits, autosuffisants. Prêt pour `/sprint-auto`.

## Carte des tronçons (8, perf-first)
| # | Kickoff | Cœur | Golden |
|---|---------|------|--------|
| ① | `01_altitude.md` | Champ `altitude` déterministe + expo snapshot | NEUTRE ✅ FAIT |
| ② | `02_eau_surface_ruissellement.md` | `eau_surface` + `tick_ruissellement` (double-buffer) | RE-FIGÉ LARGE ✅ FAIT (`284a3dc`) + test `284a3dc`… golden courant `eb46b49d…` |
| ③ | `03_marecage.md` | `marais_memory` + hystérèse + effets décompo/pH + banc `tourbiere` | NEUTRE hors banc |
| ④ | `04_faune_de_mare.md` | Moustique + libellule (data-driven) + 5 voix | pop NEUTRE/maîtrisé annoncé |
| ⑤ | `05_aulne_sphaigne.md` | Aulne (Betulaceae fixe-N) + Sphaigne (ingénieur) + voix | NEUTRE hors smoke |
| ⑥ | `06_carnivore.md` | Drosera + PUITS→`moustique` (1er végétal-prédateur) + voix | NEUTRE hors smoke |
| ⑦ | `07_gestes_creuser_drainer.md` | Gestes `creuser`/`drainer` (actions + pont) | NEUTRE (event-driven) |
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
  `sprints/sprint_hydrologie_marecage/00_etat.md`. Non commit (Nico commit).

## §REPRISE
**① CLOS** (altitude). **② CLOS** — cœur déjà committé en `284a3dc` (`eau_surface` +
`tick_ruissellement` double-buffer lisant `altitude`+`epaisseur_sol`, capture du
surplus, boucle, snapshot, pont), golden RE-FIGÉ LARGE au moment du commit puis
évolué à `eb46b49d…` ; test dédié `tests/test_ruissellement.py` ajouté ce session
(12/12 PASS). **PROCHAIN = ③** (`03_marecage.md`) — `marais_memory` + hystérèse +
effets décompo/pH, lit `eau_surface > SEUIL_FLAQUE`. ③→⑦ visent NEUTRE, ⑧ pur-vue.
**⚠️ AVANT ③ : élucider l'échec préexistant de `test_senescence` (pommier mort à
4.5 ans) — non causé par ce sprint, mais à trancher avec Nico.** Tout re-figeage NON
annoncé par un kickoff = bug (`/sprint-auto` refuse).
