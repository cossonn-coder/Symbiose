# Sprint FLUIDITÉ PC — LEVIERS (2ᵉ `/conception D116`) — carnet de conception

> Phase : **CLOS le 2026-10-26** (①→⑤ faits, golden intact `fecccded…`, pont 0.6.0) — attend le run PC (§F5). Doc : `docs/perf/fluidite/conception_fluidite_pc_leviers.md`.
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
| ① | `01_outil_zoom.md` | journal + rapport copiable des changements de palier, balayage VM, chiffres « avant » | intact | **fait** (07c703b) |
| ② | `02_butineurs_pollen_lot.md` | butineurs + pollen en un lot `LotTriangles` | intact | **fait** (b25718f) |
| ③ | `03_paliers_prets.md` | décor : une maille par palier ; plantes : pas de vectoriel direct au zoom (si mesuré) | intact | **fait** (837b7e0) |
| ④ | `04_pont_delta.md` | pont en delta opt-in (semaine de naissance, segments changés, gènes 1 fois), 0.6.0 | intact | **fait** (efff211) |
| ⑤ | `05_lisiere_devant_bilan.md` | lisière côté caméra devant le jardin + bilan VM + protocole PC + clôture | intact | **fait** (non commité) |

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

## ② Butineurs + pollen en lot — FAIT (2026-10-26)
- `LotTriangles.Grain(c, r, col)` : grain pixel-art (r < 2 → losange 2 triangles ; sinon
  octogone 6 triangles) au lieu d'un `DrawCircle` 64 côtés. `PollenLot` et `ForagerLayer`
  accumulent dans leur lot et envoient UN `DrawMesh` par nœud (ordre corps → pollen porté
  conservé ; nœuds, `ShowBehindParent`, ZIndex, LOD, cadences, culling inchangés). Logique
  de vol/dépôt non touchée. LDC : Forager 271, PollenLot 102, LotTriangles 108.
- Mesure banc 3 phases VM [n=1 run chacun, llvmpipe, `-3 25,25,20 -A 1 -W 90 -S 1521550718`,
  ~270 fleurs pollinisées, 53 butineurs] — phase C (moteur en pause) avant → après :
  draw calls **1 037 → 608**, primitives 146 752 → 120 602, butineurs _Draw **2,16 → 0,32**
  ms/image, moyenne image 197,7 → 187,6 ms [bruit VM ± ~10 ms], rendu CPU 118 → 119 ms
  (inchangé : llvmpipe, dominé ailleurs) ; phase A : draw calls 483 → 314, butineurs _Draw
  1,08 → 0,19. Alloc. nouvelle 172 Ko/s (ToArray du lot), GC sans effet visible.
- Captures `captures_02/` (×4, ×8, image 39, avant/après + loupe ×4) : les butineurs
  bougent en temps réel (`Time.GetTicksMsec`) → captures non comparables au pixel ; à ×4
  les tas de pollen restent des blocs crème pixel-art. ×8 : aucun butineur dans le cadre
  (images identiques) → à juger au F5.
- F5 Nico : butineurs et pollen à ×4 / ×8 « comme avant » ? (losange/octogone vs disque).

## ③ Paliers prêts — FAIT (2026-10-26)
- **Décor** : `visuals/DecorLayer.Mailles.cs` (126 LDC) — une `ArrayMesh` FIGÉE par palier
  (×0,5 ×1 ×2 ×4, `LotTriangles.Figer`). Changer de palier = un `DrawMesh` de la maille
  prête. Palier courant manquant (1er dessin, après `Build`) = construit d'un bloc comme
  avant ; les autres en tâche de fond (`_Process`, 8 tranches = assise/motif par secteur,
  budget 8 ms, le plus proche du palier courant d'abord). Le semis du kit / détails fins /
  calage au pixel lisent `ZoomConstr` (palier construit) au lieu de `CurrentZoom` (sed
  dans Kit/Patchwork/Houppiers/Roche/Eau). Points d'eau du scintillement stockés par
  maille, publiés à la permutation. Invalidation : `Build()` (ceinture changée, rotation,
  F10) jette les 4 mailles. Fil principal seulement (TriangulatePolygon + listes partagées).
  Ancien redessin conservé (`DessinerToutLot`, non appelé).
- **Plantes — mesure d'abord** : nouveau poste `plantes vectoriel` (PerfPostes) = tracé
  direct des plantes sans image. Diagnostic temporaire (retiré) : au cran, les plantes
  sans image sont celles que la file n'a pas encore cuites (VM : file jamais vidée en 4 s
  ≤ ×8) ; « trop grandes » (> 2048 px) seulement à ×16/×32 (≤ 47). Levier : au CHANGEMENT
  DE PALIER (`RedrawAllPlants(changementPalier: true)`, molette + `PoserCamera`, pas la
  capture), une plante sans image qui a déjà un tracé vectoriel le GARDE (mis à l'échelle
  par la caméra, comme une image cuite gardée) jusqu'au Commit de sa cuisson ou au Begin
  raté (trop grande) qui la redessinent (`PlantRenderer.Bake.cs`, `_traceVecteur`).
- **Mesures** [VM llvmpipe, n=1 balayage chacun, `-Z 4 -S 1521550718 -w 90 -c 1650,950`] :
  décor _Draw au cran **27-37 ms → 0,0 ms** (12/12 crans) ; mailles de fond : ×1 39 ms /
  ×2 22 / ×4 21 en 8 tranches, pire image de fond 21 ms [au démarrage, > budget 8 ms : une
  tranche forêt ×1 dépasse] ; `plantes vectoriel` dans la pire image du cran **45-95 ms
  (×2→×32, ×32→×4) → ≤ 5 ms**, sauf ×16→×8 58,6 ms (dézoom : plantes libérées hors champ
  qui rentrent, chemin ReleaseOffscreen non touché). Pire image moyenne des 12 crans
  292 → 279 ms [VM, n=1 : dominée par le rendu llvmpipe ~100-150 ms + cuisson, qui devient
  le poste dominant de la pire image, 15-168 ms]. Banc 3 phases (`-3 25,25,20 -A 1 -W 90`)
  phase C : moy. 197,5 ms (② : 187,6) [bruit VM ±10], draw calls 626 (② 608), plantes
  _Draw 2,44 + vectoriel 1,61 ms/image. Captures `captures_03/` ×2 avant/après :
  **identiques à l'octet** (PNG, Movie Maker).
- Reste visible au cran : la **cuisson (file)** (jusqu'à 80-168 ms dans une image [VM])
  et le rendu ; hors périmètre ③ — à relire sur le run PC.
- F5 Nico : zoomer/dézoomer → l'à-coup a-t-il baissé ? touche Z à coller. Juste après un
  cran, une plante pas encore cuite montre une image au palier précédent agrandie/réduite
  (traits plus fins ou plus épais) jusqu’à sa cuisson [VM : plusieurs s ; PC : non mesuré] : acceptable ?

## ④ Pont en delta — FAIT (2026-10-26)
- **Python** `tools/simserver/pont_delta.py` (76 LDC) : opt-in `"delta": true|"complet"` sur
  `step_week`/`snapshot`/`action` ; sans la clé, snapshot complet inchangé. Plantes du SOL :
  `pid` + `segd` (entier > 0 recopie, < 0 saut, liste de 11 = littéral `[parent, base3, dir3,
  long, ép, apex, semaine de naissance]`), `genes` au 1er envoi, bloc `delta {complet,
  disparues}`. Conteneurs : format complet. Identité d'un segment = l'OBJET `Segment` (vérifié
  au code : croissance en fin de liste, taille/élagage `_rebuild` gardent l'ordre des
  survivants) ; recopie seulement si même objet ET même charge arrondie → exact par
  construction. Semaine de naissance dérivée côté pont (`week − age_weeks`), `sim/` intact.
  `SegmentsVue.entrees` (mêmes arrondis). `cmd_init` oublie l'état. Pont **0.6.0**.
- **Test** `tests/simserver/delta.py` (section 23, 11 checks) : 2 serveurs même graine, client
  miroir ; reconstruction == complet sur 36 réponses (taille au segment, déracinement →
  `disparues`, resynchro). Aussi vérifié monde `full` s92→s99 (8/8 semaines égales).
- **C#** `core/PontDelta.cs` (121 LDC) : cache par `pid`, matérialise DANS le snapshot
  (`segs_lus` PackedFloat32Array 10/segment, âge = semaine − naissance ; `genes` remis) →
  rotation / dossier / étalement relisent sans état caché. Ordre garanti par TICKET pris sous
  `_ioLock` (le parse se fait hors verrou, sur 2 fils). Incohérence / réponse perdue →
  requête suivante en `complet`. `SimBridge.ModeDelta` (défaut vrai ; smoke console faux),
  `Init` → `Oublier`. `PlantStructure.FromSnapshot` / `PlanteLue` lisent `segs_lus` sinon
  `segments`. Temps de reconstitution compté dans `parse`.
- **Mesures** [VM chargée (stockfish, loadavg ~9), n=1 run chacun, banc 3 phases
  `-3 25,25,20 -A 1 -W 90 -S 1521550718`] phase B avant → après : réponse **2 383 → 915 Ko**,
  parse **188 → 118 ms** (reconstitution comprise), lecture plantes **247 → 63 ms**, step vu
  par la vue 1 673 → 1 345 ms, **1,67 → 1,39 s/sem** ; phase A 2,80 → 2,09 s/sem. Python
  in-process [n=8 semaines, s92-99] : `json.dumps` 138 → 52 ms, octets 2,30 → 0,86 Mo ; le
  codage delta coûte ~+20 ms au `_snapshot` [bruit VM].
- F5 Nico : HUD « pont 0.6.0 », aucun changement visuel attendu (plantes, survol des gènes,
  dossier, taille au clic, rotation).

## ⑤ Lisière devant + bilan — FAIT (2026-10-26)
- **Lisière** : `visuals/DecorLayer.Devant.cs` (nouveau) — les pièces HAUTES des 2 bords
  côté caméra (forêt/friche : sous-bois + arbres ; falaise entière hors tapis ; rivière :
  berges à roseaux) vont dans un 2ᵉ lot → `Maille.MeshDevant`, dessiné par un enfant
  `DecorDevant` (Node2D, signal Draw, **z 30 absolu** > plantes 20-24, bâches 12,
  butineurs 11). Assise, tapis, lit d'eau, bords du fond : inchangés (z −5). « Côté
  caméra » = normale sortante du bord qui descend à l'écran (`WorldToScreenOffset`) →
  suit la rotation D35 (Build jette les mailles, déjà le cas). Tranches et tâche de fond
  du ③ inchangées (2 lots par tranche). +1 draw call. Ancien `DessinerToutLot` : tout
  reste dans un lot (`_lotHaut` null).
- **Écart au kickoff** : la boussole N/S/E/O (Labels au sol) disparaissait derrière la
  lisière devant → `l.ZIndex = 31` (`world/WorldView.Monde.cs`). Pas de tri arbre ↔
  plante : les arbres sont au-delà de la frontière (profondeur > AmplitudeCm), donc tout
  point du jardin dans la même colonne d'écran est derrière eux (raisonnement, vérifié en
  capture).
- **Captures** `captures_05/` [VM, full graine 1521550718, warmup 12, ×1, banc décor F10,
  coin bas d'écran de chaque rotation] : `avant_rN`/`apres_rN` (N=0..3) + `avant_pont_r0`/
  `apres_pont_r0` (ceinture du pont, sans F10). Avant : tuiles par-dessus houppiers et
  face de falaise ; après : arbres/falaise devant les tuiles, bords du fond inchangés.
- Effet de bord vu : une forêt côté caméra masque une bande du jardin à ×1 (houppiers
  larges) → dette D112 (n).

## Bilan VM du sprint (avant → après ①→⑤)
[VM llvmpipe, n=1 run par case, graine 1521550718 `full` ; « avant » = mesures « avant »
de chaque tronçon (charges VM différentes : ④ avant à loadavg ~9, après à ~2-4)]

| mesure | avant | après | source avant |
|---|---|---|---|
| banc 3 phases, A : s/sem (1 s demandée) | 2,80 | **2,10** | ④ avant |
| B (rendu suspendu) : s/sem | 1,67 | **1,32** | ④ avant |
| B : réponse / parse / lecture plantes | 2 383 Ko / 188 / 247 ms | **909 Ko / 119 / 61 ms** | ④ avant |
| B : tick moteur moy. | — | 833 ms | — |
| C (moteur en pause) : moy. image | 197,7 ms | 208,5 ms [bruit VM ±10] | ② avant |
| C : draw calls | 1 037 | **648** | ② avant |
| C : butineurs _Draw | 2,16 ms/image | **0,36** | ② avant |
| C : rendu CPU | 118 ms/image | 111 | ② avant |
| balayage zoom (12 crans, `-Z 4 -w 90 -c 1650,950`) : pire image moyenne | 292 ms | **249 ms** | ① |
| décor _Draw au cran ≤ ×4 | 27-37 ms | **0,0** | ① |
| pire image ×8→×4 / ×16→×8 | 271 / 286 ms | 357 / 240 ms | ① |

Lecture : la vue a gagné sur le pont et les draw calls, la cadence VM passe sous 2 s/sem
en A ; mais **toutes les images restent > 100 ms sur VM** (rendu llvmpipe ~100-120 ms +
cuisson au cran 60-85 ms dans la pire image ; file non vidée en 4 s ≤ ×8). Les deux
réponses vraies sont au PC.

## §F5 — protocole PC (UN run) + questions
**Main Run Args** (Godot → Projet → Paramètres → Run → Main Run Args), F5, ne rien
toucher jusqu'à `[banc] FIN` (~2 min), puis copier le rapport (console) :
```
--capture-banc=full --capture-seed=1521550718 --capture-etalonnage=25 --capture-banc-3phases=25,25,20 --capture-banc-cadence=1 --capture-banc-semaine=90
```
Puis (même session, après le banc, ou un 2ᵉ F5 sans arguments) : zoomer/dézoomer en
molette ×0,5 → ×32 → ×0,5 en marquant ~2 s par palier, puis **touche Z** → coller le
rapport des à-coups de zoom.
Questions :
1. (②) butineurs et pollen à ×4 / ×8 « comme avant » ? (grains losange/octogone au lieu
   de disques)
2. (③) l'à-coup au zoom a-t-il baissé ? Juste après un cran, une plante pas encore
   cuite garde son dessin au palier précédent agrandi/réduit (traits plus fins/épais)
   jusqu'à sa cuisson : acceptable ?
3. (④) HUD « pont 0.6.0 » ; rien ne doit changer à l'écran (plantes, survol des gènes,
   dossier, taille au clic, rotation).
4. (⑤) au SE (et après rotation, sur les 2 bords du bas d'écran) les arbres / falaise /
   roseaux de lisière passent-ils DEVANT les tuiles et les plantes ? Les bords du haut
   restent-ils derrière ? La boussole reste-t-elle lisible ? La part de jardin masquée
   par une forêt côté caméra gêne-t-elle (D112 n) ?

## §REPRISE
Sprint **CLOS** (①→⑤ faits ; ⑤ à commiter par l'orchestrateur + journal). Suite : **1 run
PC de Nico** (§F5) → 3ᵉ temps D116 (levier moteur si 2 s/sem non tenu ; cuisson au cran à
relire), puis D112 vue.
