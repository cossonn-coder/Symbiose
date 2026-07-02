# Sprint BUGS D'ÉMERGENCE — état vivant (conception en cours)

> Carnet de bord `/conception` (§0bis). Reprise à froid : lire `CLAUDE.md` +
> ce fichier. Sujet lancé le 2026-07-02 par Nico : deux comportements émergents
> indésirables observés au F5 / en sim longue.

## Sujet
- **S2 — floraison synchronisée** : toutes les plantes fleurissent en même temps.
- **S3 — invasion de bourse-à-pasteur (Capsella) à ~6 ans qui « bloque toute
  germination »** : monoculture pionnière qui verrouille la succession.

## Phase courante
**FIGÉ le 2026-07-02** — conception validée par Nico, kickoffs écrits, prêt pour
`/sprint-auto`. Diagnostic clos, arbitrages tranchés. Aucun fichier moteur touché
(seulement docs/kickoffs). Doc : `docs/conception/CONCEPTION_BUGS_EMERGENCE.md`.

## Décisions figées (arbitrage Nico)
- **Périmètre** : UN sprint, 2 volets (S2 floraison + S3 succession).
- **S3** : direction **C** = facilitation écologique (amorçage OM des tardifs +
  bride pioneer) **+ D56** (champs initiaux riches & hétérogènes).
- **S2** : **gène de phénologie** `phenologie_florale` (émergent, sélectionnable,
  précédent = `germination_thermique`).

## Carte des tronçons (4, perf-first, golden en cascade maîtrisée)
- **① `01_champs_initiaux.md`** — D56 : champs initiaux riches & hétérogènes
  (fondation). Golden re-figé si touche le build golden.
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

## §REPRISE
DIAGNOSTIC CLOS (causes S2 & S3 confirmées, cf. ci-dessus). Phase A : EN ATTENTE
des réponses de Nico aux 3 questions d'arbitrage. Ne RIEN figer avant OK. Une
fois tranché : durcir la conception (doc `CONCEPTION_*`), découper en tronçons
perf-first, écrire les kickoffs `0N`. Le diagnostic est reproductible via
`/tmp/diag_symbiose.py <ans>` (jetable, monde complet an par an).
