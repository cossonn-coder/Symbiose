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

## Reste (⑤)

- **⑤ Ponts de cycle de vie (D)** — chenille→papillon, syrphe_larve→syrphe ;
  `HERBIVORY_GAIN` lit `ravageur + chenille`. **Golden re-figé MAÎTRISÉ.** §D.
- **⑥⑦ COUCHE JOUEUR** (ruche/miel H/I, piqûre J) — sprint distinct, golden neutre.

## Garde-fous

- Golden re-figé uniquement aux tronçons ② et ⑤ — **maîtrisé + annoncé**, isolé.
- Déterminisme : `seed`/`_hash_noise`/`daylength`, jamais de RNG vivant.
- Couches `plants ← fields ← sim` ; ~350 l code pur ; doc d'abord (FAIT).
- **Reprise à froid** : « lis `sprints/sprint_pollinisation_cycle_vie/00_etat.md`
  puis lance le tronçon ⑤ (conception §D : ponts de cycle de vie) ».
