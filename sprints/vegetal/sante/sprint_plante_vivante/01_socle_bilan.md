# ① Socle du bilan carbone — en OMBRE (golden INTACT)

Lire d'abord : `CLAUDE.md`, `00_etat.md`, `docs/vegetal/sante/conception_plante_vivante.md`
(§1-§3, en entier).

## Objectif
Calculer chaque semaine, pour chaque plante vivante, le bilan `P − E − X` et tenir les
deux états neufs `feuillage` et `reserves` — **sans qu'aucun lecteur ne s'en serve
encore**. Le moteur se comporte exactement comme avant ; on prépare et on calibre.

## À faire
1. `plants/physiologie.py` (NEUF, couche `plants`) : les 3 paramètres d'espèce
   `reserve_semaines`, `photo_max`, `cout_feuillage` (§2), défauts par forme de vie
   dérivés de l'existant (strate du stade mature `growth_stages[-1].strate`,
   `life_cycle`, `winter_strategy`, `deciduous`, `longevity()`) + table de
   surcharges par nom de classe pour les **52 espèces** (`plants/catalogue.py`).
   Chaque surcharge porte un commentaire pédagogique d'une ligne (pourquoi cette
   espèce s'écarte). Fonction `capacite_reserve(plant)` = `reserve_semaines ×
   facteur_stade` (plantule ≈ 0,05 → adulte 1, monotone sur l'index de stade ;
   à choisir et justifier).
2. `PlantInstance` (`plants/base/instance.py`) : champs `feuillage: float = 1.0`,
   `reserves: float = 1.0` (fraction de la capacité), + `bilan_net: float = 0.0`
   (dernier solde, pour bancs/pont). **Ne PAS les ajouter à `_PLANT_ATTRS` du
   golden** (`tests/test_golden.py`).
3. Calcul du bilan (§1) dans la passe physiologique hebdomadaire
   `_update_physiology` (`sim/engine/croissance.py`, ~l. 296-495), qui calcule déjà
   `light_eff`, `facteur_nutrition`, `_f_croissance_allelo` : **réutiliser ces
   valeurs**, ne pas les recalculer (règle « pas de recalcul dans un tick »).
   `f_eau` (rampe sur `eau_percue` vs `0,15/tolerance_secheresse` et `HUM_NOYE`),
   `f_T` (rampe sur `temp_min_growth` → optimum → `lim_chaud`/`t_feuille`,
   plage D139), entretien Q10 = 2 avec facteur de dormance (hiver, `winter_strategy`),
   présence phénologique du feuillage (caduc défeuillé = 0 de production, 1 de
   `feuillage`). Mettre la logique pure dans un module `sim/bilan.py` (couche `sim`,
   fonctions pures testables) appelé depuis `_update_physiology`.
   Mise à jour de `reserves` / refeuillaison selon §1 — **en ombre** : les valeurs
   évoluent mais rien ne les lit.
4. Banc de calibration `tests/test_bilan.py` (+ éventuel script de mesure sous
   `sprints/vegetal/sante/sprint_plante_vivante/mesures/`) :
   - chaque espèce du monde `full` (`sim/monde_complet.py` PLACEMENTS) à sa niche en
     été : `bilan_net > 0` ;
   - plantule héliophile sous ombre dense : `bilan_net < 0` ;
   - chêne adulte défeuillé à 100 % en juin, réserves pleines : survit ≥ 20 semaines
     en simulation de bilan isolée ; semis défeuillé : réserves vides en ≤ 3 semaines ;
   - caduc en hiver : réserves qui baissent lentement (≤ 30 % de C sur l'hiver).
   Consigner la table des `bilan_net` par espèce dans `00_etat.md` (acquis du ①).

## Golden
**INTACT** (aucun lecteur, aucune ligne de log neuve, champs hors digest). Vérifier
`python3 -m tests.test_golden` + suites `tests/` vertes. Si le golden bouge, c'est
qu'un lecteur a été branché par erreur → annuler.

## Ne PAS faire
- Toucher `vitalite`, `erode`, `can_grow`, `growth_factor`, l'herbivorie (②/③).
- Créer un gène (anti-doublon : les tolérances existent).
- Lancer `test_epaisseur_500ans` (interdit).
- Taille : `sim/engine/croissance.py` est à surveiller (`tools/compte_ldc.py`) —
  la logique va dans `sim/bilan.py`, croissance n'a que l'appel.

## Perf
Un calcul scalaire par plante : mesurer le tick monde `full` s10-s30 avant/après
(3 paires alternées, charge VM via `uptime`) ; ≤ +5 %.
