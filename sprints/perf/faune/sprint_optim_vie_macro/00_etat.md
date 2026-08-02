# sprint_optim_vie_macro — 00_etat (carnet de bord conception, D100)

**Phase courante** : CLOSE côté sprint (2026-08-01) — la MESURE a tué D100 comme sprint → D100 déclassée
en dette d'opportunité, `at_plot`→D103. Reste 1 question ouverte à Nico (taille-cible jardin) avant tout D32.
**Origine** : dette D100 (`perf/faune`). Rapport curator `~/skills-lab/2026-07-29_204602_curator_golden.md`.
**Verdict curator** : `tick_populations` = **24,8 % du tick** (1er poste), impact d'ablation **faible** (2,03).
Étiquette « **ambiance chère** » → **garder le rendu ressenti, dégraisser le coût**. Ne PAS couper la faune.

## Diagnostic code (vérifié 2026-08-01)

- **20 champs de population** tickés/tick (15 trophiques `build_population_specs` + 5 pollinisateurs
  `build_pollinator_specs`). Chaque `PopulationField.tick` (`fields/population/field.py`) :
  `resource_fn` → grille `rows×cols` ; `habitat_fn` → grille ; parfois `signal_fn` → grille ;
  puis double boucle `r×c` de relaxation avec `sum(predators.at_plot)`.
- **Recomputation redondante intra-tick MASSIVE** (viole `feedback_pas_de_recalcul_tick`),
  STRUCTURELLE (indépendante du scénario) :
  - `_litter_grid` recalculé **×4** (limace res+hab, cloporte res+hab) — scan `eco.litiere`.
  - `_undisturbed_grid` **×4** (lombric, campagnol, carabe, couleuvre).
  - `_pollinisateur_habitat_grid` (grille UNIFORME) matérialisée **×4** (papillon/bourdon/abeille/osmie).
  - `_make_nectar_grid` : **5 scans de plantes** (1 par pollinisateur) pour la même floraison.
  - `_foliage_grid` ×2-3, `_espece_grid("puceron"/"limace")` ×2, `_mare_habitat_grid` ×2.
- **Aucune infra de mémoïsation par tick** aujourd'hui (à créer).
- **Piège mémoïsation** : `_avec_abri_paillage` MUTE la grille de base en place (`g[r][c]=…`) →
  un cache renvoyant la grille de base serait empoisonné dès qu'il y a du paillage. Copy-on-write requis.

## Leviers identifiés (tous visés BIT-IDENTIQUES → golden INCHANGÉ = « même rendu » au sens fort)

1. **Mémoïsation intra-tick** des grilles partagées (litter/undisturbed/foliage/espece) + copy-on-write. **Scénario-robuste** (redondance structurelle).
2. **Consolidation des scans de plantes** : 1 passage plantes → accumulateurs (foliage/root/famille/floraison) réutilisés par toutes les guildes. **Scénario-robuste**, gros levier en monde dense.
3. **Grilles uniformes** en scalaire (éviter `[[val]*cols]*rows` ×4). Bit-identique.
4. **Relaxation clairsemée** (skip plots où pop=0 ET capacité=0 → new=0=pop, skip exact) + accès direct `.data[r][c]`. **Scénario-BIAISÉ** (flatté par le golden clairsemé → à valider sur banc dense AVANT dimensionnement).

## Décisions arrêtées (Nico, 2026-08-01)
- **D1 — bit-identique ABANDONNÉ comme exigence** (je l'avais imposé à tort). Réimplémentation
  profonde de la vie macro AUTORISÉE, y compris changement réel de comportement du jardin.
  → les 3 options d'approximation sont rouvertes de plein droit, plus « en dernier recours ».
- **D2 — cible visuelle = 1 individu par type d'animal présent dans la tuile** (pas la population
  entière). MAIS **chantier SÉPARÉ** du coût de tick : *la calculatrice ≠ le peintre*. Alléger le
  dessin (sprites/pont) ne retire pas 1 point aux 25 % du tick. Deux chantiers, deux gains, deux mesures.
- **D3 — tronçon ① = MESURE PURE**, critère d'acceptation EN NÉGATIF : produit (a)+(b)+(c)+(d)
  ci-dessous ET RIEN D'AUTRE. Aucune optim, aucun cache, aucun refactor. Interdiction de modifier
  `vie_macro.py` (si je m'y surprends → stop).
- **D4 — toute décision de design vient APRÈS le point 2** (les mesures), jamais avant.

## Tronçon ① — livrables (mesure pure)
- **(a) Part réelle sur banc DENSE** : `tick_populations` %tick sur `bancs/luxuriance.py`, comparé aux
  24,8 % du golden clairsemé. Enjeu : LightField O(N²) (D32) monte avec la densité → si la part
  s'effondre, D100 n'est plus le 1er poste et le sprint est mal dimensionné.
- **(b) Inventaire COMPLET des lecteurs** des champs de population, TROUVÉ PAR COMMANDE (pas de
  mémoire) : pour chaque lecteur, la ligne de code + la nature de l'usage (**continu / seuil /
  présence**). C'est cette liste seule qui dit jusqu'où « 37 limaces » → « il y a des limaces » sans
  casser l'écologie. (déjà cités à confirmer : herbivorie, `pollinator_reach`, Vigueur macro.)
- **(c) Compte d'appels RÉEL** sur un tick réel (cProfile ncalls) : confirmer/infirmer le tableau
  ×4/×5 (lu, pas exécuté). C'est lui qui dit où est l'argent, même si on réimplémente.
- **(d) Indicateurs de « ressenti » du jardin + enveloppe de dérive** — remplaçant du filet
  « ça bouge = bug » perdu avec D1. Mesurés sur l'état ACTUEL, enveloppe écrite À L'AVANCE (pas
  ajustée après coup), proposés en fin de tronçon → **Nico valide**.

## Corrections Nico (2026-08-01, 2e passe) — décisions arrêtées
- **D5 — (a) est une PENTE, pas une invariance** : 24,1 %→20,5 % à 2,6× densité/plot (23→40 plantes,
  seulement 1,7× en absolu). Mon « reste 1er poste même dense » = **extrapolation 2 points** (mode
  de défaillance catalogué). À corriger par une VRAIE courbe densité→part. **Enjeu caché** : si le
  jardin-cible est un potager MÛR, le sprint c'est **D32 (light O(N²))**, pas D100. → QUESTION À NICO :
  à quelle échelle de jardin le joueur passe-t-il le plus de temps ? (peut ANNULER ce sprint).
- **D6 — Q1 = figer chantier A SEUL** (dégraissage champ, sortie inchangée, golden = filet). Le
  chantier B (peintre, D2) NE se scope PAS avant sa mesure (coût du chemin sprite/pont + ce qu'il
  resterait à 1 individu/type/tuile). Une mesure, pas une estimation.
- **D7 — enveloppe sans plancher de bruit = vide.** Prérequis qui décide tout : la sim est-elle
  DÉTERMINISTE à graine fixe ? (à montrer PAR COMMANDE : 2 runs, diff). Si oui → ±X est un vrai
  critère. Si non → n≥3 runs de référence + enveloppe adossée à la dispersion observée. Tolérances
  fixées APRÈS, UNE fois, écrites avant tout code, jamais réajustées au vu des résultats.
- **D8 — prochain tronçon mesure** (critère négatif) : produit **coût peintre + 8 valeurs de
  référence + réponse déterminisme oui/non**, RIEN d'autre. Toujours 0 ligne dans `vie_macro.py`.

## Tronçon ① — RÉSULTATS (mesurés 2026-08-01, cProfile 52 ticks warm 40)
- **(a) Part sur banc dense** : golden `tick_populations` **24,1 %** (confirme curator), light 10,3 %.
  Luxuriance (dense, 64 plots/40 plantes) `tick_populations` **20,5 %**, light 11,1 %. → **NE s'effondre
  PAS** : reste le 1er poste même dense À CETTE ÉCHELLE. NUANCE : luxuriance = petite tuile ;
  `tick_light` O(N²) (D32) explose avec le NOMBRE ABSOLU de plantes → sur un jardin mûr (200+ plantes)
  light dépasserait populations. D100 est bien dimensionné au stade potager, D32 devient le gros
  poisson à maturité.
- **(c) Compte d'appels RÉEL confirme le tableau** (par tuile/tick) : `_litter_grid` **×4**,
  `_undisturbed_grid` **×4**, `_pollinisateur_habitat_grid` (UNIFORME) **×4**, `_foliage_grid` **×3**,
  scan nectar `_make_nectar_grid` **×5** (closure la + lourde en self), `_avec_abri_paillage`/`_espece_grid`
  **×6**, **42 `_zero_grid`/tuile/tick** (churn d'alloc). **`at_plot` = ~6 % du tick ENTIER**
  (406 ms/6747, method overhead) → accès direct `.data` = gros gain scénario-robuste.
- **(b) Inventaire des lecteurs (par commande) + NATURE** :
  - **CONTINU (l'écologie a besoin de la densité au plot)** : herbivorie `perturbations.py:417`
    (dégât ∝ densité, floor 0.005), bascule létale aux `:453`, root_herbivory_memory `croissance.py:382`
    (lerp), pollinisation `reproduction.py:72,85` (portée ∝ sat densité), vigueur macro
    `vigueur_macro.py:82`, drosera `carnivore.py:47` (capture ∝ dens), agents butineurs `butineurs.py:117`.
  - **SEUIL** : annélation létale `perturbations.py:506` (`dens ≥ LETHAL` → mort binaire) ;
    signes visuels `semiologie.py:134,149` (`_ramp(FLOOR,1)` : invisible sous floor puis continu).
  - **ÉCRITURE au quantum sprite** : gestes `gestes.py:416,533,558` (écraser/bioturbation ±0.06).
  - **PEINTRE (déjà coarse)** : pont `serialize.py:314`→`sample_sprites` (quanta 0.06, cap 4/plot,
    cap monde 5000). ← C'est ICI que vit la cible D2 « 1 individu/type/tuile », **séparé** du champ.
  - **VERDICT (b)** : « 37 limaces → il y a des limaces » **casserait l'écologie** si appliqué AU CHAMP
    (les lecteurs éco sont continus ∝ densité). Le coarsening est LÉGITIME côté PEINTRE seulement.
    → le champ reste continu ; le gain sur les 25 % vient de tuer la REDONDANCE + `at_plot`, pas de
    dégrader la densité.
- **(d) Indicateurs « ressenti » + enveloppe** : proposés ci-dessous (à valider Nico avant tout code).

## Tronçon mesure 2 — RÉSULTATS (2026-08-01)
- **(1) DÉTERMINISME = OUI, prouvé par commande** : 2 runs golden × 40 ticks → signature IDENTIQUE
  (`945070d8b6f054f8`). Conséquence : toute dérive vient du CHANGEMENT, pas du bruit → ±X est un vrai
  critère, et le chantier A bit-identique a le GOLDEN pour filet parfait (0 % de dérive).
- **(2) COURBE densité→part (1 tuile 12×12, mesurée, 6 points)** :
  | plantes | pop% | light% |  15→**33,0**/5,7 · 32→24,7/10,2 · 58→19,1/14,5 · 91→**13,6**/17,2 · 117→10,3/**18,6** |
  → **CROISEMENT vers ~70 plantes** : `tick_populations` domine seulement au stade potager clairsemé ;
  `tick_light` (D32) le dépasse dès qu'un jardin mûrit. L'ancien « reste 1er poste même dense » est
  RÉFUTÉ (c'était une pente). **Décide la priorité D100 vs D32 selon l'échelle-cible du jardin.**
- **(3) COÛT PEINTRE (snapshot sprites, par snapshot ≠ par tick)** : golden 2,0 ms = **4,6 %** d'un
  tick (175 sprites) ; dense-100 4,1 ms = **3,3 %** (386 sprites). MODESTE en CPU. Mais cible D2
  (1 individu/type/tuile présent) ≈ **5-12 sprites** vs 175-386 → **×15-30 en moins** : gain surtout
  VISUEL + taille de snapshot transféré à Godot, peu de CPU.
- **CONSÉQUENCE sur (d)** : le peintre est READ-ONLY en aval du champ → D2 ne touche PAS l'écologie
  (les lecteurs éco lisent le CHAMP, pas les sprites). Donc l'enveloppe de B = **indicateurs VISUELS
  seuls** (présence/rythme/grappe par guilde) ; les 4 indicateurs éco restent à 0 (champ inchangé).
  Seule une coarse-grid du CHAMP mordrait sur l'éco — et la courbe (2) suggère qu'à l'échelle où
  D100 compte, le bit-identique suffit probablement.

## Tronçon mesure 3 — COÛT ABSOLU + cadence (2026-08-01) — CONVERGENCE
- **Courbe en MS ABSOLUS (correction Nico : le % était un piège)** : `pop_ms` va de **43,7 à 51,2 ms**
  sur 15→117 plantes (tuile 144 plots) = **+17 %, PAS « plat »** — majoritairement ∝ plots, avec une
  composante ∝ plantes (scans nectar/feuillage) d'environ +17 % sur la plage. En **ms/plot** : ~0,30-0,34
  quel que soit le scénario (golden 30,9 ms/96 plots = 0,32 ; dense 48,4/144 = 0,34). ⚠️ le point
  « golden » est sur 96 plots, les autres sur 144 → comparer en ms/plot, pas en ms brut (une variable
  a changé). `light_ms` 7,7→**91,5** (×12, O(N²) plantes). `reste_ms` 81→**355** (uptake/croissance/décompo ∝ plantes).
  → **Optimiser populations rapporte un ms CONSTANT à toute densité** ; le gain NE rétrécit PAS à
  maturité. Mon « croisement → D100 mal dimensionné » est RÉFUTÉ (artefact de part).
- **Cadence snapshot = 1:1** (`cmd_step_week` = 1 tick + 1 `_snapshot()`), +ε par geste. Donc peintre
  ≈ 3-5 % d'un tick PAR SEMAINE. Bénéfice principal de D2 (rendu Godot + taille JSON transférée) =
  **HORS périmètre mesuré, INCONNU** (pas « modeste »).
- **VERDICT convergé** (Nico option 3 : les deux régimes existent, run éternel) :
  - **populations = plancher plat ∝ plots** (~45 ms/tuile 144 plots). D100-A (bit-identique : tuer la
    redondance ×4/×5/×6 + overhead `at_plot` ~6 % + scalaires + skip) enlève un ms CONSTANT à toute
    échelle → sert la **sim rapide debug/test** + baisse la baseline partout. Golden = filet (déterminisme prouvé).
  - **le RALENTISSEMENT à maturité** (dealbreaker Nico « si ça ralentit en jouant, j'arrête ») =
    travail ∝ plantes : `light` O(N²) (+84 ms) + `reste` (+274 ms). **PAS populations** (+7 ms). →
    c'est **D32 + uptake/croissance**, levier SÉPARÉ et plus GROS à maturité. NE PAS l'absorber dans D100.
  - **D2 peintre** = chantier B distinct (souhait visuel de Nico) ; CPU faible, vrai gain non mesuré
    (Godot). À scoper après mesure taille snapshot + coût Godot (F5, hors de ma portée).
- **Contexte jeu (Nico)** : budget normal = 1 min/semaine (60 s/tick, ÉNORME vs 130-500 ms) → perf
  non-facing au rythme chill ; l'enjeu réel = **mode debug/test le + rapide possible** + **ne pas
  ralentir quand le jardin mûrit** (partie 100-1000 h). Durée de chaque phase = INCONNUE de Nico.

## PLAFOND de gain (dérivé du cProfile, 2026-08-01) + VERDICT
- **Récupérable par mémoïsation** (grilles à args IDENTIQUES, `cum×(n-1)/n`) : golden **2,87 ms/tick**
  = **9,3 % de pop / 2,1 % du tick** ; dense-117 **4,60 ms/tick** = 9,5 % de pop / 1,3 % du tick.
  + nectar (PLAFOND haut, grilles diffèrent) → 3,31 / 5,76 ms. `at_plot` (accès direct, MOTEUR ENTIER,
  fraction dans pop non isolée) : 7,9 / 13,4 ms. `_zero_grid` churn : ~0,2 ms.
- **Plafond réaliste de réduction de pop ≈ 5 % du tick** (memo ~10 % de pop + accès direct at_plot).
  Sur un tick 135-345 ms dont **67 % dans le « reste »** (uptake/croissance/décompo), c'est marginal.
- **VERDICT : D100 n'est PAS un sprint, c'est une DETTE D'OPPORTUNITÉ.** Nettoyer la redondance
  ×4/×5 (offense « pas de recalcul dans un tick », `feedback_pas_de_recalcul_tick`) QUAND on repassera
  dans `resources.py`/`field.py` pour autre chose — pas un sprint dédié à ~5 % de tick invisible.
- **Décision Q2 (Nico)** : D2 (peintre, 1 individu/type/tuile) et D32 (ralentissement maturité =
  light O(N²) + reste) restent des **dettes DISTINCTES**, pas rattachées à D100.

## RÉFUTÉS — à ne PAS refaire re-marcher la prochaine session
- ❌ « `tick_populations` reste 1er poste même dense » → **RÉFUTÉ** : c'est une PENTE en % (24→10 %),
  et en ms `pop` est un plancher ∝ plots pendant que `light`+`reste` explosent ∝ plantes.
- ❌ « croisement à ~70 plantes disqualifie D100 » → **RÉFUTÉ, artefact de pourcentage** : optimiser
  pop rapporte un ms CONSTANT à toute densité (le gain ne rétrécit pas), c'est juste que la tarte grossit.
- ❌ « le peintre est modeste » → **NON MESURÉ** : CPU Python ~3-5 %/tick (1 snapshot/tick), mais le
  vrai gain de D2 (rendu Godot + taille JSON transférée) est HORS profil Python = INCONNU.
- ❌ « bit-identique = exigence de Nico » → FAUX (imposé à tort, D1). Réimplémentation autorisée ;
  mais la courbe montre que le bit-identique suffirait de toute façon (plafond petit).
- ❌ « banc luxuriance = dense » → à nuancer : 0,63 pl/plot, petit en absolu ; la vraie courbe densité
  vient de `build_dense(n)` (tuile 12×12), pas de luxuriance.

## CORRECTIONS Nico (2026-08-01, 3e passe) — actées
- **C1 — `at_plot` NE fait pas partie de D100** : je l'avais mis dans le plafond alors que son coût est
  TRANSVERSAL (moteur entier). Le plafond réel imputable à populations = **mémoïsation SEULE = 2,1 %
  du tick** (pas 5 %). `at_plot` sorti en **dette autonome D103** avec sa contrepartie (lisibilité/
  encapsulation ↔ ~6 % de tick), arbitrage à poser à Nico, pas à trancher en passant.
- **C2 — je recommandais D32 sans avoir ouvert `reste`** (355 ms, 67 %, 4× light) : mon
  « uptake/croissance/décompo » était une SUPPOSITION, pas une mesure. → décomposé ci-dessous.
- **C3 — « D32 = dealbreaker maturité » n'est établi par aucune mesure** : à 131 plantes tick = 343 ms
  / budget 60 s = **175× sous**. Rien n'est visible au joueur à toute échelle mesurée. Phrase juste :
  « aucun poste perf n'est visible au joueur à toute échelle mesurée ; le seul moteur de décision
  restant = la boucle debug/test ». Et si c'est le test qui décide, la cible = le plus gros TERME.

## Décomposition de `reste` (mesurée 2026-08-01, `dense(117)`, `mesures/decompose_reste.py`)
Tick 343 ms/tick, 131 plantes, 144 plots. **pop 49 ms (14 %) · light 58 ms (17 %) · RESTE 236 ms (69 %)**.
`reste` en cumtime (overlap indicatif) — **il n'est PAS ce que j'avais supposé** :
- **`apply_disturbances` 35,7 ms** (herbivorie + `_local_density` + charge sporale `_spore_load`) —
  **1er poste de `reste`, TOTALEMENT OMIS** dans ma supposition. ∝ plantes + voisinage.
- **cluster croissance ~70 ms** : `_apply_uptake` 25 + `grow_plant` 24 + `_update_physiology` 16 +
  exudats/stades 5 — structurel (cœur de croissance), ∝ plantes.
- `tick_seed_bank` + `succession` ~14 ms · `tick_decomposition` **8,7 ms** (MINEUR — j'en avais fait
  un pilier, faux) · longue traîne (diffusion/abri/mycélium/rosée/hydro/ph/structure) ~25 ms, chacun <5 ms.
- **Plombier transversal** (self-time, somme exacte) : genexprs `tile.py` **20 ms** + `at_plot` **13 ms**
  + `grids.set` **4 ms** ≈ 37 ms d'itération/accès étalés partout (⇒ D103).
- **Lecture** : à cette échelle `light` (58 ms) reste le plus gros poste unique OPTIMISABLE (le cluster
  croissance est structurel), MAIS light n'est « le vrai levier » que si le jardin-cible dépasse
  largement 131 plantes — non établi. Rien ne ralentit le joueur ici.

## §REPRISE — DÉCISION PRISE (2026-08-01)
- **D100 → DÉCLASSÉE en dette d'opportunité** (`DETTE.md` D100 réécrite : plafond 2,1 %, bit-identique,
  nettoyer la redondance ×4/×5/×6 quand on repassera dans `resources.py`/`field.py`).
- **`at_plot` → dette autonome D103** (`DETTE.md`, arbitrage lisibilité ↔ ~6 % tick).
- **AUCUNE conception D32 ouverte** : `reste` est maintenant décomposé (croissance structurel + surprise
  `apply_disturbances`), MAIS la 2ᵉ prémisse manque encore → **QUESTION OUVERTE À NICO : taille max
  plausible d'un jardin en fin de partie (en plantes) ?** Sans ce nombre, « light devient le levier »
  reste une extrapolation. Tant qu'inconnue → on ne fige rien sur D32.
- Scripts de mesure (durables, `PYTHONPATH=data/code python3 <script>`) : `mesures/mesure_d100.py`,
  `mesures/mesure_d100b.py`, `mesures/plafond_d100.py`, `mesures/decompose_reste.py`.
- **Interdits** : `test_epaisseur_500ans` ; modifier `vie_macro.py` (dette d'opportunité, hors sprint).

## Échelle N_max — recadrage Nico (2026-08-01, 4e passe) : mesurer le jardin de fin de partie
**But du jeu = luxuriance maximale = toutes les tuiles pleines** → la taille de fin de partie n'est
pas une fourchette, c'est un PRODUIT dérivé du moteur. Si un terme est O(N²) sur le nombre de plantes
et que le but est de maximiser N, c'est une **incompatibilité structurelle avec le but**, pas un détail
perf — et ça déplace qui tranche (conception, pas optim).

- **N_max dérivé du moteur (par commande)** : monde plantable `[0, MONDE_CM=2000]²` = 40×40 = **1600 plots**
  (`peripherie.py:50`) ; maison 800×800 cm = 16×16 = **256 plots** non plantables (`building.py:29`) ;
  périphérie (bande `PROFONDEUR_CM=900`) = **DEHORS** le jardin (`peripherie.py:44,277`) → ne retire rien.
  ⇒ **plots plantables ≈ 1600 − 256 = 1344** (hors chemins 50 cm inter-tuiles, non chiffrés).
- **Densité de saturation** : `[LU dans capacite.py, NON RE-VÉRIFIÉ]` — commentaire annonce plateau
  ÉMERGENT ~100-105 pl pour tuile 11×11 (121 plots) = ~0,83 pl/plot ; grande tuile 256 plots ~150-200
  (~0,68). Disjoncteur dur `CAP_PERF_TUILE=800`/tuile (jamais atteint). **À RE-MESURER** (tuile qui se
  remplit germination ON, compter le plateau) avant de graver le chiffre — c'est le multiplicateur de N_max.
- **⇒ N_max ≈ 900-1115 plantes, ordre ~1000** (conditionné au chiffre de saturation ci-dessus).

### Vérif #2 (Nico) — couplage inter-tuiles côté lumière : PAS de fuite de borne
`fields/light.py:211` `compute(self, plants, saison, house, tile_origin, ceinture)` : les SEULS occulteurs
sont `plants` (liste d'UNE tuile, passée `tile.plants` en `boucle.py:205`), `house` (global), `ceinture`
(périphérie via `occulteurs(ceinture)`). **Aucune référence aux plantes d'autres tuiles** → ombrage
plante↔plante **strictement intra-tuile**. **Fait de conception ASSUMÉ** (pas artefact) : `CLAUDE.md`
documente « chemins 50 cm inter-tuiles non simulés ; **pas d'ombrage inter-tuiles** ». Conséquence : le
terme O(N²) de light (`_point_in_capsule`) porte sur les plantes d'UNE tuile (bornée ~200 plateau / 800
disjoncteur), **pas du monde**. La borne par tuile NE fuit pas côté lumière. Pas de dette neuve.

### Vérif #3 (Nico) — D100 déclassée sur 1/9 du monde : PRÉDICTION écrite AVANT la mesure
`pop` ∝ plots. Banc = 144 plots → 49 ms. Monde ≈ 1344 plots → **pop ≈ 1344/144 × 49 ≈ 457 ms absolu**.
Et light ∝ N²/tuile pendant que pop ∝ plots → **la PART de pop doit encore BAISSER** à l'échelle monde
→ la mesure A doit RENFORCER le déclassement, pas l'infirmer. Réfuté si pop ≫ ~450 ms ou si sa part remonte.

### Mesure FAITE 2026-08-02 00:00→00:14 → `mesures/RESULTATS_nmax_saturation.txt` (fichier complet, conclusions incluses)
**(A) MONDE multi-tuiles** (k tuiles 12×12 pleines, 144 pl/tuile) :
| k | plantes | tick | tick/k | light | pop | reste |
|--|--|--|--|--|--|--|
| 1 | 147 | 501 | 501 | 78 | 51 | 372 |
| 2 | 294 | 1063 | 532 | 162 | 107 | 794 |
| 4 | 588 | 2053 | 513 | 321 | 208 | 1524 |
| 8 | 1176 | 4006 | 501 | 627 | 403 | 2975 |
| 9 | 1323 | 4670 | 519 | 730 | 470 | 3470 |
→ **`tick/k` PLAT (501→519) : tick du monde LINÉAIRE en tuiles. Borne par tuile CONFIRMÉE par mesure.**

**(B) TUILE-UNIQUE géante** (une tuile, n croissant, rc=√n) : plants 147→787, light 79→316,
`light/plots` = 0,55·0,50·0,51·0,44·0,38 **décroissant → light ~LINÉAIRE en plots, PAS O(N²)** à
densité naturelle (le `light_index`/`in_bbox` sous-quadratise). L'O(N²) du carnet (light 7,7→91,5)
n'existait qu'à **densité croissante sur plots FIXES** (15→117 sur 144 plots) = **régime hors-jeu**.

**(#1) SATURATION re-mesurée** (tuile 11×11, germination ON, seed 12345) : oscille **0,55–0,79 pl/plot,
moy ~0,65, max 0,79, PAS de plateau strict** (crash à 0,14 an 26 = dynamique réelle). Commentaire
`capacite.py` (~0,83) = **optimiste**. CAVEAT : setup ≠ celui du commentaire → re-mesure honnête, pas
définitive. **N_max recalculé = 1344 × [0,65..0,79] ≈ 875–1060, ordre ~1000.**

**Prédiction #3** : pop au monde ≈ 457 ms → **mesuré k=9 = 470 ms → CONFIRMÉ**. MAIS « la part de pop
baisse » → **RÉFUTÉ** (elle reste plate ~10 %) : ma prédiction portait encore l'hypothèse fausse
« light quadratique » ; light est linéaire-par-tuile → la part de pop ne bouge pas.

## VERDICT FINAL (2026-08-02, les 3 vérifs soldées → conclusion autorisée)
1. **PAS d'incompatibilité structurelle avec « luxuriance maximale »** : tick monde LINÉAIRE en tuiles (A) ;
   light ~linéaire en plots à densité de jeu (B) ; light per-tuile + tuiles bornées → aucun terme n'explose.
2. **Rien n'est visible au joueur, même à N_max** : monde plein (1323 pl) = **4,67 s/tick vs budget 60 s
   = 12,8× sous**. La luxuriance max reste jouable au rythme chill.
3. **Seul coût réel = boucle debug/test à N_max** : 4,67 s/tick × 500-1000 sem = ~40-78 min/run, RÉEL mais
   LINÉAIRE. Levier = le plus gros terme = **RESTE (74 % à toute échelle)**, PAS light (16 %), PAS pop (10 %).

**Conséquences dettes** :
- **D100** (pop) : **déclassement CONFIRMÉ** (10 % plat, linéaire ; prédiction 457 ms confirmée). Reste dette d'opportunité.
- **D32** (light « O(N²) ») : **prémisse à RE-CADRER** — à densité de jeu, light est linéaire-par-tuile (16 %),
  **pas** le dealbreaker de maturité annoncé ; l'O(N²) strict est un régime hors-jeu. **D32 non prioritaire** ;
  si ouvert un jour, c'est pour la boucle test, **derrière RESTE**. → à mettre à jour dans `DETTE.md` D32.
- **RESTE** : jamais tracé, et c'est le vrai gros terme (74 %) pour la boucle test (croissance structurel +
  `apply_disturbances` ~36 ms/tuile, surprise). **Candidat à une dette « coût boucle debug/test à N_max »**
  SI Nico veut des runs d'endgame rapides. **À trancher par Nico** (pas urgent, non player-facing).

**PROCHAINS PAS pour Nico (à ton réveil)** : (a) valider/corriger ces conclusions ; (b) décider si on
re-cadre D32 dans `DETTE.md` (light non prioritaire, densité de jeu) ; (c) décider si `reste`/boucle-test
mérite une dette. **Aucune action moteur en attente. Interdits inchangés** (`test_epaisseur_500ans` ; `vie_macro.py`).
**Critère d'acceptation (négatif)** : rend les ms aux paliers atteints + liste des paliers non atteints +
statut du chiffre de saturation + réponse couplage inter-tuiles — RIEN d'autre. Aucune conclusion
« pas d'incompatibilité structurelle » avant que #1 (saturation re-mesurée) soit soldé.

## RÉVISION 2026-08-02 (revue) — le VERDICT FINAL ci-dessus est CORRIGÉ sur 3 points
Résultats bruts : `mesures/RESULTATS_review_2026-08-02.txt` (scripts `mesure_review_1b_3.py`,
`mesure_review_B_expo.py`, `mesure_review_C_satur.py`).

### Dette A — `k` est une CONSTANTE du monde ; (A) mesurait un axe qui n'existe pas
`main.py:48-57` : **8 secteurs en dur** (NO NE SO SE N O E S). `tiles.append` seulement dans
`build_world_full`, aucun `add_tile`/`remove` en cours de partie, extension-par-maîtrise **non câblée**.
⇒ **k = 8, toujours.** Donc « tick_monde = Σ tick_tuile linéaire en nombre de tuiles » est une
**tautologie sur une constante** (une somme est linéaire en son nombre de termes ; ce nombre ne varie
jamais). Le banc (A) a fait varier k = un axe que le produit n'a pas. **L'axe réel de fin de partie =
N à géométrie FIXE** (8 tuiles figées qui se remplissent) = régime « surface fixe, densité croissante »,
touché par NI (A) NI (B) d'hier — seulement par 1b/B.
→ **Conclusion (A) réécrite en MAJORATION sous hypothèse de MONOTONIE** (coût monotone croissant en N
et en plots, *plausible, non prouvée*) : le banc k=9 majore le monde de fin de partie sur les 3 axes
(1296 plots > 1188 réels ; 1323 plantes > 772-939 ; 1,02 pl/plot > 0,79). Un majorant mesuré à
**4,67 s/tick** (cProfile, donc pessimiste ; re-mesuré 5,9 s machine chargée) suffit à conclure « pas
de mur perf » — sous cette hypothèse écrite.
→ **Marge joueur = fourchette, pas 12,8×** : `SecondsPerWeek ∈ [30,180]` (`WorldView.Parametres.cs:77`)
÷ 4,67 s = **6,4× (à 30 s) à 38,5× (à 180 s)**. [Le brief citait 25,6× = plafond 120 s ; le plafond
réel offert est 180 s → 38,5×.] Le tick étant cProfile-gonflé, la marge réelle est plus grande.

### Dette B — exposant de light à géométrie produit : **α ≈ 1, exclut 2** (IC retiré)
Surface FIXE = plus grande tuile réelle (16×11=176). **α ≈ 1** : banc propre (endpoints, machine au
repos, alterné) = **1,09** [enveloppe dispersion 1,07-1,09] ; régime RÉEL ≤176 (≤1 pl/plot) = **1,04** ;
global avec empilé = 1,07 (écart empilement 0,03 **de signe attendu** — empiler met plus de paires dans
le même bucket spatial → pousse α vers le haut ; **confirme le mécanisme, sans effet sur la conclusion**).
**PAS d'IC à décimales** : le [0,99;1,16]
SE=0,029 gravé au 1er jet était un OLS i.i.d. sur le bruit court terme, PAS sur le bruit dominant
(inter-jour +27 %, dette 3) → un intervalle faux, retiré. light est linéaire, **jamais O(N²)** à la
géométrie du produit (les points empilés 1,1-1,6 pl/plot = régime spatial que le jeu ne produit jamais).
⇒ **prémisse « O(N²) » de D32 RÉFUTÉE par mesure.** Plage jouable seule : light 15,5→49,6 ms (35→102 pl).
FAUTE consignée : B et C lancés en background SIMULTANÉ → ms de B contaminées par la charge de C
(règle « pas de sim lourde en parallèle d'un banc de ms » énoncée 2 tours plus tôt, violée le même tour).

### Dette C — saturation 3 seeds sur 176 : effondrements STOCHASTIQUES, pas de plateau
| seed | max pl/plot | chutes ≥25 % |
|--|--|--|
| 12345 | 0,812 | 18, 21, **26** (−81 %, 0,131), 28 |
| 271828 | 0,795 | 19, 25 |
| 987654 | 0,778 | 3, 15, 22, 27, 29 |
- Dates **toutes différentes** ⇒ effondrements **stochastiques** (l'an-26 est un artefact du seed 12345,
  qui reproduit la catastrophe d'hier/121). « pas du bruit car déterministe » = abus : un tirage rare
  seedé est déterministe ET stochastique.
- **CORRECTION** : le max (0,78-0,81) n'est PAS le plateau. **Médiane hors transitoire (années 11-30) =
  0,671 / 0,665 / 0,622 ≈ 0,62-0,67** (Q1 ~0,53-0,57, Q3 ~0,71-0,76) ⇒ **≈ 0,68 de `capacite.py` →
  capacite.py CONFIRMÉ, PAS réfuté.** Mon « RÉFUTÉ » du 1er jet comparait une mauvaise grandeur.
- **Cause EXOGÈNE à la tuile, et PARTAGÉE par tout le monde** (site d'appel `boucle.py:91-95` :
  `seed = game_state["seed"]` global, `event, temp_now, nebul = weather_state(seed, week)` calculé **une
  fois AVANT la boucle tuiles**, puis fan-out à toutes les tuiles `boucle.py:115` (`temperature.fill`) et
  `:161` (`appliquer_alea` sur chaque tuile). `weather_at(seed, week)` (`weather.py:124`) n'a **aucun
  paramètre de tuile** → même événement, même instant, **8 secteurs simultanés**. Année 26 seed 12345 :
  Gelée tardive (w1311), **double Tempête** (w1332-33) + Pluie prolongée (w1334). Lien létal précis non tracé.
- **Fréquence** : 11 chutes ≥25 % / 87 années-tuile = **1 tous les 7,9 ans**. Mais la mesure est PAR TUILE
  ISOLÉE ; en jeu la météo est partagée ⇒ ce n'est PAS « un coin flanche de temps en temps », c'est
  **le JARDIN ENTIER qui s'effondre le même hiver, ~1-3 fois par partie**. Sur un jeu dont le but est la
  luxuriance maximale, « un coin » vs « tout le jardin » = deux jeux différents → **FAIT DE GAMEPLAY** (décision 2).
- Les 3 séries **oscillent sans plateau** ⇒ **« luxuriance maximale » n'est PAS un état stationnaire** ;
  N_max est une **distribution à queue basse** (jusqu'à 0,13 pl/plot). **N_max NON recalculé** (nature de
  l'effondrement = conception, pas mesure). Ancien « N_max ≈ 875-1060 » → **[1 seed, non répliqué], NON gravé.**

### Dette 3 — « PLAT » : défendable en MÉTHODE seulement
k=1 méd 647,7 vs k=9 méd 658,6 = **+1,7 %, dans le bruit intra-palier (1,2-2,5 %)** → « tick/k constant
± bruit » tient. MAIS absolus **instables entre jours** (hier 519, aujourd'hui 658, +27 %). 144 n'existant
pas dans le produit, **aucune conclusion moteur** n'en est tirée.

### 5 décisions EMPILÉES pour Nico, PAR ORDRE (aucune n'est une mesure — NE PAS les mesurer)
**Urgentes (1 & 2)** :
1. **Écrire `cleanupPeriodDays`** dans `~/.claude/settings.json` (valeur au choix ; l'important = qu'elle
   soit écrite). **Débloque le chantier A** (atelier hook, hors Symbiose), coût nul. Transforme un état
   caché version-dépendant en observable.
2. **Effondrements ~1-3 par partie : voulus ou pas ?** Seul point qui touche le jeu que Nico fait.
   → décider si ça part vers `/conception` ou reste un fait acquis.

**Peuvent attendre (3-5)** :
3. **Re-cadrage D32** dans `DETTE.md` : light **≈ linéaire (α ≈ 1), pas O(N²)** à géométrie produit.
   Direction acquise ; formulation exacte = après dette 1(a)(b) [FAITE]. Je ne touche pas `DETTE.md`.
4. **Marge min garantie à `SecondsPerWeek` = 30 s** (plancher mesuré 6,4×).
5. **`reste`** = 74 % du tick dont **~72 % sans nom** (seul ~28 % identifié) → dette « boucle debug/test » ou pas.
