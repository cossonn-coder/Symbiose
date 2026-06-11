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
### Tranche 4 — volet B (actions joueur) : CODÉ (2026-06-11), en attente F5
- **Livré Python** : `sim_server.py` protocole **v1** (`ENGINE_VERSION
  0.2.0`) — `ensure_player` à l'init (le tick moteur fait seul régen+refill,
  hook existant `engine.py:774` gardé par `"vigueur" in game_state`) ; bloc
  `player {vigueur, vigueur_max}` au snapshot ; commande **`action`**
  (verbe+target+params → `result` ACK/NAK + **snapshot frais joint**).
  Désignations : plante PAR POSITION (±0,1 cm, `PLANT_EPSILON_CM`), plot
  `(tile,r,c)` borné, tuile, rien. Refus métier = `ok:true` +
  `applied:false` + message (le `ok:false` reste aux commandes malformées).
  Le serveur appelle les façades `sim/actions.py` SANS réimplémenter de
  règle (coût×maîtrise×urgence, effets — tout côté moteur).
- **Tests** : `test_sim_server.py` **47/47** (bloc player, régen +10/sem via
  tick, refill plein à la semaine 14, manger/deraciner par position +
  disparition dans le snapshot JOINT, URGENCE_MULT 15→22,5 visible, refus
  verbe inconnu/cible introuvable/plot hors tuile/Vigueur insuffisante avec
  serveur survivant, déterminisme 2 runs MÊMES actions byte-identiques).
  **Golden écolo intact** (`16a1b937…`, vérifié).
- **Livré C#** : `SimBridge.Action(verb, target, params)` (réponse complète
  result+snapshot) ; `WorldView.cs` — **`ScreenToWorld`** (inverse analytique
  + orientation défaite dans l'ordre inverse, à côté de l'aller, leçon D2) ;
  touches **1..8 en `PhysicalKeycode`** (AZERTY : la rangée chiffres émet
  `&é"'(…` en Keycode) dans l'ordre de la table `COUTS` ; clic gauche →
  désignation par famille de cible (plante ≤ 30 cm monde, plot/tuile par
  containment, grelinette sans cible) → action en **Task** (pipe
  maître/esclave : UNE requête en vol, step OU action ; clic ignoré sinon ;
  `_ExitTree` attend les deux) ; `tailler` Maj+clic = branche ; `ecraser`
  `urgence` = phase Saison (Pause = tarif planification, temps figé) ; HUD
  2ᵉ ligne « Vigueur x/y — geste : … » + dernier message, flash rouge sur
  refus ; **étiquette AU SURVOL** (F3 cycle survol/toutes/aucune, défaut
  survol — demande Nico 2e F5) via le même `FindPlant` que le clic ; légende
  enrichie gestes 1..8.
- **1er F5 Nico (2026-06-11)** : actions ✓, refus/flash ✓, survol ✓. Retour
  triagé + correctifs :
  - **Turbo affamait les clics** (pipe jamais libre) → **file d'UNE
    intention** : clic mémorisé (le dernier gagne), part en priorité dès que
    le pipe se libère, avant la semaine suivante.
  - **« tailler ne montre rien »** : la coupe est réelle et immédiate
    (prouvé : 6→5 segments dans le snapshot joint) mais invisible sur de
    jeunes sujets → **flash jaune de la plante ciblée** à chaque geste
    réussi (après ApplySnapshot — pas de conflit avec le fondu de mort).
  - **Messages instructifs serveur** : `manger` affiche le gain
    (« +4.1 Vigueur — gain ∝ maturité ») ; `ecraser` affiche
    « ravageurs 0.80 → 0.60 » (lecture pure du champ — les sprites = t5).
  - **Pas des bugs (design expliqué)** : régen = +10/semaine SIMULÉE (rien
    en Planification, temps figé — la « méditation au foyer » comblera) ;
    manger à 0 Vigueur fonctionne (coût nul, gain ∝ maturité — un semis ne
    nourrit pas) ; spam manger = D19 (déplétion d'organe, déjà gravé) ;
    ombre disque uniforme = placeholder → volet C.
- **Décisions Nico (2026-06-11)** : ordre de fin de tranche = **volet C
  (ombre solaire animée) PUIS volet D (taille au segment près à la souris)**.
  Volet D pré-étudié : moteur prêt (`atteindre_segment(seg_id)`), il faudra
  étendre la façade `tailler` de `sim/actions.py` (couche joueur, golden
  écolo intact), le protocole (`target.segment`), et le hit-test/surbrillance
  des segments côté vue.
- **2e F5 Nico (2026-06-11) : correctifs volet B VALIDÉS** (« ok c'est
  bon ») → **volet B CLOS, commit 48f1bdd**.

### Tranche 4 — volet C (ombre solaire animée) : CODÉ (2026-06-11), en attente F5
- **Livré (C# seul, zéro Python)** : `WorldView.cs` — portage de
  `fields/light.py:solar_slice` (latitude 49°N, déclinaison saisonnière
  ±23,4°, lever/coucher astronomiques `cos H = −tan φ·tan δ`) ; la **jauge
  intra-semaine devient l'heure du jour** (1 semaine vécue ≈ 1 journée
  visuelle, du lever au coucher) ; statiques partagées `SunShadowDir` /
  `SunInvTan` (borné 3,5× la hauteur) / `SunStrength` ; Planification/
  Turbo → midi figé, Pause → ombre figée (accumulateur gelé) ; **early-out
  < 2°** (≈ 1 redraw/s à 60 s/sem, ~15/s en debug 3 s). Ombre MAISON =
  enveloppe convexe monde (empreinte + coins déplacés + faîte,
  `Geometry2D.ConvexHull`) re-projetée — survit à la rotation D35. Alpha ∝
  force solaire (soleil bas = ombre pâle et longue). `PlantRenderer.cs` —
  le disque devient une **ombre-capsule** (disque glissé le long de la
  direction sur hauteur × 1/tan(élévation)) = le modèle EXACT des
  ombres-capsules du moteur ; `_heightCm` calculé au `SetStructure`.
- **Valeurs attendues** (vérifiées sur le `solar_slice` Python) : hiver
  jour court ±60°, ombre midi 3,15×h ; été ±120°, midi 0,48×h, ombres du
  soir pointant légèrement SUD (soleil levé au nord-est — réalisme
  gratuit). Les saisons se lisent à l'œil.
- **F5 Nico (2026-06-11) : volet C VALIDÉ, 5/5 critères** (balayage,
  saisons contrastées, pause/planification, rotation, maison transparente
  qui ombre toujours). Témoin de build vu et adopté. Au passage Nico a
  observé les ombres SUD des matins/soirs d'été — réel (azimut du lever
  `cos A = sin δ/cos φ` → lever au NE à δ=+23,4°), pédagogie donnée.
- **Idée design Nico consignée (2026-06-11)** : un événement météo se
  représentera comme l'ombre — déroulé sur la SEMAINE vécue (pluie, vent,
  gel), même granularité hebdo que le moteur, et son impact (humidité,
  température, ombrage, vent) suivra le même patron visuel. À reprendre au
  sprint rendu météo (cf. `CONCEPTION_METEO.md`).

### Tranche 4 — volet C2 (perf ombres + mesures) : CODÉ (2026-06-11), F5 rapide à faire
- **Retour perf Nico** : « plus la simulation avance plus l'ombre ralentit
  le jeu ». Cause racine : le balayage solaire faisait `QueueRedraw` sur la
  PLANTE entière (tous segments, ~15×/s en debug). Livré :
  - **Ombre = nœud enfant `PlantShadow`** (`ShowBehindParent`) : le soleil
    ne redessine QUE les ombres (1 petit polygone chacune), plus jamais les
    segments — le coût ne grandit plus avec l'âge des plantes.
  - **Touche O** : coupe toutes les ombres (`WorldView.ShadowsOn`,
    `_Draw` no-op + `UpdateSun` endormi = coût strictement nul).
  - **Touche F4 — overlay de perfs** (demande Nico) : FPS, durée du dernier
    tick complet (pipe+sim+parse), cadence réelle s/semaine (+ jours
    simulés/s), plantes (+pousses), segments, état ombres, zoom. Mesuré
    côté vue, moteur non instrumenté.
  - Témoin de build → **« t4·C2 ombres O + perfs F4 — 2026-06-11 »**.
- **TRANCHE 4 CLOSE après ce F5** (volets A, B, C, C2). La taille au
  segment près (ex-volet D) devient la **tranche 5 — kickoff PRÊT :
  `05_taille_segment.md`** (façade `tailler(segment_id)` + protocole
  `target.segment` + hit-test/surbrillance). Après t5 : t6 = organes +
  overlays + vie macro (kickoff `06_*.md` à écrire).
- **Workflow acté (2026-06-11, cf. mémoire feedback-format)** : un retour
  Nico sur livrable → tri en sprint indépendant ou dette + clôture
  facilitée du sprint en cours (pas de dev immédiat) — appliqué ici même.

### Tranche 5 — taille au segment près (souris) : CODÉE (2026-06-11), en attente F5
- **Livré Python (commit 5b8d793)** : `sim/actions.py:tailler` accepte
  `segment_id` keyword — valide (existe, pas le collet) → REMPLACE le
  sélecteur `_segment_cible`, sinon comportement t4 inchangé (compat prouvée :
  `test_vigueur` 110/110 et `test_croissance` 67/67 SANS modification) ; coût/
  gain identiques (on ne tarife pas la précision). `sim_server.py` protocole
  **0.2.1** : `target.segment` optionnel sur `tailler` (= index dans
  `segments` du snapshot, ordre `structure_to_dict()` stable), validé AVANT
  la façade — hors bornes / collet / non entier = refus métier à **coût
  NUL** ; message « taillé (segment i) ». `test_sim_server.py` **58/58**
  (le snapshot joint perd EXACTEMENT le sous-arbre ciblé — vérifié via les
  champs `parent`, repli `params.cible` intact, serveur survivant).
  **Golden écolo intact** (`16a1b937…`).
- **Livré C#** : `PlantRenderer.cs` — propriété `HighlightSegment` (setter
  early-out : écrite chaque frame, redraw seulement au CHANGEMENT ; remise à
  −1 à chaque `SetStructure`, les index changent à chaque snapshot) ;
  `FindSegmentNear(canvasPos, maxPx)` = distance point-segment via la MÊME
  géométrie que le dessin (Iso, leçon D2) — **segment 0 (collet) exclu** :
  clic au pied → repli t4, jamais un refus surprise ; surbrillance jaune
  clair (la couleur du flash de geste réussi — un seul langage visuel)
  dessinée par-dessus le bois. `WorldView.cs` — `UpdateTailleHighlight()`
  chaque frame en mode tailler (même résolution que le clic : ce qui est
  surligné = ce qui part) ; tolérance **8 px ÉCRAN** à tout zoom
  (divisée par le palier) ; clic → `target.segment` si une branche est
  trouvée, `params.cible` toujours joint en repli ; légende mise à jour.
  Témoin de build → **« t5 taille au segment — 2026-06-11 »**.
- **Critères F5** (kickoff `05_taille_segment.md`) : surbrillance suit la
  souris en mode 7 ; clic → CETTE branche + sous-arbre disparaissent, flash
  jaune ; clic au pied = comportement t4 ; segment disparu entre temps →
  refus propre.
- **1er F5 Nico (2026-06-11) : 3/3 critères validés.** Retours triagés :
  - **« Les segments qui dépassent le carré de départ ne peuvent pas être
    taillés »** → défaut du livrable (le filtre par collet à 30 cm excluait
    la couronne débordante d'un arbre) → **correctif t5·B (C# seul)** :
    `FindSegmentGlobal` cherche LA branche sous la souris chez TOUTES les
    plantes (préfiltre `PickExtentCm` = 1,5×(étalement+hauteur) — la hauteur
    compte car la souris est re-projetée au sol z=0), survol ET clic ; sans
    branche sous le curseur, repli collet 30 cm = t4. `FindSegmentNear`
    renvoie aussi la distance (comparaison entre plantes). Build témoin →
    **« t5·B portée de taille — 2026-06-11 »**. En attente F5.
  - **« Taillée, la plante devrait repousser à deux têtes (hors
    monocotylédones) »** → **le moteur le fait DÉJÀ** (vérifié par
    expérience, 2026-06-11) : tomate écimée semaine 9 → **2 apex** dès le
    tick suivant (témoin : 1 apex), émergent du débourrement §D.3 (bourgeons
    sous le seuil d'auxine une fois l'apex dominant coupé — rien de codé en
    dur, philo #2). Les monocotylédones (graminées) sont insensibles par
    construction (profil d'espèce, CONCEPTION_CROISSANCE). Les nouvelles
    têtes font quelques cm la 1ʳᵉ semaine — probablement invisibles au
    moment du F5 ; à ré-observer sur 2-3 semaines simulées. Si le port
    « touffu » reste jugé trop timide à l'usage → sprint CALIBRAGE moteur
    (AUXIN_INHIB_THRESHOLD / dominance), pas de mécanique manquante.
- **CLAUDE.md rafraîchi** (demande Nico, même date) : tranches 1-5 closes,
  prochaine = t6, D1–D35, rappel DebugSecondsPerWeek.
- **2e F5 Nico (2026-06-11) : correctif t5·B validé (« ok c'est bon ») →
  TRANCHE 5 CLOSE.** Prochaine : **tranche 6 (organes + vie macro + overlays
  debug), kickoff PRÊT `06_organes_overlays_viemacro.md`** — dernière tranche
  de contenu avant t7 = packaging.

### Tranche 6 — volet A (organes procéduraux) : CODÉ (2026-06-11), en attente F5
- **Livré Python** : `sim_server.py` protocole **0.2.2** — 3 hints par plante
  au snapshot (lecture seule, kickoff §1) : `foliage_density`
  (`foliage_density_at(plant, saison)`, déjà saisonnier — caduc hiver = 0),
  `organ` (proxy saisonnier `REPRO_BY_SEASON` **importée de
  `tools.render_structure`** — outil→outil, zéro duplication ; espèce absente
  → repli `DEFAULT_REPRO` : fleur printemps, fruit mûr été/automne, rien
  l'hiver), `organ_site` (profil d'espèce). Moteur JAMAIS touché.
  `test_sim_server.py` **68/68** (section 9 : hints présents/bornés, printemps
  = flower partout, été = pommier `fruit_unripe` ≠ tomate `fruit_ripe`
  (cycles distincts, critère F5), hiver = organ null partout + pommier caduc
  densité 0). **Golden écolo intact** (`16a1b937…`). Mesure : hints ≈ +60
  o/plante comme prévu (snapshot smoke sem 40 : ~39 Ko / 23 plantes).
- **Livré C#** : `PlantStructure.cs` — 3 champs DTO (lecture TOLÉRANTE,
  défauts si snapshot pré-0.2.2 ; `organ` null JSON → "" = rien) ;
  `PlantRenderer.cs` — portage de `_draw_organs` : feuilles (segments apex ou
  ≤ 1,6 cm, 1/11 cm, déport 7 cm au hash, ellipse-polygone 10 pts, opacité
  0,92, **sous-échantillonnage au hash si densité < 1** — ajout kickoff vs
  prototype), couleur palette espèce × saison (printemps ×1,25, automne
  AUTUMN_LEAVES au hash, hiver ×0,7 persistants), fleurs 5 pétales + cœur /
  fruits disque + reflet aux bouts d'apex (`terminal`) ou latéraux hors
  meneur (`lateral`), plafond 10 ; **hash C# local** (mix entier xorshift,
  stable inter-frames/sessions, zéro Random — pas de parité bit-à-bit avec le
  SVG, assumé kickoff). Dessin dans `DrawSegments` APRÈS le bois, AVANT la
  surbrillance t5 ; redraw **uniquement au SetStructure** (leçon perf C2).
  `WorldView.cs` — statique `CurrentSeason` (assigné dans ApplySnapshot AVANT
  les SetStructure), témoin de build → **« t6·A organes procéduraux —
  2026-06-11 »**.
- **Signalé (design, pas bug)** : le proxy saisonnier fleurit TOUTE plante à
  apex, même une pousse d'une semaine (fidèle au prototype SVG — le vrai état
  reproducteur = D19/D33). Si le F5 juge ça gênant : filtre par stade = 1
  ligne côté serveur, à trancher.

### REPRISE (session suivante, démarrage à froid)
1. **F5 Nico du volet A** d'abord (critères : pommier fleurs printemps →
   fruits verts été → fruits rouges + feuillage automnal → nu l'hiver ;
   tomate cycle propre ; FPS stable au F4). `DebugSecondsPerWeek=3` actif =
   pratique pour voir défiler les saisons.
2. Retours F5 → triage (workflow acté : correctif de volet, ou dette/backlog).
3. Puis **volet B (vie macro visible)** et **volet C (heatmaps F6)** — tout
   est spécifié dans `06_organes_overlays_viemacro.md` (§4-7 et §8-10).
   `ENGINE_VERSION` : 0.2.2 → 0.2.3 (B) → 0.3.0 (C, fin de tranche).
4. Fin de tranche : remettre `DebugSecondsPerWeek=0`, noter les mesures de
   taille snapshot ici, puis t7 = packaging PyInstaller.

## Lien dette
Lève progressivement **D24** (le « portage C# » devient « pont », plus un portage
intégral) + **D2/D3/D4/D8** (rendu/scène). À refléter dans `DETTE.md`/`BACKLOG.md`
quand le sprint démarre.
