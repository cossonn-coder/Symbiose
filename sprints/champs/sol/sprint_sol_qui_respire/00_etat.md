# Sprint « le sol qui respire » (D111) — état partagé

**Phase** : CONCEPTION FIGÉE le 2026-10-22 → prêt pour `/sprint-auto sprint_sol_qui_respire`.
Doc : `docs/champs/sol/conception_sol_qui_respire.md`. 8 tronçons, aucun commencé.

## Carte des tronçons (statut)

| # | Kickoff | Golden | Statut |
|---|---|---|---|
| ① | `01_bilan_hydrique.md` | RE-FIGÉ annoncé | à faire |
| ② | `02_bois_mort.md` | re-figé probable | à faire |
| ③ | `03_regne_fongique.md` | neutre | à faire |
| ④ | `04_parasite_faiblesse.md` | re-figé si hôte affaibli au smoke | à faire |
| ⑤ | `05_voix_champignons.md` | neutre | à faire |
| ⑥ | `06_manger_vision.md` | neutre | à faire |
| ⑦ | `07_nectar_espece.md` | re-figé si floraison au smoke | à faire |
| ⑧ | `08_vue_godot.md` | intact | à faire |

Golden de départ : à relever par ① (`python3 -m tests.test_golden`) avant toute modif.

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
Chaque tronçon met à jour sa ligne de statut, consigne ses mesures [n=…] et ses hashes golden.
## Liste fongique VALIDÉE (Q7)

Bois mort : pleurote (comestible) · hypholome en touffes (vénéneux, sosie) · collybie à pied
velouté (comestible, hiver). Humus/prairie : coprin chevelu (comestible, sol remué/compost) ·
rosé des prés (comestible, prairie) · clitocybe blanchâtre (mortel, sosie du rosé) · psilocybe
lancéolé (psychédélique, graminées) · morille (comestible, printemps, vergers). Mycorhiziens :
cèpe (comestible, chêne/hêtre) · amanite phalloïde (mortelle, chêne/hêtre) · amanite
tue-mouches (psychédélique + toxique, bouleau). Parasites : armillaire (comestible cuit,
feuillus dont Rosacées fruitières, chêne) · polypore du bouleau (non comestible, amadou).
