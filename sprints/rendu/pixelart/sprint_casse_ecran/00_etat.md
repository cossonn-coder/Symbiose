# Sprint CASSÉ À L'ÉCRAN (D112) — état partagé

**Conception FIGÉE le 2026-10-29** (`/conception D112`, accord Nico « oui »). Doc :
`docs/rendu/pixelart/conception_casse_ecran.md`. **Référence visuelle** (brief de Nico,
gravé tel quel) : `docs/rendu/pixelart/etude_brief_da_16bits.md`. Pure vue + pont
lecture/debug → **golden JAMAIS re-figé** (`fecccded…`, `python3 -m tests.test_golden`
depuis `data/code/`). Filet C# : `dotnet build Symbiose.csproj`. Yeux : `tools/capture_vm.sh`.
Perf : `tools/perf_vm.sh`.

## Décisions clés
- Périmètre = tout D112 (Nico) ; hors : bug de vent en longue partie, nuit (→ D117), sol (D34).
- Une espèce = UNE recette (rampe 3-5 tons à teinte qui dérive, motif, squelette, accent,
  ancrage), **la même à tous les paliers** : palier fin = plus de motifs.
- Masses sans contour ; petits objets = trait de la teinte sombre de LEUR rampe ; jamais `#000`.
- Éclat côté **soleil réel** (`WorldView.SunShadowDir`) ; ombres portées gardées mais teintées.
- **Palette indexée** : atlas = indice de ton + orientation de face ; shader + LUT par matière ;
  F11 post-process retiré ; 0 recuisson au mouvement du soleil.
- Dialectes : SoM = plante seule ; CT forêt = couverts denses / lisière ; nuit = dette D117.
- Iso 2:1 gardée ; bruit/variation = hash, jamais Random. Validation = banc de mesure (①),
  F5 Nico = ressenti seul.

## Tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_charte_banc_mesure.md` | **fait** (2026-10-29, non commité) |
| ② | `02_defauts.md` — (b)(n)(e)(d)(h) | **fait** (2026-10-29, non commité) |
| ③ | `03_palette_indexee_soleil.md` — (f)(l), paliers bas | **fait** (2026-10-29, non commité) |
| ④ | `04_paliers_hauts.md` — (i)(m) | **fait** (2026-10-30, non commité ; à-coup de cran +27 % à confirmer) |
| ⑤ | `05_faune_icones.md` — (a) | **fait** (2026-10-30, non commité) |
| ⑥ | `06_lisiere_decor.md` — (k) + résidus lisière | **fait** (2026-10-30, non commité) |
| ⑦ | `07_bilan_ecran.md` — planche, mesures, protocole F5 | **fait** (2026-10-30, non commité ; perf : à-coups de zoom +20 % à confirmer au PC) |

## Notes de tronçon
(chaque tronçon ajoute ici : ce qui est fait, mesures avant/après, écarts au kickoff)

### ① Charte + banc de mesure — fait
- **Table des rampes** `visuals/RampesDa.cs` (NON branchée au rendu, c'est ③) : 12 matières
  hex du brief (canopée jour, tronc, buisson vif, couvert olive, touffe claire, gazon, feuille
  de fleur, fleur jaune, fleur magenta, terre cuite, pierre, crème) ; `Deriver(base)` OKLab →
  5 tons (base = ton 2 inchangé ; ombre vers 230° froid, clair vers 105° jaune, 6°/cran ;
  ombre des jaunes → orangé ; anti-noir sous L 0,33) ; recettes `Plante/Faune/Carpophore`
  mémoïsées ; `Contour(rampe)` = ton le plus sombre. Accesseurs lecture seule ajoutés :
  `PlantRenderer.TeintesEspece` (Organs.cs), `MacroLife.CouleurEspece`. Valeurs NON mesurées
  du brief (ombre de fleur jaune, magenta, gris crème, pierre) = dérivées puis figées, signalées.
- **Banc** `tools/mesure_da.py` (+ `tools/da_image.py` : PNG et OKLab en stdlib pure — ni PIL
  ni numpy sur la VM). Mode monde = paire test/réf : même capture avec `-x …,Objects` → masque
  par différence (ombres = assombrissement uniforme retiré) ; mode planche = fond uni.
  `--charte visuals/RampesDa.cs` contrôle la table (0 défaut). Chaque seuil a sa ligne de
  rationale en tête du fichier. ~12 s par image [VM].
- **`capture_vm.sh`** : `-F` (palette F11 au montage) et `-O` (ombres portées coupées).
- **Écart au kickoff** : la planche L ne pose PAS les espèces séparément (elle zoome sur UNE
  plante du monde) → isolation par la paire test/réf. Protocole retenu :
  `capture_vm.sh -b BANC -c X,Y -w W -O -x Weather,MacroLife,House [-F] -l 2 -n 190` puis la
  même avec `,Objects` ; `mesure_da.py planche_xN_t.png --ref planche_xN_r.png`. La planche
  nomme ×0,5 `planche_x0,5.png` (virgule).
- **Ligne de base AVANT** (médianes par sprite, pixels logiques, soleil de référence 135° ;
  chaque cellule [n=1 capture]) :

| scène | palier | sprites | tons lus | qnoir % | dérive ° | aplat px (> 24) | éclat côté soleil | voisins identiques |
|---|---|---|---|---|---|---|---|---|
| luxuriance F11 off | ×1 | 5 | 4 | 0 | 25,8 | 1 (0/5) | 0/5 | 1/2 paires |
| | ×2 | 10 | 6 | 0 | 43,0 | 1 (0/10) | 3/10 | 0/14 |
| | ×4 | 15 | 5 | 0 | 2,2 (7/15 > 3°) | 94 (13/15) | 7/15 | 0/9 |
| | ×16 | 6 | 2 | 0 | 10,7 (3/6) | 190 (6/6) | 2/6 | — |
| luxuriance F11 on | ×1 | 4 | 5 | 0 | 48,6 | 2 (0/4) | 0/4 | 0/1 |
| | ×2 | 10 | 6 | 0 | 15,5 | 2 (0/10) | 3/10 | 0/17 |
| | ×4 | 26 | 5 | 0 | 41,7 | 82 (21/26) | 11/26 | 0/106 |
| | ×16 | 9 | 3 | 0 | 32,5 | 86 (7/9) | 2/9 | 0/2 |
| forêt (automne, nus) | ×1 | 11 | 5 | 0 | 39,4 | 2 (1/11) | 4/11 | 0/3 |
| | ×2 | 13 | 4 | 0 | 20,2 | 3 (3/13) | 5/13 | 0/2 |
| | ×4 | 4 | 1 | 0 | 0,0 (0/4) | 20 (1/4) | 0/4 | — |
| diversité (tournesols) | ×2 | 18 | 4 | 0 | 40,1 | 3 (0/18) | **0/18** | **10/138** |
| faune (luxuriance) | ×4 | 8 | 1 | **3/8 sprites à 100 %** | 0,0 | 17 (3/8) | 3/8 | 1/3 |

  Lecture : (1) **paliers hauts = aplats** (×4/×16 : 13/15 et 6/6 sprites > 24 px d'un seul
  ton) et dérive qui s'effondre (×4 : 2,2°) — cible ④ ; (2) **éclat jamais côté soleil** aux
  bas paliers (0/5, 0/18 : l'éclat est en BAS du sprite, cf. `Kit.cs` `Eclairement`) — cible
  ③ (l) ; (3) **voisins identiques** à ×1/×2 (10 paires de tournesols) — cible hash ③/④ ;
  (4) **faune quasi-noire** (merle/carabe : 3 sprites 100 % quasi-noirs) — cible ⑤ ; (5) aucun
  quasi-noir sur les plantes (le contour ×1 actuel est vert sombre, pas neutre) ; (6) couleurs
  brutes 24-43 par sprite de 50 px à ×1 = fondu non indexé (attendu jusqu'à ③).
  **Trouvaille hors mesure** : à ×16 la planche sur le cerisier (forêt) n'affiche AUCUN pixel
  de l'arbre (0 sprite, image vérifiée) → à regarder en ④.
- Captures de la ligne de base (hors dépôt, effacées au reboot) : `/tmp/claude-1000/da/base2/`.

### ② Défauts — fait
- **(b) maison en verre** — ⚠️ prescription du kickoff RÉFUTÉE en partie : retirer le
  biais de ZIndex de strate (tri Y pur, maison ancrée au coin avant) cachait les plantes
  plantées DEVANT un mur latéral (pied plus haut que le coin avant, vu en capture : tuteur
  disparu). Retenu : plantes sans biais de ZIndex (strate = biais de Y infime 0,001 px/rang,
  `PlantYBias`, départage à pied égal → invariant luxuriance ⑥) + **deux plans** dans
  `Objects` : la maison ET ce qui est derrière elle (pied au-dessus du pied des 2 murs côté
  caméra, dans sa largeur ± 80 px) en ZIndex relatif −1, le reste à 0
  (`WorldView.Maison.cs` `ZObjet`, appliqué aux plantes, plantes en pot, supports,
  conteneurs, compost) ; ombres des plantes −1 → −2. Effet : ×1 orient 0 / 2, 1 900 /
  7 528 px changés [n=1 capture chacune], tous sur le toit/mur (les plantes de derrière ne
  le traversent plus) ; ×4 : plantes derrière cachées, tuteur devant visible.
- **(n)** `DecorLayer.SetDevantAlpha` : H rend la lisière côté caméra translucide (même
  alpha 0,15 ; mémorisé, survit à la rotation). Capture ×0,5 : arbres S/E fondus.
- **(e)** `visuals/JaugesInfoBulle.cs` : barre 2 px (pas 1 : illisible en 1080p), remplie
  du « mal » vert→rouge, repère au seuil de visibilité, pastille = couleur F6 du champ lié,
  mot léger/marqué/grave, chiffre brut gardé entre parenthèses. Sens par clé commenté dans
  `InfoBulle.cs`/`InfoBulleVivant.cs` ; abondance d'une bête laissée en chiffre (son « bon »
  dépend du rôle). Captures plante (PoaAnnua, 5 jauges) et limace lues.
- **(d)** pont 0.6.1 : `fields` sert toujours `vent`/`lisiere`/`turbulence` (neutres 0/0/1
  sans créer le champ, `CHAMPS_NEUTRES`) ; vue : `FieldOverlay.OrdreCycle` met le vent en
  tête (avant : « alarme » en tête), palettes à bornes fixes 0..1,2 / 0..1 / 1..2.
- **(h)** op debug `carpophore` (touche **U**, plot sous la souris, psilocybe) :
  ⚠️ un carpophore n'a PAS d'état (perception recalculée) → ajout d'une mémoire de
  perception `carpophores_debug` (bornée à la semaine) dans `sim/champignon_manger.py`
  (hors `tools/simserver/`, hors tick, clé absente = no-op, golden intact) : snapshot,
  cueillette, vision passent par `carpophores_tuile` comme en jeu. Format compact factorisé
  (`champignon_route.carpophores_compacts`, serialize −6 LDC). Test pont : mangé → vision.
- Outils : `capture_vm.sh -H` (touche H) et `-6` (F6 au montage). Tests pont mis à 0.6.1
  + checks (d)(h) ; `test_sim_server` 307 ✅, `test_vision` 38/38, golden `fecccded…` PASS.
- Captures (hors dépôt) : `/tmp/claude-1000/da/c2/` (`avant_*` / `apres_*`).

### ③ Palette indexée + soleil (paliers bas) — fait
- **Encodage (pour ④⑤⑥)** — `visuals/PaletteIndexee.cs` (en-tête) : pixel d'atlas RGBA8 =
  R/G n° de palette (14 bits), B = `128 | ton<<4 | orientation` (ton 0..4 creux·ombre·BASE·
  clair·éclat ; orientation 0..7 = k×45° repère ÉCRAN, 0 droite / 2 bas / 6 haut, 8 = plat),
  A = 0/1. Palette = `RampesDa.Deriver(base)` (5 tons, ton 2 = couleur d'origine), une par
  couleur DISTINCTE quantifiée 6 bits/canal, mémoïsée dans une LUT 512×256 (16 384 palettes ;
  pleine → vidée + recuisson générale, journalisé). Shader unique
  `visuals/palette_indexee.gdshader` (cos face·soleil > 0,3 → +1, > 0,8 → +2 éclat, < −0,3 →
  −1 ; modulate du nœud par-dessus : fondus, flash, teinte LOD survivent).
- **Kit** : atlas RG8 — R = niveaux d'avant (planche du kit, décor `DecorLayer.Kit`, rendu
  littéral : INCHANGÉS), G = code indexé (`PlantRenderer.KitCodes.cs` : normale = dôme de la
  touffe + pli de la feuille ; séparation = ombre plate ; trous intérieurs = creux plat ; grain
  hash 12 % → ton 1 ; **pas d'anneau de contour**). Fleurons : 4 coins/bras orientés, cœur =
  palette `FlowerHeart`. Pièce indexée = UN tracé (texture des codes × modulate palette) au
  lieu de 4 bandes. `Eclairement()` (bas éclairé) ne nourrit plus que R.
- **Qui encode** : seul le PINCEAU de cuisson sous ×4 avec F11 ON (`Indexe`, `Lit()` :
  tiges, bois nu, neige des touffes, fleurons). Dessin direct (plante pas encore cuite) et
  paliers ≥ ×4 = littéral inchangé. Matériau choisi au `_Draw` : `PlantBaker.ImageIndexee`
  → `PaletteIndexee.Materiau`, sinon `Unpremultiply`. Météo/santé/givre/automne = dans la
  couleur de base (→ autre palette) ; vent = poses inchangées ; fondu/flash = modulate.
- **Soleil** : `PaletteIndexee.MajSoleil` chaque image = −ombre monde projetée (suit D35) ×
  cos(élév.) + haut écran × sin(élév.) ; `WorldView.Soleil.cs` calcule le soleil même ombres
  coupées (O). 0 recuisson au mouvement du soleil.
- **F11** = palette indexée ON/OFF (avant/après). `PaletteSnes.cs` + `palette_snes.gdshader`
  débranchés (en-tête), gardés : vision du psilocybe intacte, banc du seuil `--capture-palette`.
- **Ombres teintées** : `PlantShadow` #071010 α 0,2 (ex-noir 0,18) ; maison `Palette16.Ombre`
  #071010 α 0,18 (ex-noir 0,16).
- **Voisins** : variante/taille de touffe tirées avec une graine individuelle (`_swayPhase`).
- ⚠️ **Prescription réfutée (①)** : `RampesDa.ZoneJaune` 30° → 12° — les verts olive
  (OKLab 118-126°) étaient traités en « jaunes » → ombre orangée, dérive à l'envers (mesuré
  −6,5° méd. luxuriance ×2) ; après : +26,6°. `--charte` 0 défaut.
- **Outils** : `capture_vm.sh -j DEG` (angle horaire ; journal `[Soleil] écran N°` à passer
  à `mesure_da.py --soleil`) et `-L` (LUT coupée = « avant ») ; `perf_vm.sh -L`.
- **Banc** (paire test/réf, `-O -x Weather,MacroLife,House`, [n=1 capture par cellule]) :

| scène | palier | soleil écran | avant (LUT off) | après |
|---|---|---|---|---|
| luxuriance | ×2 | 13° (matin) | couleurs brutes 23-43/sprite, dérive 40,3°, éclat 3/8 | brutes 5-8, tons 5, dérive 26,6°, éclat 3/6, voisins id. 0 |
| diversité | ×1 | 13° | tons 4, dérive 26,3°, éclat 1/3 | tons 5, dérive 35,2°, éclat **3/3** |
| | ×1 | 122° / 133° (midi / soir) | — | éclat 2/3 · 1/3 |
| | ×2 | 13° | tons 4, dérive 36,2°, éclat 11/18 | tons 5, dérive 27,3°, éclat 8/18 |
| | ×2 | 122° / 133° | — | éclat **15/18 · 13/18**, voisins id. 0/153 |

  Partout : quasi-noir 0 %, contour noir 0 %, aplats ≤ 5 px. Visuel lu : la sunflower ×2
  s'éclaire à droite le matin, en haut-gauche le soir (crops `cdiv_h-60/h60.png`). ×0,5 :
  plantes sous le seuil du banc (0 sprite, tapis). Le banc sur une plante de 50 px est
  bruité (5 % le plus clair = 2-3 px) : le matin (soleil rasant à droite) ×2 reste 8/18.
  Rotation 1 non mesurable : `-r 1 -z 2` cadre en ×1 sur luxuriance (0 sprite) — outil, pas rendu.
- **Perf** (`perf_vm.sh` full ×1, A/B entrelacé LUT off/on, même build) : frame 89,5 → 92,4 ms
  et 83,0 → 85,5 ms (+3 % [n=2 paires, VM chargée 1-3,5]) ; draw calls 78 = 78. ×2 : 62,0 →
  65,4 ms (+5,5 % [n=1, charges différentes]), draw calls 69 = 69.
- **Écarts / reste** : éclat par TOUFFE (le shader ne connaît pas le centre de la plante) ;
  petites fleurs ≥ ×4 (`Flower.cs`) non touchées → ④. Captures : `/tmp/claude-1000/da/c3/`.
- **F5 Nico** : ×1/×2 au lever, midi, coucher ; tourner la caméra (R) ; F11 avant/après ;
  vérifier le fondu d'apparition et le flash d'action sur une plante cuite.

### ④ Paliers hauts — fait
- **Grammaire unique** — `visuals/PlantRenderer.Motifs.cs` (nouveau, 228 LDC) : à ×4+ chaque limbe
  (et chaque masse ×4, et le contour fidèle ×16+) est REMPLI d'une texture de motifs (feuille ≈ 3×4,
  4 formes au hash, creux = ton 0 dans les interstices, plus nombreux vers le bas), calée 1 texel =
  1 px interne → le motif garde sa taille à l'écran, la feuille en porte plus en zoomant. Masse de
  valeur = DÔME : cœur (orientations mêlées) + couronne de quads orientés vers l'extérieur. Coût
  CONSTANT par feuille quel que soit le palier (1 polygone + ~10 quads ; la texture 2560×512 porte
  les motifs, générée une fois en octets bruts). Bois : flancs orientés + stries 2-3 tons au hash.
  Arbres : racines en éventail (4-5) + halo de sol dithéré #2c3c1e. Fleurs/fruits : dôme pur +
  contour du ton 0 de LEUR rampe (`DrawPoint` à ×4). Trous du limbe = creux de la rampe du limbe.
- **Indexé à TOUS les paliers** : `Indexe` et `PlantBaker._nextIndexee` ne testent plus le palier ;
  tous les tracés ×4+ passent par `Lit()`/`Ton()` (Leaf, Flower, Froid, Meteo, PaliersHauts, Organs,
  squelette). Filet ajouté au shader : pixel sans bit 7 = littéral tel quel. Dessin DIRECT (plante >
  2048 px internes : arbres dès ×8) = même recette en littéral, soleil fixe haut-gauche.
- ⚠️ **Prescription réfutée (orchestrateur/①)** : le cerisier invisible à ×16 n'est PAS un défaut de
  rendu — la planche cadrait le centre de la boîte d'un houppier clairsemé (un trou). Corrigé dans
  `WorldView.Planche.cs` : dès ×8, visée = axe du collet à mi-hauteur (×2/×4 co-centrés gardés pour
  la continuité). Vérifié : aulne ×16 visible (`/tmp/claude-1000/da/c4/ap_foret/`).
- ⚠️ **Écart** : pas d'estampille « un tracé par motif » (∝ zoom², explosait ×16/×32) → texture
  UV-mappée ; ④b non nécessaire. `capture_vm.sh -r 1 -z 2` (défaut d'outil signalé en ③) NON traité.
- **Banc** (luxuriance, planche sur une violette, paire test/réf `-O -x Weather,MacroLife,House`
  [n=1 capture par cellule], avant = stash du même arbre) :

| palier | aplat méd (> 24 px) avant → après | tons lus méd | éclat côté soleil |
|---|---|---|---|
| ×4 | 86 px (5/5) → 34 px (4/5 ; le reste = tuteur) | 4 → 11 | 4/5 → 4/5 |
| ×8 | 15 (12/390) → 1 (2/124) | 1 → 2 | 88/390 → 67/124 |
| ×16 | 66 (211/270) → 14 (7/215) | 1 → 1 | 43/270 → 67/215 |
| ×32 | 15 488 → 2 079 (1 sprite) | 5 → 15 | 0/1 → 1/1 |

  ×8/×16 : la paire isole mal (centaines de « sprites » = sol/tapis) — médianes bruitées.
  **Continuité ×2→×4** (script hors dépôt, ΔE OKLab moyen ×4 réduit vs ×2 flouté 4×4, sur le
  masque plante) : 0,119 → 0,111 [n=1, 52 blocs, petite violette] — baisse MODESTE, pas « nette » :
  la géométrie diffère encore (×2 = touffes le long des rameaux, ×4 = limbes déportés). Piste ⑦/dette.
- **Perf** (même build, avant = stash) : banc E ×4 frame 92,8 → 98,3 ms (+6 % [n=1, charge VM 15 vs
  1,4]) ; draw calls 102 → 98. Balayage Z : pire cran 341 ms → 435 ms (+27 % [2ᵉ run, 1ᵉʳ run
  aberrant à 3,2 s sous charge 5,6 ; n=1 chacun]) — ×2→×4 315 → 431, ×8→×4 306 → 435. **Hors
  budget « pas pire qu'avant » si confirmé** : à remesurer au PC (cuisson des limbes ~5× plus de
  tracés). Captures : `/tmp/claude-1000/da/c4/`.
- **F5 Nico** : zoomer ×2 → ×32 sur un pommier et une touffe (« même plante, plus de détails ») ;
  tourner le soleil (éclat des limbes et des troncs) ; F11 avant/après ; regarder le halo au pied
  d'un arbre (taille réglable `AncrageMaxPx`) et l'à-coup de zoom ×2↔×4.

### ⑤ Faune en icônes — fait
- **Portraits** : `visuals/FauneSilhouettes.cs` (données, 159 LDC) = 19 bêtes + pollen décrites en
  ellipses dans le repère du corps (u tête +1 / queue −1, v travers ; ton −1 = dôme orienté, 0..4 =
  ton fixe ; `Fin` = détail dès 8 px ; `Miroir` = paires ; motifs Bandes/Segments/Piquants/Ecailles ;
  couleuvre = axe ondulé). `visuals/FauneIcones.cs` (198 LDC) = rastériseur + atlas 1024² en pixels
  INDEXÉS (encodage ③), cuit à la demande par (espèce, taille px exacte, cap 0..7 au hash), mémoïsé ;
  > 128 px → cuisson réduite posée en blocs entiers k×k. Contour 1 px = ton 0 de la rampe de la partie
  (dès 8 px) ; « plumage » 4×3 en appareil de briques dès 24 px (anti-aplat). Sous 3 px = point de la
  couleur du corps (texel de l'atlas). Pose = 1 quad dans le lot → **1 DrawMesh par couche**.
- **Branché** : `MacroLife` (taille réelle inchangée) et `ForagerLayer` (taille = diamètre de l'ancien
  grain ; pollen porté = icône « pollen ») ; matériau = `PaletteIndexee.Materiau` (éclat côté soleil
  réel). **F11 off = rectangles/grains d'avant** (A/B). `PaletteIndexee.Generation` (++ au vidage de
  LUT) → l'atlas se recuit. Icônes OPAQUES au repos (fondus gardés).
- ⚠️ **Écarts au kickoff** : (1) vue OBLIQUE écrasement 0,7 et non iso 0,5 (à 0,5 le merle de profil =
  un cigare, vu à la planche) ; (2) `BaseAlpha` 0,9 abandonné pour les icônes : l'alpha partiel mêlait
  le vert du sol au merle → 23 % de quasi-noirs neutres mesurés à ×4 (0 % après) ; (3) merle
  #1e1e22 → #2b2a3a (noir bleuté), carabe #2e3a44 → #2a3a52 (bleu-violet) — quasi-noirs neutres au
  banc ① ; `FieldOverlay` garde les anciens hex (heatmap, non touchée) ; (4) l'orientation des caps est
  écran (pas monde) : ne tourne pas avec la rotation D35.
- **Banc** : `capture_vm.sh -K` = planche de la faune (`visuals/PlancheFaune.cs`, rangées dans l'ordre
  du journal `[PlancheFaune]`, ×2 ×4 ×8 ×16 cap 0 + ×8 caps 1/6, `mesure_da.py --pas 1`). Planche
  [n=1 capture par cellule, 61 sprites] : avant (`-L`, rectangles) tons 1, aplat 378 px (63/63 > 24),
  éclat 0/63, 26 paires de voisins identiques → après : tons 7 (multi-rampes : corps+ailes+bec), qnoir
  0 %, contour noir 0 %, dérive 9,1°, aplat méd 21 px (29/61 > 24, les très grandes ×16), éclat 50/61
  (soleil 329°) · 29/61 (soleil 155°), voisins identiques 0.
  Monde (luxuriance, planche L, paire `-O -x Weather,House,Objects` / `+,MacroLife,ForagerLayer`
  [n=1 capture par cellule]) :

| palier | sprites | tons lus avant → après | éclat côté soleil avant → après | aplat méd |
|---|---|---|---|---|
| ×2 | 3 | 1 → 5 | 0/3 → 1/3 | 9 → 9 |
| ×4 | 6 | 1 → 6 | 1/6 → 4/6 | 8 → 12 (> 24 : 2/6 → 0/6) |
| ×8 | 1 | 1 → 6 | 0/1 → 1/1 | 38 → 17 |
| ×16 | 2-3 | 1 → 5 | 1/3 → 2/2 | 18 → 14 |

  Quasi-noir 0 % partout après ; ×4 avant correctif d'alpha : merle 22,9 % qnoir. Reconnaissance (Read
  des captures) : merle (bec orange, queue), hérisson (dôme de piquants + museau clair), couleuvre
  (ondulée), limace, abeilles/bourdon rayés, papillon 4 ailes lisibles dès ×4 ; coccinelle/doryphore/
  chrysope restent minuscules à taille réelle (coccinelle 4 px à ×16, points dès ×32).
  Captures : `/tmp/claude-1000/da/c5/` (`pf_*` planche faune, `pl_*` planche L monde).
- **Perf** (banc E ×4, `perf_vm.sh -E 20 -O`, `-L` = avant, même build, [n=1 run chacun, charge VM
  2,7-7]) : draw calls 105 → 102 ; vie macro `_Draw` 0,00 ms → 0,00 ms (18 bêtes au banc) ; frame
  89,6 → 99,5 ms (écart dominé par la charge VM : postes faune nuls). Cuisson d'un portrait non mesurée
  isolément (à la demande, une fois par espèce × taille × cap).
- `MacroLife.cs` 308 LDC (🟡, une seule responsabilité) ; `ForagerLayer.cs` 292.
- **F5 Nico** : trouver un merle, un hérisson, une coccinelle (×16/×32) ; tourner le soleil (éclat) ;
  F11 avant/après ; un geste près d'une bête (sursaut) ; papillon/abeille en vol.

### ⑥ Lisière et décor — fait
- **Pipeline indexé du décor** — `visuals/DecorLayer.Indexe.cs` (149 LDC) : atlas du kit écrit en
  CODES (R/G = n° de palette de la teinte, B = ton + orientation, encodage ③) + bande de 32 lignes
  de **texels-codes** pour les aplats (palette de la couleur, ton, orientation, alloués à la demande) ;
  **hook `LotTriangles.Encodeur`** : chaque sommet du décor est réécrit (aplat → UV de son texel-code ;
  couleur de sommet = R valeur du plan · G amplitude du vent · B phase au hash · A alpha). Les motifs
  ne règlent que l'état (`Aplats(orient, ton, matière)`, `Vent(...)`). Vidage de LUT → atlas réécrit
  sur place (mêmes UV). `PaletteIndexee` : palettes NOMMÉES à rampe exacte du brief
  (`PaletteNommee`, ex. `couvert_olive`, `touffe_claire`, `pierre`), `Soleil`/`Lut` exposés, soleil
  calculé même sans matériau de plante.
- **Shader unique** `visuals/decor_indexe.gdshader` (fond + couche devant) : lecture LUT + soleil réel ;
  grains procéduraux au PIXEL INTERNE du palier : orientation 9 = **tissage en chevrons 2×3** (assise,
  plateau, enveloppe des houppiers, ombres au pied), 10 = **roche** en blocs 8×4 à joints (face de
  falaise, face réelle dans le canal B → éclairée au soleil), 11/12 = **écorce** (stries, flanc G/D).
  ⚠️ **`texelFetch` obligatoire** : avec `texture()` le DrawMesh filtre en LINÉAIRE → codes lus décalés
  d'un cran (rivière brune, tissage perdu — mesuré : palette 75 lue 74). À retenir pour tout atlas de
  codes en maille.
- **Dialecte 2** — `visuals/DecorLayer.KitCodes.cs` (116 LDC) : masses (sous-bois, ronciers, bouquets)
  sans contour, grain en chevrons 2×3, bord haut clair, grains creusés au hash ; touffe = 3-5 grains
  obliques 2×3 ; galets/blocs = orientation par pixel (3 tons + éclat au soleil) + ombre sous le bord,
  0 contour noir. Sous-bois = rampe EXACTE `couvert_olive` (#302806…#aab164), herbe claire =
  `touffe_claire`, roche = `pierre`. Assise forêt = couvert olive (près ton 2, fond ton 1). Troncs : 2
  flancs orientés + contour = ton creux de LEUR rampe (fini le gris `EcorceLenticelle`).
- **Vent** — `visuals/DecorLayer.Vent.cs` (62 LDC) : le vertex shader rejoue `WindWave.PoseFor`
  (mêmes constantes, même temps `WindWave.Temps`, mêmes risées, phase monde projetée par
  `ScreenToWorld` → **mêmes fronts que les plantes**) ; amplitude au sommet : arbre 3 % de sa hauteur
  (nul au pied), sous-bois 0,40 · roseaux/herbe haute 0,30 · herbe 0,25 · roncier 0,20 × hauteur de
  pièce ; roche/galets 0. Déplacement arrondi au px interne. **Aucun redessin CPU** ; calme = force 0.
- **Résidus** : (a) bande prolongée jusqu'à `FondCm` 3 600 cm + 4 coins extérieurs, en tissage
  (capture `-c -900,-900` ×0,5 : plus de vert uni) ; (b) face de falaise = roche procédurale (traits de
  joints/lits d'avant conservés derrière `TraitsFalaiseAvant`, éteints) ; (c) ⚠️ **prescription
  réfutée** : le pic « 165 ms au changement de palier ×4 » n'existe plus depuis LEVIERS ③ (mailles
  prêtes) — mesuré AVANT ⑥ : redessin décor **0,0 ms** à chaque cran ; les pics du balayage Z sont
  la cuisson des plantes (×2→×4 : plantes _Draw 166 ms + cuisson 84 ms). Rien à réduire côté décor.
- **Mesures** (banc décor F10 `-B`, `-O -x Weather`, [n=1 capture par cellule]) — `mesure_da.py`
  paire test/réf (réf = `-x Weather,Decor`, `--pas 2`, zone hors HUD) :

| scène | avant | après |
|---|---|---|
| falaise ×2 | aplat 29 517 px, contour noir 2,6 %, qnoir 0,2 %, dérive 1,1° | aplat méd **4 px**, contour noir **0 %**, qnoir 0 %, dérive 1,7° |
| forêt ×2 | 56 sprites (aplats > 24 : 56/56, méd 93 px), tons 2, 77 voisins identiques | 1 masse connexe : plus grand aplat 2 339 px (ombres au pied sombres : ±1 ton peu lisible au creux), tons 16, dérive 28,7° |

  Soleil (forêt ×2, plantes masquées, `-j −60` vs `-j 60`, soleil écran 329° / 155°) : **jardin 0 %**
  de px changés, **tronc 90 %**, sol olive 23 % → l'éclat du décor suit le soleil réel. Vent (×1 forêt,
  plantes masquées, 8 images à 5 fps) : `-v 0,8` → 91 k à 241 k px changés vs image 0 ; `-v 0` → **0**
  (rien n'anime au calme). Rotations `-r 1..3` ×0,5 lues : coins et décor corrects.
- **Perf** : balayage Z (seed 1521550718, `-c 1650,950`) : redessin décor au cran 0,0 ms → 0,0-0,6 ms ;
  construction ×0,5 au 1er dessin 157 → 178 ms (+13 % [n=1]) ; tranches de fond pire image 16,2 →
  16,8 ms ; sommets ×4 113 877 → 115 665. `perf_vm.sh -z 0.5` : **draw calls 77 = 77** (décor 1 + 1
  devant inchangés) ; frame 96,8 → 76,4 ms [n=1 run chacun, charge VM 3,7-4,3 : écart = bruit].
- **Écarts / restes** : décor TOUJOURS indexé (F11 n'agit pas sur lui ; avant/après = stash) ; la
  rivière (eau) reste en aplats plats (hors dialecte 2) ; ombres au pied encore sombres et peu
  grainées ; ⚠️ soupçon hors tronçon : `FauneIcones` (⑤) lit son atlas de codes via le matériau des
  plantes (`texture()`) — si ses quads sont filtrés comme ici, palettes décalées possibles : à
  vérifier en ⑦. Captures : `/tmp/claude-1000/da/c6/` (`av_*` / `ap_*`).
- **F5 Nico** : lisière par vent calme puis fort (`-v`), au fil de la journée (le flanc éclairé des
  troncs et des rochers tourne) ; touche H (lisière devant translucide) ; zoom ×0,5 → ×4 ; rotation R ;
  bord du cadre au dézoom (plus de vert uni).

### ⑦ Bilan à l'écran — fait
- **Correctif trivial et localisé (soupçon ⑥ confirmé)** : `palette_indexee.gdshader` lit son
  atlas par `texelFetch` (et non `texture()`). A/B même capture (luxuriance ×4, déterministe :
  contrôle A/A = 0 px) : **2 480 px changés, tous sur la faune** (plantes 0 px) — contour 1 px
  du hérisson rétabli, œil du papillon de nouveau de sa palette. L'atlas des plantes (③) n'avait
  pas le défaut (dessin aligné au pixel) ; le correctif ne le change pas.
- **Planche complète** (banc `full`, seed 42, `-c 648,1474 -w 24`) lue au Read : paliers ×0,5→×32
  (`-l`), 4 rotations × 3 heures à ×2 (`-r 0..3 -j −60/0/60`), ×8/×32 en rotations 1 et 3, vent
  calme/fort à ×1 ; + planche L (luxuriance, forêt, diversité) et planche faune (`-K`). Lu : maison
  opaque, plantes devant/derrière justes ; ×16 « même tournesol » (limbes à motifs, tête en dôme) ;
  ombres qui tournent avec l'heure ; bêtes reconnaissables (merle, hérisson, couleuvre, papillon,
  abeilles rayées). `capture_vm.sh -r 1 -z 2` (défaut d'outil signalé en ③) **non reproduit** sur
  `full` (cadre bien ×2). Captures : `/tmp/claude-1000/da/c7/` (`ap/` paires, `full/`).
- **Rapport final du banc ①** (même protocole que `base2.sh` : paire test/réf `-O -x Weather,
  MacroLife,House[,Objects]`, planche `-l 2`, soleil de mesure 135° comme la ligne de base ;
  chaque cellule [n=1 capture]) :

| critère | scène · palier | avant (①) | après (⑦) |
|---|---|---|---|
| tons lus (méd) | luxuriance ×1 / ×2 / ×4 / ×16 | 4 / 6 / 5 / 2 | 6 / 6 / 11 / 9 |
| | faune ×4 | 1 | 9 |
| | planche faune (61 sprites) | 1 [`-L`, ⑤] | 8 |
| #000 / quasi-noir | toutes plantes | 0 % / 0 % | 0 % / 0 % |
| | faune ×4 | **3/8 sprites à 100 %** | **0/8** |
| contour noir | toutes scènes | 0 % | 0 % (falaise ⑥ : 2,6 % → 0 %) |
| dérive ombre→éclat (méd) | luxuriance ×1 / ×2 / ×4 / ×16 | 25,8° / 43,0° / 2,2° / 10,7° | 34,8° / 16,6° / 51,4° / −0,4° |
| | diversité ×2 | 40,1° | 38,8° |
| aplat > 24 px | luxuriance ×4 | 13/15 (méd 94 px) | 9/14 (méd 50 px) |
| | luxuriance ×16 | 6/6 (méd 190 px) | 3/10 (méd 14 px) |
| | faune ×4 | 3/8 | 0/8 |
| voisins identiques | diversité ×2 (tournesols) | **10/138 paires** | **0/136** |
| | faune ×4 | 1/3 | 1/1 (2 icônes de même espèce, même taille, même cap au hash) |
| éclat côté soleil (cos > 0) | luxuriance ×4 | 7/15 | 11/14 |
| | diversité ×2 | 0/18 | 6/18 [soleil 135° fixe ; au soleil réel ③ : 15/18 midi] |
| | faune ×4 | 3/8 | 7/8 |
| continuité ×2→×4 (ΔE OKLab, ×4 réduit vs ×2 flouté) | luxuriance, planche | 0,120 [136 blocs] | 0,102 [114 blocs] |

  Lecture : les cibles du brief sont tenues sur les plantes seules et la faune (noir 0, voisins 0,
  éclat majoritairement au soleil, aplats divisés par 2 à 13 aux paliers hauts). Restes : dérive
  ×16 ≈ 0 (le tracé direct des grandes plantes reste à soleil fixe, ④) ; forêt ×2/×4 = tons 1 car
  la paire isole surtout l'**ombre d'un arbre nu** (couleur unie, identique avant/après : pas une
  régression, artefact du banc) ; luxuriance ×4 « 1 voisin identique » = deux flancs de tuile, pas
  des plantes ; continuité −15 % seulement (la géométrie ×2 ≠ ×4 demeure).
- **Vent** (×1 `full`, plantes/faune/météo masquées, images 3→5 à 5 fps [n=1 capture chacune]) :
  calme **0 px** changé, fort (`-v 0,9`) 15 475 px → la lisière bouge au vent, rien n'anime au calme.
- **Perf** — A/B entrelacé avec l'état de DÉPART du sprint (worktree `985a388`, même VM, même
  minute ; charge 2,9-6,0 : peu fiable) :

| mesure | départ | fin de sprint | limite |
|---|---|---|---|
| banc partage A, s/sem (A1·A2·A3·A4) | 2,91 · 2,24 · 2,02 · 2,24 | 2,88 · 2,01 · 2,02 · 2,57 / 2,86 · 2,26 · 2,53 · 2,51 | [n=1 / n=2 runs, VM] |
| A, médiane des 4 sous-phases | 2,24 | 2,30 / 2,51 (+3 % / +12 %) | [idem] |
| C (moteur en pause), image moy. | 227 ms | 235 / 299 ms | [idem ; 2ᵉ run sous charge 6] |
| C, draw calls | 648 | 673 / 811 | [idem] |
| balayage Z, moyenne des 12 pires images | 291 ms | 340 / 348 ms (**+17 / +20 %**) | [n=1 / n=2 aller-retour] |
| Z, ×2→×4 · ×8→×4 · ×16→×8 | 313 · 282 · 285 ms | 504/427 · 453/460 · 390/461 ms | [idem] |
| banc E ×4 (`-E 20 -O`) | 89,6-92,8 ms (③-⑤, notes) | 100,8 ms, draw calls 102 | [n=1 run, charge 4,3] |

  **Verdict** : régime établi dans le bruit (≤ +12 % [n=2, VM]) ; **à-coups de zoom +20 %**
  [n=1 vs n=2, VM] = au-delà du budget 10 %, cohérent avec le +27 % du ④ et localisé à l'ENTRÉE
  des paliers ×4/×8 (postes : plantes `_Draw` 152 ms + cuisson 76 ms à ×2→×4). Non corrigé
  (consigne ⑦) → note D112 (o), à confirmer au PC avant toute action.
- **Taille** : `compte_ldc.py` sur les 78 fichiers touchés par le sprint : aucun > 400 LDC →
  pas de `/refactor`. 🟡 : `serialize.py` 392 (398 avant), `SimBridge.cs` 348 (345 avant),
  `MacroLife.cs` 308 (289 avant, signalé ⑤).
- **Restes consignés** (D112, pas de dette nouvelle) : (o) à-coups de zoom ; (p) orientation des
  icônes faune en repère écran (ne tourne pas avec R, ⑤) ; (q) ombres au pied des arbres de
  lisière sombres et peu grainées, F11 sans effet sur le décor (⑥) ; (r) dérive nulle ×16 en
  dessin direct ; (s) à ×32 une abeille peut passer devant le mur de la maison (couche faune
  au-dessus des objets — vu une fois, `z32_r3`, non investigué).

## §F5 — protocole de Nico (ressenti seul, ~10 min, aucune mesure)
1. **Maison** : tourner autour (R) — aucune plante ne traverse les murs ; **H** rend maison ET
   lisière côté caméra translucides.
2. **Maj+F3** sur une plante puis une bête : jauges colorées lisibles (léger/marqué/grave).
3. **F6** : le premier champ est le **vent**.
4. **U** sous la souris fait pousser un psilocybe → le cueillir/manger → la vision se déclenche.
5. Zoomer **×2 → ×32** sur un tournesol puis un pommier : « la même plante, plus de détails ».
   Noter si le passage ×2→×4 ou ×8→×4 accroche (à-coup).
6. **Soleil** : au lever puis au coucher, les touffes et troncs s'éclairent du côté du soleil
   (F11 = avant/après).
7. **Bêtes** : reconnaître merle, hérisson, papillon, abeille, couleuvre (×4-×16).
8. **Lisière** : par vent fort elle ondule avec les plantes, au calme elle est immobile.

## §REPRISE
**Sprint TERMINÉ côté code (①→⑦).** Reste : **F5 de Nico** (§F5 ci-dessus) puis commit de ⑦
(orchestrateur). Restes consignés en D112 (o)→(s) — à trancher après le F5 ; à-coups de zoom
+20 % [VM] à confirmer au PC. Encodage indexé : §Notes ③ ; `Ton()`/`RemplirDome()` ④ ; atlas de
portraits ⑤ ; décor indexé ⑥ — **tout atlas de codes se lit en `texelFetch`** (⑥ décor, ⑦ plantes
et faune). Banc : protocole ①, campagne ⑦ (`/tmp/claude-1000/da/c7/`, hors dépôt).
