# Sprint Intégration Godot ↔ Python — kickoff & état partagé

> **Kickoff autosuffisant** (démarrage à froid). Ce fichier porte aussi la
> **conception actée** (Option B, validée par Nico le 2026-06-07 : « tes
> recommandations sont bonnes, on suivra ce chemin »). Source de vérité du
> moteur = **Python `data/code/`** ; ce sprint construit la **VUE Godot**, pas un
> second moteur. **GDScript INTERDIT, tout en C#, namespace `Symbiose`.**

## Ce qu'on construit, en une phrase
Faire **jouer/voir** le jardin dans Godot **sans réécrire le moteur** : Python
(moteur, source de vérité) tourne comme **sous-process**, émet l'**état du monde
en JSON**, Godot le **rend** et lui **renvoie les actions joueur**. On généralise
le pont déjà en place (`tools/export_structure.py` → `structure.json` →
`visuals/PlantRenderer.cs`).

## Décision d'architecture ACTÉE — Option B (Python moteur / Godot vue)
**Pourquoi B et pas « porter en C# » (A) :**
- Le moteur est **~7 500 lignes 100 % stdlib** (aucune dépendance tierce —
  vérifié) → se **gèle en un exécutable autonome** (PyInstaller/Nuitka), zéro
  Python à installer chez les joueurs. Le seul reproche fait à B s'effondre.
- **Source de vérité unique** (règle projet : « Godot une vue, aligner vers
  Python »). A dédoublerait le moteur → **divergence permanente** à re-porter à
  chaque évolution Python (7 500 lignes mûres, golden-protégées).
- **Budget temps réel énorme** : 1 semaine = 60 s réel, tick ≈ 177 ms Python
  (×339 de marge) → la sérialisation JSON + IPC est **négligeable**.
- **Déterminisme + debug** : le flux JSON est inspectable (≈ philo du save JSON
  lisible). Même seed → même run ; Godot peut enregistrer/rejouer.
- A ne se justifierait que pour shipper **un seul binaire natif** — le binaire
  gelé règle déjà ça. **Hybride** (porter plus tard un point chaud en C# si la
  perf serre) reste une porte de sortie, pas un prérequis.

## Protocole d'échange (direction actée, détails à figer en tranche 1)
- **Transport** : **sous-process + stdin/stdout, JSON ligne-délimité** (simple,
  debuggable, pas de port à gérer). Godot **pilote la boucle** (envoie des
  commandes, Python répond).
- **Charge utile** : **snapshot complet du monde** au départ (diffs = optimisation
  ultérieure si la taille gêne ; à mesurer). Schéma **versionné** (`engine_version`,
  comme le save). JSON **lisible**.
- **Python possède les RÈGLES** (validité d'une action, coût Vigueur, etc.) ;
  **Godot est « bête »** : il rend et transmet l'intention du joueur.

## Mapping de la boucle hybride (cf. CLAUDE.md « Boucle hybride »)
- **Phase planification (temps figé)** : Python au repos, Godot fait l'UI/
  l'interaction ; les actions « préparation » sont envoyées et validées.
- **Phase saison (15 min réel, 1 sem = 60 s)** : Godot demande « avance d'une
  semaine », Python ticke et renvoie le snapshot ; Godot **anime/interpole** le
  visuel entre deux snapshots hebdomadaires (tweens), la sim reste hebdo.
- **Save** : Python possède le save JSON (au passage de saison) → **converge avec
  le futur « sprint save global »** (naturellement Python). Godot le déclenche.

## Rendu — ce que Godot dessine du snapshot
Tuiles iso (monde) · plantes **procédurales** (porter `_iso` + structure ; les
**organes** `_draw_organs` du prototype Python SVG → C#) · **ombre de la maison**
· overlays de champs en **mode debug** (heatmaps) · **vie macro** (sprites
échantillonnés) · HUD/**notifications hiérarchisées** · plus tard encyclopédie/
carnet. Indices **visuels** d'abord (philo #5 : pas de chiffres en HUD primaire).

## État de départ Godot (ce qui existe déjà)
- **Fonctionnel** : `core/PlantData.cs`, `TileData.cs`, `GridField.cs`,
  `PlantCatalogue.cs` (14 esp.), `SpriteLoader.cs` ; `core/PlantStructure.cs` +
  `visuals/PlantRenderer.cs` (lisent `structure.json`, projection `Iso()` = portage
  de `_iso`) ; `world/TileGrid.cs` (affiche **1** tuile iso 6×8 + 4 plantes démo).
- **Stubs vides (15 lignes)** : `Main.cs` (classe `Node2d`, hors namespace !),
  `GameManager`, `TurnSystem`, `EcologySystem`, `SeedBankSystem`, `SoilField`,
  tout `plants/*`, `ui/*`, `LightOverlay`/`PlantAnimator`/`WindAnimator`.

## Découpage proposé en sous-sprints (vertical slices — révisable)
1. **Pont vivant minimal** : `tools/sim_server.py` (boucle stdin/stdout JSON :
   commandes `init(seed,config)` / `step_week` / `snapshot`) côté Python ; côté C#
   un `core/SimBridge.cs` qui lance le sous-process, parse le snapshot. **But :
   prouver le tube** (un snapshot s'affiche, une semaine avance). Réutilise le
   schéma `structure.json`. Golden Python **intact** (on lit le moteur, on n'y
   touche pas). → **✅ FAIT côté Python + C# écrit (2026-06-10), voir
   « Avancement » ci-dessous. Compilation Godot à confirmer par Nico.**
2. **Monde statique rendu** : Godot dessine le **monde complet** du snapshot
   (tuiles hétérogènes + maison + plantes procédurales + ombre) — **corrige
   D2/D3/D8** au passage (tuiles **78×57**, noms de sprites, scène principale
   propre). Reprend `TileGrid`/`PlantRenderer`.
   → **✅ CLOSE (2026-06-10, confirmée F5 par Nico) — voir « Avancement »
   ci-dessous.**
3. **Saison animée** : bouton « avancer », `step_week` ×N, **interpolation**
   visuelle entre snapshots ; cycle de saison + auto-save déclenché.
   → **✅ CLOSE (2026-06-10, confirmée F5 par Nico) — voir « Avancement »
   ci-dessous.**
4. **Actions joueur** : clic → commande Python (planter, arroser, tailler,
   manger…) ; Python valide + applique (coût Vigueur), renvoie le snapshot.
5. **Organes + overlays + vie macro** : porter `_draw_organs` en C#, heatmaps
   debug, sprites auxiliaires/nuisibles échantillonnés.
6. **Packaging** : gel PyInstaller du moteur en binaire, Godot le spawne ;
   build exportable pour amis/famille.
*(HUD riche, encyclopédie, carnet, pages secrètes = au-delà, sprints dédiés.)*

## Contraintes & pièges
- **Pas de `dotnet` CLI ici** → **Nico build/lance dans Godot sur son poste**,
  Claude code et Nico fait les retours (boucle plus lente, prévoir des tranches
  vérifiables).
- **GDScript interdit, namespace `Symbiose`, déterminisme** (seed global).
- `Main.cs` = `Node2d` hors namespace (D8) ; tuiles **78×57** ≠ 96×48 codé dans
  `TileGrid.cs` (D2) ; noms sprites attendus ≠ disque (D3) ; `Main.tscn` obsolète.
- Le moteur Python **ne doit pas être modifié pour Godot** : si Godot a besoin
  d'une donnée, on l'**expose en lecture** (nouveau champ du snapshot), on ne
  change pas la logique → golden intact.

## Questions ouvertes (à trancher au fil, défaut sobre + signaler)
- **Granularité du snapshot** : complet vs diffs (mesurer la taille/latence à la
  tranche 1 avant d'optimiser).
- **Format des commandes joueur** (verbe + cible + params) : à figer en tranche 4.
- **Cycle de vie du sous-process** : un process persistant (état en mémoire) vs
  relancé (rejoue depuis le save) — défaut **persistant**, à confirmer.
- **Où vit le save** : ici (Python) ou attendre le « sprint save global » — défaut
  **Python ici**, convergent.

## Avancement

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
### Tranche 4 — volet A (caméra D35) : ✅ CLOS (2026-06-11, confirmé F5)
- **Livré** : `world/WorldView.cs` + `visuals/PlantRenderer.cs`. Caméra
  jouable : **pan flèches** (vitesse px écran, bornée monde + marge 10 %),
  **zoom molette** par paliers {0.5, 1, 2, 4, 8, 16, 32} centré souris
  (paliers < 4 provisoires, cf. kickoff), **rotation PageUp/PageDown** par
  quarts de tour (`_orientation` dans `WorldToScreen` + `RebuildWorld()` ;
  variante **`WorldToScreenOffset`** point/vecteur pour les offsets plante —
  le phototropisme penche vers le même point monde à toute orientation).
  **Légende des commandes** au HUD (bas-gauche). **D35 levée.**
- **Retours Nico (1er F5 t4) intégrés** : toit **pyramidal** 4 pans + façades
  teintées côté MONDE (soleil au sud — la maison tourne visiblement) ;
  **boussole** N/S/E/O au sol ; **étiquettes** espèce·stade sous chaque
  plante (toggle **F3**) ; **maison transparente** (toggle **H**) ; **modes
  simu** (touche **M**) : Saison / Continu / Turbo ; **ombres placeholder**
  (maison vers le nord, disque au pied des plantes) ; sens de rotation =
  caméra orbite à droite sur PageUp.
- **Retour Nico (2e F5, 2026-06-11) — triage** :
  - **Ombre solaire animée** (direction/longueur selon heure du jour et
    saison, au lieu du nord fixe) : le modèle existe déjà côté moteur
    (`fields/light.py:solar_slice`, azimut+élévation astronomiques). Décision
    Nico : **après le volet B** (volet C de cette tranche ou t5) — portage
    de la formule côté vue, balayage de l'arc solaire pendant la semaine
    vécue (le moteur n'a pas de notion de jour : 1 semaine vécue ≈ 1 journée
    visuelle, fidèle au modèle, zéro Python touché).
  - **Étiquette au survol uniquement** (pas toutes à la fois) : intégrée au
    **volet B** — premier consommateur du picking `ScreenToWorld`.
  - **Plusieurs plantes par plot** : limite réelle du MOTEUR
    (`sim/succession.py` : « Plot déjà occupé → pas de germination ») →
    **sprint Python dédié** gravé au backlog (compétition intra-plot).
  - **Plantes mortes visibles + décomposition** : moteur aussi → **sprint
    « décomposition & compost »** gravé au backlog.
- **Prochaine étape : volet B — actions joueur** (kickoff
  `04_camera_actions.md` §B) : Vigueur branchée dans `sim_server.py` via
  façades existantes, commande `action` verbe+cible+params, plante désignée
  PAR POSITION, `urgence` = phase Saison, 8 gestes existants —
  `planter`/`arroser` EXCLUS : pas d'équivalent moteur, backlog. S'y ajoute
  l'étiquette au survol (picking partagé clic/survol).

## Lien dette
Lève progressivement **D24** (le « portage C# » devient « pont », plus un portage
intégral) + **D2/D3/D4/D8** (rendu/scène). À refléter dans `DETTE.md`/`BACKLOG.md`
quand le sprint démarre.
