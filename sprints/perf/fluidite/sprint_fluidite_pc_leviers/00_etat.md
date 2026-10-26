# Sprint FLUIDITÉ PC — LEVIERS (2ᵉ `/conception D116`) — carnet de conception

> Phase : **FIGÉE le 2026-10-26** (GO Nico). Doc : `docs/perf/fluidite/conception_fluidite_pc_leviers.md`.
> Sprint précédent (diagnostic) : `sprints/perf/fluidite/sprint_fluidite_pc/00_etat.md`
> (golden `fecccded…`, pont 0.5.58). Cible inchangée : PC, 1 s/sem demandée → ≤ 2 s/sem
> effectives, aucune image > 100 ms.

## Lecture du run PC 3 phases (2026-10-26, s90 an 2, ×4, graine 1521550718) [n=1 run, PC]
- **B (rendu suspendu)** : 2,27 s/sem · tick 1 572 ms · step vu 2 454 ms → surcoût pont
  ≈ 880 ms/step (sérialisation 2,2 Mo + parse 192 + lecture plantes 173 ms). Même sans
  rendu, la cible 2 s est manquée.
- **A (normal)** : 6,26 s/sem · tick 3 179 ms → **le rendu double le tick** (contention
  CPU confirmée côté moteur, malgré BelowNormal). Images 108 ms moy., 63 > 100 ms.
- **C (moteur en pause)** : images **pires** (245 ms moy., 4,1 FPS, inexpliqué 69 ms) →
  la contention n'explique PAS les images lentes : le rendu seul est trop lourd au PC.
  Biais : C passe en premier (285 fleurs pollinisées, 53 butineurs ; en A 285→116).
  Rendu CPU 117 (C) / 44 (A) ms, draw calls 861 / 449.
- **Butineurs _Draw** 29 ms/image (pics 108 ms) en C. Vérifié au code : le pollen est
  dessiné en **1 `DrawCircle` par grain** (`visuals/PollenLot.cs:131-138`, ≤ 8/fleur), les
  butineurs aussi (`ForagerLayer.cs` ~l.362) → ~2 300 cercles [estimation code, non mesuré].
- GPU non mesuré (ANGLE D3D11 → 0).

## Retours F5 Nico (2026-10-26)
pont 0.5.58 OK · décor juste sans F10 (D112 c confirmé fermé) · lisière « mieux ».
Nouveaux : décor absent > ×4 (= LOD `DecorLayer.MaxZoom = 4`, voulu) ; décor immobile au
vent ; SE : tuiles du jardin AU-DESSUS des arbres de lisière (décor en ZIndex −5,
`WorldView.cs:311`) ; maison en verre (= D112 b) ; contours noirs des plantes disparus
(regrettés, beau à ×1 — origine à établir) ; lisière à animer (vent + lumière) ; le soleil
ne s'éclaire sur aucune plante ; à-coup au changement de zoom + **outil demandé** pour
l'extraire en zoomant/dézoomant.

## Décisions arrêtées (Nico, 2026-10-26)
- **Ordre : vue d'abord, re-mesure PC, puis le reste.** Le moteur Python (tick) n'est PAS
  dans ce sprint : il se décide sur le run PC d'après.
- **Périmètre** : perf vue + outil à-coup de zoom + ordre de la lisière côté caméra (SE).
  Tout le reste → **inscrit en dette** (exigence Nico) : décor au vent/lumière, soleil
  visible sur les plantes, cohérence DA inter-paliers, maison en verre (D112 b).
- **Contours noirs** : existent au palier bas ×1 (kit, `PlantRenderer.Kit.cs:37-38`,
  contour 1 px si touffe ≥ 7 px) et pas aux paliers hauts (×4+, segments). Nico veut le
  style ×1 comme MODÈLE et chaque palier plus fin = la même idée + plus de détails
  (assets prêts par palier ; 2 méthodes : agrandir ×0,5 et ajouter, ou partir de ×32 et
  retirer) → **dette** (D112 i étendue), pas ce sprint.

## Carte des tronçons (FIGÉE 2026-10-26)
| # | Kickoff | Contenu | Golden | État |
|---|---|---|---|---|
| ① | `01_outil_zoom.md` | journal + rapport copiable des changements de palier, balayage VM, chiffres « avant » | intact | **fait** (non commité) |
| ② | `02_butineurs_pollen_lot.md` | butineurs + pollen en un lot `LotTriangles` | intact | à faire |
| ③ | `03_paliers_prets.md` | décor : une maille par palier ; plantes : pas de vectoriel direct au zoom (si mesuré) | intact | à faire |
| ④ | `04_pont_delta.md` | pont en delta opt-in (semaine de naissance, segments changés, gènes 1 fois), 0.6.0 | intact | à faire |
| ⑤ | `05_lisiere_devant_bilan.md` | lisière côté caméra devant le jardin + bilan VM + protocole PC + clôture | intact | à faire |

Dette déjà inscrite à la conception : D112 (k) décor animé, (l) soleil sur les plantes,
(m) cohérence DA inter-paliers ; D116 mise à jour (run PC + conception).

## ① Outil à-coup de zoom — FAIT (2026-10-26)
- `world/WorldView.ZoomJournal.cs` (147 LDC) : fenêtre ~1 s (≥ 3 images) après chaque
  palier changé (molette `StepZoom`, planche L et balayage via `PoserCamera`), 40 derniers
  gardés. **Touche Z** (F8 réservé par l'éditeur Godot = Stop → écarté) = rapport copié
  (ligne par changement + synthèse par paire). Décor capté via `DecorLayer.Dessins/
  DernierDessinMs` (posés dans `TracerDessin`), file via `BakeQueue.FileEligibles`.
- Balayage : `tools/perf_vm.sh -Z SEC` (→ `--capture-zoom-balayage`), temps réel (pas le
  Movie Maker, qui fausse les temps d'image). Limite : le rendu CPU de la pire image n'est
  pas relevé (mesure Godot inactive hors banc E) → pire − postes = rendu + hors postes.
- **Tableau « avant » (référence ② ③)** [VM llvmpipe, n=1 balayage, 4 s/palier, graine
  1521550718 `full`, warmup 90 → semaine moteur 91 = automne an 2 s13 (pas été), centre
  1650,950, 590 plantes, régime VM hors cran 100-210 ms/image] :

| cran | pire (ms) | images >100 / fenêtre | décor _Draw (ms) | file départ | poste dominant pire image |
|---|---|---|---|---|---|
| ×0,5→×1 | 442 | 4/4 | 37,3 | 580 | cuisson 77 |
| ×1→×2 | 316 | 6/6 | 34,0 | 311 | cuisson 55 |
| ×2→×4 | 330 | 5/5 | 29,9 | 220 | cuisson 72 |
| ×4→×8 | 338 | 5/5 | — | 164 | plantes _Draw 73 |
| ×8→×16 | 252 | 6/6 | — | 80 | cuisson 98 |
| ×16→×32 | 274 | 5/9 | — | 38 (vidée 1,2 s) | plantes _Draw 65 |
| ×32→×16 | 238 | 7/7 | — | 56 (vidée 4,1 s) | plantes _Draw 80 |
| ×16→×8 | 286 | 5/5 | — | 126 | plantes _Draw 87 |
| ×8→×4 | 271 | 5/5 | 31,4 | 200 | cuisson 16 |
| ×4→×2 | 233 | 6/6 | 29,2 | 271 | cuisson 15 |
| ×2→×1 | 258 | 6/6 | 27,2 | 483 | cuisson 15 |
| ×1→×0,5 | 271 | 6/6 | 10,3 | 574 | plantes _Draw 28 |

  Lecture : chaque cran invalide les 590 plantes ; la file de cuisson ne se vide pas en
  4 s aux paliers ≤ ×8 [VM] ; le décor recoud ~30 ms à chaque cran ≤ ×4 (cible ③) ; au
  zoom avant ×4→×32 le dessin direct des plantes (pas encore cuites) domine (cible ③).

## §REPRISE
Exécution : `/sprint-auto sprint_fluidite_pc_leviers` (tronçon suivant = ② ; ① fait, à commiter par l'orchestrateur). Après : 1 run PC de Nico → 3ᵉ temps D116 (levier moteur si 2 s/sem non tenu).
