# sprint_precuisson_splats — état du sprint

**Conception FIGÉE le 2026-11-20** (`/conception`, Nico : « vas-y ») →
`docs/rendu/splatting/conception_precuisson_splats.md`. Sprint (a) « plantes » du
programme « tout en splats » (D7). **Prêt pour `/sprint-auto sprint_precuisson_splats`.**
Golden : **INTACT à tous les tronçons** (vue + outillage, `data/code/` jamais touché).

## Carte des tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_atelier_cuisson.md` — outil `tools/splat/` + feuille composée, format palette indexée, tous paliers, mesures — **PORTE DE DÉCISION** | **fait 2026-11-20 — porte PASSÉE avec réserves** (cf. compte rendu) |
| ② | `02_feuilles.md` — bibliothèque des feuilles (formes, variantes, vues, trous D5) | **fait 2026-11-20** (non commité) |
| ③ | `03_tetes_fruits_bois.md` — têtes, fleurs, fruits, bourgeons, bois (couture mesurée) | **fait 2026-11-20** (non commité) — bois NON livré (couture visible) |
| ④ | `04_vue_paliers_hauts.md` — vue ×4 → ×32 | **fait 2026-11-20** (`aba3663`, partiel) **+ ④bis fait 2026-11-20** (non commité) : couverture complétée là où une recette existe ; reste dessiné listé au compte rendu ④bis |
| ⑤ | `05_vue_paliers_bas.md` — vue ×0,5 → ×2 (kit) | à faire |
| ⑥ | `06_portraits.md` — 162 portraits | à faire |
| ⑦ | `07_vue_encyclopedie.md` — encyclopédie + magazine, clôture | à faire |

## Règles du sprint
- Si la porte du ① échoue (pièce illisible à 3-9 px, ou ton/orientation non
  extractibles) : **arrêt**, retour en `/conception`.
- Poids (D2) mesuré à chaque tronçon ; alerte et arrêt si les pièces dépassent ~200 Mo.
- Capture VM sans écran pour voir avant le F5 : `tools/capture_vm.sh` (Godot + Xvfb
  sous `~/opt`, cf. `tools/lib_vm_godot.sh`).
- Interdits : `test_epaisseur_500ans` ; DeepSeek dans les sous-agents (protocole) ;
  modifier les sources copiées d'ink-studio.

## Compte rendu des tronçons
(rempli par chaque tronçon : fait, mesures, chemins des planches et captures)

### ① Atelier de cuisson (2026-11-20) — PORTE PASSÉE avec réserves
**Fait.** ink-studio copié dans `tools/splat/vendor/ink/` (commit `fb94031…`, MIT,
11 Mo, 1 004 fichiers ; provenance dans `tools/splat/README.md`) ; `tools/splat/.gdignore`
(Godot n'importe pas le dossier). Outil JS : `cuire.js` (orchestration),
`lib/iso.js` (caméra), `lib/codes.js` (passes → codes), `lib/planche.js`,
`lib/controle.js`, `mesurer_vues.js`, recette `recettes/feuille_composee.js`
(fonction `feuille` du prototype). Sorties : `assets/splats/feuille_composee_x{0_5,1,2,4,8,16,32}.png`
+ `feuille_composee.json` ; contrôle `mesures/controle_feuille_composee.png`
(rampe 5 tons + soleil fixe haut-gauche, règle exacte du shader ; en bas, la rangée
« Composee » du kit actuel capturée par `capture_vm.sh -k`, agrandie ×10).
**Format = atlas du kit existant** : R = niveau (littéral F11 OFF), G = `128|ton<<4|orient`,
A = posé. Manifeste : palier, inclinaison, variante, lacet, planche, rect, attache.

**Mesures [VM, n=1 cuisson complète, charge ~1].**
- Sculpture+bake d'une forme : ~0,18 s. Photo d'une pièce : 84 ms (×0,5) · 130 (×1) ·
  305 (×2) · 277 (×4) · 267 (×8) · 853 (×16) · 3 140 (×32). Recette entière
  (504 pièces = 7 paliers × 8 lacets × 3 inclinaisons × 3 variantes) : **6 min 08 s**.
- Poids : planches 0,84 Mo (dont ×32 469 Ko, ×16 178 Ko) + manifeste 100 Ko ;
  contrôle 227 Ko ; vendor 11 Mo. Extrapolation ~15 feuilles + ③ ≈ 30-60 Mo [estimation, pas mesurée].
- Déterminisme : 2 cuissons complètes → sha256 IDENTIQUES sur les 8 fichiers + le contrôle.
- **V retenu = 8 lacets × 3 inclinaisons (−30°, 0°, +30°)**. Mesure (`mesurer_vues.js`,
  1 − IoU des silhouettes recalées sur l'attache, 96 photos/tour) : AUCUN coude —
  le saut entre vues voisines décroît linéairement (×4 : V=4 0,97 · V=8 0,81 · V=12 0,66
  · V=16 0,58 · V=24 0,49 ; mêmes valeurs ×0,5 → ×16). Inclinaison ±15° ≈ 0,6,
  ±30° ≈ 0,83 (≈ le pas de 45° en lacet). Donc « aucun saut visible quand l'organe
  tourne » n'est atteignable par AUCUN V aux paliers ≥ ×4 (une feuille fine qui
  tourne de 15° change de silhouette à 50 %). V=8 choisi parce que : multiple de 4
  (rotation D35 = vues exactes), même pas que la quantification des orientations
  (45°), poids ÷2 vs 16. **Conséquence pour ④** : choisir la vue sur l'azimut AU
  REPOS de l'organe (pas sur la pose de vent), sinon une feuille proche d'une
  frontière clignotera entre deux vues.
- **Lisibilité (regardée au Read, contrôle + comparaison au kit)** :
  ×0,5 (2-5 px) = une MARQUE orientée (tiret clair/sombre), pas une forme — ni
  plus ni moins lisible que la touffe 3 px du kit actuel ; ×1 (~8×4 px) = rameau
  de folioles orienté, lisible comme feuillage ; ×2 (~15×8) = feuille composée
  reconnaissable ; ×4 → ×32 = nettement plus riche que le kit (folioles,
  rachis, revers sombres). Réserves : pièces plus CLAIRES que le kit (une feuille
  couchée regarde « en haut » → +1/+2 ton dès que le soleil est haut ; le kit
  dôme répartit ses normales sur 8 directions) et sans contour sombre → contraste
  moindre sur sol ; à juger au F5 (⑤), réglable par `TON_DE` dans `cuire.js`.

**Écarts au kickoff (hypothèses réfutées / corrigées).**
1. Échelle : CLAUDE.md dit 78×39 px/plot ; le code dit **39×19,5 px INTERNES**
   (SubViewport ×2) → 0,39 px/cm × palier. Pièces calées sur les px internes.
2. La vue est une projection OBLIQUE (verticales à l'échelle du sol), une caméra
   ortho ne la reproduit pas : tangage 30° + lacet 45° = sol exact, verticales
   **+22 %**. Accepté (< 1 px jusqu'à ×4 sur une feuille) ; l'ORIENTATION, elle,
   est projetée par la vraie projection oblique (comme `PaletteIndexee.MajSoleil`).
3. Lire le splat propriétaire pixel par pixel = bruit poivre-et-sel illisible aux
   paliers bas : ajout d'un **suréchantillonnage** (×4 jusqu'à ×2, ×2 à ×4, ×1 dès
   ×8) puis moyenne normale/ton par pixel. C'est la « réduction » de D4, pas un
   contournement.
4. Ton : cuisson sans soleil (`sunK=0`, ambiant 0,75 + ciel 0,25 → revers ×0,75),
   10 crans de gris → tons 0/1/2 (seuils 0,2 / 0,5). Tons 3-4 jamais cuits (shader).
   Seuil « plat » = 0,3 (FacePlate du kit, ~17,5° face caméra).
5. Les pièces vont dans `assets/splats/` (une planche PAR PALIER : chargement ×16/×32
   à la demande possible au ④).

### ② Bibliothèque des feuilles (2026-11-20) — FAIT
**Fait.** 18 recettes de feuille + 6 touffes, toutes cuites dans `assets/splats/`
(une planche par palier, `<recette>_kit.png` pour les touffes, un manifeste par recette).
Briques nouvelles : `tools/splat/lib/limbe.js` (limbe en volume depuis un contour 2D
de la vue : 2 moitiés en coussin `S.puff` relevées en V autour de la nervure, pétiole,
gaufrage), `lib/feuille.js` (fabrique fiche → recette), `lib/trous.js` (trous D5 =
solides négatifs `{ neg: true }`), `recettes/touffe.js` (+ 6 `touffe_<forme>.js`),
`controle_feuilles.js` (planche de toute la bibliothèque, relue sur disque).
`cuire.js` : axes `trous`, `tailles` (+ `empriseCm`), lacets/inclinaisons propres à
la recette, défaut d'inclinaisons = −30,0,30 ; `planche.js` groupe par nom de planche.
Non-régression : `feuille_composee` recuite → pièces saines IDENTIQUES à l'octet
(×0,5-×8 inchangées, entrées saines du manifeste égales ; ×16/×32 : pièces trouées
ajoutées APRÈS les saines).

**Table « nom vue → recette »** (aussi dans le champ `vue` de chaque manifeste) :
Ovale + `LeafShape.Elliptique` → `feuille_ovale` · Lanceolee + `LeafShape.Lanceolee`
→ `feuille_lanceolee` · Coeur + `LeafShape.Cordee` → `feuille_coeur` · Composee +
`LeafShape.Composee` → `feuille_composee` · Paume + `LeafShape.Lobee` (palmilobée :
courge, figuier, vigne) → `feuille_paume` · `FormeFeuille.Lobee` (lobes PENNÉS :
chêne, moutarde) → `feuille_lobee` — **même mot, deux formes** : `LeafShape.Lobee`
couvre aussi chêne et moutarde (Leaf.cs) ; au ④ de choisir par espèce · Dentee →
`feuille_dentee` · Spatule → `feuille_spatule` · Scie → `feuille_scie` · Lierre →
`feuille_lierre` · Ruban → `feuille_ruban` · Cuillere → `feuille_cuillere` · Plume →
`feuille_plume` · Palmee → `feuille_palmee` · Triade → `feuille_triade` ·
`LeafShape.Aciculaire` → `feuille_aiguille` (absente de `FormeFeuille`) ·
Scie/Lanceolee + `Gaufre` → `feuille_scie_gaufree` / `feuille_lanceolee_gaufree` ·
kit `KitTouffe(LeafShape, 3|5|7|9, v)` → `touffe_<forme>` (planche `kit`, `taille_px`).
Contours RECOPIÉS de la vue (ContourDente, Spatule, Lobe, Ovale, Coeur, Scie, Lierre,
Paume, ProfilLanceole) ; dispositions de PoserPlume/Palmee/Triade/Cuillere.

**Marques.** Cuites (relief) : `Pli` (gouttière en V de 0,5 rad, dans TOUS les rubans),
`Gaufre` (sillons négatifs le long des nervures secondaires, 2 recettes `_gaufree` ;
tomate : la composée garde sa forme du prototype, pas de version gaufrée). Laissées à
la vue (couleur / brillance) : `Duvet`, `Gouttes`, `Eclat`, `Revers` (dessous argenté =
palette ; le revers en volume, lui, est déjà cuit via les inclinaisons), `Nervures`
(lierre : nervures PÂLES, couleur, à plat).

**Trous (D5).** Morsure (bord, degrés 1 = 1 bouchée, 2 = 3) et grêle (criblage,
1 = 3 trous, 2 = 7, grêlon ≤ 1 cm) ; aux seuls ×16 et ×32 (PaliersHauts.cs), les
encoches de grêle de Froid.cs sont servies par les morsures. **Décision : trous sur
la variante 0 seulement** (`TROUS_VARIANTES` = 1 dans cuire.js) — ×3 sur les
variantes = +~20 min CPU et ~×3 de poids troué par recette ; réversible. Pas de trous
sur aiguille ni plume (rien à cribler, la vue n'en dessine pas). Manifeste : `trou`,
`degre`.

**Mesures [VM, n=1 cuisson complète, 12 processus parallèles, charge ~13].**
- 24 recettes, **11 520 pièces** (dont 2 880 trouées, 72 touffes ; 223 vides : aiguille
  et cuillère aux paliers bas, quelques vues de profil à ×0,5).
- Temps : **48 min 44 s** mur, 288 min CPU ; une recette va de 39 s (aiguille) à 49 min
  (paume, rayon 29 cm : ×32 ≈ 10 s/photo en charge).
- **Poids** : `assets/splats/` = **14,8 Mo** (planches 12,3 + manifestes 2,5), soit
  +13,9 Mo au ② ; contrôles `mesures/` +1,8 Mo. Loin de l'alerte 200 Mo.
- Déterminisme : composée recuite = octets identiques au ① (pièces saines).

**Contrôles** (lus au Read) : `mesures/controle_feuilles.png` (toute la bibliothèque :
×1 + 8 lacets ×8, puis ×16 saine + 4 degrés de trous ; touffes en bas) et
`mesures/controle_<recette>.png` (toutes vues). Lecture : toutes les formes se
distinguent dès ×8, le pli en V donne deux faces (ombre/lumière) très lisibles, les
trous se lisent à ×16. Les touffes donnent des taches orientées variées (leurs feuilles
montent de 0 à ~50°) ; mêmes réserves qu'au ① (plus claires que le kit, sans contour).

**Points pour la suite.**
- **TAILLE** (④ ⑤) : une feuille est cuite à UNE longueur nominale par forme
  (ovale 9 cm, dentée 15, ruban 30, paume 20 + 6 de pétiole…, cf. `longCm` des
  recettes) ; la vue a des feuilles de 2 à 30 cm selon espèce et stade. Pas de mise à
  l'échelle (zooms entiers) → le ④ devra choisir : accepter la taille nominale, ou
  demander une classe de taille de plus (×2 pièces/poids) — décision à remonter.
- Largeurs (`large`) fixées par forme (médiane des fiches) : une seule géométrie sert
  des espèces plus ou moins larges.
- Le kit des touffes a la largeur de la taille demandée (±1 px) mais une hauteur
  ~moitié (vue iso), là où le kit actuel est carré : à juger au ⑤.

### ③ Têtes, fleurs, fruits, boutons, bois (2026-11-20) — FAIT, bois non livré
**Fait.** 22 recettes d'organes cuites dans `assets/splats/` (table « nom vue → recette »
dans le champ `vue` de chaque manifeste) :
- têtes (`FormeTete`, 13) : `tete_capitule` · `_bouquet` · `_chapelet` · `_epi` · `_ombelle` ·
  `_boule` (sert aussi la tête de graines du capitule) · `_grappe` · `_soleil` · `_etoile` ·
  `_pendante` · `_corolle` (sert aussi PoserFleurSnes et PiecesFleur) · `_trompette` · `_papillon` ;
- autres fleurs : `chaton` (PoserChaton), `epi_ble`, `epi_barbu` (seigle), `panicule` (pâturin) —
  dessinés par PortChaume, oubliés du kickoff ;
- fruits : `fruit_globe` (tous les fruits ronds, herbacées et arbres), `fruit_long` (courgette,
  `Allonge` > 1), `gousse` (haricot hors fleur) ; `bouton` (boutons floraux) ; `fleuron` (kit
  D4, tailles 1/2/3 px).
Briques : `lib/organe.js` (fabrique sans trous + pétale/boule/tige/corolle), `controle_organes.js`
(planche relue sur disque), `recettes/bois.js` + `couture_bois.js` (mesure). `cuire.js` : recette
peut fixer ses `paliers` ; **COUCHES** (`couches: [...]`) → une pièce par couche et par vue, même
attache, champ `couche` du manifeste (`lib/codes.js` : pixel à la couche majoritaire de ses
échantillons). Non-régression : `feuille_composee` ×0,5/×1/×2 recuite hors dépôt = octets
identiques ; aucune feuille du ② recuite.

**Couches cuites** (une palette par couche à l'assemblage, comme `CouchePiece`) : corolle et
fleuron `petales|coeur` · soleil `rayons|coeur|revers` · ombelle `fleurs|rayons` · chapelet
`fleurs|silicules` · bouton `petales|sepales` · fruits `fruit|pedoncule`. Les autres : une couche
(le cœur sombre de l'étoile ou le fond de la trompette = le creux, ton 0).

**Vues** : 8 lacets × 3 inclinaisons (V du ①) partout, sauf symétrie de révolution →
1 vue (`fruit_globe`, `bouton`, `fleuron`) ; `fruit_long` couché : inclinaisons −15/0/15.

**Mesures [VM, n=1 cuisson complète, 11 processus parallèles, charge ~12].**
- 12 702 pièces (832 vides : surtout couches de cœur aux paliers bas, ×0,5 de profil).
- Temps : **29 min 44 s** mur, 118 min CPU ; de 1 s (fleuron) à 24 min (tournesol, ×32).
- **Poids** : `assets/splats/` 14,8 → **24,9 Mo (+10,1 Mo)** ; contrôles `mesures/` +2,0 Mo.
  Cumul loin de l'alerte 200 Mo.
- Contrôles (lus au Read) : `mesures/controle_organes.png` (toute la bibliothèque) et
  `mesures/controle_<recette>.png`. Toutes les formes se lisent dès ×8 ; tournesol, ombelle,
  capitule, épis, chaton, courgette nets dès ×2 ; papillon et silicules du chapelet les plus faibles.

**Bois — couture MESURÉE, NON LIVRÉ** (`mesures/couture_bois.png`, `couture_bois.js`) :
5 tronçons de 8 cm posés le long de 3 vrais segments du « Pommier · an 10 » (tronc 15,1 cm
vertical, branche 7,4 cm, rameau 1,7 cm), ×8 et ×16, en A (direction exacte), B (vue du
catalogue 8 lacets × 0/30/60/90°) et C (un cylindre d'un tenant). **A montre déjà les joints**
(anneaux et fissures rompues sur le tronc, bourrelets sur le rameau) ; B y ajoute des marches de
0 / 1,3-2,7 / 3,2-6,3 px (×8-×16) ; C est propre. → la vue garde son bois dessiné (consigne du
kickoff, pas de bricolage). Aucune planche `bois_*` dans `assets/`.

**Écarts au kickoff (hypothèses corrigées).**
1. Liste des fichiers incomplète : les têtes sont dans `PortTetes.cs` (+ PortTigeFormes,
   PortTapis, PortRampante, PortVolubile, Prairie), fruits de port dans `Ports.cs`, épis de chaume
   dans `PortChaume.cs`. Inventaire refait au grep (sans DeepSeek).
2. `FlowerShape` / `DrawFlowerShape` (Flower.cs : Simple, Ombelle, Capitule, Papilionacee, Epi,
   Clochette) n'a **aucun appelant** = code mort (signalé, non supprimé, non cuit).
3. « Bourgeons » : la vue ne dessine aucun bourgeon végétatif → servis par `bouton`.
4. Oblique : ③ **tasse les axes** (× 0,816 en vertical) avant la caméra ortho (`lib/organe.js`)
   → épis, gousses, chatons tombent sur la projection de la vue ; rayons gardés ronds. Les feuilles
   du ② ne sont pas tassées (couchées, écart < 1 px jusqu'à ×4) — incohérence mineure assumée.
5. **Échelle des organes ronds** : la vue dessine un disque de r cm à r × 0,39 px/cm × zoom
   (PxPerCmX), la caméra (fidèle au losange du sol) à r × 0,55 → les têtes et fruits cuits sont
   **√2 plus gros** que les disques d'aujourd'hui (même échelle que les feuilles du ②). Le bois,
   lui, colle (WoodWidthFactor 1,5 → 0,585 contre 0,55).

**Points pour la suite (④ ⑤).**
- TAILLE NOMINALE par recette (médiane des fiches, en tête de chaque recette) : tête 0,8 à
  12,5 cm selon l'espèce, épi de 8 cm (la vue le fait suivre la hampe), chapelet sur hampe de
  20 cm, globe de 2 cm (cerise 1 → pomme 3,5 ; fruit d'arbre qui grossit avec la maturité). Même
  arbitrage que les feuilles du ② : taille nominale ou classes de taille.
- Échelle √2 ci-dessus : accepter (cohérent avec les feuilles) ou réduire les rayons nominaux.
- **Planches trop hautes** : `tete_soleil_x32` 2020×12 375 (25 Mpx, refusée par le lecteur PNG
  d'ink-studio, sautée par `controle_organes.js`) et, héritée du ②, `feuille_paume_x32`
  2042×17 394 (> 16 384, limite usuelle d'une texture GPU) → le ④ devra scinder ces planches.
- Les couches de cœur s'effacent sous ~×2 (pièces vides) : la vue posera alors la couche 0 seule.

### ④ Vue ×4 → ×32 (2026-11-20) — FAIT, PARTIEL (périmètre ci-dessous)
**Fait.** `visuals/SplatPlanches.cs` (chargeur : manifestes, planches → textures de CODES
`(1,1,G,1)`, bandes ≤ 16 384 px, cache du seul palier courant) + `visuals/PlantRenderer.Splats.cs`
(choix forme → recette, vue, variante, trou ; pose au point d'attache, palette = celle que la vue
calculait déjà). Crochets d'UNE ligne (ancien dessin intact derrière) : `PoserFeuillePort`
(rosette), `PoserFeuilleTige` (tige, volubile, **feuilles d'arbre ×8+** via la fiche-limbe),
`PoserFeuillePaume` (rampante), `PoserFeuilleTapis` (chaque foliole), `PoserTete` (13 têtes,
une palette par couche), `PoserFruit` (globe / long). Criblage vectoriel coupé quand la feuille
est une pièce (`_feuillesSplat`, PaliersHauts/Prairie : trous D5 = la pièce, ×16-×32, variante 0).
**Interrupteur** : Maj+F11 (Controls.cs) ou `SYMBIOSE_SPLATS=0` au lancement ; éteint, F11 OFF,
dessin direct ou pièce absente/vide → ancien dessin vectoriel.

**Chargement (justification).** `importer="keep"` : 280 `assets/splats/*.png.import` écrits
(3 lignes chacun) ; lecture par `Image.LoadFromFile` = décodeur PNG de Godot sur le fichier même →
octets INTACTS (pas de compression VRAM, pas de mipmap, pas de `fix_alpha_border` qu'aurait
l'import « texture »), et « keep » copie le PNG tel quel dans le .pck à l'export (t7). Testé sur
la VM : `godot --headless --import` respecte les `keep` (aucun `.ctex` produit pour les planches) ;
l'import a semé 154 `.import` parasites (docs/, sprints/) → supprimés. Sans ces fichiers, l'éditeur
Windows importerait les 280 planches en textures (et échouerait sur celles > 16 384 px).
**Planches > 16 384 px** : découpées EN MÉMOIRE au chargement (coupe entre deux rangées de pièces,
octets des pièces copiés tels quels) → **aucune planche régénérée** (arbitrage « repack outil »
non nécessaire, D2 : historique git intact).

**Choix de vue.** Lacet = direction ÉCRAN de l'organe au repos (`WorldToScreenOffset(fe.U)`)
défaite par la projection d'orientation 0 → angle vu par la caméra, rotation D35 comprise
(capture `-r 1` : les feuilles changent de vue, restent du même côté). Inclinaison = montée du
bout (`HautZ` / emprise au sol). Pas la pose de vent (arbitrage) : le vent ne déplace que l'attache.
Têtes : lacet au hash, inclinaison la plus proche de 0. Fruit long : lacet de l'angle au hash de
`PoserFruit`. Attaches : base de l'épi (tiers haut de la hampe), foyer de l'ombelle (2,75 cm sous
le plateau), sommet ailleurs ; centre pour les fruits.

**Mesures [VM, banc planche_especes, n=1 capture par palier, charge ~1-2].**
- Cuisson, régime établi (planches et manifeste déjà chargés) : carotte ×8 0,68 ms contre
  0,54 ms vectoriel [n=1 plante] — même ordre. Premier usage d'une recette : lecture du manifeste
  JSON ≈ 20-70 ms [estimé par différence, tomate 116 ms dont 43 ms de planches] + planche 2 ms (×4)
  à 153 ms (`feuille_scie_gaufree_x32`, 2028×2145) → **à-coup unique au changement de palier**,
  chronométré depuis au journal (`[Splats] manifeste … ms`). Tomate ×8 : 116,7 ms 1ʳᵉ cuisson
  contre 1,3 ms vectoriel.
- Mémoire vidéo des planches de codes (RGBA8) : ×4 2,7 Mo (13 planches), ×8 5,4 Mo, ×32 17,7 Mo
  pour UN fraisier (3 planches) [n=1 cadrage par palier]. Plafond théorique si toutes les planches
  d'un palier servaient : ×16 225 Mo, ×32 835 Mo [somme des planches] → d'où le cache du seul
  palier courant (les autres sont rendus au changement de palier).
- Poids dépôt : +280 `.import` (~8 Ko) ; aucune planche touchée ; `assets/splats/` 26 Mo.

**Captures (lues au Read)** : `mesures/vue4_{avant,apres}_x{4,8,16,32}.png` (planche_especes,
tomate ×4/×8, courgette ×16, fraisier ×32) et `mesures/vue4_{avant,apres}_x8_r1.png` (rotation D35).
Lecture : volume net (folioles, revers sombres, gaufrage du fraisier, courgettes cylindriques) ;
ombelle de la carotte et étoile de la tomate en pièces. **Défauts** : (1) TAILLE — pièces à la taille
nominale de leur recette, plus grandes que le dessin : feuilles de fraisier ~×1,5, fraise et courgette
~×2 en diamètre (nominal + √2 du ③), plume de carotte plus étalée ; (2) paume de courgette à ×16
presque plate (2 tons) ; (3) les marques vectorielles (duvet, éclat, revers d'armoise, nervures
pâles du lierre, gouttes de drosera) ne sont PAS posées sur une feuille-pièce (leurs positions
suivaient la géométrie dessinée, pas celle de la pièce) ; poils ×32 et gel/taches restent aux sites.

**Écarts au kickoff / hypothèses corrigées.**
1. Les pièces ne passent pas par l'import Godot (keep + LoadFromFile) : « vérifier qu'un import
   produit les mêmes octets » devient sans objet — c'est le PNG lui-même qui est lu.
2. Les organes d'un port sont dans un LOT de triangles (un envoi, peint à la fin) : chaque pièce
   vide le lot avant d'être tracée (ordre de peinture conservé).
3. **Périmètre non couvert (toujours dessiné)**, faute de crochet unique : prairie (trèfle, plantain,
   dactyle, fétuque), chaume (rubans, `epi_ble`/`epi_barbu`/`panicule` pourtant cuits), masses du
   buisson, feuilles de hampe, gousses (`PoserGousses`), boutons, chatons, ARBRES à ×4 (gerbes)
   et leurs fleurs/fruits (PiecesFleur, FleursArbre, FruitsArbre), chemin générique `DrawOrgans`
   (espèces sans fiche). À trancher par l'orchestrateur : tronçon ④ bis, ou au fil de ⑤.
4. Bois : dessiné (③). Pas de classe de taille créée (arbitrage) ; écart signalé au F5.

### ④bis Vue ×4 → ×32, couverture complétée (2026-11-20) — FAIT
**Fait.** `visuals/PlantRenderer.SplatsOrganes.cs` (neuf, 63 LDC) : `PoserOrganeSplat` (organe
générique : toutes ses couches, lacet écran ou au hash, inclinaison la plus proche de 0, la
pose naturelle — seigle retombant, gousse et chaton pendants — étant CUITE dans la recette).
`PlantRenderer.Splats.cs` : la fin de `PoserFeuilleSplat` factorisée en `PoserPieceFeuille`
(attache + inclinaison + direction écran), partagée avec le chemin générique ; `RecetteTete`
renvoie `null` pour `Papillon` hors fleur (le ④ posait `tete_papillon` sur les gousses : bogue
corrigé, les gousses passent par `gousse`). Crochets d'UNE ligne, ancien dessin intact :
- chaume : `PoserEpis` → `epi_ble` (blé) / `epi_barbu` (seigle), lacet = côté où penche le brin ;
  `PoserPanicule` → `panicule` (pâturin, teinte des épillets verts) ;
- haricot : `PoserGousses` → 2 × `gousse` ;
- arbres et segments : `PoserChaton` → `chaton` ; `PoserFleurSnes` → `tete_corolle` ;
  `DrawPiecesFleurs` → `bouton` (teinte de bouton d'espèce, sépales du feuillage) ou
  `tete_corolle` ; **×4 : pièces allumées, la fleur d'arbre est posée une à une** (chemin du ×8,
  plafond `FleursArbreMax`) au lieu des gerbes de fleurs ; fruits d'arbre : déjà couverts au ④
  (`DrawFruitsHouppier` → `PoserFruit`) dès ×4 ;
- prairie : `PoserBoule` → `tete_boule` (pompons du trèfle, glomérules du dactyle ; attache
  1,8 cm sous le centre de la boule) ; feuilles du plantain → `feuille_lanceolee` ; épi du
  plantain → `tete_epi` ; feuilles de hampe (molène) → recette de la forme de la fiche ;
- chemin générique `DrawOrgans` (plantes sans fiche : jeunes arbres, squelettes) : feuilles ×8+
  → recette de la `LeafShape` d'espèce (Aciculaire→aiguille, Cordée→cœur, Composée, Lancéolée,
  Lobée→paume, sinon ovale), attache au point d'insertion, sauf feuille naissante sous le
  plancher de rayon ; fleurs ×4 (points) et ×8 → `tete_corolle` ; fruits ×4+ → `fruit_globe`.
- **Lot de triangles** : un lot périmé (déjà envoyé, pas vidé) était re-tracé par la 1ʳᵉ pièce
  qui « vide le lot » → `Vider()` ajouté avant les pièces dans `DrawFleurs`, `DrawFruits`,
  `DrawPiecesFleurs` et la boucle de feuilles générique.

**Reste DESSINÉ (et pourquoi)** — ni recette à la bonne échelle, ni crochet propre :
1. feuilles du TRÈFLE (3-4 folioles de 3 cm) : `feuille_triade` est la feuille du haricot,
   14 cm (~×4 trop grande), et aucune recette à 4 folioles ;
2. BRINS et RUBANS des graminées (dactyle, fétuque, rubans du chaume) : lanières de 5 à 80 cm
   que le vent plie point par point ; `feuille_ruban` est fixe (30 cm) et la pièce ne bougerait
   plus qu'à l'attache, au sol → la prairie ne ploierait plus ;
3. MASSES du buisson (grains du thym, lames de la lavande) : abstraction de feuillage, sans
   recette (grain 1,9 cm, lame 8 cm contre aiguille 3 cm / ruban 30 cm) ;
4. panicule de la FÉTUQUE (épillets roux de 0,5 cm) et anthères du blé : trop fins ;
5. ARBRES ×4 : masses de feuillage (gerbes de feuilles, `DrawGerbesPalierMasses`) — pas de
   recette de masse (les `touffe_*_kit` sont le ⑤) ; masses ×4 des plantes génériques
   (`DrawMassesFeuillage`) idem ;
6. BOIS (③ : couture visible), et toutes les marques vectorielles déjà listées au ④
   (duvet, éclat, nervures du plantain, pruine ×32 des fruits génériques).

**Vérif.** Golden `bce813af…` INTACT. `dotnet build` vert, 0 avertissement. Fichiers : Organs.cs
321 LDC (était 318, 🟡 préexistant), Prairie.cs 303, Splats.cs 157, SplatsOrganes.cs 63.
**Captures [VM, n=1 image par cas, charge ~2]** `mesures/vue4bis_{avant,apres}_*.png` (avant =
`SYMBIOSE_SPLATS=0`) : `cereales_x4` (blé, haricot, poivron), `cereales_x8` (épis de blé),
`seigle_x8`, `haricot_x8` (gousses), `prairie_x4` (trèfle, minette), `prairie_x8` (plantain :
feuilles + épi), `verger_x4`/`verger_x8` (`verger_floraison -w 0` : pommiers en fleur). Lecture :
épis bien posés sur leur chaume, seigle retombant dans des directions variées, gousses pendues aux
mêmes points ; fleurs de pommier à ×8 en corolles volumées un peu plus petites que les pièces
dessinées (nominal 1,3 cm de rayon contre 2 cm) ; **×4 : fleurs d'arbre plus CLAIRSEMÉES qu'avec
les gerbes** (fleurs une à une plafonnées) ; jeunes pommes ~×2 (taille nominale, point F5 du ④).
Chatons non capturés (aucun banc ne force la floraison du noyer et de ses pareils).
**Signalé** : chaque première lecture d'une planche émet au journal Godot « Loaded resource as
image file, this will not work on export » (`Image.LoadFromFile` sur `res://`, depuis le ④) — à
vérifier au packaging (t7) : l'hypothèse « keep copie le PNG dans le .pck » n'est pas démontrée.

## F5 (recette pour Nico — complétée par ④⑤⑦)
**④ (×4 → ×32)** — banc `planche_especes`, zoomer ×4 → ×32 sur tomate, carotte, courgette,
fraisier, tournesol, poivron ; Maj+F11 pour comparer avec l'ancien dessin.
- Les feuilles, têtes et fruits ont du VOLUME ; le côté éclairé suit le soleil (heure qui tourne).
- PgUp/PgDn (rotation D35) : les feuilles changent de vue sans « sauter » de côté ; vent fort :
  elles suivent la tige sans clignoter.
- `tailler` marche toujours au pied (taille au port).
- **À calibrer** : la TAILLE (feuilles, fraise, courgette, têtes ~×1,5 à ×2 du dessin d'avant —
  garder, réduire les rayons nominaux des recettes, ou classes de taille ×2 de poids) ; la paume
  de courgette trop plate à ×16 ; la perte des marques (duvet, éclat, revers, nervures du lierre).
- Changement de palier : un court à-coup la 1ʳᵉ fois (lecture des planches) — gênant ou non ?

**④bis** — mêmes gestes, sur blé / seigle / pâturin, haricot en gousses, plantain, trèfle en
fleur, et un pommier en fleur (`verger_floraison`) ; Maj+F11 pour comparer.
- Épis, panicule, gousses, pompons, épi du plantain, fleurs et boutons d'arbre en volume ; le
  seigle retombe toujours, dans des directions variées, et suit la rotation D35.
- **À juger** : à ×4 le pommier fleuri est-il assez fleuri (fleurs une à une au lieu des gerbes,
  plus clairsemé) ? Les chatons (noyer, noisetier…) en floraison réelle. La prairie garde ses
  brins et le trèfle ses feuilles dessinés (cf. compte rendu) : le mélange se voit-il ?

# Carnet de conception (historique)

## Contexte
- Prototype tomate validé par Nico (« c'est ça que je veux pour Symbiose ») :
  `docs/rendu/splatting/prototype/` (ink-studio CPU sur la VM, 106 000 splats,
  cuisson 17 s [n=1 plant, VM]).
- Refonte 3D temps réel = horizon (mémoire `project_refonte_splatting`) ; PC de Nico
  en cours d'achat, budget serré : carte 8 Go probable, 16 Go de RAM.
- Ce sprint = amener le rendu splat DANS la vue actuelle (iso 2D) par PRÉCUISSON
  hors ligne (images produites sur la VM, affichées par Godot).

## Faits vérifiés (code)
- Vue : cuisson EN JEU par plante (`visuals/PlantBaker.cs`, atlas de poses de vent
  ≤ 8, pages communes `AtlasPages`) depuis un dessin vectoriel ; paliers bas
  ×0,5-×2 = « plante assemblée » : vrais segments + TOUFFES du kit
  (`PlantRenderer.Kit.cs`, 3-9 px, codes de palette indexée ton + orientation de
  face lus par shader, lumière côté soleil réel).
- Moteur : la tomate n'est qu'une tige droite (port inventé côté vue).
- Catalogue : 54 espèces [classes distinctes des 5 tables de `plants/catalogue.py`].
- ink-studio : export `atlas --directions N --maps depth,normal,...` (cartes de
  normales → codes d'orientation de face possibles).

## Décisions arrêtées
- **D1 (Nico 2026-11-20) fidélité MAX au moteur dans le jardin** : la plante en jeu
  suit ses vrais segments (taille au segment, phototropisme, vent, santé, rotation
  D35). → plantes entières précuites (A) EXCLUES en jeu ; reste B (kit d'organes
  précuits assemblé sur les segments) ou C (B + portraits entiers hors jeu).
- **D2 (Nico 2026-11-20) images versionnées dans git** (git = seul canal
  VM→Windows) avec les recettes. Place disque côté Nico non limitante (30 Go libres
  sur le PC actuel). Garde-fou retenu : poids du dépôt mesuré à chaque tronçon,
  alerte si le kit dépasse ~200 Mo (croissance de l'historique à chaque
  régénération, pas le disque) ; régénérer seulement ce qui a changé.

- **D3 (Nico 2026-11-20) option C** : kit d'organes précuits en splats assemblé
  sur les vrais segments DANS le jardin + PORTRAITS entiers (façon prototype
  tomate) pour encyclopédie / magazine / carnet (hors jeu, sans contrainte de
  fidélité segment par segment).

- **D4 (Nico 2026-11-20) TOUS les zooms en splats** (×0,5 → ×32) : le kit pixel
  des paliers bas (touffes 3-9 px, fleurons) est lui aussi généré depuis les
  recettes splat (réduction + quantification), plus de pièce dessinée à la règle.
  « Tous les graphismes » : périmètre au-delà des plantes → lot 3.
- **D5 (Nico) symptômes ×16** : TROUS (morsures, criblage de grêle) = variantes
  précuites de chaque feuille, 2-3 degrés ; COULEURS (nécrose, taches, givre) =
  palette / peint par-dessus, comme aujourd'hui.
- **D6 (Nico) portraits** : 3 par espèce (jeune · mûre en pleine saison · fin de
  cycle / hiver), dévoilés avec les 3 niveaux de fiche de l'encyclopédie ; le
  magazine montre le portrait mûr.

- **D7 (Nico 2026-11-20) programme « tout en splats »**, un sprint par famille,
  F5 entre chaque : (a) plantes [CE sprint] → (b) décor de lisière → (c) faune +
  champignons → (d) structures + maison → (e) sol, litière, eau, neige, météo →
  (f) icônes. Les sprints (b)-(f) sont à concevoir après le F5 de (a).
- **D8 (Nico) icônes de gestes = petits objets en splats** (trois quarts), sous
  réserve d'un F5 de lisibilité avant de remplacer les icônes actuelles (sprint f).

## Faits vérifiés (lot 2)
- Grammaire de la vue (`PlantRenderer.PortsFiches.cs`) : 7 ports (Rosette, Tige,
  Chaume, Tapis, Buisson, Rampante, Volubile) + arbres (Houppier/Arbres), 15 formes
  de feuille, 14 formes de tête (inflorescences), 8 marques. → bibliothèque de
  recettes = ce vocabulaire, PAS 54 recettes d'espèce.
- Paliers hauts (`PaliersHauts.cs`) : ×4 masses de feuillage + points ; ×8 organes
  (forme de feuille, fleur par famille, fruit globe) ; ×16 symptômes (morsures,
  grêle, nécrose, taches, givre) ; ×32 intime (nervures 2ᵉ, étamines, poils).
- Palette indexée (`visuals/PaletteIndexee.cs:14`) : pixel = n° de palette (R,G) +
  B = 128 | ton(0-4) << 4 | orientation(0-7 écran, 8 plat). Une pièce splat peut
  s'y couler : ton = volume (creux/ombre/base/clair), orientation = normale
  quantifiée (carte de normales ink-studio), palette posée à l'assemblage → UNE
  géométrie de feuille sert toutes les teintes (espèce, saison, santé, maturité).
- Panneaux existants : `world/EncyclopediePanel.cs`, `MagazinePanel.cs`,
  `CarnetPanel.cs`.

## §REPRISE
Lire `CLAUDE.md`, ce fichier, la conception, puis le kickoff du premier tronçon
« à faire » de la carte. ①②③④ faits, ④bis fait (non commité) : couverture ×4-×32 complétée là où
une recette existe ; reste dessiné listé au compte rendu ④bis. Outils réutilisables tels quels :
`SplatPlanches.Trouver`, `PoserPieceSplat`, `PoserPieceFeuille`, `PoserOrganeSplat`. **Prochain :
⑤** (`05_vue_paliers_bas.md`, paliers ×0,5-×2 : planches `touffe_*_kit` / `fleuron_kit` ; les
masses ×4 d'arbre et de plantes génériques, sans recette, pourraient y trouver leurs touffes).
Tailles nominales et densité des fleurs d'arbre ×4 = points F5 ouverts. Golden `bce813af…` intact.
