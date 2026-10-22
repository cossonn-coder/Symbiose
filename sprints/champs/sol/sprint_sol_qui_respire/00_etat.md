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
| ③ | `03_regne_fongique.md` | neutre | à faire |
| ④ | `04_parasite_faiblesse.md` | re-figé si hôte affaibli au smoke | à faire |
| ⑤ | `05_voix_champignons.md` | neutre | à faire |
| ⑥ | `06_manger_vision.md` | neutre | à faire |
| ⑦ | `07_nectar_espece.md` | re-figé si floraison au smoke | à faire |
| ⑧ | `08_vue_godot.md` | intact | à faire |

Golden de départ (relevé par ①) : `22768f339ac41bb20b1604bb29672bb3b209ee62ec659b1c8369dd31ccd6cfb8`.
Golden après ① : `1ce02bce275a2b4c262564e7eda384b1071125ebc67e65346d101820102d6bfd` (re-figé
UNE fois, annoncé : climat + hydrologie changent partout). Pont **0.5.50**.

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
Remontées de ① tranchées (D114, D115). **② FAIT mais INERTE** (aucun ligneux ne s'élague,
cf. §②) → à trancher par Nico/orchestrateur : ajouter une cause de mort de branche
(cladoptose par l'ombre ?) avant ③, ou accepter que le bois mort n'arrive que par ④/squelettes.
Prochain tronçon : ③ `03_regne_fongique.md` (golden de départ `1ce02bce…`, pont 0.5.51).
Chaque tronçon met à jour sa ligne de statut, consigne ses mesures [n=…] et ses hashes golden.
## Liste fongique VALIDÉE (Q7)

Bois mort : pleurote (comestible) · hypholome en touffes (vénéneux, sosie) · collybie à pied
velouté (comestible, hiver). Humus/prairie : coprin chevelu (comestible, sol remué/compost) ·
rosé des prés (comestible, prairie) · clitocybe blanchâtre (mortel, sosie du rosé) · psilocybe
lancéolé (psychédélique, graminées) · morille (comestible, printemps, vergers). Mycorhiziens :
cèpe (comestible, chêne/hêtre) · amanite phalloïde (mortelle, chêne/hêtre) · amanite
tue-mouches (psychédélique + toxique, bouleau). Parasites : armillaire (comestible cuit,
feuillus dont Rosacées fruitières, chêne) · polypore du bouleau (non comestible, amadou).
