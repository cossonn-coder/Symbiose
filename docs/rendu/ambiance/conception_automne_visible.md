# Conception — AUTOMNE VISIBLE et arbres fidèles (D123 + D118 (A) pour les arbres)

Figée le 2026-11-02 avec Nico. Sprint : `sprints/rendu/ambiance/sprint_automne_visible/`.

## 1. Le problème

F5 du 2026-11-02 : « la chute des feuilles en automne est invisible ni dans leur couleur sur
les arbres, ni dans le tapis de feuilles au sol ». Le moteur calcule la phénophase `automne`
et dépose la litière, mais rien n'arrive à l'écran.

Causes vérifiées (monde `full`, seed 42, an 1 [n=1 run, VM + captures]) :

1. **Lisière** : aucune lecture de la saison dans `visuals/DecorLayer*.cs` → verte toute l'année.
2. **Pommier = bâton** : 4 segments, 175 cm au départ. Réglage voulu (`perennials.py` : latéraux
   vers l'an 7) mais démarrage à `maturity_years` = 5. Aulnes = semis de ~1 cm.
3. **Couronne pleine jusqu'à s40** : `foliage_density_at` ne tombe à 0 qu'à `saison == "hiver"`,
   alors que le largage a lieu en s30-36.
4. **Tapis** : toute la masse sur le plot du tronc ; le pont n'exporte que le tissu dominant
   (`feuille` domine 0-3 plots) ; `LeafLitterLayer` MinZoom 2, 6 feuilles max par plot.
5. **Chute** : aucune animation.

Structure des 11 arbres en pré-croissance seule (`pre_croitre`, seed 42, sans lumière ni
concurrence [n=1 par âge, VM]), format segments/hauteur cm/rayon cm :

| Arbre | 5 ans | 10 ans | 15 ans |
|---|---|---|---|
| AppleTree | 4/179/50 | 45/357/187 | 69/271/333 |
| CherryTree | 6/296/140 | 45/588/280 | 70/352/499 |
| WalnutTree | 7/285/160 | 34/569/357 | 70/395/571 |
| OakTree | 4/177/185 | 25/352/286 | 70/329/461 |
| BeechTree | 4/201/140 | 25/401/241 | 70/375/416 |
| BirchTree | 8/383/70 | 37/765/271 | 70/274/305 |
| HornbeamTree | 6/230/100 | 46/457/240 | 67/266/418 |
| Alder | 7/273/50 | 35/544/238 | 70/223/364 |
| Willow | 9/448/60 | 67/896/362 | 70/342/314 |
| Fig | 5/209/95 | 24/418/218 | 80/491/395 |
| FirTree | 4/237/110 | 10/473/131 | 57/708/312 |

Deux défauts lisibles : **la hauteur s'effondre entre 10 et 15 ans** dès que le plafond de
segments est atteint (bouleau 765 → 274 cm : un arbre ne rapetisse pas ; cause non
diagnostiquée, `max_segments` suspect) et **9 caducs sur 10 ont le même `port_archetype`
`etale`**, d'où l'effet « arbre générique » de D118.

## 2. Décisions de Nico

- **A1** Arbres du jardin dans ce sprint ; golden libre de bouger, à annoncer.
- **A2** Les feuilles au sol sont la vérité du MOTEUR.
- **A3** Lisière **4 saisons**, qui affiche aussi les **signes diégétiques macro** (style canicule).
- **A4** De D118, seuls les **11 arbres** sont traités ici ; le reste de D118 (37 plantes, reliquats
  DA, rivière, perf vue) est le sprint suivant.

## 3. Le modèle retenu

### 3.1 Les arbres (fiche → port → recette)
Une **fiche morphologique** par arbre (`docs/vegetal/croissance/fiches_arbres.md`) : port, taille à
10 et 30 ans, forme de couronne, tronc et écorce, feuille, **couleur d'automne propre**, fruit.
Elle se traduit deux fois : en **paramètres moteur** (port, vitesse, branches) et en **recette
de sprite** (palette, couronne). Couleurs d'automne attendues : bouleau jaune d'or, cerisier
rouge-orangé, charme jaune-roux, hêtre cuivré et marcescent, chêne roux tardif, noyer jaune
terne, pommier jaune-brun, figuier jaune, saule jaune pâle, **aulne qui largue presque vert**,
sapin inchangé.

Monde de démo : les ligneux fondateurs de `full`/`propre` démarrent assez âgés pour avoir une
couronne (cible 10-12 ans), plus 2-3 caducs aux couleurs distinctes (bouleau, cerisier, charme),
placés sans ombrer le potager.

### 3.2 Les feuilles au sol (moteur)
Le largage s'étale sur quelques semaines à partir de `semaine_abscission` et se répartit sur
`foliar_plots` (limité à la tuile : pas d'échange inter-tuiles). La masse totale suit la couronne,
pas seulement la hauteur, pour qu'une couronne large fasse un vrai tapis. Le sol sous l'arbre
reçoit donc plus de matière : c'est un effet écologique voulu. Le pont exporte la masse de feuilles
de chaque plot, même quand un autre tissu domine.

### 3.3 La couronne (hint de pont)
Le pont envoie `feuillage ∈ [0,1]` par plante : 1 jusqu'à l'abscission, puis baisse au rythme du
largage. `foliage_density_at` n'est PAS modifiée : la lumière au sol reste réglée sur l'entrée en
hiver. **Limite assumée** : jusqu'à ~10 semaines où l'arbre semble déjà dégarni alors que son ombre
moteur reste celle d'un feuillage plein.

### 3.4 La chute
Un seul calque en lot, hash déterministe, entraîné par le vent réel. Actif seulement quand
`feuillage` baisse, sur les arbres visibles. Philo DA : l'animation signale un état.

### 3.5 La lisière
Teinte par saison, déduite de `week_in_year`, décalée par pied au hash (pas de bascule d'un
coup) : printemps vert tendre et fleurs de prairie, été comme aujourd'hui, automne jaune → roux
puis dégarni, hiver ternes et clairsemés avec prairie paille. Sapins, roche et eau inchangés.
Elle affiche aussi la météo et les signes du bloc `ciel` : prairie grillée et brume de chaleur
(canicule, sécheresse), brume rasante et givre (gelée), ciel bas et prairie sombre (pluie),
neige (état `snow`). Elle ne montre que ce que le moteur émet : les ~20 % d'événements
imprévisibles le restent. **D107 garde la loi de la canicule** ; ici, seulement ce qu'on voit.

## 4. Philo de design

- **#2** : aucun bonus sur les plantes ; le tapis nourrit le sol par la litière existante.
- **#3** : zéro RNG, tout au hash.
- **#5** : pas de chiffres ni d'icônes ; les saisons et signes se lisent dans le paysage.
- **Pas de nouvelle espèce** : ces arbres existent déjà (`PERENNIAL_CATALOGUE`), pas de voix à écrire.

## 5. Perf

- Moteur : plafonds de segments conservés, ~+100-200 segments dans `full` pour 4 000 en an 2
  [estimation non mesurée, à mesurer au ②] ; budget ≤ +10 % de tick par tronçon.
- Lisière : pas de reconstruction du décor chaque semaine, 1 draw call conservé.
- Chute : un seul CanvasItem, à l'arrêt hors des semaines de chute.
- Le joueur a déjà des à-coups (10,2 s de pire tick [n=1 run, PC]) : tout surcoût se signale.

## 6. Hors périmètre

Annuelles et herbacées du jardin ; reste de D118 ; loi de la canicule (D107) ; effet du
dégarnissement sur la lumière (limite du §3.3) ; à-coups de tick (noté au backlog).
