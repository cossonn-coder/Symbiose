# CONCEPTION — Bugs d'émergence : floraison synchronisée (S2) + verrou de succession Capsella (S3)

> Figé le 2026-07-02 après diagnostic sim + arbitrage Nico (`/conception`).
> Deux comportements émergents indésirables observés au F5 / en sim longue,
> corrigés dans UN sprint à deux volets. Source de vérité = moteur Python
> (`data/code/`). Diagnostic reproductible : `/tmp/diag_symbiose.py <ans>`
> (jetable, monde complet, composition + banque-sol + champs an par an).

---

## Volet S3 — le verrou de succession (invasion Capsella)

### Symptôme
À ~5-6 ans, la bourse-à-pasteur (Capsella, pioneer) envahit tout et « bloque la
germination » : la succession n'avance jamais vers la prairie vivace, et les
plantes cultivées sont effacées. Sim du monde complet :

```
an  pion fixe gram comp cult   sbPio  sbFix  sdeep
 1   152   38   37   61   36    0.127  0.009  0.014
 3   601   16   32   38   17    0.393  0.007  0.037
 5   979   23    7    8    0    0.689  0.006  0.058   ← cultivées=0, ~95% Capsella
```

### Cause racine (confirmée)
Ce n'est PAS un effondrement de niche (`disturbance` relaxe vers ~0.5, stable).
C'est un **verrou de banque-sol** :

1. **Emballement pioneer** — `SeedBank.tick_disturbance_enrichment` pompe des
   graines pioneer CHAQUE semaine, sans aucune porte (disturbance ~0.5 permanent).
   `sbPio` sature vers 1.0.
2. **Tardifs jamais amorcés** — les archétypes tardifs (nitrogen_fixer, grass,
   competitor) n'entrent dans la banque QUE via `tick_late_succession_enrichment`,
   gaté sur `soil_memory_deep ≥ 0.2` (competitor ≥ 0.4). Or `soil_deep` monte de
   façon *décennale* (0.014 → 0.058 en 5 ans). Le seuil n'est jamais franchi avant
   ~15 ans → les tardifs n'entrent JAMAIS dans la banque.
3. **Cercle vicieux** — un tardif ne peut grener (`tick_plant_production`) que
   s'il germe ; il ne germe que s'il est dans la banque ; il n'y entre que via un
   trickle gaté sur un sol mûr, lui-même bâti par des plantes établies. Seul
   pioneer échappe au verrou. `germination_candidates` ne renvoie donc que
   pioneer, et `choisir_archetype` ne peut choisir que lui — quelle que soit la
   maturité réelle du sol.

Régression probable du **sprint germination thermique** (2026-07-01, suppression
de `spring_flush`) : la levée s'est concentrée dans la fenêtre chaude où Capsella
(fenêtre thermique la plus large et la plus froide : `t_germ_opt=11`, `tol=13`)
domine. D25 (« bascule prairie ~30 ans ») date d'AVANT.

### Fix retenu — direction C (facilitation écologique + D56)
Fidèle à la philo #2 (**flux → contrainte → réponse émergente**, jamais de
bascule scriptée) et #7 (hétérogénéité). Deux leviers couplés :

**(a) Facilitation par la matière organique.** Les pionnières *construisent* le
milieu (litière → `om_active`/`om_stable`). On remplace le signal décennal
`soil_deep` par un **indice OM réactif** (l'OM répond en une saison, `soil_deep`
en une décennie) pour amorcer les tardifs :
- `om_index = clamp((om_active + om_stable) / OM_FACILITATION_REF, 0, 1)` ;
- nitrogen_fixer & grass s'amorcent dès `om_index ≥ ~0.05` (un peu de litière
  déposée par les pionnières) ;
- competitor dès `om_index ≥ ~0.20` (sol bien bâti) ;
- gain relevé (`SEED_LATE_GAIN`) pour que les tardifs *accumulent* vraiment.

C'est la **facilitation** réelle de l'écologie de succession : le pionnier
prépare le lit du successeur. Déterministe (aucun RNG), O(plots) (boucle existante).

**(b) Bride de l'emballement pioneer.** L'apport pioneer par `disturbance`
DIMINUE à mesure que le sol se bâtit — les pionnières de sol nu n'inondent plus
la banque une fois le couvert installé :
`pioneer_gain = d · SEED_DISTURBANCE_GAIN · (1 − om_index)`.
Le tapis Capsella cesse de se sur-alimenter → les tardifs, désormais présents en
banque, prennent le relais. Bascule pionnier → prairie qui **émerge** du flux OM.

**(c) D56 — conditions initiales riches & hétérogènes.** Aujourd'hui
`om_active`/`om_stable` démarrent à 0 partout et les champs sont pauvres (monde
« fade », F5 S4). On enrichit les valeurs de départ (microbiome, un peu d'humus
`om_stable` hérité, NPK, humidité) AVEC hétérogénéité spatiale déterministe (hash
`tile_id + (r,c)` via `fields/noise.py`). Effet double : (1) monde vivant dès le
départ ; (2) certains secteurs ont assez d'OM initial pour amorcer les tardifs
plus tôt → **succession hétérogène** (philo #7), deux jardins jamais identiques.

---

## Volet S2 — la floraison synchronisée

### Symptôme
Toutes les plantes fleurissent la même semaine. Au-delà du visuel, `floraison`
alimente le nectar (`fields/population/registry._make_nectar_grid`) → les
pollinisateurs → le miel (`fields/apiculture`). Un pic synchrone unique = **boom /
bust** des pollinisateurs (famine hors-pic) au lieu d'un nectar soutenu.

### Cause racine (confirmée)
`sim/engine/floraison.py` : double porte GDD (`gdd_floraison`) + photopériode
(`bloom_daylen_*`), seuils **constants de classe** identiques pour tous les
individus. Température quasi uniforme sur la tuile → tous accumulent les mêmes
degrés-jours → franchissent la porte la même semaine. Aggravé par la levée
thermique synchrone (cohorte de printemps). **Aucune variation individuelle** du
déclenchement floral.

### Fix retenu — gène de phénologie florale
Précédent EXACT à répliquer : le gène `germination_thermique` (sprint 2026-07-01)
qui décale l'optimum de levée par individu. On ajoute un gène **`phenologie_florale`**
EN QUEUE de `GENE_NAMES` (garde-fou des canaux de hash), qui décale le seuil GDD
effectif de chaque pied :

```
gdd_eff = gdd_floraison − FLORA_GENE_SHIFT · (gene − 1.0)
```

Le gène est tiré du pool de la banque-sol (`sample_genes`, avec variance) → les
individus fleurissent à des dates **étalées** ; la sélection darwinienne
(pool-sol imprimé au terrain) fait dériver la lignée localement — **zéro code
dédié**, exactement comme le thermique. Nectar soutenu émergent, pollinisateurs
stables.

---

## Coût perf
Nul en pratique : toutes les modifs vivent dans des boucles O(plots) déjà
parcourues chaque semaine (ticks banque-sol, `_tick_floraison`, `init_eco`).
Aucun nouveau balayage géométrique. Budget largement respecté.

## Impact golden (cascade maîtrisée & annoncée)
Chaque tronçon qui change une trajectoire émergente **re-fige le golden**
(dérive localisée, expliquée) — même patron que le sprint germination thermique.
- **①** D56 : re-figé (conditions initiales du monde changées).
- **②** Rééquilibrage banque : re-figé (dérive de succession — c'est le but).
- **③** Gène floraison : re-figé MAÎTRISÉ (ajout d'une clé sérialisée ; à
  `FLORA_GENE_SHIFT=0` la sim est identique au démarrage, l'étalement émerge
  ensuite — preuve du ④ thermique).
- **④** Voix + bancs : NEUTRE (corpus read-only + bancs hors tick golden).

## Découpage (4 tronçons, perf-first, golden-gaté)
1. **① D56 — champs initiaux riches & hétérogènes** (`fields/ecofields/*`,
   `main.py`/`tests` si besoin). Foundation.
2. **② Rééquilibrage de la banque-sol** — facilitation OM des tardifs + bride
   pioneer (`fields/seedbank.py`, appelant `fields/ecofields/sol.py`) + banc
   « bascule pionnier→prairie ». Déverrouille S3.
3. **③ Gène `phenologie_florale`** — `plants/genetics.py` (GENE_NAMES) +
   `sim/engine/floraison.py` (décalage GDD par individu, grain propre + pool
   féral). Désynchronise S2.
4. **④ Voix narratives + bancs d'acceptation** — concepts `succession` /
   `phenologie` (encyclopédie/carnet) + banc étalement floraison. Golden neutre.

## Ce que ce sprint ne fait PAS
- Pas de nouvelle espèce (les 27 du catalogue suffisent) → pas de « 5 voix » à créer.
- Pas de refonte de la porte thermique de germination (elle est correcte ; c'est
  la banque-sol qui verrouillait).
- Pas de bascule scriptée / bonus direct sur plante (philo #1/#2 strictes).
