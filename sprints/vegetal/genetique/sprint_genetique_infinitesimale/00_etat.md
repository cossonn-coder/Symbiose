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
| ③ | `03_unites_compromis.md` — °C et semaines, compromis, banc « réponse à la sélection » | **FAIT** 2026-11-16 (non commité), golden RE-FIGÉ `07122393…` → `3927690e…` |
| ④ | `04_vue.md` — pont (unités + F), survol G, voix « lignée », banc F5 `lignees` | **FAIT** 2026-11-18 (non commité), golden INTACT `3927690e…`, pont 0.6.17 |

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

## Notes ③
- **Golden** `07122393…` → **`3927690e63786bafe77188881166e70c465d88952e77520dd8a1f64c02cdc2b3`**.
  `tests/population_hash.txt` `da7c9133…` → `0c795eb9…`. Dérive **prouvée = unités +
  compromis + tri** : en mémoire, avec (i) K_PREC neutralisé, (ii) σ_A germination ramené
  à 0,35 °C (= l'ancien 3,5 °C × 0,10), (iii) `gdd_par_semaine` fixé à 2 °C·j (= l'ancien
  FLORA_GENE_SHIFT 20 × 0,10) et (iv) le tri à la levée coupé, le log des 104 semaines est
  identique au bit près à HEAD, le digest hors gènes aussi, et le hash population retombe
  sur `da7c9133…`. Composition finale : T0 36 → 37 plantes (+1 bourse-à-pasteur), T1 21
  inchangé.
- Registre : `germination_thermique` = °C (neutre 0, σ_A 1,5, bornes ±6) ;
  `phenologie_florale` = semaines d'avance (neutre 0, σ_A 1, bornes ±4).
- **`sim/tempo.py` (neuf)** = la conversion partagée des 3 horloges : `seuil_floraison`
  (seuil − avance × `gdd_par_semaine(espèce)`, °C·j d'une semaine à l'époque où l'espèce
  fleurit, climat normal, mémoïsé par espèce), `semaine_abscission` et
  `onset_senescence` (ancien calibrage, avance / `SEMAINES_PAR_TEMPO` = 10 → σ_A 1 sem =
  l'ancien σ 0,10). Moteur (floraison, decompo, mortalité) ET miroir `semiologie` y
  passent. `T_BASE_FLORAISON` y est déplacé (ré-exporté par floraison.py), et
  `semaine_abscission` (ré-exporté par decompo.py, lu par le pont). `FLORA_GENE_SHIFT`,
  `GERM_GENE_SHIFT` : OBSOLÈTES, conservés.
- Calibrage mesuré : tournesol en moteur réel, avances −2/−1/0/+1/+2 sem. → floraison
  S13/12/11/10/9 (exactement 1 semaine par unité). Taux : noisetier 1,0 · pommier 5,0 ·
  phacélie 8,25 · tournesol 8,98 · la plupart 9,64 · armoise 11,2 °C·j/sem. Avant, σ 0,10
  décalait la floraison de 2 °C·j ≈ 0,2 semaine en été : l'étalement est ×5.
- Compromis : `PlantInstance.facteur_hauteur()` = gène hauteur × `facteur_precocite`
  (1 − 0,03·avance, borné [0,5 ; 1,5]) ; lu par les 2 `height_at` (herbacées + ligneux).
- Germination : lecture directe en °C (`t_germ_opt − gène`) aux 2 lecteurs de
  `succession.py`, défaut = neutre de l'espèce (avant : 1.0 codé en dur).
- Greffe : simple recopie de valeur, aucune hypothèse de neutre 1 → rien à changer.
- **Décision hors kickoff (à valider par Nico) — tri thermique à la levée férale**
  (`succession._levee_triee`) : la levée férale est décidée avec la MOYENNE du pool, puis
  les gènes sont tirés au hasard → le gène de l'individu n'était jamais lu au moment où il
  compte, la sélection ne pouvait pas mordre. Le semis est désormais tiré parmi les graines
  que CE sol a réveillées (produit de 2 gaussiennes, exact, O(1), même tirage z, aucun
  canal neuf). Réversible : une fonction + un appel.
- **Banc** `mesures/banc_reponse_selection.py` (seed 42). (a) 10 ans de friche seule, 1
  tuile 8×8 : témoin (T_MOY 11, gain solaire 15) → semis féraux moyens **+0,11 °C
  [n=96]** ; parcelle froide (T_MOY 7, sans gain solaire) → **+0,02 °C [n=80]** ; pool
  pondéré entre −0,18 et +0,06 °C. **Cible ≥ +1 °C NON atteinte : réponse nulle dans le
  bruit.** Enquête : (1) trou structurel ci-dessus, corrigé par le tri ; (2) même trié, le
  coefficient de tri σ²/(σ² + tol²/2) ≈ 0,05 (tolérances de levée 7-10 °C ≫ σ_A 1,5) ;
  (3) les levées arrivent quand le sol est AU voisinage de l'optimum (la cloche filtre),
  donc m* − μ ≈ 0 (moyenne opt − T_sol à la levée : −1,3 °C témoin, +2,3 °C froid) ;
  (4) ≈ 8-10 levées férales par an sur 64 plots (vivaces installées), et lever plus tôt ne
  rapporte rien ensuite (aucun avantage de saison). Ces leviers relèvent de la niche
  thermique (sprint ②, `sprint_niche_thermique`) : à reprendre là, ou à arbitrer par Nico.
  (b) 6 générations, 8 frères/génération : tomate F 0,50 → 0,66 → 0,88 → 0,94 → 0,97 →
  **0,98**, variance de hauteur 0,0049 → **0,00016** (÷30) ; courgette F 0,00-0,09, variance
  de hauteur 0,002-0,005 et de phénologie 0,2-0,7 sem² (reste bigarrée). La fixation des
  lignées autogames répond comme prévu.
- Tests : `tests/test_unites_compromis.py` neuf (19/19). Adaptés à la nouvelle unité :
  `test_caracteres` (les 2 caractères en vraies unités), `test_desync_phenologie` (appelle
  `sim/tempo` au lieu de recopier les formules en g − 1, + neutralité abscission),
  `test_floraison_forcage` (cohorte −2…+2 sem. au lieu de 0,70…1,30), banc
  `bancs/biotique.etalement_floraison` (±1,1 sem. ≈ même plage de seuils 29→47 °C·j).
- Non touché : `sim/seeds.PlayerSeedBank.mean_gene` garde un défaut 1.0 (aucun appelant ;
  juste pour un facteur). Le cache `gdd_par_semaine` suppose le climat normal : à revoir
  quand le climat deviendra un choix du lieu (BACKLOG « climats et lieux »).
- Batterie : 130/132 vertes. Rouges **préexistants à HEAD** : `test_peripherie` (connu) et
  `tests.bancs.test_edaphique` (carence « n reste bas », n=0,424 à HEAD comme après ③).
  Golden smoke : 5,3 s avant et après [1 run chacun, charge VM 0,5 puis 1,3].
- Taille : `sim/succession.py` 223 → 245 LDC, `sim/tempo.py` 34 LDC ; tout ≤ 300.

## Notes ④
- Repris d'une session du 2026-11-16 restée inachevée : l'existant était juste, complété et
  corrigé (ci-dessous). **Golden INTACT `3927690e…`** (moteur non touché hors voix).
- **Pont 0.6.17** : `F` par plante neuve (à côté de `genes`, même règle d'envoi en delta,
  cache `PontDelta.cs` + miroir `tests/simserver/delta.py`) ; clé de snapshot `caracteres`
  = `{unites: {nom: {unite, libelle, sens}}, ordre: [registre], lignee: {fixee, melangee}}`
  (`tools/simserver/genes_pont.py`, table construite une fois à l'import). Snapshot smoke
  seed 42, 6 semaines, 90 plantes : **identique à HEAD** hors `caracteres`, `F` et `perf`
  (chronos). Ajout de cette reprise : la liste `ordre` (le serveur sérialise avec
  `sort_keys`, le survol sortait les gènes par ordre alphabétique).
- **`sim/lignee.py`** (neuf, pur, sans import interne) : seuils F (0,75 / 0,25), catégorie,
  ligne de log `🫘 Ressemis de ma récolte [T] @(r, c) : espèce, cause` écrite par
  `planter` quand la graine porte des gènes (= récoltée ; sachets magazine/quêtes/bancs
  sans gènes, vérifié au grep), relue par `evenements` (kind `lignee`) et
  `maitrise_detection` (preuve « reproduction » du concept). Découverte au hook A du pont.
- Voix : concept « lignée » dans `encyclopedie_types.CONCEPTS` + fiche 3 niveaux dans
  **`sim/concept_corpus.py`** (écart au kickoff, qui citait
  `sim/encyclopedie_corpus/concepts.py` : ce dernier porte les phénomènes climatiques ;
  les concepts de MAÎTRISE vivent dans `concept_corpus.py`, aligné sur `CONCEPTS`).
  Carnet : `CONCEPT_DE` + 6 gabarits (3 causes × descriptif/interprétatif).
- **Survol G** (`WorldView.Genes.cs`) : lignée (« fixée / en voie de fixation / mélangée »,
  F affiché) puis chaque caractère dans son unité (°C, sem., %, ×facteur), ordre du
  registre. Label décalé à x = 72 (la palette de gestes le masquait).
- **Banc `lignees`** (`bancs/lignees.py`, départ S10, survol G ouvert au montage) : 8 tomates
  (6 générations précalculées par `heredite`) F 0,98, var. hauteur 0,00035 ; 8 courgettes
  F 0,00 (une à 0,50), var. 0,0061 ; 8 basilics du pool fondateur, F 0, var. 0,0073.
  **Correction de cette reprise** : sans garde, l'herbivorie tuait les 24 pieds en S15-S17,
  avant la fin du warmup F5 (capture : 1 seule plante à l'écran) → `sans_herbivorie(eco)`,
  patron de `houppiers`/`biotique` (D127). Après : 24/24 vivants à S22.
- Planche `planche/planche_04_survol_{tomate,courgette,basilic}_x2.png` (capture VM, ×2) :
  survol lisible, tomate « lignée fixée (F 0,98) · autofécondation 98 % », courgette
  « lignée mélangée (F 0,00) · 12 % ». Constat : les tomates restent petites à S22 et
  tous les pieds portent le signe « se fane par le pied, jaune-brun » (moteur, hors ④).
- Tests : `tests/test_lignee_voix.py` neuf (17/17, dont palier → interprétatif et crédit
  `detecter`) ; `test_sim_server` 349/349 ; heredite, unites_compromis, caracteres,
  encyclopedie, carnet, evenements, maitrise, journal, voix (champignon, périphérie,
  attente, dispersion), maitrise_detection, pages, magazine verts. `dotnet build` vert.
- Taille : `tools/simserver/serialize.py` **305 LDC 🟡** et `world/WorldView.cs` **301 🟡**
  (déjà au seuil, +2 et +1 lignes) ; tout le reste ≤ 300.

## Recette F5 (Nico)
Monter le banc **`lignees`** (le survol G s'ouvre seul ; G le bascule). À voir :
1. **Tomates** (rangée du fond, côté maison) : pieds semblables, survol « lignée fixée
   (F 0,98) », caractères presque identiques d'un pied à l'autre.
2. **Courgettes** (milieu, en quinconce) : tailles et floraisons dispersées, « lignée
   mélangée », valeurs qui varient d'un pied à l'autre.
3. **Basilics** (rangée avant) : diversité du pool sauvage, F 0.
4. Survol en unités : « optimum de levée −1,3 °C », « avance de floraison −1,0 sem. »,
   « autofécondation 98 % », « hauteur ×0,96 ».
5. Récolter une tomate puis la ressemer (`planter`) : au tick, le **carnet** note « J'ai
   semé … des graines de tomate tirées de ma récolte… » et l'**encyclopédie** gagne le
   concept « lignée ».

## REPRISE
**Sprint CLOS côté code** (①→④, golden `3927690e…`, pont 0.6.17). Reste : **F5 de Nico**
(recette ci-dessus), puis commit de ④ et `sprint_niche_thermique`. Décisions à valider :
celles de ② (a)(b) et le garde `sans_herbivorie` du banc `lignees`.
