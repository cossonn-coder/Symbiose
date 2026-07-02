# Sprint BUGS D'ÉMERGENCE — état vivant (conception en cours)

> Carnet de bord `/conception` (§0bis). Reprise à froid : lire `CLAUDE.md` +
> ce fichier. Sujet lancé le 2026-07-02 par Nico : deux comportements émergents
> indésirables observés au F5 / en sim longue.

## Sujet
- **S2 — floraison synchronisée** : toutes les plantes fleurissent en même temps.
- **S3 — invasion de bourse-à-pasteur (Capsella) à ~6 ans qui « bloque toute
  germination »** : monoculture pionnière qui verrouille la succession.

## Phase courante
**EN COURS** — tronçon ① (D56) LIVRÉ le 2026-07-02 (moteur touché, golden re-figé,
non commité). Reste ②③④. Doc : `docs/conception/CONCEPTION_BUGS_EMERGENCE.md`.

## Décisions figées (arbitrage Nico)
- **Périmètre** : UN sprint, 2 volets (S2 floraison + S3 succession).
- **S3** : direction **C** = facilitation écologique (amorçage OM des tardifs +
  bride pioneer) **+ D56** (champs initiaux riches & hétérogènes).
- **S2** : **gène de phénologie** `phenologie_florale` (émergent, sélectionnable,
  précédent = `germination_thermique`).

## Carte des tronçons (4, perf-first, golden en cascade maîtrisée)
- **① `01_champs_initiaux.md`** — D56 : champs initiaux riches & hétérogènes
  (fondation). **LIVRÉ 2026-07-02.** Golden RE-FIGÉ maîtrisé
  `ea135bf181a21fcb621658c13a92cc6d28de9101ba34fca14acb0e4889365f8f`
  (ancien `ae445d3f…`). Raison : les TUILES démarrent avec un humus de fond
  `om_stable` hérité, non nul et HÉTÉROGÈNE par plot → la cascade OM/CEC/
  soil_memory dérive légèrement sur le smoke 2 tuiles × 4 ans.
- **② `02_reequilibrage_banque.md`** — facilitation OM des tardifs + bride
  pioneer (déverrouille S3) + banc bascule. Golden RE-FIGÉ (but du tronçon).
- **③ `03_gene_phenologie_florale.md`** — gène `phenologie_florale` + décalage
  GDD par individu (désynchronise S2). Golden re-figé MAÎTRISÉ (ajout clé).
- **④ `04_voix_et_bancs.md`** — voix (concepts succession/phénologie) + bancs
  d'acceptation. Golden NEUTRE.

## Constats établis (par lecture du code)

### S2 — floraison synchronisée — CAUSE IDENTIFIÉE
- `sim/engine/floraison.py` : double porte GDD + photopériode + maturité.
- `gdd_floraison`, `bloom_daylen_min/max` sont des **constantes de CLASSE**,
  identiques pour tous les individus d'une espèce.
- `temperature.at_plot` quasi uniforme sur la tuile → tous accumulent les mêmes
  GDD → **tous franchissent la porte la même semaine**.
- Aggravé par la porte thermique de GERMINATION (sprint germination thermique
  2026-07-01) qui concentre les levées dans une fenêtre chaude étroite → cohorte
  synchrone → floraison synchrone.
- **Aucune variation individuelle** du déclenchement floral (pas de gène, pas de
  modulation par âge/vigueur). → C'EST le trou.
- Précédent EXACT à réutiliser : gène `germination_thermique` qui décale
  `t_opt_eff = t_germ_opt − GERM_GENE_SHIFT·(gène−1)` par individu (grain propre
  + pool féral `GeneStat.mean`). Même patron pour un gène phénologie florale
  décalant `gdd_floraison`.

### S3 — invasion Capsella — CAUSE CONFIRMÉE (diagnostic sim)
Diagnostic `/tmp/diag_symbiose.py` (monde complet, an par an) :
```
an  pion fixe gram comp cult  germ   sbPio  sbFix  sdeep
 1   152   38   37   61   36    593   0.127  0.009  0.014
 2   318   29   26   32   29   1048   0.265  0.008  0.026
 3   601   16   32   38   17   1889   0.393  0.007  0.037
 4   838   15    7   12    3   3247   0.544  0.007  0.048
 5   979   23    7    8    0   4095   0.689  0.006  0.058   ← cultivées=0, ~95% pioneer
```
Marche MONOTONE vers la monoculture Capsella ; cultivées effacées dès l'an 5.
Impact S2 (floraison) confirmé côté conséquence : `floraison` alimente le nectar
(`registry._make_nectar_grid`) → pollinisateurs → miel (`apiculture`) ; pic
synchrone unique = boom/bust pollinisateurs (au lieu d'un nectar soutenu).
- **Emballement de la banque pioneer** : `tick_disturbance_enrichment` pompe
  pioneer CHAQUE semaine (disturbance ~0.5, jamais gaté) → `sbPio` sature ;
  les tardifs restent au plancher 0.007.
- **`soil_memory_deep` monte beaucoup trop lentement** (0.014→0.037 en 3 ans ;
  SOIL_DEEP_RATE décennal). Or `tick_late_succession_enrichment` (SEUL amorçage
  des tardifs dans la banque) exige `soil_deep ≥ 0.2` (competitor ≥ 0.4). Seuil
  jamais franchi avant ~15 ans → **fixer/grass/competitor n'entrent JAMAIS dans
  la banque** → `germination_candidates` ne renvoie QUE pioneer → `choisir_
  archetype` ne peut choisir que pioneer, quelle que soit la maturité du sol.
- **Cercle vicieux** (chicken-and-egg) : les tardifs ne peuvent grener (donc
  s'auto-alimenter via `tick_plant_production`) que s'ils germent ; ils ne
  germent que s'ils sont dans la banque ; ils n'y entrent que via le trickle
  gaté sur `soil_deep`, lui-même gaté sur des plantes établies. Seul pioneer
  échappe au verrou (enrichi par disturbance, sans gate).
- **Capsella gagne aussi la course thermique** (opt 11 / tol 13 = fenêtre la
  plus large & froide) → lève la première à chaque printemps.
- Vécu joueur = les **cultivées chutent** (36→17 en 3 ans), tout devient
  bourse-à-pasteur. « Bloque toute germination » = bloque tout SAUF pioneer.
- `disturbance` NE s'effondre PAS (relaxe vers ~0.5) → S3 n'est PAS un
  effondrement de niche, mais un **verrou de succession** (banque + seuil).
- **Régression probable** du sprint germination thermique (2026-07-01) qui a
  supprimé `spring_flush` et concentré la levée dans la fenêtre chaude, là où
  Capsella domine. D25 (« bascule prairie ~30 ans ») date d'AVANT.

### S3 — HYPOTHÈSES (archive du raisonnement pré-diagnostic)
- Capsella (`plants/species/adventices.py`) : pioneer, `t_germ_opt=11`,
  `t_germ_tol=13` = **la fenêtre thermique la plus large & la plus froide** des
  archétypes → lève **la première et la plus large** à chaque sortie d'hiver.
- `niche_index = light·(1−root_density)·disturbance·(1−soil_deep·0.5)` :
  une fois le tapis Capsella levé, `root_density` monte → niche des autres
  s'effondre → pré-emption de la fenêtre de printemps chaque année.
- `choisir_archetype` favorise pioneer sur sol nu ; les tardifs (fixer/grass/
  competitor) ont `t_germ_opt` proches (12-13) mais tol plus étroite → perdent
  la course de printemps.
- D25 disait la succession « résolue » (bascule prairie ~30 ans) AVANT le sprint
  germination thermique (2026-07-01) qui a **supprimé `spring_flush`** et
  concentré la levée : **S3 est probablement une régression de ce sprint.**
- D56 relie S3 aux **champs initiaux pauvres** (S4) → succession affamée.
- Reste à confirmer par le diagnostic : est-ce (a) monoculture de banque-sol
  pioneer, (b) effondrement de niche (disturbance→0 → plus RIEN ne lève), ou
  (c) pré-emption thermique par Capsella ? → oriente le fix.

## Diagnostic en cours
Script jetable `/tmp/diag_symbiose.py` (12 ans, composition + germinations +
banque-sol + champs moyens par an). Run lancé, sortie bufferisée.

## Proposition de fix (à valider par Nico)

### S2 — gène de phénologie florale (précédent EXACT = `germination_thermique`)
- Ajouter `phenologie_florale` EN QUEUE de `GENE_NAMES` (canaux de hash préservés).
- `floraison.py` : `gdd_eff = gdd_floraison − FLORA_GENE_SHIFT·(gene−1)` par
  individu ; gène tiré du pool banque-sol (`sample_genes`, variance) → étalement
  des dates de floraison + sélection darwinienne émergente.
- Golden re-figé MAÎTRISÉ : ajout d'une clé sérialisée ; SHIFT=0 ⇒ sim identique
  au démarrage, l'étalement émerge plus tard (preuve = celle du ④ thermique).

### S3 — déverrouiller la succession (3 directions, à trancher)
- **A. Facilitation écologique (reco)** : amorcer la banque des tardifs sur un
  signal RÉELLEMENT bâti par les pionnières (OM/N/microbiome), pas sur le
  `soil_deep` décennal ; + borner l'emballement pioneer. Émergent, philo #2.
- **B. Recalibrage léger** : baisser seuils `tick_late_succession_enrichment`
  (0.2→…), accélérer `soil_deep`, plafonner `sbPio`. Simple mais « magique ».
- **C. A + D56** : champs initiaux riches & hétérogènes par secteur → succession
  hétérogène (philo #7). D56 déjà en dette, couplage naturel.

## Questions ouvertes (posées à Nico, en attente de réponse)
1. Périmètre : UN sprint 2 volets (S2+S3) vs deux sprints ?  [reco : un sprint]
2. Direction S3 : A / B / C ?  [reco : A, ou C si on absorbe D56]
3. S2 : gène de phénologie (émergent) vs jitter non-génétique (plus léger) ?
   [reco : gène]

## Avancement tronçon ① (D56) — livré 2026-07-02
- `fields/noise.py` : ajout `stable_str_hash(text)` (FNV-1a 32 bits DÉTERMINISTE,
  ≠ `hash()` natif randomisé) → canal de bruit propre à chaque tuile depuis son
  `tile_id`, reproductible d'un run à l'autre (philo #3).
- `fields/ecofields/constants.py` : `OM_STABLE_INIT = 0.15` (humus de fond hérité)
  et `INIT_AMPLITUDE = 0.30` (amplitude de l'hétérogénéité spatiale par plot).
- `fields/ecofields/container.py` : helper `_init_heterogene(grid, plancher)`
  (pose `plancher · (1 + INIT_AMPLITUDE·(2·bruit−1))` par plot) ; appelé sur
  `om_stable` DEPUIS `init_eco` (chemin des TUILES), PAS depuis `__post_init__`.
- **DÉCISION de design imprévue** : l'hétérogénéité ne porte QUE sur `om_stable`,
  pas sur humidité/microbiome/NPK. Motif : (1) `om_stable` est le levier exact de
  la facilitation S3 (`om_index` du tronçon ②) ; (2) l'appliquer aux champs forcés
  par `init_eco` cassait 4 suites unitaires (test_eau/lessivage/substrat/mycelium)
  qui contrôlent l'humidité/NPK plot à plot. Choix conforme au kickoff §Modèle
  (« garder le contrôle du re-figeage »).
- **DÉCISION #2** : humus posé dans `init_eco` et NON `__post_init__` — sinon les
  mini-sols de conteneur (tile_id auto-incrémenté `pot:potN`) recevaient un humus
  dépendant de leur ID → `test_conteneur::test_determinisme` cassait (deux
  conteneurs « identiques » divergaient). Les conteneurs appellent `EcoFields(...)`
  direct + recette → restent à om_stable=0, déterminisme intact.
- Tests recalés (baseline humus=0, hors périmètre du levier D56) : `test_lessivage`
  (`_eco` remet om_stable à 0 pour ses égalités math exactes) et `test_structures`
  (`test_epandre` idem). SUITE COMPLÈTE VERTE (44 suites + golden re-figé ; hashes
  population/vigueur INCHANGÉS).

## §REPRISE
TRONÇON ① (D56) LIVRÉ & vérifié (golden re-figé `ea135bf1…`, toutes suites vertes,
NON commité — Nico commit). **Prochain : tronçon ② `02_reequilibrage_banque.md`**
(facilitation OM des tardifs via `om_index` = `(om_active+om_stable)/OM_FACILITATION_REF`
+ bride pioneer ∝ `(1−om_index)` — le socle `om_stable` hétérogène est en place).
Diagnostic S2/S3 clos (cf. ci-dessus) ; reproductible via `/tmp/diag_symbiose.py`.
