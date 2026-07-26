# ③ Pluie de graines, nappe de berge, corridor de lisière

> Sprint **PÉRIPHÉRIE** (D73). Lis d'abord `CLAUDE.md` + `00_etat.md` + ①/②.
> Spec : `docs/champs/peripherie/conception_peripherie.md` §4.2, §3.4.
>
> **Golden attendu : INCHANGÉ.** Interdiction de re-figer.

## Objectif

Les trois flux entrants restants : la matrice comme **réservoir de vivant** (graines,
faune) et comme **soutien hydrique** (berge). Après ce tronçon, la périphérie agit
pleinement sur le jardin et les gestes du ④ auront de quoi mordre.

## A. Pluie de graines — le canal d'acquisition #3 enfin porté

**Point de greffe** : `data/code/fields/seedbank.py`, sur le patron **exact** de
`tick_late_succession_enrichment(om_index_field)` (ligne 244) — lis-le avant d'écrire.

`tick_apport_peripherie(ceinture)` : chaque secteur sème dans les plots **du bord
correspondant**, avec **décroissance de la distance au bord** (portée ~4 plots = 2 m,
au-delà : rien — inutile de balayer la grille).

| Type de secteur | Archétype semé | Intensité |
|---|---|---|
| `friche` | `pioneer` | forte — c'est la friche périphérique |
| `foret` | `competitor` | ∝ `densite_ligneuse` |
| `prairie` | `grass` | modérée |
| `riviere` / `falaise` | — | rien |

C'est le support mécanique qui manquait au **canal d'acquisition #3 (friche
périphérique)** : jusqu'ici la friche était une intention sans code.

⚠️ `ceinture=None` ⇒ **la méthode n'est pas appelée** ⇒ banque de graines inchangée.

## B. Nappe de berge — condition aux limites

**Lis §3.4 de la conception avant de coder.** L'amorce initiale supposait qu'on pouvait
appliquer « la même physique hydraulique hors terrain de jeu » : **c'est faux**,
`altitude` et `eau_surface` s'arrêtent au bord du jardin, il n'existe aucune grille
au-delà. Simuler un cours d'eau serait un second système pour un bénéfice nul.

Modèle retenu : un secteur `riviere` porte `ligne_eau` (cm, relatif au bord). À chaque
tick d'hydrologie, il **pousse** de l'eau dans les plots de la première rangée du bord
(si `ligne_eau > 0`) ou **en retire** (si `< 0`), avec décroissance sur ~3 plots.

Greffe dans `fields/ecofields/hydrologie.py` / `ruissellement.py` — **en amont** du
double-buffer existant, jamais en concurrence avec lui. Le ruissellement et
`marais_memory` déjà en place produisent ensuite la zone gorgée puis le marécage : rien
n'est scripté, tout émerge (#2).

## C. Corridor de lisière — `eco.lisiere` (attention, c'est ici que #2 se joue)

**Le raisonnement complet est au §4.2 de la conception ; ne l'improvise pas.** Résumé :

Le champ de population **colonise déjà depuis zéro** partout où ressource + habitat
existent (`fields/population/field.py`) — il n'y a aucune barrière de dispersion à
lever. Écrire « la périphérie augmente l'habitat » serait donc un **bonus déguisé**,
interdit par #2.

La formulation juste : la lisière **est** un habitat — c'est de l'écologie, pas une
faveur. On l'exprime comme un **champ du milieu**, que chaque guilde lit **à sa
manière** :

1. `eco.lisiere` — `GridField` ∈ [0,1], créé **lazy** (patron `eco.vent` / `eco.givre`,
   `fields/ecofields/container.py:380-395`). Gradient décroissant depuis chaque bord,
   porté par le type de secteur : `foret`/`friche` fort, `prairie` faible,
   `riviere` moyen (berge), `falaise` faible.
   **Statique** tant que la ceinture ne change pas → calculé une fois, mémoïsé sur une
   signature (le projet interdit de recalculer dans un tick ce qui l'a déjà été).
2. `TrophicSpec.lisiere_w: float = 0.0` — nouveau champ, **défaut 0.0**
   (`fields/population/spec.py`, patron `signal_fn`/`habitat_w`). Il entre dans le calcul
   de `capacite` dans `field.py::tick`.
3. Dans `fields/population/registry.py`, ne renseigne un poids **que** pour les guildes
   que la lisière concerne réellement : carabes, syrphes, oiseaux, hérisson, auxiliaires
   d'hivernage. **Pas** les pucerons, pas les ravageurs de culture.

À `lisiere_w = 0.0` partout + `eco.lisiere` absent ⇒ `capacite` **strictement
inchangée** ⇒ golden intact.

## Tests

Étendre `tests/test_peripherie.py` :

1. **Neutralité** — sans ceinture : seedbank, hydrologie et populations bit-identiques.
2. **Graines** — secteur `friche` au nord ⇒ `pioneer` croît sur la rangée nord,
   **décroît avec la distance**, nul au-delà de la portée. Bord sud intact.
3. **Berge** — `ligne_eau > 0` ⇒ `humidite`/`eau_surface` montent sur la rangée du bord ;
   `< 0` ⇒ baissent. Après plusieurs ticks avec `ligne_eau` fort, `est_marais()` finit
   par répondre vrai près du bord (émergence, pas script).
4. **Corridor** — une guilde à `lisiere_w > 0` gagne en capacité près d'une lisière
   forestière ; une guilde à `lisiere_w = 0.0` est **inchangée au bit près**.

## Golden

`python3 -m tests.test_golden` → **INCHANGÉ**.

## Ce qu'il NE faut PAS faire

- **N'ajoute pas de terme d'habitat conditionnel** du type
  `if secteur.type == "foret": hab += 0.2` — c'est le bonus direct que #2 interdit.
  Le milieu porte l'information, la guilde y répond via son poids déclaré.
- **Ne simule pas de rivière hors grille** : condition aux limites, point.
- **Ne balaie pas toute la grille** pour un effet de bord : portée bornée, scatter depuis
  le bord (réflexe D32).
- **Ne recalcule pas `eco.lisiere` à chaque tick** s'il n'a pas changé.
- **N'exécute JAMAIS** `test_epaisseur_500ans`.
