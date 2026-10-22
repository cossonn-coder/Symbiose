# Sprint « le sol qui respire » (D111) — état partagé

**Phase** : CONCEPTION FIGÉE le 2026-10-22 → `/sprint-auto sprint_sol_qui_respire` en cours.
Doc : `docs/champs/sol/conception_sol_qui_respire.md`. 8 tronçons ; ① FAIT et commité.
**Remontées de ① TRANCHÉES (Nico, 2026-10-22)** : perf +33 % acceptée → dette **D114** (URGENTE,
sprint perf juste après ce sprint ; F5 suspendu d'ici là) ; banc succession 4/6 → dette **D115**
(banc conservé tel quel : il révèle un trou de mécanique, ne pas l'affaiblir). Pour les tronçons
suivants : budget perf mesuré **par rapport à ①** ; ne pas tenter de résorber D114 ici.

## Carte des tronçons (statut)

| # | Kickoff | Golden | Statut |
|---|---|---|---|
| ① | `01_bilan_hydrique.md` | RE-FIGÉ `22768f33…` → `1ce02bce…` | FAIT (D114, D115) |
| ② | `02_bois_mort.md` | INTACT `1ce02bce…` (prémisse fausse) | FAIT — ⚠ inerte en pratique |
| ②bis | `02b_mort_branches.md` (ajouté 2026-10-22, accord Nico) | INTACT `1ce02bce…` (pommier du smoke trop jeune) | FAIT — ⚠ flux quasi nul sur `full` |
| ②ter | `02c_arbres_adultes.md` (ajouté 2026-10-22, mandat Nico « favoriser le résultat ») | RE-FIGÉ `1ce02bce…` → `df6ebf04…` (tolérance ombre pommier, seul motif) | FAIT — ⚠ objectif bois NON atteint sur `full` |
| ③ | `03_regne_fongique.md` | INTACT `df6ebf04…` | FAIT — ⚠ 8 espèces/13 sur `full` [3 graines] (composition) |
| ④ | `04_parasite_faiblesse.md` | INTACT `df6ebf04…` (hôte affaibli attaqué 1 sem., dérive sous la résolution du digest) | FAIT — ⚠ aucune mort d'hôte (trappe de faiblesse seule) |
| ⑤ | `05_voix_champignons.md` | INTACT `df6ebf04…` | FAIT — pont 0.5.53 ; clé générique `champignon` retirée |
| ⑥ | `06_manger_vision.md` | INTACT `df6ebf04…` | FAIT — pont 0.5.54 ; overdose +75 ms/snapshot [n=1 run, `full`] |
| ⑦ | `07_nectar_espece.md` | re-figé si floraison au smoke | à faire |
| ⑧ | `08_vue_godot.md` | intact | à faire |

Golden de départ (relevé par ①) : `22768f339ac41bb20b1604bb29672bb3b209ee62ec659b1c8369dd31ccd6cfb8`.
Golden après ① : `1ce02bce275a2b4c262564e7eda384b1071125ebc67e65346d101820102d6bfd` (re-figé
UNE fois, annoncé : climat + hydrologie changent partout). Pont **0.5.50**.
Golden après ②ter : `df6ebf044655d162293ce3dfee1baa3dc781a7f39bae78d4a7594f120b80b0e6` (tolérance
à l'ombre du pommier 0,90 → 0,85, dérive locale prouvée).

## ① Bilan hydrique — FAIT (2026-10-22)

**Livré** :
- 1a `sim/weather.humidite_air(seed, week, event)` (océanique ~0,80 ± 0,07 saisonnier ± 0,05
  bruit, imposée par l'événement : pluie 0,97, sécheresse/canicule 0,50) → passée à
  `tick_rosee(…, humidite_air=)` ; point de rosée = T_air − (1−HR)·`ECART_ROSEE_HR` (20 °C,
  règle des météorologues). Défaut `None` = dérivation historique depuis le sol.
- 1b canal `K_PLUIE` (90_008) : les semaines CALMES tirent un épisode `P_PLUIE_SAISON`
  {printemps .27, été .16, automne .22, hiver .35} → « Pluie prolongée » (« Orage » l'été,
  intensité ≤ 0,75 < SEUIL_SEVERE du composé). Fréquences totales mesurées [200 graines ×
  2 ans] : printemps 1/4,0 · été 1/6,1 · automne 1/4,0 · hiver 1/3,0. Aléas inchangés (un
  aléa exclut la pluie). `BASE_RAIN` 0,015 → 0,006 ; `PLUIE_APPORT` Pluie 0,012 → 0,14,
  Orage 0,010 → 0,10.
- 1c `feuillage` (attribut d'espèce, défaut `moyen`) + `sim/engine/transpiration.py` :
  facteur = demande (T_air 3→16 °C, ciel, vent) × feuillage présent (caduc 0 hiver/après
  abscission, vivace dormante 0,15 l'hiver, débourrement sem. 1→8) × `COEF_FEUILLAGE`
  {large 1,3 · moyen 1 · fin 0,8 · cireux 0,55 · aiguilles 0,4}. Eau seule.
  Large : courgette, tournesol, figuier, noyer, consoude, bourrache. Cireux : thym, lavande,
  lierre, myrtille, ail, armoise, molène. Fin : blé, seigle, pâturin, bambou, carotte,
  achillée, phacélie, sphaigne, drosera, bouleau, saule. Aiguilles : sapin. Reste moyen.
- 1e banc TEST `pluie_continue` (monde `full`, flag `pluie_forcee` → `weather_state`) +
  `mesures/banc_pluie.py` : **5/5 maillons OK** [40 sem., n=1 run] — sol 3,00 (80 % plots au
  plafond), `eau_surface` 79, `marais_memory` ≥ MARAIS_ON sur 73 plots, asphyxie argile 69 %
  des plantes (témoin 0 %), acclimatation 66 % (témoin 78 %).

**Calibrage** (`mesures/bilan_eau.py`, monde full, 156 sem.) [n=1 run par graine] :
| graine | hum. méd. an 0/1/2 | sem. ~10 (fin d'hiver) an 1/2 | sem. ~35 an 1/2 | pluie/an |
|---|---|---|---|---|
| 1521550718 | 1,61 / 1,92 / 1,86 | 2,37 / 2,26 | 1,59 / 1,72 | 17/17/17 |
| 7 | 1,07 / **0,85** / 0,99 | 0,97 / 1,29 | 0,71 / 0,74 | 4/9/12 |
| 1515525502 | 1,76 / 1,82 / 1,86 | 2,12 / 1,98 | 1,70 / 1,69 | 16/15/18 |
Cible tenue sauf graine 7 an 1-2 (années sèches, 9 et 12 sem. de pluie) ; creux d'été jamais
< 0,7 ; fin d'hiver ≈ 2,0-2,4/3,0 (« presque plein » partiel). Rosée 0,005-0,008/plot/sem
(avant : 0,008 → 0,0001). Uptake hiver ≈ 0 (transpiration).

**⚠ REMONTÉE PERF (règle du kickoff : dépassement ⇒ STOP)** [graine 1521550718, n=1 run, base
et ① lancés en parallèle] : tick moyen an 0 626 → 626 ms, an 1 1126 → 1112, **an 2 1417 →
1884 ms (+33 %)** ; population an 2 539→449 (base, mort de soif) contre 628→675 (①, +32 %).
Coût PAR PLANTE inchangé (~2,9 ms/plante an 2 dans les deux) : le surcoût est la population
qui survit enfin, pas le mécanisme. Population NON bridée. → décision orchestrateur/Nico.

**⚠ REMONTÉE banc `succession_bascule`** (`tests/bancs/test_succession`, 4/6) : pioneer final
40 (53 %) au lieu de 9. Ablation : la bascule de la base se jouait dans un DÉSERT (hum. méd.
banc 0,03-0,10, drought_memory 0,5-0,8 des 4 archétypes [n=1 run]) — c'est la soif qui
rabattait le pioneer, pas la facilitation OM. Sol arrosé (hum. 1,1-1,8) → pioneer non rabattu.
Chaque correction seule (pluie / rosée / transpiration) passe, les trois ensemble non : banc
fragile. Non « réglé » ici (hors périmètre) → à trancher (dette succession ou oracle).

**Autres constats** : échecs PRÉ-EXISTANTS inchangés (base 2026-10-22 déjà rouge) :
`bancs.test_edaphique` 6/7, `test_peripherie_pont` 49/50, `test_population` (hash), `test_vent`
52/54. Acclimatation du monde full après ① [40 sem., n=1 run] : 259/374 plantes portent
`tolerance_ombre`, pas la sécheresse → le « voile cireux » F5 viendra surtout de l'OMBRE.
Conteneurs : `plant_uptake` y reste à transpiration 1,0 (défaut neutre, non saisonnier).

## ② Bois mort qui tombe — FAIT (2026-10-22), golden INTACT `1ce02bce…`

**Livré** : `_elaguer` puis `grow_plant` RENVOIENT les segments élagués (growth reste pur,
sans `eco`) ; `sim/engine/decompo.deposer_bois_tombe(plant, tombes, eco)` dépose
`length × thickness² × BOIS_MORT_PAR_CM3` (1e-4, calé sur le squelette d'un pommier de
10 ans [n=1 arbre]) en litière `bois` au plot de la verticale du milieu du segment
(`base` = repère cm de la TUILE, vérifié : collet = `(x_cm, y_cm, 0)`), borné à la tuile.
Ligneux = même critère que le squelette (`frac_bois_mort` > 0, i.e. `age_curve`).
Branché en 9c de `boucle.py` (tuile seule ; les conteneurs ignorent le retour). Pont
**0.5.51** : entrée `litiere` = `[r, c, tissu_dom, masse, age, bois_masse, bois_age]`.
Test `tests/test_bois_mort.py` 9/9 ; mesure `mesures/bois_mort.py`.

**⚠ REMONTÉE — prémisse du kickoff fausse, mécanique INERTE en pratique** : AUCUN ligneux
ne s'élague. `wood_persistence = 4000` sem. sur `PerennialWoody` (bois sans apex ne meurt
pas avant ~77 ans) et le plafond `max_segments` (70-90) n'est pas atteint : pommier, chêne,
bouleau, figuier isolés sur 520 sem. → 0 segment tombé (pommier 55 seg. à 10 ans) [n=1 arbre
par espèce, sans lumière]. Monde `full`, 1521550718, 104 sem. [n=1 run] : **0/1188 plots
avec bois** (inchangé), mycélium max 0,449 / méd 0,0021 (identique avec/sans dépôt ; le
« 0,24 » du kickoff datait d'avant ①). Seules les herbacées élaguent (trèfle, pâturin…,
écartées par la règle « ligneux seuls »). → pour que du bois tombe vraiment, il faut une
**cause de mort de branche** : cladoptose par l'OMBRE (branche basse sous la couronne qui
ne reçoit plus de lumière → meurt), ou ④ armillaire/vent. Décision de conception (Nico) —
non inventée ici. Aussi : lierre/jasmin/thym/lavande/myrtille/framboisier, ligneux réels,
ne portent pas `age_curve` → exclus.
Perf : surcoût nul (aucun dépôt ; état identique avec/sans, écarts de tick = bruit de deux
runs parallèles). Échecs pré-existants non relancés hors suites touchées.

## ②bis Les branches meurent — FAIT (2026-10-22), golden INTACT `1ce02bce…`

**Livré** :
- Donnée d'espèce `ligneux` (+ `fragilite_bois`, `bois_chute_cm3`, `bois_chute_semaine`,
  défauts neutres, `plants/base/familles.py`) ; `frac_bois_mort` lit `ligneux` (plus
  `age_curve`). **Espèces `ligneux`** : les 11 arbres (figuier, pommier, cerisier, noyer,
  chêne, hêtre, bouleau, charme, sapin, aulne, saule) + lierre, jasmin, framboisier, thym,
  lavande, myrtille. Écartés : bambou (chaume sans bois secondaire), armoise, chanvre.
  Fragilité : saule 1,6 · bouleau 1,5 · figuier 1,4 · aulne 1,2 · hêtre 0,7 · chêne,
  charme 0,6 · autres 1,0. Chute arbustes : framboisier 600 cm³ sem. 38, lavande 80 sem.
  48, thym 40 sem. 48, myrtille 60 sem. 46 (× maturité, après 1 an).
- `sim/growth/cladoptose.py` (NOUVEAU, pur) : axe porteur protégé (enfant le plus épais),
  lumière par pointe = lumière reçue × (1 − densité·0,35)^n pointes plus hautes (auto-
  ombrage que LightField exclut), branche morte si TOUTES ses pointes < 0,18/tol et racine
  ≥ 26·tol sem. ; SANS ÉTAT (pas de champ neuf sur `Segment` → snapshot/save inchangés) ;
  une branche > 25 % de la structure tombe par rameaux. Choix de casse levier × hachage.
- `sim/engine/branches.py` (NOUVEAU) : étape 9c-ter de `boucle.py` — ombre (saison
  feuillée), tempête (vent local × rafale × turbulence, seuil 0,45), neige (manteau ≥ 0,3
  une semaine de Neige, caduc ×0,3), arbustes ; même relais `deposer_bois_tombe`.
- `sim/bois_initial.py` (NOUVEAU) appelé par `tools/simserver/commands.py` pour `full` et
  `propre` (pas `smoke`) : bois sous les ligneux + 2-4 pièces/tuile (souche 1,5-3 / branche
  0,4-1), âges 0-150 sem.
- Tests `test_bois_mort` 21/21 (12 neufs) ; mesure `mesures/bois_mort.py` étendue.

**Mesures** [graine 1521550718, monde `full`, 104 sem., n=1 run ; base = HEAD lancé en
parallèle] :
| sem. | plots bois>0 | masse bois | mycélium max / méd | base (②) |
|---|---|---|---|---|
| 0 | 21/1188 | 18,1 | 0 / 0 | 0 plot |
| 52 | 21 | 7,3 | **0,371** / 0,0001 | 0 plot, 0,059 / 0,0001 |
| 104 | 21 | 3,3 | 0,449 / 0,0023 | 0 plot, 0,449 / 0,0021 |
Branches tombées sur `full` : **0** en 2 ans (le monde ne porte qu'UN ligneux, le pommier
pré-vieilli dont seule `age_years` est vieillie — sa structure est juvénile ; aucun arbuste).
Arbres isolés, croissance pure 520 sem. [n=1 arbre/espèce, plein soleil] : pommier 0-1
branche/an dès l'an 7, chêne/hêtre 1-2/an, bouleau 0 ; ~0,01-0,1 de bois/an/arbre.
Pommier dans le moteur (tuile seule, 10 ans) : 1 casse tempête an 6, 1 ombre an 8.
Perf : tick an 0 934 → 948 ms (+1,5 %), an 1 1126 → 1132 ms (+0,5 %) [n=1 run] — sous +5 %.

**⚠ REMONTÉES** :
1. **Flux continu non atteint sur `full`** : la mécanique marche (tests, arbres isolés) mais
   le monde de jeu n'a qu'un ligneux juvénile → seul le bois INITIAL nourrit le mycélium
   (max 0,06 → 0,37 l'an 1), et il fond de 60 %/an (décompo `bois` × saprophyte). Pistes
   (décision Nico) : la ceinture boisée (D73) lâche du bois en lisière ; planter des
   ligneux/arbustes dans `full` ; pré-faire pousser la STRUCTURE des fruitiers pré-vieillis.
2. Cible kickoff « 2-6 branches/an pour un arbre de 10 ans » NON tenue : la structure est
   trop grossière (≤ 55 segments, pas de réitération) — seuil 0,30 démantèle chêne/hêtre
   (32 → 12 segments), 0,18 retenu = 0-2/an.
3. Héliophile/sciaphile non différencié entre arbres : tous ont `shade_tolerance` 0,9 (strate
   haute) → seuls les gènes modulent. Donner une tolérance par arbre change aussi croissance
   et germination → hors périmètre.
4. Taille : `perennials.py` 375 et `sauvages.py` 352 LDC (bande vigilance, déjà 367/346).

## ②ter Arbres adultes — FAIT (2026-10-22), golden RE-FIGÉ `df6ebf04…`

**Livré** :
- A. `sim/precroissance.py` (NOUVEAU, pur, hors tick) `pre_croitre(plant, seed, annees)` :
  `grow_plant` semaine 1..N·52 (finit en fin d'hiver) + cladoptose au rythme borné du jeu
  (plein soleil, auto-ombrage seul), puis `update_footprint`. Appelé par
  `commands._pre_vieillir_fruitiers` (`full`/`propre`) et par `bancs/base.vieillir` (bancs F5).
  Pommier de `full` : 1 seg./22 cm → **4 seg., 174 cm**, couronne r 50 cm. Init : +~10 ms ;
  snapshot +3 segments. La graine ne change pas la forme [3 graines testées].
- B. `shade_tolerance` par arbre (échelle existante, défaut strate haute 0,90) : bouleau
  0,75 · cerisier, noyer, saule 0,80 · **pommier 0,85** · figuier, aulne 0,85 · chêne 0,90 ·
  charme 1,15 · sapin 1,25 · hêtre 1,30. Lecteurs vérifiés : croissance (`light·tol` plafonné
  à 1 → un tol < 1 freine aussi en plein soleil : 0,6+0,4·tol), `shade_stress_damage` (÷tol),
  germination/succession, cladoptose. Pommier d'abord à 0,80 : `test_senescence` ROUGE (mort
  « carence lumineuse » à 54 ans sous ses propres rejets ; 0,75 → 35 ans, 0,78/0,82/0,85 →
  sénescence 59,8 ans) → test au bord du chaos, 0,85 retenu.
- C. Rythme BORNÉ sans état : `fenetre_ouverte` (1 sem./`CLADO_FENETRE`=6, phase hachée par
  position) + `n_max=CLADO_PAR_FENETRE`=1 (la branche la plus sombre) → ≤ ~6/an. Ce bornage
  permet `CLADO_SEUIL` 0,18 → **0,25** sans raser. Balayage 0,18/0,25/0,30, 7 arbres pré-crûs
  14 ans [n=1 arbre/espèce] : adultes plein soleil pommier 1-3/an, cerisier 2-4, chêne/hêtre
  0-2, bouleau ~0 ; lumière 0,6 : bouleau 3-6/an, hêtre 0-3. Pommier 10 ans en plein soleil :
  34 seg. (55 sans cladoptose), couronne r 186 cm (cible 200).
- Tests `test_bois_mort` 28/28 (7 neufs : J pré-croissance, K ordre des tolérances, L rythme).

**Golden** : dérive LOCALE prouvée (pommier remis à `shade_tolerance=None` → `1ce02bce…` au
bit près) : pommier du smoke `growth_factor` 0,780 → 0,770, abscission 0,122→0,121, 4 lignes
NPK ±0,001, voisins ~1e-10 (ombre). `df6ebf044655d162293ce3dfee1baa3dc781a7f39bae78d4a7594f120b80b0e6`.

**Mesures** [graine 1521550718, `full`, 104 sem., n=1 run ; base = HEAD ②bis en parallèle] :
| sem. | plots bois>0 | masse bois | mycélium max / méd | branches tombées |
|---|---|---|---|---|
| 0 | 21/1188 | 18,13 | 0 / 0 | — |
| 52 | 21 | 7,30 | 0,371 / 0,0001 | 0 |
| 104 | 21 | 3,29 | 0,449 / 0,0023 | 0 |
Identique à ②bis. Perf : tick an 0 642 vs 652 ms, an 1 1061 vs 1075 ms (−1,5 %) [n=1 run].
Variante MESURE seule (non livrée) pommier pré-crû **10 ans** : 36 seg., 347 cm ; bois sem. 0
23,3 (43 plots) → 9,75 → 4,40 ; ombre 2 branches an 1, 3 an 2 (0,054 puis 0,026 de bois/an).

**⚠ REMONTÉE — objectif de Nico NON atteint, et hors de portée de ce tronçon** : (1) le
pommier de 5 ans n'a pas de branche latérale dans la morphogénèse (flèche seule jusqu'à
l'an 6-7) → 0 branche en 2 ans ; (2) même adulte, UN arbre lâche ~0,03-0,05 de bois/an,
quand le stock au sol perd ~55-60 %/an (≈ 10/an l'an 1, ≈ 2/an l'an 2) : écart **×40 à
×100**. Une souche initiale (1,5-3) vaut tout le bois d'un pommier de 10 ans (3,6). Seule
une source à l'échelle d'un BOISEMENT tient le flux : ceinture boisée D73 qui lâche du bois
en lisière, ou des ligneux dans `full` — décision de composition (Nico), non prise ici.

## ③ Règne fongique — FAIT (2026-10-22), golden INTACT `df6ebf04…`, pont **0.5.52**

**Livré** :
- `fields/fongique.py` (NOUVEAU, données pures) : `REGISTRE_FONGIQUE` 13 espèces (clé, nom,
  groupe, substrats ⊂ {bois, humus, racines}, hôtes = familles OU noms d'espèce, fenêtres,
  comestibilité en tags cumulables — tue-mouches `psychedelique`+`veneneux`, polypore
  `immangeable` —, pH optionnel, `parasite`). Fenêtres : collybie SEULE sem. 44-52 et 1-4,
  morille SEULE sem. 5-13, le reste de l'été à sem. 43. Niche du plot : `bois` =
  `bois_fresh_at > 0` ; `humus` = `om_active ≥ HUMUS_OM_MIN` (0,6) ou plot d'ancrage d'un
  bac/pile ; `racines` = labels des racines vivantes. Départage par hash spatial (sosies
  sur la même niche : pleurote/hypholome/collybie/armillaire, rosé/clitocybe, cèpe/phalloïde).
- Parasites (armillaire racines, polypore) : niche `racines` seulement sur hôte AFFAIBLI
  (`etat != "sain"`, labels `"!"`-préfixés) — la visibilité seule ; l'attaque reste ④.
  Armillaire fructifie aussi sur le bois (souche).
- `sample_carpophores(eco, seed, wiy, pluie_prec, racines)` : gate automne SUPPRIMÉ
  (`_CARPO_AUTOMNE` retiré) → semaine qui SUIT une pluie (`PLUIE_APPORT ≥ 0,05`, Pluie
  prolongée/Orage), fenêtre de l'espèce, niche ; `Carpophore.espece`. Seuils recalibrés
  `CARPO_MYCEL_MIN` 0,30 → **0,20**, `CARPO_HUMIDE_MIN` 1,5 → **1,2** (perception seule).
- `sim/champignon_role.py` : `racines_par_plot` (une fois par tuile, seulement après pluie)
  + `pluie_semaine_precedente(gs)` (météo `week−2`, pure, honore `pluie_forcee`).
- Pont : 7ᵉ champ carpophore = clé d'espèce ; `CarpophoreLayer.cs` lit par index → ignore.
- Tests : `tests/test_fongique.py` 28/28 (NOUVEAU) ; `test_mycelium` 36/36 (section M
  adaptée : niche humus + pluie) ; versions 0.5.52 dans `tests/simserver/*`.
- Mesure : `mesures/fongique.py` (lit le VRAI bloc `carpophores` du snapshot).

**Mesures** [`full`, n=1 run par graine ; « plot-sem. » = plot fructifiant une semaine] :
| graine | plot-sem. an 0/1/2 | sem. avec carpophores an 0/1/2 | espèces vues (plot-sem. sur 3 ans) |
|---|---|---|---|
| 1521550718 | 70 / 90 / 103 | 15 / 11 / 7 | coprin 156 · collybie 41 · hypholome 34 · armillaire 13 · pleurote 10 · rosé 3 · clitocybe 3 · psilocybe 3 |
| 7 (sèche) | 6 / 0 / 10 | 3 / 0 / 3 | coprin 8 · collybie 4 · hypholome 2 · psilocybe 2 |
| 1515525502 | 65 / 156 / 167 | 10 / 13 / 9 | coprin 264 · hypholome 33 · collybie 32 · clitocybe 27 · armillaire 18 · rosé 8 · psilocybe 4 · pleurote 2 |
`full` 1521550718, 104 sem. via le pont : coprin 65 · collybie 41 · hypholome 31 · armillaire
13 · pleurote 10 ; carpophores dans TOUTES les saisons (printemps 4-5 = collybie sem. 1-4).
Où : coprin sur 20 plots d'humus riche (planches), bois sur les 21 plots de bois initial
(collybie l'hiver, hypholome/pleurote/armillaire l'automne), prairie = racines du pâturin.
Banc `pluie_continue` 104 sem. : 0 carpophore l'an 0 (pas de bois initial, mycélium max
0,08 à sem. 41) puis coprin **chaque semaine** sem. 78-95 (fin de sa fenêtre sem. 43).
Perf : tick inchangé (aucun code de tick touché) ; perception carpophores 3,1 ms/snapshot
(0,3 % du tick ; 0,8 % sur le banc pluie) [n=1 run].

**⚠ REMONTÉES** :
1. **Morille, cèpe, phalloïde, tue-mouches, polypore : 0 sur `full`** — composition, pas
   mécanique : aucune Fagacée/bouleau/sapin dans `full` ; sous le pommier le mycélium plafonne
   ~0,015 (sol pauvre en `om_active`, pas de bois). Couverts par `test_fongique`. Même
   décision de boisement que ②ter (ligneux dans `full` / ceinture D73).
2. Coprin domine (~60 %) : 90 % des plots à mycélium ≥ 0,2 ont `om_active` ≥ 0,6 (le réseau
   vit de l'humus des planches, pas du bois). Fidèle au moteur, à garder en tête au F5.
3. Hôte `Pinaceae` ajouté à la tue-mouches (écologie réelle : bouleau, pin, épicéa).
4. `serialize.py` 377 → 380 LDC (bande vigilance, inchangée en nature).

## ④ Parasite de faiblesse — FAIT (2026-10-22), golden INTACT `df6ebf04…`

**Livré** :
- `sim/engine/racines.py` (NOUVEAU, pur, sans état) : `HOTES_PARASITES` = union des `hotes`
  des espèces `parasite=True` du registre (Pommier, Cerisier, Fagaceae, Bouleau — DONNÉES) ;
  `faiblesse` = 0 si vitalité > SEUIL_SAIN (même porte que les labels `"!"` du ③), rampe
  → 1 à SEUIL_AFFAIBLI ; `pression_parasite = PARASITE_K (2,0) × mycélium moyen sous les
  `root_plots` × faiblesse`, AJOUTÉE à la cible `rong` du lerp `root_herbivory_memory`
  (`_update_physiology`, `min(1, campagnol + parasite)`).
- `fields/ecofields/uptake.facteur_racinaire(mémoire, tolérance, mycélium)` : formule
  extraite de `plant_uptake` (bit-identique), SOURCE UNIQUE du facteur racinaire.
- `eau_percue(plant, eco, hum)` = hum × facteur racinaire : lue par le stress hydrique
  (`croissance._update_physiology`) et la convalescence (`mortalite`, `min(1, hum)`).
- Test `tests/test_parasite.py` 17/17 (NOUVEAU) ; mesure `mesures/parasite.py` (`--sans` = avant ④).

**⚠ PRÉMISSE RÉFUTÉE (canal)** : `root_herbivory_memory` ne réduisait QUE l'uptake (ce que
le sol cède) ; aucun lecteur ne ramenait la perte à la plante (stress, croissance,
convalescence lisent l'humidité du SOL) → forcer la mémoire à 1,0 sur TOUT le smoke ne
changeait rien à la plante (pommier hauteur 59,983 → 59,980, vitalité moyenne T0 ↑). Le
canal campagnol était donc INERTE aussi. Corrigé par `eau_percue` — **le campagnol est
désormais ressenti lui aussi** (979 plantes l'an 2 sur `full`, population 650 vs 651
[n=1 run]). Autre prémisse fausse : le smoke porte du campagnol (mémoire du pommier ~0,09) — le
commentaire « densité nulle (smoke) » de `croissance.py` est périmé (non touché).

**Golden** : smoke = pommier affaibli sem. 92 (vitalité 0,733, mycélium 0,017) → pression
0,010, mémoire 0,0675 → 0,0681 en fin de run ; pas d'écart sur le digest ni le log (uptake
d'eau d'hiver ≈ 0, arrondis) → hash INCHANGÉ, cas « constaté, intact ».

**Mesures** `full`, 156 sem. [n=1 run par graine] :
| graine | hôtes vus | attaqués (sem., pression max) | morts d'hôtes | tick an 2 avec / sans |
|---|---|---|---|---|
| 1521550718 | 1 pommier | 1 sem., 0,037 | 0 | 1256 / 1277 ms |
| 7 | 2 pommiers | 30 et 85 sem., 0,018 / 0,014 | 0 | 991 / 1011 ms |
| 1515525502 | 2 pommiers | 65 sem., 0,053 | 0 | 1132 ms |
Bois produit par le parasite : 0 (aucune mort). Perf : surcoût non mesurable (écarts −2 %,
bruit de runs parallèles) — sous +5 %.
Banc contrôlé (pommier pré-crû 8 ans, vitalité 0,6, mycélium et sol imposés, 312 sem.)
[n=1 arbre par cas] : semaines non saines témoin/parasite (myc 0,4) : sol ≤ 0,5 → 72/126 ;
≤ 0,4 → 126/270 ; myc 0,25 sol ≤ 0,3 → 270/312 (jamais guéri). **0 mort** dans tous les cas.

**⚠ REMONTÉES** :
1. **Le parasite ne tue pas** : c'est une TRAPPE de faiblesse (convalescence bloquée,
   stress hydrique ↑), pas une mort. Limite structurelle du canal partagé : facteur
   racinaire ≥ 0,5 à mémoire 1 (`ROOT_HERBIVORY_UPTAKE_MALUS` 0,5, compensation
   mycorhizienne, plancher 0,3) → sur sol humide (≥ 1) l'eau perçue ne descend jamais sous
   le seuil de stress (0,5). Tuer exige une décision de Nico : (a) régime LÉTAL
   « pourridié du collet » miroir de l'annélation du campagnol (mort mécanique d'un hôte
   « malade » à mémoire saturée — interdit par le kickoff, d'où non fait) ; ou (b) un malus
   propre au parasite, non plafonné par le cap campagnol.
2. Paradoxe assumé : la compensation mycorhizienne (`MYCO_ROOT_COMPENS`) atténue aussi la
   pourriture alors que c'est le même réseau qui l'apporte (champ `mycelium` unique) —
   net = myc × (1 − 0,5·myc), monotone ; à revoir si un champ par guilde existe un jour.
3. Composition (comme ②ter/③) : le seul hôte de `full` est le pommier, sous lequel le
   mycélium plafonne ~0,01-0,05 → pression ≤ 0,053.
4. `mortalite.py` 246 LDC, `croissance.py` 220 : bande verte.

## ⑤ Voix des champignons — FAIT (2026-10-22), golden INTACT `df6ebf04…`, pont **0.5.53**

**Livré** :
- `sim/champignon_encyclo.py` RÉÉCRIT (ex-fiche générique Q2) : `FICHES_CHAMPIGNON`, 13
  espèces = registre ③ (même ordre) : `concept` (saprophytie ×5 · mycorhize ×3 [morille,
  cèpe, tue-mouches] · sosies ×3 [hypholome, clitocybe, phalloïde] · parasitisme ×2),
  `vu` (avant le nom, sans nom ni comestibilité), `comestibilite`, fiche 3 niveaux
  (N3 = effets + comestibilité), carnet D/I (sans `{e}` : la note ne nomme pas), article.
- `sim/champignon_voix.py` (NOUVEAU, hors tick) : `noter_fructification` (ledger
  `kind="fructification"`, dédup espèce×saison), `crediter_concept` (découverte espèce →
  concept p1 ; espèce NOMMÉE → +1, plafond 3 ; au 3 → page récompense),
  `champignons_nommes` (nom + comestibilité des seules espèces nommées).
- Branchements : `encyclopedie_types.CHAMPIGNONS` = registre ; `encyclopedie` fiche
  champignon 3 niveaux `min(palier,3)` (sans `interconnexions` → rendu 3 niveaux côté vue) ;
  `carnet` verse CONCEPT_DE/GABARIT `("fructification", espèce)` ; `signes.appris` :
  `faune` += espèces fongiques nommées, nouvelle clé `champignons {clé:{nom,comestibilite}}` ;
  `magazine_articles` (+ `articles` dans `cmd_magazine`) ; pages **P43-P47** (amadou/Ötzi,
  psilocybe, tue-mouches, morille, ronds de sorcière) ; pont `observer_espece` accepte les
  clés fongiques (+ `zone`), `legende.champignons {clé: vu}`, debug `palier3` les 13.
- C# minimal (sans quoi le nom ne se gagnait plus en jeu) : `CarpophoreLayer` lit le 7ᵉ
  champ et le survol envoie la clé d'espèce ; info-bulle : `vu` par espèce, nom réel +
  ligne de comestibilité une fois nommé. `dotnet build` 0 erreur.
- Tests : `tests/test_champignon_voix.py` 23/23 (NOUVEAU) ; adaptés : `test_encyclopedie`
  70/70, `test_signes_legende` 42/42, `test_infobulle_vivant` 31/31, `test_sim_server`
  287/287 (versions 0.5.53) ; carnet/pages/magazine/fongique/mycélium verts.

**⚠ PRÉMISSES RÉFUTÉES / DÉCISIONS** :
1. « Fructification consignée au ledger via `sim/evenements.py` » : faux — les carpophores
   sont de la perception (snapshot), absents du log du tick ; les consigner au snapshot
   rendrait le journal dépendant de la fréquence d'appel. Consignés au SURVOL (patron
   `observer_signe`).
2. Les concepts fongiques n'avaient aucun chemin de crédit (comme `carnivorie`) → règle
   ajoutée : nommer les espèces crédite leur concept (sinon carnet descriptif à vie).
3. Clé générique `champignon` retirée partout (Python) ; `observer("champignon")` = no-op.
   `CHAMPIGNON_VU`/`CHAMPIGNON_ROLE` (signes_corpus) gardés : repli et rôles b/r/h.
4. Le survol n'envoie pas encore le lieu → notes « au jardin » (le pont accepte
   `tile`/`x_cm`/`y_cm` : à brancher au ⑧ si voulu).

## ⑥ Manger un champignon et la vision — FAIT (2026-10-22), golden INTACT `df6ebf04…`, pont **0.5.54**

**Livré** :
- `sim/champignon_manger.py` (NOUVEAU) : `carpophores_tuile` (source UNIQUE snapshot +
  geste, moins les mangés de la semaine : `game_state["carpophores_manges"]`, remis à
  zéro au changement de semaine) ; `manger_carpophore` : comestible → +`HARVEST_GAIN_FULL`
  × densité/`CARPO_DENS_REF` ; vénéneux → −0,5 × Vigueur max ; mortel → −0,9 × max
  (plancher 0, pas de mort) ; psychédélique → vision ; tue-mouches → vision + perte ;
  immangeable → refus sans consommation. Message sans nom tant que l'espèce n'est pas nommée.
- `sim/vision.py` (NOUVEAU) : `game_state["vision"][joueur] = {debut, fin, overdose,
  survols}` (JSON pur). Durée : semaine où l'on mange + 1 semaine pleine (`week ≤ fin`).
  `palier_lu` = transcendant pendant l'effet, branché SEULEMENT dans les lecteurs :
  `carnet._registre`, `encyclopedie_lire` (niveau ; la découverte reste au vrai palier →
  pas de fiche créée), `signes.signe_appris`/`faune_apprise`, `champignons_nommes`.
  `maitrise.palier` (Vigueur max, magazine, extension) jamais touché. Clôture
  `clore_si_echue` dans `cmd_step_week` (hors tick) : survols ≥ 3 → +1 palier EXACT
  (crédit ÷ spillover), plafond 4, inconnue → découverte ; `player.vision.reste` notifié une fois.
- `sim/voix_etres.py` + `sim/voix_etres_corpus.py` (NOUVEAUX) : besoins mesurés
  (plante : mémoires sécheresse/asphyxie/ombre + voisin qui fait de l'ombre, Liebig N/P/K,
  pH/chlorose, allélopathie effective, concurrence racinaire + rival, campagnol/parasite,
  ravageurs, vent ; bête : ressource, famille florale/proie, abri `habitat_fn`, prédateurs,
  humidité des hygrophiles ; champignon : rôle b/r/h) → ≤ 3 phrases, variante par hash.
- Pont : commande `parler` (`tools/simserver/vision_cmds.py`, NOUVEAU), `manger` +
  `target.carpophore [r, c, slot]` (`champignon_route.py`, NOUVEAU, aiguillé dans
  `plante_route`), `player.vision`, clé `voix` en overdose seulement.
- Tests : `tests/test_vision.py` 37/37 (NOUVEAU) ; versions 0.5.54 dans tests/simserver.

**Mesure overdose** [n=1 run, `full` sem. 61, 509 plantes, médiane de 5 snapshots] :
snapshot 80 → 154 ms (+75 ms) ; avant mémoïsation du voisinage par tuile : +198 ms.

**⚠ DÉCISIONS / PRÉMISSES** :
1. Palette : `manger` reste famille « plante » (le kickoff pointait `palette.py`) ;
   l'aiguillage carpophore se fait sur la FORME du target (patron `ecraser`/`creuser`)
   pour ne pas casser la cohérence des macros.
2. `parler` n'est pas strictement read-only : il compte le survol (seule écriture,
   tranche vision). Un survol = un appel → la vue ⑧ doit appeler `parler` UNE fois par
   entrée de survol (pas par frame). Seuil 3 survols (knob `SEUIL_SURVOLS`).
3. Pendant la vision l'index de l'encyclopédie n'est PAS élargi (on lit complètes les
   fiches déjà découvertes) ; l'info-bulle nomme TOUT (bêtes et champignons, comestibilité).
4. Pertes via `vigueur.spend` → masquées par « Vigueur infinie » (ON par défaut).
5. Champignons parlent aussi (rôle local), pour que leur survol compte dans « ce qui reste ».
6. `serialize.py` 380 → 385 LDC (bande jaune, déjà au-dessus avant ⑥).
7. Dette « voix écrites à la main » = D113 (déjà ouverte, rien à ajouter).

## Ajouts de Nico à l'accord (2026-10-22)
- Bois mort VISIBLE au sol, dégradation en sprite à stades (② pont, ⑧ dessin).
- Overdose : 2ᵉ psychédélique pendant l'effet → phrases de TOUS les êtres à chaque snapshot.
- Ce que le jardinier a longuement survolé pendant la vision lui reste (palier durable borné).

## Diagnostic mesuré (phase A)

Script : `mesures/bilan_eau.py <seed> <semaines>` (monkeypatch mémoire, golden intact).
Seed 1515525502, monde `full`, 156 sem. [n=1 run] :
- humidité médiane an0 1,34 → an1 0,41 → an2 0,08 ; semaines de pluie (Pluie+Orage) : 3 / 2 / 1 par an.
- par plot et par semaine : uptake 0,010 → 0,019 → 0,014 ; drainage 0,0075 → 0,0012 ; apport net hydro ≤ +0,012.
- → **la transpiration dépasse tout l'apport, toute l'année**, pas de recharge hivernale.
- CONFIRMÉ sur 2 autres graines [n=3 graines au total, 1 run chacune] : seed serveur 1521550718
  (0x5AB1057E) hum méd 1,34 → 0,27 → 0,07, pluie 6/2/1 sem. ; seed 7 : 1,02 → 0,17 → 0,06, pluie 1/1/1.
  Plancher commun ≈ 0,07 dès l'an 2 ; population 400-620 plantes en an 1-2.
- ROSÉE mesurée (seed 1521550718, 104 sem.) : +0,0079/plot/sem an 0 → +0,0014 an 1. Elle
  S'EFFONDRE avec le sol : `rosee.py` dérive le point de rosée de l'humidité du SOL
  (`GAIN_HUM_ROSEE · humidite/3`, pas de champ « humidité de l'air ») → boucle sèche.

Causes au code (vérifiées) :
1. `sim/weather.py` : `P_EVENT = 0.15` → 85 % des semaines « Beau temps », nébulosité 0,10
   (`NEBULOSITE`, `fields/ecofields/constants.py`) → évaporation radiative quasi max chaque semaine.
   La pluie n'existe QUE comme aléa : « Pluie prolongée » fenêtre sem. 27-52, en concurrence avec
   Tempête/Redoux/Neige ; « Orage » local, été. Aucune pluie ordinaire au printemps-été.
2. `BASE_RAIN = 0.015` constant ; `PLUIE_APPORT["Pluie prolongée"] = +0.012` (une semaine de pluie
   ne fait que doubler l'apport de fond).
3. `fields/ecofields/uptake.py` : prélèvement `UPTAKE["humidite"]` par stade (0,05-0,18/plante/sem),
   modulé lumière/ombre/mémoire de sécheresse, **mais pas par la saison ni la demande climatique**
   → une plante dormante en hiver boit autant qu'en été.
4. Champignons : `sim/growth/phases.py::_elaguer` retire les segments morts **sans déposer de bois**
   (« pure structurelle ») → 0 bois mort au sol, mycélium affamé. Fructification gatée par l'automne
   seul (`fields/population/perception.py`, `CARPO_*`), jamais par la pluie.
   Encyclopédie champignon = UNE fiche générique (décision Q2 du sprint vie macro identifiable,
   `sim/champignon_encyclo.py`) → à renverser si ~10 espèces.
5. Nectar : `fields/population/registry.py::_make_nectar_grid` = floraison × goût de famille, sans
   production propre à l'espèce.

## Décisions arrêtées

- **D-pluie (Nico, Q1)** : PAS de pluie chaque semaine en jeu (seulement possible dans un banc
  de test). La rosée « tombe régulièrement » doit jouer son rôle. → la correction passe par
  des épisodes de pluie mieux répartis + transpiration saisonnière + rosée régulière (lot 2).
- **D-armillaire (Nico, Q2)** : parasite ACTIF et comestible ; « défonce les racines du
  cerisier ». Piste : canal racinaire existant `root_herbivory_memory` (campagnol → uptake),
  hôte affaibli → mort → bois mort → saprophytes (boucle fermée).
- **D-espèces (Q2)** : liste de 11 espèces proposée, non contestée ; fiche par espèce
  (renverse Q2 vie macro) supposée acceptée — à confirmer implicitement au lot 2.
- **D-vision (Nico, Q3)** : manger un psychédélique = UNE SEMAINE d'effet : couleurs plus
  vives, informations plus claires « comme un niveau transcendant de compréhension » le temps
  de l'effet, et plantes + animaux PARLENT dans leur info-bulle : disent leurs besoins
  (nourriture, voisins…). Comestible → Vigueur ; vénéneux → Vigueur effondrée sans mort (reco,
  non contesté).

- **D-eau (Nico, Q4, lot 2)** : (a) rosée calculée sur une HUMIDITÉ DE L'AIR océanique
  saisonnière déterministe (plus sur l'humidité du sol) ; (b) transpiration SAISONNIÈRE, portée
  par les FEUILLES : dormant/défeuillé ≈ 0, ∝ chaleur + ciel, et ∝ TYPE DE FEUILLAGE (Nico :
  « les feuilles grandes et ouvertes transpirent plus que les épines ») → constante par espèce
  (PAS un gène : `tolerance_secheresse` = tolérance de croissance, autre chose ; forme des
  feuilles n'existe qu'en C# — kit de rendu — donc donnée Python neuve) ; (c) épisodes de pluie
  dans TOUTES les saisons : hiver ~1 sem/3, printemps/automne ~1/4, été orages ~1/6, chaque
  épisode recharge vraiment. **Cible de calibrage validée** [3 graines] : humidité médiane
  annuelle ∈ [1,0 ; 2,0], sol presque plein fin d'hiver, creux visible fin d'été sans désert.
  **Banc « pluie chaque semaine »** voulu (test seulement) + vérifier qu'il a VRAIMENT agi.
- **D-nectar (Nico, Q5)** : `nectar` ∈ [0,1] par espèce (data) ; nourriture butineur =
  floraison × nectar espèce × goût famille. Phacélie/bourrache/trèfle/tilleul haut, pommier
  moyen bref, tomate ≈ 0 (pollen vibré), graminées 0. « Essayons ça » → re-mesurer (i).
- **D-voix-vision (Nico, Q6)** : phrases des êtres sous vision GÉNÉRÉES par le moteur depuis
  leurs vrais besoins (gabarits). Version écrite à la main par espèce = DETTE lointaine
  (finition du jeu) → ouvrir une Dxx en phase C.
- **D-fiche (Nico)** : UNE FICHE PAR CHAMPIGNON (renverse Q2 vie macro identifiable).
- **D-parasite (Nico)** : cerisier et armillaire ne sont que des EXEMPLES → mécanique
  GÉNÉRIQUE : un champignon parasite attaque les racines des hôtes de ses familles (data).
  Nico a demandé la liste du catalogue fongique motivée → posée en lot 3.

- **D-catalogue-fongique (Nico, Q7)** : les 13 espèces ci-dessous VALIDÉES (« j'adore »).
  Hôtes/substrats/saisons = DONNÉES par espèce, jamais codés en dur.
- **D-parasite-faiblesse (Nico, Q8)** : le parasite n'attaque qu'un hôte DÉJÀ affaibli
  (vitalité basse). Canal vérifié : `plant.root_herbivory_memory` lerpé vers une pression
  `rong` (`sim/engine/croissance.py` ~l.383) puis lu par `plant_uptake` → le parasite ajoute
  sa pression à ce canal (intention ; placement exact au sous-agent).
- **D-feuillage (Nico)** : constante par espèce `type de feuillage` ∈ {large, moyen, fin,
  aiguilles, cireux/duveteux} → coefficient de transpiration. Validé.

## Questions ouvertes

Aucune. Accord de Nico pour figer : 2026-10-22.

## §REPRISE

Lire `CLAUDE.md` + ce fichier + le kickoff du prochain tronçon « à faire » de la carte.
Remontées de ① tranchées (D114, D115). ② + ②bis + ②ter FAITS : bois mort initial réel,
causes de mort de branche codées et bornées, arbres pré-crûs, ombre par espèce — mais
**flux continu NUL sur `full` (un seul ligneux, 5 ans, sans latérales)** (cf. §②ter
remontée) → source boisée à trancher par Nico avant ③ (ceinture D73 ou ligneux dans `full`).
③ FAIT (golden INTACT `df6ebf04…`, pont **0.5.52**) : 13 espèces data-driven, fructification
après la pluie ; seules 8 sortent sur `full` (pas d'hôte mycorhizien, cf. §③ remontée 1).
④ FAIT (golden INTACT `df6ebf04…`) : parasite générique sur hôte affaibli + `eau_percue`
(canal racinaire enfin ressenti, campagnol compris) ; ne tue pas (cf. §④ remontée 1).
⑤ FAIT (golden INTACT `df6ebf04…`, pont **0.5.53**) : 13 champignons avec leurs 5 voix,
clé par espèce de bout en bout (survol C# compris) ; cf. §⑤.
⑥ FAIT (golden INTACT `df6ebf04…`, pont **0.5.54**) : manger un carpophore, vision d'une
semaine (lecture transcendante via `sim/vision.palier_lu`), `parler`, overdose, palier durable ;
cf. §⑥ (pour ⑧ : `parler` une fois par entrée de survol ; `target.carpophore [r, c, slot]`).
Prochain tronçon : ⑦ `07_nectar_espece.md` (golden de départ **`df6ebf04…`**, pont 0.5.54).
Chaque tronçon met à jour sa ligne de statut, consigne ses mesures [n=…] et ses hashes golden.
## Liste fongique VALIDÉE (Q7)

Bois mort : pleurote (comestible) · hypholome en touffes (vénéneux, sosie) · collybie à pied
velouté (comestible, hiver). Humus/prairie : coprin chevelu (comestible, sol remué/compost) ·
rosé des prés (comestible, prairie) · clitocybe blanchâtre (mortel, sosie du rosé) · psilocybe
lancéolé (psychédélique, graminées) · morille (comestible, printemps, vergers). Mycorhiziens :
cèpe (comestible, chêne/hêtre) · amanite phalloïde (mortelle, chêne/hêtre) · amanite
tue-mouches (psychédélique + toxique, bouleau). Parasites : armillaire (comestible cuit,
feuillus dont Rosacées fruitières, chêne) · polypore du bouleau (non comestible, amadou).
