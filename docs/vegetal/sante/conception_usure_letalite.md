# CONCEPTION — Usure, pas punition : létalité & compétition (D64 reframé)

> Conception FIGÉE le 2026-07-04 (Nico, via /conception). Sprint borné,
> **prérequis** de la future conception « Luxuriance / stratification » (§6).
> Source de vérité = moteur Python (`data/code/`). Golden = smoke test
> (`tests/test_golden.py`).

## 1. Problème — le diagnostic D64 était FAUX

D64 accusait « herbivorie létale + mortalité de fond qui se cumulent ». Le repro
instrumenté (banc `grimpantes`, seed 42) **réfute** cette hypothèse : à la
densité de ravageur observée (≈ 0,012), `herbivory_pressure` calcule
`pressure = 0,012 × HERBIVORY_GAIN(0,20) = 0,0024 < seuil 0,005` → **l'herbivorie
ne tire jamais**. Le tournesol-hôte de la démo ③ meurt en réalité du **système de
conflit spatial** (`_resoudre_conflits` + `detect_conflicts` + `regress`) :

- **w11** : le tournesol passe au stade `jeune` → `age_weeks` remis à 0. Ses
  empreintes `foliar` ET `root` chevauchent le haricot voisin. **Deux**
  `ConflictNotification` distincts naissent (un `foliar`, un `root`),
  `weeks_active=1`. `loser()` = le plus jeune par `age_weeks` → le tournesol qui
  vient de grandir est **désigné perdant des DEUX**.
- **w12** : les deux conflits atteignent `weeks_active=2 ≥ space_tolerance(2)` et
  se résolvent **dans le même tick**, chacun appelant `loser.regress()` :
  `[foliar]` jeune→semis (health 3), puis `[root]` semis→**health=0 = mort**.

→ **jeune → semis → mort en un tick**, par **double régression** d'une seule
relation de compétition comptée deux fois (aérien + racinaire).

Trois odeurs de design cumulées : (1) **double comptage** foliar+root d'une même
paire ; (2) **`regress()` létal** (au stade 0 → `health=0`) : une seule relation
tue une plante saine ; (3) **« le plus jeune perd » + reset d'âge à la montée de
stade** → grandir te désigne perdant (rétroaction perverse).

## 2. Ancrage — le code viole une conception DÉJÀ figée

`docs/vegetal/catalogue/conception_competition_intraplot.md` (Nico, 2026-06-13) a tranché **Q3** :

> « La mort du perdant **émerge** du déclin de santé (`_tick_senescence_health`)
> → nécromasse. **Jamais** de mortalité "verdict". »

et décrit `detect_conflicts` comme purement informatif (« `resolved` n'est jamais
positionné → aucune mortalité n'en découle »). Or `_resoudre_conflits` positionne
`resolved` ET tue via `regress()`. **Ce sprint ne conçoit rien de neuf sur ce
point : il ALIGNE le code sur cette décision figée.** `regress()` n'est appelé que
là (grep exhaustif) → neutralisation propre.

**Mesure décisive** (regress-kill neutralisé, `grimpantes` seed 42, 1 an) : le
tournesol (le plus HAUT) survit et prospère ; le haricot (plus bas) accumule
`shade_memory` 0,07 → 0,64 → 0,69 (> seuil 0,6) et décline lentement (santé 3→2 à
w52) → **dépérissement émergent par ombrage** = exactement la mort de Q3. **Aucun
zombie** → le §2.3 de la conception intra-plot (densité incluant les co-occupants)
**n'est PAS nécessaire** (sa condition explicite : « seulement si embouteillage »).

## 3. Décisions FIGÉES (Nico, 2026-07-04)

- **Périmètre = REFRAME** de D64 (modèle compétition + létalité), pas patch étroit.
- **Modèle = C (hybride)** : `detect_conflicts` reste une **notification**
  diégétique ; la résolution **n'est plus létale** (plus de `regress()`/kill). La
  mort du dominé **émerge** des voies continues (ombrage LightField + ponction
  racinaire partagée + sénescence).
- **Cap de létalité chronique par tick** : une plante saine ne peut plus mourir en
  un tick des voies de FOND indépendantes. Échelle santé **0-3 conservée**
  (élargir = hors périmètre).
- **Séquencement** : ce sprint borné D'ABORD ; « Luxuriance / stratification »
  ensuite, comme conception séparée (§6).

## 4. Modèle par tronçon

### ① Conflit non-létal — `sim/engine/mortalite.py::_resoudre_conflits`
`_resoudre_conflits` **détecte encore** (log/notification), mais ne **régresse
plus** et ne **tue plus** : suppression de l'appel `loser.regress()` et du
`c.resolved = True` qui scellait une mort. Le conflit devient un simple signal
« deux plantes se disputent la place » ; l'issue (qui l'emporte, qui décline)
tombe des champs continus. Pruning léger des conflits périmés (plante morte /
plus de chevauchement) pour borner `tile.conflicts`. La méthode `regress()`
(instance.py) devient **inutilisée** → **conservée** (règle « ne jamais jeter de
code »), signalée dans le kickoff.

- **Rend caduques d'un coup** les 3 odeurs (double comptage, regress létal, « plus
  jeune perd ») — plus aucune n'a d'effet létal.
- **Golden : RE-FIGÉ annoncé** → `a6c2f651…` devient `a1c9c51f61c60fd6edf2500663ebcecfb9eac9d02a1120670f7ecf3fecd434cf`
  (mesuré : le smoke exerçait des morts par conflit ; elles disparaissent ou
  glissent vers le stress/sénescence — dérive localisée, attendue).

### ② Cap de létalité chronique — `sim/effects/perturbations.py::apply_disturbances`
Avant `apply_mutations`, **borner à −1 santé/tick/plante** le cumul des
`ReduceHealth` issus des voies **CHRONIQUES** :
`{herbivorie, mortalité de fond, stress hydrique sévère, carence lumineuse,
maladie fongique}`. Les voies **AIGUËS restent exemptes** : `fonte des semis`
(damping_off, mort décisive d'un semis en sol froid détrempé = leçon permaculture)
et gel/grêle/vent (déjà `_mediated_damage`/`_wind_damage`, hors `apply_disturbances`).

Implémentation : partitionner les mutations du tick en `acute` (damping_off) et
`chronic` (les autres voies) ; pour chaque plante, si la somme des amounts
chroniques > 1, la **clamper à 1** (garder le premier point, ignorer le surplus) ;
puis `apply_mutations(acute + chronic_clampé)`. **Zéro RNG** (simple clamp
déterministe, philo #3). Tue le mort-éclair théorique herbivorie-létale(−2) +
fond(×0,7) dans un même tick.

- **Golden : re-figeage LOCALISÉ pré-autorisé** (attendu **neutre** — le smoke
  utilise sols drainants + espèces neutres, le cumul chronique dépasse rarement
  −1 ; si le cap mord, dérive expliquée = cumul borné). Le kickoff autorise le
  `--capture` si divergence.

### ③ Vue Godot & validation F5 — `grimpantes`
Le rendu de l'**usure** est **déjà en place** : `PlantRenderer.Organs.cs:214-222`
mappe le signe `ombre` (`_litFactor` dépérissant). Ce tronçon : (a) **vérifie de
bout en bout** la chaîne `serialize.leaf_symptoms(ombre/sénescence) → PlantRenderer`
(le dépérissement progressif du dominé se VOIT — « usure, pas punition »
lisible) ; (b) **rejoue le banc `grimpantes` en F5** : l'hôte tournesol survit et
se fait ombrer, plus de mort-éclair ; (c) **rattache** le volet (b) de D64
(lisibilité des auxiliaires) à **D60** (déjà conçu) — **non fondu ici**. Petit
ajustement `PlantRenderer` **seulement si** l'usure n'est pas assez lisible.

- **Golden : INTACT** (vue C# / lecture pure).

## 5. Perf
Toutes les modifs sont O(plantes)/O(mutations) locales, sans nouvelle passe
spatiale globale → budget ≤ +10 %/tick trivialement tenu. ② n'ajoute qu'un
regroupement par plante des mutations déjà produites.

## 6. Hors périmètre — Luxuriance / stratification (conception SÉPARÉE à venir)
Nico (2026-07-04) : le vrai but est la **luxuriance par stratification** — un plot
porte plusieurs plantes de strates différentes (couvre-sol trèfle + tomates
au-dessus + grimpantes + traçantes), la compétition **émergeant de la
densification**. Fondations déjà présentes (strates `sol/basse/moyenne/haute/
grimpante`, co-occupation autorisée, ombrage vertical LightField). **Manque**, à
concevoir dans une /conception dédiée (4 briques, toutes prioritaires pour Nico) :
1. **Densification clonale** des couvre-sols/traçantes (stolons : trèfle, fraisier,
   menthe tapissent la tuile).
2. **Champ de couverture au sol** par strate (« sol couvert à X % de trèfle »), lu
   par l'écologie ET le rendu.
3. **Empilement multi-strates VISIBLE** (superposition/ordre de dessin lisible).
4. **Empreinte graphique propre à l'espèce** — **taille au sol ET silhouette**
   (trèfle ras ↔ courge étalée ↔ tournesol haut).

**§2.3 en réserve** (non implémenté) : si un jour deux compétiteurs de MÊME
hauteur zombifient, le remède est déjà conçu (CONCEPTION_COMPETITION_INTRAPLOT
§2.3 Q4 : inclure les co-occupants dans `_local_density`).

## 7. Découpage (perf-first, golden maîtrisé)
1. **① Conflit non-létal** — moteur, golden **re-figé** `a1c9c51f…`.
2. **② Cap létalité chronique** — moteur, golden re-figeage localisé pré-autorisé.
3. **③ Vue Godot & F5** — rendu (déjà en place) + validation banc, golden intact.
