# CONCEPTION — Rendu pixel-art 16-bits (Chrono Trigger)

> Cap visuel de Symbiose : passer du **rendu vectoriel propre actuel** à un vrai
> **pixel-art 16-bits façon Chrono Trigger**. Conçu le 2026-06-23 à partir de trois
> analyses de papiers (génération procédurale d'arbres 3D, Lane & Prusinkiewicz 2002,
> Runions 2014) + une recherche web rendu pixel-art, toutes confrontées au code.
> **Aucun dev encore** — ce document fige le cap avant tout sous-sprint.

## 0. État des lieux (ce que le code fait VRAIMENT)

- **Sol** : losanges placeholder en **aplats unis** (`WorldView.Monde.cs`, `SoilColor`),
  une couleur par type de sol, **aucune transition** entre types, aucun dégradé.
- **Plantes** (`PlantRenderer.cs` + `.Organs.cs`) : branches `DrawLine` iso, largeur
  ∝ épaisseur ; couleur **binaire** apex-vert / bois-brun (pas de lignification
  progressive) ; feuilles = **ellipses génériques identiques** pour toutes les espèces ;
  fleurs = 5 pétales ; fruits = disque + reflet. Tout en **aplats unis**, LOD silhouette
  à zoom faible, squelette mort gris.
- **Faune** (`MacroLife.cs`) : **disques colorés** par espèce + errance sin/cos.
- **Butineurs** (`ForagerLayer.cs`) : agents sautant de fleur en fleur (plus élaboré).
- **Champignons** : **AUCUN rendu** alors que le moteur décompose/composte → manque net.
- **Racines** : **AUCUN rendu** (souterraines, jamais montrées).
- Contraintes déjà en place ✓ : `default_texture_filter=0` (Nearest), 1920×1080,
  zoom paliers entiers ×4/×8/×16/×32, tout le visuel **déterministe au hash** (zéro Random).

Le problème de fond : c'est du **vectoriel à la résolution écran**, pas des « gros
pixels » cohérents. Et presque tout est en **aplat uni** (une couleur par organe).

## 1. Philosophie & contraintes (non négociables)

1. **Pixel-art SNES** (réf. Chrono Trigger) — Nearest partout, zoom paliers ENTIERS.
2. **Déterminisme total** — toute variation (dithering, placement de feuille, teinte)
   dérive d'un hash/seed, jamais d'un Random (philo design #3). Le code respecte déjà
   cette culture (`Hash01`, `HashKey`).
3. **Indices visuels, pas de chiffres** (philo #5) — le rendu RÉVÈLE l'état écologique
   (santé, maturité, humidité) sans barre ni nombre. Les overlays debug (`FieldOverlay`)
   restent un mode technique séparé.
4. **Philo du naturaliste** — visible mais non identifiable sans maîtrise (faune surtout).
5. **Interconnexion des acteurs** — chaque amélioration relie un acteur aux autres
   (ex. champignons ↔ décomposition du sol).

## 2. Deux couches à ne JAMAIS confondre

La question « améliorer le rendu des plantes » mélange en réalité deux couches :

- **Couche A — géométrie source** (QUELLE forme) : contour de feuille, topologie de
  branches, position des organes. Vit en **Python** (source de vérité, `data/code/`,
  `tools/render_structure.py`). C'est ce que touchent les papiers de morphogenèse.
- **Couche B — pixellisation** (QUELS pixels) : palette, rampes, dithering, autotiling,
  upscale. Vit en **Godot/C#** (`visuals/`, `world/`). C'est le cœur de ce document.

**Discipline (dette D10)** : toute amélioration de forme se prototype d'abord en **SVG
Python** (`tools/render_structure.py`, validé à l'œil), PUIS se porte en C#. Sinon Python
et la vue divergent. Le **golden reste préservé** : le rendu est une vue passive, il ne
touche pas le moteur ; les prototypes `tools/` ne touchent pas la simulation.

## 3. PROJECTION — iso 2:1 CONSERVÉE (le top-down 3/4 a été essayé puis abandonné)

**Décision Nico, 2026-06-23 (matin)** : tenter de basculer l'**iso 2:1** (losange)
vers une **vue top-down 3/4 carrée façon Chrono Trigger**. **Implémenté au SS① puis
REJETÉ le même jour au 1er F5** : la maison et la grille en top-down « ne rendaient
pas bien ». **On garde donc l'iso 2:1 d'avant.** Chrono Trigger reste la référence
**chromatique / pixel** (SS②), pas la projection — c'est la *palette*, pas la *forme*,
qui fait l'identité 16-bit.

**Ce qui est acté techniquement** : la projection (`WorldView.Projection.cs`) reste
l'**iso 2:1 historique** (`((x−y)·PxX, (x+y)·PxY)`, rotation losange). Le « pixel-art »
ne vient PAS de la projection mais du **SubViewport basse-réso** (§4). Seule la
**calibration** a changé : les losanges sont calibrés en pixels **internes** du
SubViewport (**39×19,5** = moitié du plein écran d'avant), et l'upscale ×2 rétablit la
taille à l'écran. L'orientation D35 (rotation par quarts de tour) est préservée.

> Leçon : la centralisation de la projection (D2, « écrite une fois ») a permis de
> faire l'aller-retour top-down → iso en quelques fichiers, sans casser plantes /
> faune / ombres (tout délègue à `WorldToScreen` / `WorldToScreenOffset`).

## 4. Levier ① — SubViewport basse-résolution + upscale ×N

**Le plus gros impact, transversal.** Dessiner toute la scène dans un `SubViewport` à
résolution réduite, puis l'afficher agrandi ×N en `Nearest`. Chaque primitive devient
un bloc de pixels carrés homogènes → **look SNES instantané et unifié**.

> **ACTÉ au SS① (2026-06-23)** : résolution interne **960×540, upscale ×2**
> (`stretch_shrink=2`). Le 480×270 ×4 d'abord essayé était **trop pixellisé** au goût
> de Nico. **Seul le MONDE** passe dans le SubViewport ; **HUD, sélecteur, ambiance
> météo ET étiquettes des plantes restent plein écran (nets)** — choix assumé : le HUD
> de debug doit rester lisible, et le texte upscalé est illisible. L'« UI dans la même
> grille » du SNES est reportée au sprint UI. Piège résolu : le `SubViewportContainer`
> a un parent `Node2D` → ses ancrages ne s'appliquent pas, sa taille est **forcée en
> code** à la fenêtre (sinon il retombe à 2×2 et le monde est invisible).

**Pourquoi en premier** : on obtient le « grain » pixel-art **sans réécrire** les `_Draw`
existants (ils dessinent pareil, dans un canevas qui pixellise). Résout aussi le fait que
les ellipses/cercles actuels ne sont pas alignés à une grille de pixels.

**Pédagogie Godot** : un `SubViewport` est une fenêtre de rendu off-screen ; on y place le
monde, un `Sprite2D`/`TextureRect` l'affiche à l'échelle. C'est le réglage standard
pixel-art sous Godot 4. S'articule avec les paliers de zoom entiers déjà prévus.

**À cadrer** : interaction avec la caméra existante et le picking souris (les coordonnées
passent désormais par l'échelle du viewport).

## 5. Levier ② — Palette : rampes + hue-shifting + lumière du sud

**Fondation chromatique commune à tous les acteurs.** Remplacer chaque aplat
(`WoodColor`, `ApexColor`, chaque feuille, chaque fruit, chaque sol) par une **rampe
2-3 valeurs**. Le soleil est au **sud** dans le moteur (`WorldView.Soleil`, modèle E-O
symétrique) : éclaircir la face sud, assombrir la face nord en **décalant la teinte vers
le froid** (hue-shift) plutôt que vers le noir. C'est *la* signature 16-bit, et la
direction de lumière est déjà disponible.

**Budget palette** : viser une palette globale limitée (~16-32 couleurs, esprit SNES),
partagée entre acteurs pour la cohérence. À fixer au sous-sprint palette.

## 6. Acteur par acteur

### Plantes
- **Branches vertes ↔ ligneuses** : remplacer le binaire `IsApex` vert / bois brun
  (`PlantRenderer.cs:335`) par une **rampe vert-tendre → brun** indexée par `ThicknessCm`
  (ou l'âge du segment si exposé) → lignification progressive, lisible.
- **Feuilles** : aujourd'hui **ellipse générique unique** (`Organs.cs:141`). Cible :
  (a) nervure centrale + bord ombré (volume) ; (b) **silhouette par famille botanique**
  (lancéolée, dentée, composée, ronde) — la famille est connue côté moteur.
  **Réf. Runions 2014** : la morphogenèse fine (auxine/PIN/CUC) est **surdimensionnée** à
  la densité pixel (illisible à ×4/×8). On garde l'IDÉE (forme par famille, qui se
  complexifie avec le stade), on jette la simulation. **3-5 silhouettes paramétrées >
  simulation moléculaire.**
- **Fleurs** : déjà 5 pétales + cœur. Crans : 2 valeurs/pétale + **corolle par famille**
  (ombelle Apiaceae, capitule Asteraceae…).
- **Fruits** : déjà reflet + couleur de maturité (bien). Manque un **croissant d'ombre**
  bas-droite (hue-shift) pour la rondeur.

### Champignons (manque total à combler)
Le moteur décompose/composte (sprint décomposition ①-⑤) mais **rien ne le montre**.
Cible : sprites procéduraux (chapeau + pied, 2-3 valeurs) sur la **litière et le bois
mort**, là où le moteur signale de la décomposition → **relie le visuel à la
décomposition** (règle d'interconnexion).

### Faune
Aujourd'hui **disques colorés** par espèce (`MacroLife`). Cible : **silhouettes par
gabarit/catégorie** (oiseau en V, rampant trapu, volant fin) plutôt qu'un point — mais
**philo naturaliste** : silhouettes génériques au début, qui **s'affinent en sprite
d'espèce à la maîtrise**. La perception progresse avec le savoir.

### Sol & racines
- **Transitions de sol** : **dual-grid autotiling** (5 tuiles, grille graphique décalée
  d'½ plot lisant 4 voisins logiques) au lieu d'aplats tranchés. Se branche sur le
  `t["soil"]` du snapshot. Déterministe.
- **Affichage des champs** : **dithering ordonné (Bayer)** entre deux teintes de palette
  → rend humidité/fertilité en texture de sol **lisible sans HUD chiffré** (philo #5),
  alternative diégétique aux heatmaps debug.
- **Racines** : **vue racinaire diégétique** (toggle, ou débloquée à la maîtrise « sol »)
  affichant l'empreinte racinaire (`root_plots` existe côté moteur) en pixel-art sous la
  surface. Forte valeur pédagogique pour un jeu de permaculture (rendre l'invisible).

## 7. Ordre de réalisation (sous-sprints, golden préservé)

Le rendu ne touche pas le moteur → **golden trivialement préservé** à chaque tronçon
(seuls comptent les revalidations F5 par Nico). Découpage proposé :

1. **SS① Fondation** — ✅ **FAIT & validé F5 (2026-06-23)**. SubViewport basse-réso
   **960×540 ×2** (le pixel-art) ; **projection laissée en ISO 2:1** (top-down essayé
   puis abandonné, cf. §3) ; **étiquettes plantes rendues nettes hors grille**
   (`WorldView.Etiquettes.cs`). Picking reconverti via le SubViewport
   (`WorldMouseCanvas`). Golden inchangé. **Reste pour un vrai pixel-art : la palette
   (SS②) — Nico note au F5 que les couleurs manquent de dégradés/relief.**
2. **SS② Palette** — rampes + hue-shifting + lumière sud sur les acteurs existants
   (plantes d'abord). **F5 = volume 16-bit.**
3. **SS③ Sol** — dual-grid autotiling + dithering des champs.
4. **SS④ Plantes/organes** — lignification branches + feuilles par famille (réf. Runions)
   + volume fleurs/fruits. Prototype SVG Python d'abord.
5. **SS⑤ Champignons** — sprites procéduraux reliés à la décomposition.
6. **SS⑥ Faune** — silhouettes par gabarit, affinage à la maîtrise.
7. **SS⑦ Racines** — vue racinaire diégétique.

## 8. Décisions ouvertes & références

- **Budget palette** : nombre de couleurs total, partage inter-acteurs — à fixer SS②.
- **Affichage des champs** : teinter le sol (immersif) vs overlay toggle — à trancher SS③.
- **Résolution interne du SubViewport** : ~~480×270 (×4) vs autre~~ → **TRANCHÉ SS① :
  960×540, upscale ×2** (le ×4 était trop gros).
- **Floyd-Steinberg** : meilleure qualité que Bayer mais séquentiel → réserver à la
  génération d'asset hors-ligne, pas au runtime déterministe.
- **Cache de sprite `PlantRenderer`** : « rendre une fois sur surface puis blitter » si le
  procédural redessine trop (piste perf).

### Sources
- Lane & Prusinkiewicz 2002, *Generating Spatial Distributions for Multilevel Models of
  Plant Communities* (déjà versé `BACKLOG.md` §génération de terrain).
- Runions 2014 (thèse, Calgary), *Computational Modeling of Leaf Development and Form*
  — pertinent COUCHE A (forme de feuille), surdimensionné à la densité pixel.
- Rendu pixel-art : Excalibur (dual-grid), redblobgames & BorisTheBrave (autotiling),
  surma.dev ditherpunk & Wikipedia (dithering Bayer), MegaCat Studios & Lospec (palettes
  SNES). Liens dans `BACKLOG.md` §rendu pixel-art.
