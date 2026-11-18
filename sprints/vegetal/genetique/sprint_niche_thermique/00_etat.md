# Sprint NICHE THERMIQUE — état (D139, sprint ② sur 3)

> Conception figée le 2026-11-16 : `docs/vegetal/genetique/conception_niche_thermique.md`
> (à lire en entier). **Prérequis** : `sprint_genetique_infinitesimale` CLOS (registre des
> caractères, unités en °C, F). Suite : `sprint_caracteres_vivants`.

## But
Le basilic meurt du froid d'automne, la mâche passe l'hiver, la canicule grille la plante
assoiffée au soleil, et chaque lignée porte sa plage vivable en °C, qui dérive de
génération en génération.

## Diagnostic d'origine (vérifié au code le 2026-11-16, détail §1 de la conception)
Mort calendaire aux semaines 49-52 (mi-février) · gel limité au stade `semis` · aucun dégât
de froid sans gel · nuit type au lieu de la plus froide (≈ 7 semaines de gel/an [seed 42,
sol nu]) et T_air hebdo ≤ 24,9 °C [8 ans, seed 42].

## Décisions clés (Nico, 2026-11-16)
- T1 **Le moteur ne tue pas, la plante meurt** : plus de mort calendaire ; sénescence de fin
  de cycle propre à la plante ; pas de filet de vieillesse arbitraire.
- T2 Nuit la plus froide + jour le plus chaud ; T_feuille = soleil × soif.
- T3 Plage d'espèce + 3 caractères en °C (`rusticite_froid` refondu, `limite_froid`,
  `limite_chaud`) + endurcissement et acclimatation en °C.
- T4 Signes par paliers (froid → confort → chaud), sans chiffre. T5 Gel sur tous les stades.

## Golden
Départ = hash de fin du sprint ①. ① **RE-FIGÉ annoncé** (nuit la plus froide) · ②
**RE-FIGÉ annoncé** (clés neuves + `rusticite_froid` en °C) · ③ **RE-FIGÉ annoncé, dérive
large** (dates de mort des annuelles) · ④ INTACT · ⑤ INTACT.

## Tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_temperatures_extremes.md` — nuit la plus froide, jour le plus chaud, T_feuille | **FAIT** 2026-11-18 (`8c55f4a`) |
| ② | `02_niche_caracteres.md` — niches des 52 espèces, 3 caractères, plasticité, coût | **FAIT** 2026-11-18 (non commité) |
| ③ | `03_reponse_mort.md` — dégâts gradués, fin de la mort calendaire, fin de cycle | **FAIT** 2026-11-18 (non commité) |
| ④ | `04_signes.md` — posture thermique et marques, voix | à faire |
| ⑤ | `05_vue.md` — postures et teintes, banc `niche_thermique`, recette F5 | à faire |

## ① FAIT (2026-11-18)
- `fields/ecofields/thermique.py` : `t_min_nuit_at` = **nuit la plus froide** (nuit type −
  `ECART_NUIT_FROIDE`·(1−couvert)·(1−nébul)) ; ancienne formule gardée en
  `t_min_nuit_type_at` ; `t_max_jour(t_air, nebul)` = T_air + (`AMPLITUDE_DIURNE` +
  `ECART_JOUR_CHAUD`)·(1−nébul). Constantes 3,0 / 7,0 / 5,0 dans `constants.py`.
- Lecteurs : gel (`boucle.py`) et glace (`glace.py`) → nuit la plus froide ; **rosée/givre →
  nuit type** (bilan de toutes les nuits, calibrage D111 conservé).
- `sim/engine/feuille.py` : `t_feuille(plant, eco, t_air, nebul)` + `soif` = stress hydrique
  instantané sur `eau_percue` (pas `drought_memory`, trop lente). Aucun lecteur (③).
- **Écart au kickoff** : `t_max_jour` sans `eco, r, c` (l'air est uniforme ; soleil et soif
  sont dans `t_feuille`). **Garde du gel levé** : `boucle.py` ne gelait que si T_air < 0
  (8 sem./8 ans [seed 42]) → la nuit la plus froide n'aurait rien changé ; chaque plot
  décide maintenant par sa nuit, log seulement si sév > 0.
- Mesures (`mesures/mesure_extremes.py`, seed 42, 8 ans, sol nu sans vent) : nuits < 0 °C
  54 → 113 semaines (6,8 → 14,1/an [n=1 seed]), min −7,8 → −10,6 °C ; jour le plus chaud
  max 35,9 °C (T_air 24,9). Smoke 5,99 → 5,58 s [1 run chacun] ; voie gel ≈ 0,01 s [cProfile].
- Golden **RE-FIGÉ** `3927690e…` → `72896cbd4fa9e596d23cf1c8ccc6101e744d694a0c7983e5c18bfea2fdd2c575` :
  1ʳᵉ divergence = gel des semis en W1 (T_air 7,2 °C, nuit claire) ; 2 → 26 lignes de gel,
  le reste en découle. Suites vertes : temperatures_extremes (neuve, 28/28), meteo_heterogene,
  rosee, mare_vivante, couvertures, senescence, stress_chronique, evergreen, evenements,
  microbiome_clim, signes_legende, humectation, caracteres, genetique, heredite, population.
- F5 : la glace des mares prend plus souvent (lit la nuit la plus froide) — à regarder.

## ② FAIT (2026-11-18)
- Niche d'espèce : 5 attributs sur `PlantBase` (`familles.py`, défauts —/−6/10/32/45) +
  une ligne par espèce sur les **52** (tableau §7, aucune absente, vérifié par le test).
- Registre : `rusticite_froid` en °C (0, σ 1,5, ±6, adaptogène, même canal) ;
  `limite_froid` (0, σ 1,0, ±4) et `limite_chaud` (0, σ 1,5, ±6, adaptogène) **en queue**.
- `PlantInstance` : `lim_gel/lim_froid/lim_chaud/lim_brul` (source unique ③④ ; `lim_froid`
  = −∞ si `t_froid_lesion` None), `plasticite_c(nom, ampleur)` = ampleur·(expr−1)/(EXPR_MAX−1),
  `expressed_gene` renvoie le génotype seul pour un caractère non « facteur ».
  `heat_memory` (signal T_feuille > `t_chaud_stress − 5`, réf 10 °C, lerp 0,05) ↔
  `limite_chaud` dans `ADAPTOGENIC_GENES` (priming automatique), acclimatation ≤ 3 °C
  (`ACCLIM_CHAUD_MAX`). T_feuille via `feuille.t_feuille_de` (cœur pur : lumière et
  humidité ressentie déjà lues par `_update_physiology`, rien n'est relu).
- Coût : `cout_thermique` = 1 − 0,02·Σ parts positives des 3 caractères, **multiplié
  dans `cout_defense`** (donc mêmes sites croissance/convalescence, sans toucher aux appelants).
- Gel des semis (`boucle.py`) : sév = (`lim_gel` − nuit)/6, plus de `gene_name` ; filtre
  `semis` conservé. `TEMP_FROST_DAMAGE` n'est plus importé par `boucle.py` (constante gardée).
- Voix : niveau 2 encyclopédie de basilic, tomate, poivron, courgette, haricot, mâche,
  seigle (frilosité/rusticité en mots). Pont : libellés `limite_froid/limite_chaud`.
- Golden **RE-FIGÉ** `72896cbd…` → `9e83a0cb0338b9d280b41114e855780aff94ce52c47a0db76ba8d6f4f9b3b477` :
  1ʳᵉ divergence = gel W0 (chaque semis gèle sous SA limite ; 74 → 10 lignes de gel,
  les rustiques ne gèlent plus à 0 °C), le reste en découle ; clés `limite_*` au digest.
- Tests : `test_niche_thermique` (neuve, 24/24) ; `test_caracteres` mis à jour (33/33) ;
  120 suites lancées : vertes sauf `test_peripherie` et `test_population`, **rouges déjà
  sur HEAD `8c55f4a`** (pré-existant, hors tronçon, non diagnostiqué).
- **À trancher (calibrage)** : σ_A 1,5 °C de `rusticite_froid` donne des variétés de
  tomate à `lim_gel` **+2,8 °C** (golden : tirage −3,8 °C, F 0,9) — gel au-dessus de 0 °C,
  physiquement douteux (le froid sans gel est le rôle de `lim_froid`). Piste : borner
  `lim_gel ≤ 0`, ou σ_A plus petit. Non fait (hors spec).
- Taille : `species/sauvages.py` 370 LDC (🟡, était ≈ 362).

## ③ FAIT (2026-11-18)
- `sim/engine/reponse_thermique.py` (mixin) : nuit la plus froide calculée 1×/plante ;
  **gel tous stades** (`_mediated_damage(seulement_semis=False)` ; la grêle garde le
  filtre) ; **froid sans gel** `FROID_LESION_K` 0,25 pt/°C sous `lim_froid` (cause
  `froid`) ; **brûlure** `BRULURE_K` 0,5 pt/°C au-dessus de `lim_brul` (cause `brulure`).
- `T_feuille` calculée 1×/sem. dans `_avancer_stades` (nouveau param `nebulosite`),
  mémorisée `plant.t_feuille` (hors digest) ; relue par `heat_memory`, la brûlure et la
  nouaison. Feuille > `lim_chaud` → pas d'avance de stade (log `🔥 … stagne (chaud`) et
  **nouaison reportée** d'une semaine (`a_fleuri` gardé) dans `_tick_fruits`.
- **Mort calendaire supprimée** : `_winter_transition` ne tue plus (branches `die` et
  bisannuelle an 2 retirées, notées historiques) ; dormance/persistantes aux semaines
  40-43 (`SEMAINE_HIVER` + `DUREE_ENTREE_HIVER` 4, même dose qu'avant).
- **Fin de cycle** (`sim/engine/fin_de_cycle.py`) : annuelles ET bisannuelles,
  horloge `floraison_abs` (semaine absolue de 1ʳᵉ floraison, jamais remise à zéro —
  `bloom_week` l'est chaque s1) + `bloom_duration` + maturation (défaut 6) → −1/3 de
  vitalité par semaine, convalescence coupée, log `✿ … meurt (fin de cycle)`. Carotte :
  fleurit an 2 s12, meurt s26 → règle `age ≥ 2` retirée.
- **Graines** : sans dépôt, une annuelle finie en été ne laisse rien (`_reproduction` ne
  passe qu'en s39). Dépôt à la fin de cycle : archétype (à l'identique) + **gènes**
  (`find_father`/`heredite`/priming, au pied). Banc 3 ans, pic de vivants/an :
  bourse-à-pasteur [5, 9, 7] avec, [5, 8, 8] sans [n=1 seed] ; basilic, phacélie,
  moutarde [1, 0, 0] dans les deux cas — sans archétype, la succession ne les relève
  jamais (préexistant ; sur HEAD le [1,1,1] venait d'une annuelle qui ne mourait pas :
  `deposer_mort` n'abaisse pas la vitalité).
- Banc `mesures/banc_reponse_mort.py` (perturbations coupées pour nuit/basilic/canicule) :
  nuits forcées 6/7/8 °C → basilic mort en 3/4/5 sem. (cible 3-5) ; basilic semé s12 :
  nu mort s32, paillé (litière ≈ 1) s33, voilé s36 — tous de froid [seed 42] ; mâche et
  seigle semés s27 passent l'hiver (vitalité min 0,17 / 0,33), fleurissent s12 an 2,
  s'éteignent s25/s26 ; canicule 28 °C s16-19 : assoiffé au soleil T_f 50,8 °C → brûlé
  à mort, arrosé (40,0 °C) et ombragé (43,2 °C) vivants sans croissance.
- Perf [cProfile, 1 run, smoke neuf] : nuit froide 0,81 %, T_feuille + gate ≈ 0,2 %,
  brûlure 0,14 %, fin de cycle + dépôt 0,13 % → ≈ +1,3 % (budget 2 %). Smoke 5,3-5,6 s
  → 4,4 s [1 run] (moins de plantes).
- Golden **RE-FIGÉ** `9e83a0cb…` → `88cca899abcfe6912d76e9f2bb8108a142c24b5e0acda8238cca56a236adbe22` :
  1ʳᵉ divergence = W1, tomate/basilic/poivron tués par le froid sans gel (nuit ≈ 0 °C),
  haricot et tournesol en S2-3 (10 morts « froid », 0 avant) ; plus de mort `(annual)`
  (92 lignes, l'annuelle « mourait » 4×/hiver sans mourir) → 19 fins de cycle
  (bourse-à-pasteur 18, phacélie 1) ; 97 semaines « stagne (chaud » (bourse, trèfle) ;
  pommier gelé S04 an 1 (−0,29, rétabli). Vivants finaux 58 → 37. `population_hash.txt`
  re-capturé `ca58ecb6…` → `a9106f3b…` (même cause ; le reste du test vert).
- Tests : `test_reponse_thermique` (neuve, 16/16). Adaptés (le froid tue les semis
  tendres posés à l'équinoxe, ce que ces tests ne mesurent pas) : `test_parasite`,
  `test_stress_chronique`, `test_floraison_forcage` (froid neutralisé, commenté) ;
  `test_catalogue_lot2` (courgette semée s11, « a dépassé le semis vivante ») ;
  `simserver/taille.py` + `delta.py` (monde `full` : plus aucune plante du smoke n'atteint
  2 segments). 124 suites : toutes vertes sauf `test_peripherie` (préexistant).
- **Écarts au kickoff** : marques `froid`/`brulure` posées mais ignorées par
  `leaf_symptoms` (pas de PRIORITE/corpus : ④) ; `CAUSE_DE_RAISON` ne les connaît pas
  (→ « autre », ④). `heat_memory` lit la T_feuille de l'étape 6 (humidité avant uptake).
- **Constats pour Nico / suite** : (a) le monde smoke perd toutes ses cultures en S1-3
  (semis tendres à l'équinoxe) — couverture du golden à rediscuter (date de semis ou
  voile) ; (b) endurcissement du pommier plafonné à `lim_gel` ≈ −14 °C (expression 1,09)
  vs −30 °C visés (calibrage ②) ; (c) l'ombrière n'atténue que la lumière-SOL, pas
  `light_received` (le banc force 0,3) ; (d) le geste `pailler` (`eco.paillage`) ne
  réchauffe pas la nuit (seule la litière `om_fresh` compte) ; (e) tomate `lim_gel`
  +2,8 °C : pas de mort aberrante mesurée, la tomate meurt du froid sans gel
  (`lim_froid` 10 °C) bien avant.
- **Réponse à la sélection** (banc ①, cas (a), 10 ans, seed 42) : semis féraux site froid
  **+0,21 °C [n=85]** vs témoin −0,15 °C [n=126] (écart +0,36 °C ; avant ③ : +0,02 [n=80]
  vs +0,11 [n=96]) ; vivants an 10 : +0,80 °C [n=25] vs −0,15 °C [n=28] ; pool banque
  an 10 : +0,065 vs −0,372. Cible ≥ +1 °C **non atteinte** sur les semis ; la population
  vivante, elle, dérive de ≈ +0,95 °C [1 seed].

## REPRISE
Lire `CLAUDE.md`, ce fichier, puis le kickoff du premier tronçon « à faire » (④).

## Report du sprint ① (génétique infinitésimale, décision Nico 2026-11-16)
La réponse à la sélection sur `germination_thermique` (banc
`sprint_genetique_infinitesimale/mesures/banc_reponse_selection.py`, cas (a), parcelle
froide 10 ans) est NULLE : +0,02 °C [n=80] vs témoin +0,11 °C [n=96], cible ≥ +1 °C.
Le tri thermique à la levée (`_levee_triee`, `sim/succession.py`) existe déjà ; ce qui manque
est la **pression** : tolérances de levée (7-10 °C) ≫ σ_A 1,5 ; levées près de l'optimum ;
~9 levées/an ; aucun avantage à lever tôt. Ce sprint doit la créer et **re-mesurer avec ce
banc** avant clôture (un tronçon inerte n'est pas un succès).
