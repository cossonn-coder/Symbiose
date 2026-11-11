# sprint_zoochorie — carnet de bord de conception (D42)

**Sujet** : dispersion animale des graines (D42) — le merle mange un fruit et sème
ailleurs ; le geai cache des glands et en oublie (décision Nico 2026-11-06 :
« merle, geai », suite de la relève ligneuse D130).
**Phase** : **CONCEPTION FIGÉE** le 2026-11-09 (« on suit ta reco »), prêt pour
`/sprint-auto sprint_zoochorie`. Doc : `docs/faune/vie_macro/conception_zoochorie.md`.
Golden de départ `a10b7225…` ; **re-figé au ⑥ seulement** (mulot → rapace/couleuvre).

## Constats vérifiés au code (2026-11-09)
1. Deux systèmes de fruits sans lien : les **fruits traçables** (`sim/engine/decompo.py
   _tick_fruits` : nouaison, maturation, chute en litière `fruit`) et la **recrue
   abstraite** (`sim/engine/mortalite.py _reproduction` : tirage hebdo
   `reproduction_rate`, toute l'année, sans lien avec les fruits).
2. Le merle (`fields/population/registry.py`, `resources._merle_food_grid`) lit le
   fruit **tombé** (litière `fruit`, fraîcheur ≤ 3 sem) + lombric. Il ne **retire**
   rien : aucune faune ne consomme de fruit. Habitat uniforme 0,20, `lisiere_w` 0,25.
3. Graines d'arbre déposées en banque-sol (`add_species`) : **jamais germées** — la
   germination férale ne passe que par les archétypes (`germination_candidates`).
   Seule recrue d'arbre = directe, sous la couronne du parent (relève ②).
4. Véhicule existant idéal : `GrainEnAttente` (`fields/seedbank.py`) — gènes PROPRES,
   `expression` (priming), position sous-plot, levée différée gatée niche/lumière ×
   tolérance/pH/T_sol/allélopathie (`sim/succession._lever_grains_en_attente`).
   Manques : pas de viabilité (un grain attend pour toujours), `cultive=True` par
   défaut, aucun plafond par plot.
5. Fruitiers traçables : figuier (stérile), pommier, cerisier, noyer ; tomate,
   courgette, fraisier, framboisier. Chêne, hêtre : **pas de fruits traçables**.
   Myrtille (`Vaccinium`), lierre : non fruitiers au moteur.
6. Faune : pas de geai, d'écureuil ni de mulot. Ceinture `foret` : `densite_ligneuse`
   par secteur, apport à la banque via `tick_apport_peripherie` (archétype
   `competitor`, sans espèce).
7. Golden smoke : Tomato (meurt S2-3) + AppleTree (< 5 ans) → aucun fruit mûr →
   frugivorie neutre attendue. À revérifier au tronçon.
8. Boucle par tuile (`boucle.py` l.221) ; chaque tuile a `origin_x_cm/origin_y_cm`
   → une graine peut changer de tuile (monde 20×20 m < portée d'un merle).

## Décisions arrêtées (Nico, 2026-11-09)
- Q1 périmètre : **merle + geai + écureuil + mulot** (4 disperseurs). Rôles proposés :
  merle = endozoochore (baies, sème sous les perchoirs) ; geai = caches de glands /
  faînes / noix en terrain découvert, longue portée (ceinture → jardin) ; écureuil =
  caches dispersées près des arbres, portée moyenne, arboricole ; mulot = caches
  courtes sous couvert + prédateur de graines au sol, proie du rapace/couleuvre.
- Q2 **unifié** : pour les espèces zoochores, la recrue passe par les VRAIS fruits
  (tombé → graine au pied, mangé → graine au loin) ; `_reproduction` abstraite
  retirée pour elles. Recalibrage de la relève (D130) accepté.
- Q3 graine du merle sous les perchoirs naturels **+ geste « poser un perchoir »**.
- Golden : une guilde neuve (mulot surtout, proie du rapace) peut faire dériver le
  smoke → re-figeage probable, à vérifier au code et annoncer au kickoff.

- Q4 (lot 2) **chêne + hêtre fruitiers** (glands/faînes traçables) **+ noisetier
  ajouté** au catalogue (5 voix, chatons = nectar de soudure T6).
- Q5 **mulot prédateur de graines** (au sol + grains en attente) **+ années de
  glandée** (masting déterministe par espèce/an → satiation des prédateurs).
- Q6 graine tombée au pied = `GrainEnAttente` aussi (levée par la niche) ; fin de
  la pose directe « plot le plus lumineux » pour les zoochores.
- Sans question (bio, décidé par Claude) : durée de vie des grains sauvages par
  espèce ; dormance (noyau, gland → printemps suivant) ; plafond de grains par plot.

## Tronçons
| # | kickoff | golden | état |
|---|---|---|---|
| ① | `01_grain_sauvage.md` — `GrainEnAttente` sauvage : dormance, péremption, plafond | inchangé | **fait** 2026-11-09 |
| ② | `02_chute_unifiee.md` — fruit tombé → grains ; `_reproduction` coupée pour les fruitiers pérennes ; chêne/hêtre fruitiers ; glandée ; recalibrage relève | inchangé | **fait** 2026-11-09 |
| ③ | `03_noisetier.md` — espèce neuve + 5 voix | inchangé | **fait** 2026-11-09 |
| ④ | `04_merle_perchoirs.md` — `sim/zoochorie.py`, prise saturante, grille perchoir, tampon monde, geste `poser_perchoir` | inchangé | **fait** 2026-11-11 |
| ⑤ | `05_geai_ecureuil.md` — 2 guildes `disperseur`, caches + oubli, apport ceinture | inchangé | **fait** 2026-11-11 |
| ⑥ | `06_mulot.md` — guilde, prédation saturante des grains, caches ; proie rapace/couleuvre | **RE-FIGÉ** `b4a921f8…` | **fait** 2026-11-11 |
| ⑦ | `07_voix_mesure.md` — événements, carnet `dispersion`, signes ; 200 ans verger_mur + banc `nucleation` ; calibrage | inchangé depuis ⑥ | à faire |
| ⑧ | `08_vue_godot.md` — faune, fruits à coque, noisetier, perchoir, banc F5 ; clôture D42 | inchangé | à faire |

## Coût perf (estimé)
Frugivorie : boucle sur les fruitiers mûrs (quelques plantes) ; pose : un tirage
pondéré par plot sur une grille « perchoir » (couronnes ligneuses) déjà connue
(`foliar_plots`). Grains : plafond par plot. Attendu ≪ +10 % de tick.

## Tronçon 1 — fait (2026-11-09)
- `GrainEnAttente` + `origine`/`levee_des`/`perime_a` (défauts = grain joueur, au bit
  près) ; `grain_sauvage(cls, …)` et `deposer_grain_sauvage(tile, r, c, grain)` dans
  `fields/seedbank.py`, plafond `GRAINS_SAUVAGES_MAX_PLOT = 3` (sauvages seuls).
- **Écart au kickoff** : `species` porte la **clé catalogue** (« pommier »), pas
  `cls.__name__` — la levée lit `PLANT_CATALOGUE.get(species)`. Résolue par reverse
  lookup (import local de `plants` dans `grain_sauvage`).
- Dormance : `levee_des` = wiy 1 de l'année suivante (un dépôt PILE au wiy 1 attend
  un an). Trait `graine_viabilite_ans` (défaut 1 ; pommier/cerisier 2, fraisier 3,
  framboisier 5 [ordres de grandeur]).
- Levée : purge des périmés (`week >= perime_a`, silencieuse), plus ancien grain
  éligible (ordre d'insertion), log `🌱 Levée (semé par <origine>)` hors joueur.
- Sauvegarde : `grains_en_attente` n'est sérialisé nulle part (ni save ni pont) →
  rien à porter.
- `tests/test_grain_sauvage.py` 18/18 ; contre-factuel (e) : levée semaine 4, ancien
  et nouveau code [1 scénario]. Golden `a10b7225…` INCHANGÉ ; evenements, carnet,
  encyclopedie, planter, plasticite, paillage, bancs.test_verger_mur verts.
- `plants/base/familles.py` à 293 LDC (🟢).

## Tronçon 2 — fait (2026-11-09)
- Prédicat unique `recrue_par_fruits(cls)` (`sim/reproduction.py`) = fruitier ∧ pérenne
  ∧ `graine_fertile` : pommier, cerisier, noyer, fraisier, framboisier, chêne, hêtre.
  `_reproduction` : `continue` pour eux (ni pool banque-sol ni recrue directe).
- `decompo.semer_chute` appelé par `deposer_fruits(…, seed, week)` : `n = nombre ×
  P_GRAIN_CHUTE`, fraction par hash canal `week*73`, plots foliaires (arbre) / pied
  (herbacée), gènes `child_genes(mère, find_father)`, `child_expression`, x/y None.
- Glandée : trait `glandee_periode_ans` (chêne 4, hêtre 6), `facteur_glandee` (CRC du
  nom, canal r=7907), `GLANDEE_MAIGRE` 0,15, multiplie `frac` avant `nouer`.
- Chêne/hêtre fruitiers : 80 glands/site × 0,012, 150 faînes/site × 0,002 ;
  **maturation 7 sem (pas 15)** : le moteur noue le chêne vers wiy 21 [1 scénario] ;
  à 15 sem le gland tombait wiy 40 (hiver), à 7 il tombe wiy ~30 (mi-oct.).
  Encyclopédie niveau 2 chêne/hêtre : glands/faînes + glandée.
- **Calibrage** (`diag_releve` verger_mur, seed 42, 200 ans, [n=1 run par valeur]) :
  P 0,02 → fourré 18 ✗ ; 0,008 → fourré 12 ✗ ; **0,005 retenu** → fourré 9 [marge 1],
  remplacement noyer 2,5 · pommier 31 · cerisier 322 ; vivants an 200 : cerisier 47,
  noyer 3, pommier 0, figuier 1. Les grains lèvent bien dans ce banc.
- **À surveiller** : fraisier/framboisier (herbacées, 1 fruit = 1 cohorte) ne sèment
  presque plus (400 fruits pour 2 grains) — leur relève reste clonale (stolons,
  drageons) ; un chêne de lab (structure neuve) noue ~10 glands [1 scénario].
- Tests : `test_chute_seme.py` 4/4 ; `test_banque_semis` (d)/(e) portés sur un
  charme (recrue directe toujours vivante pour les non-fruitiers) ; grain_sauvage,
  fruits, encyclopedie, evenements, carnet, genetique, figuier_realiste,
  bancs.test_verger_mur verts. Golden `a10b7225…` INCHANGÉ.
- Perf `full` 5 ans, tick médian an 3-5 : 1006,5 → 1011,9 ms (+0,5 %) [n=1, charge VM
  0,6 → 2,9 pendant la mesure].
- LDC : decompo 177, reproduction 82, mortalite 257, familles 294, forestiers 161 (🟢).

## Tronçon 3 — fait (2026-11-09)
- `HazelTree` dans `plants/perennials/forestiers.py` (199 LDC 🟢, section « arbuste de
  haie »), clé catalogue `"noisetier"`, ré-export `plants.perennials`, ajouté aux bancs
  `houppiers` (12ᵉ place (27,35)) et `foret_ports`. Betulaceae, cépée approchée par
  `buissonnant` (pas d'archétype multi-tiges, mono-collet comme le figuier),
  `rejet_souche` 0,9, `maturity_years` 8, `glandee_periode_ans` 2, `fruits_par_site` 25
  (~40-45 sites à 10 ans [1 forme par banc]), 0,006, maturation 18 sem.
- **Prémisse réfutée — chatons en février impossibles** : wiy 1 = équinoxe et le forçage
  floral (`gdd_accum`) repart à 0 à wiy 1 → aucune espèce ne fleurit avant fin mars.
  Retenu : `bloom_forcing_gdd` 1,0 → chatons wiy 1 (saule wiy 3) [seed 42]. Février
  demanderait de faire courir le forçage d'une année sur l'autre (mécanisme neuf) :
  reliquat pour ⑧/F5, pas de dette ouverte.
- **Pollen précoce aux butineurs** : aucun canal par espèce (`pollen_vibre` = par
  famille, bourdon seul ; brancher Betulaceae toucherait bouleau/charme du monde `full`)
  → non branché, noté dans la docstring.
- **Événements** : nouaison et abscission couvertes ; la floraison n'a pas de marqueur
  par plante (TODO(voix) existant d'`evenements.py`) et la ligne `Chute fruit` n'est pas
  parsée → à poser au ⑦ avec `dispersion`. Carnet : `CONCEPT_DE` indexé par (kind, cause),
  rien à ajouter. Signes et voix des êtres non indexés par espèce. Magazine : automatique
  (famille Betulaceae + fiche).
- Voix : fiche encyclopédique 3 niveaux (`ligneux.py`, test corpus 51 → 52), page P50
  « La baguette de coudrier » (voix C, concept `eau`).
- Effet en jeu (2 pieds de 10 ans, 2,5 ans, [1 scénario seed 42]) : nouaisons 182 /
  691 / 48 fruits (glandée maigre-forte-maigre), noisettes tombées wiy 28 (~début oct.),
  1 semis de noisetier levé l'an 2.
- Tests : `test_noisetier` 4/4 ; encyclopedie 70/70, carnet 19/19, evenements 46/46,
  pages 77/77, croissance 134/134, magazine, peripherie_voix, chute_seme, grain_sauvage
  verts. Golden `a10b7225…` INCHANGÉ.

## Tronçon 4 — fait (2026-11-11)
- `sim/zoochorie.py` (118 LDC) : `merle_prend` (par tuile, 15c-bis après `_tick_fruits`)
  + `merle_seme` (une fois, 17a-bis après la boucle des tuiles). Trait `mange_par`
  (défaut `()`, `familles.py` 295 LDC) = `("merle",)` sur cerisier, framboisier, fraisier.
  Placeholders `TAUX_PRISE` 0,15, `APPETIT` 25 fruits/unité de densité/sem, `P_TRANSIT`
  0,05 (calibrage ⑦). Seuil mûr `1 − 1e-9` (7 × 1/7 < 1,0 en flottant). Canal `week*83`.
- **Écart au kickoff** : TOUTES les graines passent par le tampon (pas seulement celles
  d'une autre tuile), et la grille perchoir est calculée au vidage, sur l'état de fin de
  tick du monde : l'ordre des tuiles ne décide rien (testé). Clé `zoochorie_tampon`
  créée au besoin et retirée au vidage (rien au save). Log par plante `🐦 Merle : <n>
  fruits pris sur <espèce>@<pos>` + une ligne de semis par tick `🐦 Merle : <n>
  graine(s) semée(s) sous les perchoirs`.
- Geste `poser_perchoir` (200 cm, « fin ») : coût MODÉRÉ, technique `perchoir`
  (TECHNIQUES + fiche 3 niveaux), fiche geste, déblocage `action poser_tuteur` ou
  `maitrise perchoir 1`. `support_compatible("…", "perchoir")` → False (aucune grimpante
  ne s'y accroche, aucun plantage). **Prémisse réfutée** : `poser_tuteur` n'a AUCUNE
  route au pont (réponse « verbe inconnu ») ; `poser_perchoir` reçoit sa propre branche
  dans `tools/simserver/actions.py` (342 LDC 🟡), pont **0.6.11**. Tuteur/treillis/pergola
  restent non routés : à trancher (⑧ ou dette).
- Effet `full` seed 42, 5 ans [n=1 run] : cerises prises 136 / 133 / 126 / 83 (ans 2-5),
  23 graines semées, 10 grains `merle` en attente en fin de run.
- Perf `full`, tick médian ans 3-5 : avec 852 / 890 / 900 ms, sans 949 / 900 / 882 ms
  [n=1, charge VM 2 à 5] → écart dans le bruit.
- Tests : `test_merle_seme` 18/18 ; encyclopedie 70/70, deblocage 24/24, grimpe, chute_seme,
  grain_sauvage, fruits 30/30, acquisition_outils, test_sim_server 322/322 verts.
  Golden `a10b7225…` INCHANGÉ. C# non touché (glyphe/rendu du perchoir au ⑧).
- `geste_corpus.py` 353 LDC 🟡 (corpus, une seule responsabilité).

## Tronçon 5 — fait (2026-11-11)
- Guildes `geai`, `ecureuil` (catégorie neuve `disperseur`, lue par personne — grep
  `category_density(` vérifié), sels 0x2B4001/0x2B5001, insérées avant les super-prédateurs,
  fenêtre large, rampe thermique −5→5 °C, `lisiere_w` 0,35 / 0,20. Ressource/habitat dans
  **`fields/population/disperseurs.py`** (neuf, 57 LDC) : `resources.py` (379 LDC) aurait
  passé 400. `registry.py` 327 LDC 🟡 (registre, une responsabilité).
- **Écart au kickoff** : « cimes connexes » = voisinage 3×3 touché par ≥ 2 couronnes
  DISTINCTES (ligneux vivants ≥ 300 cm). La règle « ≥ 2 voisins foliaires » rendait tout
  grand arbre isolé habitable (couronne de chêne 10 ans ≈ 97 plots).
- `mange_par = ("geai", "ecureuil")` sur chêne, hêtre, noyer, noisetier. `sim/zoochorie.py`
  : prise généralisée en `prendre(…, nom, taux, appétit, decal)` (merle bit-identique,
  18/18). **`sim/caches.py`** (neuf, 154 LDC) : `caches_prennent` (15c-ter, geai puis
  écureuil sur le reste) + `caches_sement` (17a-ter : découvert monde / anneau de lisière
  ≤ 1500 cm + apport ceinture). Canaux `week*83 + 2…7`. Tampon `zoochorie_caches`, retiré
  au vidage. Placeholders ⑦ : TAUX 0,15, APPÉTIT geai 40 / écureuil 30, P_OUBLI 0,10,
  LUM_DECOUVERT 0,5, BONUS_REPERE 2, APPORT_CEINTURE 15 (4 → 0 gland en 4 ans).
- Ceinture : chêne toujours + hêtre si essence `hetre` (y compris ripisylve : non filtré),
  gènes `founder_genes` au plot, `origine="ceinture"`.
- Effet `full` seed 42, 5 ans [n=1 run] : **inerte** — aucun arbre à coque, ceinture sans
  `foret` ; geai moyen ≤ 0,10, écureuil ≤ 0,08 (aucun lecteur). Perf ans 3-5 avec / sans :
  1437/1418/1388 vs 1401/1425/1371 ms [n=1, charge VM 2 à 15] → bruit.
- Effet `verger_mur` (2 noyers) + ceinture nord `foret`/hêtre 0,9, 4 ans [n=1 run, seed
  42] : noix prises geai 172 / écureuil 111 (an 4 cumulé), 14 + 13 oubliées, levées
  geai 5 · écureuil 5 ; ceinture 17 glands/faînes (dont 15 l'an 4 = glandée), 2 levées.
- **À calibrer (⑦)** : la satiation ne mord qu'au-delà de ~267 fruits par plot de couronne
  (APPÉTIT/TAUX) — aucune glandée du moteur actuel n'y arrive ; test (e) en scénario forcé.
- Pont : `sprites` porte 2 espèces de plus (22) ; C# retombe sur `EspeceInconnue`
  (glyphe à faire au ⑧). Pas de bump de version. C# non touché.
- Tests : `test_geai_ecureuil` 18/18 ; faune_dediee, population, merle_seme, peripherie
  71/71, sim_server 322/322, signes_legende, infobulle_vivant, encyclopedie, evenements,
  carnet, fruits, attraction, chute_seme, grain_sauvage, noisetier, banque_semis verts.
  Golden `a10b7225…` INCHANGÉ.

## Tronçon 6 — fait (2026-11-11)
- Guilde `mulot` (catégorie `disperseur`, sel 0x2B6001, avant les sommets, fenêtre large,
  rampe −5→5 °C, `lisiere_w` 0,25, `predators=("rapace","couleuvre")`). Ressource/habitat
  dans **`fields/population/mulot.py`** (neuf, 38 LDC) : grains sauvages/3 + fruit tombé
  (tout âge) ×0,5 + banque-sol LUE ×0,3 ; habitat = couronnes ligneuses 0,30 + piles,
  décoré `_avec_abri_paillage`. Rapace et couleuvre : `"mulot"` ajouté à `_proies_grid`.
  Encyclo faune `mulot` (liens symétriques rapace/couleuvre + 5 arbres), `FAUNE_VU`/
  `FAUNE_ROLE` (+ rôle couleuvre « chasse rongeurs et limaces »).
- **Écart au kickoff** : la prédation vit dans **`sim/mulot.py`** (neuf, 79 LDC), pas
  dans `sim/zoochorie.py` (autre responsabilité), appelée UNE fois par tick à l'étape
  **17a-quater**, APRÈS `caches_sement` : tous les dépôts du jour (chute 15c, merle,
  caches, ceinture) sont posés. Tuiles indépendantes (cache dans la même tuile).
  Placeholders ⑦ : `PRED_MAX` 0,5, `A_SATIATION` 40 grains/tuile, `P_CACHE_MULOT` 0,15,
  `R_CACHE_CM` 300 ; couvert de cache = max(couverture_sol, habitat), sans couvert → mangé.
  Canal `week*89` (libre, grep). Grain caché : `origine="mulot"`, dormance/péremption
  conservées ; plafond ① refuse → mangé. Grains `joueur` jamais touchés.
- **Golden re-figé** `a10b7225…` → `b4a921f8…` ; `population_hash` `0556d1c1…` →
  `5a6b5135…`. Dérive smoke (moyennes/plot, an 1 / an 2, avant → après) : rapace
  0,0273→0,0285 / 0,0216→0,0247 ; couleuvre 0,0187→0,0197 / 0,0175→0,0202 ; campagnol
  0,0936→0,0932 / 0,1003→0,0991 ; limace 0,0373→0,0372 / 0,0608→0,0603 ; merle −0,1 %.
  Digest : aucune plante ne change de stade/vie ; `growth_factor` ~1e-4, 4 `vitalite`
  au 1e-4, `soil_memory`/`k`/`p` au 3ᵉ décimale. Aucun grain sauvage au smoke (0 ligne
  mulot). **Contre-factuel** : mulot gardé mais retiré des proies → hash = `a10b7225…`
  exact → dérive 100 % chaîne rapace/couleuvre.
- Effet `full` seed 42, 5 ans [n=1 run] : grains mangés 1/12/15/14/11, cachés 0/1/1/2/0 ;
  grains sauvages en attente en fin d'an 0-2 (sans prédation : 13/27/31/24). **À calibrer
  au ⑦** : hors glandée le mulot vide presque tout le stock — vérifier que la relève D130
  (200 ans verger_mur) tient.
- Perf : grilles mulot 3,8 ms/tick + passe 0,01 ms [n=20 itérations, monde full] ;
  la mesure macro avec/sans (1433-1532 vs 929-976 ms) est faussée par la charge VM
  (15 → 4 pendant la mesure), non concluante.
- Tests : `test_mulot` 12/12 ; faune_dediee (DISPERSEURS + jeton `cerisier`), population
  (hash re-capturé), signes_legende 42/42, sim_server 322/322 (23 espèces), stress_chronique,
  evenements 46/46, geai_ecureuil, merle_seme, encyclopedie 70/70, infobulle 31/31,
  grain_sauvage, chute_seme, carnet, bancs.test_verger_mur verts. C# non touché (sprite
  `mulot` → `EspeceInconnue` jusqu'au ⑧).
- LDC : registry 338 🟡 (registre), signes_corpus 227, boucle 311.

## §REPRISE
Prochain : ⑦ `07_voix_mesure.md` (golden `b4a921f8…`). `sim/mulot.py` = prédation des grains (17a-quater) ; placeholders mulot à calibrer avec ceux de ④⑤. `sim/zoochorie.prendre` = prise saturante générique ; `sim/caches.py` = caches + oubli + `_semer` (grille pondérée, gènes fondateurs si `None`) ;. Lire `CLAUDE.md`, ce fichier, le doc de conception, puis le premier kickoff « à
faire » du tableau. Chaque tronçon met à jour sa ligne + une section « Tronçon N —
fait » courte (constats chiffrés avec leur limite entre crochets).
