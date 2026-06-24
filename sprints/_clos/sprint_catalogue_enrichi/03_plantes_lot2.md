# Tronçon ③ — PLANTES lot 2 (familles + cycles NEUFS)

> Sprint CATALOGUE ENRICHI. État partagé : `00_etat.md` (lire d'abord).
> Doc de référence FIGÉ : `docs/conception/CONCEPTION_CATALOGUE_ENRICHI.md`
> (§4.1-4.4 espèces, §7.2 mécanismes à vérifier). Kickoff **autosuffisant**.
> Lancement Python depuis `data/code/`. Filet C# : `dotnet build Symbiose.csproj`
> (zéro C# attendu ici).

## Objectif

Ajouter **5 espèces** qui introduisent **5 familles botaniques NEUVES** et
**2 cycles de vie jamais exercés** (`biennial`). C'est le tronçon le plus
« moteur » du sprint : contrairement à ②, l'attractivité florale n'est PAS
héritée gratis (familles absentes des tables `_ATTRACT_*`) et le cycle
`biennial` a un **trou** confirmé (cf. point chaud ci-dessous).

| Espèce | Latin | Famille (NEUVE) | Cycle | Hiver | Niche |
|---|---|---|---|---|---|
| **Carotte** | *Daucus* | **Apiaceae** | **biennial** | dormant | ombellifère → syrphe n°1, hôte machaon, racine comestible |
| **Ortie** | *Urtica* | **Urticaceae** | perennial | dormant | hôte chenilles, litière azotée, bioindicatrice N, anémophile |
| **Courgette** | *Cucurbita* | **Cucurbitaceae** | annual | die | **`fruitier`**, gros fruits → attraction animale, étalée (compétition sol) |
| **Mâche** | *Valerianella* | **Caprifoliaceae** | annual | die | couvre-sol d'hiver (jours courts), résiste au gel, comestible |
| **Ail** | *Allium* | **Amaryllidaceae** | **biennial** | dormant | **répulsif** familial, compagnon Solanaceae/Rosaceae, comestible |

## ⚠️ POINT CHAUD — le cycle `biennial` (carotte, ail) : trou confirmé

**Audit fait** : `biennial` n'est lu QUE par deux endroits —
- `plants/base/familles.py:175` : `longevity()` → 2 ans.
- `sim/engine/mortalite.py:209` : **mort monocarpique** à `age_years >= 2.0`
  (graines si archétype + dépôt nécromasse). ✅ ce bout marche.

**Ce qui MANQUE** : la progression de stade (`sim/engine/croissance.py:50`,
`_avancer_stades`) est gatée **uniquement par `duration_weeks`** (modulée par le
gène vigueur). **Aucun gate annuel** → une bisannuelle aux stades courts
**monterait à fleur dès l'an 1**, ce qui contredit la biologie « rosette an 1 →
ombelle an 2 ». La mort à `age>=2` tomberait alors sur une plante déjà montée et
refleurie plusieurs fois. **C'est le trou à combler.**

**Approche RECOMMANDÉE (à confirmer en début de tronçon)** — gate annuel minimal,
chirurgical, dans `_avancer_stades` : pour une espèce `life_cycle=="biennial"`,
**bloquer le passage VERS le stade de montaison/floraison tant que
`age_years < 1.0`**. Concrètement : marquer le 1ᵉʳ stade fleuri (convention : le
stade portant un effet `floraison`, ou un champ explicite type `bolt_stage`) et,
dans le `if plant.age_weeks >= needed and can_grow`, ajouter une condition
`and not (biennial and prochaine_etape == bolt and plant.age_years < 1.0)`.
Résultat : an 1 = rosette qui s'arrête avant la hampe ; an 2 = montaison +
floraison + graines ; fin an 2 = mort monocarpique (déjà gérée). **Coût golden**
= NEUTRE si aucune bisannuelle n'est plantée par le smoke (c'est le cas, cf.
§Golden), MAIS le code de `_avancer_stades` change → re-lancer le golden pour
**confirmer** la neutralité (un gate qui ne s'active que pour `biennial` ne doit
toucher AUCUNE espèce du smoke).

**Alternative écartée** (à mentionner si Nico préfère zéro-moteur) : donner au
stade rosette une `duration_weeks` ~ 45-50 pour qu'il « ne monte qu'après ~1 an ».
Fragile (la durée de stade n'avance pas pendant la stagnation froid/dormance →
le timing dérive) et sémantiquement faux (durée ≠ vernalisation). Le gate annuel
explicite est plus propre et plus lisible.

`evergreen` : **déjà vérifié au tronçon ②** (`tests/test_evergreen.py`). Rien à
refaire ici.

## Familles NEUVES — déclaration + câblage `_ATTRACT_*`

Deux choses par famille :

1. **Classe famille** dans `plants/base/familles.py` (sur le patron des 5
   existantes) — ou simple chaîne `family="…"` au niveau de l'espèce si AUCUN
   effet familial (patron Phacelia/Borage qui posent `family` directement sur
   `PlantBase`). Décisions d'effet familial (doc §7.2) :
   - **Amaryllidaceae** (ail) : **effet répulsif**. ⚠️ il n'existe PAS d'action
     qui injecte du négatif dans le champ `ravageur`. Le seul levier « défensif »
     data-pur aujourd'hui = `adjacency_bonus`/`reduce_maladie_rondelle` (→ booste
     le microbiome local, resolution.py:146, comme Lamiaceae). **Recommandé** :
     réutiliser ce levier pour l'ail (répulsif ≈ protection voisine), et NOTER
     qu'une vraie baisse du champ `ravageur` serait une action moteur nouvelle
     (à flaguer en dette si Nico la veut littérale).
   - **Urticaceae** (ortie) : **injection azote** → `family_effects` avec
     `inject_field fertilite +` (patron Fabaceae/minette). Anémophile.
   - **Apiaceae, Cucurbitaceae, Caprifoliaceae** : pas d'effet familial (chaîne
     `family` au niveau espèce suffit) — leur rôle est porté par les effets de
     stade (floraison, fruitier).

2. **Câbler les 3 tables `_ATTRACT_*`** (`fields/population.py:538-552`) — SINON
   ces familles tombent sur `_ATTRACT_DEFAUT=0.30` (et l'ombellifère-syrphe, gros
   intérêt de la carotte, serait raté). **Valeurs proposées** (allure naturaliste,
   calibrage post-test) :

   | Famille | abeille | syrphe | papillon | note |
   |---|---|---|---|---|
   | Apiaceae | 0.45 | **1.0** | 0.50 | ombelle ouverte = ressource syrphe n°1 |
   | Cucurbitaceae | 0.70 | 0.40 | 0.40 | grosses fleurs, abeille/bourdon |
   | Caprifoliaceae | 0.40 | 0.50 | 0.30 | petites fleurs mâche |
   | Urticaceae | **0.0** | **0.0** | **0.0** | anémophile (`pollination_mode="wind"`) |
   | Amaryllidaceae | 0.30 | 0.20 | 0.20 | visitée, pas primaire |

   ⚠️ Ajouter la clé dans **les 3 dicts** (même les 0.0 pour Urticaceae — explicite
   = pas de retombée sur le défaut). Vérifier que `build_pollinator_registry`
   (~ligne 638) lit toujours ces tables sans changement.

## Données indicatives par espèce (à étudier, calibrage post-test)

Champs sur le patron des espèces existantes (`cultivees.py`/`compagnes.py`).
Pose `floraison → add_rondelle pollinisateur` au stade fleuri pour que la
`resource_fn` nectar lise l'espèce (sauf ortie, anémophile : pas de rondelle
pollinisateur — elle ne nourrit pas les butineurs).

**Carotte** *(Apiaceae, `biennial`)* — rosette an 1 → ombelle an 2 :
- `family="Apiaceae"`, `life_cycle="biennial"`, `winter_strategy="dormant"`
- `foliage_density≈0.40`, `longevity_years=2`, `reproduction_rate≈0.06`
- stades : semis → **rosette** (basse, pas d'effet floraison — c'est le stade
  an-1) → **ombelle** (basse-moyenne, effet `floraison add_rondelle pollinisateur`
  — stade GATÉ à `age_years>=1.0`) → mature (récolte racine / graines).
- `keywords=["Comestible","Mellifère","Bisannuelle","Hôte"]`. Hôte machaon :
  pour CE tronçon, rester sur le pont chenille **générique** (le rattachement à
  une famille-hôte nommée = extension data du `LifeCycleBridge`, doc §7.2, à
  flaguer en ④/dette — NE PAS l'ouvrir ici sauf décision Nico).

**Ortie** *(Urticaceae, perennial)* — indicatrice azote, anémophile :
- `family="Urticaceae"`, `perennial`, `dormant`, `pollination_mode="wind"`
- `foliage_density≈0.50`, `longevity_years=8`, `reproduction_rate≈0.10`
- `family_effects` : `inject_field fertilite +0.03 local` (azote, patron minette)
- stades : semis → adulte vivace (`duration_weeks=0`, basse, `root_radius` moyen).
  **Pas** d'effet floraison-pollinisateur (anémophile). `keywords=
  ["Bioindicatrice","Comestible","Biomasse","Hôte"]`.

**Courgette** *(Cucurbitaceae, annual, `fruitier`)* — étalée, gros fruits :
- `family="Cucurbitaceae"`, `annual`, `die`, `fruitier=True` (patron Tomato —
  vérifier le gate `engine._tick_fruits` : `fruitier ET age_years>=maturity_years` ;
  `maturity_years=0` → fructifie dès l'année). `foliage_density≈0.60`.
- couvre-sol étalé : `canopy_radius` LARGE au stade adulte (occupation de sol →
  exerce la compétition). stades : semis → adulte (effet `floraison
  add_rondelle pollinisateur`) → mature (récolte). `keywords=["Comestible",
  "Fruitier","Couvre-sol","Mellifère"]`.
- ⚠️ si `fruitier=True` seul ne suffit pas à produire des fruits traçables
  (la nouaison `FRUIT_NOUAISON_WEEK` lit `REPRO_BY_SEASON`/profil reproducteur —
  cf. `plants/base/stades.py:64`), VÉRIFIER ce qui rend Tomato/AppleTree éligibles
  et reproduire le strict nécessaire pour la courgette. Possible petit ajustement
  moteur → golden à re-confirmer.

**Mâche** *(Caprifoliaceae, annual)* — couvre-sol d'hiver :
- `family="Caprifoliaceae"`, `annual`, `die` (mais germe en jours courts),
  `foliage_density≈0.30`, strate sol. `temp_min_growth` BAS (≈2 °C) pour
  « pousse quand tout stagne » (lit le gel ⑥). `reproduction_rate≈0.05`.
- stades : semis → adulte (effet `floraison add_rondelle pollinisateur` léger) →
  mature. `keywords=["Comestible","Couvre-sol","Rustique"]`.

**Ail** *(Amaryllidaceae, `biennial`)* — répulsif compagnon :
- `family="Amaryllidaceae"`, `biennial`, `dormant`, `foliage_density≈0.20`,
  strate basse, `longevity_years=2`, `reproduction_rate≈0.03`.
- `family_effects` répulsif (cf. décision Amaryllidaceae ci-dessus).
- stades : semis → **rosette/feuilles** (an 1) → **hampe** (an 2, GATÉ
  `age_years>=1.0`, effet floraison léger) → mature (récolte bulbe). `keywords=
  ["Répulsif","Comestible","Compagne","Bisannuelle"]`.

## Où écrire (garde-fou taille — `tools/compte_ldc.py`, seuil ~350 LDC pur)

- **Familles neuves** → `plants/base/familles.py` (mesurer après ajout ; si
  proche du seuil, ne déclarer en classe QUE celles à effet familial — ortie/ail
  — et laisser carotte/courgette/mâche en `family="…"` au niveau espèce).
- **Espèces** : carotte/mâche → `cultivees.py` (potager) ; ortie → `adventices.py`
  ou un nouveau `sauvages.py` selon la mesure (ortie n'est PAS un archétype de
  succession → ne PAS lui mettre d'`archetype`, sinon télescopage `WEED_CATALOGUE`) ;
  courgette → `cultivees.py` (fruitière, voisine de Tomato) ; ail → `compagnes.py`
  (répulsif compagnon) ou `cultivees.py`. **Décider à la mesure** ; si un fichier
  franchit ~350, basculer dans un fichier dédié et le signaler.
- **Brancher** : `species/__init__.py` + `plants/__init__.py` (ré-exports) +
  `plants/catalogue.py` (5 entrées `PLANT_CATALOGUE` : `"carotte"`, `"ortie"`,
  `"courgette"`, `"mache"`, `"ail"`). **NE PAS** toucher `WEED_CATALOGUE` ni
  `PERENNIAL_CATALOGUE`.
- `fields/population.py` : les 5 clés de famille dans les 3 dicts `_ATTRACT_*`.
- `sim/engine/croissance.py` : le gate annuel `biennial` (point chaud).

## Golden — re-figeage MAÎTRISÉ possible, sinon NEUTRE

Le smoke (`tests/test_golden.py`, 2 tuiles × 4 ans) plante un **jeu fixe**
d'espèces, **n'instancie AUCUNE** des 5 nouvelles. Donc :
- ajout de classes + entrées catalogue + tables `_ATTRACT_*` (lues seulement si
  l'espèce est plantée) ⇒ **NEUTRE**.
- le **gate biennial** dans `_avancer_stades` : ne doit s'activer que pour
  `life_cycle=="biennial"` → aucune espèce du smoke n'est bisannuelle ⇒ **doit
  rester NEUTRE**. Si le hash bouge, le gate fuit sur une espèce non-bisannuelle
  → BUG, pas un re-figeage.
- un éventuel **ajustement nouaison courgette** pourrait toucher le golden SI il
  modifie un chemin commun → dans ce cas re-figeage **MAÎTRISÉ** (dérive localisée,
  expliquée, annoncée) après confirmation que c'est attendu.

→ **Attendu par défaut : NEUTRE.** Tout mouvement de hash doit être expliqué
avant re-figeage.

## Validation

1. `python3 -m tests.test_golden` → PASS (hash inchangé sauf re-figeage maîtrisé
   annoncé).
2. `python3 -m tests.test_evergreen` → toujours PASS (non-régression ②).
3. **Nouveau test `tests/test_biennial.py`** (patron des suites existantes) :
   planter une carotte, simuler 2+ ans ; asserter (a) an 1 elle **reste au stade
   rosette** (ne monte pas : `current_stage` < index du stade fleuri) ; (b) an 2
   elle **atteint** le stade fleuri et pose `pollinisateur` ; (c) elle **meurt**
   après `age_years>=2`. Verrouille le gate.
4. **Attractivité familles neuves** : un test (ou extension de `test_population`/
   `test_attraction`) qui vérifie qu'une carotte fleurie nourrit le **syrphe**
   (Apiaceae=1.0) — preuve que `_ATTRACT_SYRPHE` est bien câblé.
5. **Sanity catalogue** : étendre `test_evergreen.test_catalogue_germination`
   (ou un test jumeau) pour les 5 nouvelles clés — instanciables + germent.
6. **Courgette fruitier** : vérifier qu'elle produit ≥1 fruit traçable (ou
   documenter pourquoi non, si la nouaison exige plus que `fruitier=True`).
7. `tools/compte_ldc.py` sur tout fichier touché : aucun > ~350 sans signalement.

## À faire en fin de tronçon

- Mettre à jour `00_etat.md` (③ ✅ + statut `biennial` vérifié/comblé, décisions
  familles, impact golden réel).
- **Entrée `journal/` + index `journal.md`** (catalogue enrichi ③ : +5 plantes,
  5 familles neuves + `_ATTRACT_*`, gate `biennial`, impact golden).
- Commit : `feat(catalogue) : +5 plantes lot 2 (carotte, ortie, courgette, mâche, ail) — 5 familles neuves + gate biennial`.
- Proposer ④ (faune parfums, golden-neutre) ou ⑤ (nouveaux pollinisateurs) —
  **pas** d'enchaînement auto.
