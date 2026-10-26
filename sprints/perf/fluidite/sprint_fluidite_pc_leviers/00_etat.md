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
| ① | `01_outil_zoom.md` | journal + rapport copiable des changements de palier, balayage VM, chiffres « avant » | intact | à faire |
| ② | `02_butineurs_pollen_lot.md` | butineurs + pollen en un lot `LotTriangles` | intact | à faire |
| ③ | `03_paliers_prets.md` | décor : une maille par palier ; plantes : pas de vectoriel direct au zoom (si mesuré) | intact | à faire |
| ④ | `04_pont_delta.md` | pont en delta opt-in (semaine de naissance, segments changés, gènes 1 fois), 0.6.0 | intact | à faire |
| ⑤ | `05_lisiere_devant_bilan.md` | lisière côté caméra devant le jardin + bilan VM + protocole PC + clôture | intact | à faire |

Dette déjà inscrite à la conception : D112 (k) décor animé, (l) soleil sur les plantes,
(m) cohérence DA inter-paliers ; D116 mise à jour (run PC + conception).

## §REPRISE
Exécution : `/sprint-auto sprint_fluidite_pc_leviers` (tronçon suivant = le premier « à
faire »). Après : 1 run PC de Nico → 3ᵉ temps D116 (levier moteur si 2 s/sem non tenu).
