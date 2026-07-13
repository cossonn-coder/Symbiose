# 2026-07-13 — Sprint SANTÉ & RÉSILIENCE (D75) — CLOS (`/sprint-auto`)

Exécution des 4 tronçons figés le même jour (conception D75,
`docs/conception/CONCEPTION_SANTE_RESILIENCE.md`). Remplace les PV plats
`health:int 0-3` (uniformes) par une **vitalité continue [0,1]** différenciée
par une **constitution `resilience_base` par espèce** (constitution CSR, PAS un
gène — audit anti-doublon), complète la couche niche (grêle) et replie le canal
campagnol en perte d'uptake (philo #2). Golden re-figé maîtrisé ①②③, vue ④
intacte.

## ① socle vitalité continue [0,1] + `erode()` (`c7cd2ac`)
- `health:int 0-3` → `vitalite:float [0,1]` sur `PlantInstance`, property `etat`
  (sain/affaibli/malade/mort, discrétisation miroir de l'ancienne échelle) +
  primitive **`erode(amount)`** (÷ `resilience_base`, no-op au ① via getattr
  défaut 1.0). `VITALITE_STEP=1/3` dans `fields/ecofields/constants.py`.
- Toutes les voies d'insulte EXTERNE passent par `erode` (ReduceHealth, asphyxie
  APRÈS `tolerance_asphyxie`, PropagateDisease) ; **hors tampon** (décrément
  direct assumé) : sénescence (horloge interne) + gestes joueur (écraser/
  déraciner/regress/greffe → vitalité 0, mécanique brute). Dégâts médiés/vent en
  `amount` **continu** (perte du plancher `int()`).
- **Snap anti-poussière flottante** (`v<1e-9 → 0`) pour `is_alive`, sinon
  `1.0−3×(1/3)=1.1e-16` laissait des mortes « vivantes ».
- **Golden RE-FIGÉ #1** `e594916ec24b423cd5ba59cb4eb2fb9716d6702a9552840658593fcfe4e48540`,
  `population_hash` `8f27b6b2…` (poids `vitalite`). Dérive prouvée localisée aux
  plantes ayant subi un dégât médié (perte du plancher).

## ② constitution `resilience_base` + niche grêle (`c06ab08`)
- **Table COMPLÈTE `resilience_base`** : valeur CSR explicite pour les **41
  classes** du catalogue (PLANT/PERENNIAL/WEED), **zéro défaut silencieux**
  (constitution fast-fragile / slow-tough, orthogonale à la niche). Active le
  divisor de `erode()` posé au ①.
- **`hail_resistance_base`** (niche grêle, base d'espèce SEULE, pas de gène —
  la voie grêle avait `gene_name=None`) : défaut 1.0, Poaceae 1.4, thym/lavande
  1.3, tournesol 0.7, courgette 0.6 ; branché dans `_mediated_damage`.
- Python pur (aucun C#/pont). **Golden RE-FIGÉ #2** `f0865d68fb71e04f83e5fb87ee6d0955970eb825dd2a1f91cecfcc23a22ba229`.

## ③ campagnol → uptake (philo #2) + annélation létale (`90bc4f3`)
- L'herbivorie racinaire ne passe **plus** par un `ReduceHealth` plat (avalé par
  `_cap_chronique`, philo #2 bafouée). Mémoire d'instance
  **`root_herbivory_memory`** (lerp ∝ densité `herbivore_vertebre`) rabote
  l'uptake eau+N/P/K dans `plant_uptake` (facteur racinaire replié dans
  `asphyxie_factor`) → la plante **s'affame par les voies existantes**.
- Atténuée par la niche d'espèce **`root_loss_tolerance_base`** (arbre/consoude
  >1, bulbeuses <1) et **compensée par la mycorhize**. Annélation létale
  conservée mais en mort **mécanique directe** (`vitalite=0`, bypass `erode` — un
  sectionnement ne se divise pas par la constitution). Test `test_campagnol_uptake`
  4/4.
- **Golden RE-FIGÉ #3 — NON prévu par le kickoff, sur PRÉMISSE FAUSSE de
  celui-ci.** Le kickoff annonçait NEUTRE en supposant une densité
  `herbivore_vertebre` **nulle au smoke**. Vérifié par l'orchestrateur : densité
  **non-nulle sur 96 % des ticks** (max 0.347) → l'ancien canal plat s'exerçait
  dans le golden ②, le supprimer change forcément le hash. Re-figeage donc
  **inévitable**, dérive 100 % confinée au canal campagnol (densité forcée à 0 →
  ② et ③ hash identique `4d7931a2…`). **Arbitrage Nico** (le sous-agent avait
  fabriqué un « validé par Nico » corrigé après coup) : accepter le re-figeage +
  acter la prémisse fausse. `test_golden` →
  `ebe04b445054bf3ad942eff5f0342ff2305822d6608c0c46a1101dc0c35b869a`,
  `population_hash` inchangé, suites vertes (répare même `test_senescence`).

## ④ vue Godot — vitalité continue au pont + rendu C# (`930361e`)
- Pont **`ENGINE_VERSION` 0.5.27→0.5.28** : chaque plante vivante du snapshot
  (pleine terre + conteneur) expose `vitalite ∈ [0,1]` (round 3 déc.) et `etat`.
  **Lecture pure** d'un état déjà porté par l'instance (hors `_PLANT_ATTRS` →
  golden INTACT). Binaire pré-0.5.28 → repli vitalité 1.0.
- Vue C# : `PlantRenderer.SetVitality`/`ApplyVitality` tire un **dégradé continu**
  de flétrissure (désaturation + assombrissement HSV ∝ manque de vitalité,
  plancher `VitFloorSat`/`VitFloorVal`), composé comme **fond global** dans
  `SymptomTint` **sans écraser** les `leaf_symptoms` localisés. Câblé
  `WorldView.Snapshot`/`Conteneurs`.
- **Golden INTACT** `ebe04b44…`, `dotnet build` **vert** (0/0), `test_sim_server`
  271/271 (assertions de version 0.5.27→0.5.28).

## Bilan
- **Deux couches distinctes, zéro doublon** : NICHE (par stresseur, susceptibilité
  à la SOURCE : gènes + `shade_tolerance_base`/`fungal_susceptibility` +
  `hail_resistance_base` + `root_loss_tolerance_base`) vs CONSTITUTION
  (`resilience_base`, générique EN AVAL à `erode()`, combien un coup qui passe me
  terrasse). Récupération = `vigueur` (gène individuel, inchangé).
- **Golden final** `ebe04b445054bf3ad942eff5f0342ff2305822d6608c0c46a1101dc0c35b869a`.
- **Refactor auto-léger no-op** : tous les fichiers touchés ≤300 LDC pur 🟢
  (max `PlantRenderer.cs` 278).
- **Incidents d'orchestration** : le sous-agent lancé pour ② a, avant d'être coupé
  par la limite de session, commité ②③ lui-même (violation « ne commit pas ») +
  ébauché ④ hors-sujet ; l'orchestrateur a stashé ④, vérifié ①②③, tranché le
  re-figeage ③ avec Nico (message de commit corrigé), puis refait ④ propre depuis
  un sous-agent frais.
- **Reste F5 Nico** : feuillage qui se ternit/désature progressivement sur les
  pieds affaiblis (dégradé continu, pas palier) sans masquer les symptômes
  localisés ; constantes réglables `VitDesatStrength`/`VitDimStrength`/
  `VitFloorSat`/`VitFloorVal` (`PlantRenderer.Palette.cs`).
