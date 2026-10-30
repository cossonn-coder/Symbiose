# Conception — le sol nourricier (D120)

> Figée le 2026-10-30 (`/conception D120`, arbitrages de Nico Q1-Q3 « oui aux
> recommandations »). Sprint : `sprints/champs/sol/sprint_sol_nourricier/`.
> Voisines : `conception_sol_nutriments_npk.md` (Liebig, lessivage, CEC),
> `conception_sol_qui_respire.md` (D111), D41 (mort par carence, hors périmètre),
> D119 (densités de faune, hors périmètre).

## 1. Le problème (mesuré, monde `full`, seed 42, [n=1 run])

Retour F5 de Nico : « tous les êtres vivants ont l'air de crever de faim » et, sous
vision, toutes les plantes réclament du potassium. Quatre causes :

1. **Le sol se vide sans retour.** NPK médian des tuiles : 1,01/1,01/1,01 (s0) →
   0,02/0,82/0,16 (s52) → 0,03/0,40/0,01 (s91). Le lessivage passif agit chaque
   semaine (N 12 %, K 5 %, P 0,5 %) même sans eau qui draine, et aucun flux
   d'entrée n'existe hors litière et légumineuses.
2. **La carence n'a aucun effet.** La croissance (`_avancer_stades`,
   `growth_factor`) ne lit pas N/P/K. qi médian 0,00 en an 2, vitalité 0,81-0,93,
   680 plantes. Le signe « faim » ne correspond à aucune conséquence (philo #2, #5).
3. **Voix plante** : seuil 0,4 × 3 = 1,2, au-dessus des valeurs de départ.
4. **Voix bête** : faim = nourriture locale absolue < 0,4 → 75-100 % des bêtes
   « affamées » alors que leurs populations sont stables.

## 2. Écologie de référence (pour Nico)

Les plantes puisent dans une **réserve disponible** qui se recharge sans cesse :
- **altération** des minéraux (argiles, micas, feldspaths) → K surtout, P très lentement ;
- **apports atmosphériques** d'azote (≈ 10-20 kg N/ha/an en Europe) + fixation par
  des bactéries libres du sol ;
- **recyclage** : litière, humus, déjections (déjà modélisé).

Un sol exploité sans apport descend vers un **plancher propre à sa roche**, jamais à
zéro ; mis en **jachère**, il remonte. Le lessivage de l'azote suit **l'eau qui
traverse le sol** — surtout l'hiver, quand il pleut et que les plantes dorment.

## 3. Décisions

### 3.1 Recharge vers l'équilibre de la roche (Q1)
- Chaque plot tend LENTEMENT vers un **équilibre hérité de son sol**
  (`NUTRIENT_INIT_PAR_SOL`, déjà la « roche-mère » du code) : sous l'équilibre, un
  apport `RECHARGE[e] · (équilibre − stock)` par semaine ; au-dessus, rien (les
  surplus de compost et de légumineuses ne sont pas « aspirés », ils s'en vont par
  consommation et lessivage). Échelles de temps visées : N ≈ 1 an, K ≈ 2-3 ans,
  P ≈ 5 ans (demi-vies de remontée en jachère).
- **Lessivage lié à l'eau** : le lessivage passif ne s'applique plus que là où de
  l'eau draine (`drainage_last`) ; sans drainage, rien ne part. L'amplification par
  la pluie existante (`facteur_pluie`) et son plafond restent.
- Effet de jeu : **jachère** = remontée ; **compost / légumineuses** = au-dessus de
  l'équilibre ; **sur-exploitation** = sous l'équilibre. Hétérogénéité (#7) : sable
  pauvre, argile riche, conservée.

### 3.2 Conséquence : la plante carencée pousse plus lentement (Q2)
- Même patron que l'allélopathie (`sim/engine/croissance.py`, escompte de la cible
  de `growth_factor`, plancher 0,3 déjà en place) : la cible est multipliée par un
  **facteur de nutrition** ∈ [plancher, 1], continu (rampe), calculé sous l'empreinte
  racinaire avec la loi de Liebig (le nutriment le plus rare **relativement à
  l'équilibre du sol** commande ; la carnivore ignore N, comme dans `qi_local`).
- Le besoin du **stade** pèse (profils `BESOIN` : N au végétatif, K en fructification) :
  une plante qui fructifie ressent d'abord le potassium.
- Pas de mort par carence (D41, hors périmètre). Golden **re-figé, annoncé**.

### 3.3 Voix justes
- **Plante** : l'intensité de « faim » = `1 − facteur de nutrition` du 3.2 — UNE
  source de vérité, le signe dit exactement ce que la plante subit.
- **Bête** : « faim » = la population **dépasse ce que sa nourriture locale peut
  porter** (elle décline), pas « nourriture basse ». Grille de rendu pure, comme
  `activite_grid` (zéro impact sim).

### 3.4 Mare au nord-est (Q3)
- Monde `full` seulement : une mare **déjà remplie et peuplée** dans la tuile NE
  (sable) : cuvette (altitude basse), lame d'eau, sol saturé, mémoire de marais
  installée (patron `bancs/hydrologie.py tourbiere`), plantes de mare semées
  (aulne `Alder`, sphaigne `Sphagnum`, rossolis `Drosera`), faune de mare
  (moustique, libellule) présente dès le départ.
- Golden **intact** (le smoke ne passe pas par `build_world_full`).

### 3.5 Vue
Mare visible et lisible en grammaire SNES (eau, berges, plantes de mare), voix sous
vision vérifiées en capture, banc d'observation F5. Golden intact.

## 4. Coût perf
Recharge : 3 lerps/plot/tick (~1 200 plots) — négligeable. Facteur de nutrition :
réutilise l'empreinte racinaire déjà dérivée (pas de recalcul). Voix bête : une
grille de plus par guilde, écrite dans la boucle existante. Budget ≤ +2 % de tick.

## 5. Hors périmètre
Mort par carence chronique (D41) ; densités et comportements de la faune (D119) ;
DA générale (D118).
