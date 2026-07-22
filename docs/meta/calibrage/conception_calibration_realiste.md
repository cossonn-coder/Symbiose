# Conception — Calibration réaliste (microbiome + échelle vitalité) (SYMBIOSE)

> **Document de conception FIGÉ (2026-07-17).** Spec de référence du sprint
> d'implémentation (MOTEUR + vue). Découpe = **3 tronçons** (§7). Kickoffs :
> `sprints/meta/calibrage/sprint_calibration_realiste/0N_*.md`. Carnet d'état : `00_etat.md`.
> Origine : `BRIEF_CHAMPS_CONCEPTION.md` **P1** (verdicts 1 + 5), issu de
> `audit_champs.md` §9. Couple deux verdicts que la mesure a révélés être **un
> seul problème** : les champs vivants du sol opèrent ~10× sous la plage
> attendue par leurs normalisateurs de lecture.

---

## 0. Constat & périmètre

L'audit des champs a soulevé deux alertes traitées ici :

1. **« Le microbiome décroche »** — il chute 0.34 → 0.02 sur 10 ans (`audit_champs.md`
   §3.1). L'audit demandait : dérive de calibration ou dynamique voulue ? Le brief
   pariait sur un **artefact du monde smoke** (« en densité réaliste ça se soutient »).
2. **« `vitalite_average` très bas »** — la métrique de vitalité du sol sort ~0.02
   en monde dense et devrait, selon Nico, « sortir une valeur lisible, pas 0.02 ».

### Ce que la mesure a établi (banc `bench.py`/`bench2.py`/`bench3.py`, seed 42)

Trois faits mesurés qui **recadrent** le brief :

- **Deux « vitalités » distinctes étaient conflées.** `plant.vitalite` (santé de la
  plante) est SAINE dans tous les mondes testés (moyenne 0.5–0.75, médiane souvent
  0.7–1.0). Le « 0.02 » n'a jamais été la santé d'une plante : c'est `eco.vitalite`,
  la **métrique agrégée du SOL** (moyenne des plots), qui **n'a aucun lecteur dans le
  tick** — c'est une grandeur de VUE (snapshot/overlay F6).
- **Le microbiome décroche AUSSI en monde lâche** (2 tuiles 12×16, même nombre de
  plantes, canopée non fermée) — donc **ce n'est pas un artefact de densité**.
  Abaisser `MICROBE_FOOD_REF` de 1.0 à 0.15 (famine quasi désactivée) ralentit mais
  n'arrête pas le déclin. Le microbiome **relaxe** simplement depuis son semis
  généreux (0.3) vers son **équilibre bas réel** (~0.05), fixé par un apport
  d'exsudats limité par la lumière (~0.18). C'est écologiquement correct : la biomasse
  microbienne suit l'apport de carbone.
- **Racine commune = un mismatch d'échelle.** Le microbiome opère (moyenne) dans
  ~[0, 0.35], plot riche ~0.3–0.5, avec des pics transitoires jusqu'à ~2.3 an 1–2.
  Or **tous ses consommateurs le divisent par 3.0** (`FIELD_NORM`, le « cap
  canonique ») :
  - `uptake.py:63` (TICK) → bonus d'assimilation réel **~4 %** au lieu des 40 %
    annoncés (`UPTAKE_MICRO_BONUS`) ;
  - `sol.py:121` protection maladie (TICK) → logistique centrée sur 0.5, jamais
    atteinte → protection quasi-nulle même sur sol sain ;
  - `sol.py:136` + `qi_local` + vitalité VUE → ~0.01.
  Idem `om_active` divisé par 5.0 alors qu'il plafonne à ~0.67.

**Conclusion : le sol vivant fonctionne (il capitalise l'humus, cf. `om_stable`
0.15→2.66 sur 50 ans), mais il est LU sur une échelle où même son meilleur état
est écrasé — mécaniquement inerte ET affiché « mort ».** On ne pose PAS de plancher
(décision Nico) : on **réaligne l'échelle de lecture** sur la vraie plage
d'opération, côté VUE et côté TICK.

### Une nuance décisive : `om_stable` est un accumulateur centennal

Le banc 50 ans montre `om_stable` moyen monter 0.15 → **2.66 à 50 ans, encore en
hausse** (tend vers ~5 sur un siècle). Donc **`om_stable / 5.0` est CORRECT** : un
jeune sol lit bas sur ce terme, un vieux sol lit haut — c'est la mémoire longue du
terrain (philo #7, hétérogénéité persistante). **On n'y touche pas.** Le problème
d'échelle ne concerne QUE les champs « rapides » sous-plafonnés : `microbiome`
(÷3.0) et `om_active` (÷5.0).

---

## 1. Le phénomène (rappel bio)

La biomasse microbienne d'un sol suit l'apport de carbone labile (rhizodéposition +
litière fraîche). Sous une canopée qui capte peu de lumière, la photosynthèse — donc
les exsudats — est modeste : le microbiome se stabilise **bas mais vivant**. Ce n'est
pas une maladie du modèle, c'est le régime d'un sol forestier fermé peu productif.
Le rôle du microbiome (assimilation rhizosphérique, protection contre les pathogènes,
détox) reste **présent en proportion** : un sol qui en a peu en tire peu, un sol
qui en a beaucoup (hotspots sous racines actives, jeune sol amendé) en tire beaucoup.
L'échelle de lecture doit **rendre cette proportion**, au lieu de tout aplatir.

---

## 2. Traduction mécanique — le réalignement d'échelle

### 2.1 Principe : séparer *saturation/dynamique* et *effet/lecture*

Le littéral `microbiome / 3.0` porte AUJOURD'HUI **deux sémantiques distinctes**
qu'on confond :

- **Référence de saturation (dynamique du champ).** Dans `croissance.py:241`, la
  borne anti-emballement `× (1 − micro_norm)` **fixe l'équilibre** vers lequel le
  microbiome converge. La changer déplacerait la trajectoire du champ lui-même.
  → **INCHANGÉE** (préserve la dynamique, donc la valeur `microbiome` du golden).
- **Référence d'effet (lecture du champ).** Dans `uptake.py:63`, `sol.py:121`,
  `sol.py:136`, `qi_local`, le `/3.0` traduit « combien de microbiome = plein
  effet ». C'est **elle** qui est mal calée (3.0 vs plage réelle ~0.5).
  → **RÉALIGNÉE** sur la plage réelle.

On matérialise la distinction par une **constante nommée** dédiée à l'effet :

```
MICROBE_EFFECT_REF = 0.6   # microbiome « plein effet » (plage réelle plot riche ~0.5)
OM_ACTIVE_REF      = 1.0   # om_active « plein effet » (plafond réel ~0.67)
# om_stable : reste sur /5.0 (OM_STABLE_REF = 5.0, accumulateur centennal — inchangé)
```

Effet obtenu avec `MICROBE_EFFECT_REF = 0.6` sur `uptake` (`1 + micro_norm ×
UPTAKE_MICRO_BONUS`) :

| microbiome plot | micro_norm | bonus uptake |
|---|---|---|
| 0.05 (équilibre, sol pauvre) | 0.083 | ×1.03 (≈ nul — correct) |
| 0.4 (plot riche sous racine) | 0.67 | ×1.27 (significatif) |
| ≥ 0.6 (hotspot / jeune sol amendé) | 1.0 (clampé) | ×1.40 (plein) |

La **rétroaction rhizosphère** redevient discriminante : le sol pauvre n'a pas de
bonus, le sol riche en a un vrai — sans jamais poser de bonus direct sur la plante
(philo #2 : le flux microbien module l'assimilation, la plante répond).

### 2.2 Attention — `FIELD_NORM` sert AUSSI aux nutriments

Dans `qi_local` (`vigueur_plante.py`), `FIELD_NORM = 3.0` normalise **et** le
microbiome (ligne 82) **et** les nutriments (ligne 81, échelle NPK [0,3]). Le
réalignement ne concerne **que le terme microbiome** : repointer la ligne 82 sur
`MICROBE_EFFECT_REF`, **laisser la ligne 81 (nutriments) sur son échelle [0,3]** — la
calibration NPK de fond est un autre chantier (P2, sliders worldgen). Ne pas
confondre les deux normalisations sous un seul nom.

### 2.3 La métrique de vitalité du sol (VUE)

`eco.vitalite(r,c)` = somme pondérée `micro·0.35 + om_active·0.25 + fert·0.20 +
om_stable·0.20 − disturb·0.15`, bornée [0,1], moyennée sur les plots. Avec les
normalisateurs réalignés (micro/0.6, om_active/1.0, om_stable/5.0 inchangé,
fertilite_index/3.0 inchangé), la métrique **s'étale à nouveau** : un sol dégradé
reste bas, un sol qui capitalise humus + vie microbienne monte visiblement.

**Objectif de calibration (ancres, via le banc) :** la métrique doit **discriminer
en bande lisible** — sol jeune/pauvre ~0.1–0.2, sol mûr/riche nettement plus haut
(~0.5+), sol dégradé/perturbé ~0.05. Le critère de succès n'est PAS une valeur
absolue imposée mais que la métrique **cesse d'aplatir tous les états près de 0.01–
0.07** et sépare visiblement bon et mauvais sol. Si, après réalignement des
normalisateurs, la **pénalité `disturbance` (0.15)** domine encore les termes
positifs et écrase la bande, le tronçon ① est autorisé à **ré-équilibrer les poids**
(somme ≈ 1, clamp [0,1] conservés) — dérive documentée dans le kickoff.

---

## 3. Respect de la philosophie #1–#7

- **#2 (flux → contrainte → réponse, jamais de bonus direct).** Respecté : on ne
  touche à aucun attribut de plante. On recalibre comment un **champ** (microbiome)
  est **lu**. La plante répond au flux d'assimilation, comme avant — plus finement.
- **#3 (déterminisme).** Aucun RNG introduit. Ce sont des changements de constantes
  et de normalisations, bit-déterministes. La *saturation-ref* du champ reste figée →
  la dynamique du microbiome ne bouge pas d'elle-même.
- **#5 (indices visuels, pas de HUD chiffré).** La métrique vitalité reste une
  grandeur d'overlay debug (F6) / snapshot ; le réalignement la rend simplement
  lisible. Aucun chiffre promu en HUD primaire.
- **#7 (hétérogénéité persistante).** `om_stable/5.0` conservé → un vieux sol lit
  haut, un jeune bas ; la mémoire longue du terrain reste discriminante.

---

## 4. Interconnexions (qui bouge quand on réaligne)

- **microbiome → uptake → NPK → croissance → exsudats → microbiome.** Réaligner
  `uptake` rouvre la rétroaction rhizosphère : un sol vivant assimile mieux, la
  plante croît mieux, exsude plus, nourrit le microbiome. C'est la boucle vertueuse
  visée par le sprint « sol vivant » — aujourd'hui **débranchée par l'échelle**.
  → C'est ce qui re-fige le golden au tronçon ② (cascade attendue et voulue).
- **microbiome → protection maladie** (`sol.py:121`) : un sol sain protège enfin
  réellement contre la propagation (logistique qui atteint sa zone active).
- **om_active → vitalité VUE** : la matière active devient lisible (métrique).
- **Non touché ce sprint (interconnexions préservées telles quelles) :** decompo
  speed (`matiere_organique.py:96,133`), soil_memory (`sol.py:71`), CEC/lessivage
  (`om_stable/5.0` conservé), worm resource (`resources.py:255`), détox allélo
  (`allelopathie.py:43`), bascule létale perturbation (`perturbations.py:364`),
  saturation exsudats (`croissance.py:241`). Voir §6 (non-périmètre).

---

## 5. Voix narratives

Aucune espèce ajoutée ni modifiée → **pas de nouvelle voix à écrire**. Effet
indirect bienvenu : la métrique vitalité lisible sert l'**overlay debug** (F6) et,
à terme, la lecture diégétique « sol vivant » (encyclopédie/carnet) sans chiffre en
HUD primaire. Rien à produire au titre de la règle des 5 voix.

---

## 6. Non-périmètre (assumé, noté en suivi)

Les autres sites qui lisent `microbiome / 3.0` partagent le même mismatch latent
mais **ne sont PAS réalignés ici** — ce sont des **modulateurs de rythme** tissés
dans la dynamique du sol (vitesse de décompo, mémoire du sol, ressource lombric,
détox, bascule de perturbation). Les réaligner **reshaperait tout le modèle de
matière organique** (cascade décompo → NPK → humus) et sort du cadre de P1
(calibration de lecture microbiome/vitalité). À rouvrir dans un sprint de
**calibration MO/décompo** dédié si le besoin se confirme au banc. Consigné en
**dette (D-cal)**.

De même, la **calibration NPK de fond** (P effondré, `fertilite_index/3.0`) relève
de **P2** (sliders d'abondance à la worldgen, `BRIEF_CHAMPS_CONCEPTION.md`).

---

## 7. Découpage en tronçons (perf-first, golden maîtrisé)

Coût perf : **nul** (changement de constantes/normalisations, aucune boucle
ajoutée). Le banc `tools/` est un outil hors-tick.

### ① Banc de calibration + métrique vitalité VUE
- **Livrable outillage :** `tools/banc_calibration.py` (promotion de `bench.py`,
  conservé) — mesure les plages d'opération (microbiome, om_active, om_stable,
  vitalité) sur N années, mondes dense/lâche. Réutilisable pour toute calibration
  future.
- **Livrable moteur :** introduit `MICROBE_EFFECT_REF`, `OM_ACTIVE_REF` dans
  `constants.py` ; réaligne **les seuls lecteurs de VUE** : `eco.vitalite`
  (`sol.py:136` micro → `MICROBE_EFFECT_REF`, `sol.py:137` om_active →
  `OM_ACTIVE_REF`, `sol.py:139` om_stable **inchangé**). Ré-équilibre les poids
  seulement si nécessaire (§2.3).
- **Golden : re-figé LOCALISÉ** au seul champ `"vitalite"` des lignes `ECO` du
  digest (la métrique change de valeur ; rien d'autre ne bouge car aucun lecteur
  tick). Dérive attendue, expliquée.

### ② Normalisateurs d'effet TICK
- Réaligne les **lecteurs d'effet du tick** sur `MICROBE_EFFECT_REF` :
  `uptake.py:63`, `sol.py:121` (maladie), et le **seul terme microbiome** de
  `qi_local` (`vigueur_plante.py:82` ; nutriments ligne 81 **inchangés**).
- `croissance.py:241` (saturation) **INCHANGÉE**.
- **Golden : re-figé LARGE, annoncé.** La rétroaction rhizosphère rouvre la cascade
  uptake → NPK → croissance. Dérive globale attendue et voulue (le microbiome
  devient mécaniquement utile). Re-capture maîtrisée + smoke test relu.

### ③ Vue Godot — overlay F6 + banc d'observation
- Overlay `FieldOverlay` vitalité à la **nouvelle échelle** (la heatmap doit rester
  lisible sur la bande recalibrée). Snapshot `"vitalite"` déjà exporté → vérifier le
  mappage couleur côté C# (`FieldOverlay.cs`).
- Banc d'observation F5 : une carte où Nico juge « le sol vivant se lit » (un coin
  riche vs un coin pauvre nettement distincts à l'overlay).
- **Golden : intact** (rendu pur).

---

## 8. Rattachement à l'existant

- **BRIEF** `BRIEF_CHAMPS_CONCEPTION.md` P1 (verdicts 1 + 5) ; P0 (banc) **absorbé**
  dans le tronçon ① ; P2 (NPK worldgen) et P3 (mycélium) restent des sprints à part.
- **DETTE** : D41 (mort par carence édaphique, bloquée `qi_local` épuisé — le
  réalignement `qi_local` de ② y contribue indirectement) ; **D-cal** (nouvelle :
  calibration MO/décompo des modulateurs de rythme, §6).
- **Conceptions voisines** : `etude_sol_vivant.md` (MO/microbiome),
  `docs/champs/sol/conception_decomposition_compost.md`, `CONCEPTION_PHYSICOCHIMIE_SOL.md` (NPK,
  Liebig), `docs/faune/mycelium/conception_mycelium_interconnexions.md` (mycorhize → uptake P, futur
  câblage P3).
- **Golden** : `tests/test_golden.py` — re-figé au ① (localisé) et au ② (large),
  intact au ③.
