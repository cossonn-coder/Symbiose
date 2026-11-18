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
| ② | `02_niche_caracteres.md` — niches des 52 espèces, 3 caractères, plasticité, coût | **FAIT** 2026-11-18 (`c5520e1`) |
| ③ | `03_reponse_mort.md` — dégâts gradués, fin de la mort calendaire, fin de cycle | **FAIT** 2026-11-18 (`23c7822`) |
| ④ | `04_signes.md` — posture thermique et marques, voix | **FAIT** 2026-11-18 (`b2d6f10`) |
| ⑤ | `05_vue.md` — postures et teintes, banc `niche_thermique`, recette F5 | **FAIT** 2026-11-18 — sprint CLOS côté code, F5 attendu |

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

## ④ FAIT (2026-11-18)
- `sim/engine/posture_thermique.py` : `etat_thermique(plant, eco)` → (posture ∈ [−1, 1],
  palier | None). Froid (nuit) : pendant (1ʳᵉ limite + 3 °C, = max(lim_froid, lim_gel)) →
  violacé (× (1 + `cold_memory`)) → `froid` translucide (< lim_froid) → `gel` noirci
  (< lim_gel) → effondré (gel + vitalité ≤ 1/3). Chaud (T_feuille) : replié (lim_chaud − 3)
  → flétri à midi (× (1 + `soif`)) → bords jaunis (> lim_chaud) → `brulure` (> lim_brul).
  Bandes de 0,25 ; rampes pleines à 1 point de dégât/sem. (`1/FROID_LESION_K`,
  `FROST_SEVERITY_REF`, `1/BRULURE_K`) ; les marques prolongent les paliers de dégât.
- **Écart au kickoff** : module dans `sim/engine/` et non `sim/semiologie.py` — il relit
  les pentes de `reponse_thermique` et `feuille.soif` ; `sim/` n'importe pas `sim.engine`
  (couches). Nuit mémorisée `plant.t_nuit` par `_tick_nuit_froide` (hors digest, lue par
  aucun code du tick : le snapshot n'a pas la météo de la semaine) ; T_feuille = `t_feuille`
  du ③. Palier nommé « pendant » (accord de « feuilles pendantes »).
- Marques `froid` (prio 4,5) et `brulure` (1,5) dans `PRIORITE` → `leaf_symptoms`.
- Corpus `sim/signes_corpus_thermique.py` (fusionné dans `SIGNES`) : froid, brulure +
  6 paliers (pendant, violace, effondre, replie, fletri_midi, bords_jaunis), concept
  `météo` → carnet D/I, encyclopédie, `observer` et `legende` les connaissent d'office.
  1ʳᵉ observation = dédup existante (espèce, signe, **saison**) — pas « par vie ».
- Pont **0.6.18** : `posture_thermique` + `palier_thermique` (pleine terre et conteneurs).
  Snapshot smoke comparé HEAD/après (sem. 3 et 30) : seules ces 2 clés s'ajoutent.
- Smoke 104 sem. [seed 42] : 2 233 plante·semaines ; replié 265, bords jaunis 125,
  effondré 2, pendant 1 ; côté froid quasi muet (les cultures tendres meurent en S1-3).
  Pommier « bords jaunis » à T_f 32,9 °C en S15 (lim_chaud du ②, à regarder).
- Tests : `test_posture_thermique` (neuve, 17/17) ; `test_signes_legende` mis à jour
  (13 signes + 6 paliers, météo p3 = tous les signes météo ; 43/43) ; versions 0.6.18 dans `tests/simserver/` (voix, delta, conteneurs, structures). 119 suites vertes (hors `test_peripherie`, préexistant). Golden INTACT `88cca899…`.

## ⑤ FAIT (2026-11-18)
- Vue `visuals/PlantRenderer.Thermique.cs` (partial neuf) : posture QUANTIFIÉE (8 échelons
  par demi-échelle → recuisson au changement, jamais par frame). Port : froid → feuilles
  qui PENDENT (`LeafDropCm` + port des fiches `PointFeuille`, jusqu'à 10 cm à −1) ; chaud →
  limbe REPLIÉ de profil (`LeafOpen`, même fermeture que la canicule). Teinte du palier
  posée après le symptôme dominant (`SymptomTint`, tous les chemins : segments, fiches,
  prairie, houppiers, paliers bas) : violacé, vert d'eau détrempé, noirci (effondré plus
  fort) ; terne (flétri à midi), jaune, roux brûlé. 5 couleurs `Palette16.Th*`. Marques
  `froid` (taches détrempées) et `brulure` (bord roussi) avec les marques fines (×16,
  `DrawLeafDamage`, `MarquesFines`). Conteneurs compris.
- Pont **0.6.19** : `plage_thermique` = {gel, froid, chaud, brulure, nuit, feuille} °C par
  plante vivante (`genes_pont.plage_thermique`, lit `lim_*`, `t_nuit`, `t_feuille`) ;
  réponse d'`init` d'un banc de `BANC_WARMUP` → `warmup`. Survol G : ligne « plage : gèle
  < … · froid < … · chaud > … · brûle > … » + « vécu : nuit … · feuille … ».
- Banc **`niche_thermique`** (`bancs/niche_thermique.py`, départ s20, warmup F5 **2**,
  germination férale coupée au post_init, herbivorie coupée, survol G ouvert d'emblée).
  (b) trois MÂCHES repiquées (stade adulte) : sable sec plein soleil · terre gorgée plein
  soleil · sable sec à l'ombre du mur nord. (a) tuile AUTOMNE : basilics nu / paillé
  (litière 3) / voilé, mâches, seigles.
- **Écarts au kickoff** : (1) canicule NON forcée — il faudrait un drapeau moteur (patron
  `pluie_forcee`) ; le banc vit la canicule du **seed 42** (s16, s24 ; la vue envoie toujours
  `WorldView.Seed` = 42, `BANC_SEED` n'atteint donc jamais le F5 — préexistant). (2) Scène
  (b) en **mâche**, pas en basilic : le basilic (lim_froid 10 °C) est « détrempé » par les
  nuits de juin et masque le côté chaud ; la mâche (chaud 25 °C, brûle 42 °C) monte toute
  la gamme chaude. (3) Warmup par banc (12 → 2) : avec 12 semaines la canicule passait
  hors champ ; `BANC_WARMUP` côté Python, lu par la vue (une capture `-w` reste prioritaire).
- Mesure (`mesures/mesure_banc_vue.py`, seed 42, chronologie = celle du F5) :
  ouverture s22 → mâche sèche « bords jaunis », arrosée « repliée », ombre « flétrie à
  midi » ; s24 (canicule, T_feuille sèche 46,0 °C) → mâche sèche **brûlée** (marque jusqu'à
  s40), les deux autres jaunies ; basilics nu morts **s31**, paillés **s33**, voilés **s36**
  (froid sans gel) ; mâche et seigle verts tout l'hiver. 2 basilics (col. 6) tués par la
  **grêle** en s22 [seed 42]. Mâche et seigle de la scène (a), semés en été, meurent de **fin
  de cycle** (fleuris en automne) en s42 / s48 — pas du froid.
- Captures VM (`planche/planche_05_*.png`) : ouverture ×4, canicule ×4 (mâches sèches
  rousses, arrosées vert-jaune), mâche brûlée ×16 + survol G, automne ×4 + survol G
  (basilics nus pâles détrempés, voilés verts).
- Golden INTACT `88cca899…` ; `test_sim_server` 349/349 ; `dotnet build` vert.
  `tests/bancs/test_biotique` rouge **déjà sur HEAD** (IndexError, hors tronçon).
- Taille : `core/SimBridge.cs` 351 LDC (🟡, était 349).

## Recette F5 (Nico)
Monde **niche_thermique** (sélecteur, catégorie « niche_thermique »). Le survol G est ouvert.
1. **Ouverture (s22, été)**, au sud de la maison, deux tuiles : mâches sur **sable** (à
   gauche) feuillage **jaune aux bords** ; sur **terre** (à droite) feuilles **repliées**
   (limbe étroit) mais vertes. Survole : « plage : gèle < −10 °C · chaud > 25 °C · brûle
   > 42 °C », « vécu : … feuille 3x °C ».
2. Touche **H** (maison transparente) ou **Page↑** : derrière le mur nord, 3 mâches à
   l'**ombre** — feuilles repliées / « flétries à midi » (terne), jamais brûlées.
3. Lance la saison jusqu'à **s24 (canicule, ciel dégagé)** : les mâches du sable
   **roussissent** (brûlées, une peut mourir) ; ×16 : bord roussi sur les feuilles ;
   les arrosées et l'ombre restent jaunies, vivantes.
4. Tuile **AUTOMNE** (sud-est) : basilics en 3 rangées (nu, paillé, voilé), mâches,
   seigles. De **s23 à s36** : les basilics **pendent** (nuits < 13 °C), virent au **vert
   d'eau pâle détrempé**, puis meurent : **sol nu d'abord (≈ s31), paillis ensuite (≈ s33),
   voile en dernier (≈ s36)**. ×16 : taches détrempées. La mâche et le seigle restent
   **verts** pendant tout ce temps (et au gel de décembre, s37-39).
5. À juger : la teinte détrempée est-elle lisible (assez distincte du vert pâle
   d'étiolement) ? la pendaison se voit-elle à ×4 ? le roux brûlé ×4 ? les anneaux
   roussis ×16 (même dessin que le bord noirci du gel) ?
Limites connues : mâche/seigle de l'automne meurent de fin de cycle en s42/s48 (semés en
été dans le banc) ; brindilles de litière très visibles sur le sable (couche Litter,
préexistant) ; pucerons visibles (densité seulement neutralisée).

## REPRISE
**`test_biotique` réparé (2026-11-18, décision Nico)** : rouge depuis ③ (basilic du banc
`infestation_ravageur` mort de froid au printemps ; l'été les pucerons sauvages colonisent le
témoin — aucune date ne passe) → hôte remplacé par la **mâche**, 12/12. Reliquats (sélection,
pommier, ombrière, paillage, golden smoke, tomate) → **D139, dette pour plus tard**.
`test_peripherie` rouge depuis avant le sprint (inchangé). `test_population` : hash de champ
re-capturé à ② et ③ (dérive annoncée).

Sprint **CLOS côté code** (①→⑤). Reste : commit, F5 de Nico (recette ci-dessus), puis
`sprint_caracteres_vivants`. Points ouverts pour la suite : calibrage `lim_gel` tomate
(②), endurcissement du pommier (③ b), ombrière ↔ `light_received` (③ c), paillage
`eco.paillage` (③ d), réponse à la sélection < cible (③).

## Report du sprint ① (génétique infinitésimale, décision Nico 2026-11-16)
La réponse à la sélection sur `germination_thermique` (banc
`sprint_genetique_infinitesimale/mesures/banc_reponse_selection.py`, cas (a), parcelle
froide 10 ans) est NULLE : +0,02 °C [n=80] vs témoin +0,11 °C [n=96], cible ≥ +1 °C.
Le tri thermique à la levée (`_levee_triee`, `sim/succession.py`) existe déjà ; ce qui manque
est la **pression** : tolérances de levée (7-10 °C) ≫ σ_A 1,5 ; levées près de l'optimum ;
~9 levées/an ; aucun avantage à lever tôt. Ce sprint doit la créer et **re-mesurer avec ce
banc** avant clôture (un tronçon inerte n'est pas un succès).
