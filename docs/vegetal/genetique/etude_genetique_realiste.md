# ÉTUDE — Une génétique alignée sur la réalité

> Document à étudier (2026-11-16, `/conception` D139). Ce n'est pas une
> conception figée : il explique comment marche la génétique des plantes
> réelles, ce que fait le moteur aujourd'hui, l'écart entre les deux, et
> trois options de refonte avec ma recommandation. Tu décides ensuite.

## 1. Ce que fait le moteur aujourd'hui

- **10 gènes** (`plants/genetics.py:GENE_NAMES`). Chacun est un **facteur sans
  unité** autour de 1,0 : `hauteur`, `rusticite_froid`, `vigueur`,
  `resistance_pathogene`, `tolerance_secheresse`, `tolerance_ombre`,
  `tolerance_asphyxie`, `port_trapu`, `germination_thermique`,
  `phenologie_florale`.
- **Fondateurs** : tirés autour de 1,0 avec un écart-type σ = 0,10.
- **Enfant** = moyenne des deux parents + **mutation** gaussienne σ = 0,05
  (`sim/reproduction.py:child_genes`), réduite en autofécondation, bornée à
  [0,4 ; 1,6].
- **Banque de graines du sol** : par parcelle de sol et par espèce, une moyenne et
  une variance de chaque gène (`GeneStat`) ; une graine qui lève y est tirée.
- **Plasticité** (6 gènes « adaptogènes ») : le stress vécu fait monter
  l'expression du gène (jusqu'à ×1,30), avec un coût en croissance et une
  transmission atténuée à la graine (épigénétique maternelle).
- **Effet** : le plus souvent un **multiplicateur** d'un dégât ou d'un seuil
  (`1/gène`). Deux gènes seulement sont lus en **°C** : `germination_thermique`
  (3,5 °C par unité de gène) et `phenologie_florale` (forçage thermique).

**Pourquoi l'impact paraît faible.** Un facteur 0,8 sur un dégât qui arrive
rarement (le gel ne touche que les semis) ne change presque jamais l'issue. Et un
facteur sans unité ne se lit pas : « rusticité 1,12 » ne dit rien au joueur, alors
que « tient jusqu'à −4 °C » dit tout.

## 2. Ce que dit la réalité

### 2.1 Les caractères qui comptent sont quantitatifs
Résistance au froid, date de floraison, taille, tolérance à la sécheresse : ces
caractères dépendent de **dizaines à centaines de gènes** aux petits effets qui
s'additionnent. On ne les modélise pas gène par gène (Mendel et ses pois lisses
ou ridés, c'est l'exception), mais comme une **valeur continue dans une vraie
unité** (°C, jours, cm). C'est le **modèle infinitésimal** de Fisher (1918), la
base de toute la sélection végétale.

### 2.2 D'où vient la diversité des enfants : le brassage plus que la mutation
Dans la réalité, deux frères diffèrent surtout parce que **chaque parent transmet
une moitié tirée au hasard de ses gènes** (ségrégation et recombinaison), pas à
cause de mutations neuves. Les mutations n'ajoutent qu'un **filet** de variation
par génération, environ mille fois moins que le brassage.

Conséquences du modèle infinitésimal :
- enfant = moyenne des parents + un écart de **brassage**, dont la variance vaut
  la **moitié de la variance génétique de la population** ;
- la diversité se **conserve** tant que la population est grande et se croise ;
- elle **s'érode** sous forte sélection, dans les petites populations (dérive) et
  en **autofécondation**.

Le moteur, lui, utilise une **mutation fixe** (σ = 0,05) comme seule source de
diversité. C'est la plus grosse différence avec le réel.

### 2.3 Autogames et allogames
- **Autogames** (tomate, basilic en partie, laitue, haricot, pois) : la plante se
  féconde elle-même. En quelques générations, une **lignée se fixe** : les frères
  deviennent presque identiques, la diversité est **entre** lignées. C'est pour ça
  qu'on peut garder une variété de tomate de grand-mère pure.
- **Allogames** (courges, choux, maïs, carotte, la plupart des sauvages) : le
  pollen voyage, les lignées se **mélangent**, la diversité reste **dans** la
  population. Garder une courge pure est difficile.

Le moteur connaît déjà `pollination_mode` (`self`, `insect`, `wind`) : c'est le
bon levier.

### 2.4 Phénotype = génotype + milieu, et ce qui s'hérite
Une plante est le produit de ses gènes **et** de ce qu'elle a vécu. La part de la
variation transmise aux enfants s'appelle l'**héritabilité** (h², de 0 à 1).
Ordres de grandeur publiés [fourchettes de littérature, variables selon espèce et
milieu] : date de floraison 0,5-0,9 ; tolérance au gel 0,3-0,6 ; rendement 0,1-0,3.

L'**équation du sélectionneur** : gain par génération R = h² × S, où S est l'écart
entre les parents qui se reproduisent et la moyenne. Le moteur n'a pas besoin de
calculer R : il **émerge** si les survivants font plus de graines.

### 2.5 L'ampleur réelle des différences
Ordres de grandeur [littérature, non revérifiés espèce par espèce — à recouper au
tableau des niches] :
- **gel létal** : entre populations d'une même espèce, plusieurs °C, jusqu'à
  ~7 °C chez *Arabidopsis* (de −4 à −11 °C après endurcissement) ;
- **endurcissement** (plasticité) : une plante rustique gagne 5 à 10 °C de
  tolérance en quelques semaines de froid doux ;
- **froid sans gel** chez les tropicales : de 2 à 4 °C entre variétés ;
- **adaptation locale** : sous sélection forte, une population se décale
  nettement en **5 à 20 générations** (variétés paysannes, « graines du lieu »).

Avec σ = 0,10 et 3,5 °C par unité, la diversité fondatrice actuelle de
`germination_thermique` vaut ±0,35 °C (un écart-type) : c'est **dix fois trop
petit** pour le gel létal.

### 2.6 Rien n'est gratuit : les compromis
Un gène qui aide quelque part coûte ailleurs (**pléiotropie**). Les compromis les
mieux documentés :
- résistance au froid ↔ croissance plus lente (sucres et protéines antigel) ;
- floraison précoce ↔ plante plus petite, moins de graines ;
- défense ↔ croissance (déjà dans le moteur, via la plasticité).
Sans compromis, la sélection pousse tout au maximum et la diversité meurt :
c'est le compromis qui fait coexister des lignées différentes (philo #7).

### 2.7 Le cycle de vie est lui aussi inscrit dans la plante
Une annuelle ne meurt pas « parce que c'est l'hiver ». Elle meurt soit parce que
le **froid** dépasse sa limite, soit par **sénescence programmée** une fois ses
graines mûres : la plante vide ses feuilles au profit des fruits, puis s'éteint.
Une mâche ou un mouron passent l'hiver parce que leur limite de froid est basse.
Une bisannuelle fleurit après un hiver (vernalisation), puis meurt. Les morts
naturelles (vieillesse, froid, chaleur, maladie, sécheresse) sont des **seuils de
la plante** franchis par le **milieu** : le moteur ne tue pas, il constate.

### 2.8 La chaleur aussi a une limite
- **Photosynthèse** : elle baisse au-delà de ~30-35 °C chez la plupart des plantes
  de nos climats (plantes en C3), et la plante cesse de croître.
- **Fertilité** : le pollen de tomate devient stérile au-dessus de ~32-35 °C :
  fleurs mais pas de fruits pendant une canicule.
- **Brûlure (échaudage)** : une feuille en plein soleil peut être **10 à 15 °C plus
  chaude que l'air** quand elle ne transpire plus, c'est-à-dire quand la plante a
  soif et ferme ses stomates. Les tissus meurent vers 45-50 °C. Oui, les plantes
  **grillent au soleil**, surtout assoiffées. Une plante bien arrosée se
  refroidit en transpirant.
- **Dormance estivale** : certaines plantes (pâturin, coquelicot, plantes
  méditerranéennes) se mettent en veille par la chaleur.
Couplage naturel : **chaleur × sécheresse × soleil**. Un coin ombragé et paillé
garde ses plantes vertes pendant la canicule. C'est le milieu qui protège (philo #1).

## 3. Écart moteur ↔ réalité (synthèse)

| Point | Moteur | Réalité |
|---|---|---|
| Unité | facteur ~1,0 | °C, jours, cm |
| Source de diversité | mutation σ fixe | brassage (½ variance de la population) + filet de mutation |
| Autogamie | σ réduit | la lignée se fixe en quelques générations |
| Ampleur | ±0,35 °C (σ fondateur, germination) | plusieurs °C (gel), 2-4 °C (froid sans gel) |
| Compromis | défense ↔ croissance seulement | froid ↔ croissance, précocité ↔ taille… |
| Mort des annuelles | calendrier (sem. 49-52) | froid ou sénescence après graines |
| Chaleur | aucun gène | photosynthèse, stérilité, brûlure, dormance |

## 4. Trois options de refonte

**A — Minimale.** On garde le moteur génétique tel quel. Les seuls gènes
thermiques sont lus en °C avec un fort coefficient. *Simple, mais la mutation
fixe reste irréaliste : la diversité ne dépend ni de la population ni de
l'autogamie.*

**B — Modèle infinitésimal (ma reco).** Chaque caractère est une valeur en
**vraie unité** (°C, jours, cm), avec une valeur moyenne d'espèce et une diversité
d'espèce réaliste. Un enfant = moyenne des parents + **brassage** (dont la variance
est la moitié de celle des parents, réduite par l'autofécondation) + un **filet**
de mutation. La banque de graines `GeneStat` porte déjà moyenne et variance : elle
s'y prête directement. On ajoute les **compromis** documentés (§2.6).
*Déterministe (hash), lisible (« −4 °C »), et la diversité émerge de la
population : une lignée de tomate se fixe, une courge reste bigarrée.*

**C — Mendélien par locus** (allèles, dominance, diploïdie). Le plus réaliste à
l'échelle du gène, mais lourd, illisible pour le joueur, et sans gain visible sur
des caractères polygéniques. *Écarté.*

## 5. Coût de calcul d'un gène
Mesuré sur le smoke test (2 tuiles × 4 ans, profilage cProfile, le 2026-11-16) :
tout ce qui touche aux gènes (lecture, expression, enfants, banque) coûte
**~0,13 s sur 13,1 s, soit ~1 % [smoke, 10 gènes, profilage qui gonfle les petits
appels]**, donc ~0,1 % par gène [même mesure].
Un gène coûte peu à **porter**. Ce qui coûte, c'est ce qui le **lit** à chaque tick
pour chaque plante : un test de seuil en °C est négligeable ; une boucle sur toute
la grille ne l'est pas. La mémoire vive n'est pas un sujet (un nombre par gène et
par plante, plus moyenne et variance par parcelle de sol et par espèce).

## 6. Ce que le joueur en verrait
- Des **lignées** : les graines récoltées sur les basilics qui ont tenu jusqu'en
  octobre donnent, d'année en année, un basilic du lieu un peu plus robuste.
- Des **variétés qui se fixent** (tomate) et d'autres qui se mélangent (courge).
- Au survol (touche G), une fois le palier de maîtrise atteint : « tient jusqu'à
  −3 °C », « souffre au-dessus de 32 °C », plutôt qu'un facteur.
- Des **compromis** visibles : la lignée rustique pousse un peu moins vite.
