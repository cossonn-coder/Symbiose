# Sprint GÉNÉTIQUE INFINITÉSIMALE — état (D139, sprint ① sur 3)

> Conception figée le 2026-11-16 : `docs/vegetal/genetique/conception_genetique_infinitesimale.md`
> (à lire en entier). Étude : `docs/vegetal/genetique/etude_genetique_realiste.md`.
> Suite : `sprint_niche_thermique` (②), puis `sprint_caracteres_vivants` (③), même dossier parent.

## But
Des gènes en vraies unités, une diversité qui vient du brassage, des lignées qui se fixent
(autogames) ou se mélangent (allogames), et des gènes qui coûtent.

## Décisions clés (Nico, 2026-11-16)
- G1 Modèle infinitésimal (option B de l'étude). G2 Brassage = ½σ_A²(1−F̄), mutation = filet.
- G3 Consanguinité F par plante. G4 `autofecondation` = gène (taux par plante).
- G5 Compromis : dépression de consanguinité (allogames) + précocité ↔ taille.
- G6 Multiplier les gènes autant qu'il faut (≈ 0,1 % de tick par gène [smoke, cProfile]).
- Ajout de gènes **en queue** seulement (canaux de hash positionnels).

## Golden
Départ `b4a921f8…` (`data/code/tests/golden_hash.txt`). ① INTACT · ② **RE-FIGÉ LARGE
annoncé** (toutes les valeurs de gènes changent) · ③ **RE-FIGÉ annoncé** (unités +
compromis) · ④ INTACT. Chaque re-figeage : dérive expliquée et consignée ici avec le hash.

## Tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_registre.md` — registre des caractères, neutre par caractère, bornes | **FAIT** 2026-11-16, golden INTACT `b4a921f8…` |
| ② | `02_heredite.md` — brassage, F, autofécondation, fondateurs, variétés, banque | **FAIT** 2026-11-16, golden RE-FIGÉ `b4a921f8…` → `07122393…` |
| ③ | `03_unites_compromis.md` — °C et semaines, compromis, banc « réponse à la sélection » | à faire |
| ④ | `04_vue.md` — pont (unités + F), survol G, voix « lignée », banc F5 `lignees` | à faire |

## Notes ①
- Registre = `plants/caracteres.py` (pur, sans import interne) : `Caractere` (unite, neutre,
  sigma_a, bornes, adaptogene), table `CARACTERES` ordonnée, helpers `parametres_espece`
  (helper UNIQUE neutre/σ_A effectifs), `neutre`, `sigma_a`, `borne`. Ré-exportés par
  `plants.genetics` et `plants`. `GENE_NAMES = tuple(CARACTERES)` ; `GENE_INIT_SIGMA` et
  `GENE_HARD_MIN/MAX` dérivés du registre.
- `PlantBase.genetique = {}` (familles.py). `PlantInstance.gene()` : absent → `neutre(nom,
  plant_class)`. ⚠ un nom hors registre lève désormais `KeyError` (avant : 1.0) — tous les
  appelants actuels lisent des noms de `GENE_NAMES` (vérifié au grep).
- `borne(nom, x)` remplace `clamp_gene` dans `child_genes`, `founder_genes`,
  `sample_genes`, `expressed_gene`. `clamp_gene` reste exporté (bancs, tests).
- `GeneStat` des gènes (banque-sol + `seed_founder_pool`) part de `neutre(g, espèce)`.
  Non fait au ① (laissé au ②) : `founder_genes`/`seed_founder_pool` tirent encore autour
  de 1.0 avec `GENE_INIT_SIGMA` global (pas encore le σ_A d'espèce).
- Test neuf `tests/test_caracteres.py` (30/30). Suites génétique/plasticité/diversité/greffe vertes.

## Notes ②
- **Golden** `b4a921f86d6e…` → **`07122393662be0d37c978066d147d7f3f00a176d1daac6c6eea731235d9f58c8`**.
  `tests/population_hash.txt` `5a6b5135…` → `da7c9133…`. Dérive **prouvée génétique** :
  sous l'ancienne loi (monkeypatch : ancien `child_genes`, fondateurs sans
  `autofecondation`, variétés = fondateurs), le log des 104 semaines est identique au bit
  près à HEAD, le digest ne diffère que par la clé `autofecondation`, et le hash
  population retombe sur `5a6b5135…`. Composition finale quasi inchangée (T0 36 plantes,
  T1 20 → 21).
- Registre : `autofecondation` en queue (probabilité, [0, 1], σ_A 0,05), neutre déduit de
  `pollination_mode` via le champ `Caractere.neutre_par_pollinisation`.
- `sim/reproduction.heredite(mère, père, seed, week) → (gènes, F)` (formules §4 ; z₁ =
  canal historique, z₂ filet et choix croisé/autofécondé = canaux décalés en `r`).
  `child_genes` reste (= `heredite(...)[0]`). `SELFING_SIGMA_RATIO`, `MUTATION_SIGMA` :
  marqués OBSOLÈTES, conservés. `H_MUT`, `DI` dans `plants/genetics.py`.
- `PlantInstance.F` ; `depression_consanguinite()` multipliée aux 2 sites de `cout_defense`
  (croissance, convalescence). F voyage : tampons merle/caches (F **en fin de tuple**),
  `GrainEnAttente.F`, `grain_sauvage(..., F)`, `Seed.F` (JSON : omis si 0, relu avec 0 par
  défaut), banque-sol `rec["F"]` + **`sample_F`** (fonction sœur de `sample_genes`, qui
  garde son retour dict : moins d'appelants touchés). Clones (rejet, bouture, ramet) : F
  de la mère. Greffe : `autofecondation` passe en **gène aérien**, et F = celui du greffon.
- Fondateurs : `neutre + σ_A·z` ; `seed_founder_pool(sigma=None)` → σ_A d'espèce.
  Variétés : `fields.variete_genes` (semis `semer_fondateur` et graine `planter` sans
  gènes). `semer_fondateur(..., sauvage=True)` pour la mare initiale (flore sauvage).
- **Décisions hors kickoff (à valider par Nico)** : (a) le catalogue ne connaît que 2
  espèces `self` → tomate, haricot, blé et bourse-à-pasteur reçoivent la surcharge
  `genetique = {"autofecondation": {"neutre": 0.95}}` (sinon « les tomates se
  ressemblent » ne pouvait pas arriver) ; (b) la graine **récoltée** (banque-joueur)
  devient un descendant (`heredite`) et non plus une copie de la mère, pour que la lignée
  se fixe au fil des ressemis.
- Perf [smoke cProfile, VM chargée à 1,1-1,8] : 13,17 s avant, 13,42 et 12,74 s après. La
  génétique cumule ≈ 0,04 s (≈ 0,3 %). Budget ≤ +2 % tenu.
- Tests : `tests/test_heredite.py` neuf (19/19). Tests adaptés à la nouvelle loi :
  `test_genetique` (introgression : croisement forcé, la tomate est autogame),
  `test_diversite_fondatrice` (variance sur les facteurs seulement), `test_caracteres`
  (nouveau caractère), `test_merle_seme` (tuple du tampon + F). Toute la batterie est
  verte, sauf `test_peripherie`, **rouge déjà à HEAD** (préexistant, hors périmètre).
- Taille : `fields/seedbank.py` passe de 278 à **308 LDC (🟡)** ; `sim/engine/boucle.py`
  de 311 à 316 (🟡, déjà au-dessus avant).

## REPRISE
Lire `CLAUDE.md`, ce fichier, puis le kickoff du premier tronçon « à faire » (③).
