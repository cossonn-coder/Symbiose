# Intégration Godot — avancement archivé : tranches 1 à 3

> Historique détaillé des tranches **closes** 1 (pont), 2 (monde statique),
> 3 (saison animée). Extrait de `00_etat.md` au Sprint refactor global (SS①,
> 2026-06-15) pour alléger l'état partagé. Suite : `_avancement_t4_t6.md`.
> État actif du sprint (tranche 7, reprise) : `00_etat.md`.

## Avancement (tranches 1-3)

### Tranche 1 — pont vivant minimal : ✅ CLOSE (2026-06-10, confirmée dans Godot)
- **Livré** : `data/code/tools/sim_server.py` (serveur stdin/stdout, protocole
  v0 : `init`/`step_week`/`snapshot`/`quit`, survit aux commandes malformées,
  meurt sur EOF) ; `data/code/tests/test_sim_server.py` (**20/20** : forme,
  avancement, robustesse, déterminisme 2 runs byte-identiques, arrêt propre) ;
  `core/SimBridge.cs` (Process + pipes, API synchrone `Init/StepWeek/
  GetSnapshot/Quit` + `SmokeTest()` statique) ; toggle `RunSimBridgeTest` dans
  `world/TileGrid.cs`. **Golden intact** (`16a1b937…`).
- **Décisions prises** :
  - `ENGINE_VERSION = "0.1.0"` **locale à `sim_server.py`** — le sprint save
    global décidera où la centraliser (moteur non touché).
  - Monde du `init` : **réutilise `tests.test_golden.build_world`** (2 tuiles
    terre/argile + maison) — zéro duplication ; `config="smoke"` seul accepté
    en v0, le monde complet vient en tranche 2.
  - `week` du snapshot = **compteur moteur brut** (prochaine semaine à simuler,
    1 = rien simulé) ; `year`/`season` dérivés. Plantes : position **locale
    tuile** (`x_cm`,`y_cm`) + `tile` pour replacer en monde via `origin_*_cm`.
  - Segments via `structure_to_dict()` **bruts** (format Croissance·6, pas de
    2ᵉ format, pas d'arrondi — pas d'optimisation avant mesure).
  - C# : stderr **non redirigé** (tracebacks Python → console Godot) ;
    `Dispose()` kill le process (jamais de Python zombie).
- **Mesure taille snapshot** (2 tuiles, JSON compact) : ~7 Ko sem 5 → ~51 Ko
  an 5 (198 segments, le bois domine ~250 o/segment, borné par `MAX_SEGMENTS`).
  Extrapolé 8 tuiles ≈ 200 Ko/snapshot pour 1 snapshot/60 s réel → **snapshot
  complet VALIDÉ, pas de diffs** (question ouverte tranchée).
- **Confirmé par Nico dans Godot (2026-06-10)** : F5 → console = moteur lancé
  (pid), init 2 tuiles + maison, semaine 5 / printemps, 17 plantes vivantes
  listées (pommier `stade=arbre`, T0 avec attire-auxiliaires vs T1 sans),
  arrêt propre. GTX 950M / Compatibility OpenGL 3.3. NB : le visuel à l'écran
  reste l'ancienne démo (tuiles opaques 96×48 + spécimens `structure.json`) —
  c'est l'objet de la tranche 2.

### Tranche 2 — monde statique rendu : ✅ CLOSE (2026-06-10, confirmée F5)
- **Livré Python** : fabrique du monde extraite de `main.py`
  (`build_world_full()` : 8 tuiles SECTORS plantées + maison ; scénario démo
  passé sous `if __name__ == "__main__"`, sortie vérifiée **byte-identique**) ;
  `sim_server.py` accepte `init(config="full")` (import de la fabrique, zéro
  copie) ; `tests/test_sim_server.py` étendu (**30/30** : 8 tuiles, 3 sols,
  origins distincts, maison [600,600]→[1400,1400], 53 plantes posées, config
  inconnue refusée + le serveur survit). **Golden intact** (`16a1b937…`).
- **Livré C#** : `world/WorldView.cs` + `WorldView.tscn` (**nouvelle scène
  principale**, `run/main_scene` basculé ; `Main.tscn`/`TileGrid.tscn`
  conservés) — au `_Ready` : Start → Init(42,"full") → StepWeek×12 (~1,8 s
  mesuré) → rendu. **Projection UNIQUE** `WorldToScreen` calibrée sur le
  losange réel de `tile_terre.png` (78×39 px pour 50 cm → 0,78/0,39 px/cm,
  `PxPerCmZ`=0,78) — `PlantRenderer.Iso` délègue désormais à cette projection
  (l'ancien couple cos30×0,42 supprimé, **D2 levée**). Sol = couche ZIndex 0,
  maison+plantes = nœud `Objects` **YSortEnabled** (tri de profondeur iso).
  `StructureLoader.FromSnapshot()` (collet = base du segment 0, comme
  `export_structure.py`). Caméra de cadrage zoom 0,5.
- **Décisions prises** :
  - **Placeholders procéduraux** pour tuiles ET maison (décision Nico
    2026-06-10) : les PNG tuiles sont **opaques** (damier de transparence cuit
    en gris, alpha=255 partout — c'était la cause des « tuiles opaques » vues
    en t1) et de **tailles incohérentes** (78×57 vs 32×23) → **D34** ; cahier
    des charges + prompt LLM image : `assets/sprites/tiles/GENERATION_TUILES.md`.
    Couleurs des losanges = teintes dominantes mesurées des PNG (terre #967a64,
    argile #cd7434, sable #f1e9bb), damier ±5 % pour lire la grille, fond
    fenêtre gris pierre = chemins.
  - Échelle plante = **échelle monde** (0,78 px/cm : pommier 350 cm ≈ 273 px) —
    la démo TileGrid affichera ses spécimens plus grands, assumé.
  - `canopy_radius` **pas exposé** dans le snapshot (LOD silhouette inutilisé
    en t2 ; `CanopyRadiusCm=0`) — à exposer en lecture si besoin futur.
  - Plantes du snapshot **sans segments** (germinations non procédurales) :
    pas de nœud créé, comptées en console (« pousses minimales » assumées).
- **Mesures** : snapshot full ~17 Ko sem 2 (54 plantes) → **~83 Ko sem 13**
  (152 plantes, germinations seedbank comprises) — toujours négligeable à
  1 snapshot/60 s. Tick full ≈ 150 ms.
- **Dette** : **D2 ✅, D8 ✅** levées ; **D3** statuée (obsolescence partielle :
  rendu procédural) ; **D4** mitigée (placeholder maison) ; **D34** ouverte
  (ré-export assets tuiles). `DETTE.md` à jour.
- **Confirmé par Nico dans Godot (2026-06-10)** : monde complet affiché —
  1188 plots placeholder, maison [600,600]→[1400,1400] h=600, **152 plantes
  affichées / 0 sans segments**, warmup 12 semaines = **3451 ms** sur son
  poste (vs 1,8 s sur la VM). Plantes « toutes petites » = attendu (échelle
  monde 0,78 px/cm × zoom cadrage 0,5) → résolu par les paliers de zoom.
- **Demande Nico post-F5 → D35** : contrôles caméra (déplacement flèches,
  zoom par paliers ×4-×32, rotation de la vue par quarts de tour gauche/
  droite = re-projection, pas rotation canvas). Pure vue, tranche dédiée
  après t3/t4.

### Tranche 3 — saison animée : ✅ CLOSE (2026-06-10, confirmée F5)
- **Livré** : `world/WorldView.cs` SEUL modifié (zéro Python, protocole v0
  suffisant). Boucle hybride côté vue : machine à états **Planification
  (défaut) ↔ Saison ↔ Pause**, bascule **Espace** (`_UnhandledInput`) ;
  accumulateur temps réel dans `_Process` (`SecondsPerWeek=60`,
  `DebugSecondsPerWeek=3` prioritaire si >0 — à remettre à 0 hors debug) ;
  **step en `Task.Run` pollée** par `IsCompleted` (une seule en vol, échec →
  Planification + erreur) ; `ApplySnapshot` en **diff par clé**
  `tile|species|x|y` (connue → `SetStructure`, nouvelle → fondu in 0,6 s,
  disparue → fondu out 0,9 s + `QueueFree`) ; **fin de saison** = `season` du
  snapshot change → retour auto Planification + hook `OnSeasonEnd()` (TODO
  auto-save, sprint save global) ; **HUD provisoire** `CanvasLayer` + `Label`
  28 px contour noir : « été · an 1 — semaine 5/13 [====------] état »
  (jauge intra-semaine animée, fige en pause).
- **Décisions prises** :
  - Plante persistante = **mise à jour** (`SetStructure` → `QueueRedraw`),
    pas destroy/recreate — le fondu ne marque que naissances/morts.
  - `_ExitTree` **attend la Task en vol** (2 s) avant `quit` — jamais deux
    écritures concurrentes sur le pipe, même à la fermeture.
  - Step **consommé même en pause** (semaine déjà engagée côté moteur).
  - Sémantique horloge assumée : `week` = **prochaine semaine à simuler** →
    la planification s'affiche « semaine 1/13 » de la saison À VENIR (rien
    d'elle n'est simulé) — cohérent boucle hybride (préparer puis vivre).
- **Confirmé par Nico dans Godot (2026-06-10)** : critères tous validés —
  lancement figé en planification ; Espace → semaines défilent, fondus
  visibles (« pixels verts » naissances/morts) ; **pause/reprise OK** ;
  **aucun gel perceptible** aux ticks ; été complet déroulé (13 sem.) +
  retours auto en planification aux passages été→automne. Golden intact
  (`16a1b937…`). Au passage : 1ʳᵉ saison post-warmup = 1 semaine (warmup 12
  sem. → démarrage sem. 13/13 du printemps), assumé kickoff.
