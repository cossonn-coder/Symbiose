# Sprint — Compétition intra-plot (cohabitation, stratification & éclaircissage)

> **Kickoff autosuffisant** (démarrage à froid). Implémente la **compétition
> intra-plot** : lever le verrou de germination, ajouter la **stratification**
> (tolérance à l'ombre + étiolement), laisser l'**éclaircissage émerger**. La
> conception est **figée** : source de vérité des décisions =
> **`data/code/CONCEPTION_COMPETITION_INTRAPLOT.md`** (§3 décisions Q1–Q11, §4
> calibrage, §6 découpage). Ce fichier porte le **plan d'implémentation testable**.
>
> Règles projet : **moteur Python = source de vérité** ; pédagogie explicite ;
> conserver tout code/test. **Re-figeage golden MAÎTRISÉ et ANNONCÉ** attendu
> (`7ee907d3…` → nouveau hash) — à TROIS causes isolées (§ tronçons). Ampleur :
> **moyen** (cœur écolo + vecteur de gènes + golden). Pur **Python** — aucun
> fichier C# (le pont n'a rien de neuf à router ; volet vue ultérieur).

## Ce qu'on construit, en une phrase
Plusieurs plantes peuvent **essayer** de pousser sur un même plot ; les
**conditions réelles** (lumière au sol ombragée, sol, eau, nutriments) décident
qui lève et qui prospère ; un **gène `tolerance_ombre`** + l'**étiolement** font
émerger la **guilde stratifiée** (couvre-sol sciaphile sous une haute) ; les
perdants **dépérissent par les stress existants** (jamais un verdict).

## État de départ (vérifié au kickoff, 2026-06-13) — golden `7ee907d3…`

**La compétition est DÉJÀ émergente — ne pas la réinventer (CONCEPTION §2.0) :**
- **Empilement permis au niveau bas** : `world/tile.py:add_plant(cls,r,c)` crée
  une `PlantInstance` **sans vérifier l'occupation**. Le verrou est UNIQUEMENT
  dans la germination.
- **Lumière asymétrique** : `fields/light.py:light_received` ne filtre que par
  voisins **plus hauts** (le plus haut gagne ; le plus bas n'ombrage pas
  au-dessus). `shade_memory` monte pour l'ombré (`engine.py:309`).
- **Uptake partagé** : `engine.py:_apply_uptake` puise sur tout `root_plots` ;
  empreintes chevauchantes épuisent le même sol.
- **Phototropisme directionnel** codé : `sim/growth.py:_phototropic_bias`
  (`phototropism_strength` par espèce, `light_field` passé à `grow_plant`).

**Le verrou à lever (le seul) — `sim/succession.py`, DEUX gardes par porte :**
- `succession()` : ligne **145** `if (r,c) in occupied_roots: continue` **ET**
  ligne **184** `if any(p.position==(r,c) … ): continue`.
- `spring_flush()` : ligne **226** (skip `occupied_roots`) **ET** ligne **261**.
- `_lever_grains_en_attente()` : ligne **64** `if (r,c) in occupied_roots …:
  continue` (le grain planté patiente).
- `occupied_roots` est bâti (lignes 130, 211) depuis `root_plots` + `position`
  de toutes les plantes vivantes ; il est **muté** après chaque levée pour
  éviter une re-germination dans le même tick.

**Les points de lecture à brancher :**
- **Germination** : `niche = seed_bank.niche_index(r,c, light, root_density,
  disturbance, soil_deep)` (`succession.py:161/241`), puis
  `germination_candidates(r,c,seed,week,niche)` (`seedbank.py:254`,
  `threshold = niche * density` par archétype) + `choisir_archetype`. C'est
  **ici** qu'entre la **lumière effective** (`light × tolerance_ombre`).
- **Croissance** : `engine.py:_update_physiology` —
  `growth_factor = 0.6 + 0.4 × light` (`:324`) et `shade_memory` (`:309`). C'est
  **ici** qu'entre la **lumière corrigée** + le départ de l'**étiolement**.
- **Densité** : `sim/effects.py:_local_density` compte les voisins via
  `tile.plots_within_radius(r,c,1)` **qui exclut le centre** (`tile.py:131
  discard((row,col))`) → co-occupants non comptés. `damping_off` (`:363`) lit
  cette densité.
- **Gènes** : `plants/genetics.py:GENE_NAMES` (5 gènes), `child_genes` hérite
  **automatiquement** tout gène du tuple (canal de hash = index). `tolerance_secheresse`
  est le **patron** à recopier. `plants/base.py` : champ `strate` ∈ {haute,
  moyenne, basse, sol, grimpante}, `STRATE_PROFILES`.

## Modèle figé (résumé — détail dans CONCEPTION §2-§3)
1. **Lever le verrou** SANS terme « occupation » artificiel : on supprime les
   deux gardes des 3 portes. Le frein vient des **champs réels** (lumière-sol
   ombragée + `soil_memory_deep`) déjà dans `niche_index`. **Pas de cap dur** (Q2).
2. **Gène `tolerance_ombre`** (Q6, >1 = sciaphile), défaut par strate
   (sol/basse ≈ 1.25, haute ≈ 0.90), hérité via `child_genes`. Branché en
   **germination** (lumière effective `light × tolerance_ombre`) **et** en
   **croissance** (`growth_factor` sur lumière corrigée).
3. **Étiolement** (Q7) : héliophile (`tolerance_ombre < 1`) ombragé
   (`light_eff < 0.4`) → **élongation axiale +30 %** + **robustesse −10 %** →
   sauvé s'il atteint la lumière (phototropisme), sinon dépérit
   (`_tick_senescence_health` → nécromasse). Garantir `light_field` passé.
4. **Éclaircissage par convergence** (Q3/Q4) : **mesurer d'abord** si l'émergent
   tue ; sinon inclure les **co-occupants du centre** dans `_local_density` →
   fonte des semis éclaircit le serré. Place racinaire / uptake / asphyxie déjà
   émergents. **Aucune mortalité « verdict ».**
- **Philo** : flux (lumière/eau) → contrainte (rareté/ombre) → réponse (déclin)
  émergente (#2) ; semer dense = vraie décision apprise (#6) ; sols/lumières
  différents → cohabitations différentes (#7).

## Plan (étapes vérifiables) — tronçons isolés, golden re-figé pas à pas

> **Ordre critique** : tronçon 1 **seul d'abord** (isole la dérive « empilement »
> avant d'introduire le gène/étiolement → chaque re-figeage a UNE cause claire).

1. **Lever le verrou** (`sim/succession.py`) — supprimer les **deux gardes** des
   3 portes (`succession` 145+184, `spring_flush` 226+261, `_lever_grains_en_attente`
   64). Garder la **mutation** d'`occupied_roots` après chaque levée (évite la
   double-germination dans le tick) — mais ne plus l'utiliser comme **skip
   d'entrée**. **MESURER (Q3)** : compter les germinations et observer sur N
   saisons si les dominés meurent (`main.py` long run / test dédié).
   → **vérif** : **golden RE-FIGÉ maîtrisé** — compter germinations avant/après,
   vérifier que la **seule** dérive est l'empilement (population plus dense),
   aucune autre mécanique de tick ne bouge. Diff expliqué dans le commit.
2. **Gène `tolerance_ombre`** (`plants/genetics.py`) — l'ajouter à `GENE_NAMES`
   (après `tolerance_secheresse`). Défaut **par strate** au niveau espèce
   (`species.py`/`perennials.py` ou dérivé de `STRATE_PROFILES`). Brancher la
   **lumière effective** : (a) germination — escompter `light` par la
   `tolerance_ombre` de l'archétype/espèce candidat dans le seuil (cf. piège
   « niche commune ») ; (b) croissance — `growth_factor = 0.6 + 0.4 ×
   min(1, light × tolerance_ombre)` (`engine.py:324`).
   → **vérif** : **golden re-figé maîtrisé** (dérive structurelle = un gène de
   plus + sciaphiles qui lèvent/prospèrent à l'ombre). Test : héliophile **ne**
   lève **pas** sous canopée dense, sciaphile **oui** ; sciaphile ombragé garde
   sa croissance.
3. **Étiolement** (`sim/growth.py`) — élongation axiale accrue à l'ombre pour
   `tolerance_ombre < 1` quand `light_eff < 0.4` (constante `ETIOLEMENT_GAIN ≈
   0.30` sur la vitesse dans `_elongate_emit`/`grow_plant`) + coût robustesse
   (santé/résistance −10 % tant qu'étiolé). Garantir le `light_field` du tick
   passé pour TOUS les co-occupants ombragés.
   → **vérif** : **golden re-figé maîtrisé** (morphogénèse ombragée). Test :
   héliophile ombragé file (hauteur ↑, segments grêles) puis sauvé si trouée /
   dépérit sinon.
4. **Densité intra-plot** (`sim/effects.py:_local_density`) — *SI tronçon 1
   montre l'embouteillage* : inclure les co-occupants du plot central (les
   plantes vivantes à `position == (r,c)`, hors `plant` elle-même) dans le
   compte, poids 1.0 normalisé `/6`. → fonte des semis (`damping_off`) éclaircit
   le serré. **Sauté si l'émergent suffit (Q3).**
   → **vérif** : **golden re-figé maîtrisé**. Test : semis serré (3+ même
   position, sol humide) fond ; semis isolé survit.
5. **Tests + suite complète** : co-germination (héliophile/sciaphile),
   stratification viable (1 haute + 1 couvre-sol survivent ensemble), étiolement,
   éclaircissage sur N saisons, **déterminisme byte-identique**, golden re-figé.
   Lancer `test_golden`, `test_croissance`, `test_vigueur`, `test_genetique`,
   `test_population`, `test_sim_server` ; `main.py` tourne.

## Critères de succès
- [ ] **Golden re-figé MAÎTRISÉ** : nouveau hash, dérive **expliquée** (empilement
      + gène + étiolement), comptée avant/après ; aucune cause hors ces trois.
- [ ] **Stratification émerge** : un couvre-sol sciaphile **survit** sous une
      haute ; un héliophile **ne lève pas** / dépérit à l'ombre.
- [ ] **Étiolement** observable (héliophile ombragé file vers la lumière).
- [ ] **Éclaircissage** : un semis serré fond (mesuré, ou via tronçon 4) ; aucune
      mortalité « verdict » ajoutée (mort par `_tick_senescence_health`).
- [ ] **Déterminisme** byte-à-byte (`test_sim_server`, 2 runs identiques).
- [ ] `main.py` tourne propre ; toute la suite verte.

## Pièges identifiés (à ne pas réapprendre à chaud)
- **DEUX gardes par porte, pas une.** Chaque porte a le skip `occupied_roots`
  **ET** une garde `any(p.position==(r,c))`. Lever les deux, sinon l'empilement
  ne se fait pas (la garde position bloque le co-spawn exact).
- **Garder la mutation d'`occupied_roots`** après chaque levée (anti
  double-germination intra-tick) — c'est le **skip d'ENTRÉE** qu'on retire, pas
  la mise à jour. Sinon : risque de germinations multiples non déterministes au
  même tick.
- **Niche commune vs tolérance par espèce.** `niche` est calculée **avant** le
  choix d'espèce (commune au plot), or `tolerance_ombre` est **par espèce**. Pour
  l'escompte lumière, moduler **dans `germination_candidates`** (seuil par
  archétype : `threshold = niche_with(light×tol_arch) * density`) plutôt que la
  niche globale — sinon tous les archétypes sont escomptés pareil. À confirmer
  selon l'archi `seedbank`.
- **Nouveau gène = golden plus large.** Ajouter à `GENE_NAMES` change la **taille
  du vecteur** → décale les canaux de hash de `child_genes`/`sample_genes`.
  Dérive **structurelle attendue** (pas un bug) ; c'est pourquoi le tronçon 1
  (empilement seul) passe **avant** — pour ne pas mélanger les causes.
- **`growth_factor` borné [0.3, 1.0]** (`engine.py:326`) : la correction
  `light × tolerance_ombre` doit rester dans les bornes ; un sciaphile ne doit
  pas dépasser 1.0 (cap `min(1, …)`).
- **`health` est un `int` 0-3** (`base.py`) : le coût robustesse de l'étiolement
  ne doit pas tuer instantanément ; préférer une pénalité sur la **résistance**
  / la susceptibilité que sur `health` direct, pour rester émergent.
- **Perf D32** (`LightField` = 53 % CPU, ∝ canopée) : pas de cap design, mais
  **surveiller** la densité au calibrage ; si emballement, alerter Nico avant
  d'introduire un cap (décision écartée a priori, Q2).
- **Déterminisme** : aucun RNG neuf ; réutiliser `_hash_noise`/canaux de
  succession existants. L'itération plots est déjà ordonnée.

## Après ce sprint
- Mettre à jour `journal.md` (clôture), `BACKLOG.md` (retirer « compétition
  intra-plot » des suivants), la mémoire projet.
- **Rendu Godot** de la pile (offsets visuels, profondeur, lisibilité d'une
  cohabitation) = **volet vue ultérieur** ; le pont n'a rien de neuf à router.
- Reste backlog : save global (hook `OnSeasonEnd` posé), décomposition/compost,
  saisonnalité vie macro, physico-chimie sol, **tranche 7 packaging PyInstaller**.

---
*Réfs : `data/code/CONCEPTION_COMPETITION_INTRAPLOT.md` (conception figée),
`sprint_competition_intraplot_conception.md` (kickoff de conception),
`sprint_ecrasement_plantes.md` (gabarit de structure), `sim/succession.py`
(3 portes), `fields/seedbank.py` (`niche_index`, `germination_candidates`),
`fields/light.py` (`light_received`), `sim/engine.py` (`_apply_uptake`,
`_update_physiology`, `_tick_senescence_health`), `sim/effects.py`
(`_local_density`, `damping_off`), `world/tile.py` (`plots_within_radius`,
`add_plant`), `plants/genetics.py` (`GENE_NAMES`, `child_genes`),
`plants/base.py` (`strate`, `STRATE_PROFILES`), `sim/growth.py`
(`_phototropic_bias`, `_elongate_emit`), `tests/test_golden.py`.*
