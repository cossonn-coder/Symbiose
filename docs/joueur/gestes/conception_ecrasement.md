# CONCEPTION — Réponse des plantes à l'écrasement (volet 2)

> **Statut : conception FIGÉE (2026-06-12, Q1–Q6 tranchées par Nico).** Prête
> pour l'implémentation. Fait suite au retour F5 du 2026-06-12 (« écraser
> maladroit ») dont le **volet 1** — écraser n'importe quelle guilde animale au
> clic — est déjà livré et testé. Ce volet 2 traite le cas où le sprite cliqué
> est une **plante**. Les décisions de Nico sont reportées en **§5**.

## 1. L'intention (mots de Nico)

> « guildes animales **et plantes** — écraser une plante ne la tue pas
> forcément mais peut la déformer. Ça dépend de la variété de la plante.
> Certaines plantes profitent du fait d'être écrasées. C'est au joueur de le
> découvrir. »

Trois exigences en découlent :
1. Écraser une plante a un effet **gradué** (pas binaire mort/rien) : surtout
   une **déformation**.
2. L'effet **dépend de l'espèce** (variété).
3. **Certaines espèces en profitent** — et ce n'est ni dit ni montré : le
   joueur le découvre par l'observation (philo #6).

## 2. La bonne nouvelle : le mécanisme existe DÉJÀ

`sim/growth.py:241` expose un **seam de perturbation unique** :

```python
def atteindre_segment(plant, segment_id, intensite):  # intensite ∈ [0,1]
```

dont le commentaire annonce déjà notre cas : « `tailler` aujourd'hui ; grêle /
ravageur / **vent** plus tard appelleront le **MÊME** seam ». L'écrasement
d'une plante en sera un **nouvel appelant** — zéro mécanique neuve dans le
moteur de croissance.

Le seam a deux régimes, séparés par `COUPE_NETTE = 0.8` :

| Régime | Intensité | Effet structurel immédiat | Réponse émergente (tick suivant) |
|---|---|---|---|
| **DOUX** | < 0.8 | baisse l'auxine du segment, structure **intacte** | l'inhibition tombe → les **latéraux débourrent** → la plante **ramifie** |
| **NET** | ≥ 0.8 | **écimage** : retrait du segment + son sous-arbre (collet protégé) | rejet depuis les bourgeons survivants, ou rejet de souche |

→ « déformer » = régime **DOUX** ; « profiter » = régime DOUX **sur une plante
dont le port tire bénéfice de la ramification** ; « abîmer/tuer » = régime
**NET** sur une plante fragile. **Tout est déjà là** — il reste à décider
*avec quelle intensité* l'écrasement frappe *quel segment*, et *comment
l'espèce module ça*.

## 3. Modèle proposé

### 3.1 Le geste mappé sur le seam
Écraser une plante (sprite végétal cliqué) appelle :
```
atteindre_segment(plant, segment_cible, intensite_effective)
```
La **réponse n'est jamais écrite directement** sur la plante (pas de
mort/bonus posé à la main) — elle **émerge** au `grow_plant` suivant. C'est
exactement la philo #2 (flux → contrainte → réponse biologique émergente) et
ça garantit la cohérence avec `tailler`.

### 3.2 Quel segment ? — le collet, ou le segment cliqué (Q2 tranchée)
Le pied tape à la **base** / là où la souris désigne. On réutilise le
`target.segment` optionnel de `tailler` : présent → ce segment ; **absent → le
collet** (segment 0). Écimer le collet d'un semis est la voie de la mort
émergente (sentiers, Q3). Pour une rosette (pissenlit, achillée), la haute
résistance maintient l'intensité DOUCE → la plante plie sans casser, même au
collet.

### 3.3 Quelle intensité ? — résistance × âge (Q1, Q4 tranchées)
On introduit **deux** traits sur `PlantBase`, sur le modèle de
`apical_dominance_base` (sémantique complète en §5) :

```python
resistance_ecrasement:  float = 0.5   # ∈ [0,1] — encaisse avant de casser
stimulation_ecrasement: float = 0.0   # ∈ [0,1] — repart-elle après ? (basilic, pâturin)
```

L'intensité appliquée au seam est modulée par l'âge (Q4) :
```
intensite_effective = INTENSITE_PIED * (1 - resistance_ecrasement * f_lignification(age))
```
avec `INTENSITE_PIED` une constante de calibrage (≈ 1.0 pour qu'une espèce peu
résistante passe en régime NET, une résistante reste DOUX) et
`f_lignification(age)` croissante bornée (semis ≈ 0 → s'écrase ; établi ≈ 1 →
inécrasable). Pour les annuelles, `f` ≈ constante (vie courte).

- **Résistance effective basse** (tournesol, semis d'arbre) → intensité ≥
  `COUPE_NETTE` → **écimage**, voire **mort** si c'est le collet d'un semis (Q3).
- **Résistance effective haute** (pâturin, trèfle, pissenlit, tronc établi) →
  intensité DOUCE → structure intacte → **ramification** si `stimulation` > 0.

**Le « bénéfice » n'est PAS un bonus de santé** (philo #2) : après le coup,
`stimulation_ecrasement` lève l'inhibition (auxine) sur les apex survivants →
le débourrement latéral **émerge** au tick. Un pâturin (résistance + stimulation
hautes) talle et **gagne** ; un tournesol (les deux basses) **perd** sa tête ;
un basilic (résistance basse **mais** stimulation haute) est écimé **et** repart
buissonnant — le pincement. Deux axes, trois issues, zéro règle ad hoc.

### 3.4 La mort, cas limite (Q3 — VOULUE)
Pas de « mort par écrasement » écrite à la main. Elle **émerge** : écimer le
collet d'un **semis** (1–2 segments, pas de bourgeon survivant) → `grow_plant`
ne trouve aucun apex → la plante n'a plus de structure viable. C'est le
mécanisme des **sentiers** (Q3). Garde-fou à valider en test : le rejet de
souche existant ne doit pas ressusciter un semis écrasé (il est prévu pour des
plantes établies) — sinon pas de chemins.

## 4. Réponse par espèce (deux scalaires, à affiner au calibrage)

Valeurs de DÉPART (calibrage fin post-test, comme `K`/`BASE` de la maîtrise) :

| Espèce | Port actuel | `resistance` | `stimulation` | Issue attendue |
|---|---|---|---|---|
| **Poa annua** (pâturin) | herbacé bas | **0.9** | **0.9** | graminée : talle, profite du piétinement |
| **Trifolium** (trèfle) | couvre-sol | **0.85** | **0.8** | couvre-sol piétinable, ramifie |
| **Taraxacum** (pissenlit) | rosette | **0.8** | **0.4** | rosette plaquée, encaisse, repart mou |
| **Achillea** (achillée) | rosette/stolon | **0.75** | **0.6** | stolons, repart |
| **Medicago** (lupuline) | rampant | **0.7** | **0.5** | port bas, encaisse |
| **Bursa pastoris** (capselle) | rosette+hampe | **0.55** | **0.2** | hampe cassable, rosette survit |
| **Phacelia** | dressé tendre | **0.45** | **0.2** | tige tendre, déformée |
| **Basilic** | buissonnant | **0.4** | **0.85** | **écimé MAIS repart** = le pincement |
| **Tomate** | buissonnant (dom. 2.2) | **0.35** | **0.4** | tige cassante, repart un peu |
| **Poivron** | buissonnant | **0.35** | **0.4** | idem |
| **Haricot** | grimpant | **0.3** | **0.2** | tige volubile fragile |
| **Tournesol** | flèche unique | **0.15** | **0.05** | écimé = décapité, ne repart pas |
| **Arbres** (figuier, pommier, cerisier, noyer, chêne) | ligneux | base **0.1** × âge | **0.3** | semis s'écrase ; tronc, non (Q4) |

Le **basilic** (résistance 0.4 / stimulation 0.85) valide les deux axes :
écimé facilement, il **repart buissonnant** — exactement le pincement
horticole. Les **arbres** portent une résistance de base faible **×** l'âge
(Q4) : leur semis s'écrase, le tronc établi non.

## 5. Décisions FIGÉES (Nico, 2026-06-12)

- **Q1 → DEUX scalaires.** « résiste » et « profite » sont deux axes
  indépendants (le basilic résiste mal **mais** profite). On porte donc deux
  traits distincts sur `PlantBase` :
  - **`resistance_ecrasement` ∈ [0,1]** (défaut 0.5) — résistance
    *structurelle*. Pilote l'intensité au seam : haute → reste DOUX (plie),
    basse → NET (casse/écime). Modulée par l'âge (Q4).
  - **`stimulation_ecrasement` ∈ [0,1]** (défaut 0.0) — *bénéfice* de
    repousse. Après le coup, lève l'inhibition (baisse d'auxine) sur les
    **apex survivants** ∝ ce trait → débourrement latéral → ramification au
    tick suivant. Reste **émergent** (on n'écrit que l'auxine, jamais la
    santé) : à 0 la plante subit, à 1 elle talle vigoureusement. Découple
    proprement le basilic (résistance basse **+** stimulation haute).
- **Q2 → le COLLET, ou le segment cliqué si la vue le précise.** Le pied tape
  à la base / là où la souris désigne — PAS l'apex le plus haut. On réutilise
  le `target.segment` optionnel déjà introduit pour `tailler` (protocole
  0.2.1) : présent → ce segment ; absent → le **collet** (segment 0). Écimer
  le collet d'un semis = la voie de la mort (Q3).
- **Q3 → la mort émergente est VOULUE, et centrale.** Un **sentier** est un
  endroit régulièrement écrasé où moins de plantes poussent : écimer le collet
  d'un semis (aucun bourgeon survivant) → `grow_plant` ne trouve plus d'apex →
  la plante s'éteint, *sans qu'on l'écrive*. À vérifier impérativement : le
  **rejet de souche** existant ne doit PAS ressusciter un semis écrasé (il est
  pour des plantes établies) — sinon pas de sentiers.
- **Q4 → `resistance` × âge.** L'intensité effective lit
  `resistance_ecrasement × f_lignification(age)` : un **semis** d'arbre a une
  résistance quasi nulle (s'écrase), un sujet établi tend vers l'inécrasable.
  `f_lignification` croît avec `age_weeks` (ou le nombre de segments
  lignifiés), bornée. S'applique surtout aux ligneux ; neutre pour les
  herbacées annuelles (durée de vie courte → `f` ≈ constante).
- **Q5 → l'écrasement se CUMULE.** Pas de saturation : chaque passage rebaisse
  l'auxine (le seam est déjà cumulatif sur l'auxine douce, idempotent sur
  l'écimage déjà fait). Deux écrasements rapprochés enfoncent la plante /
  entretiennent le sentier — cohérent avec Q3.
- **Q6 → pont confirmé.** Écraser une plante = même `target` que
  `manger`/`deraciner` (`tile`, `x_cm`, `y_cm`) + `segment` optionnel ; verbe
  `ecraser`. Le routage animal/plante se fait sur la forme du `target`
  (`guilde` → guilde animale ; `x_cm/y_cm` → plante). La vue n'envoie rien de
  neuf au-delà de ce qu'elle sait déjà pour les autres gestes sur plante.

## 6. Garanties (par construction)

- **Golden intact** : comme `tailler`, l'écrasement est **event-driven**, hors
  du tick déterministe. Les nouveaux traits ont des valeurs par défaut → au
  **repos** ils ne changent **rien** (le seam n'est appelé que sur geste).
  Aucun re-figeage attendu.
- **Pédagogie / philo** : aucun bonus/malus direct (#2 — on n'écrit que
  l'auxine, la réponse émerge) ; l'action directe sur le vivant est possible
  mais perturbatrice (#1) ; l'effet se découvre par l'observation, rien n'est
  annoncé (#6) ; deux joueurs verront des réponses différentes selon ce qu'ils
  ont planté (#7) ; les sentiers (Q3) sont un motif spatial ÉMERGENT (#1, le
  sol porte la mémoire).
- **Coût Vigueur** : réutiliser le coût de `tailler` (MODÉRÉ, geste direct sur
  le vivant) — cohérent avec Q6.

## 7. Découpage d'implémentation (conception figée → prêt)

1. Traits `resistance_ecrasement` + `stimulation_ecrasement` sur `PlantBase` +
   valeurs par espèce (§4) + `f_lignification(age)` pour les ligneux (Q4) —
   golden intact (défauts neutres, repos inerte).
2. `actions.py` : `ecraser_plante(gs, player, plant, eco, segment_id=None)` →
   intensité = `INTENSITE_PIED × (1 − resistance × f_age)` → `atteindre_segment`
   (collet si `segment_id` absent, Q2) → si apex survivants, lever l'auxine ∝
   `stimulation` (Q1). Cumulatif (Q5). Coût type `tailler` (Q6).
3. `sim_server.py` : router `ecraser` vers la cible plante quand `target`
   désigne une plante (x_cm/y_cm) vs une guilde — protocole inchangé ou bump
   mineur.
4. Tests : déformation (régime doux, structure intacte, ramification au tick
   suivant), écimage (régime net), survie/mort du semis, par-espèce contrasté.

---
*Réfs : `sim/growth.py` (seam §F `atteindre_segment`, `COUPE_NETTE`,
`_update_auxin`), `plants/base.py:433` (`port_archetype`,
`apical_dominance_base`), `docs/vegetal/croissance/conception_croissance.md`, `docs/vegetal/croissance/conception_hormones.md`.*
