# Tronçon ③ — Articulation boucle Liebig + préemption survie

> Sprint **Automate dirigé par le but** (D87). Conception :
> `docs/joueur/automate/conception_automate_but.md` (§3). Lis `CLAUDE.md` +
> `00_etat.md` + ce fichier. ① (log) et ② (`avancer_plans`) sont faits.

## Objectif

**Brancher** le planificateur (`planification.avancer_plans`, ②) dans la boucle de
décision (`boucle.jouer_tick`) : fusionner les gestes créatifs avec les plans
réactifs, en garantissant la **préemption survie** (les créatifs passent SOUS les
facteurs de survie du vivant existant), puis EXÉCUTER les gestes créatifs et TRACER
(`geste`/`geste_coupe`). Régler le **timing de `favoriser_auxiliaire`**.

## Rappel — la boucle actuelle (`tools/jardinier_auto/boucle.py`)

`jouer_tick` : (1) `_collecter` produit `plans` (réactifs) + `impasses` ; (2)
`_appliquer_part_recoltee` ; (3) tri étape 4 par `_prio` (priorité décroissante +
départage `(tile_id, y_cm, x_cm)`, avec `BONUS_OBJECTIF` pour un geste servant un
objectif) ; (4) mode payé → `separer_verrouilles` + `_couper_au_budget` ; mode libre
→ `assurer_solde_libre` ; (5) exécute + `consigner` + `incrementer`.

Les gestes réactifs sont des tuples `(cle, tile, eco, plant, Plan)`. Les gestes
CRÉATIFS n'ont pas toujours une `plant` (magazine) ni le même exécuteur.

## Fichiers à toucher

- `tools/jardinier_auto/boucle.py` — insérer l'étage créatif.
- `tools/jardinier_auto/execution.py` — mapper les verbes créatifs (`planter`,
  `acheter_magazine`, `favoriser_auxiliaire`) vers `sim.actions`/`sim.magazine`.
  Vérifie comment `executer` dispatche déjà les verbes existants.
- `tests/test_automate_determinisme.py` — étendre (le run reste déterministe).

## Modèle — insertion

Après `_collecter` et le calcul de `actifs`, appeler
`plans_creatifs, veilles = avancer_plans(engine, actifs, self.profil)`.

**Représentation homogène** : donne aux plans créatifs une clé de départage
canonique même sans `plant` — p.ex. `cle = (tile_id_ou_"~", y_cm_ou_0, x_cm_ou_0)`
pour `planter`/`favoriser_auxiliaire` (position du plot choisi), et une sentinelle
stable pour `acheter_magazine` (pas de zone). Un tuple créatif peut être
`(cle, tile|None, eco|None, plant|None, Plan)` pour rester compatible avec le tri.

**Préemption survie** : les `Plan` créatifs portent `priorite = PRIO_CREATIF` (≈5,
défini au ②), donc le tri `_prio` existant les place **après** les facteurs de
survie (10-20). NE PAS leur donner `BONUS_OBJECTIF` (ce bonus vise les gestes sur
cultivées existantes servant un objectif ; un `planter` créatif ne doit pas doubler
la survie). Résultat : advenir **ralenti**, jamais au prix du vivant.

- **Mode payé** (`paie_vigueur=True`) : `_couper_au_budget` s'applique aux créatifs
  comme au reste → si la Vigueur manque, le `planter` est **reporté** (trace
  `geste_coupe {verbe, cause:"budget"}`) et la survie, mieux priorisée, passe
  d'abord. `cout_action` connaît déjà `planter`/`favoriser_auxiliaire` (`couts.py`) ;
  `acheter_magazine` débite via `acheter_au_magazine` (COUT_MAGAZINE) — traite son
  coût AVANT exécution pour la cohérence budget (voir comment `magazine` débite).
- **Mode libre** (`paie_vigueur=False`, défaut coût-0) : rien n'est coupé, mais le
  tri par priorité **ordonne** quand même déterministement (survie avant créatif).

**Exécution + trace** : pour chaque geste créatif retenu, l'exécuter via
`execution.executer` (étendu), tracer `entree_geste` (résultat) ; si un objectif est
servi, laisser le comptage `incrementer` inchangé (mais `planter`/`acheter` ne sont
PAS le geste-cible `recolter` → ils n'incrémentent pas la progression, seul
`recolter` le fait — VÉRIFIE que `objectifs_servis` ne les compte pas par erreur).

**Timing `favoriser_auxiliaire`** (§2.4) : posé au plus tôt (dès qu'une cultivée
`fruitier` sans habitat existe — la décision est faite au ②) ; ici on l'exécute et
on le trace. One-shot garanti par la pré-condition « zone sans rondelle auxiliaire ».

**Veilles** : consigner les `veille` retournées par `avancer_plans` via le
constructeur `entree_veille` (une fois par objectif — réutilise le patron
`marquer_inatteignable_signale` d'`objectifs.py` pour ne pas noyer le log).

## Golden

**INTACT** (`57c166d8…`). L'automate reste hors tick ; le golden tourne sans
joueur/objectif → `avancer_plans` renvoie vide → no-op strict. Vérifie
`python3 -m tests.test_golden`.

## Tests

- `test_automate_determinisme.py` : un run AVEC objectif `recolter tomate` (graine
  en banque, monde jouable) reste **déterministe** (2 runs → journaux égaux — utilise
  l'oracle du ①).
- Préemption : construire un tick où une cultivée existante est en déficit hydrique
  ET un `planter` créatif est proposé, en mode payé avec budget serré → le `planter`
  est `geste_coupe:"budget"`, l'arrosage passe. En mode libre → les deux passent mais
  l'arrosage est ORDONNÉ avant (vérifier l'ordre dans le journal).
- `favoriser_auxiliaire` : posé une seule fois pour une cultivée fruitière.

## Ne PAS faire

- NE PAS donner `BONUS_OBJECTIF` aux gestes créatifs.
- NE PAS faire compter `planter`/`acheter` dans la progression de l'objectif.
- NE PAS toucher le moteur/tick. NE PAS re-figer le golden.
- NE PAS implémenter la veille/re-sonde fine (c'est ④) — ici, juste consigner les
  veilles produites par ②.

## Fin de tronçon

Golden intact + tests verts → `00_etat.md` (§REPRISE : ③ fait, planif branchée) +
commit (`feat(automate ③) : planif branchée dans la boucle + préemption survie`).
