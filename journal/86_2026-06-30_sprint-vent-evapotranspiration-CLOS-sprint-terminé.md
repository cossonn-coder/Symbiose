## 2026-06-30 — Sprint VENT & ÉVAPOTRANSPIRATION (D37) — SPRINT TERMINÉ (⓪→⑦)

**Objet.** Faire du **vent** un facteur micro-climatique **complet** (solde **D37**)
et **enrichir l'évapotranspiration** pour rééquilibrer la rosée (re-résout **D39**).
Contrainte #1 = **perf** (Nico : « peur que le moteur soit trop lent »). Découpage
**perf-first 8 tronçons** ⓪→⑦ (§8 de `CONCEPTION_VENT_EVAPOTRANSPIRATION.md`).

**Ce qui a été livré (par tronçon).**
- **⓪ Référence perf + scatter (solde D32).** Boucle lumière-sol de `light.compute`
  passée d'un *gather* à un *scatter* (chaque ombre ne visite que la bbox de sa
  capsule) — **bit-identique**, golden INTACT `11eceeb9…`. Verrou
  `test_scatter_lumiere_sol.py`. Gain **×6 plancher** sur la boucle sol (pire cas
  dense). Budget : aucun tronçon n'ajoute > ~+10 % au tick.
- **① Masse d'air (golden NEUTRE).** Module neuf `sim/wind.py` (calqué `weather.py`,
  zéro RNG vivant) : `wind_at(seed,week)→WindState(force,direction)`, **direction
  O(1)** (somme de sinusoïdes, pas de marche cumulée O(week)). Non branché → golden
  intact `11eceeb9…`.
- **② Évapotranspiration enrichie (golden RE-FIGÉ LARGE, D39 vert).** Deux pilotes
  greffés dans `tick_hydrology` (zéro nouvelle traversée) : rayonnement
  `−EVAP_RAD_COEF·(1−nébulosité)` (contre-flux exact de la rosée) + vent
  `−EVAP_WIND_COEF·vent_masse_air`. Nébulosité DYNAMIQUE (le vent chasse la couverture).
  Golden `4a3cfe03…`. **D39 re-résolu PAR LE FOND** : pommier remeurt de sénescence
  à 59.8 ans (bilan hydrique rosée vs évaporation réel).
- **③ Champ d'abri spatial (golden RE-FIGÉ, perf +0 %).** Module neuf `fields/abri.py` :
  `compute_abri` spatialise la masse d'air en `eco.vent` (GridField par plot).
  Obstacles = maison + plantes hautes (≥80 cm → haie = brise-vent émergent, philo #1),
  capsule SOUS LE VENT réutilisant `_point_in_capsule` du LightField + scatter D32,
  venturi en frange. **CACHE** sur (obstacles, direction discrétisée) → géométrie non
  recalculée en régime permanent. Wind chill nocturne. Golden `4ce4ae3c…`. **Perf ≈ +0 %**
  grâce au cache → PAS d'off-ramp, ③ implémenté en entier.
- **④ Thigmomorphogénèse (golden RE-FIGÉ).** Gène neuf `port_trapu` (queue de
  `GENE_NAMES` → existants intacts) ↔ mémoire `wind_memory`, paire plastique
  (`_EXPR_MEMOIRE`, hystérèse) ; semis extérieur endurci. Dégât MÉCANIQUE médié
  `_wind_damage` (sév × étiolement/port_trapu × (1−paillage)). Transpiration foliaire
  (grande feuille au vent souffre plus de la soif). Golden `d948f648…`.
- **⑤ Pollinisation & dispersion anémophiles (golden INTACT).** Module
  `sim/engine/anemophilie.py` (pollen ∝ vent × floraison des congénères EN AMONT) ;
  butineurs cloués par grand vent ; trait `seed_dispersal` (barochore/anémochore) →
  la lignée féral migre sous le vent. Golden `d948f648…` (re-figeage prévu mais non
  survenu : `pollen_recu` hors digest, pas de fruitier anémophile mûr dans le smoke).
- **⑥ Vent × maladies fongiques (golden INTACT).** `fungal_disease` enrichie sans
  bonus/malus direct (philo #2) : **assèchement protecteur** (feuillage venté sèche →
  la ventilation est un remède) + **dispersion des spores** sous le vent (`_spore_load`
  somme l'inoculum des voisins au vent, voisinage déjà calculé → zéro passe neuve).
  Golden `d948f648…` (actif mais aucun flip discret du tirage).
- **⑦ Transport éolien de la litière & voix (golden RE-FIGÉ MAÎTRISÉ — clôture).**
  Module pur neuf `fields/ecofields/transport.py` : la litière LÉGÈRE (feuille/herbace)
  des plots EXPOSÉS est charriée vers leur voisin SOUS LE VENT *si* plus abrité
  (`vent[d] > vent[a]`, §5.6) → la matière s'amasse derrière un brise-vent comme une
  congère (philo #2 : flux → contrainte → hétérogénéité du sol). DÉTERMINISME : snapshot
  double-buffer (ordre indifférent), conservation stricte, zéro RNG. **PASSE
  CONDITIONNELLE** (perf, levier 5) : no-op les jours calmes (`wind_force <
  TRANSPORT_SEUIL`) → coût NUL. **Voix** : événement neuf `transport_litiere` (signe
  `🍃`, `sim/evenements.py`) → carnet descriptif→interprétatif (`sim/carnet.py`).
  Helpers conteneur `retirer_litiere`/`tick_transport`, câblé `boucle.py` 15d.

**Golden.** Re-figé maîtrisé à chaque cran, chaque dérive **localisée et expliquée** :
⓪/① `11eceeb9…` (intact) → ② `4a3cfe03…` (LARGE, nébulosité dynamique) → ③ `4ce4ae3c…`
(évaporation par plot + wind chill) → ④ `d948f648…` (port_trapu + transpiration/dégât)
→ ⑤⑥ `d948f648…` (intacts) → **⑦ `0d3ca606c815c9efb99e8e438a2e7c47bf7abd4d17dade8de0f51b892be1d6ad`**.
Au ⑦, sur 41 lignes de digest qui bougent le SEUL champ modifié est `drought_memory`
(4ᵉ–6ᵉ décimale) : la litière déplacée change la matière organique de surface → la
rétention d'humidité locale → la mémoire de soif. Aucun changement structurel.

**Tests.** `test_vent` **54/54** (18→26→36→42→54 au fil des tronçons),
`test_sim_server` **207/207**, `test_senescence` PASS (pommier 59.8 ans, **D39 vert**),
`test_journal` 15/15, `test_carnet` 19/19, `test_structures` 80/80, plus
`test_croissance`/`test_rosee`/`test_eau`/`test_fruits`/`test_stress_chronique` verts
aux tronçons concernés. C# non touché.

**Perf.** Tick stable ~52-54 ms (`tools/profile_tick.py`, monde smoke). ⓪ a *baissé*
le tick (−12 %, scatter). Aucun tronçon hors budget : ③ neutre (cache), ⑦ +2.2 ms
pire cas (+4.2 %, passe sautée les jours calmes).

**Dettes.** **D37 SOLDÉE** ; **D32** (⓪) et **D39** (②) confirmées vertes.
**« Arbres en drapeau »** (déformation permanente du port par vent dominant) reste
**hors périmètre → dette future**.

**Reste / pistes** (non bloquant, hors périmètre) : rendu C# des effets vent (vue,
dette D24) ; `transport_litiere` non encore consigné au ledger driver (`consigner`)
ni exposé au pont ; D38 (rosée/hygrométrie de l'air) ; D40 (sensibilité décompo T/H).
Aucun F5 requis pour ce sprint (moteur Python pur).
