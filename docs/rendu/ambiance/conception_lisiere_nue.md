# Conception LISIÈRE NUE (D124) — branches d'hiver, fleurs en colonies, butineurs de bord

Figée le 2026-11-02 avec Nico. Sprint : `sprints/rendu/ambiance/sprint_lisiere_nue/`.

## 1. Retours de Nico (F5 AUTOMNE VISIBLE, 2026-11-02)

- « il manque les branches aux arbres de la lisière après que les feuilles soient tombées » ;
- « les marguerites sont trop en quadrillage, il y en a partout dans la lisière tout autour de la maison » ;
- les fleurs restent, « tant que ça semble réaliste », et « les pollinisateurs peuvent y manger » ;
- cadence jugée ok, « restons vigilants ».

## 2. Causes vérifiées (code et captures `smoke` banc décor, ×0,5, s20 et s46, seed 42, VM)

- **Arbres** : `DrawArbreKit` pose tronc + enveloppe + bouquets. Le tronc s'arrête au bas du houppier : pieux en hiver,
  plus des blocs résiduels (`DEGARNI_MAX` = 0,85, trous par cellules de 4 px).
- **Fleurs** : `ChoisirPiece` tire 9 % des touffes de prairie (5 % en friche), partout à densité égale. Au printemps, le
  shader ajoute une vraie grille (`ip.x % 6 == 3 && ip.y % 4 == 2`).
- **Damier** : `DrawAssise` teinte des parcelles rectangulaires de 120 × 200 cm, très lisibles à ×0,5.
- **Moteur** : `_make_nectar_grid` ne lit que les plantes de la tuile ; les fleurs de lisière ne nourrissent personne.

## 3. Le modèle

### 3.1 Colonies de fleurs : vérité moteur

Les prairies de bord sont un réservoir réel de pollinisateurs. Les colonies vivent donc en Python, et la vue les peint.

- **Géométrie** : fonction pure de (seed, côté, type du secteur). Quelques taches irrégulières de plusieurs mètres par
  secteur, de grands vides entre elles. Prairie : plusieurs ; friche : peu ; rivière : rares ; forêt et falaise : aucune.
- **Une couleur par tache** : marguerite (blanc, Asteraceae) ou bouton d'or (jaune, Ranunculaceae).
- **Floraison** [ordres de grandeur de mémoire, non sourcés] : bouton d'or avril-juin, marguerite fin avril-juillet, plus rien
  en fin d'été. La semaine 1 = équinoxe de printemps (`calendrier.py`).
- **Pas d'espèce au catalogue** : c'est un milieu, comme l'effet de lisière. Pas de graines ni de voix narrative.

### 3.2 Les butineurs y mangent

Grille statique de proximité aux colonies (patron `maj_lisiere` : mémoïsée, `None` sans ceinture), multipliée par un
scalaire de floraison de la semaine et par le goût de chaque type (`attractivite`), ajoutée à la ressource des pollinisateurs.
Philo #2 : un flux de nourriture, la population répond. Effet attendu : population présente dès l'an 1, sans population de
départ imposée, ce qui répond à D119 (c) si la mesure le confirme.

### 3.3 Butineurs visibles sur les colonies

Le pont donne un compte par colonie, dérivé de la population réelle du bord et borné. La vue les fait voler dans le patron
de `ForagerLayer` (horloge + hash, aucun état). Pas de colonie en fleur : aucun insecte.

### 3.4 Branches

Posées dans `DrawArbreKit` AVANT l'enveloppe. L'été le houppier les cache ; le dégarnissement du shader les révèle, sans
aucune logique de saison. Axe prolongé dans la couronne, 3-5 charpentières selon le port, rameaux seulement si `DetailsVisibles`.
Sapins exclus. Classe `ClasseSansSaison` : neige et givre s'y posent.

### 3.5 Couronne d'hiver réaliste (marcescence)

Hêtre, charme et chêne gardent quelques feuilles sèches, surtout en bas de couronne, en petites touches rousses ; le bouleau
est nu. Le shader connaît déjà l'id de palette de chaque texel de bouquet, et `hauteur` : une comparaison suffit, sans donnée
de plus. L'enveloppe (id variable, `SourceCouleur` × `mod`) disparaît en plein hiver. [Réalisme de mémoire, non sourcé.]

### 3.6 Damier

Parcelles de l'assise : limites données par un bruit basse fréquence au lieu de blocs rectangulaires, mêmes sommets.

## 4. Limites assumées

- Les colonies ne se déplacent pas et ne réagissent pas aux gestes du joueur.
- Effet indirect possible : plus de pollinisation, donc plus de graines et de plantes. À mesurer au ① (cadence, vigilance de Nico).

## 5. Budgets

- Tick an 2 de `full` ≤ +10 %, plantes an 3 comparées à avant, sur 3 ans de jeu maximum.
- Draw calls constants ; décor reconstruit seulement au changement de palier ou de ceinture, jamais par semaine.
