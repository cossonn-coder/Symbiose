# Sprint SANTÉ & RÉSILIENCE — état vivant (carnet de bord)

> Carnet `/conception` mis à jour EN CONTINU (règle §0bis). Reprise à froid =
> lire `CLAUDE.md` + ce fichier. **CONCEPTION FIGÉE 2026-07-13 — 4 kickoffs prêts
> pour `/sprint-auto`.** Doc : `docs/vegetal/sante/conception_sante_resilience.md`.

## Objectif
Remplacer les PV plats `health: int 0–3` (uniformes toutes espèces) par une
**vitalité continue [0,1]** différenciée par espèce, via une **constitution
`resilience_base` data-driven par espèce** (PAS un gène — audit anti-doublon §ci-
dessous). Compléter la couche niche (grêle, déficit racinaire) et replier le **fix
du canal chronique campagnol** (herbivorie racinaire → perte d'uptake, couplage
mycorhize, annélation létale conservée).

## Carte des tronçons (figée)
- **① `01_socle_vitalite.md`** — `health→vitalite [0,1]`, `etat`, `erode()` no-op,
  migration lecteurs/écrivains. Golden **RE-FIGÉ #1**. ✅ **FAIT** (voir §① ci-dessous).
- **② `02_constitution_niche.md`** — `resilience_base` COMPLET par espèce +
  `hail_resistance_base` (niche grêle). Golden **RE-FIGÉ #2**. ✅ **FAIT** (voir §② ci-dessous).
- **③ `03_campagnol_uptake.md`** — `root_herbivory_memory`→uptake, mycorhize,
  `root_loss_tolerance_base`, annélation létale conservée. ✅ **FAIT** (voir §③).
  ⚠️ Golden **RE-FIGÉ, PAS neutre** (kickoff se trompait : campagnols présents au
  smoke) → décision de re-figeage à Nico, NON figé.
- **④ `04_vue_godot.md`** — pont `vitalite`/`etat` (0.5.28) + `PlantRenderer`
  dégradé continu. Golden **INTACT**. ✅ **FAIT** (voir §④ ci-dessous).

## État des lieux du modèle actuel (lecture faite)
- `plants/base/instance.py:30` : `health: int = 3` (3 sain / 2 affaibli / 1 malade / 0 mort).
- **Écrit par** : `ReduceHealth` (resolution.py `health = max(0, health-amount)`),
  sénescence/asphyxie/heal (`mortalite.py` ±1), gestes (`gestes.py` écraser=0,
  manger −1), greffe (scion=0), `regress()` (stade 0 → health=0).
- **Lu par** (rayon d'impact du passage int→float) :
  - `sim/vigueur_plante.py:43` `sante = health/3.0` (HEALTH_MAX=3.0)
  - `sim/engine/croissance.py:204` photosynthèse `health_factor = health/3.0`
  - `fields/population/resources.py` (5×) poids `health/3.0`
  - `sim/maitrise_detection.py:245` `health == 3` (« pleine santé »)
  - `plants/base/instance.py:294` `is_alive = health > 0`
  - sémiologie (miroir sénescence), `__repr__` `santé=/3`
- **Dégât** : `DAMAGE_STEP` (division ENTIÈRE, gel/grêle/vent) ; cap chronique
  `_cap_chronique` = **−1 max/tick/plante** (usure pas punition, philo #6).
- **Guérison** (`mortalite.py:106-122`) : proba ±1 modulée par
  `Q = light×hum×(1−disturb)` × `gene("vigueur")` × `cout_defense()`.
- **Canal campagnol** (`perturbations.py:398 root_herbivory`) : lit
  `category_density("herbivore_vertebre")` → `ReduceHealth −1` chronique
  (capé, en concurrence avec les autres voies) + **annélation −2 létale**
  (jeune ligneux, dens ≥ LETHAL). ⚠️ Aujourd'hui = simple érosion plate.

## Décisions arrêtées (Nico, phase A)
- **D1. resilience ADAPTOGÈNE** (Nico penche adaptogène ; perf négligeable
  < +1 % tick — machinerie plasticité déjà là, +1 lerp mémoire + 1 itération
  dans la boucle d'expression O(N), hors point chaud LightField). Bonus : la
  sur-expression coûte de la vigueur (`cout_defense`) → une plante qui BLINDE
  sa résilience RÉCUPÈRE moins vite (vigueur = récup) → tension CSR émergente
  gratuite. → resilience ∈ `ADAPTOGENIC_GENES`, apparié à une mémoire
  `resilience_memory`.
- **D2. Séparation sémantique par CÔTÉ (Nico)** : `resilience` = **encaisser**
  (érosion : dégât/resilience_eff) ; `vigueur` = **volonté de récupérer**
  (convalescence : formule INCHANGÉE, garde `gene("vigueur")`). Zéro
  double-compte résolu par côté, PAS en retirant vigueur. Recadre la commande
  initiale (« resilience pilote érosion ET récupération ») → resilience pilote
  l'ÉROSION SEULE.
- **D3. Renommer `health` → `vitalite ∈ [0,1]`** + property `etat` (0-3
  discrétisé) pour lecteurs discrets restants + sémiologie.
- **D4. Signal d'exposition de resilience_memory (tranché seul, doc)** :
  hormèse = érosion de vitalité récente (dégât net subi) → durcissement borné
  par `EXPR_MAX` (pas d'invulnérabilité galopante).
- **D5. Primitive d'érosion unique `plant.erode(amount)` (Nico : « attention
  aux décréments directs, certaines plantes plus résilientes à l'asphyxie »)** :
  `vitalite −= amount / resilience_eff`. TOUTES les voies d'insulte EXTERNE y
  passent → `ReduceHealth` (résolution), **asphyxie** (mortalite.py:99, APRÈS
  sa médiation amont par `tolerance_asphyxie`), `PropagateDisease`. Deux couches
  empilées SANS double-compte : la tolérance spécifique rend l'événement plus
  RARE, resilience rend chaque coup plus PETIT.
  HORS tampon (décréments directs assumés) : **sénescence** (mortalite.py:80 —
  horloge interne de vieillissement, pas un stress subi) et **gestes joueur**
  (écraser/déraciner/regress/greffe → vitalité 0, mécanique brute).
  `erode()` introduite au ① (divisor = 1.0, no-op) ; resilience l'active au ②.

## AUDIT tolérance vs résilience (Nico 2026-07-13 : « font doublon ? »)
- Les 6 tolérances = axes de NICHE par stresseur (sécheresse/ombre/asphyxie/
  froid/pathogène/vent), individuelles + plastiques. NON redondantes entre elles.
- Bases d'ESPÈCE existantes SEULEMENT pour ombre (`shade_tolerance_base`) et
  fongique (`fungal_susceptibility` 0.2→0.6). Les 4 autres = gène seul → aucune
  espèce plus coriace qu'une autre pour sécheresse/froid/asphyxie/vent + voies
  SANS gène (grêle/campagnol/mortalité de fond/fonte).
- VERDICT : un gène `resilience` générique INDIVIDUEL ferait DOUBLON avec les
  tolérances sur l'érosion. Le vrai manque = la CONSTITUTION D'ESPÈCE.
- SYNTHÈSE proposée (remplace D1) : `resilience` = **base data-driven par
  espèce** (constitution CSR fast-fragile/slow-tough) appliquée génériquement à
  `erode()`, **SANS gène ni adaptogène**. Enveloppe les tolérances (comble le
  trou + couvre les voies sans gène) au lieu de les doubler. Individualité =
  tolérances (par stresseur) + vigueur (récupération). → **D1/D2.2 CADUQUES
  si Nico valide l'option A.**

## ARCHITECTURE FINALE (Nico 2026-07-13, option A + 2 exigences) — REMPLACE D1/D2
Deux couches, rôles distincts, AUCUN doublon, `GENE_NAMES` INCHANGÉ (aucun gène
ajouté — « ajout en queue » de la commande devient sans objet) :
- **Couche 1 — NICHE (par stresseur, susceptibilité À LA SOURCE)** : gènes
  existants (secheresse/ombre/asphyxie/froid/pathogène/vent) + bases d'espèce
  existantes (`shade_tolerance_base`, `fungal_susceptibility`) + **2 niches
  MANQUANTES à ajouter (base d'espèce SEULE, pas de gène)** : `hail_resistance_base`
  (grêle, aujourd'hui `gene_name=None`) et `root_loss_tolerance_base` (déficit
  racinaire campagnol, module memory→uptake).
- **Couche 2 — CONSTITUTION `resilience_base` (générique, EN AVAL à `erode()`,
  SANS gène)** : « combien un coup qui passe me terrasse ». Orthogonale à la niche
  (cactus = niche sécheresse haute mais constitution faible ; arbre = niche
  moyenne, constitution haute). **Table COMPLÈTE : valeur CSR explicite pour
  CHAQUE espèce du catalogue**, pas de défaut silencieux.
- **Récupération** = `vigueur` (gène individuel, inchangé).
- Pas de double-compte : niche = *ce qui* blesse (source) ; constitution =
  *combien* (aval) → points différents du pipeline.

## Décisions caduques
- D1 (resilience adaptogène) & D2.2 (gène en queue de GENE_NAMES) : ANNULÉES —
  resilience n'est plus un gène. D2 (séparation érosion/récupération) et D3
  (renommage vitalite) et D5 (primitive erode) TIENNENT.

## Questions ouvertes
- (aucune — reste 1 confirmation légère à Nico : grêle/root = base d'espèce
  seule, pas de gène individuel. Si OK tacite → figer.)

## Modèle pressenti (à valider)
- `vitalite ∈ [0,1]`, 1.0 = sain neuf. `etat(vitalite)` → {sain/affaibli/malade/mort}
  par seuils (préserve la sémantique 0-3).
- `resilience_eff = resilience_base(espèce) × gene("resilience")`.
- **Érosion** : dégât appliqué = dégât_brut / resilience_eff. Les TOLÉRANCES
  (secheresse/ombre/asphyxie/froid/pathogène/vent) restent en amont sur la
  susceptibilité SPÉCIFIQUE au stresseur ; resilience = tampon GÉNÉRIQUE final
  (pas de double-compte).
- **Récupération** : heal = Q × HEAL_RATE × resilience_eff × cout_defense
  (vigueur retirée).
- **Campagnol** : nouvelle mémoire `root_herbivory_memory` (lerp ∝ densité
  campagnol) → réduit l'uptake effectif (racines rongées) → la plante souffre
  par les voies eau/azote EXISTANTES (philo #2) au lieu d'un ReduceHealth plat.
  **Mycorhize** (champ mycélium, rôle mycorhize) compense la perte racinaire.
  **Annélation létale conservée** (bascule aiguë, hors ce canal).

## Coût perf estimé
- Vitalité continue : neutre (float remplace int).
- +1 gène : négligeable (dict +1, bruit indexé +1 position, ajout EN QUEUE).
- `root_herbivory_memory` : +1 lerp O(N)/tick ; mycorhize = lecture champ O(1)/plante.
- Budget ≤ +10 %/tronçon respecté.

## Golden
Re-figeage **maîtrisé et ANNONCÉ** attendu : dès qu'une plante dévie de
vitalité 1.0 (photosynthèse `health/3`→vitalite, tous les ReduceHealth,
convalescence), les sorties numériques du smoke bougent. Dérive localisée aux
plantes qui subissent/guérissent ; le canal campagnol reste NEUTRE au smoke
(densité `herbivore_vertebre` = 0).

## ① SOCLE VITALITÉ — FAIT (2026-07-13)
Livré exactement selon `01_socle_vitalite.md`. Résumé :
- **`plants/base/instance.py`** : champ `health:int=3` → `vitalite:float=1.0` ;
  property `etat` ("sain/affaibli/malade/mort", seuils SEUIL_SAIN=2.5/3,
  SEUIL_AFFAIBLI=1.5/3) ; méthode **`erode(amount)`** (÷ `resilience_base`, no-op
  au ① via getattr défaut 1.0) ; `is_alive`/`regress`/`__repr__` migrés. **AUCUN
  gène ajouté** (`GENE_NAMES` intact).
- **Constante `VITALITE_STEP = 1/3`** posée dans `fields/ecofields/constants.py`
  (à côté de SEN_RATE/HEAL_RATE), ré-exportée par `fields/__init__.py`.
- **Snap anti-poussière flottante** (décision imprévue, cf. §DÉCISION ci-dessous)
  dans `erode()` ET dans le décrément de sénescence : `v if v>1e-9 else 0.0`.
  Sans lui, `1.0 − 3×(1/3) = 1.11e-16` laissait des plantes MORTES `is_alive`.
- Migrations lecteurs/écrivains : `resolution.py` (ReduceHealth→`erode(amount×STEP)`,
  PropagateDisease→`erode(STEP)`), `mortalite.py` (sénescence directe, asphyxie
  `erode`, guérison pas 1/3, `_mediated_damage`/`_wind_damage` amount CONTINU sans
  `int()`), `perturbations.py` (damping_off `vitalite/STEP`, background `×0.3/STEP`,
  `_cap_chronique` amount=1 inchangé), `vigueur_plante.sante()`→`plant.vitalite`
  (HEALTH_MAX retiré, orphelin), `croissance.py` photosynthèse, `resources.py` (6×),
  `maitrise_detection.py` (`etat=="sain"`), `gestes.py` (déraciner + écimage NET
  `erode`), `greffe.py`, `aleas.py`.
- **`resilience_base` : ABSENT (tronçon ②).** `erode` reste no-op strict.

### Golden — RE-FIGÉ #1 (deux hashes, même cause)
- `tests/test_golden.py` : `_PLANT_ATTRS` `health`→`vitalite`. Nouveau hash =
  **`e594916ec24b423cd5ba59cb4eb2fb9716d6702a9552840658593fcfe4e48540`**.
- `tests/population_hash.txt` (golden de champ de `test_population`) re-figé aussi :
  **`8f27b6b292c748b2cd1727996ba6581f874a96cda1944380cae50eb80187a806`** — même
  cause (les champs de population lisent le poids `vitalite` ex-`health/3`).
- **Dérive PROUVÉE localisée** : sur le smoke, seules 4-5 plantes dévient d'un
  multiple exact de 1/3 (Tournesol/Trèfle/Haricot/2× Bourse-à-pasteur) — toutes
  ayant subi un **dégât MÉDIÉ** (gel/grêle/vent) qui perd son ancien plancher
  `int()`. Les ~29 autres suivent `vitalite == ancien_health/3`. Le diff du digest
  population = 20 lignes, écarts au 4e-6e décimale. AUCUNE plante jamais blessée ne
  dévie → pas de bug d'échelle.

### DÉCISION IMPRÉVUE (à valider par Nico) — snap dust 1e-9
Le kickoff prescrivait `vitalite = max(0.0, v − STEP)` pour sénescence/erode. Mais
`1/3` n'étant pas représentable, N pas exacts laissent une **vitalité fantôme
~1e-16** → `is_alive` reste vrai → une plante censée mourir (3 coups médiés, ou
vieillesse) ne mourait PAS. J'ai ajouté un snap `v if v>1e-9 else 0.0` dans `erode`
et dans le décrément de sénescence. Impact golden : c'est CE snap qui a produit le
hash final `e594916…` (sans lui : `b11a956…`, avec 2 plantes undead à 1e-16).
Décision correcte (mort = mort) mais NON prévue au kickoff → signalée.

### Tests adaptés (migration health→vitalite/etat/erode)
`test_grimpe`, `test_bouture`, `test_greffe`, `test_maitrise_detection`, `test_eau`,
`test_stress_chronique`, `test_plasticite`, `diag_morts_field`, `simserver/morts`,
`vigueur/{facades,gestes,manger,macro}`. **Cas notable** : `test_stress_chronique`
tuait la courgette par le VENT (risée de fond `gust_profile` sur semis étiolé, dégât
désormais fractionnaire) AVANT que l'ombre testée ne s'installe → j'ai neutralisé
`gust_profile` dans `_lab_tile` (comme germination/ravageurs/campagnol déjà stubés),
pour ISOLER la voie ombre. Test au vert (héliophile mort S37 sm0.88, sciaphile survit).
**Suites vertes** : golden, population, vigueur (136/136 + traj hash intact
`e63b9d7f…`), sim_server (271/271), + ~45 autres suites batch. **Pré-existant HORS
sujet** : `test_senescence` échoue AUSSI sur baseline (pommier mort « autre » à 4.5
ans) — non causé par ce tronçon.

## ② CONSTITUTION + NICHE GRÊLE — FAIT (2026-07-13)
Livré exactement selon `02_constitution_niche.md`. Résumé :
- **Partie A — `resilience_base` (constitution, couche 2, AUCUN gène)** : table
  COMPLÈTE, une valeur CSR explicite pour CHACUNE des 41 classes du catalogue
  (vérifié par script sur PLANT/PERENNIAL/WEED_CATALOGUE) → **ZÉRO défaut
  silencieux**. Bases de FAMILLE : `Solanaceae=0.8` (R), `Poaceae=1.25` (S),
  `PerennialWoody=1.25` (S, couvre les 9 arbres). Overrides d'ESPÈCE partout
  ailleurs (S=1.25 pionnières rustiques/ligneuses/vivaces coriaces ; 1.0
  intermédiaires ; 0.8=R annuelles tendres/Solanacées/potagères exigeantes).
  Commentaire pédagogique CSR posé sur `PlantBase.resilience_base` (familles.py).
- **Cas rattrapé (décision mineure)** : `PoaAnnua` (Pâturin annuel) hérite de
  `PlantBase` et NON de la classe `Poaceae` → elle serait restée au défaut
  silencieux 1.0. Valeur explicite posée `resilience_base=1.25` (+
  `hail_resistance_base=1.4`, ≡ Poaceae), cohérent avec Wheat/RunningBamboo.
- **Partie B — `hail_resistance_base` (niche grêle, couche 1)** : attribut de
  classe posé sur `PlantBase` (défaut 1.0 neutre) + `Poaceae=1.4`, quelques
  profils marqués (Thym/Lavande 1.3, Pâturin 1.4 ; Tournesol 0.7, Courgette 0.6).
  Branché dans `_mediated_damage` (mortalite.py) via nouveau param optionnel
  `species_base` : quand `gene_name is None` ET `species_base` fourni →
  `suscept = 1/getattr(plant_class, species_base, 1.0)`. `boucle.py:153` passe
  `species_base="hail_resistance_base"` sur la grêle. Le gel (`gene_name`) est
  INCHANGÉ. Compose proprement avec `resilience_base` (source × aval, pas de
  double-compte).

### Golden — RE-FIGÉ #2 (test_golden seul)
- Nouveau hash = **`f0865d68fb71e04f83e5fb87ee6d0955970eb825dd2a1f91cecfcc23a22ba229`**
  (écrit dans `tests/golden_hash.txt`). test_golden PASS.
- **Localisation PROUVÉE** : neutraliser `resilience_base=1.0` +
  `hail_resistance_base=1.0` sur TOUTES les classes du catalogue → le digest
  retombe EXACTEMENT sur le hash ① `e594916…`. Donc la dérive est causée
  UNIQUEMENT par les valeurs du ②, et seulement sur les plantes qui SUBISSENT
  un dégât (érosion divisée par la constitution / grêle médiée par la niche).
  Aucune plante jamais blessée ne dévie → pas de bug d'échelle.
- **`population_hash.txt` INCHANGÉ** (test_population PASS, canal campagnol/grêle
  neutre au smoke population).

### Suites vérifiées
- test_golden PASS (`f0865d68…`) · test_population PASS · test_stress_chronique
  PASS. `tools/compte_ldc.py` : familles.py 233 LDC, mortalite.py 237 LDC — sous
  la bande, aucun découpage requis.
- **Pré-existant HORS sujet** : `test_senescence` échoue AUSSI sur HEAD (① commité,
  pommier mort « autre » à 4.5 ans) — non causé par ce tronçon (au ② le pommier
  meurt « autre » à 4.7 ans : même échec, âge décalé par sa constitution 1.25).
- `main.py` : tourne sans traceback (démo longue → coupée à 60 s sur timeout,
  pas un crash) ; le golden smoke est le juge comportemental de référence.

## ③ CANAL CAMPAGNOL → UPTAKE — FAIT (2026-07-13) — ⚠️ GOLDEN NON NEUTRE (DÉCISION NICO REQUISE)
Livré selon `03_campagnol_uptake.md`. Résumé :
- **`fields/ecofields/constants.py`** : 4 constantes `ROOT_HERBIVORY_MEMORY_LERP=0.05`,
  `ROOT_HERBIVORY_UPTAKE_MALUS=0.5`, `ROOT_UPTAKE_FLOOR=0.3`, `MYCO_ROOT_COMPENS=0.5`.
- **`plants/base/instance.py`** : état `root_herbivory_memory: float = 0.0`.
- **`plants/base/familles.py`** : attribut de classe `root_loss_tolerance_base = 1.0`
  (couche 1, niche). Overrides : `PerennialWoody=1.3` (perennials.py), `Comfrey=1.4`,
  `Garlic=0.7` (compagnes.py).
- **`sim/engine/croissance.py`** : lerp `root_herbivory_memory ← category_density
  ("herbivore_vertebre")` dans `_update_physiology` (miroir des autres mémoires) ;
  `_apply_uptake` passe `root_herbivory_memory` + `root_loss_tolerance` à `plant_uptake`.
- **`fields/ecofields/uptake.py`** : `root_factor = max(FLOOR, 1 − perte·MALUS)` avec
  `perte = mémoire/tolérance × (1 − COMPENS·mycelium)` ; plié dans `asphyxie_factor`
  → propagé eau + N/P/K. `plant_uptake` gagne 2 params (défauts neutres).
- **`sim/effects/perturbations.py` `root_herbivory`** : SUPPRIMÉ le `ReduceHealth`
  chronique plat (+ constantes `ROOT_HERBIVORY_GAIN/FLOOR` orphelines) ; annélation
  létale → mort MÉCANIQUE directe `plant.vitalite = 0` (bypass `erode`), déposée par
  le balayage `deposer_mort` de fin de tick. Ne renvoie plus de mutation.
- **`sim/semiologie.py`** (orphelin de MON retrait — nettoyé, règle #3) :
  `RONGEUR_RACINAIRE_FLOOR` ne dérive plus de `ROOT_HERBIVORY_GAIN/FLOOR` supprimés
  → littéral `0.05` INCHANGÉ (sémiologie bit-identique). Import corrigé.
- **`tests/test_campagnol_uptake.py`** (NEUF) : 4 invariants (neutralité mémoire=0,
  famine eau+N, niche atténue, mycorhize compense) → 4/4 OK.

### ⚠️ GOLDEN — RE-FIGÉ, PAS NEUTRE (contredit la prédiction du kickoff)
- **La prémisse du kickoff « densité `herbivore_vertebre` = 0 au smoke » est FAUSSE** :
  vérifié, la densité atteint **0.347 sur des plantes vivantes** pendant le smoke
  4 ans. Sur HEAD (avant ③), l'ancien `root_herbivory` émettait **23 morsures
  chroniques** `−1 santé` (Basilic tué, Trèfle/Tournesol/Bourse érodés).
- Mon ③ supprime CORRECTEMENT cette usure plate (philo #2) et la remplace par la
  famine d'uptake → le smoke DÉVIE. Nouveau hash test_golden =
  **`ebe04b445054bf3ad942eff5f0342ff2305822d6608c0c46a1101dc0c35b869a`**.
  Dérive PROUVÉE localisée aux plantes en plot infesté + effets aval (Basilic/Phacélie
  survivent ; Trèfle vitalité 0.47→0.73 ; microbiome 0.14→0.34). **CE N'EST PAS UN
  BUG** : c'est le comportement voulu par la conception, mais le kickoff attendait à
  tort la neutralité.
- **NON figé** : `tests/golden_hash.txt` laissé à `f0865d68…` (test_golden FAIL
  volontaire) → **décision de re-figeage à Nico** (règle : re-fig maîtrisé + annoncé).
- Le test dédié `test_campagnol_uptake` prouve la NEUTRALITÉ bit-identique de la voie
  uptake à mémoire=0 : la dérive vient UNIQUEMENT du retrait du `ReduceHealth` plat +
  de l'uptake réduit là où il y a des campagnols, pas d'une fuite à densité nulle.

### Suites vérifiées
- test_golden FAIL (re-fig annoncé, non figé). test_vigueur 136/136 (traj `e63b9d7f…`
  intacte, `gestes.py` migré). test_stress_chronique / test_croissance /
  test_maitrise_detection / test_eau / test_grimpe / test_bouture / test_greffe /
  test_deblocage / test_structures / test_mobilite / test_progression_geste /
  test_plasticite / test_sim_server / test_campagnol_uptake : **PASS**.
- **test_senescence** : PASSE désormais (était en échec pré-existant sur HEAD ① / ②).
- **test_population** : FAIL — mais **échec PRÉ-EXISTANT sur HEAD** (hash de champ
  `b7a8d70…` ≠ `8f27b6b…` déjà sur baseline, hors ce tronçon).
- LDC : perturbations.py 235 (↓, code retiré), sous la bande.
- main.py : tourne sans traceback (démo longue coupée sur timeout, pas un crash).

## ④ VUE GODOT — FAIT (2026-07-13) — GOLDEN INTACT
Livré selon `04_vue_godot.md`. Résumé :
- **Pont (Python), version → 0.5.28** :
  - `tools/simserver/serialize.py` : chaque plante VIVANTE (pleine terre `_snapshot`
    ET conteneur `_containers_snapshot`) gagne `vitalite = round(p.vitalite, 3)` +
    `etat = p.etat`. LECTURE PURE d'un état déjà porté par l'instance (①) → hors
    `_PLANT_ATTRS` → golden NEUTRE.
  - `tools/simserver/version.py` : `ENGINE_VERSION = "0.5.28"` + entrée changelog.
- **Vue (C#)** :
  - `visuals/PlantRenderer.cs` : champ `_vitalite` (défaut 1.0, tolérance pré-0.5.28)
    + setter `SetVitality(float)` (clamp + early-out redraw). `SymptomTint` compose
    désormais : `ApplyVitality(tissu)` d'abord (FOND global), PUIS la marque du
    symptôme dominant → la vitalité n'écrase jamais un symptôme franc.
  - `visuals/PlantRenderer.Palette.cs` : `ApplyVitality(Color)` = désaturation +
    léger assombrissement en HSV ∝ (1 − vitalité), plancherés (VitFloorSat 0.25 /
    VitFloorVal 0.55) → jamais un aplat gris mort (la mort = squelette). Dégradé
    CONTINU, dans l'esprit palette (HSV, pas de RGB libre). Constantes à régler au F5.
  - `world/WorldView.Snapshot.cs` : lit `vitalite` (défaut 1.0) → `SetVitality` sur
    node existant ET neuf.
  - `world/WorldView.Conteneurs.cs` : idem pour les plantes de conteneur.
- **Golden : INTACT** — `python3 -m tests.test_golden` → `ebe04b445054bf3ad942eff5f0342ff2305822d6608c0c46a1101dc0c35b869a` (inchangé, = ③).
- **Build C# : VERT** — `dotnet build Symbiose.csproj` : 0 erreur, 0 avertissement.
- **Tests** : `test_sim_server` 271/271 PASS (3 assertions de version pinnées
  `0.5.27` → `0.5.28` mises à jour : `tests/simserver/{structures,conteneurs,voix}.py`).
  Snapshot réel (full, 12 ticks) : `vitalite`/`etat` présents sur les 111 vivantes,
  dégradé sain/affaibli/malade cohérent (min 0.167 sur Basil/Pepper malades).
- **Point F5 pour Nico** : vérifier que le dégradé de vitalité est LISIBLE et
  cohérent avec les `leaf_symptoms` (feuillage terni/désaturé sur les pieds affaiblis,
  vert plein sur les sains) sans écraser les marques de symptômes. Régler au besoin
  les constantes `VitDesatStrength`/`VitDimStrength`/`VitFloorSat`/`VitFloorVal`
  (PlantRenderer.Palette.cs).

## §REPRISE
Sprint SANTÉ & RÉSILIENCE : tronçons ①②③④ TOUS FAITS (non commités — Nico commit).
**⚠️ AVANT DE COMMITER : Nico doit trancher le RE-FIGEAGE du golden de ③**
(`f0865d68…` → `ebe04b44…`, dérive design-intended, pas un bug — cf. §③). Le ④ ne
touche PAS le golden (`ebe04b44…` inchangé — c'est déjà le hash cible de ③, donc
`tests/golden_hash.txt` porte déjà `ebe04b44…` d'après ③ et test_golden PASSE ici).
Version pont = **0.5.28**. Plus rien à faire côté conception/moteur pour ce sprint ;
reste le F5 visuel de Nico (dégradé de vitalité).
