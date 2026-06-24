# T2 — Sol : texture pré-cuite (relief lumière-sud + grain), 4 orientations D35

> Lire d'abord `00_etat.md` (invariants) + `CONCEPTION_RENDU_PIXELART.md` §5 (bloc
> « Relief du SOL »). Couche **B pure** (C#). Golden trivialement préservé, build C#
> vert, F5 = Nico. DERNIER tronçon → CLÔT le sprint. **Le dernier aplat du rendu.**

## But

Le sol est aujourd'hui un **aplat** : `WorldView.Monde.cs` pose un losange
`Polygon2D` d'**une seule couleur** par plot (`MakeLozenge` + `SoilColor`, + damier
±5 %). On le remplace par une **texture pré-cuite en C#** portant, **en une passe** :
- un **relief bombé lumière-sud** (moitié sud éclaircie, moitié nord assombrie +
  refroidie) → le sol n'est plus plat ;
- un **grain dithering 3 valeurs** au pixel, déterministe → micro-texture de terre.

## Contexte technique (état réel)

- Losange iso 2:1 : **`TileWPx = 39`, `TileHPx = 19.5`** (`WorldView.Projection.cs:32-33`),
  donc une `Image` cible **≈ 39×20 px** (petit → grain volontairement grossier, c'est
  du pixel art). Sommets du losange : nord `(0,-h/2)`, est `(w/2,0)`, sud `(0,h/2)`,
  ouest `(-w/2,0)`.
- `BuildGround` (`WorldView.Monde.cs:62`) boucle sur tous les plots et fait
  `poly = MakeLozenge(soil ou soil.Darkened(0.05))` puis `poly.Position = WorldToScreen(...)`.
- **Damier ±5 %** : alternance `(r+c)%2` par plot — NE peut pas vivre dans une texture
  partagée → reste un `modulate`/`self_modulate` léger appliqué par plot.
- **Rotation D35** : la maison gère déjà le sud-monde par index de mur
  (`FacadeColors`/`ToitColors`, cycle 0 nord/1 est/2 sud/3 ouest). Le sol doit suivre
  la même logique : la cap éclairée pointe vers le **sud-monde**, qui à l'écran tombe
  sur un sommet différent du losange selon l'orientation → **4 textures cuites**.
- Couleurs de sol : `Palette16` après T1 (`TerreColor`/`ArgileColor`/`SableColor`/`SolInconnu`).
- Direction sud écran : `WorldView.WorldToScreenOffset(0,1)` (déjà utilisée par le
  hue-shift des plantes, `PlantRenderer.Palette.cs:132` `SouthDir`). À NE PAS confondre :
  ici on cuit dans l'espace TEXTURE du losange, pas à l'écran — voir §B.

## Travail

### A. Cuisson de la texture (nouveau fichier `world/SolTexture.cs` ou helper dédié)

- Une fonction `static ImageTexture BakeLozenge(Color soil, int orientation)` qui rend
  une `Image` ~39×20 px (`Image.CreateEmpty(..., Image.Format.Rgba8)`) :
  - **Hors du losange** : pixel **transparent** (alpha 0). Test « dans le losange » =
    `|x/(w/2)| + |y/(h/2)| <= 1` (équation du losange centré).
  - **Dans le losange** :
    1. **Relief** : facteur de luminosité ∝ position le long de l'axe **nord→sud-monde**
       (dépend de `orientation`). Côté sud → éclaircir (hue-shift CHAUD), côté nord →
       assombrir + refroidir (hue-shift FROID). **Réutiliser le `HueShift`** de
       `PlantRenderer.Palette.cs` si exposable, sinon répliquer la même formule HSV
       (cohérence chromatique sol ↔ plantes — c'est tout l'intérêt de la palette
       partagée). Amplitude douce (le sol est mat, pas un organe rond) : à régler F5.
    2. **Grain** : 3 valeurs. Pour chaque pixel, un `Hash01(plotSalt?, x, y)` →
       quantifié en 3 niveaux (−1/0/+1) qui module légèrement la valeur. **Déterministe**
       (philo #3) : pas de `Random`. Bayer 4×4 OU hash pixel — choisir le plus lisible
       au F5 ; commenter le choix. Le grain ne doit PAS effacer le relief (faible amplitude).
  - `image.SetPixel(x, y, c)` ; à la fin `ImageTexture.CreateFromImage(image)`.
- **Filtre Nearest** sur la texture/le sprite (invariant). Avec `Polygon2D` : la
  texture se pose via `Texture` + UV ; avec `Sprite2D` : `TextureFilter =
  TextureFilterEnum.Nearest`. **Choisir l'approche la plus simple** (un `Sprite2D` par
  plot pointant sur la texture cuite PARTAGÉE est le plus direct ; les Polygon2D
  actuels peuvent aussi recevoir une texture + UV losange). Justifier le choix.

### B. Orientation D35

- Cuire **4 textures par type de sol** (une par orientation), p.ex. un
  `Dictionary<(string soil, int orient), ImageTexture>` rempli à l'init.
- L'« orientation courante » = la même que celle qui pilote la maison. **Repérer**
  comment `BuildHouse`/la projection connaît l'orientation (probablement un champ de
  `WorldView` lu par `WorldToScreen`) et l'utiliser pour choisir la texture au moment
  où `BuildGround` (re)construit le sol. `BuildGround` est déjà rappelée à chaque
  rotation (les enfants de `_ground` sont reconstruits, cf. boussole commentaire
  `WorldView.Monde.cs:94`) → il suffit de lire l'orientation courante à la cuisson/au
  choix de texture.
- **Cuisson PARESSEUSE et CACHÉE** : ne pas recuire 4×N images à chaque rotation —
  cuire une fois par `(soil, orient)` et réutiliser la même `ImageTexture` pour tous
  les plots d'un type sous une orientation donnée (≤ 4 sols × 4 orient = 16 textures max).

### C. Brancher dans `BuildGround`

- Remplacer `MakeLozenge(...)` par un nœud portant la texture cuite (relief+grain) du
  bon `(soil, orientation)`, positionné comme avant (`WorldToScreen(cx, cy)`).
- **Damier** : appliquer le ±5 % via `modulate`/`self_modulate` par plot (la texture
  reste partagée). Garder l'effet subtil actuel.
- La **boussole** et le reste de `BuildGround` (cardinaux, maison) NE changent PAS.

## Vérifications

1. `dotnet build Symbiose.csproj` → **0 erreur, 0 warning**.
2. Golden inchangé : `cd data/code && python3 -m tests.test_golden` → `2ab026ad…`.
3. Relecture : texture cuite déterministe (hash, pas Random) ; filtre Nearest ;
   4 orientations cachées (pas de recuisson par frame) ; damier conservé ; hors-losange
   transparent (pas de carré opaque qui dépasse).

## Clôture (MAJ `00_etat.md` → SPRINT CLOS)

- Passer T2 ✅ + bannière **🏁 SS² RENDU PIXEL-ART — CLOS** dans `00_etat.md`.
- §REPRISE : entrée T2 = fichier de cuisson créé, approche nœud retenue (Sprite2D vs
  Polygon2D texturé), méthode de grain (Bayer/hash) + amplitude relief retenues, gestion
  des 4 orientations + cache, golden vérifié, `dotnet build` vert.
- **Verdict F5 attendu (à écrire pour Nico)** : le sol n'est plus un aplat — chaque
  plot montre un **léger bombé** (sud plus clair/chaud, nord plus sombre/froid) ET un
  **grain** de terre ; au quart-de-tour (D35) le bombé **suit le sud du jardin** (comme
  la maison), il ne reste pas collé à l'écran ; les 3 types de sol restent distincts ;
  pas de carré opaque hors losange. Verser tout défaut en dette ciblée.
- **Journal** : écrire une entrée de clôture `journal/NN_2026-…_sprint-rendu-pixelart-ss2-CLOS.md`
  + l'indexer dans `journal.md`.
- **Mémoire** : mettre à jour `project_rendu_pixelart.md` (SS② CLOS : sol + palette).
- Commit (ex. `feat(rendu) : T2 sol texturé relief+grain 4 orientations — SS² CLOS`).
