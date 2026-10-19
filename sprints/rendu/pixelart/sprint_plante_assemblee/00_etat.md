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
| ② | `02_plantes_atlas_commun.md` | plantes en pages d'atlas communes (D109 d) + bilan ×4 VM | intact | à faire |
| ③ | `03_accelere_legende_f1.md` | banc accéléré + postes + priorité + ForagerLayer ; bug F1 | intact | à faire |
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

## §REPRISE
① FAIT (non commité, à commiter par l'orchestrateur). Prochain : ② `02_plantes_atlas_commun.md`
(base ×4 = 471 draw calls [VM, n=1], dont Objects ≈ 380 [VM, n=1, relevé d'entrée]). Chaque tronçon met à jour sa ligne + « Mesures ».
