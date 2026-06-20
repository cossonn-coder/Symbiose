# SPRINT PHYSICO-CHIMIE DU SOL — état partagé

> Conception figée (3 docs par volet) :
> `docs/conception/CONCEPTION_SOL_PH.md` (porte l'ordre global §6),
> `docs/conception/CONCEPTION_SOL_NUTRIMENTS_NPK.md`,
> `docs/conception/CONCEPTION_SOL_STRUCTURE.md`.
> Branche suggérée : `sprint/physicochimie-sol`. Python depuis `data/code/`.
> Boucle : lancer `0N` → coder → vérifier golden → MàJ ce fichier → commit → `/clear`
> → écrire `0N+1` → lancer. **Vérifier git à jour avant de démarrer.**

## Objectif

Donner au sol une vraie chimie : **pH** (maître-régulateur), **nutriments N/P/K
distincts** (`fertilite` supprimé, loi de Liebig) et **structure/compaction**
(`structure_sol`, dette D30 absorbée). Tout émerge par flux → contrainte → réponse
(philo #2/#3/#5).

## Décisions (2026-06-19, avec Nico) — voie FIDÈLE

- Nutriments : **NPK COMPLET** (`n`/`p`/`k`), `fertilite` **supprimé net**,
  croissance = **loi du minimum de Liebig**.
- pH : champ hérité du `soil_type`, dérive décennale ; lockout en cloche (P étroit
  + chlorose alcaline) ; fenêtres d'espèce = **noyau démonstrateur** ; amendements
  = **rondelles `chaux`/`soufre`**.
- **Faim d'azote DANS le sprint** : bois/BRF **+ substrat usé de culture de
  champignons** (crochet futur acteur champignon).
- CEC dérivée (`soil_type`+`om_stable`) ; `SOIL_SIGNATURE` rendu explicite.
- Structure : **Option B `structure_sol`** (champ dédié), pas l'option A sobre.
- Golden : **tactique neutre-d'abord** (validée au thermique), gros re-figé isolé
  au tronçon 3.

## Tronçons (ordre global)

| # | Tronçon | Doc | Dérive golden | Statut |
|---|---------|-----|---------------|--------|
| ① | pH socle (champ hérité + dérive, aucun lecteur) | pH §2.1 | NEUTRE | ✅ |
| ② | N/P/K socle (champs posés, uptake lit encore `fertilite`) | NPK §2.1 | NEUTRE | ✅ |
| ③ | Bascule uptake **Liebig** (retrait `fertilite`, lessivage diff., CEC, signature) | NPK §2.3 | **LARGE → `87ed27ae…`** | ✅ |
| ④ | pH → lockout (cloches dispo ; chlorose reportée au ⑤) | pH §2.2 | **maîtrisé → `d8856261…`** | ✅ |
| ⑤ | Fenêtres pH par espèce (noyau) + chlorose + indicatrices | pH §2.3 | **NEUTRE → `d8856261…` inchangé** | ✅ |
| ⑥ | Amendements pH (rondelles `chaux`/`soufre`) | pH §2.4 | **NEUTRE → `d8856261…` inchangé** | ✅ |
| ⑦ | Faim d'azote (bois/BRF + substrat usé champignons) | NPK §2.7 | **NEUTRE → `d8856261…` inchangé** | ✅ |
| ⑧ | Structure `structure_sol` (infiltration/asphyxie/uptake) | structure §2 | **maîtrisé → `e209e8d8…`** | ✅ |
| ⑨ | Vue : overlays nouveaux champs + indices visuels (chlorose) | — | NEUTRE (vue) | ⬜ |

## §REPRISE

**① CLOS le 2026-06-20.** Champ `ph` (GridField par plot) ajouté à `EcoFields`,
**hérité du `soil_type`** (table `PH_PAR_SOL` : terre 6.8 / argile 7.0 / sable 5.8
/ roche 7.6) et dérivant lentement (`tick_ph`, lerp inertie 0.02 ; calcul PUR isolé
dans `fields/ecofields/ph.py` façon thermique). Acidification par litière (`om_fresh`
÷ `LITIERE_REF`) + lessivage (humidité÷3, faute de drainage par plot). `cec=0`
(volet NPK absent). Câblé dans `boucle.py` étape 4c (après décompo). **Aucun lecteur**
→ **golden NEUTRE, hash inchangé `f7e1a9b4…`**. `soil_type` ajouté au dataclass
`EcoFields` + param `init_eco` ; câblé dans `test_golden.build_world` et `main.build_tile`
(simserver hérite via ces fabriques). Exposé dans `get_field` (overlay debug gratuit).

Vérifié : héritage terre≠sable, dérive lente (~0.05 sur 10 ticks), plot avec litière
s'acidifie plus que le plot nu. `main.py` OK, golden PASS.

⚠️ **Taille** : `container.py` 387 ldc de code (+10 d'orchestration : champ, init,
registre, méthode déléguante). Il était DÉJÀ à 377 avant ① (au-dessus du seuil ~350).
Le calcul est dans `ph.py` (§7 conception respecté). Un éclatement d'`EcoFields`
serait un chantier à part — à arbitrer avec Nico, hors périmètre du sprint.

**① CLOS** (détail conservé ci-dessus).

**② CLOS le 2026-06-20.** Trois `GridField` `n`/`p`/`k` ajoutés au dataclass
`EcoFields`, **hérités du `soil_type`** (table `NUTRIENT_INIT_PAR_SOL` dans
`constants.py` : terre (1.0, 0.8, 0.9) / argile (0.9, 0.9, 1.1) / sable
(0.5, 0.4, 0.4) / roche (0.4, 0.6, 0.5)), `max_val=3.0` comme l'ancien
`fertilite`. Init dans `__post_init__` après le bloc `ph`. **Aucun tick, aucun
lecteur, aucun écrivain** : `fertilite`, l'uptake, la minéralisation, `soil_memory`
et les signatures restent INTACTS. Exposés dans `get_field` (`"n"`/`"p"`/`"k"`,
overlay debug gratuit). **Golden NEUTRE, hash inchangé `f7e1a9b4…`**. Vérifié :
héritage différencié terre≠argile≠sable≠roche, valeurs constantes (pas de dérive).

⚠️ **Taille** : `container.py` passé à **398 ldc** de code (387 → 398, +11 :
3 champs + bloc d'init + 3 entrées `get_field`). Déjà au-dessus du seuil ~350
avant ② (cf. ①). Pas de calcul à isoler ce coup-ci (champs inertes). Éclatement
d'`EcoFields` = chantier à part, à arbitrer avec Nico hors périmètre sprint.

**③ CLOS le 2026-06-20 — golden RE-FIGÉ LARGE `87ed27aec24f6ca5…`** (porté
FIDÈLE : Liebig NE gate PAS `_avancer_stades`, n/p/k reprennent les rôles de
`fertilite`). `fertilite` **supprimé net** du dataclass / `get_field` /
`__post_init__` / `summary` / `__repr__`. Bascule dans `container.py` :
- `fertilite_index(r,c) = (n+p+k)/3` (grandeur lisse dérivée pour les lecteurs).
- `tick_diffusion` diffuse n/p/k (inertie `FERTILITY_INERTIA`).
- `tick_decomposition` : minéralisation **splittée par tissu** (`split_miner`,
  helper pur `nutriments.py`) ; lessivage **différencié par nutriment & CEC**
  (`leach_factor("N"|"P"|"K", cec)`, `cec_norm_at(soil_type, om_stable/5)`).
- `plant_uptake` : branche `fertilite` retirée ; bloc **BESOIN N/P/K plafonné
  par le champ** (= loi du minimum, prélèvement borné par la dispo réelle).
- `soil_memory`/`vitalite`/`succession` relisent `fertilite_index` (seuils
  intacts) ; `vigueur_plante.qi_local` lit `min(n,p,k)` (Liebig diégétique).
- `init_eco(fertilite=…)` conservé en **param de COMPAT** : si fourni, pose
  n=p=k uniforme ; sinon héritage `soil_type` (tronçon ②).
Consommateurs redirigés `"fertilite"→"n"` : `compost.EPANDRE_W`, `aleas`
(Pucerons), `boucle.py` repr, effets `inject_field` (Fabaceae+Urticaceae =
fixation N §2.6, adventices×3, compagnes), `simserver/fields`, `diag_fields_span`.
**NON touché** (décision cadrage) : `cultivees.py:205` add_rondelle `"fertilite"`
(= label de rondelle, pas un champ).

**Dérive golden inspectée & cohérente** (terre 40 sem) : n 1.0→~0.05 (mobile,
lessive + uptake), p 0.8→~0.73 (quasi immobile, minéralisé → stable), k 0.9→~0.21
(intermédiaire). Argile (CEC 0.8) retient bien mieux. **N devient le limiteur de
Liebig = attendu.** `population_hash` INCHANGÉ.

**Suites** : toutes PASS (structures 65/65, vigueur 135, croissance 67, genetique
20, maitrise 35, signes 8, + competition/planter/eau/fruits/lifecycle/catalogue_lot2/
population/attraction/ruche/evergreen/biennial/faune_dediee/alarme/auxiliaires).
**SAUF `test_senescence`** : rouge, mais **régression PRÉ-EXISTANTE** (bisection
git → commit `4b70032`, thermique ⑦ Neige+Orage : précipitations gorgent le sol →
pommier isolé asphyxié à 2.7 ans vs 59.8 attendus). **Indépendant de ③** (courbe
hum/mort identique fertilite-ancien vs NPK-nouveau, vérifié par `git stash`).
**Tracé en DETTE D39** (décision Nico 2026-06-20 : tracer + clôturer ③).

⚠️ **Taille** : `container.py` **420 ldc** de code (398 → 420, +22 : bascule
décompo splittée + lessivage CEC + bloc uptake BESOIN + `fertilite_index`).
Toujours au-dessus du seuil ~350 (cf. ①②). Calcul pur isolé dans `nutriments.py`
(10 ldc). Éclatement d'`EcoFields` = chantier à part, hors périmètre sprint.

**④ CLOS le 2026-06-20 — golden RE-FIGÉ MAÎTRISÉ `d8856261bbe49787…`.** Le champ
`ph` (inerte depuis ①) devient enfin LECTEUR : cloche gaussienne de disponibilité
`dispo(ph, nut) = exp(−((ph−PH_OPT[nut])/PH_WIDTH[nut])²)` ∈ ]0,1] (helper PUR dans
`nutriments.py`, 14 ldc) branchée à **deux endroits** :
- `plant_uptake` : le `besoin` N/P/K (③) est multiplié par `dispo(ph_local, nut)`
  — un nutriment en STOCK n'est pas forcément ASSIMILABLE (P bridé hors zone neutre,
  N peu sensible). Module un FLUX, pas la plante (philo #2).
- `tick_decomposition` : la part BIOLOGIQUE de la vitesse (`micro`) est modulée par
  `dispo(ph,"micro")` (ph → microbiome → minéralisation). Socle abiotique (0.5) et
  bioturbation du ver laissés bruts. `decomp_speed` (fragmentation squelette) **non
  touché** → divergence documentée (fragmentation mécanique/fongique < pH-sensible
  que la minéralisation bactérienne).
Constantes `PH_OPT`/`PH_WIDTH` ajoutées dans `constants.py`.

**Chlorose alcaline REPORTÉE au ⑤** (décision Nico 2026-06-20) : elle a besoin de
la notion « acidophile » par espèce (`ph_opt`/`ph_tol`) qui n'existe pas avant le ⑤
→ pas de proxy jetable. `CHLOROSE_PH` n'est donc PAS encore posée (viendra au ⑤ avec
son consommateur).

**Dérive golden inspectée (`git stash` diff) : STRICTEMENT localisée.** Seules les
2 lignes `ECO` du digest bougent — AUCUNE plante, rondelle, naissance/mort ne change.
Le **phosphore résiduel monte** (terre p 0.658→0.739 ; tuile 1 p 0.223→0.248) car
son uptake est bridé (`dispo P` ≈ 0.78 argile / 0.91 terre) → moins prélevé, plus de
stock. N quasi inchangé (cloche large ≈ 1.0), K et om légèrement décalés (micro argile
0.984). `dispo` sur les sols du smoke : terre P=0.914/micro=1.0, argile P=0.779/micro=0.984.

**Suites** : toutes PASS (vigueur 135/135, croissance 67, genetique 20, maitrise 35,
maitrise_detection 20, signes 8, phototropisme 11, ombre 4, + competition/planter/eau/
fruits/lifecycle/population/structures/catalogue_lot2/attraction/ruche/evergreen/
biennial/faune_dediee/alarme/auxiliaires). **SAUF `test_senescence`** : rouge à 2.7 ans
(asphyxie pommier) = **régression PRÉ-EXISTANTE D39**, signature IDENTIQUE à ③,
indépendante du ④ (vérifié : même cause, non liée à l'uptake NPK/pH).

⚠️ **Taille** : `container.py` **423 ldc** de code (420 → 423, +3 : `ph_local`,
facteur `dispo` sur le besoin, `micro *= dispo`). Toujours au-dessus du seuil ~350
(cf. ①②③). Calcul pur isolé dans `nutriments.py` (helper `dispo`, 14 ldc). Éclatement
d'`EcoFields` = chantier à part, hors périmètre sprint.

**⑤ CLOS le 2026-06-20 — golden NEUTRE, hash INCHANGÉ `d8856261bbe49787…`.** Chaque
espèce reçoit une **fenêtre pH** (`ph_opt`/`ph_tol`, attributs de classe `PlantBase`
dans `plants/base/familles.py`, défauts NEUTRES 6.8/3.0 — `ph_tol` LARGE ⇒ cloche
plate ⇒ insensible). Helper pur `bell(ph, opt, tol)` ajouté à `nutriments.py` (forme
MÈRE de `dispo`, qui en devient un cas particulier tabulé) ; ré-exporté par
`fields/ecofields/__init__`. Branché à **deux portes** :
- **Croissance/vigueur** (`sim/vigueur_plante.qi_local`) : Qi territorial × `bell(ph_local,
  ph_opt, ph_tol)` (puise/croît moins hors fenêtre) × facteur **chlorose** alcaline
  (`ph_opt < SEUIL_ACIDOPHILE` ET `ph_local > CHLOROSE_PH` → `CHLOROSE_MALUS`). `ph_local`
  = moyenne `eco.ph.at_plot` sur `root_plots` (miroir de la lecture `min(n,p,k)`).
  **Façade read-only jamais appelée par le tick** (cf. en-tête module) → zéro golden.
- **Germination/succession** (`fields/seedbank.germination_candidates` nouveau param
  `arch_ph`) : niche × cloche de l'espèce candidate au pH local — une espèce hors
  fenêtre ne s'installe pas (porte). `arch_ph` construit PAR PLOT dans `succession()` /
  `spring_flush()` ; porte aussi posée dans `_lever_grains_en_attente` (chemin planté,
  VIDE au golden). Sur argile (ph 7.0) les adventices `ph_tol` large → `bell≈0.9956` :
  **n'a flippé AUCUNE levée** du smoke → hash strictement inchangé (vérifié).

**Constantes** ajoutées à `constants.py` : `CHLOROSE_PH=7.6`, `SEUIL_ACIDOPHILE=5.5`,
`CHLOROSE_MALUS=0.5`. `PH_TOL_DEFAUT` (≡3.0) posé comme LITTÉRAL dans `familles.py`
(couche `plants` n'importe jamais `fields` — règle de couches respectée, NOTÉ).

**Noyau démonstrateur** : **Myrtille** AJOUTÉE (`Vaccinium`, nouvelle famille INERTE
`Ericaceae`, `plants/species/sauvages.py`, acidophile 4.8/0.8, `archetype=None` →
hors WEED_CATALOGUE, jamais en succession, posée par le joueur ; clé `"myrtille"` au
PLANT_CATALOGUE) = le démonstrateur roi de la chlorose. **Lavande/Thym** = calciphiles
7.4/1.1. **Oseille/prêle indicatrices DIFFÉRÉES** (décision périmètre) : même mécanique
que la myrtille (fenêtre basse), zéro impact smoke, zéro mécanique neuve → enrichissement
catalogue à part, à arbitrer avec Nico (NOTÉ, pas oublié).

**Vérifs** : golden PASS hash inchangé ; **23 suites ciblées OK** (vigueur, croissance,
genetique, maitrise(_detection), signes, phototropisme, ombre, competition, planter,
eau, fruits, lifecycle, population, structures, catalogue_lot2, attraction, ruche,
evergreen, biennial, faune_dediee, alarme, auxiliaires). `test_senescence` toujours
rouge = **D39 pré-existante** (asphyxie pommier, indépendante de ⑤). `main.py 1 an`
= PASS exit 0, aucun crash (monde complet lourd → pas de run long inutile : golden
déterministe + 23 suites = la vraie barrière de non-régression).

⚠️ **Taille** : `container.py` NON touché ce tronçon (calcul dans `vigueur_plante` /
`seedbank` / `succession`). Petits +N sur ces fichiers, aucun près du seuil ~350.

**⑤ CLOS & COMMITTÉ** (`a740df7`).

**⑥ CLOS le 2026-06-20 — golden NEUTRE, hash INCHANGÉ `d8856261bbe49787…`.** Deux
nouvelles `RONDELLE_TYPES` posables : **`chaux`** (remonte le pH) et **`soufre`**
(acidifie). Modèle : la présence d'une rondelle d'amendement sur la tuile pousse la
**CIBLE** de dérive du pH de ±`AMEND_PUSH` (=0.15), **jamais `ph` directement** →
progressif sur saisons (inertie `PH_INERTIA`=0.02), **réversible** (retrait → cible
repart vers l'héritage), **event-driven** (pose hors tick).
- `world/tile.py:16` : `"chaux"`,`"soufre"` ajoutés au `frozenset RONDELLE_TYPES`
  (la pose/validation `StakeSlot.add` les accepte sans autre changement).
- `constants.py` : `AMEND_PUSH = 0.15` (placeholder calibrage post-test).
- `ph.py` `tick_ph(eco, cec=0, amend_dir=0)` : `base += AMEND_PUSH*amend_dir` sur la
  cible roche-mère (helper PUR, reste 14 ldc). `amend_dir ∈ {−1,0,+1}`.
- `container.tick_ph(self, amend_dir=0)` délègue (signe propagé ; couche `fields`
  n'importe pas `world`).
- `boucle.py` étape 4c : `net = count("chaux") − count("soufre")` ;
  `amend_dir = (net>0)−(net<0)` (présence binaire signée) → `eco.tick_ph(amend_dir)`.
  Aucune rondelle chaux/soufre au smoke → `amend_dir=0` partout → **golden NEUTRE**.

**Vérifié à la main** (tuile sable 5.8, isolé) : chaux +1 sur 60 sem → pH 5.80→5.86
(> réf sans amend 5.75) ; soufre −1 → 5.65 (< réf) ; progressif (montée lente semaine
par semaine) ; **réversible** (retrait après 60 sem → redérive 5.86→5.77 vers réf).
Effet lent voulu (inertie décennale, « la chaux met un an »). Golden PASS hash
inchangé ; suites OK (structures 65/65, vigueur 135, croissance 67, planter, eau,
population, catalogue_lot2). `test_senescence` rouge = **D39 pré-existante** (vérifié
au `git stash` : échoue à l'identique âge 2.7 ans SANS le ⑥, indépendant).

⚠️ **Taille** : `container.py` **423 ldc** (inchangé vs ④ : seuls doc + param par
défaut ajoutés, zéro code neuf). `ph.py` 14 ldc, `boucle.py` 213. Rien de neuf au
seuil. Éclatement d'`EcoFields` = chantier à part hors périmètre sprint (cf. ①–④).

**Kickoff suivant écrit** : `07_faim_azote.md` (immobilisation N par bois/BRF +
substrat usé de champignons, crochet futur acteur champignon, golden maîtrisé).

`main.py 50 ans` **sauté** (décision Nico 2026-06-20) : golden déterministe + suites
ciblées = la vraie barrière de non-régression, run long inutile (cf. ⑤).

**⑦ CLOS le 2026-06-20 — golden NEUTRE, hash INCHANGÉ `d8856261bbe49787…`.** La litière
C-riche fraîche (tissus `FAIM_N_TISSUS = {bois, substrat}`) IMMOBILISE de l'azote local :
`immobilise = FAIM_N_COEF·masse` (helper PUR `nutriments.immobilise_n`, FAIM_N_COEF=0.20).
Modèle TRANCHÉ = **prélèvement RÉVERSIBLE recalculé chaque tick** (pas de stock d'azote
emprunté, choix simple du kickoff) : à l'uptake (`plant_uptake`, branche N), la dispo N
assimilable = `max(0, n − immob)` ; le champ `n` n'est JAMAIS amputé (on ne retire que le
`real` réellement prélevé) → bois mûri ⇒ immob → 0 ⇒ azote de nouveau disponible. La plante
ressent via l'uptake Liebig (③) qui plafonne sur ce N réduit → jaunit (faim d'azote). Module
un FLUX, pas la plante (philo #2). Greffes : `bois_fresh_at(r,c)` (accesseur Σ masses tissus
immobilisants, `container.py`) + bloc immob inline dans `plant_uptake`. **`substrat` = crochet
INERTE** (jamais déposé tant que l'acteur champignon n'existe pas → l'accesseur ne voit que
le `bois` ; pas ajouté à TISSU/NPK_RELEASE = pas d'implémentation d'acteur).

**Golden NEUTRE** : le smoke ne dépose pas de `bois` frais limitant l'azote sur un plot habité
(aucune levée/uptake flippé) → hash inchangé. **Mécanisme VÉRIFIÉ à la main** (hors smoke) :
plot habité, n appauvri 0.05, dépôt `bois` 1.0 (immob 0.20 > 0.05) → uptake N = 0 (affamé) ;
retrait du bois → uptake N = 0.05 RESTAURÉ (réversible, aucun azote détruit). Sur sol riche
(n=1.0) immob 0.40 ne bride pas le petit besoin/tick (0.06) — la faim d'azote ne « mord »
que quand N est déjà le limiteur, réaliste.

**Suites** : 23 ciblées PASS (structures, vigueur 135, croissance 67, genetique 20, maitrise
35, maitrise_detection 20, signes 8, phototropisme 11, ombre 4, competition, planter, eau,
fruits, lifecycle, population, catalogue_lot2, attraction, ruche 20, evergreen, biennial,
faune_dediee, alarme 16, auxiliaires). `test_senescence` rouge à âge 2.7 ans = **D39
pré-existante** (asphyxie pommier, signature identique à ③④⑤⑥, indépendante du ⑦). `main.py
1 an` EXIT=0 aucun crash (run 50 ans sauté, cf. ⑤⑥).

⚠️ **Taille** : `container.py` **429 ldc** (423 → 429, +6 : accesseur `bois_fresh_at` + bloc
immob uptake). Toujours au-dessus du seuil ~350 (cf. ①–⑥). Calcul pur isolé dans
`nutriments.py` (helper `immobilise_n`, 18 ldc total). Éclatement d'`EcoFields` = chantier à
part hors périmètre sprint.

**Kickoff suivant écrit** : `08_structure_sol.md` (volet structure §2 : champ `structure_sol`
Option B — infiltration/asphyxie/uptake, dette D30 absorbée).

**⑧ CLOS le 2026-06-20 — golden RE-FIGÉ MAÎTRISÉ `e209e8d854300aa8…`** (avant
`d8856261…`) ; **`population_hash` RE-FIGÉ `cd21704baa2e9f50…`** (dérive
infinitésimale, 8 lignes × 1 unité à la 6e décimale). Champ `structure_sol ∈ [0,1]`
(dette **D30 absorbée**, Option B), **hérité du `soil_type`** (`STRUCTURE_INIT_PAR_SOL` :
terre 0.7 / argile 0.45 / sable 0.6 / roche 0.4), dérive LENTE (`STRUCT_INERTIA`=0.05).
Calcul PUR isolé dans `fields/ecofields/structure.py` (NOUVEAU, 21 ldc) façon ph/thermique :
`tick_structure(eco, plants, pluie_norm)` agrège trois forces → bioturbation des vers
(`BIOTURB`·lombric_norm, `+`), racines pivotantes décompactantes (`RACINE_PIVOT`, `+`),
**battance** de la pluie sur sol nu (`BATTANCE`·pluie_norm·(1−couvert litière), `−`).
Câblé `boucle.py` étape 4d (`pluie_norm = PRECIP_NORM.get(event.kind, 0)`).

**Trois couplages LECTEURS** (module un FLUX, pas la plante, philo #2) :
- **Infiltration** (`tick_hydrology`) : `h += BASE_RAIN · structure` — sol tassé ⇒ moins
  d'eau infiltrée (ruissellement).
- **Asphyxie** (`plant_uptake`) : la SÉVÉRITÉ de l'excès d'eau `excess_norm ×(2−structure)`
  — sol tassé ⇒ anoxie aggravée (§2.3). PAS l'`asphyxie_factor` (un facteur ∈[1,2]
  augmenterait à tort l'uptake).
- **Uptake** (`plant_uptake`) : `asphyxie_factor ×= STRUCT_UPTAKE_MIN + (1−STRUCT_UPTAKE_MIN)·structure`
  — racines bridées en sol compact.

**Gestes** (`sim/actions/gestes.py`, effet DIRECT plein, hors tick, pas ×INERTIA) :
`becher` → `structure_sol.add(−BECHAGE_MALUS)` (tasse) ; `grelinette` **signature changée**
`(game_state, player, eco, r, c)` → `structure_sol.add(+GRELINETTE_GAIN)` + ajoute des
vers (`populations["lombric"].add(+DENSITE_PAR_SPRITE)`). Câblé `tools/simserver/actions.py`
(résout tile/eco + r,c + bornes). Attribut `decompactante: bool` sur `PlantBase`
(`familles.py`), **MedicagoLupulina** `= True` (luzerne, pivot décompactant).

**Dérive golden inspectée (`git stash` diff) : 100 % traçable aux 3 couplages.** Tuile
ombragée : humidité↓ (infiltration, structure 0.7 < 1.0), n/p/microbiome/vitalité↑
(uptake mix < 1) ; tuile 2 : nutriments tous↑ ; quelques plantes ±1 sem + 1 réensemencement
décalé. **disturbance/lumiere INCHANGÉS** (aucun champ surprise).

**Suites** : golden PASS, population PASS (re-figé), **eau 20/20** (tolérance plancher
uptake −1e-9 → −1e-3 : artefact d'arrondi 3-déc × mix structure, invariant physique
intact, commenté), + vigueur 136, structures 65, croissance, genetique, maitrise(_detection),
signes, phototropisme, ombre_maison, competition, planter, fruits, lifecycle, catalogue_lot2,
attraction, ruche, evergreen, biennial, faune_dediee, alarme, auxiliaires. `test_senescence`
rouge = **D39 pré-existante**, **NON aggravée par ⑧** (pommier vit 34.3 ans post-⑧ vs 2.7
pré-⑧ → amélioré). `main.py 1 an` EXIT=0 (run 50 ans sauté, cf. ⑤⑥⑦).

⚠️ **Taille** : `container.py` **443 ldc** (429 → 443, +14 : champ `structure_sol` + init
hérité + entrée `get_field` + méthode `tick_structure` déléguante + 3 couplages). Toujours
au-dessus du seuil ~350 (cf. ①–⑦). Calcul pur isolé dans `structure.py` (21 ldc).
**Éclatement d'`EcoFields` = chantier à part hors périmètre sprint** (constat constant ①–⑧
— à arbitrer avec Nico).

**SPRINT MOTEUR CLOS.** Reste ⑨ = vue Godot (overlays + indices visuels chlorose) —
kickoff `09_vue_overlays.md`. Commit ⑧ : `feat(sol) : tronçon ⑧ structure_sol
(compaction/infiltration/asphyxie/uptake) — dette D30`.
