# CONCEPTION — Réponse des plantes à l'écrasement (volet 2)

> **Statut : brouillon à étudier / amender par Nico.** Conception seule, aucun
> code. Fait suite au retour F5 du 2026-06-12 (« écraser maladroit ») dont le
> **volet 1** — écraser n'importe quelle guilde animale au clic — est déjà
> livré et testé. Ce volet 2 traite le cas où le sprite cliqué est une
> **plante**. Sujet de design écologique → doc à lire posément, pas une rafale
> de questions.

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

### 3.2 Quel segment ? — l'apex le plus exposé
Un pied écrase **le sommet** de la plante (ce qui dépasse). Proposition :
cibler **l'apex le plus haut** (segment au sommet de l'enveloppe). Pour une
herbacée en rosette (pissenlit, achillée), il n'y a quasi pas de tige dressée
→ peu de prise → effet faible **naturellement** (le modèle le donne sans cas
spécial : peu de hauteur = peu de segment exposé). *Question ouverte Q2.*

### 3.3 Quelle intensité ? — un trait de résistance par espèce
On introduit **un seul** trait sur `PlantBase`, sur le modèle de
`apical_dominance_base` :

```python
resistance_ecrasement: float = 0.5   # ∈ [0,1] — défaut : herbacée nominale
```

et l'intensité appliquée au seam est :
```
intensite_effective = INTENSITE_PIED * (1 - resistance_ecrasement)
```
avec `INTENSITE_PIED` une constante de calibrage (≈ 1.0 pour qu'une espèce
peu résistante passe en régime NET, une espèce résistante reste DOUX).

- **Résistance basse** (tournesol, jeune arbre) → intensité ≥ `COUPE_NETTE` →
  **écimage**, voire mort si c'est le collet d'un semis.
- **Résistance haute** (pâturin, trèfle, pissenlit) → intensité DOUCE →
  structure intacte → **ramification**.

**Le « bénéfice » n'est PAS un bonus** : il émerge du couplage
*intensité douce × port à faible dominance apicale*. Un pâturin (graminée
tallante, dominance basse) ramifie et **gagne** de la surface ; un tournesol
(flèche unique) ramifie mal et **perd** sa tête. Le même geste, deux issues,
zéro règle ad hoc — juste la structure existante. *Question ouverte Q1 : un
seul scalaire suffit-il, ou faut-il distinguer « résiste » de « profite » ?*

### 3.4 La mort, cas limite
Pas de « mort par écrasement » écrite à la main. Elle **émerge** : écimer le
collet d'un **semis** (1–2 segments, pas de bourgeon survivant) → `grow_plant`
ne trouve aucun apex → la plante n'a plus de structure viable. À vérifier :
le rejet de souche existant ne doit pas ressusciter un semis écrasé (il est
prévu pour des plantes établies). *Question ouverte Q3.*

## 4. Réponse proposée par espèce (à valider)

Trois archétypes lisibles, dérivés du `port_archetype` déjà présent :

| Espèce | Port actuel | `resistance_ecrasement` proposée | Issue attendue |
|---|---|---|---|
| **Poa annua** (pâturin) | herbacé bas | **0.9** tolérant→**stimulé** | graminée : talle, profite du piétinement |
| **Trifolium** (trèfle) | couvre-sol | **0.85** stimulé | couvre-sol piétinable, ramifie |
| **Taraxacum** (pissenlit) | rosette | **0.8** tolérant | rosette plaquée au sol, peu de prise |
| **Achillea** (achillée) | rosette/stolon | **0.75** tolérant | stolons, repart |
| **Medicago** (lupuline) | rampant | **0.7** tolérant | port bas, encaisse |
| **Bursa pastoris** (capselle) | rosette+hampe | **0.55** nominal | hampe cassable, rosette survit |
| **Phacelia** | dressé tendre | **0.45** sensible | tige tendre, déformée |
| **Basilic** | buissonnant | **0.4** sensible mais **profite du pincement** | cas litigieux, cf. Q1 |
| **Tomate** | buissonnant (dom. 2.2) | **0.35** sensible | tige cassante, dégât |
| **Poivron** | buissonnant | **0.35** sensible | idem |
| **Haricot** | grimpant | **0.3** sensible | tige volubile fragile |
| **Tournesol** | flèche unique | **0.15** très sensible | écimé = décapité |
| **Arbres** (figuier, pommier, cerisier, noyer, chêne) | ligneux | **0.05** au stade SEMIS, ~**0.95** établi | un semis s'écrase ; un tronc, non |

⚠ Les arbres exigent une **résistance fonction du stade/lignification** (un
chêne adulte est inécrasable, son semis non) — le scalaire seul ne suffit pas,
il faut le moduler par l'âge/le bois. *Question ouverte Q4.*

Le **basilic** est le cas qui éprouve le modèle : botaniquement le pincement
de l'apex le fait ramifier (bénéfice), mais sa tige est tendre (sensible).
« sensible » et « profite » ne sont donc **pas** le même axe → argument pour
**deux** traits (Q1).

## 5. Questions ouvertes (à trancher par Nico, pas par moi)

- **Q1 — un scalaire ou deux ?** `resistance_ecrasement` seul (simple,
  bénéfice émergent du port) **ou** + un `tolerance_pietinement` distinct pour
  les cas type basilic (résiste mal **mais** profite) ? *Reco : commencer à
  UN scalaire, le port porte déjà le « profite » ; ajouter le 2ᵉ trait
  seulement si le basilic sonne faux en test.*
- **Q2 — quel segment ?** apex le plus haut (proposé) / le collet / tous les
  segments au-dessus d'une hauteur de cheville ?
- **Q3 — mort émergente ?** acceptable qu'un semis écrasé meure « sans qu'on
  l'ait écrit » (cohérent philo #1, l'action directe est perturbatrice) ?
- **Q4 — arbres & stade :** comment moduler la résistance par la
  lignification/l'âge sans cas spécial laid ? (piste : `resistance` ×
  f(age_weeks) ou × nombre de segments lignifiés.)
- **Q5 — geste répété :** écraser deux fois de suite cumule-t-il (chaque
  passage baisse encore l'auxine) ou sature-t-il ? (le seam est idempotent sur
  l'écimage, cumulatif sur l'auxine douce.)
- **Q6 — pont & vue :** le pont passe déjà `target` pour les plantes
  (`x_cm/y_cm`, cf. `manger`/`deraciner`) ; écraser une plante = même cible,
  verbe `ecraser`. La vue n'a rien de neuf à envoyer. À confirmer.

## 6. Garanties (par construction)

- **Golden intact** : comme `tailler`, l'écrasement est **event-driven**, hors
  du tick déterministe. Le nouveau trait `resistance_ecrasement` a une valeur
  par défaut → au **repos** il ne change **rien** (le seam n'est appelé que
  sur geste). Aucune re-figeage attendu.
- **Pédagogie / philo** : aucun bonus/malus direct (#2) ; l'action directe sur
  le vivant est possible mais perturbatrice (#1) ; l'effet se découvre par
  l'observation, rien n'est annoncé (#6) ; deux joueurs verront des réponses
  différentes selon ce qu'ils ont planté (#7).
- **Coût Vigueur** : à décider — réutiliser le coût de `tailler` (MODÉRÉ,
  geste direct sur le vivant) paraît cohérent. *Sous-question de Q6.*

## 7. Découpage d'implémentation pressenti (après validation du doc)

1. Trait `resistance_ecrasement` sur `PlantBase` + valeurs par espèce
   (Q1/Q4 tranchées) — golden intact (défaut neutre, repos inerte).
2. `actions.py` : brancher `ecraser` sur une **cible plante** → calcul de
   l'intensité → `atteindre_segment`. Coût type `tailler`.
3. `sim_server.py` : router `ecraser` vers la cible plante quand `target`
   désigne une plante (x_cm/y_cm) vs une guilde — protocole inchangé ou bump
   mineur.
4. Tests : déformation (régime doux, structure intacte, ramification au tick
   suivant), écimage (régime net), survie/mort du semis, par-espèce contrasté.

---
*Réfs : `sim/growth.py` (seam §F `atteindre_segment`, `COUPE_NETTE`,
`_update_auxin`), `plants/base.py:433` (`port_archetype`,
`apical_dominance_base`), `CONCEPTION_CROISSANCE.md`, `CONCEPTION_HORMONES.md`.*
