# Sprint « Stabilisation perf en run éternel » — état vivant (carnet de bord)

> Carnet de conception (`/conception`). Phase A (challenge) EN COURS — rien n'est
> figé. Reprise à froid = lire `CLAUDE.md` + ce fichier.

## Sujet
La simulation du **monde complet 8 tuiles + maison + vie macro** ralentit énormément
au fil des années (turbo ~0,8 j/s à la 5e année) puis **plante**. Objectif : borner
le coût (CPU + mémoire) à horizon INFINI (philo #4 run éternel) sans trahir
l'émergence écologique (#1/#2/#7). Question annexe : réécrire le moteur en C/C++/C# ?

## Faits mesurés (Nico, profil inline borné)
- 8 tuiles : an1 s26 = 3088 ms/tick (360 plantes, 1254 segments) → an1 s52 = 6869 ms/tick
  (534 plantes, 2771 segments). Tick DOUBLE en ½ an, suit plantes (×1,5) et segments (×2,2).
- 2 tuiles / 6 ans : plantes 30→120, ms/tick 210→600 (suit les plantes) ; segments PAR
  plante plafonnés (~40, `_elaguer`). RSS tracemalloc croît linéairement 0,4→6,2 Mo,
  QUE Nico dit « indépendant des plantes/segments » → à PROUVER (tranche a).

## Diagnostic investigation (lecture seule, moi, 2026-07-05)
Trois moteurs, CONFIRMÉS/nuancés :

1. **Population NON bornée globalement** — CAUSE RACINE. Le verrou d'occupation a été
   DÉLIBÉRÉMENT LEVÉ au sprint « compétition intra-plot » (décision Q1/Q4) :
   `sim/succession.py:86-92` — un grain lève même sur plot occupé, la cohabitation est
   décidée par les champs réels, pas un terme d'occupation artificiel. Le recrutement
   féral n'est donc atténué QUE par `niche_index` (lumière-sol + densité racinaire) +
   `couverture_sol` (`succession.py:217`, couvert dense étouffe les adventices).
   Reproduction + ramets clonaux (ceux-ci DÉJÀ gatés couverture) ajoutent aussi.
   → Le frein émergent EXISTE des 2 côtés (recrutement: couverture ; mortalité:
   self-thinning par `shade_stress_damage`) mais il est TROP FAIBLE pour équilibrer :
   recrutement > mortalité → la population croît année après année.

2. **LightField super-linéaire** (`fields/light.py`, ~53 % CPU, D32). Deux boucles :
   - lumière REÇUE par plante (l.240-263) : pour chaque plante, parcourt les voisins
     PLUS HAUTS (tri décroissant + break) → **O(N²)** au pire (densité haute).
   - lumière-sol SCATTER (l.276-325) : coût ∝ plantes × bbox de capsule. Déjà élagué
     (D32 gather→scatter) mais toujours ∝ nombre × taille des plantes.
   → boucle de rétroaction avec (1) : plus de plantes → plus cher → et N grandit.

3. **Mémoire** — PAS de fuite « smoking gun » trouvée en lecture : `game_state["log"]`
   est purgé (`commands.py:156 gs["log"].clear()`), le journal des voix est FIFO borné
   (`sim/journal.py`, JOURNAL_MAX=200), la seedbank est bornée (plots × ≤27 espèces ×
   gènes). Les squelettes ligneux sont retirés à bois épuisé (`decompo.py:71`). La
   croissance RSS mesurée est donc plausiblement : (a) accumulation d'OBJETS plantes +
   squelettes ligneux qui traînent (chacun porte segments + genes + expression), (b)
   dicts seedbank par plot qui se remplissent jusqu'à ~27 espèces sur TOUS les plots,
   (c) overhead tracemalloc. « Indépendant des plantes » = HYPOTHÈSE À PROUVER par un
   profil mémoire PAR CATÉGORIE d'objets (tranche a). NE PAS affirmer avoir trouvé la
   fuite avant preuve.

## Question C/C++/C# — recommandation (à valider Nico)
**Rejeter la réécriture intégrale.** Le problème est ALGORITHMIQUE (N non borné +
O(N²) lumière), pas la vitesse du langage. Réécrire en C donnerait ~30-50× de constante
mais NE change PAS l'asymptote : un O(N²) sur N croissant explose en C aussi, juste plus
tard → on rachète quelques années d'éternel puis même mur. Or « run éternel » = horizon
infini → seul l'asymptote compte. Coûts d'une réécriture : jette « Python = source de
vérité » (invariant CLAUDE.md), casse Option B (Godot = vue), tue l'itération design
rapide, et devrait préserver le golden bit-à-bit (déterminisme flottant inter-langage =
très dur). → Ordre de ROI recommandé : (1) borner N + cache/LOD lumière EN PYTHON
(corrige l'asymptote, préserve tout) ; (2) SI une constante manque encore pour le 20×20,
vectoriser numpy la grille lumière ; (3) en dernier recours, noyau C/Cython pour la SEULE
fonction chaude `_point_in_capsule` (feuille), Python reste source de vérité. JAMAIS de
port intégral.

## Arbitrages TRANCHÉS (Nico, 2026-07-05)
- **A. Plafond population = ÉMERGENT + BACKSTOP.** Renforcer couverture→germination +
  self-thinning densité-dépendant jusqu'à l'équilibre recrutement=mortalité (#2/#7 OK),
  PLUS un cap dur PUR-perf placé très au-dessus du plateau, qui ne se déclenche jamais
  en jeu normal (filet anti-pathologie).
- **C. Périmètre = PYTHON PUR d'abord** (borner N + cache/LOD lumière). numpy et noyau
  Cython (`_point_in_capsule`) restent en RÉSERVE, activés SEULEMENT si les mesures
  post-optim l'exigent encore. PAS de port intégral, PAS de C# (rouvrirait D10).
- **Départ = PROFILEUR MÉMOIRE d'abord** (tronçon ①) : prouver la cause du crash avant
  tout code correctif.
- **B. Re-figeage golden** : ② lumière = BIT-IDENTIQUE (comme D32) → golden intact.
  ③ population = re-figeage MAÎTRISÉ possible (2 tuiles × 4 ans peut voir le self-thinning
  mordre) → annoncé par le kickoff, mesuré.

## Découpage FIGÉ (4 tronçons, perf-first, vue Godot en dernier)
- **① Profileur mémoire + colmatage** — `tools/profile_memoire.py` : tracemalloc PAR
  CATÉGORIE d'objets sur ~12 ans / 8 tuiles → NOMME ce qui croît linéairement. Si une
  catégorie croît INDÉPENDAMMENT de N (suspects : dict `species[r][c]` de la seedbank
  jamais purgé des espèces éteintes ; toute liste appendée par tick), la BORNER
  (cap/FIFO/prune) en préservant le golden. Diagnostic + colmatage ciblé. Golden INTACT.
- **② Spatial LOD LightField** — `fields/light.py` : spatial hash (bucket par plot) pour
  couper la boucle « lumière reçue » O(N²)→O(N·k) ; ne visiter que les capsules qui
  PEUVENT couvrir l'échantillon, dans le MÊME ordre hauteur-décroissante → produit
  flottant BIT-IDENTIQUE (golden intact, comme le gather→scatter D32). + cache géométrique
  réutilisable en temps figé. Golden INTACT (sinon = bug).
- **③ Capacité de charge émergente + backstop** — renforcer `couverture_sol`→germination
  (`succession.py`) + self-thinning densité-dépendant (voie `shade_stress_damage`/
  chronique) jusqu'à l'équilibre recrutement=mortalité ; + cap dur PUR-perf par tuile,
  très au-dessus du plateau. Re-figeage golden MAÎTRISÉ ANNONCÉ.
- **④ Vue Godot — banc d'observation perf** — compteur discret debug (ms/tick, N plantes,
  RSS) + banc F5 d'observation longue durée de la stabilisation. Golden INTACT.

## Leviers perf identifiés (à chiffrer finement en phase B)
- Spatial hash / partition des plantes → boucle lumière reçue O(N²)→O(N·k).
- Cache LightField : géométrie ne bouge qu'à la croissance (hebdo) ; réutilisable tel
  quel en temps figé (planification), recomputable à fréquence réduite en saison.
- Borner N (arbitrage A) → coupe l'asymptote à la racine.
- numpy vectorisation du scatter grille.
- Décimation macro (déjà pop-bornée, foragers n_max) — marge faible.

## Tronçon ① — RÉSULTAT (profileur mémoire, 2026-07-05)
Profileur FINALISÉ et EXÉCUTÉ (`tools/profile_memoire.py`, 128 LDC pur).
- **Modifs** : RSS mesuré via `resource.getrusage(RUSAGE_SELF).ru_maxrss` (au lieu de
  `tracemalloc`, overhead ~10× qui tuait le profil >240 s). Comptages par catégorie
  inchangés. Log purgé chaque tick (comme le serveur `commands.py:156`) → RSS reflète
  le jeu réel. Diagnostic durci : critère = **intensité PAR PLANTE (`catégorie/N`)** qui
  grimpe (immune au départ à 0), plus le ratio de facteurs cassé.
- **Échelle réellement exécutée : 8 tuiles × 4 ans** (1188 plots), 262 s. Suffisant pour
  voir la tendance (N ×2,4 sur la fenêtre).
- **VERDICT : AUCUNE fuite indépendante de N.** N_vivantes 534→1277 (×2,39), RSS 25→62 Mo
  **en lockstep avec N**. Intensité/plante PLATE ou DÉCROISSANTE pour TOUT :
  `sb_species/N` 0,125→0,104, `grilles`/`cellules_grille` **constants en absolu** (328
  grilles, 48708 cellules — jamais alloués par tick), `journal` = 0 (FIFO borné), `log`
  purgé. Le suspect nommé `SeedBank.species[r][c]` est **DÉJÀ purgé** par
  `tick_species_aging` (`fields/seedbank.py:294-297`, `del cell[cls]` si densité < 1e-4,
  appelé chaque semaine via `tick_seed_bank`) → self-bornant, réfuté par le code ET la
  mesure. `data[r][c]` = 4 archétypes/plot fixes.
- **COLMATAGE : AUCUN** (rien à borner — pas de fuite inerte). Le RSS SUIT N → **le
  tronçon ③ (borner N) résout aussi la mémoire**. C'est la population non bornée (M1), pas
  une fuite, qui fait planter le monde complet.
- **Golden INTACT** : `061934db09ad646a01f19b8f4d0b677f13438e87bce2f8531527be425e7c22a8`
  (outil lecture seule, aucun colmatage). Confirmé `python3 -m tests.test_golden` → PASS.

## Tronçon ② — RÉSULTAT (spatial LOD LightField + cache, 2026-07-05)
Deux leviers livrés, tous deux BIT-IDENTIQUES (golden intact) :
- **Spatial hash** de la boucle « lumière reçue par plante » (`fields/light_index.py`,
  NOUVEAU, `ObstacleIndex`, 31 LDC). Buckets de plots (pas PLOT_CM) indexant les
  obstacles par CENTRE de canopée + rang dans `order`. Pour chaque échantillon, on
  ne collecte que les candidats dont le centre est dans un carré de portée
  `max_height·inv_tan + max_radius` (sur-ensemble strict des couvrants), puis on les
  RE-TRIE par rang = ordre EXACT de `order` (hauteur décroissante, départages
  identiques) avant d'appliquer les facteurs `(1-qd)` → produit `att` bit-à-bit. Le
  `break qh<=ph` original devient un `continue` sur candidats triés = strictement
  équivalent. L'index n'élague que des obstacles qui renvoyaient déjà False (facteur
  1.0 neutre), comme D32 gather→scatter.
- **Cache géométrique** (`light.py`, `self._geom_key`) : empreinte PURE de l'état
  (saison, house, tile_origin, tuple (x,y,h,r,d) par obstacle — pas de `id()`, ordre
  déterministe de `infos`, squelettes secs inclus). Clé identique → `return []`
  immédiat, `self.data`/`self.received` réutilisés (temps figé). Croissance hebdo →
  MISS → recompute → golden neutre. HIT/MISS vérifiés à la main (HIT ne recalcule
  pas, plante déplacée → recompute).
- **Golden INTACT** : `061934db09ad646a01f19b8f4d0b677f13438e87bce2f8531527be425e7c22a8`
  (`python3 -m tests.test_golden` → PASS).
- **Gain mesuré** (`profile_tick 52 20`, 2 tuiles, 49 plantes, mesure ISOLÉE
  `LightField.compute`, moyenne 3 runs) : **~19,0 ms → ~8,2 ms** (−57 %), part du
  tick 29,5 % → 8,0 %. Le gain O(N²) mord surtout à haute densité (8 tuiles) non
  mesurée ici (profile_tick = 2 tuiles) ; à 2 tuiles/faible N le gain est DÉJÀ net
  (moins d'obstacles visités par échantillon). Le « tick complet » affiché varie
  (bruit machine), seule la mesure isolée est fiable.
- **Fichiers** : `fields/light.py` (222 LDC pur, norme verte ≤300) + NOUVEAU
  `fields/light_index.py` (31 LDC). Imports intacts. Pas de C#.
- **NON COMMITTÉ** (consigne : orchestrateur commit).

## Tronçon ③ — RÉSULTAT (capacité de charge émergente + backstop, 2026-07-05)
Population BORNÉE par deux freins écologiques resserrés + un disjoncteur perf. N(t)
PLAFONNE désormais au lieu de croître sans fin (cause racine M1 traitée → borne aussi
la mémoire, cf. ①).

- **Vis A — couverture→germination GRADUÉE** (`sim/succession.py`,
  `fields/ecofields/constants.py`). La réponse binaire est devenue continue : le
  facteur `(1 − couverture)**COUVERTURE_GERM_EXP` multiplie `niche` sous le seuil dur,
  fenêtre de germination férale qui se ferme d'autant plus vite que le tapis
  s'épaissit (philo #2 : flux couvert → contrainte fenêtre → réponse). **Réglages
  retenus : `COUVERTURE_GERM_EXP = 4.0` (succession.py) + `COUVERTURE_ADVENTICE_SEUIL`
  abaissé 0.6→0.5 (constants.py)**. Les grains PLANTÉS (geste joueur) ne sont pas
  concernés. Reproduction férale (`_reproduction`) grène dans la banque-sol → lève via
  `succession` → subit le MÊME frein ; ramets clonaux gardent leur gate couverture
  (`COUVERTURE_SATURATION=0.85`, `sim/clonal.py`).
- **Vis B — self-thinning** (`sim/effects/perturbations.py`, `shade_stress_damage`) :
  seuil abaissé **0.6→0.55** (souffrance un peu plus tôt). **Le taux reste 0.10** :
  BORNÉ PAR HAUT par l'invariant `test_stress_chronique` (un sciaphile doit SURVIVRE à
  l'ombre profonde) — toute hausse tue aussi le sciaphile (marge nulle mesurée). Les
  adventices férales sont sciaphiles (base 1.25) → la vis B mord peu sur elles ; **le
  gros du plafonnement vient de la vis A**.
- **Backstop PUR-perf** (`sim/capacite.py` NOUVEAU, 4 LDC pur) : `CAP_PERF_TUILE = 800`,
  `recrutement_bloque(tile)` gèle levée férale + grains + reproduction + ramets quand
  `len(alive) ≥ cap`, logge `⚠ cap perf tuile T atteint`. Importé par `succession`,
  `clonal`, `mortalite`. Disjoncteur : ~4-5× le plus grand plateau plausible, **ne fire
  JAMAIS** en jeu normal (vérifié : cap=30 forcé borne bien N, cap=800 jamais atteint au
  smoke).
- **PLATEAU observé** (échelle testée : 2 tuiles × 14 ans, `tools/profile_capacite.py`,
  sweeps via importlib) : trajectoire N `13 136 146 161 165 183 191 206 184 205 178 218
  192 204 201` → **stable band ~178-218 (moyenne ~197, ±10 %) à partir de l'an 6, SANS
  tendance haussière sur 8 ans** (an6=183 → an14=201, plat). Plateaux **par tuile
  différents** : NO ~105, N ~96 → **#7 préservé**. Baseline avant ③ : N grimpait sans
  borne (188→214→...→446 sur 3 tuiles). Comparatif exposant : exp=2 laissait N dériver
  vers le haut (271, croissant), exp=4 stabilise.
- **Golden RE-FIGÉ MAÎTRISÉ ANNONCÉ** : ancien
  `061934db09ad646a01f19b8f4d0b677f13438e87bce2f8531527be425e7c22a8` →
  **nouveau `84d359834f7b22d6a072e5c14def5c5326ecb9d4e7d3dafdb0a27d10caab5f54`**.
  Justification : *frein de recrutement resserré (vis A graduée seuil 0.5/exp 4) + onset
  self-thinning avancé (vis B seuil 0.55) → dérive LOCALISÉE (44→42 plantes vivantes au
  smoke, 2 germinations férales tardives supprimées), 0 NaN/inf, ordre déterministe
  intact, cap PUR-perf jamais firé*. Suites ciblées OK : `test_stress_chronique` (invariant
  sciaphile), competition, population, signes, planter, couplage, lifecycle, mycelium,
  vent, substrat, conteneur.
- **Fichiers** : `sim/succession.py` (+ import + exposant + frein gradué + guard cap),
  `fields/ecofields/constants.py` (seuil 0.5), `sim/effects/perturbations.py` (vis B),
  `sim/clonal.py` (+ guard cap), `sim/engine/mortalite.py` (+ guard cap), NOUVEAU
  `sim/capacite.py`, NOUVEAU `tools/profile_capacite.py` (harness calibrage per-tile).
  Pas de C#. **NON COMMITTÉ** (orchestrateur commit).
- **Digest satellite `test_population` re-figé (même cause, extension du re-figeage
  annoncé)** : le hash interne de `tests/test_population.py` (60 semaines, densités de
  vie macro pucerons/limaces/pollinisateurs/lombrics) dépend de la végétation présente ;
  ③ change la végétation (moins de levées férales, self-thinning avancé) → ce digest
  dérive pour la MÊME cause que le golden principal. Les 6 invariants STRUCTURELS de la
  suite passent (dormance, photopériode, bornes densité ∈[0,POP_MAX], cap sprites,
  stabilité des positions) → dérive localisée, pas un bug. `population_hash.txt` re-figé
  `5a1873db…` → `c2b4a01d…`, re-vérifié PASS. Reste de la suite (46 suites hors 500 ans) VERT.

## §REPRISE
Tronçons ①②③ CLOS (① pas de fuite indépendante de N ; ② spatial hash + cache
bit-identiques −57 % ; ③ **N BORNÉ = plateau émergent ~197/2 tuiles + backstop cap 800**,
golden re-figé maîtrisé `84d35983…`). **Prochain = tronçon ④** :
`sprints/sprint_perf_run_eternel/04_*.md` — vue Godot banc d'observation perf (compteur
debug ms/tick + N plantes + RSS, banc F5 longue durée de la stabilisation). Golden INTACT
attendu (④ ne touche pas le moteur). Golden actuel = smoke 2 tuiles × 2 ans, hash
`84d359834f7b22d6a072e5c14def5c5326ecb9d4e7d3dafdb0a27d10caab5f54` dans
`tests/golden_hash.txt`.
