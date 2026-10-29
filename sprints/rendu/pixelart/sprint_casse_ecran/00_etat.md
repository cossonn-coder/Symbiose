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
| ④ | `04_paliers_hauts.md` — (i)(m) | à faire |
| ⑤ | `05_faune_icones.md` — (a) | à faire |
| ⑥ | `06_lisiere_decor.md` — (k) + résidus lisière | à faire |
| ⑦ | `07_bilan_ecran.md` — planche, mesures, protocole F5 | à faire |

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

## §REPRISE
Lire `CLAUDE.md` + ce fichier + le kickoff du premier tronçon « à faire » (④ `04_paliers_hauts.md`).
④ réutilise l'encodage ③ (§Notes ③) : cuire les paliers hauts en codes + `PaletteIndexee`.
Lancement : `/sprint-auto sprint_casse_ecran`. Valider chaque tronçon visuel au banc :
protocole et ligne de base en §Notes ① (`tools/mesure_da.py`, `capture_vm.sh -O -F`).
