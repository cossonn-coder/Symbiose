# CONCEPTION — Floraison & fructification (grappe D84 + D86)

> Figé le 2026-07-18 (skill `/conception`). Sprint :
> `sprints/vegetal/floraison/sprint_floraison_fructification/`. Préalable biologique à D87
> (automate dirigé par le but).
> Diagnostic-first : cette conception corrige un **défaut structurel du modèle de
> floraison** révélé par le sprint DÉSYNCHRONISATION PHÉNOLOGIQUE (journal 119),
> pas une simple régression de calibrage.

## 0. Problème observé (Nico, F5, 2026-07-18)

- Le **pommier fleurit « début automne »**.
- Les autres fleurs (« espèces du sud ») apparaissent **à la semaine 6-7 de
  l'automne** (= `week_in_year` **S33-34**) et **disparaissent aussitôt**. → D84.
- En jeu, **quasi aucun fruit ne noue** : « une seule pomme sur le pommier ». → D86.

## 1. Diagnostic CONFIRMÉ (sonde empirique + lecture code)

### 1.1 Le modèle actuel (`sim/engine/floraison.py`)
DOUBLE PORTE, par plante vivante :
1. **Forçage thermique** : `gdd_accum` cumule `max(0, T−T_BASE_FLORAISON)` (base
   6 °C) chaque semaine, **remis à 0 à la semaine 1**. Porte ouverte quand
   `gdd_accum ≥ gdd_eff`, avec `gdd_eff = gdd_floraison − FLORA_GENE_SHIFT·(g−1)`
   (`FLORA_GENE_SHIFT = 200`, gène-tempo `phenologie_florale`, g>1 = précoce).
2. **Photopériode** : `daylength(wiy) ∈ [bloom_daylen_min, max]` (défaut
   **[13.5, 16.5] h**).
+ garde de maturité (`is_seed_bearing`). `floraison ∈ [0,1]` relaxe vers 1
(montée 0.35/tick) si **les deux** portes ouvertes, vers 0 (descente 0.50/tick)
sinon. La vue C# dessine une fleur au-delà de `floraison ≥ 0.5`.

### 1.2 Sonde annuelle sous la météo du jeu
Météo : `temp_norm = 11 − 7·cos(2π(w−4)/52)` (pic S30) ; `daylength =
12 + 4·cos(2π(w−25)/52)` (solstice S25). Cumul GDD (base 6 °C), reset S1 :

| Repère | Semaine |
|---|---|
| Fenêtre photopériode [13.5–16.5 h] OUVERTE | **S16 → S34** |
| GDD franchit **130** (pommier, seuil patché) | **S29** |
| GDD franchit **200** (DÉFAUT — toutes les autres espèces) | **S35** |

### 1.3 Cause racine — tout s'explique
- **Le cumul GDD-depuis-S1 place toute floraison en fin d'été/automne.** Le
  printemps (S11–S18) n'a quasi aucun degré-jour (T ne franchit 6 °C que ~S11).
  **Aucun mécanisme de floraison printanière** n'existe.
- **Pommier « début automne » ✅** — `gdd_floraison` avait *déjà* été rabaissé à la
  main 200→130 (sprint thermique) ; il fleurit **S29–34**, or l'automne = S27+.
  Le patch l'a sorti du « zéro floraison » sans corriger le placement.
- **« Aucun fruit sauf une pomme » ✅** — **toutes les espèces sauf le pommier**
  gardent `gdd_floraison=200` (franchi **S35**) alors que la photopériode **ferme
  S34** → **recouvrement = 0 semaine** → `floraison` **ne monte JAMAIS** → zéro
  nouaison. Seul le pommier (patché 130) peut fleurir → seule espèce qui fructifie.
- **« Fleurs du sud S33-34, disparaissent aussitôt » ✅** — pour une espèce au
  seuil 200, le GDD franchit près du **bord fermant** : recouvrement de **0-1
  tick** → `floraison` fait un pas de 0.35 (< SEUIL_FLEURI 0.5) puis retombe = un
  **flash** jamais compté comme « fleuri ». Pommier (S29-34) et espèces du sud
  (S33-34) sont **le même empilement d'automne**.
- **Aggravant** : `FLORA_GENE_SHIFT=200` (sprint désync) étale la variance mais ne
  corrige pas le placement structurel.
- **D86 secondaire (nouaison)** : même quand la floraison marche (pommier
  `insect`), `frac_nouaison = pollen/(pollen+POLLEN_DEMI)` sans plancher ; dose
  butineurs faible dans la démo → peu de fruits. À distinguer de la cause
  structurelle.

## 2. Modèle retenu — FORÇAGE THERMIQUE ÉVÉNEMENTIEL

**Décision (arbitrages Nico 2026-07-18)** : direction **B — typage phénologique
par espèce**, concrétisée en **modèle de forçage thermique** (le standard de
phénologie *GDD-to-bloom*), à la demande de Nico : « année chaude → floraison plus
précoce ; la chaleur est une variation continue toute l'année (météo +
ensoleillement) ; plus ou moins tardive par plante selon les gènes ;
biologiquement juste autant que possible ».

Dans `_tick_floraison`, par plante vivante :
```
si wiy == 1:  gdd_accum = 0.0 ;  bloom_week = -1        # reset annuel
gdd_accum += max(0.0, temp_locale - T_BASE_FLORAISON)   # temp.at_plot(r,c) : météo + ombre/ensoleillement
gdd_eff = cls.bloom_forcing_gdd - FLORA_GENE_SHIFT * (g - 1.0)   # seuil INDIVIDUEL (g>1 → précoce)
si bloom_week < 0 et is_seed_bearing(plant) et gdd_accum >= gdd_eff:
    bloom_week = wiy                                     # FRANCHISSEMENT → armement (1×/an)
en_fleur = (0 <= bloom_week) et (wiy < bloom_week + cls.bloom_duration)
cible = 1.0 si en_fleur sinon 0.0
taux = FLORAISON_MONTEE si cible > floraison sinon FLORAISON_DESCENTE
floraison += (cible - floraison) * taux
```

### 2.1 Les deux corrections structurelles
1. **Floraison = ÉVÉNEMENT de durée bornée.** Armée au *franchissement* du seuil
   (`bloom_week`), elle fleurit `bloom_duration` semaines puis fane. Remplace
   l'état permanent « GDD ≥ seuil » (qui durait tout l'été) → **fin de la
   floraison éternelle** ET **fin de la fugacité** (durée garantie).
2. **Seuils `bloom_forcing_gdd` BAS et par saison-cible** + **porte photopériode
   SUPPRIMÉE** (`bloom_daylen_min/max` retirés). C'est la porte photopériode qui
   créait le recouvrement nul de S34. Le placement saisonnier vient désormais du
   *seul* seuil de forçage (bas → printemps, haut → automne).

### 2.2 Réponse point par point à la demande de Nico
| Demande | Mécanisme |
|---|---|
| Année chaude → floraison précoce | `gdd_accum` monte plus vite → seuil franchi plus tôt → `bloom_week` plus petit |
| Chaleur continue (météo + ensoleillement) | `gdd_accum += max(0, temp.at_plot(r,c))` : `temp.at_plot` intègre déjà l'ombre maison et la météo hebdo |
| Plus/moins tardive selon gènes (même espèce) | `FLORA_GENE_SHIFT·(g−1)` abaisse le seuil du pied précoce (héritable, déterministe) |
| Biologiquement juste | forçage thermique = modèle standard de phénologie |
| Interconnexion (règle « tout coexiste ») | ombre maison → temp locale plus basse → accumulation plus lente → **floraison plus tardive à l'ombre** (gratuit) |

### 2.3 État & données
- **État plante neuf** : `bloom_week: int = -1` (semaine de franchissement, reset
  annuel). `gdd_accum` **conservé** (existe déjà, `instance.py:143`), `floraison`
  conservé. Tous **hors `_PLANT_ATTRS`** du golden.
- **Données espèce** : remplacer `gdd_floraison` / `bloom_daylen_min` /
  `bloom_daylen_max` (familles.py) par :
  - `bloom_forcing_gdd: float` — seuil de forçage (bas→printemps … haut→automne) ;
  - `bloom_duration: int` — durée de floraison **en semaines, fixe par espèce**
    (Nico 2026-07-18 : pommier ~3 sem court, annuelles estivales longues).
- **Calibrages actés** : pommier = **printemps** → **annuler le patch
  `gdd_floraison=130`** (perennials.py:197-207). `FLORA_GENE_SHIFT` **recalibré à
  la baisse** (~15-30) : à seuils bas, 200 rendrait un pied g=1.2 négatif ; ~20
  donne ±1-2 sem à ±σ (σ=0.10).

### 2.4 Table de calibrage de départ (à affiner en F5)
Correspondance GDD-cumulé → semaine de franchissement (sonde §1.2) :
`GDD 6→S14, 9→S15, 13→S16, 24→S18, 38→S20, 55→S22, 75→S24, 97→S26, 130→S29,
180→S33, 200→S35, 220→S37`.

| Groupe | Espèces (exemples) | `bloom_forcing_gdd` | franchit ~ | `bloom_duration` |
|---|---|---|---|---|
| Printemps précoce | Pommier, Cerisier, Violette, Fraise | 6–13 | S14–16 | 3–4 |
| Été | Tomate, Courgette, Tournesol, Bourrache, Phacélie, Consoude | 40–86 | S20–25 | 6–10 |
| Automne | Armoise (Asteraceae), asters, lierre | 180–220 | S33–37 | 4–5 |
| **Défaut** familles.py | (mid-été) | **60** | S22–23 | **6** |

Valeurs **de départ**, pas des vérités : le placement exact se cale en F5 (③).

### 2.5 Limite assumée (biologie « de manière générale »)
Les vrais **fleurisseurs de jours courts** (aster, lierre, chrysanthème) sont ici
approximés par « seuil de chaleur ÉLEVÉ → franchi en automne ». Le *résultat*
(floraison automnale) est juste ; le *mécanisme* n'est pas photopériodique. Un
second type « jour-court » (déclenché par `daylength` descendant sous un seuil sur
le limbe décroissant) est une **extension future** si Nico la demande — pas
maintenant : **un seul mécanisme = simplicité** (philo). Écart signalé.

### 2.6 Ce qui est CONSERVÉ
Gène-tempo `phenologie_florale` (rôle inchangé, seuil recalibré), garde de
maturité `is_seed_bearing`, relaxation montée/descente, synchronie des clones
(gène copié) vs étalement des semis (variance fondatrice), miroir sémiologique de
**sénescence** (`semiologie.senescence`, non touché — il concerne l'onset de
sénescence, pas le forçage floral). La nouaison en fin de floraison
(`decompo._tick_fruits`) reste branchée sur `floraison` (SEUIL_FLEURI /
SEUIL_NOUAISON / `a_fleuri`) — inchangée dans son principe.

## 3. Nouaison (D86 secondaire) — calibrage de la dose

Une fois la floraison replacée au bon moment (avec une durée franche), le pommier
fleurit plusieurs semaines en plein passage des butineurs → `pollen_recu`
s'accumule (`sim/engine/butineurs.py:102`) → `frac_nouaison` monte. Reste à
**calibrer** pour que « une belle floraison bien pollinisée = beaucoup de
fruits » :
- Mesurer `pollen_recu` d'un pommier mûr sur la floraison saine (banc dédié).
- Tuner `POLLEN_DEMI` (`decompo.py`, demi-saturation de `g(pollen) =
  pollen/(pollen+POLLEN_DEMI)`) et/ou le débit de dépôt des butineurs pour qu'une
  floraison bien visitée noue une fraction significative (cible indicative :
  frac ≥ 0.5 quand la densité pollinisatrice est bonne).
- **Sans plancher, invariant** : 0 pollinisateur → 0 fruit (pression écologique,
  philo #2). On ne touche PAS cette règle.

## 4. Coût perf
**Nul.** `gdd_accum` est déjà accumulé aujourd'hui ; on remplace deux tests de
porte par un test de seuil + un test d'intervalle de semaines ; un `int
bloom_week` par plante en plus. O(plantes/tuile), inchangé.

## 5. Découpage (perf-first, vue Godot en dernier — règle projet)

- **① Moteur — floraison retypée** (`sim/engine/floraison.py` + données espèces
  `plants/base/familles.py` + `plants/perennials.py` + `plants/species/*` +
  `plants/base/instance.py` pour `bloom_week`). Retirer `bloom_daylen_min/max` et
  `gdd_floraison` (y compris le patch pommier 130) ; ajouter `bloom_forcing_gdd` /
  `bloom_duration` ; recalibrer `FLORA_GENE_SHIFT`. Tests neufs : **placement**
  (chaque espèce fleurit dans SA saison-cible), **étalement** (σ>0 des semaines de
  floraison via le gène), **neutralité g=1** hors placement. **Golden re-figé
  maîtrisé SI** un fruitier mûr fleurit/noue dans le smoke (→ litière `fruit` →
  eco haché) ; **sinon NEUTRE** — à constater à l'implémentation, les deux cas
  prévus par le kickoff. Adapter `tests/test_desync_phenologie.py` et
  `tests/test_fruits.py` au nouveau modèle (ils forcent la `floraison`).
- **② Moteur — nouaison calibrée** (`sim/engine/decompo.py`,
  `sim/engine/butineurs.py`, éventuellement `sim/reproduction.py`) : banc de
  mesure de `pollen_recu` sur floraison saine, tuning `POLLEN_DEMI` / débit de
  dépôt, invariant « sans plancher » préservé. Golden selon fruits dans le smoke.
- **③ Vue Godot + banc F5** : le scalaire `floraison` est **déjà** exporté
  (`serialize.py`, désync ②) et **déjà** lu par la vue (`PlantRenderer.Organs.cs`,
  fleurs sur `Floraison ≥ 0.5`, désync ③) → sans doute **aucun** changement de
  rendu. Vérifier les **palettes de fleur** printemps/été/automne des espèces
  concernées, poser un **banc d'observation** floraison→pollinisation→nouaison→
  fruit sur une année, F5 Nico. **Golden intact.**

## 6. Ce qu'on ne fait PAS (anti-scope-creep)
- Pas de vrai mécanisme photopériodique jour-court (approximé par seuil élevé —
  §2.5) ; extension future si demandée.
- Pas de modèle de dormance/chill hivernal (option C écartée : sur-dimensionné).
- Pas de renommage du gène `phenologie_florale` (garde sa clé — churn/golden).
- Pas de refonte de l'arc pollinisation (butineurs, champs) — on ne fait que
  **calibrer** la dose au ②.
- Pas de touche au miroir sémiologique de sénescence (hors sujet).
