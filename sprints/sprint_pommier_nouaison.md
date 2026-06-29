# Sprint POMMIER NOUAISON — kickoff autosuffisant

> Sprint **d'investigation + correction** d'un bug pré-existant. Petit a priori
> (1 chaîne, moteur Python), mais la cause est à diagnostiquer avant de coder.
> Repars à froid : tout le contexte nécessaire est ci-dessous.

## Symptôme exact (reproductible)

La suite du pont a **un check rouge** stable :

```
❌ le pommier pré-âgé a noué des fruits réels (fin de floraison) — 0 fruits @ S52
[test_sim_server] FAIL — 205/206 checks verts
```

Reproduire (depuis `data/code/`) :
```
python3 -m tests.test_sim_server      # 205/206, la rouge = pommier pré-âgé
```
Le test fautif : `tests/simserver/morts.py::test_pommier_fruite` (≈ L88-120).
Il fait `init seed=42 config="full"` (la config **full** pré-vieillit le pommier
à `maturity_years` pour qu'il fleurisse **dès l'an 1** au lieu de l'an 6), puis
avance semaine par semaine jusqu'à S52 et attend `len(pommier["fruits"]) > 0`.
Aujourd'hui : **0 fruit à S52** → la chaîne floraison→pollinisation→nouaison ne
produit aucun fruit dans l'année 1.

## Historique (NE PAS perdre de temps à re-chercher)

- Le check était **vert** à l'origine (levier démo « vue·rattrapage 02 »).
- Il est devenu **rouge** au **sprint THERMIQUE & MICROCLIMAT (2026-06-18)** :
  hypothèse consignée à l'époque = le re-figeage LARGE de la météo (seed 42
  décalée) a déplacé la fenêtre de floraison/pollinisation.
- Il est resté rouge au travers des sprints suivants (catalogue enrichi,
  physico-chimie, plasticité, voix narratives) et du **sprint météo→champs
  (2026-06-29)** qui a encore bougé l'humidité. **Donc le bug n'est pas dans ces
  sprints** — c'est une **régression de calibration/timing** dormante depuis la
  thermique. Le sprint météo→champs ne l'a NI causé NI aggravé (vérifié : déjà
  rouge sur la baseline `f7811b5`).

## La chaîne en jeu (où regarder)

La nouaison entomophile du pommier passe par 3 maillons. Le bug est dans **un**
d'entre eux — instrumenter pour trouver lequel casse :

1. **Floraison** — le pommier doit voir sa `floraison` franchir `SEUIL_FLEURI=0.5`
   PUIS retomber sous `SEUIL_NOUAISON=0.2` (front descendant = fin de floraison).
   La `floraison` est pilotée par une **double porte** : accumulation GDD
   (`gdd_accum`, `T_BASE_FLORAISON`) **ET** photopériode (`bloom_daylen_min/max`
   de l'espèce). Vérifier : *le pommier full atteint-il seulement `SEUIL_FLEURI`
   avant S52 ?* Si le froid de la météo seed 42 ralentit le GDD, la floraison peut
   ne jamais s'armer dans l'année.
2. **Pollinisation** — entomophile → `plant.pollen_recu` doit être alimenté par
   les **butineurs** (`sim/engine/butineurs.py`, `fields/foragers.py`,
   `eco.foragers`). La fraction nouée = Monod `pollen/(pollen+POLLEN_DEMI)` **sans
   plancher** (0 butineur → 0 fruit). Vérifier : *le pommier reçoit-il du pollen
   pendant sa floraison ?* (butineurs absents/hors fenêtre = nouaison nulle.)
3. **Nouaison** — `sim/engine/decompo.py::_tick_fruits` (≈ L92-130) : déclenchée
   en fin de floraison (front `a_fleuri` armé ≥ `SEUIL_FLEURI`, noué < `SEUIL_NOUAISON`)
   **ET** gate `age_years >= maturity_years`. Vérifier : *le pré-vieillissement de
   la config full pose-t-il bien `age_years >= maturity_years` (=5 pour AppleTree) ?*
   Si le pré-âge a glissé sous le seuil, le gate bloque tout.

Fichiers clés : `tests/simserver/morts.py` (test) · le code d'init de la config
**full** (pré-vieillissement du pommier — `tools/sim_server.py` / `cmd_init`) ·
`sim/engine/decompo.py` (`_tick_fruits`) · le tick de floraison (GDD+photopériode) ·
`sim/engine/butineurs.py` + `fields/foragers.py` (pollen) · la fiche AppleTree au
catalogue (`maturity_years`, `bloom_daylen_*`, trait mellifère/attractivité).

## Démarche suggérée (investigation AVANT correction)

1. **Instrumenter** un run `seed=42 config="full"` : logguer chaque semaine, pour
   le pommier full, `age_years`, `gdd_accum`, `floraison`, `a_fleuri`,
   `pollen_recu`. Repérer le maillon qui ne s'active jamais avant S52.
2. **Conclure** quel maillon casse, et pourquoi (le diagnostic dicte le correctif).
3. **Corriger au bon endroit** :
   - Si c'est la **floraison qui ne s'arme pas** (GDD trop lent sous la météo
     seed 42) → arbitrer avec Nico : ajuster un **knob de calibration** de la
     fenêtre de floraison du pommier, OU adapter le test (le pommier full ne
     fleurit peut-être réellement pas en an 1 avec ce climat — le test serait
     alors trop optimiste). **Décision de design = remonter à Nico**, ne pas
     trancher seul.
   - Si c'est le **pré-âge** (gate maturity raté) → corriger le pré-vieillissement
     de la config full (bug franc, pas de re-figeage attendu).
   - Si ce sont les **butineurs absents** → vérifier la fenêtre/présence des
     pollinisateurs sur le jardin full pendant la floraison.
4. **NE PAS** simplement supprimer/relâcher le check sans comprendre : c'est un
   garde-fou de la chaîne floraison→pollinisation→nouaison (Partie A vivante).

## Critères de succès

- `python3 -m tests.test_sim_server` → **206/206** (le pommier pré-âgé noue ≥ 1
  fruit avant/à S52), **OU** décision explicite de Nico que le test doit être
  réécrit (le pommier full ne fleurit pas en an 1 sous ce climat) — dans ce cas,
  ajuster le test avec sa justification.
- **Golden préservé** : ce sprint NE doit pas re-figer le golden. Si une
  correction touche un knob de calibration qui dérive le golden, c'est un
  **re-figeage maîtrisé et ANNONCÉ** (dérive localisée + expliquée) — à valider
  avec Nico, jamais aveugle. Re-figeage : `python3 -m tests.test_golden --capture`
  (+ population si elle bouge), consigner le nouveau hash + la raison.
- Lancer aussi `python3 -m tests.test_fruits` (chaîne de nouaison) et
  `python3 -m tests.test_biennial` (intact).

## Garde-fous projet (rappel)

- Source de vérité = Python `data/code/`, lancement depuis `data/code/`.
- Déterminisme (philo #3) : **aucun RNG neuf**. Philo #2 : flux → contrainte →
  réponse, jamais de bonus/malus direct sur la plante.
- Un fichier = une responsabilité, ~350 lignes de code pur max, français +
  commentaires pédagogiques au cœur des fichiers.
- **Décision de design → remonter à Nico** (ce sprint a un point d'arbitrage
  probable : « calibrer la floraison » vs « corriger le test »).
- Pas de C# (le rendu n'est pas concerné). Le pont n'a pas à bouger.
- Clôture : MAJ `journal.md` (index) + entrée `journal/NN_…`, retirer la mention
  « pré-existant » de la dette une fois le check vert.

## Reprise

« lis `sprints/sprint_pommier_nouaison.md` » → investiguer, diagnostiquer,
corriger (ou remonter l'arbitrage), garder le golden, viser 206/206.
