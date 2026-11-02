# Fiches morphologiques des 11 arbres

Sprint AUTOMNE VISIBLE ①. Référence de ce que chaque arbre de `PERENNIAL_CATALOGUE` **devrait être** ;
ce qu'il **est** aujourd'hui : `sprints/rendu/ambiance/sprint_automne_visible/mesures/avant.md`.
Se traduit au ② en paramètres moteur, au ④ en recette de sprite.

## Lire ces fiches

- **Réel** : sujet isolé, sol correct, climat normand. Ces fourchettes sont des ordres de grandeur
  de mémoire d'arboriculture, sans source vérifiée ligne à ligne ; chacune le porte par `[odg]`.
  Elles servent à donner une allure, pas à calibrer une loi.
- **Dates d'automne** : un pic de couleur et une chute ordinaires, `[odg]` eux aussi (±2 semaines selon
  l'année). Converties en semaine de jeu `sN` par la table de `data/code/calendrier.py` (1ᵉʳ oct = s29,
  1ᵉʳ nov = s33, 1ᵉʳ déc = s37).
- **Cibles à 10 ans** : hauteur et rayon de couronne que le ② doit viser au banc `bancs/mesure_arbres`.
  Ce sont des choix de jeu, pas des mesures ; `[choix]` le rappelle.
- **Échelle** : le monde fait 20×20 m avec une maison de 8×8 m. Un chêne centenaire réel n'y tient pas.
  Les arbres du jeu restent donc à l'échelle du jardin, et chaque écart est écrit dans sa fiche.
- **Archétype de port** : le mot visé par le joueur et par le rendu. `port_archetype` n'est lu par aucun
  code aujourd'hui (descriptif, `plants/base/familles.py`) : le port doit naître des paramètres de
  croissance, le mot seul ne change rien.

## Pommier — `AppleTree` (*Malus domestica*)

- **Port** : petit arbre étalé, tête arrondie, charpentières basses et noueuses, souvent aussi large que haut.
- **Réel** : 10 ans 3-5 m de haut, 1,5-2,5 m de rayon `[odg]` ; 30 ans 5-8 m, 3-4 m `[odg]`.
- **Tronc** : court, 1 à 1,5 m avant la fourche ; écorce gris-brun qui s'écaille en plaques.
- **Feuille** : ovale, dentée, alterne, 5-10 cm `[odg]`, duveteuse dessous.
- **Été** : vert moyen un peu terne.
- **Automne** : jaune-brun, sans éclat ; pic fin oct., chute début à fin nov. (s32-36) `[odg]`.
- **Fruit** : pomme ronde de 6-8 cm `[odg]`, verte puis rouge ou jaune, sept.-oct.
- **Floraison** : blanc rosé, en bouquets, avr.-mai, avec les feuilles.
- **Jeu** : archétype `étalé`, cible 10 ans 350 cm de haut, 200 cm de rayon `[choix]`. Des latéraux dès
  ~3-5 ans. **Écart** : pas de porte-greffe ni de taille simulés, un seul gabarit de plein vent.

## Cerisier — `CherryTree` (*Prunus avium*)

- **Port** : tronc droit, branches en étages réguliers, couronne ovoïde qui s'ouvre avec l'âge.
- **Réel** : 10 ans 5-8 m, 2-3 m de rayon `[odg]` ; 30 ans 10-15 m, 4-6 m `[odg]`.
- **Tronc** : droit ; écorce brun-rouge luisante, à bandes horizontales (lenticelles), qui pèle en lanières.
- **Feuille** : ovale pointue, dentée, alterne, pendante, 7-14 cm `[odg]`.
- **Été** : vert franc, assez sombre.
- **Automne** : rouge-orangé vif, le plus flamboyant du jardin ; pic mi-oct., chute fin oct. à mi-nov. (s30-34) `[odg]`.
- **Fruit** : cerise rouge sombre de 2 cm `[odg]`, en grappes pendantes, juin-juil.
- **Floraison** : blanc pur, très dense, avr., avant les feuilles.
- **Jeu** : archétype `ovoïde étagé`, cible 10 ans 500 cm, 250 cm `[choix]`.
  **Écart** : plafonné à 10 m (`max_height_cm`), là où un merisier forestier dépasse 20 m.

## Noyer — `WalnutTree` (*Juglans regia*)

- **Port** : grande tête ronde et large, grosses branches tortueuses, sous-bois clair et vide.
- **Réel** : 10 ans 5-8 m, 3-4 m de rayon `[odg]` ; 30 ans 12-20 m, 6-10 m `[odg]`.
- **Tronc** : massif et court ; écorce gris argent, lisse jeune, crevassée en long avec l'âge.
- **Feuille** : composée, 5-9 folioles, alterne, grande (20-40 cm) `[odg]`, odeur forte au froissé.
- **Été** : vert jaune un peu bronze à la feuillaison, puis vert franc.
- **Automne** : jaune terne virant au brun-noir ; feuille tôt tombée, pic début oct., chute oct. (s29-32) `[odg]`.
- **Fruit** : noix dans un brou vert, sept.-oct., brou noircissant au sol.
- **Floraison** : chatons pendants verts, mai, discrète.
- **Jeu** : archétype `arrondi large`, cible 10 ans 600 cm, 350 cm `[choix]`.
  **Écart** : le gabarit moteur actuel (25 m × 10 m de rayon) dépasse une tuile ; à tenir au ② à l'échelle du jardin.

## Chêne — `OakTree` (*Quercus robur*, choisi ici : la classe ne précise que le genre)

- **Port** : large et tortueux, branches maîtresses coudées, silhouette massive et irrégulière.
- **Réel** : 10 ans 3-5 m, 1,5-2,5 m de rayon `[odg]` ; 30 ans 8-14 m, 4-6 m `[odg]`.
- **Tronc** : court et puissant ; écorce gris-brun profondément crevassée.
- **Feuille** : lobée, base à oreillettes, alterne, groupée en bout de rameau, 7-14 cm `[odg]`.
- **Été** : vert soutenu, mat.
- **Automne** : roux tardif, marcescence partielle des jeunes sujets ; pic début nov., chute nov. à déc. (s34-38) `[odg]`.
- **Fruit** : gland à long pédoncule, cupule, sept.-oct.
- **Floraison** : chatons jaune-vert, avr.-mai, discrète.
- **Jeu** : archétype `étalé tortueux`, cible 10 ans 400 cm, 280 cm `[choix]`.
  **Écart** : plus large et plus rapide que le réel, pour qu'il se lise comme un chêne dès 10 ans.

## Hêtre — `BeechTree` (*Fagus sylvatica*)

- **Port** : ovoïde dense, houppier haut et fermé, branches montantes souples.
- **Réel** : 10 ans 3-5 m, 1,5-2,5 m de rayon `[odg]` ; 30 ans 10-15 m, 4-6 m `[odg]`.
- **Tronc** : droit, lisse, gris clair « peau d'éléphant », sans crevasses.
- **Feuille** : ovale, bord ondulé cilié, alterne, 5-10 cm `[odg]`, en plans horizontaux.
- **Été** : vert frais tendre au printemps, puis vert franc brillant.
- **Automne** : cuivré, marcescent : les jeunes sujets gardent des feuilles sèches tout l'hiver ; pic fin oct., chute nov. (s32-36) `[odg]`.
- **Fruit** : faîne, petite capsule hérissée, sept.-oct.
- **Floraison** : chatons discrets, avr.-mai, avec les feuilles.
- **Jeu** : archétype `ovoïde dense`, cible 10 ans 400 cm, 220 cm `[choix]`.
  **Écart** : marcescence non simulée dans ce sprint (le moteur fait tout tomber ; seule la couleur la suggère).

## Bouleau — `BirchTree` (*Betula pendula*)

- **Port** : élancé et léger, tronc droit, rameaux fins franchement pendants, couronne claire.
- **Réel** : 10 ans 6-9 m, 1,5-2,5 m de rayon `[odg]` ; 30 ans 15-20 m, 3-5 m `[odg]`.
- **Tronc** : mince ; écorce blanche qui pèle, losanges noirs à la base.
- **Feuille** : triangulaire, doublement dentée, alterne, 3-7 cm `[odg]`, très mobile au vent.
- **Été** : vert clair.
- **Automne** : jaune d'or lumineux ; pic mi-oct., chute oct. à début nov. (s30-33) `[odg]`.
- **Fruit** : petit strobile pendant, graines ailées, été-automne.
- **Floraison** : chatons mâles pendants jaunes, avr.
- **Jeu** : archétype `dressé pleureur`, cible 10 ans 750 cm, 180 cm `[choix]`.
  **Écart** : rayon réduit par rapport au moteur actuel (271 cm `[seed 42, sans lumière, VM]`), pour rester un arbre mince.

## Charme — `HornbeamTree` (*Carpinus betulus*)

- **Port** : ovoïde régulier, ramure fine et serrée.
- **Réel** : 10 ans 4-6 m, 2-3 m de rayon `[odg]` ; 30 ans 10-15 m, 4-6 m `[odg]`.
- **Tronc** : sinueux, cannelé, « musclé » ; écorce gris lisse.
- **Feuille** : ovale, nervures marquées et plissées, doublement dentée, alterne, 5-10 cm `[odg]`.
- **Été** : vert franc, assez sombre.
- **Automne** : jaune-roux, marcescence fréquente en haie ; pic fin oct., chute nov. (s32-36) `[odg]`.
- **Fruit** : akène sur bractée trilobée, en grappes pendantes, sept.-oct.
- **Floraison** : chatons verts, avr.-mai.
- **Jeu** : archétype `ovoïde`, cible 10 ans 450 cm, 220 cm `[choix]`.
  **Écart** : pas de haie taillée ici ; le geste `eteter` et le rejet existants restent les seuls liens à la taille.

## Aulne — `Alder` (*Alnus glutinosa*)

- **Port** : conique et dressé, tronc suivi jusqu'à la cime, branches courtes et régulières.
- **Réel** : 10 ans 6-9 m, 1,5-2,5 m de rayon `[odg]` ; 30 ans 15-20 m, 3-4 m `[odg]`.
- **Tronc** : droit, écorce brun sombre, fissurée.
- **Feuille** : ronde à sommet échancré, gluante jeune, alterne, 4-9 cm `[odg]`.
- **Été** : vert sombre lustré.
- **Automne** : **presque aucun changement** : largue encore vert, à peine bruni ; chute nov. à début déc. (s33-37) `[odg]`.
- **Fruit** : petit cône ligneux noir, persistant tout l'hiver.
- **Floraison** : chatons pourpres pendants, févr.-mars, avant les feuilles.
- **Jeu** : archétype `conique`, cible 10 ans 650 cm, 170 cm `[choix]`.
  **Écart** : réservé aux berges du monde de démo ; pas de cépée multi-troncs (collet unique du moteur).

## Saule — `Willow` (*Salix alba*)

- **Port** : grande tête ample et arrondie, rameaux souples aux extrémités retombantes ; pas un saule pleureur.
- **Réel** : 10 ans 8-11 m, 3-4 m de rayon `[odg]` ; 30 ans 15-20 m, 5-8 m `[odg]`.
- **Tronc** : court, écorce gris-brun à crêtes croisées ; rejette de souche (trogne).
- **Feuille** : étroite et lancéolée, alterne, 5-10 cm `[odg]`, dessous argenté soyeux.
- **Été** : vert gris argenté.
- **Automne** : jaune pâle tardif ; pic début nov., chute nov. (s33-37) `[odg]`.
- **Fruit** : petite capsule à graines cotonneuses, mai-juin.
- **Floraison** : chatons jaunes, mars-avr., avec les premières feuilles (précoce pour les butineurs).
- **Jeu** : archétype `arrondi souple`, avec retombée modérée, cible 10 ans 800 cm, 300 cm `[choix]`.
  **Écart** : `gravitropism_gain` 1,4 actuel le rend plus pleureur que le saule blanc ; lisibilité avant fidélité si le F5 le préfère.

## Figuier — `Fig` (*Ficus carica*)

- **Port** : buissonnant, bas et large, grosses branches souples partant de la base.
- **Réel** : 10 ans 3-4 m, 2-3 m de rayon `[odg]` ; 30 ans 5-8 m, 4-5 m `[odg]`.
- **Tronc** : court, souvent plusieurs ; écorce gris clair, lisse.
- **Feuille** : très grande, palmée à 3-5 lobes, rugueuse, alterne, 10-25 cm `[odg]`.
- **Été** : vert sombre mat.
- **Automne** : jaune, feuille qui tombe vite aux premiers froids ; pic fin oct., chute nov. (s32-35) `[odg]`.
- **Fruit** : figue verte à violette, en poire, 4-8 cm `[odg]`, août-oct.
- **Floraison** : invisible, à l'intérieur de la figue (le moteur la place en début d'été).
- **Jeu** : archétype `buissonnant`, cible 10 ans 400 cm, 250 cm `[choix]`.
  **Écart** : tronc unique (collet unique du moteur) ; le multi-tronc reste une option différée.

## Sapin — `FirTree` (*Abies alba*)

- **Port** : conique étroit, tronc suivi, étages de branches horizontales ; seul persistant.
- **Réel** : 10 ans 2-4 m, ~1 m de rayon `[odg]` ; 30 ans 12-15 m, 2-3 m `[odg]`.
- **Tronc** : droit ; écorce gris argent, lisse, écailleuse avec l'âge.
- **Feuille** : aiguille plate, 2-3 cm `[odg]`, en deux rangs, deux bandes blanches dessous.
- **Été** : vert sombre.
- **Automne** : **inchangé**, aucune chute saisonnière.
- **Fruit** : cône dressé qui se désarticule sur l'arbre, automne.
- **Floraison** : discrète, mai-juin.
- **Jeu** : archétype `conique étroit`, cible 10 ans 450 cm, 130 cm `[choix]`.
  **Écart** : pousse deux fois plus vite que le réel à 10 ans, pour peser dans une partie.

## Résumé des cibles

Tout ce tableau est `[choix]` de jeu (hauteur, rayon) et `[odg]` (semaines), recopié des fiches.

| Arbre | Archétype visé | H 10 ans `[choix]` cm | Rayon 10 ans `[choix]` cm | Chute `[odg]` | Couleur d'automne |
|---|---|---|---|---|---|
| Pommier | étalé | 350 | 200 | s32-36 | jaune-brun |
| Cerisier | ovoïde étagé | 500 | 250 | s30-34 | rouge-orangé |
| Noyer | arrondi large | 600 | 350 | s29-32 | jaune terne |
| Chêne | étalé tortueux | 400 | 280 | s34-38 | roux tardif |
| Hêtre | ovoïde dense | 400 | 220 | s32-36 | cuivré, marcescent |
| Bouleau | dressé pleureur | 750 | 180 | s30-33 | jaune d'or |
| Charme | ovoïde | 450 | 220 | s32-36 | jaune-roux |
| Aulne | conique | 650 | 170 | s33-37 | presque vert |
| Saule | arrondi souple | 800 | 300 | s33-37 | jaune pâle |
| Figuier | buissonnant | 400 | 250 | s32-35 | jaune |
| Sapin | conique étroit | 450 | 130 | sans | inchangé |
