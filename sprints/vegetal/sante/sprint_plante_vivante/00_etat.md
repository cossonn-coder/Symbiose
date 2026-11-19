# Sprint PLANTE VIVANTE (D140 G, sprint A) — état

> Conception FIGÉE le 2026-11-18 : `docs/vegetal/sante/conception_plante_vivante.md`
> (à lire en entier). Suite : `sprints/vegetal/sante/sprint_stress_au_bilan/` (B).
> Ce sprint débloque `sprints/vegetal/genetique/sprint_depart_jardin/` (reprise au ④).

## But
Les plantes n'ont plus de PV : elles vivent d'un bilan carbone (photosynthèse −
entretien − part racinaire), tiennent un `feuillage` et des `reserves`, meurent de
famine ou de destruction. Herbivorie par atteinte (la limace ne mange pas le
chêne), souches à réserve finie (fin de la cascade de rejets), ouverture du monde
`full` à mortalité partielle.

## Décisions clés (Nico, 2026-11-18)
- Règle de dégât actuelle aberrante → refonte des dégâts, des cibles de chaque
  ravageur et de leurs effets. Mesuré : la faune n'est pas en cause (pré-rouler
  la faune AGGRAVE : 130/136 morts vs 121).
- Plantes sans PV ; tout le vivant végétal passe au bilan (sprints A puis B).
- `vitalite` = lecture dérivée (réserves × feuillage) ; écrire 0 = destruction.
- Plus de mort ni de guérison au sort ; causes de mort : famine, destruction,
  défaillance hydraulique, racines perdues, fin de cycle, vieillesse (§5).
- Unité = semaine d'entretien ; 3 paramètres d'espèce neufs (`reserve_semaines`,
  `photo_max`, `cout_feuillage`) dans `plants/physiologie.py` ; tout le reste
  réutilisé (plage thermique D139, tolérances, gènes de feuille).
- Critère d'ouverture (`full`, seed 42, s10→s30) : 0 arbre posé mort ; ≤ 25 %
  d'herbacées posées mortes hors fin de cycle ; ≤ 4 rejets par arbre mort.

## Golden
Départ `25671775…` (fin du ③ de `sprint_depart_jardin`). ① **INTACT** ·
② **RE-FIGÉ → `699edb51a320f784…`** (modèle de vie) · ③ **RE-FIGÉ → `8f2dd7add938b4cb…`** (herbivorie seule,
preuve par neutralisation) · ④ intact · ⑤ **INTACT** (vérifié) · ⑥ **INTACT**.
Perf de référence à mesurer au ① (tick `full` s10-s30, commit de départ).

## Tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_socle_bilan.md` — bilan en ombre + paramètres 52 espèces + banc | **FAIT** (golden intact, non commité) |
| ② | `02_bascule_vie.md` — vitalité dérivée, famine, `erode` = tissus | **FAIT** (golden RE-FIGÉ `699edb51…`, non commité) |
| ③ | `03_herbivorie_atteinte.md` — chaque ravageur mange ce qu'il atteint | **FAIT** (golden RE-FIGÉ `8f2dd7ad…`, non commité) |
| ④ | `04_souches_reserve.md` — réserve de souche, rejets sans souche propre | **FAIT** (golden INTACT `8f2dd7ad…`, non commité) |
| ⑤ | `05_ouverture_mesure.md` — critères `full` s10→s30 + âge de la chronique | **FAIT** (golden INTACT `8f2dd7ad…`, non commité) |
| ⑥ | `06_vue_banc.md` — pont, rendu du feuillage, info-bulle, banc, clôture | **FAIT** (golden INTACT `8f2dd7ad…`, build C# vert, non commité) |

## Acquis du ① (2026-11-18)
- `plants/physiologie.py` : 3 paramètres par forme de vie + `SURCHARGES` des 52 espèces
  (commentées), `capacite_reserve` = reserve_semaines × facteur_stade (0,05 → 1,
  linéaire sur l'index de stade ; sur `age_years/maturity_years` pour les arbres à
  stade perpétuel — l'index seul ne bougeait pas pour eux).
- `sim/bilan.py` (pur) appelé en fin de `_update_physiology` ; champs `feuillage`,
  `reserves`, `bilan_net` dans `PlantInstance` (hors `_PLANT_ATTRS`). Lus par personne.
- **Écarts à la conception (calibrage mesuré)** : (1) `f_T` côté chaud ferme de
  `lim_chaud` à `lim_brul`, pas à `lim_chaud` — `t_feuille` est le pic du jour le plus
  chaud, et la plupart des herbacées ont `lim_chaud` 28-30 °C sous un pic d'été
  ordinaire de 29-30 °C : un arrêt net éteignait leur production tout l'été ;
  (2) `LUM_SATURATION` 0,4 (sur `light_eff`) ; (3) sciaphile `photo_max` 2,5 (2,0
  laissait violette/lierre en déficit au nord de la maison). Optimum thermique =
  `temp_min_growth + 8 °C` (D139 n'a pas d'optimum explicite).
- Banc `tests/test_bilan.py` vert : niche d'été > 0 pour les 43 espèces de
  PLACEMENTS ; plantule sous ombre < 0 ; chêne adulte défolié en continu tient 20 sem
  (réserves 0,29) ; semis de chêne (C = 3,5 sem) vide en 2 sem ; défolié une fois →
  feuillage refait en 7 sem, réserves au plus bas 0,87 ; caduc en hiver ≤ 30 %.
- `bilan_net` monde `full` s18 [seed 42, n=1, herbivorie neutralisée en mémoire,
  `mesures/bilan_par_espece.py`] : négatifs **myrtille −0,46, menthe −0,19, saule
  −0,12** (ombre de la maison/du sapin : lumière effective < 0,2 — placements hors
  niche, **à surveiller au ⑤**) ; ble +0,05, violette +0,06, bambou +0,12, lierre
  +0,13, consoude +0,16, framboisier +0,25 ; tous les autres +0,3 à +2,6 (tournesol).
  Semaine de canicule s24 (T_air 24,9) : la plupart en négatif (−0,1 à −2), attendu.
- Perf tick `full` s10→s30 [3 paires alternées, charge 1-2] : 9,27 s → 9,29 s (bruit).
- Suites : tout vert sauf `test_peripherie` (70/71) et `test_population` — **déjà
  rouges au commit de départ** (vérifié sur un worktree HEAD), sans lien.
- À savoir pour ② : une plantule de vivace (C = 0,4 sem) dormant l'hiver dépense ~0,9
  sem → elle mourrait de famine dès le branchement ; le facteur de stade des herbacées
  ou `DORMANCE` (0,1) sera à revoir quand la vitalité lira les réserves.

## Acquis du ② (2026-11-19)
- `vitalite` = **propriété** (`plants/base/instance.py`) : `min(1, reserves/R_CONFORT 0,5) ×
  (½ + ½·feuillage)` ; setter : ≤ 0 = destruction (réserves et feuillage à 0), > 0 = réserves
  qui relisent `v` (bancs/tests) ; `is_alive` = `reserves > 0`. Aucun constructeur ne passait
  `vitalite=` (vérifié au grep).
- `erode` = perte de feuillage (÷ `resilience_base`) ; coup ≥ vitalité = destruction.
- Famine : `_update_physiology` renvoie un log (boucle `log +=`) ; `_mort_de_faim`
  (`mortalite.py`) → « 🪦 X meurt de faim » (cause `famine` dans `sim/evenements._raison_mort`,
  textes carnet sans concept) ; annuelle en fin de cycle → ligne ✿ + graines.
- Sénescence/fin de cycle : `_retrait_reserves(1/3)`. `background_mortality`,
  `shade_stress_damage`, convalescence au sort : commentés (SUPPLANTÉ).
- Croissance : `can_grow = bilan_net > 0` (bilan du tick précédent) ; stagnation nommée par
  `plant.limitant` (`facteur_limitant`, ordre ombre/froid/chaud/eau) ; `growth_factor` vise
  `0,6 + 0,4·min(1, surplus/1 sem)`, gelé hors végétation.
- **Écarts au kickoff (mesurés, nécessaires)** : (1) `C_PLANTULE_MIN = 2` sem (albumen) dans
  `capacite_reserve` — sinon semis de S01 morts de faim la 1re semaine, plantule de vivace
  morte l'hiver ; (2) quiescence par le froid (T ≤ `temp_min_growth` ⇒ entretien × DORMANCE) —
  thym persistant ; (3) entretien × (DORMANCE + (1−DORMANCE)·présence) pendant le
  débourrement — semis de pommier, trèfle de printemps ; (4) refeuillaison ≤ ½ des réserves
  courantes / sem (sinon suicide à bilan positif) ; (5) `declin` (fin de cycle OU
  `declin_senescent ≥ HEAL_SEN_CUTOFF`, nouveau `sim/tempo.declin_senescent`) : le bilan ne
  remplit plus les réserves — sinon fin de cycle et vieillesse jamais mortelles.
- Golden : 3 premières divergences (S01) : haricot frappé de froid lit 0,62 au lieu de 0,25
  (coup = feuillage) ; lignes « stagne (bilan +0,00) » (pas de bilan avant la 1re physiologie) ;
  exsudats/compte de plantes. Smoke : vivantes s52 T0 44 (avant 25), s104 53/13 (avant 53/12) ;
  33 morts de faim, 14 fins de cycle.
- Tests adaptés (aucun supprimé) : eau, evergreen (herbivorie neutralisée : ancienne règle
  ③), gestes_manuels, squelette_herbacees, vigueur/gestes, niche_thermique, plasticite,
  reponse_thermique, parasite (hôte plafonné), stress_chronique (« l'ombre affame »),
  trefle_cycle (labo arrosé). Tout vert sauf `test_peripherie`/`test_population` (pré-existants).
- Contrôle `full` s10→s62 [seed 42, n=1, `mesures/controle_vie.py`] : 138 → 53 (s18) → 209
  (s61) ; morts famine 90, herbivorie 69, froid 4, vent 2. Vague s15-s17 (famine 54 :
  tournesol, basilic, poivron, tomate, trèfle) = défoliation par l'ANCIENNE herbivorie + printemps
  froid → à revoir après ③. Perf tick s10-30 [2 paires] : 9,9 s → 9,1 s.
- LDC : `boucle.py` 306, `perturbations.py` 301, `carnet.py` 301 (bande 🟡, une responsabilité).
- Pots (`world/container.py`) : pas de bilan → pas de refeuillaison ni famine (inchangé, à noter).

## Acquis du ③ (2026-11-19)
- `sim/effects/herbivorie.py` (neuf) : table d'atteinte `RAVAGEURS` (puceron toute plante hors
  hiver, ¼ défoliant + sucres `K_SUCRES` 1 sem ; limace = part sous 40 cm `min(1, 40/h)` ;
  doryphore Solanaceae ; chenille = larve), `sommes_feuillage` (Σ poids par plot et par ravageur,
  1×/tuile/tick, dicts creux — aucune grille équivalente côté population : `_foliage_grid`
  pondère par vitalité ET normalise/clampe), `herbivorie_atteinte` → mutation neuve
  `PerteTissus` (feuillage, réserves ; `mutations.py`, résolue dans `resolution.py`, réserves
  vides = mort, log au format « ✗ Santé X@pos … [herbivorie …] → meurt » lu par la chronique).
  Hors `_cap_chronique`. Porte `stress_memory` retirée. Hiver : rien sur un caduc nu.
  Constantes parfum/appétence/bascule DÉPLACÉES de `perturbations.py` vers `herbivorie.py`
  (ré-importées). `herbivory_pressure` conservée, SUPPLANTÉE (plus appelée).
- **Écart au kickoff (mesuré, nécessaire)** : la formule littérale `K × moy(d × part)`, part =
  w/S, donne la MÊME perte à un chêne seul et à un semis seul (part = 1) → banc chêne < 2 %
  infaisable. Perte rapportée à la quantité de feuilles de la plante : `perte(plot) = atteinte ×
  min(1, K_HERB·d / S)`, S = Σ feuillage × atteinte × `masse_foliaire` (= h/30 cm ∈ [0,1 ; 6]
  couches). `K_HERB` 0,30.
- Banc `tests/test_herbivorie_atteinte.py` 18/18 : semis limace 0,10 → 18 %/sem, nu en 12 sem ;
  basilic 8 %, haricot 1 % (ravageurs 0,10) ; chêne 25 ans (600 cm, 109 plots) ravageurs 0,15
  → max 1,7 %/sem ; limace ≤ part basse ; puceron vole plus de réserves qu'il ne défolie ;
  doryphore spécialiste ; bascule ×2 ; appétence/coriacité ; partage à deux.
- Golden : preuve par neutralisation [smoke, n=1] — HEAD ② avec `herbivory_pressure` neutralisée
  = ③ avec `herbivorie_atteinte` neutralisée = `82a85962…` (identiques) → dérive due à la seule
  herbivorie.
- Contrôle `full` seed 42 [n=1, script jetable du même patron que `mesures/controle_vie.py`] :
  vivantes s18 **152** (② : 53) ; posées mortes à s21 **10/136** (② : 104/136) ; à s30 33/136
  (fin de cycle 14) ; morts s10→s61 : famine 93, froid 40 (gel d'automne s30-s40 : tomate,
  basilic, haricot, poivron), fin de cycle 38, herbivorie 13. Famine en tête : trèfle 32,
  bambou 19, menthe 9 → **à regarder au ⑤**.
- Perf tick `full` s10→s30 [3 paires alternées, charge ~0,7] : 9,2 s → 10,7 s (**+16 %**,
  > +5 %). Herbivorie elle-même ≈ 0,8 s sur 29 s profilés [cProfile, n=1] ≈ 3 % ; le reste =
  3× plus de plantes vivantes (tick ∝ densité). À relire au ⑤ (critère d'ouverture).
- Tests adaptés : `test_caracteres_{fleurs,feuille,fruits}` lisent `facteur_gout` (au lieu de
  parser l'ancienne raison « p= »). `test_evergreen` (thym seul) et `test_trefle_cycle` (labo)
  neutralisent EN MÉMOIRE `herbivorie_atteinte` : tuile sans auxiliaires, ravageurs non régulés
  (puceron ~0,25, chenille ~0,3 l'été) → défolié puis mort de faim, hors de ce que ces tests
  examinent (hiver, vieillesse). Suites : tout vert sauf `test_peripherie`/`test_population`
  (pré-existants). `test_auxiliaires` (script 30 ans, sans assertion) enveloppait
  `sim.effects.herbivory_pressure` — patch déjà sans effet avant ③ (perturbations lit son nom
  local) ; laissé. Signe `semiologie.ravageurs` lit toujours la densité au plot-foyer (inchangé).

## Acquis du ④ (2026-11-19)
- `deposer_mort` fige `reserve_souche` (sem) = (`reserves` ou `reserves_detruites`) ×
  `capacite_reserve`, si `souche_vivante`. **Écart au kickoff (nécessaire)** : le setter
  `vitalite = 0` (destruction) vide les réserves AVANT `deposer_mort` → toute souche
  aurait eu 0 ; il garde désormais `reserves_detruites` (la coupe/le gel tuent la tige,
  pas l'amidon racinaire). Famine/herbivorie (réserves vidées) → 0 → aucun rejet.
- `COUT_REJET` 3 sem (`sim/souche.py`) = la plus grande réserve de plantule ligneuse
  (chêne 60 × 0,05) ; le rejet part réserves pleines (`min(1, COUT/C)`). N = min(capacité
  d'espèce, réserve // COUT) ≤ `N_REJETS_MAX`, réserve débitée.
- `AGE_SOUCHE_PROPRE` 3 ans dans le critère pur `souche_vivante` (`perturbations.py`) :
  vaut pour TOUT ligneux jeune (semis compris, pas de drapeau « rejet ») — plus simple,
  biologiquement défendable (pas de collet lignifié avant 2-4 saisons) ; s'applique aussi
  à la perte de couronne.
- Perte de couronne d'un arbre vivant : puise ≤ `REFEUIL_PART_RESERVES` (½) de ses
  réserves × C (même prudence que la refeuillaison), débite `reserves`.
- Banc `tests/test_souche_reserve.py` 6/6 ; `test_rejets_souche` 9/9 inchangé ;
  bois_mort, dormance_clonale, croissance, evenements, figuier_realiste, catalogue_mulch,
  caracteres_signes, peripherie_{voix,pont,gestes} verts.
- Contrôle `full` seed 42 s10→s61 [n=1, `mesures/diag_chene.py`] : **0 chêne né, 0 rejet,
  AVANT comme APRÈS ④** (HEAD ③ en worktree) — depuis l'herbivorie ③, aucun ligneux à
  souche ne meurt la 1re année : le contrôle n'est pas discriminant, la preuve est le banc.
  À relire au ⑤ sur un horizon plus long si des arbres meurent.
- LDC : `perturbations.py` 310 (🟡, était 303), `souche.py` 86, `instance.py` 286.

## Acquis du ⑤ (2026-11-19)
- Ouverture : `semer_fondateur` → réserves et feuillage à 1,0 par défaut ; la
  pré-croissance (`pre_croitre`/`grow_plant`) ne touche ni l'un ni l'autre (vérifié :
  136 plantes à l'init, min réserves 1,0, min feuillage 1,0). Rien à corriger.
- Chronique (D140 g1) : le registre porte `age_ans` (= `age_years`, ex-`age_sem` =
  `age_weeks`, semaines DANS le stade) ; texte « N sem » sous un an, « X,Y ans » au-delà.
  Seul consommateur du registre brut : `tests/test_chronique` (adapté) ; la vue C# ne lit
  que le texte. Pont non versionné (champ de rapport, pas de snapshot).
- Banc `tests/test_ouverture_vivante.py` (≈ 15 s) — **3 critères TENUS**, aucun paramètre
  d'espèce ni `K_HERB` touché [seed 42, n=1] : arbres posés morts **0/13** ; herbacées
  posées mortes hors fin de cycle **19/123 = 15,4 %** (famine 15 : poivron 7, sphaigne 3,
  drosera 2, tomate/basilic/mâche 1 — limitant `ombre` sauf mâche `chaud` ; herbivorie 3
  tomate ; froid 1 basilic) ; fin de cycle 14 ; rejets **0** pour 0 arbre mort.
- Horizon s10→s61 [même seed, n=1, hors banc] : morts posées fin de cycle 38, froid 38
  (gel d'automne des tendres : tomate 12, basilic 11, poivron 8, haricot 7), famine 20,
  herbivorie 3 ; famine trèfle 2, menthe 1, violette 1 — **myrtille, saule, bambou : aucune
  mort de posée** (la famine trèfle/bambou du ③ comptait tous les pieds : elle porte sur ceux nés après l'ouverture — ramets ou semis, non distingués ici).
  1 ligneux mort (non posé), 0 rejet → la fin de cascade reste prouvée par banc seul (④).
- Perf tick `full` s10→s30 [3 paires alternées, worktree `4097067` vs ⑤, charge 0,8-1,0] :
  10,38/10,22/9,27 s → 11,29/11,16/10,11 s = **+9 %** sur le sprint (budget ≤ +10 %/tronçon
  tenu ; le +16 % du ③ ne se retrouve pas à cette charge).
- LDC : `chronique.py` 127, `test_ouverture_vivante.py` 77.

## Acquis du ⑥ (2026-11-19)
- Pont **0.6.21** : `feuillage_bilan` + `reserves` (3 déc.) sur chaque plante vivante (sol et
  conteneur) ; légende `voix_bilan` {clairseme, epuise, refait} (`sim/signes_corpus.py`).
  **Écart au kickoff (nécessaire)** : la clé `feuillage` existait déjà (part de couronne en
  place, phénologie, AUTOMNE VISIBLE 0.6.3, lue par la chute des feuilles `LeafFallLayer`) →
  le feuillage du bilan sort sous `feuillage_bilan` (sinon une plante broutée « larguerait »
  des feuilles à l'écran). Snapshot smoke + full (2 ticks) HEAD vs après : identiques hors
  clés neuves (seul `perf.rss_mo` bouge). Tests `tests/simserver/*` bumpés, 349/349.
- Vue : `PlantStructure.FeuillageBilan` + `PartPortee` (= phénologie × bilan × taille) lue par
  les 8 sites de port et `DensiteVisible` → moins de feuilles, pas de teinte de dégât.
  `visuals/PlantRenderer.Bilan.cs` (neuf) : `SetBilan` donne au canal de vitalité les FORCES
  = min(1, réserves / R_CONFORT 0,5) au lieu de `vitalite` (qui compte déjà le feuillage :
  un chêne défeuillé à réserves pleines paraît nu, pas malade) ; détecteur de hausse du
  feuillage (1re valeur reçue ≠ variation) ; `EtatBilan` → clé de phrase (épuisé si forces
  < 0,6 et teinte visible au palier ; refait si en hausse et < 0,95 ; clairsemé si < 0,6).
  Info-bulle 1er niveau : la phrase du bilan prime sur « vert franc/terne » et s'ajoute
  sous un signe ; Maj+F3 : jauges « réserves » et « feuillage » (remplacent « vitalité ») ;
  dossier debug : ligne réserves/feuillage porté. Conteneurs : même branchement.
- Banc `plante_vivante` (`bancs/plante_vivante.py`, départ s12, warmup 1) : (a) LIMACES
  (sud-ouest) limace 0,15 uniforme, chêne 25 ans (5,3) + semis de chêne (5,13) ; (b) OMBRE
  (pied du mur nord, maison transparente touche H) 3 poivrons ; (c) REFEUILLE (sud) 3
  consoudes, (4,2) témoin, (4,4) et (4,6) à feuillage 0,2 ; (d) SOUCHE (sud-est) chêne de
  12 ans coupé à l'ouverture. Germination férale coupée. **Écarts au kickoff (mesurés)** :
  pas de laitue au catalogue et la mâche meurt l'été au lieu de refeuiller → **consoude** ;
  tournesol/basilic gardent un bilan positif au pied du mur → **poivron** (affamé, limitant
  `ombre` ; au soleil il tient, +1,5 à +2). Oracle `tests/test_banc_plante_vivante.py`
  (≈ 2 s) : chêne feuillage 1,00 / semis mort ; 3 poivrons morts de faim ; consoudes 0,96 ;
  3 rejets ≤ 4 ; clés au snapshot [seed 42, n=1, s12→s20].
- Captures VM (`tools/capture_vm.sh -b plante_vivante`) : « feuillage clairsemé, des
  feuilles ont disparu » (consoude broutée, s13), « refait ses feuilles » (s15, `-T 2`),
  « à bout de forces, son vert se ternit » (poivron, s18) — phrases vérifiées ; la
  différence de densité témoin/broutée se voit mais reste modeste à ×4.
- LDC : `serialize.py` 326 (🟡, était 322), `PlantRenderer.Bilan.cs` 32, banc 56,
  `WorldView.InfoBulle.cs` 186.
- Hors périmètre, constaté : l'étiquette de survol affiche le nom de CLASSE (« Comfrey ·
  adulte », « Pepper · adulte ») — préexistant (`PlanteLue.Tag`), relève de D141.

## Recette F5 pour Nico (banc `plante_vivante`)
Monter le banc, laisser défiler s13 → s20 en survolant (×4) :
1. LIMACES (sud-ouest) : le semis de chêne se dégarnit (« feuillage clairsemé ») puis meurt
   vers s16 ; le chêne de 25 ans, sous les mêmes limaces, ne perd rien.
2. OMBRE (derrière la maison, touche H) : les 3 poivrons pâlissent ; vers s18 « à bout de
   forces, son vert se ternit », puis morts de faim s18-s20. **À juger : la teinte
   d'épuisement est-elle assez lisible ?** (planchers d'`ApplyVitality`).
3. REFEUILLE : les 2 consoudes broutées sont nettement moins feuillues que le témoin à
   gauche, puis « refait ses feuilles » et rattrapent le témoin vers s18. **À juger : la
   densité réduite se lit-elle assez ?**
4. SOUCHE (sud-est) : trois rejets autour du chêne coupé, pas de cascade.
5. Monde `full` : une plante broutée paraît clairsemée, pas « malade » ; Maj+F3 montre les
   jauges réserves/feuillage.

## Diagnostic d'origine (2026-11-18, seed 42, n=1 par cas)
Ouverture s10 → morts des 136 posées à s21 : tel quel 121 ; faune pré-roulée 130 ;
prédateurs seuls pré-roulés 97 ; `stress_memory` amorcée 0,12 → 49. Semis de
chêne : vagues de rejets ×3 (9 → 27 → 75 → 153, s20-s32), toutes à < 1,5 m d'un
arbre mort. Scripts jetables : instrumenter `herbivory_pressure` et compter les
naissances par espèce/semaine via `SimServer().cmd_init({"config":"full","seed":42})`
puis `engine.tick_semaine()`.

## REPRISE
①→⑥ faits — **sprint A CLOS côté code** (⑥ commité `7c3bfc1`), F5 attendu (recette ci-dessus).
Golden courant `8f2dd7add938b4cb…`, pont 0.6.21. Suite : `/sprint-auto sprint_stress_au_bilan`
(B, `sprints/vegetal/sante/sprint_stress_au_bilan/`), puis reprise de
`sprints/vegetal/genetique/sprint_depart_jardin/` au ④.
