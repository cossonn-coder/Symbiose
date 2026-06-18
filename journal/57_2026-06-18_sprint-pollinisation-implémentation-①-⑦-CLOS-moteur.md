# 2026-06-18 — Sprint POLLINISATION & CYCLE DE VIE · implémentation ①→⑦ — MOTEUR CLOS

> Conception figée : `docs/conception/CONCEPTION_POLLINISATION_CYCLE_VIE.md` (§A–§J).
> État détaillé par tronçon : `sprints/sprint_pollinisation_cycle_vie/00_etat.md`.
> Mémoire : [[design_pollinisation_cycle_vie]].

## Arc complet (7 tronçons, moteur)

**Partie I — MOTEUR (re-fige le golden, isolé) :**
- **① Floraison réelle + phénologie** (§A) — `PlantInstance.floraison`/`gdd_accum`,
  double porte GDD + photopériode + maturité. Golden NEUTRE.
- **② Registre pollinisateurs + nectar réel** (§C/§E) — `PollinatorSpec` data-driven
  (abeille/syrphe/papillon), ressource `floraison × attractivité` par famille,
  remplace le proxy stade≥2. Golden re-figé MAÎTRISÉ (`08f18502…f9b3`).
- **③ Butineurs déterministes** (§F) — `fields/foragers.py`, agents marche-gradient +
  constance florale, dépôt `pollen_recu`. Golden NEUTRE.
- **④ Nouaison pollinisée** (§B) — nouaison en fin de floraison par plante, Monod sur
  `pollen_recu` pour les `insect`, sans plancher. Golden NEUTRE.
- **⑤ Ponts de cycle de vie** (§D) — `fields/lifecycle.py`, chenille→papillon &
  syrphe_larve→syrphe ; herbivorie lit `ravageur+chenille`, syrphe_larve prédate le
  ravageur. Invariant larves=0 prouvé. Golden re-figé MAÎTRISÉ (`4f9fad91…1260`).

**Partie II — COUCHE JOUEUR (golden NEUTRE) :**
- **⑥ Ruche & miel** (§H/§I) — structure `ruche` (capture d'essaim sauvage si champ
  abeille local suffit, philo #1), miel ∝ nectar mellifère butiné, `recolter_miel`
  gaté par l'équipement apicole débloqué par MAÎTRISE (D12). Pont 0.4.0.
- **⑦ Piqûre — alarme émergente** (§J) — voir ci-dessous.

## Tronçon ⑦ (ce jour) — piqûre / alarme émergente

Décision Nico (2 questions) : **modèle CHAMP GridField transitoire** (pas événement
ponctuel) + périmètre **« moteur + hooks »** (la piqûre temps réel reste au F5 Godot,
hors VM). §J le pose lui-même : le moteur EXPOSE l'alarme + la densité, **Godot anime**
la piqûre au curseur et applique le coût Vigueur.

Part moteur livrée :
- `fields/alarme.py` NEUF (PURE, duck-typé `eco`, miroir apiculture/foragers/lifecycle) :
  `declencher_alarme` (dépôt cumulatif borné) + `tick_alarme` (décroissance ×0.5/sem,
  snap à 0 sous 0.01 → liste snapshot creuse). Aucun import `sim` → aucun cycle.
- `eco.alarme` (GridField [0,1] transient) dans `ecofields/container.py`.
- **Déclencheurs (philo #1, action directe coûteuse, punie émergemment)** :
  `ecraser` une ABEILLE (phéromone apienne — un ravageur n'en pose pas) ;
  `recolter_miel` SANS équipement (avec enfumoir = aucune). `recolter_miel` gagne un
  param `eco` optionnel ; routeur le passe.
- Câblé boucle.py étape 13f (décroissance). **PUR PUITS** : n'écrit que `eco.alarme`,
  jamais un champ figé → ne peut pas dériver le tick.
- Pont **0.4.1** : snapshot expose `alarme` = liste creuse `[[r,c,intensité],…]`. Pas
  de verbe neuf (effet de bord des verbes existants). Round-trip confirmé.

## Vérifications

- **Golden INCHANGÉ** `4f9fad91…1260` (depuis ⑤ ; ⑥ et ⑦ neutres). `population_hash`
  inchangé `71f7ddda…`.
- `tests/test_alarme.py` NEUF (16/16). Suite verte : golden, ruche 20/20, lifecycle,
  sim_server 158/158 (v0.4.1), structures 65/65, population, attraction, fruits,
  vigueur 135/135, maîtrise 35/35.
- ⚠ Garde-fou taille signalé : `container.py` ~359 (+3 code), `population.py` 363 (⑥),
  `alarme.py` ≈20 — dépassements connus et annoncés.

## Reste

**Vue Godot** (différé, hors VM, F5 Nico) : sprites chenilles/syrphes/papillons,
larves, ruche/miel, et **piqûre temps réel** au curseur (coût Vigueur + perturbation
locale §J.2). Tous les hooks sont posés au snapshot (`alarme` + densité `abeille`
0.4.1, `essaim`/`miel` 0.4.0 ; `eco.larvae` reste non exposé).
