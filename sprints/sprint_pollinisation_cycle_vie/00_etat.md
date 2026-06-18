# État partagé — Sprint POLLINISATION & CYCLE DE VIE (implémentation)

> Conception FIGÉE : `docs/conception/CONCEPTION_POLLINISATION_CYCLE_VIE.md`
> (§A–§J figés, synthèse §K, découpe §L). Kickoff conception :
> `00_conception_kickoff.md`. Mémoire : [[design_pollinisation_cycle_vie]].
> Découpe = **7 tronçons** : ①→⑤ MOTEUR (re-fige le golden isolé), ⑥⑦ COUCHE
> JOUEUR (golden neutre, sprint distinct APRÈS le moteur).

## Avancement

- **① Floraison réelle + phénologie (A) — CLOS, golden NEUTRE.** ✅
  - `PlantInstance.floraison: float` + `gdd_accum: float` (instance.py).
  - `PlantBase.gdd_floraison / bloom_daylen_min / bloom_daylen_max` (familles.py,
    défauts estivaux placeholders).
  - `sim/engine/floraison.py` = `FloraisonMixin._tick_floraison` : double porte
    GDD (`T_BASE_FLORAISON=6 °C`, reset annuel) + photopériode (`daylength`) +
    maturité (`is_seed_bearing`) → relaxation de `floraison` (montée 0.35 /
    descente 0.50). N'émet AUCUN log, n'écrit que floraison/gdd_accum.
  - Câblé boucle.py (étape 9d, après croissance/sénescence ; la « phase floraison »
    proxy étape 10 reste en place jusqu'à ②/③).
  - **Golden INCHANGÉ** : `af3bfa8f…972f` (hors `_PLANT_ATTRS`, pas de log).
  - Sanity (non-régression du mécanisme) : annuelles estivales matures fleurissent
    (~0.58 pic sur 2 ans) ; tomate/poivron (morts précoces) & pommier (5 ans) à 0.

- **② Registre + champs par type + nectar (C/E) — CLOS, golden re-figé MAÎTRISÉ.** ✅
  - `PollinatorSpec` data-driven + `build_pollinator_specs()` (population.py) :
    3 types **abeille/syrphe/papillon**, attractivité florale PAR FAMILLE
    botanique (dicts placeholders §E.2), fenêtres photopériodiques distinctes.
  - `_make_nectar_grid(attractivite, defaut)` = ressource `Σ floraison ×
    préférence[famille]` / `FLOWER_REF` → **remplace `_flower_grid`** (proxy
    stade ≥ 2, conservé/annoté). `_auxiliaire_habitat_grid` pour le syrphe.
  - `build_population_specs()` ne renvoie plus le champ agrégé `pollinisateur` ;
    `EcoFields` compose `build_population_specs() + build_pollinator_specs()` →
    guildes = ravageur/auxiliaire/vers + abeille/syrphe/papillon.
  - `EcoFields.pollinator_density(r,c)` = somme des 3 types ; lu par
    `pollinator_reach` (reproduction.py) et `vigueur_pollinisateur` (vigueur_macro.py,
    borné [0,1]). L'abeille réutilise le canal sprite `_SALT_POLLINISATEUR` (continuité).
  - **Golden PRINCIPAL re-figé** : `af3bfa8f…972f` → **`08f18502…f9b3`**. Dérive
    par le SEUL canal `pollinator_reach` (densité nectar-réelle au lieu du proxy
    stade≥2) → brassage génétique des descendants sur 4 ans. Déterministe (2 runs
    identiques), état final sain (46 plantes, succession normale).
  - **Golden de champ `population_hash.txt` re-figé** : `6dc7004d…` → `6caab9d7…`.
  - Tests adaptés (guildes : test_population/attraction/genetique/simserver).
    Sanity : l'abeille décolle (nectar réel) et dort l'hiver (dormance OK).

- **③ Butineurs déterministes (F) — CLOS, golden NEUTRE.** ✅
  - `PlantInstance.pollen_recu: float` (instance.py) — accumulateur conspécifique,
    écrit par les butineurs, lu par PERSONNE à ce tronçon (④ le lira). Hors digest.
  - `fields/foragers.py` NEUF (split de population.py, garde-fou taille) :
    `ForagerParams` (n_max/substeps/perception/deposit/recharge), `ForagerAgent`
    (snapshot), `sample_foragers(field, species_grids, params, seed, wiy)` = PURE
    & déterministe (agents dérivés densité+`_hash_noise`, recréés chaque tick §F.2),
    marche par montée de gradient + constance florale (dépose si conspécifique,
    re-ciblage → charge perdue §F.4). Duck-typé sur le champ → aucun cycle.
  - `build_pollinator_registry()` factorisé dans population.py (source UNIQUE
    attractivité+fenêtres+`forager`), `PollinatorSpec.forager` ajouté.
  - `sim/engine/butineurs.py` NEUF (`ButineurMixin._tick_butineurs`) : construit la
    carte des fleurs PAR TYPE (floraison × attractivité, anémophiles écartées) +
    index plot→plantes, appelle `sample_foragers`, applique les dépôts à
    `pollen_recu` (réparti ∝ floraison), range les agents dans `eco.foragers`.
    Câblé boucle.py étape 13c (après tick_populations). `eco.foragers` (transient).
  - Snapshot : bloc `foragers` par tuile `[guild,r,c,x,y,target,charge]` ; pont
    **0.3.8 → 0.3.9** (test structures adapté). **Golden INCHANGÉ** `08f18502…f9b3`.
  - Tailles : population.py 344, foragers.py 107, butineurs.py 53 (tous < 350).
  - Sanity : bosquet phacélie dense → pollen déposé (total 40.5 / 2 ans, pas de
    reset avant ④), déterministe (2 runs identiques), 0 butineur l'hiver (dormance).

- **④ Nouaison pollinisée (B) — CLOS, golden NEUTRE.** ✅
  - `PlantInstance.a_fleuri: bool` (instance.py) — front de floraison : armé quand
    `floraison ≥ SEUIL_FLEURI`, consommé à la nouaison. Hors `_PLANT_ATTRS`.
  - `sim/engine/decompo.py:_tick_fruits` RÉÉCRIT : nouaison **en fin de floraison
    PAR PLANTE** (armée à `SEUIL_FLEURI=0.5`, nouée quand `floraison < SEUIL_NOUAISON=0.2`)
    + gate `age_years ≥ maturity_years` — **remplace `FRUIT_NOUAISON_WEEK`** (import
    retiré ; constante conservée dans calendrier.py). Fraction nouée `frac` :
    `self`/`wind` → 1.0 (plein) ; `insect` → `frac_nouaison(pollen_recu) =
    pollen/(pollen+POLLEN_DEMI)` (Monod, **SANS plancher** : 0 pollen → 0 fruit, §B.2).
    `n = round(frac × |organ_sites|)` premiers sites ; `pollen_recu` remis à 0.
  - Câblage boucle.py étape 15c (commentaire mis à jour, appel inchangé).
  - **Golden INCHANGÉ** `08f18502…f9b3` : aucun fruitier mûr ne fleurit dans le
    smoke (tomate meurt w2-3, pommier maturity 5 > 2 ans → floraison nulle).
  - `tests/test_fruits.py` adapté (helper `_nouer` = pleine floraison→fanaison ;
    nouveau test [7] modes : insect 0-pollen→0 fruit, dose forte→plein, self→plein ;
    24/24). `tests/simserver/morts.py::test_pommier_fruite` adapté (la nouaison
    suit la fanaison fin d'été, plus la semaine 14 ; pommier full noue grâce aux
    butineurs du jardin — 158/158).
  - Sanity (verger full) : pommier fleurit ~w33, noue 1 fruit ~w36 (pollen 2.25
    déposé par butineurs sur l'arbre isolé), déterministe.

- **⑤ Ponts de cycle de vie (D) — CLOS, golden re-figé MAÎTRISÉ.** ✅
  - `fields/lifecycle.py` NEUF (mirror de `foragers.py`, garde-fou taille) :
    `LifeCycleBridge` (data : larva/larva_nourrie/adult/resource_fn + fenêtre ponte
    + taux ponte/matur/métam/perte/famine, placeholders §D.5), `larval_field_names`,
    `tick_bridges` PURE & déterministe (ponte→maturation→famine→métamorphose, §D.3),
    duck-typée sur `eco`. N'importe PAS `population` (les ponts y sont CONSTRUITS) →
    aucun cycle ; reçoit la photopériode de l'appelant (copie locale `_smoothstep`).
  - `population.py` : `bridge` ajouté à `PollinatorSpec` ; 2 ponts
    `_BRIDGE_PAPILLON` (chenille, ressource=`_foliage_grid`, +herbivorie) et
    `_BRIDGE_SYRPHE` (syrphe_larve, ressource=`_ravageur_grid`, −ravageur) attachés
    à papillon/syrphe (abeille=None) ; `build_lifecycle_bridges()` (source UNIQUE) ;
    **`syrphe_larve` ajouté aux prédateurs du ravageur** (`predators=("auxiliaire",
    "syrphe_larve")`).
  - `ecofields/container.py` : `eco.larvae` (4 GridField [0,1] : chenille(_nourrie),
    syrphe_larve(_nourrie)) ; `_predator_field` (résout populations PUIS larvae) ;
    `tick_lifecycle_bridges` (délègue à `tick_bridges`, photopériode `daylength`).
  - `perturbations.py` : **`HERBIVORY_GAIN` lit `(ravageur + chenille)`** (chenille
    via `eco.larvae`, garde-fou `getattr`).
  - Câblé boucle.py **étape 13d** (APRÈS guildes 13b & butineurs 13c, ordre §K.2).
  - **INVARIANT §D.6 PROUVÉ** : ponte neutralisée (larves=0 partout) → golden
    **bit-identique** au pré-⑤ `08f18502…f9b3` → toute dérive vient des seuls cycles.
  - **Golden re-figé MAÎTRISÉ** : `08f18502…f9b3` → **`4f9fad91…1260`**. Dérive par
    (a) chenille→herbivorie ↑, (b) syrphe_larve→prédation ravageur → densités →
    santé/brassage. Déterministe (2 runs =), état final sain (69 plantes/110 sem).
  - **Golden de champ `population_hash.txt` re-figé** : `6caab9d7…` → `71f7ddda…`.
  - `tests/test_lifecycle.py` NEUF (invariant 0-adulte/chenille-0 ≡ ravageur,
    chenille mord seule, cycle syrphe_larve→syrphe, famine, déterminisme — 6/6).
    Toute la suite verte (golden, population, attraction, fruits, croissance…).
  - **⚠ Garde-fou taille SIGNALÉ** : `container.py` **356** & `population.py` **354**
    LDC pur (seuil ~350) — fichiers CŒUR pré-existants déjà à ~345, +10/+11 par l'arc
    (responsabilité unique préservée, commentaires pédago non sacrifiés). Split de
    `container.py` = candidat futur, hors périmètre surgical ⑤.

- **⑥ Ruche & miel (H/I) — CLOS, golden NEUTRE.** ✅
  - `Structure` (litiere.py) : +`essaim`/`miel` (0.0, inutilisés par bac/pile) ;
    `STRUCTURE_ACCEPTE["ruche"] = frozenset()` (n'absorbe AUCUNE litière → `accepte()`
    faux, `tick_structures` la traverse sans rien faire, contenu toujours vide).
  - `fields/apiculture.py` NEUF (PURE, duck-typé sur eco, miroir lifecycle/foragers) :
    `tick_ruches(eco, tile, plants)` — **no-op STRICT si aucune ruche** (retour AVANT
    toute lecture de champ → golden NEUTRE §H.3). Capture/déclin de l'essaim ← champ
    `abeille` LOCAL (≥`ESSAIM_MIN` croissance saturante, sinon famine §H.2) ; miel ←
    `res_abeille` LOCAL (réutilise `_make_nectar_grid` + registre §E, SOURCE UNIQUE),
    `miel += MIEL_RATE·essaim·nectar`, plafond `MIEL_MAX`. Importe population, jamais
    l'inverse → aucun cycle.
  - `fields/population.py` : `_abeille_habitat_grid` (= `_pollinisateur_habitat_grid`
    + bump LOCAL des ruches peuplées, §H.2, lit `eco.structures` en duck-type) attaché
    à l'abeille (papillon garde le générique) ; `RUCHE_HABITAT_W`.
  - `sim/actions/ruche.py` NEUF : `poser_ruche` (MODÉRÉ, binaire, modèle `poser_bac`),
    `recolter_miel` (canal récolte FAIBLE, miel→Vigueur ×`MIEL_VIGUEUR_RATIO`, **gaté
    par équipement = palier maîtrise** `CONCEPT_ABEILLES="pollinisation"` ≥ `SEUIL=3` ;
    sans équipement → récolte partielle `RECOLTE_SANS_EQUIP`, alarme/piqûre §J = ⑦ ;
    réserve vide → 0 sans Vigueur dépensée), `equipe()`. Coûts/objets dans couts.py,
    ré-exports __init__.py.
  - Câblé boucle.py **étape 13e** (APRÈS guildes 13b, lit `abeille` fraîche).
  - Pont **0.3.9 → 0.4.0** : `structures` gagne `essaim`/`miel` ; verbes `poser_ruche`
    (target plot) & `recolter_miel` (target structure index) routés. Round-trip serveur
    confirmé. Test simserver `structures.py` : assertion version 0.3.9 → 0.4.0.
  - **Golden INCHANGÉ** `4f9fad91…1260` (le smoke n'instancie aucune ruche).
  - `tests/test_ruche.py` NEUF (poser, capture/déclin, miel monte/plafonne/0-sans-fleur,
    habitat §H.2, récolte équipée/partielle/vide, neutralité no-op, déterminisme — 20/20).
    Toute la suite verte (golden, structures 65, sim_server 158, population, attraction,
    lifecycle, fruits, vigueur, maîtrise, génétique, croissance…).
  - **⚠ Garde-fou taille SIGNALÉ** : `population.py` **363** LDC pur (seuil ~350) —
    déjà flagué à 354 au ⑤, +9 par `_abeille_habitat_grid`+`RUCHE_HABITAT_W` (§H.2
    appartient aux habitat_fn de la couche registre ; le sortir créerait un cycle
    population↔apiculture). Responsabilité unique préservée. Split = candidat futur.

- **⑦ Piqûre — alarme émergente (J) — CLOS, golden NEUTRE.** ✅ (PART MOTEUR ;
  piqûre temps réel laissée au F5 Godot, hooks posés — décision Nico : Godot pas
  sur la VM, périmètre « moteur + hooks ».)
  - `PlantInstance` inchangé : l'alarme est un CHAMP, pas un attribut de plante.
  - `fields/alarme.py` NEUF (PURE, duck-typé sur `eco`, miroir apiculture/foragers/
    lifecycle — garde-fou taille) : `declencher_alarme(eco,r,c,intensite=ALARME_DEPOT)`
    (dépôt cumulatif borné, `GridField.add`) + `tick_alarme(eco)` (décroissance
    × `ALARME_DECAY=0.5`, snap à 0 sous `ALARME_FLOOR=0.01` → liste snapshot creuse).
    N'importe PAS `sim` → aucun cycle (sim/actions appelle, jamais l'inverse).
  - `ecofields/container.py` : `eco.alarme` (GridField [0,1], transient, à 0 au repos).
  - **Déclencheurs (philo #1)** : `sim/actions/gestes.ecraser` dépose l'alarme quand
    `guilde == "abeille"` (phéromone APIENNE — un ravageur écrasé n'en pose pas) ;
    `sim/actions/ruche.recolter_miel` gagne un param `eco` (optionnel, dégradation
    gracieuse) et dépose l'alarme au plot de la ruche SANS équipement (avec équipement
    = enfumoir → aucune). Routeur `actions.py` passe `eco` à `recolter_miel`.
  - Câblé boucle.py **étape 13f** (APRÈS ruches 13e) : décroissance hebdo. PUR PUITS —
    n'écrit QUE `eco.alarme`, jamais un champ figé → no-op de fait sans alarme posée.
  - Pont **0.4.0 → 0.4.1** : snapshot expose `alarme` par tuile = liste CREUSE
    `[[r,c,intensite],…]` (foyers > 0). PAS de verbe neuf (effet de bord des verbes
    existants). Round-trip confirmé : `ecraser` abeille (T0,2,2) → `alarme:[[2,2,1.0]]`.
  - **Golden INCHANGÉ** `4f9fad91…1260` (le smoke n'écrase aucune abeille, ne récolte
    aucun miel → alarme 0 partout ; et même active, pur puits non réinjecté).
    `population_hash.txt` inchangé `71f7ddda…`.
  - `tests/test_alarme.py` NEUF (déclencheur écraser abeille vs ravageur, récolte
    nue vs équipée vs sans-eco, décroissance+snap, neutralité PUR PUITS, déterminisme
    — 16/16). Suite verte : golden, ruche 20/20, lifecycle, sim_server 158/158
    (version 0.4.1), structures 65/65, population, attraction, fruits, vigueur 135/135,
    maîtrise 35/35.
  - **⚠ Garde-fou taille** : `container.py` ~359 LDC pur (+3 code : 1 champ + 2 init ;
    le bloc commentaire ⑦ est EXCLU du décompte) — déjà signalé à 356 au ⑤/⑥. `alarme.py`
    ≈20 LDC pur (très en-deçà). `population.py` non touché (reste à 363).

## Reste

- **Vue Godot — FAITE (confirmée F5 2026-06-18)**, golden INTACT (aucune ligne Python) :
  - `visuals/ForagerLayer.cs` (NEUF) : butineurs abeille/syrphe/papillon dessinés en
    AGENTS fleur-en-fleur (bloc snapshot `foragers`), saut entre fleurs conspécifiques
    voisines via index `_plantsByName` (clé = `name` FR, ≠ `species` anglais). Point
    pollen sur le dos quand l'agent porte ; **dépôt de pollen sur les fleurs butinées**
    (par atterrissage, accumulé/capé par saison, vidé à `OnSeasonEnd`). LOD ×4 + culling.
  - `visuals/MacroLife.cs` : abeille/syrphe/papillon RETIRÉS du nuage de densité
    (`NonDessine`) — ils vivent dans ForagerLayer (pas de double affichage).
  - `visuals/PiqureFlash.cs` (NEUF) + `world/WorldView.Piqure.cs` (NEUF) : **piqûre
    temps réel** « vue pure » — accumulateur déterministe `taux × alarme × densité
    abeille` (densité lue dans ForagerLayer), coût Vigueur LOCAL (écrasé au snapshot,
    pas de retour moteur), éclat éphémère. Câblé chaque frame en Saison.
  - `world/WorldView.Compost.cs` + `visuals/CompostStructure.cs` : ruche (essaim/miel)
    dessinée (3 hausses iso, remplissage miel + abeilles au trou de vol).
  - Calibrages exposés si retouche : `HopSec` (par guilde), `MaxPollenPerFlower`,
    `TauxPiqure`/`CoutPiqure`/`RayonPiqureCm`.
  - NON fait (assumé) : sprites larves/chenilles (`eco.larvae` non exposé au snapshot).

## Garde-fous

- Golden re-figé uniquement aux tronçons ② et ⑤ — **maîtrisé + annoncé**, isolé.
  ⑥ et ⑦ golden NEUTRE (ruche/alarme absentes du smoke).
- Déterminisme : `seed`/`_hash_noise`/`daylength`, jamais de RNG vivant.
- Couches `plants ← fields ← sim` ; ~350 l code pur (⑤ : 2 fichiers cœur signalés ;
  ⑥/⑦ : `population.py` 363 + `container.py` ~359, signalés).
- **SPRINT POLLINISATION & CYCLE DE VIE TERMINÉ côté moteur** : Partie I (①→⑤) +
  Partie II couche joueur (⑥ ruche & miel, ⑦ piqûre/alarme) CLOSES. Reste la **vue
  Godot** (piqûre temps réel + sprites), hors VM (F5 Nico). Reprise éventuelle : « lis
  `sprints/sprint_pollinisation_cycle_vie/00_etat.md` ».
