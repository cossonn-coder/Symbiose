# CONCEPTION — SOL · Épaisseur visible (litière → humus → relief)

> Conception figée le 2026-07-02 (dette D57, F5 S5+S11). Voisines partageant les
> champs `om_*` : `CONCEPTION_DECOMPOSITION_COMPOST.md`,
> `CONCEPTION_SOL_STRUCTURE.md`, `CONCEPTION_SOL_NUTRIMENTS_NPK.md`.
> Sprint d'exécution : `sprints/sprint_epaisseur_sol/`.

## 0. Objectif & intuition

Le sol doit **se voir monter et descendre**. La matière organique qui tombe
(litière d'automne, taille, mort d'une plante) **épaissit** le sol d'un coup —
une couche fraîche foisonne. Puis elle **se tasse** en vieillissant, la décompo
la **mange**, et il ne reste durablement que l'**humus stable** qui **s'accumule
au fil des ans**. Sur des décennies, un jardin bien mené voit son sol **monter**
d'un relief visible ; un jardin épuisé le voit s'affaisser jusqu'au plancher
minéral.

Ce n'est pas qu'un effet cosmétique : un sol épais est un sol qui **tamponne**
(plus de réserve d'eau utile, plus de stock de nutriments accessible). L'épaisseur
est donc un **champ à effet écologique**, pas une simple dérivée d'affichage.

Philosophie : **#2** (l'épaisseur module des **flux du sol** — rétention d'eau,
accès NPK — jamais un bonus direct sur la plante ; la plante répond via son bilan
hydrique et son uptake) ; **#3** déterministe (aucun RNG) ; **#4** run éternel
(le sol porte la mémoire et grandit) ; **#5** pas de chiffre HUD (le joueur lit
l'épaisseur au **relief** de la tuile) ; **#7** hétérogénéité (fond `om_stable`
hérité déjà hétérogène, D56).

## 1. État de départ (source de vérité, vérifié dans le code)

| Brique | Où | Rôle |
|---|---|---|
| `litiere[r][c]` = liste de `Parcelle` typées, `age_sem` tracé | `fields/ecofields/matiere_organique.py` | couche fraîche, foisonne, décompose vite |
| `om_fresh_at(r,c)` = Σ masses des parcelles | idem | proxy masse fraîche |
| `om_active` GridField, `OM_ACTIVE_DECAY=0.018`/sem | idem | MO en décompo (mois) |
| `om_stable` GridField, `OM_STABLE_DECAY=0.0006`/sem, init `0.15` hétérogène | idem (+ D56) | **humus persistant** (décennies) |
| Cascade fresh→active→stable, minéralise NPK + respire | `tick_decomposition` | perte de masse à chaque étape |
| Patron **dérivé non stocké** `_OmIndexField`, `vitalite`, `fertilite_index` | `fields/ecofields/sol.py` | modèle d'index dérivé |
| `cec_norm_at(soil_type, om_stable_norm)` | `fields/ecofields/nutriments.py` | rétention modulée texture + humus |
| Rétention hydrique `h += soil_memory·SOIL_RETENTION` (avant drainage) | `fields/ecofields/hydrologie.py:109` | **point de greffe eau** |
| Snapshot grille 2D par tuile (`temperature.t_sol`), liste creuse `litiere` | `tools/simserver/serialize.py:255` | **patron d'exposition** |
| Rendu sol = 1 losange `Polygon2D`/`Sprite2D` PLAT par plot, bâti une fois ; maison extrudée `PxPerCmZ=0.39 px/cm` | `world/WorldView.Monde.cs` (`BuildGround`/`BuildHouse`) | **base du relief** |
| `ENGINE_VERSION="0.5.13"` | `tools/simserver/version.py` | à bumper (save + pont) |

Ordre de tick vérifié : météo → lumière → **hydrologie (3)** → **décompo (4)** →
structures → pH → structure → **mycélium** → diffusion → … → **populations**
(`sim/engine/boucle.py`). Tous les **consommateurs de MO** (décompo, mycélium,
faune) tournent **après** l'hydrologie.

## 2. Modèle — un champ stocké à relaxation

L'épaisseur est un **`GridField` STOCKÉ** (état propre, sauvegardé), **pas** une
fonction instantanée des `om_*`. Sa dynamique = **relaxation vers une cible
bulk-density**, avec inertie asymétrique.

### 2.1 Cible (densité apparente)

```
cible(r,c) = E_fresh · om_fresh_eff(r,c)
           + E_active · om_active(r,c)
           + E_stable · om_stable(r,c)
```

avec `E_fresh > E_active > E_stable` (foisonnement décroissant : la litière
fraîche est aérée, l'humus est dense). Coefs = **placeholders calibrés au F5**.

`om_fresh_eff` = masse fraîche pondérée par un **foisonnement décroissant avec
l'âge** de chaque parcelle (`Parcelle.age_sem`, déjà tracé) : une parcelle jeune
foisonne à plein, une vieille est **plaquée**. C'est ici qu'est encapsulé le
**tassement de la litière** — l'épaisseur baisse par vieillissement **même sans
décomposition**.

### 2.2 Loi de relaxation (le seul état stocké = l'inertie)

```
epaisseur(r,c) += (cible − epaisseur) · taux_asym − EPAISSEUR_EROSION
```

- `taux_asym` **asymétrique** : **montée rapide** (un dépôt se voit presque tout
  de suite) / **descente lente** (le sol se tasse avec retard → « monte à
  l'automne, se tasse tout l'hiver »). Cette **inertie EST l'état stocké** qui
  justifie D5 (l'épaisseur n'est pas la cible instantanée, elle la poursuit).
- `EPAISSEUR_EROSION` = petit terme de **voies naturelles** (érosion/lessivage de
  surface) : le sol diminue **même sans acteur**, borné pour ne jamais passer
  sous le plancher minéral (epaisseur ≥ 0).

### 2.3 Gains et pertes — tous ÉMERGENTS, aucun couplage direct plante

| Flux | D'où il vient | Mécanisme |
|---|---|---|
| **Gain dépôt** | nouvelles `Parcelle` (chute, taille, mort) | `om_fresh` ↑ → cible ↑ → épaisseur monte vite |
| **Gain humification** | cascade active→stable | `om_stable` ↑ (lent) → plancher qui **monte sur les ans** |
| **Perte tassement litière** | `Parcelle.age_sem` | foisonnement ↓ dans `om_fresh_eff` → cible ↓ |
| **Perte consommation** | faune D31, mycélium saprophyte, minéralisation | ces flux baissent DÉJÀ `om_*` → cible ↓ → épaisseur suit |
| **Perte voies naturelles** | érosion/lessivage | `EPAISSEUR_EROSION` baseline |

Décision **plantes = SOURCE seulement** : elles déposent litière + exsudats mais
n'ingèrent pas la MO (biologiquement correct). Le **priming rhizosphérique**
(racines qui accélèrent la décompo locale) est **reporté en dette** (subtil, à
concevoir séparément). Les **puits** sont donc les **décomposeurs uniquement** :
faune du sol, mycélium saprophyte, minéralisation microbienne, tassement,
érosion.

**Anti-double-comptage** : l'épaisseur ne retire jamais de masse elle-même — elle
**suit** la cible dérivée des `om_*`, qui sont mis à jour par les vrais flux
(décompo, faune…). Le seul flux propre au champ épaisseur est l'érosion baseline.

### 2.4 Placement dans le tick

Le tick d'épaisseur (`tick_epaisseur`) se place **après tous les consommateurs de
MO** de la semaine (décompo, mycélium, populations) → la cible reflète la
consommation du tick. L'**hydrologie (étape 3)** lit l'épaisseur de la **semaine
précédente** : décalage d'un tick **uniforme et déterministe** (même patron que
la structure lue par l'hydro). Aucun RNG, golden reproductible.

## 3. Effets écologiques (tronçon ①b)

Deux canaux, tous deux **émergents** (philo #2), tous deux **modulés par la
composition** du sol (réutilisent le patron `cec_norm_at`) :

### 3.1 Rétention d'eau

Greffe dans `tick_hydrology`, juste après la ligne de rétention existante
(`hydrologie.py:109`), **avant le drainage** :

```
h += epaisseur_norm(r,c) · EPAISSEUR_RETENTION · f_composition(soil_type, om_n)
```

Un sol épais = plus grande **réserve utile** = tamponne la sécheresse. `f_composition`
(dérivé de `cec_norm_at`) fait que **l'apport MO compte plus sur sable** (pauvre,
drainant) que sur **argile** (déjà rétentrice) — hétérogénéité #7. La plante
répond via son **bilan hydrique / drought_memory**, jamais par un bonus direct.

### 3.2 Accès NPK

Le **volume de stock de nutriments accessible** croît avec l'épaisseur : un sol
épais met à disposition une plus grande fraction du stock à l'uptake racinaire.
⚠️ **Croise D41** (sol déjà affamé, uptake > minéralisation) — à **border** pour
ne **pas masquer ni aggraver** D41 : effet **plafonné**, calibrage F5, test 500
ans pour vérifier qu'aucune boucle litière→eau→croissance→litière ne s'emballe et
qu'on n'annule pas la famine édaphique voulue.

Le revers **asphyxie** (D39, sol gorgé d'eau) n'est **pas bridé** : conséquence
émergente assumée. Borne anti-emballement uniquement.

## 4. Rendu (tronçon ②, pur-vue)

- **Relief extrudé** : chaque losange de sol reçoit un **flanc iso** sous lui
  (patron `BuildHouse`, `PxPerCmZ`), le dessus décalé de `epaisseur_px`. Le sol
  n'est plus plat : il a une **hauteur** par plot.
- **Mise à jour par snapshot** : contrairement à `BuildGround` (bâti une fois),
  le relief doit **suivre le snapshot** (l'épaisseur évolue chaque semaine). À
  arbitrer côté vue : reconstruire les flancs par snapshot, ou moduler un
  paramètre.
- **Exposition snapshot** : grille 2D par tuile `epaisseur[r][c]`, patron
  `temperature.t_sol` (`serialize.py`), re-bump `ENGINE_VERSION`.
- **Recalage des objets posés** : plantes, litière, macro-vie, structures sont
  posés sur le sol → leur ancrage vertical doit **remonter de `epaisseur_px`**.
  Point **F5** délicat (probablement l'essentiel du travail visuel).

## 5. Couplages dette

- **D40** (vitesse de décompo) module la dynamique (cible ↓ plus vite si décompo rapide).
- **D31** (faune) = puits principal de consommation.
- **D41** (famine édaphique) = à **border** pour l'accès NPK (§3.2).
- **D50** (litière typée) = source du foisonnement par tissu.
- **D39** (asphyxie) = revers non bridé de la rétention.
- **D56** (fond `om_stable` hétérogène) = plancher d'épaisseur hétérogène.
- **Priming rhizosphérique** = **nouvelle dette** ouverte par cette conception
  (plantes comme puits indirect, reporté).

## 6. Découpage (perf-first, 3 tronçons)

- **①a — champ + dynamique** : `GridField epaisseur_sol` stocké + `tick_epaisseur`
  (cible bulk-density, relaxation asymétrique, foisonnement age_sem, érosion
  baseline) + save/`engine_version`. **Golden RE-FIGÉ ANNONCÉ** (champ tické neuf,
  aucun effet en retour encore). Perf : un balayage plots/tuile, O(plots), pas de
  géométrie — négligeable.
- **①b — effets écolo** : rétention eau (greffe `tick_hydrology`, modulée
  composition) + accès NPK (borné vs D41). **Golden RE-FIGÉ ANNONCÉ** (deux flux
  neufs). **Test 500 ans** anti-emballement (boucle litière→eau→croissance).
- **② — rendu** : relief extrudé (`PxPerCmZ`) + expo snapshot (grille 2D, patron
  `t_sol`, re-bump pont) + recalage objets posés. **Pur-vue, golden NEUTRE**,
  points **F5**.
