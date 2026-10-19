# Sprint PLANTE ASSEMBLÉE — état partagé

> Conception **FIGÉE le 2026-10-19** (`/conception`) →
> [`docs/rendu/pixelart/conception_plante_assemblee.md`](../../../../docs/rendu/pixelart/conception_plante_assemblee.md)
> (LIRE AVANT TOUT TRONÇON). Entrée : `docs/rendu/pixelart/entree_plante_assemblee.md`.
> Absorbe **D109 (d)(e)(f)**. **Golden jamais re-figé** : référence `22768f33…`
> (`cd data/code && python3 -m tests.test_golden`). Jamais `test_epaisseur_500ans`.

## Décisions clés (Nico, 2026-10-19)
1. UN sprint : perf ×4 + accéléré → silhouettes → légende des signes (+ bug légende F1). Un seul F5 final.
2. Paliers bas (×0,5-×2) = **plante assemblée** : vraies tiges 1 px + touffes de kit générées depuis
   `LeafShape` par espèce, posées sur les vrais segments. **×4+ inchangé.**
3. « Pixels plus fins » = éléments plus petits ; **pas de pleine résolution** (décision 8 PERF VUE close).
4. Info-bulle 2 niveaux : descriptive par défaut, cause / nom de bête une fois **appris** (palier du
   concept ≥ seuil du carnet interprétatif) ; + touche **affichage technique** (comme F6).
5. Accéléré : instrument + correctifs des suspects pendant le sprint ; UN banc PC en fin (⑦).
6. Observation d'un signe = commande pont au survol (comme `observer`), JAMAIS dans le tick.

## Constats d'entrée (vérifiés)
- Ventilation draw calls ×4, banc E s45 [VM, n=1] : total 2 013 · **Decor 1 099** · couvre-sol 449 ·
  Objects 380 · macro/ciel/météo 34 · Ground 0 (masquage sans effet, à comprendre au ①).
- PC [n=1] : ×4 = 32,5 FPS, 28,7 ms de rendu CPU, ~14 µs/draw call ; accéléré ×8 3 s/sem = 5 FPS.

## Carte des tronçons
| # | Kickoff | Contenu | Golden | État |
|---|---|---|---|---|
| ① | `01_decor_couvresol_lot.md` | Decor + couvre-sol en maillage | intact | **FAIT** (2 030 → 471 draw calls ×4) |
| ② | `02_plantes_atlas_commun.md` | plantes en pages d'atlas communes (D109 d) + bilan ×4 VM | intact | **FAIT** (×4 : 471 → 114 draw calls ; + maison en lot, hors kickoff) |
| ③ | `03_accelere_legende_f1.md` | banc accéléré + postes + priorité + ForagerLayer ; bug F1 | intact | **FAIT** (Maj+E ; butineurs _Draw 1,54 → 0,58 ms/image ; F1 tient) |
| ④ | `04_kit_elements.md` | atlas du kit (touffes, fleurons) + planche | intact | **FAIT** (atlas 84×70 px, 72 touffes + 3 fleurons ; planche `capture_vm.sh -k`) |
| ⑤ | `05_montage_paliers_bas.md` | plante assemblée à ×0,5/×1/×2 | intact | **FAIT** (`PlantRenderer.Assemblee.cs` ; ×4/×8 identiques au pixel) |
| ⑥ | `06_signes_python.md` | corpus signes + faune, observer étendu, carnet, encyclopédie, `appris` | intact (pont bumpé) | **FAIT** (corpus 11 signes + 20 bêtes ; `observer`+`signe` ; `player.appris` ; pont 0.5.46) |
| ⑦ | `07_vue_infobulle_bilan.md` | info-bulle 2 niveaux + technique + bilan + procédure PC + F5 | intact | à faire |

## Mesures
(à remplir par chaque tronçon : [machine, n=…] sur chaque chiffre)

### ① Decor + couvre-sol en lot (`visuals/LotTriangles.cs`, un `DrawMesh` par couche)
- Draw calls ×4, banc E s45 (`perf_vm.sh -E 20 -z 4`) : **2 030 [VM, n=1] → 471 [VM, n=1]**.
  Frame moyenne 117 → 91 ms [VM llvmpipe, n=1 chacun — non transposable au PC].
- Part de chaque couche avant, par masquage (`-E 5 -x …`, réf. 2 030) : Decor −1 077,
  Couverture −252, Litter −180, Allelopathie −8, Puddle −8, Mulch −5, LeafLitter −3
  [VM, n=1 chacun]. **LeafLitter laissée telle quelle** : elle dessine avec le kit de
  feuilles de `PlantRenderer` (formes, nervures, contours) — la mettre en lot = toucher
  au dessin des plantes (②) pour −3 draw calls.
- Image : 22 captures avant/après (×0,5/×1/×2/×4, seeds 42 et 2 — forêt, rivière,
  falaise, prairie —, orientations 0-3) : **géométrie identique au pixel** ; seul écart
  ±1/255 sur un canal [VM, n=22 images] = couleurs de sommet du maillage stockées sur
  8 bits (float avant). Recentrage essayé : déplace l'écart sans l'annuler → abandonné.
- **Ground « sans effet » expliqué** : le sol est déjà en lot depuis D106 (un maillage
  par tuile) → masqué = −11 draw calls [VM, n=1], dans le bruit du relevé n=1 d'entrée.

### ② Plantes en pages d'atlas communes (`visuals/AtlasPages.cs`) + maison en lot
- **Prémisse du kickoff fausse** (vérifiée par masquage, ×4 banc E s45, toutes couches masquées
  sauf `Objects`) : `Objects` ≈ 380 draw calls n'étaient PAS les plantes. **Maison ≈ 345**
  [VM, n=1] (`HouseNode` : un `DrawColoredPolygon` = un envoi), **plantes cuites ≈ 36** [VM, n=1].
  → la maison est passée au `LotTriangles` de ① (même ordre peintre, un `DrawMesh`) — écart au
  kickoff assumé : c'était le seul levier pour « Objects ÷ ≥ 3 ».
- Plantes : pages partagées 2048² par zoom (étagères de hauteur arrondie à 16 px, first-fit,
  trous fusionnés ; page dédiée si plus grande ; gomme `blend_disabled` + `ClearMode.Never` →
  une cuisson ne repeint que SON rectangle). Godot 4.6 `gl_compatibility` regroupe bien les
  plantes consécutives de même page : images cuites ×4 36 → 19 [VM, n=1], ×2 −41 [VM, n=1],
  ×8 −5 [VM, n=1] (maison masquée, HUD seul = 41 [VM, n=1]). Reste : tri Y/strates intercalés
  et plusieurs pages.
- **Bilan ×4 VM (banc E s45, `perf_vm.sh -E 20 -z 4`)** : draw calls **2 013 (entrée) → 471
  (après ①) → 114 (après ②)** [VM, n=1 chacun] ; `Objects` 382 → 31 [VM, n=1] (÷12) ;
  médiane 87,2 → 81,7 ms [VM llvmpipe, n=1 chacun — non transposable au PC].
  ×8 : 453 → 105 draw calls [VM, n=1], médiane 79,0 → 73,5 ms [VM llvmpipe, n=1].
- Mémoire vidéo du cache : ×4 34,4 → 48,0 Mo, ×8 93,8 → 118,3 Mo [VM, n=1] (granularité de page).
  File de cuisson du banc : 774 → 533 images pour vider [VM, n=1] (plus de SubViewport créé par cuisson).
- Seuil de vidange (page < 25 % occupée et une autre page du zoom existe) : **0 vidange** au
  banc E ×8 [VM, n=1] — seuil non éprouvé, le compteur est dans le log `[Cuisson]`.
- Image : 24 captures avant/après (×1/×2/×4/×8, vent 0 et 0,6, 4 cadrages dont la maison, 3
  instants chacune) **identiques au pixel, 0 px d'écart** [VM, n=24 images].

### ③ Banc accéléré + postes + butineurs + légende F1
- **Banc accéléré** = **Maj+E** au F5 (E reste le banc nominal ; touche choisie indépendante de la
  disposition AZERTY/QWERTY, comme Maj+A / Maj+F) : semaine 35, ×8, mode **Continu** 3 s/semaine,
  même centre que E, rapport copié. VM : `tools/perf_vm.sh -E 20 -z 8 -A 3 -W 35` (en-tête « banc E »
  en capture, mêmes paramètres). Constantes : `world/WorldView.BancAccelere.cs`.
- **Écart corrigé** : `-A s` laissait le mode Saison → au passage de saison (s39) la vue repassait
  en planification et coupait les steps. Cadence imposée ⇒ mode **Continu** désormais.
- Postes ajoutés au rapport : butineurs `_Process`/`_Draw` (PerfPostes) ; par step : durée vue,
  tick moteur, pipe (calcul+transport), **parse JSON** (thread du pool), taille de réponse ; **retard
  de cadence** (step en vol / semaine en application) ; **priorité du moteur relue par l'OS**
  (`SimBridge.PrioriteEffective`). GC et étalement par famille : déjà au bloc à-coups (PERF VUE ④).
- Accéléré ×8 3 s/sem, s35→41, VM llvmpipe [VM, n=1 chacun, avant → après] : butineurs `_Draw`
  **1,54 → 0,58 ms/image** ; images > 100 ms 35 → 25 [bruit n=1] ; médiane 77,0 → 76,6 ms ;
  draw calls 223-224. Cadence obtenue 3,33 s/semaine (6 semaines) ; step vu par la vue 1 041-1 068 ms
  dont tick moteur 778-780 ms, pipe 945-952 ms, **parse 55-71 ms (max 113)**, réponse 517 Ko ;
  retard de cadence **0,0 s** [VM, n=1] ; priorité lue **BelowNormal (base 10)** [Linux VM, n=1 —
  Windows à lire au ⑦].
- **Prémisse du kickoff nuancée** : `ForagerLayer` ne redessinait pas « à chaque image » mais à
  24 Hz — soit chaque image dès que le FPS < 24 (le cas accéléré). Mesure (sonde temporaire,
  retirée) : le **pollen déposé** faisait ~0,8-1,5 ms des ~1,5 ms (111-144 fleurs, 470-704 points)
  [VM, n=6 relevés]. → pollen extrait dans `visuals/PollenLot.cs` (enfant `ShowBehindParent`,
  dessous des butineurs comme avant), redessiné **sur signal** (dépôt/élagage/saison, ≤ 4 Hz ;
  pan/zoom/rotation immédiat) ; les butineurs gardent leur 24 Hz (vol). Code de tracé inchangé.
- **Nouveau suspect (hors périmètre, pour ⑦)** : les pires images accélérées sont la **file de
  cuisson** (52-72 ms dans UNE image, 3,2 ms/image en moyenne, ~230 cuissons/20 s) [VM, n=2 runs] —
  la file ne semble pas bornée en temps par image à ×8. À trancher au banc PC du ⑦.
- Nominal ×4 (`-E 20 -z 4`, s45) : draw calls 111 [VM, n=1] (109 au 2ᵉ run, VM chargée), 0 butineur.
- **Légende F1** : le bloc avait une position FIXE (1080−96) pour 4 lignes repliées → bas coupé.
  Désormais ancré en bas, grandit vers le haut (`BottomWide` + `GrowVertical = Begin`) ; + « Maj+E
  banc accéléré ». Capture VM `tools/capture_vm.sh -a` (option ajoutée) : 4 lignes entières, bas à
  ~1 065 px [VM, n=1 image].
- Taille : `core/SimBridge.cs` **301 LDC** (bande vigilance, une seule responsabilité — le pont) ;
  `WorldView.Hud.cs` 297 ; `ForagerLayer.cs` 281 → 255.

### ④ Kit d'éléments (`visuals/PlantRenderer.Kit.cs`, planche `world/WorldView.PlancheKit.cs`)
- **Atlas R8 de NIVEAUX** (0 vide · 1 contour · 2 ombre · 3 base · 4 lumière · 5 cœur), généré
  à la 1ʳᵉ demande (`KitNiveaux`) : 6 `LeafShape` × tailles 3/5/7/9 px × 3 variantes au hash
  (canaux 61-69, zéro Random) + fleurons point 1×1 / bouton 2×2 / étoile 3×3 = **84×70 px** [VM, n=1].
  Une touffe = feuilles analytiques (u le long, v en travers) rastérisées sur 3×3 sous-échantillons,
  ordre nord→sud (le sud devant), ombre de séparation ≥ 5 px, contour 1 px ≥ 7 px.
- API pour ⑤ (dans `PlantRenderer`) : `KitTouffe(forme, taille, variante)` → `Rect2I`,
  `KitFleuron(Fleuron)`, `RampeKit(couleur)` (même hue-shift OrganShade/OrganLit que ×4 ; cœur =
  `FlowerHeart`), `TeindreKit(rect, rampe)` → Image RGBA8. Teinter = remplacer l'indice par la rampe.
- **Écart au kickoff** : `HueShift` scindé en `HueShiftPur` statique (même arithmétique ; l'instance
  garde `_coolShiftScale`) pour teinter hors instance. ×4+ non touché.
- **Lumière vers le BAS de la pièce** (sud de l'orientation 0) : le kit, cuit une fois, ne suit PAS la
  rotation D35 (×4 la suit via `SouthDir`). À trancher en ⑤ (miroir par orientation ?) ou F5.
- Planche (capture `-k` : loupe ×10 teinte tomate + 3 teintes ×4 et ×2) jugée : à 3 px lancéolée (V
  dressé) ≠ composée (anneau ajouré) ; aciculaire = traits fins dès 5 px ; à 7-9 px lancéolée, lobée,
  cordée (échancrure), aciculaire reconnaissables [VM, n=1 planche]. **Faibles** : à 3 px les 3
  variantes de composée sont identiques ; elliptique ≈ cordée à 7-9 px (blob ±échancrure) ; composée
  7-9 px peu ajourée. Réglages dans les `switch` de `DisposerFeuilles`/`Dedans` (point F5).
- Déterminisme : 2 captures de la planche **md5 identiques** [VM, n=2]. Build vert, 0 avertissement.
  Taille : `PlantRenderer.Kit.cs` **243 LDC**, `WorldView.PlancheKit.cs` 60.

### ⑤ Montage de la plante assemblée (`visuals/PlantRenderer.Assemblee.cs`, appelé par `DrawPalierBas`)
- **Modèle livré** : tiges = tous les segments (épais dessous), ligne ≥ 1 px interne, couleur de
  lignification `WoodRamp` (comme ×4). Touffes du kit (forme `LeafProfiles` de l'espèce) le long de
  chaque segment `IsLeafy`, du bout vers la base, pas = 0,6 × taille, ≤ 8 par segment, gardées si
  hash(71) < `foliage_density` ; 1 sur 3 descend d'un cran (grain). Taille : 3 px ×0,5 · 5 ×1 · 7 ×2,
  +1 cran si emprise ≥ 64 px internes, bornée à 60 % de l'emprise. Tri en profondeur = Y écran de la
  projection au sol (+ hauteur en départage). Sans segment feuillé : semis sur le disque `_rayonReelCm`.
  Teinte inchangée (TeinteSaison → SymptomTint à ×2 → Frosted) ; neige = `DrawSnowCrown` par touffe
  au hash ; fleurons (×2) point/bouton/étoile selon la taille de touffe, hash < 0,6 × floraison.
- **Teinte du kit** : texture « masques » construite UNE fois (atlas des niveaux répété en 6 bandes
  blanches) ; une pièce = 4 `DrawTextureRectRegion` (contour/ombre/base/lumière) modulés par la rampe
  → zéro texture par plante ; `TeindreKit` n'est pas utilisé.
- **Lumière vs rotation D35 (tranchée ici, la conception ne tranchait pas)** : quand le sud projeté
  pointe vers le HAUT (orientations 2-3), on PERMUTE ombre ↔ lumière dans la rampe au lieu de
  retourner la pièce (un retournement ferait pendre les feuilles lancéolées dressées). Capture
  `-r 2` vérifiée [VM, n=1 image]. Effet de bord : la séparation (ombre entre feuilles) devient un
  liseré clair dans ces orientations — point F5.
- **Inchangé** : bois nu (hiver / squelette), tapis D5, `Couronne()` (picking + boîte de cuisson ;
  pas élargie : une touffe déborde d'≤ 4,5 px internes, couvert par `BakePadPx`). `DrawCouronne`,
  `DrawTige`, `DrawTachesFleurs` ne sont plus appelés — **conservés** (règle « ne jamais jeter de code »).
- **Image** : ×4 et ×8 **identiques au pixel** (md5) avant/après [VM, n=4 images, full s44 c=1650,950].
  ×0,5/×1/×2 : plus d'ellipse ; tiges + touffes ; arbre (banc `foret_ports`, pommier, été) = charpente
  + grappes le long des rameaux, lisible comme arbre à ×2 [VM, n=1 planche]. Tomate (full, S
  1075,1875) : tiges feuillées [VM, n=1 planche]. **Ail non vérifié** : aucune espèce lancéolée dans
  le monde `full` s44 ni dans un banc qui pousse (lavandes du banc `courrier` absentes à l'écran).
- **Perf banc E s45** [VM llvmpipe, n=1 chacun, avant → après] : ×2 médiane 75,0 → 72,6 ms,
  > 100 ms 0 → 0, draw calls 73 → 71 ; ×1 médiane 90,1 → 87,8 ms, > 100 ms 11 → 3 [bruit n=1],
  draw calls 68 → 68. Pinceau moyen 0,05 → 0,03 ms/plante [VM, n=2 vidanges de file par zoom] ;
  max 8,5-11,6 ms [VM, n=1 par vidange] = 1ʳᵉ cuisson qui génère l'atlas du kit + les masques (une
  fois) — aucune image > 100 ms. Changement de palier en direct non mesuré (banc à zoom fixe).
- Hors périmètre vu en capture (préexistant, identique avant) : à ×0,5 des plantes de la tuile N
  apparaissent PAR-DESSUS le toit de la maison ; les bancs `foret_ports`/`courrier` sont posés sous
  la maison.
- Build vert, 0 avertissement. Golden `22768f33…` PASS. Taille : `PlantRenderer.Assemblee.cs`
  **146 LDC**, `PlantRenderer.Paliers.cs` 156.

### ⑥ Signes côté Python (`sim/signes_corpus.py` donnée, `sim/signes.py` logique)
- **Corpus** : 11 signes (`vu` calé sur les teintes `PlantRenderer.cs` + marques ×16 `PaliersHauts.cs`,
  concept, carnet D/I, fiche 3 niveaux — niveau 3 = action par le MILIEU) + `FAUNE_VU` pour les 20
  bêtes de `FAUNE_ENCYCLO` (sans les nommer). Concepts tous EXISTANTS : chlorose → `sol` (concept
  des pages), acclimatation → `adaptation` (D43), rongeur_racinaire → `ravageurs`, gel/grêle → `météo`.
- **Observation** : `observer` + champ optionnel `signe` (+ `tile`, `x_cm`/`y_cm` → plot-foyer) →
  entrée ledger `kind="signe"` ; dédup (espèce, signe, saison de 13 sem.) relue DANS le ledger
  (aucun état neuf) ; réponse `signe_note`. Aucune maîtrise créditée (observer un signe ≠ découvrir
  son concept — choix : l'observation d'espèce découvre l'ESPÈCE, rien d'analogue pour un signe).
  Le pont ne vérifie PAS que la plante porte le signe (« la vue n'envoie que ce que le snapshot
  montre ») — à durcir si ⑦ le juge utile.
- **Hors kickoff (ajouté)** : commande pont `legende` (lecture seule, statique) → `vu`+`concept` des
  signes et `vu` des bêtes, pour que ⑦ (C#) n'ait pas à retoucher Python.
- **Carnet** : `CONCEPT_DE`/`GABARIT` alimentés depuis le corpus (boucle de 4 lignes dans `carnet.py`).
- **Appris** : `player.appris = {signes, faune}` au snapshot (sous `player`, pas à la racine),
  lecture pure. Encyclopédie : 8ᵉ type `signe` (hors `encyclopedie_types`, aucun signe n'y collide —
  testé), fiche ouverte quand appris, niveau = `min(palier(concept), 3)`.
- **Écart / trou de conception** : en jeu normal une bête ne dépasse JAMAIS le palier 1 (la détection
  ne crédite pas la faune, `encyclopedie._lire_mono`) → au seuil 3 son nom n'est **jamais** révélé ;
  seuls l'option « interprétatif anticipé » (seuil 1) ou le debug y mènent. Debug `palier3` étendu
  (concepts des signes + faune nommée) pour le F5. **À trancher par Nico** (dette ou voie de crédit).
- Tests : `tests/test_signes_legende.py` **41/41** ; `test_sim_server` **285/285** (3 attentes
  de version 0.5.45 → 0.5.46 mises à jour) ; carnet, encyclopédie, journal, signes, pages, magazine,
  peripherie_voix, maitrise, maitrise_detection, greffe, bouture verts [VM, n=1 chacun].
  Golden `22768f33…` PASS (inchangé). Pas de C#.
- Taille (LDC) : `signes_corpus.py` 170, `signes.py` 35, `carnet.py` 188 → 193, `encyclopedie.py`
  72 → 89, `serialize.py` 366 → 368 (bande vigilance, préexistant), `maitrise_cmds.py` 52.

## §REPRISE
①②③④ commités. ⑤ FAIT (non commité, à commiter par l'orchestrateur) : plante assemblée aux paliers
bas (`PlantRenderer.Assemblee.cs` + appel dans `Paliers.cs`). Points F5 (au ⑦) : « à ×2/×1/×0,5,
est-ce encore horrible ? » ; densité des touffes (sparse en hiver, `foliage_density` faible) ;
liseré clair des orientations 2-3 ; ail (lancéolée) jamais vu à l'écran. Pour ⑦ : faire lancer
Maj+E au PC (priorité moteur Windows + file de cuisson).
⑥ FAIT (non commité). Pour ⑦ : onglet « Signes » à ajouter à `EncyclopediePanel.cs` (type `signe`) ;
info-bulle = `vu` du corpus tant que non appris — commande pont `legende` (statique, une fois) ;
envoyer `observer` avec `signe`/`tile`/`x_cm`/`y_cm` ; lire `player.appris`.
Prochain : ⑦ `07_vue_infobulle_bilan.md`. Chaque tronçon met à jour sa ligne + « Mesures ».
