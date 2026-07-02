# 2026-07-02 — Sprint BUGS D'ÉMERGENCE (①→④) — SPRINT TERMINÉ (`/sprint-auto`)

Corrige deux comportements émergents indésirables observés au F5 / en sim
longue, en UN sprint 2 volets (conception figée le 2026-07-02, doc
`docs/conception/CONCEPTION_BUGS_EMERGENCE.md`) :

- **S2 — floraison synchronisée** : toutes les plantes fleurissaient la même
  semaine (seuils floraux constants de classe, aucune variance individuelle).
- **S3 — invasion Capsella à ~6 ans** : monoculture pionnière verrouillant la
  succession (« bloque toute germination »).

## Diagnostic (avant fix)
- **S2** : `sim/engine/floraison.py` — double porte GDD + photopériode + maturité,
  `gdd_floraison` constante de classe identique pour tous → franchissement
  synchrone. Aggravé par la porte thermique de germination (sprint germination
  thermique 2026-07-01) qui concentre les levées.
- **S3** : marche MONOTONE vers la monoculture Capsella (cultivées effacées dès
  l'an 5, ~95 % pioneer). Cause = **verrou de succession** : les tardifs
  (fixatrice/graminée/competitor) n'entraient en banque-sol que via
  `tick_late_succession_enrichment`, gaté sur `soil_memory_deep ≥ 0.2` (décennal,
  jamais atteint) ; seul pioneer alimentait la banque (`tick_disturbance_
  enrichment`, sans porte) → cercle vicieux chicken-and-egg. Régression probable
  du sprint germination thermique (suppression de `spring_flush`).

## Décisions figées (arbitrage Nico)
- **S3** : direction **C** = facilitation écologique (amorçage OM des tardifs +
  bride pioneer) **+ D56** (champs initiaux riches & hétérogènes).
- **S2** : **gène de phénologie** `phenologie_florale` (émergent, sélectionnable,
  précédent EXACT = `germination_thermique`).

## Tronçons (4, perf-first, golden en cascade maîtrisée)

### ① D56 — Champs initiaux riches & hétérogènes (`ce75fea`)
Le sol part désormais avec un humus de fond `om_stable` non nul et hétérogène par
plot (plancher `OM_STABLE_INIT=0.15` modulé ±`INIT_AMPLITUDE=0.30` via un bruit
dérivé du hash du `tile_id` — nouveau `stable_str_hash` FNV-1a dans `noise.py`,
zéro RNG, philo #3/#7). Fondation du déverrouillage S3 : certains secteurs partent
plus humifères → amorçage plus précoce des tardifs. L'hétérogénéité porte sur le
SEUL `om_stable`, posée dans `init_eco` (chemin tuiles, pas les mini-sols de
conteneur). **Golden RE-FIGÉ maîtrisé `ea135bf1…`** (humus initial non nul →
cascade OM/CEC légère, déterministe) ; `test_lessivage`/`test_structures` recalés
sur une baseline humus=0 (isolent lessivage/épandage). D56 livré.

### ② Rééquilibrage de la banque-sol — déverrouille S3 (`3448f40`)
L'amorçage des tardifs passe du gate `soil_memory_deep` (décennal) à un
`om_index = clamp((om_active+om_stable)/REF)` réactif, bâti par les pionnières
(levier D56) : fixatrice/graminée dès `om_index≥0.05`, competitor dès `≥0.20`,
apport ∝ `om_index`. En miroir, l'apport pioneer est bridé par `(1−om_index)` →
sur sol bâti le tapis Capsella cesse de se sur-alimenter. La bascule
pionnier→prairie ÉMERGE du flux OM (philo #2). Vue lecture-seule `_OmIndexField`
(pas d'allocation par tick). Banc neuf `succession_bascule` (oracle en tendance,
15 ans) **6/6** : pioneer culmine an 5 puis reflue (7,6 %), tardifs 92 %.
**Golden RE-FIGÉ `98bdf772…`** (but du tronçon) + `test_population` `e7f1cf19…`
(cascade T_sol→vie macro). D25/D56 notés résolus.

### ③ Gène `phenologie_florale` — désynchronise S2 (`4d3db3a`)
Gène ajouté EN QUEUE de `GENE_NAMES` (canaux de hash préservés, garde-fou
identique à `germination_thermique`) ; dans `floraison.py` le seuil effectif
devient `gdd_floraison − FLORA_GENE_SHIFT·(gène−1)` par individu (miroir exact de
`GERM_GENE_SHIFT`, `FLORA_GENE_SHIFT=40.0`). Neutre 1.0 ⇒ aucun décalage.
L'étalement des dates ÉMERGE du pool-sol (variance à la levée férale + héritage),
sans code de sélection dédié → nectar soutenu au lieu d'un pic synchrone.
**Golden INCHANGÉ `98bdf772…`** : les plantes du smoke naissent avec `genes={}`,
leur vecteur n'est jamais sérialisé → l'ajout de clé ne les touche pas ; `gene()`
rend 1.0 pour la clé absente. Re-figeage prévu mais non nécessaire, annoncé.
population/vigueur inchangés, génétique 20/20.

### ④ Voix narratives + bancs d'acceptation (`46f188f`)
Encyclopédie (`CONCEPTS`) : concepts transversaux `succession` (bascule
pionnier→prairie, N3 dévoile la facilitation OM) et `phenologie_florale`
(étalement des dates, N3 relie au nectar soutenu) — 3 niveaux, voix naturaliste.
Banc neuf `etalement_floraison` (tapis mono-espèce de phacélies aux lignées
`phenologie_florale` étalées, oracle en tendance : ≥3 semaines de franchissement
distinctes, variance > 0 — pas de hash figé). Aucune espèce neuve → pas de 5 voix.
**Golden NEUTRE / INCHANGÉ `98bdf772…`** (corpus read-only hors tick, bancs hors
sim golden). Bancs biotiques **12/12** (étalement : 44 franchissements sur 4
semaines, variance 0.973) ; `succession_bascule` **6/6** (inchangé).

## Bilan
- **Golden final smoke `98bdf772…`** / population `e7f1cf19…`. Cascade maîtrisée :
  `ea135bf1…` (①) → `98bdf772…` (②, stable ③④).
- **S2 fermé** (étalement floral prouvé au banc), **S3 fermé** (bascule
  émergente prouvée au banc). Refactor auto-léger = no-op (tous les fichiers
  touchés en zone verte de code pur, max 243 lignes).
- **Point à surveiller (hors périmètre, non corrigé)** : les cultivées continuent
  de décliner face à une succession redevenue vigoureuse — ce n'est plus le
  verrou S3 (résolu) mais un équilibre cultivées vs adventices, à observer au F5.
- **Reste F5 = Nico** : rendu visuel de l'hétérogénéité du sol (`Maj+F6`) et
  calibrage des knobs (`OM_STABLE_INIT`, `INIT_AMPLITUDE`, seuils OM,
  `SEED_LATE_GAIN`, `FLORA_GENE_SHIFT`) ; bascule visée ~5-15 ans. Aucun C#
  touché (Python pur).
