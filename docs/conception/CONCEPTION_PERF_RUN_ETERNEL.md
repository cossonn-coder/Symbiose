# CONCEPTION — Stabilisation des performances en run éternel

> Figé le 2026-07-05 (`/conception`). Sprint `sprint_perf_run_eternel`, 4 tronçons.
> Source de vérité = moteur Python `data/code/`. Golden = `tests/test_golden.py`.

## 1. Problème

Le monde complet (8 tuiles + maison + vie macro) ralentit énormément au fil des
années — turbo ~0,8 jour/s à la 5e année — puis **plante**. Mesures (Nico, profil
inline borné) :

- 8 tuiles : an1 s26 = 3088 ms/tick (360 plantes, 1254 segments) → an1 s52 = 6869 ms/tick
  (534 plantes, 2771 segments). Le tick **double en une demi-année**.
- 2 tuiles / 6 ans : plantes 30→120, ms/tick 210→600 ; segments PAR plante plafonnés
  (~40, `_elaguer`) ; RSS tracemalloc croît linéairement 0,4→6,2 Mo.

**Enjeu de design (philo #4).** « Run éternel » = un jardin unique à horizon
**infini**. Le coût (CPU + mémoire) doit rester **borné** quand le temps → ∞. Un moteur
dont le coût croît avec l'âge du jardin est incompatible avec la promesse du jeu.

## 2. Diagnostic (investigation lecture seule)

Trois moteurs de la dérive :

**(M1) Population non bornée globalement — cause racine.** Le verrou d'occupation a été
délibérément retiré au sprint « compétition intra-plot » (`sim/succession.py:86-92`,
décision Q1/Q4) : un grain lève même sur plot occupé, la cohabitation étant décidée par
les champs réels. Le recrutement féral n'est plus freiné que par `niche_index`
(lumière-sol + densité racinaire) et `couverture_sol` (`succession.py:217`).
Reproduction et ramets clonaux (déjà gatés couverture) ajoutent aussi. Le frein émergent
**existe des deux côtés** — recrutement (couvert dense étouffe les adventices) et
mortalité (self-thinning par `shade_stress_damage`) — mais **trop faible pour
équilibrer** : recrutement > mortalité → N croît chaque année.

**(M2) LightField super-linéaire** (`fields/light.py`, ~53 % CPU, dette D32). La boucle
« lumière reçue par plante » (l.240-263) est **O(N²)** au pire : chaque plante parcourt
ses voisins plus hauts (tri décroissant + break). Le scatter lumière-sol coûte ∝ plantes
× taille de canopée. Rétroaction avec M1 : plus de plantes → plus cher, et N grandit.

**(M3) Mémoire — pas de fuite « smoking gun » en lecture.** Le `log` est purgé
(`tools/simserver/commands.py:156`), le journal des voix est FIFO borné
(`sim/journal.py`, 200), la seedbank est bornée (plots × ≤27 espèces × gènes), les
squelettes ligneux sont retirés à bois épuisé (`sim/engine/decompo.py:71`). La croissance
RSS est **plausiblement** l'accumulation d'objets plantes/squelettes (chacun porte
segments + genes + expression) + le remplissage des dicts seedbank par plot. « Indépendant
des plantes » (Nico) reste **une hypothèse à PROUVER** → tronçon ① = profileur par
catégorie. On ne corrige pas une fuite non nommée.

## 3. Décision : réécrire le moteur en C / C++ / C# ? → NON

Le problème est **algorithmique** (N non borné + O(N²) lumière), pas la vitesse du
langage. Une réécriture en C donnerait ~30-50× de **constante** mais **ne change pas
l'asymptote** : un O(N²) sur N croissant explose en C aussi, juste quelques années plus
tard. Or « run éternel » = horizon infini → **seul l'asymptote compte** ; la constante ne
fait que reculer le mur.

Coûts d'une réécriture intégrale : jette l'invariant « Python = source de vérité »
(CLAUDE.md), casse Option B (Godot = vue), tue l'itération design rapide (le workflow
`/conception`→`/sprint-auto` vit en Python), et devrait préserver le golden **bit-à-bit**
— or le déterminisme flottant inter-langage est très difficile à garantir.

**Ordre de ROI retenu (Nico, 2026-07-05)** : (1) borner N + cache/LOD lumière **en
Python** → corrige l'asymptote, préserve tout ; (2) numpy en **réserve** si une constante
manque encore pour le 20×20 ; (3) noyau **Cython/C** pour la SEULE fonction chaude
`_point_in_capsule` en **dernier recours**. Jamais de port intégral ; pas de C# (rouvrirait
la divergence Python/C# D10).

## 4. Volet bio à ÉTUDIER — la capacité de charge émergente

> Pour Nico : ce §4 est un **doc à étudier**, pas des questions à trancher. Il explique
> le mécanisme écologique qui doit BORNER la population **naturellement**, sans plafond
> arbitraire (philo #2 : flux → contrainte → réponse émergente ; #7 : hétérogénéité).

### 4.1 Le principe : l'auto-éclaircie (self-thinning)

En écologie végétale, une population dense **s'auto-éclaircit**. À mesure que les
individus grandissent, ils se disputent la lumière, l'eau et les nutriments : les plus
faibles meurent, la densité **plafonne**. C'est la *loi d'auto-éclaircie de −3/2* (Yoda,
1963) : dans un peuplement qui pousse, le produit `densité × biomasse^(3/2)` reste
constant — moins d'individus, mais plus gros, jusqu'à une **capacité de charge** propre
au milieu. Un sol riche et lumineux porte plus de biomasse (plateau haut) ; un sol pauvre
ou ombragé, moins (plateau bas). D'où : **la densité d'équilibre varie par tuile** —
c'est exactement l'hétérogénéité persistante voulue (#7).

### 4.2 Ce qui existe déjà dans le moteur (les deux freins)

- **Frein au recrutement** : `couverture_sol` (champ scalaire des empreintes des plantes
  basses) supprime la germination des adventices au-dessus d'un seuil
  (`succession.py:217`, « couvert dense étouffe les adventices »). C'est le mécanisme par
  lequel un tapis établi empêche de nouvelles levées — flux (ombre au sol) → contrainte
  (pas de fenêtre de germination) → réponse (la graine attend).
- **Frein par la mortalité** : le self-thinning est porté par la voie de **mort par stress
  chronique d'ombre** (`shade_stress_damage`, sprint « mort par stress ») : une plante
  durablement sous-éclairée (car dominée par des voisines) accumule du stress et finit par
  mourir. Flux (lumière reçue faible) → contrainte (déficit photosynthétique chronique) →
  réponse (sénescence puis mort du dominé).

**Le problème n'est donc pas d'inventer un mécanisme, mais de CALIBRER** : aujourd'hui le
recrutement l'emporte sur la mortalité, la population ne plafonne pas. Le tronçon ③
**resserre les deux vis** jusqu'à ce que, sur une tuile donnée, `recrutement = mortalité`
à une densité d'équilibre — un plateau, pas une croissance sans fin.

### 4.3 Ce qui est philo-compatible (et ce qui ne l'est pas)

- ✅ Rendre la **suppression de germination** par la couverture plus mordante (seuil plus
  bas ou réponse plus raide) = agir sur le MILIEU (le couvert), pas sur la plante.
- ✅ Rendre la **mort par stress chronique** plus sensible à la privation de lumière/eau
  quand le voisinage est dense = flux → contrainte → réponse, aucun malus direct.
- ❌ Un « −1 santé si trop de voisins » = terme direct sur la plante, VIOLE #2. Interdit.

### 4.4 Le backstop de sécurité (hors gameplay)

Malgré l'équilibre émergent, un cas pathologique (bug, réglage extrême) pourrait échapper
au plateau et faire exploser N → crash. On pose donc un **cap dur PUR-perf** par tuile,
placé **très au-dessus** de la densité d'équilibre écologique (ex. 3-5× le plateau
observé). Il ne se déclenche **jamais en jeu normal** : c'est un disjoncteur, pas une règle
de gameplay. S'il fire, c'est le signe d'un déséquilibre à corriger (log debug), pas une
mécanique visible pour le joueur. Distinction explicite avec le plafond arbitraire rejeté
au §4.3 : ici on ne SCULPTE pas la population, on l'empêche seulement de diverger.

## 5. Leviers perf (chiffrage indicatif, à mesurer en ②)

- **Spatial hash / partition des plantes** (bucket par plot-foyer) : la boucle « lumière
  reçue » ne visite plus que les plantes dont la capsule PEUT couvrir l'échantillon → de
  O(N²) à ~O(N·k), k = voisins locaux. À densité constante par surface, k est borné → coût
  **linéaire** en N. Gain attendu : dominant à haute densité (le régime qui plante).
  **Bit-identique** : on visite le même sous-ensemble couvrant, dans le même ordre
  hauteur-décroissante → produit flottant inchangé (golden intact, comme D32).
- **Cache géométrique LightField** : la lumière ne change qu'à la croissance (hebdo). En
  **temps figé** (phase planification), la géométrie est stable → le champ est réutilisable
  tel quel (recompute évité). Gain : le tick de planification devient quasi gratuit côté
  lumière. Neutre pour le golden (qui recalcule chaque semaine de toute façon).
- **Borner N** (③) : coupe l'asymptote à la racine — le meilleur levier long terme.
- **Réserve** : numpy-vectoriser le scatter (constante ×10-50, mais l'ordre de sommation
  float peut casser le bit-à-bit → à réserver au non-golden) ; noyau Cython de
  `_point_in_capsule`. Activés seulement si (spatial hash + cache + N borné) ne suffisent
  pas pour le 20×20.

## 6. Découpage en tronçons (perf-first, golden-gaté, vue en dernier)

| # | Tronçon | Golden | Fichiers cœur |
|---|---------|--------|---------------|
| ① | Profileur mémoire par catégorie + colmatage des accumulateurs indépendants de N | INTACT | `tools/profile_memoire.py` (+ bornage ciblé si fuite trouvée) |
| ② | Spatial LOD LightField (bit-identique) + cache géométrique temps figé | INTACT | `fields/light.py` |
| ③ | Capacité de charge émergente (couverture→germination + self-thinning) + backstop sécurité | RE-FIGÉ maîtrisé annoncé | `sim/succession.py`, voie stress chronique, cap tuile |
| ④ | Vue Godot — banc d'observation perf (compteur debug ms/tick·N·RSS + banc F5 longue durée) | INTACT | `visuals/`, pont snapshot |

**Ordre `/sprint-auto`** : ① → ② → ③ → ④. ① prouve la mémoire (le crash) avant tout
correctif ; ② rend la lumière bon marché bit-à-bit ; ③ borne N (re-fige) ; ④ donne l'œil
pour observer la stabilisation.

## 7. Garde-fous du sprint

- **Déterminisme absolu** (#3) : aucun RNG vivant introduit ; ordre d'itération préservé.
- **Golden** : ①②④ doivent le laisser **bit-identique** (sinon = bug, pas re-figeage). ③
  seul re-fige, de façon **localisée et annoncée** (le self-thinning peut mordre dans la
  fenêtre 2 tuiles × 4 ans).
- **Ne JAMAIS lancer `test_epaisseur_500ans`** (long, inutile — mémoire projet).
- **Taille fichiers** : `profile_memoire.py` et les ajouts `light.py` restent sous la
  bande (≤300 LDC pur, `tools/compte_ldc.py`) ; scinder sinon.
- **Python source de vérité** : toute la stabilisation vit en Python. La vue ④ ne fait
  qu'OBSERVER (snapshot lecture seule), elle n'ajoute aucune règle.
