# Tronçon ① — Champ `InoculumField` + alimentation + décroissance (DORMANT)

> Kickoff autosuffisant. Lis d'abord `CLAUDE.md` (racine) + `00_etat.md` (ce
> dossier) + `docs/champs/sol/conception_memoire_inoculum.md` (§1, §2, §3, §7).
> Source de vérité = Python `data/code/`. Lancement depuis `data/code/`.

## Objectif
Créer le champ de mémoire d'inoculum, l'alimenter (2 canaux conséquence) et le
faire décroître — mais **RIEN ne le lit** dans la math du tick à ce stade
(dormant, patron D31.1). Le tick produit exactement les mêmes sorties.

## Golden ATTENDU : **INTACT**
Aucune sortie de tick ne dépend de l'inoculum au ①. Vérifie
`python3 -m tests.test_golden` inchangé. Si le golden bouge, tu as par erreur
branché l'inoculum sur une voie lue → reviens en arrière.

## À implémenter
1. **Champ** — nouveau module `fields/ecofields/inoculum.py` (ou mixin, aligne-toi
   sur la structure des autres champs du paquet ; `EcoFields` est assemblé dans
   `fields/ecofields/container.py:52`). Modèle §1 :
   - stockage sparse `dict[(r,c)] -> dict[famille -> float]` ;
   - `at(r,c,famille)->float` (défaut 0.0), `total(r,c)->float`,
     `deposit(r,c,famille,q)`, `tick_decay(...)` ;
   - constantes dans `fields/ecofields/constants.py` : `INOC_MAX`, `INOC_EPSILON`,
     `INOC_DECAY`, `INOC_MICRO_SUPPRESS`, `INOC_DEPOT_SEUIL`, `INOC_FROM_MEMORY`,
     `INOC_FROM_DEATH` (placeholders §10, commentés « calage F5 »).
   - `EcoFields` détient une instance `self.inoculum`.
2. **Canal 1 (dépôt continu)** — §2. Dans la passe par-plante déjà existante des
   effets/perturbations (celle qui itère les plantes vivantes ; NE crée PAS de
   nouvelle boucle spatiale), pour toute plante avec `infection_memory >
   INOC_DEPOT_SEUIL` : `eco.inoculum.deposit(r, c, plant.family,
   INOC_FROM_MEMORY*(infection_memory-INOC_DEPOT_SEUIL))`. Trouve le bon point de
   greffe (là où `infection_memory` et la position sont déjà en main).
3. **Canal 2 (pulse mort)** — §2. Sur la voie `deposer_mort`/nécromasse
   (`sim/effects/perturbations.py`), si la plante qui meurt a
   `infection_memory > 0` : dépose `INOC_FROM_DEATH*infection_memory` dans son
   bucket famille AVANT de perdre la référence.
4. **Décroissance** — `tick_decay` appelé une fois/tick (à placer près des autres
   `tick_*` de champs dans la boucle, `sim/engine/boucle.py` ; ordre sans
   importance puisque personne ne lit encore). Formule §3 (décroissance ×DECAY −
   microbiome, clamp 0, purge < EPSILON).

## Ce qu'il NE faut PAS faire
- NE PAS toucher `disease_probability` (c'est le ②).
- NE PAS re-dériver l'inoculum de la densité/humidité (c'est justement ce qu'on
  rejette, §5 — source = conséquence uniquement).
- NE PAS exposer au snapshot ni au rendu (c'est le ④).

## Verrou de test
Nouveau `tests/test_inoculum.py` : (a) dépôt monte le bucket de la BONNE famille ;
(b) `tick_decay` décroît et le microbiome accélère la baisse ; (c) bucket <
EPSILON purgé (sparse) ; (d) un plot jamais infecté reste à 0 pour toute famille.
Plus : `test_golden` INCHANGÉ (assert du hash courant).

## À la fin
Mets à jour `00_etat.md` (§REPRISE → tronçon ②), garde le hash golden constaté.
