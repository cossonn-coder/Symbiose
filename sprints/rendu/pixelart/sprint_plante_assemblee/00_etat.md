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
| ④ | `04_kit_elements.md` | atlas du kit (touffes, fleurons) + planche | intact | à faire |
| ⑤ | `05_montage_paliers_bas.md` | plante assemblée à ×0,5/×1/×2 | intact | à faire |
| ⑥ | `06_signes_python.md` | corpus signes + faune, observer étendu, carnet, encyclopédie, `appris` | intact (pont bumpé) | à faire |
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

## §REPRISE
①② commités. ③ FAIT (non commité, à commiter par l'orchestrateur) : Maj+E banc accéléré + postes,
pollen des butineurs sur signal, légende F1 ancrée en bas. Pour ⑦ : faire lancer Maj+E au PC (lire
la ligne « priorité du moteur » sous Windows + la file de cuisson). Prochain : ④ `04_kit_elements.md`. Chaque tronçon met à jour sa ligne + « Mesures ».
