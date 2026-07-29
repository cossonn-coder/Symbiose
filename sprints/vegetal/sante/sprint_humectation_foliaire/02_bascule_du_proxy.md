# ② Bascule du proxy — la pression fongique cesse de suivre l'humidité du SOL

**Sprint** : `sprint_humectation_foliaire`
**Golden attendu : RE-FIGÉ — MAÎTRISÉ ET ANNONCÉ** (le seul du sprint)
**Conception** : `docs/vegetal/sante/conception_humectation_foliaire.md` §1.4, §2.3
**Prérequis** : ① livré (`wetness_memory` vit et est alimentée).

## Objectif

C'est **le cœur du sprint**. Deux sites du moteur utilisent aujourd'hui l'humidité du
**SOL** comme proxy de l'humectation du **FEUILLAGE**. On les bascule sur
`wetness_memory`.

### Pourquoi c'est un bug de conception, pas un raffinement

`arroser` (`sim/actions/gestes.py:188`) n'écrit que `eco.humidite`. Donc aujourd'hui :

> `arroser` → `humidite` ↑ → `hum_norm` ↑ → **maladie fongique ↑**

Le joueur qui sauve une plante de la sécheresse **la rend malade**, par un chemin
biologiquement faux : arroser au pied ne mouille pas le feuillage et n'ouvre pas la
porte au mildiou. Le modèle enseigne **l'inverse** de la règle permacole (« arrose au
pied, jamais sur les feuilles ») → violation dormante de **philo #6**.

## Fichiers à toucher

1. `data/code/sim/effects/perturbations.py` — `fungal_disease` (~ligne 209, 216)
2. `data/code/sim/engine/croissance.py` — `infection_memory` (~ligne 316-317)

## Site 1 — `fungal_disease` (`perturbations.py`)

Aujourd'hui (lignes 209 et 216) :

```python
hum_norm = min(1.0, eco.humidite.at_plot(r, c) / 3.0)
...
p *= hum_norm * (0.4 + density) * susc
```

Cible :

```python
# HUMECTATION FOLIAIRE (sprint humectation ②) : le vrai signal de germination des
# spores est l'eau LIQUIDE posée sur la feuille pendant des heures, pas l'humidité
# du SOL. On lisait `humidite/3` — un proxy faux qui faisait monter la maladie quand
# le joueur arrosait AU PIED (l'inverse de la règle permacole, philo #6).
wet = plant.wetness_memory
...
p *= wet * (0.4 + density) * susc
```

⚠️ **Conserver `FUNGAL_VENT_DRY` et `_spore_load`** (lignes 218-221) tels quels. Le vent
joue désormais à **deux** niveaux — il sèche le feuillage (dans `wetness_memory`, ①) *et*
il garde son assèchement direct ici. C'est un léger double comptage du vent, **assumé** :
il renforce la lisibilité du levier d'aération, et ces deux coefficients sont des
placeholders que le ⑥ calibrera ensemble.

## Site 2 — `infection_memory` (`croissance.py:316-317`)

Aujourd'hui :

```python
infection_sig = ((eco.disease_probability(r, c, INFECTION_BASE) / INFECTION_BASE)
                 * min(1.0, hum / 3.0))
```

Cible — même correction (`min(1.0, hum/3.0)` → `plant.wetness_memory`) :

```python
# Pression pathogène VÉCUE = manque de protection du sol × HUMECTATION du feuillage
# (② : c'était `hum/3`, l'humidité du SOL — même proxy faux que fungal_disease).
infection_sig = ((eco.disease_probability(r, c, INFECTION_BASE) / INFECTION_BASE)
                 * plant.wetness_memory)
```

Ce site alimente par plasticité le gène `resistance_pathogene` : la cohérence des deux
sites est nécessaire, sinon la plante s'endurcirait contre un signal qu'elle ne subit
plus. **Ordre à respecter dans `_update_physiology`** : `wetness_memory` doit être mise à
jour **AVANT** `infection_memory` (au ① elle est écrite en fin de boucle → **la déplacer
avant le bloc `infection_memory`**). Sinon `infection_memory` lit la valeur du tick
précédent — décalage silencieux d'un tick.

## Golden — RE-FIGEAGE ANNONCÉ

**Le golden VA bouger, c'est voulu et inévitable** : on corrige un proxy faux, donc le
comportement change par construction.

**Dérive attendue, à vérifier et à expliquer dans `00_etat.md`** :

- La pression fongique **baisse globalement** sur le smoke. Raison : `hum_norm` valait
  typiquement 0.2-0.5 en régime courant (humidité de sol ~0.6-1.5 sur 3.0), tandis que
  `wetness_memory` ne monte qu'en présence de rosée/pluie **et** de faible séchage — donc
  souvent plus bas, et nul par temps venté ou ciel clair.
- Cascade possible : moins d'événements `ReduceHealth(reason="maladie fongique")` →
  plantes en meilleure santé → croissance/sénescence décalées. `infection_memory` plus
  basse → `resistance_pathogene` moins exprimé (cohérent : moins de pression subie).

**Attendu : la dérive doit être LOCALISÉE à la santé/maladie et à ses conséquences.**
Si tu observes une dérive sur l'hydrologie, les nutriments ou l'épaisseur du sol, ce
n'est **pas** ce tronçon : cherche l'erreur avant de re-figer.

**Procédure** :
1. Lance `python3 -m tests.test_golden`, note le nouveau hash.
2. **Explique la dérive** (quelles plantes, quelles semaines, quel sens) dans
   `00_etat.md` — un hash sans explication est un re-figeage non maîtrisé, refusé.
3. Re-fige le hash dans `tests/test_golden.py` et consigne l'ancien.
4. Lance les 11 suites ciblées ; `test_senescence` et les suites de santé peuvent
   demander un ajustement — **si une suite casse, comprends pourquoi avant de la
   toucher**.

## Ce qu'il ne faut PAS faire

- ❌ Toucher `disease_probability` (`fields/ecofields/sol.py:118`) — il reste le point de
  greffe unique (D10), microbiome + inoculum familial, **sans** terme d'humectation.
- ❌ Retirer `FUNGAL_VENT_DRY` ou `_spore_load` (double comptage du vent assumé).
- ❌ Toucher `tick_hydrology` (§1.2, D39).
- ❌ Introduire la guilde oïdium (c'est le ④).
- ❌ Ajouter un mode feuillage à `arroser` (c'est le ③).
- ❌ Re-figer un hash sans avoir expliqué la dérive.
- ❌ Lancer `test_epaisseur_500ans` (interdit).

## Vérification

1. Golden re-figé **avec explication écrite**.
2. Étends `tests/test_humectation.py` : (a) à `wetness_memory = 0`, `fungal_disease` ne
   déclenche **jamais** (le facteur est nul) ; (b) arroser au pied (`eco.humidite` seule)
   ne change **plus** la pression fongique — **c'est le test de non-régression du bug
   pédagogique**, il doit exister ; (c) `infection_memory` suit l'humectation, pas
   l'humidité du sol.
3. `python3 tools/compte_ldc.py` sur les deux fichiers.
