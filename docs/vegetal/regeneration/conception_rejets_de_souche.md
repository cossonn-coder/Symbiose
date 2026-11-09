# Conception — rejets de souche (frein des rejets du figuier, reliquat D130)

Figée le 2026-11-09 (`/conception`, décisions de Nico). Sprint :
`sprints/vegetal/regeneration/sprint_frein_rejets_figuier/`. Prolonge
[`conception_releve_ligneuse.md`](conception_releve_ligneuse.md).

## 1. Le problème mesuré

Le tronçon ③ de la relève a donné au figuier des rejets `drageon` (`sim/clonal.py`).
Sur 200 ans de `verger_mur` : 9 169 rejets, 342 figuiers à l'an 200 jusqu'à 15 m
du fondateur, fourré de 193 petits ligneux sous une couronne, pommier éteint
[seed 42, n=1 run, VM].

Diagnostic (espion 25 ans, seed 42, n=1 run, VM, 2026-11-09) :
- **164 rejets sur 164 émis en hiver** (semaines 40-52). Les deux portes
  d'établissement du clonal (lumière au sol ≥ 0,30, couverture < 0,85) sont
  calibrées pour la saison de végétation : en hiver, le caduc est nu (lumière au
  plot 1,0) et l'herbe rase (couverture 0).
- **Cascade** : chaque rejet devient mère à 5 ans → 4 générations en 25 ans.
- Sans l'hiver : **0 rejet en 25 ans**. La portée (100 cm) est sous la couronne
  (~250 cm) et la lumière sous la mère vaut 0,25 en été (< 0,30).

Tout ou rien : ce n'est pas un réglage, c'est le modèle.

## 2. Ce que fait la nature

Un arbre qui « rejette de souche » ne colonise pas en continu. Les bourgeons
dormants de sa souche, nourris par les réserves des racines, partent **quand la
partie aérienne est perdue** : mort par vieillesse, casse, coupe, gel des rameaux.
Les rejets sortent au pied, sans avoir besoin de lumière au départ (la réserve les
porte), puis la compétition pour la lumière trie : le plus vigoureux devient
l'arbre suivant. La touffe reste au pied ; pour aller plus loin, il faut une
graine (ou une bouture : pour le figuier normand, c'est le jardinier).

Une souche dont les réserves sont épuisées (arbre mort d'ombre) ou dont les
racines sont détruites (sécheresse, asphyxie, racines rongées, pourridié) ne
rejette pas. C'est la leçon du taillis : on recèpe un charme, pas un hêtre, et
jamais un arbre déjà à bout.

Les stolons et rhizomes non plus ne s'enracinent pas en dormance.

## 3. Le modèle retenu

### 3.1 Dormance clonale (toutes clonales)
Aucune émission clonale (`emettre_ramets`) en hiver (`calendrier.SAISONS`, hors
`PHASES_ACTIVES`). Mesuré : dans le golden smoke, le trèfle émet 36 ramets, 0 en
hiver [smoke, n=1 run, VM] → golden **inchangé** attendu.

### 3.2 Capacité à rejeter : trait d'espèce
`rejet_souche ∈ [0, 1]` (défaut 0, `PlantBase`), valeurs [ordre de grandeur,
choix de conception] :

| fort ~0,8 | moyen ~0,5 | faible ~0,2 | nul 0 |
|---|---|---|---|
| figuier, cerisier, charme, aulne, saule, chêne | pommier, noyer | bouleau, hêtre | sapin |

Cohérent avec `fields/peripherie.ESSENCES_QUI_REJETTENT` (charme, aulne, saule ;
hêtre et bouleau non).

Le figuier perd son `clonal_mode = "drageon"` (→ `none`) : plus d'émission de fond.

### 3.3 Souche vivante : lue sur l'état, pas sur une cause
Le moteur ne garde pas la cause d'une mort ; il garde les **mémoires** de la
plante. La souche est vivante si, au moment de la perte, aucune mémoire de
**dommage au pied** ne dépasse un seuil : `shade_memory` (réserves épuisées),
`drought_memory`, `asphyxie_memory`, `root_herbivory_memory`,
`pourriture_memory`. Les mémoires de la partie aérienne (`cold_memory`,
`wind_memory`, `infection_memory`) et la sénescence ne tuent pas la souche.
Seuil indicatif : celui où chaque mémoire commence à blesser (ombre :
`seuil_ombre` de la relève ①) — à caler au code par le tronçon.

### 3.4 Deux déclencheurs
1. **Mort** de l'arbre (tout chemin de mort passe par `deposer_mort`).
2. **Perte de couronne** de l'arbre vivant : une part majeure de sa structure
   perdue en peu de temps (casse par tempête ou neige, cladoptose, effondrement,
   **taille du joueur**) → mémoire `perte_couronne` intégrée et décroissante.
   Seuil indicatif : la moitié de la masse de bois perdue en un an. La taille
   sévère devient ainsi un recépage émergent, sans geste nouveau.

### 3.5 Émission
- Nombre de rejets ∝ `rejet_souche` × intensité du déclencheur, borné (≤ 4 par
  événement — un taillis réel en fait des dizaines qui s'éclaircissent ; on ne
  simule que ceux qui comptent, cap perf).
- Au pied (rayon ~60 cm de la souche), **sans gate de lumière** (la réserve
  porte le rejet), avec les autres portes du plot (valide, place).
- **En saison de végétation** seulement (cohérent avec 3.1) : une perte en hiver
  fait rejeter au printemps suivant.
- Le rejet est un **clone** (gènes, expression, `form_seed` copiés, comme un ramet).
- Une souche ne rejette qu'une fois par déclencheur (pas de répétition chaque
  semaine).
- Ensuite il vit comme un semis : `seuil_ombre`, banque de semis, trouée.

### 3.6 Ce qui n'est PAS fait (et pourquoi)
- **Gel des rameaux** d'un ligneux adulte : absent du moteur ; c'est pourtant le
  déclencheur n°1 d'un figuier normand. Nouvelle mécanique → dette **D131**.
- Pas de geste joueur « recéper un arbre de tuile » : la taille sévère suffit.
- Les drageons du framboisier (arbuste, sans `age_curve`) restent tels quels.

## 4. Philo de design
- #1/#2 : rien n'agit directement sur la plante ; la perte (milieu, geste) est la
  contrainte, le rejet la réponse, la lumière trie.
- #3 : tout tirage via `_hash_noise`, canaux distincts de `sim/clonal.py`.
- #6 : le joueur apprend que la taille sévère fait rejeter le figuier et pas le
  sapin, et qu'un arbre mort d'ombre ne repart pas.

## 5. Coût perf
Contrôle au moment des déclencheurs seulement (mort, perte de couronne) + une
mémoire décroissante par ligneux procédural : négligeable. Le gain attendu est
inverse : plus de colonie de figuiers (le run 200 ans a coûté 198 min au lieu de
~90 [n=1 run, VM]).

## 6. Critères de fin (mesurés par `tools/diag_releve.py`)
`verger_mur`, seed 42, 200 ans : fourré ≤ 10 sous toute couronne ; remplacement
≥ 1 pour chaque espèce dont le fondateur meurt pendant le run ; figuiers vivants
à l'an 200 : une poignée (≤ 10), pas une colonie.

## 7. Voix
- Encyclopédie : capacité à rejeter de chaque espèce (niveau 2 ou 3) ; figuier
  corrigé (rejets après perte, pas en continu).
- Carnet : réutiliser la cause `rejet_de_souche` (déjà câblée pour `receper`).
- Événements : un événement `rejet` au ledger, lu par `diag_releve`.
- Voix de l'être : `attente` du semis ombragé (absorbé de la relève ⑤).
