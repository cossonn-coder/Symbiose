# Conception — JARDIN VIVANT (sprint A : plantes, vent, météo)

> Figée le 2026-10-15 avec Nico (`/conception`). Cap parent :
> [`conception_rendu_pixelart.md`](conception_rendu_pixelart.md) (SS① SubViewport
> 960×540 ×2 + iso 2:1, SS② palette — clos). Sprint :
> `sprints/rendu/pixelart/sprint_jardin_vivant/`. Pure VUE (+ un export de pont) :
> **golden jamais touché, zéro coût de tick moteur.**

## 1. Objectif fini

Un jardin **beau et jouable** pour amis/famille, style **mignon SNES** (Chrono
Trigger / Final Fantasy VI). Sprint A = palette + curseur + plantes pré-cuites +
vent + météo. Sprint B (ultérieur) = faune (D44) + champignons + ambiance
(fumée de cheminée hivernale, eau qui scintille), qui **réutilise** la
pré-cuisson du sprint A.

## 2. Principes arrêtés

1. **L'animation est un SIGNAL d'état, jamais un décor gratuit.** Rien ne bouge
   par défaut. Calme + grand beau ⇒ jardin quasi immobile. Chaque animation est
   déclenchée par un état de la simulation (vent, pluie, gel…). C'est la philo
   #5 (indices biologiques visuels) appliquée au mouvement : ce qui bouge
   *informe*.
2. **Dessiner juste.** La couleur des feuilles suit **le calendrier de chaque
   plante** (rampe `automne` ∈ [0,1] exportée par plante — pas la saison
   globale : deux pommiers voisins ne roussissent pas le même jour, sprint
   désync phénologie). Chaque fleur garde la forme de sa famille et la couleur
   de son espèce (`PlantRenderer.Flower.cs` + `OrganPalette.Flower`, existants).
3. **Sprites 100 % procéduraux, PAR INSTANCE.** Chaque plante est cuite depuis
   SES segments réels (son port, son étiolement, ses symptômes) — jamais un
   modèle commun à l'espèce. Le dessin vectoriel actuel de `PlantRenderer` est
   **réutilisé tel quel** comme « pinceau » de la cuisson.
4. **Palette SNES** : ~32 couleurs maîtres + **tramage ordonné (Bayer)** léger,
   appliqué par un shader de quantification sur le SubViewport pixel-art
   (100 % de l'écran conforme ; étiquettes nettes hors SubViewport non
   concernées).

## 3. Pré-cuisson des plantes (cœur technique)

**Pédagogie (analogie embarqué)** : aujourd'hui `PlantRenderer._Draw()`
recalcule le dessin vectoriel de la plante à chaque redessin — c'est un calcul
à chaque appel. Pré-cuire = faire ce dessin **une fois dans une image** (une
table précalculée en RAM), puis seulement l'afficher. Animer revient alors à
choisir **quelle image** afficher, ce qui ne coûte presque rien.

- **8 poses par plante = 8 degrés de FLEXION** (0 = droite → 7 = couchée sous
  le vent), pas 8 images par seconde. La flexion courbe les segments
  progressivement (peu au collet, fort à l'apex), dans la direction du vent
  **projetée à l'écran**.
- **Re-cuisson uniquement quand ce qui est dessiné change** : croissance (tick),
  `automne`, `floraison`, symptômes, vitalité, mort, palier de zoom, ou dérive
  de la direction du vent au-delà d'un seuil angulaire.
- **JAMAIS toutes les plantes au même moment** (exigence Nico) : file de
  re-cuisson à **budget par image affichée** (N plantes ou X ms par frame),
  plantes **visibles à l'écran d'abord**. Une semaine simulée (60 s) fait
  pousser tout le jardin → la file s'étale sur ~1-2 s, invisible au joueur.
  Pendant l'attente, la plante garde son ancienne image (jamais de trou).
- **Coût estimé** : ~20 Mo [estimation non mesurée, ~300 herbacées + ~10 arbres
  supposés] → **à mesurer au T2**, chiffres réels gravés dans `00_etat.md`.

## 4. Vent en onde

`flexion(plante, t) = raideur × force_locale × enveloppe(phase)` avec
`phase = (position · direction_vent) / λ − ω·t`.

- **Onde cohérente qui APPUIE** : un front traverse le jardin dans le sens du
  vent et couche les plantes les unes après les autres. Enveloppe **asymétrique**
  (montée rapide = la poussée, retour lent = la plante se relève) + une
  composante de fond ∝ force (sous vent soutenu les plantes restent penchées).
- **Désynchronisation naturelle** : chaque plante change de pose quand l'onde
  l'atteint, donc à son propre instant. S'y ajoute un **petit balancement
  propre** à chaque plante, phase = hash déterministe de son id, amplitude ∝
  force (nulle sans vent).
- **Raideur par port** : arbre/ligneux plie peu et en retard (déphasage ∝
  hauteur) ; herbacée plie fort et tout de suite.
- **Hétérogénéité (D104, philo #7)** : la force LOCALE vient de l'abri
  (`fields/abri.py`, `eco.vent`) quand il est calculé — une plante derrière la
  haie ou la maison bouge moins. Sinon, masse d'air uniforme (`sim.wind.wind_at`).
- **Pont** : le snapshot n'exporte aujourd'hui ni direction ni force. On ajoute
  `weather.wind = {force, direction}` (lecture pure de `wind_at`, golden
  neutre : le golden hache le log moteur, pas le snapshot) + facteur local par
  plante si disponible sans forcer le calcul d'un champ LAZY.

## 5. Météo animée

Deux couches, trois temps (avant → pendant → après/traces) :
- **Ciel** (global) : `WeatherLayer.cs` existant (voile, pluie/neige/grêle,
  stries de tempête) → reharmonisé à la palette et à l'onde de vent (la pluie
  s'incline selon la vraie direction).
- **Réponse par plante** (hétérogène, D104) lue dans `leaf_symptoms`
  (`sim/semiologie.py`) : canicule = feuilles qui pendent/se ferment
  (variante de pose cuite) ; pluie/orage = gouttes qui alourdissent ; neige =
  charge blanche sur la canopée (`SnowLayer.cs` existant) ; grêle/gel = traces
  qui persistent après l'épisode.
- **Ordre** : vent → canicule → pluie/orage → neige → grêle/gel.

## 6. Vérification

- **T0 = banc de capture sur la VM** : Godot 4.6 .NET portable + Xvfb +
  rendu logiciel llvmpipe (projet en `gl_compatibility`) + Movie Maker → PNG
  qu'**un agent peut regarder** (outil Read). Sert à attraper les erreurs
  AVANT le F5 ; le F5 de Nico ne juge plus que le ressenti.
- Chaque tronçon = **une seule question F5** : « c'est mieux ? ».
- Calibrage prouvé par **mesure** (images, ms/frame, Mo), pas par F5.

## 7. Hors périmètre (sprint B ou plus tard)

Sprites faune (D44 b), champignons/carpophores, fumée de cheminée hivernale,
scintillement de l'eau, sol craquelé, thème UI (D54), sol/tuiles (D34),
pommier pré-âgé (D105).
