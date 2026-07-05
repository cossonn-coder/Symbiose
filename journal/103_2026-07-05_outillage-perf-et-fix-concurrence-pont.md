# 2026-07-05 — OUTILLAGE PERF (profileur + capture pires ticks + presse-papier) & FIX CONCURRENCE DU PONT

**Demande Nico (F5 turbo, an 6)** : pouvoir *copier-coller les perfs depuis
l'application*, *sauvegarder les ticks les plus longs + l'état à ce moment*, et
*aller vite pour les tests*. Note clé de Nico : « statistiques de tout ce qui
augmente le temps de tick, pour investiguer les priorités ». Le tout a fait
émerger un **crash du pont** capturé au même moment (voir §Fix). Travail
ad-hoc (pas un `/sprint-auto`), golden INTACT `84d35983…` de bout en bout.

## Fix — concurrence du pont SimBridge (bloquant)

Symptôme F5 : `[SimBridge] Réponse non-JSON : 0.4],[7,4,…` puis `step_week en
échec` — trois réponses (`fields`/`temperature`/`snapshot`) concaténées et
tronquées, l'erreur suivant `[VoicePanel] fermé`. **Cause racine** :
`SimBridge.Request()` faisait `WriteLine`+`ReadLine` **sans verrou** alors qu'il
est appelé depuis deux mondes — thread principal (voix/init/skip, SYNCHRONES) et
threads du pool (`Task.Run` step/action/fields). Le garde `PipeFree` ne
coordonne que les lancements async entre eux ; il n'empêche pas un appel
synchrone du thread principal de chevaucher une `Task` en vol. Scénario réel :
**heatmap F6 ON** (`Fields()` en vol) **+ panneau de voix** (`Carnet`/`Pages`
synchrones) → deux threads sur le même pipe → lignes JSON entrelacées → désync
permanente. Aggravant : la machine `fields` tourne même en pause
(`WorldView.cs`, le `return` de fin est après). **Correctif** : verrou `_ioLock`
autour du seul write→read dans `Request()` — chaque échange devient atomique,
quel que soit l'appelant. C'est le « maître/esclave strict » que l'en-tête
promettait, enfin garanti. `core/SimBridge.cs`. `dotnet build` vert.

## ① Profileur headless du monde complet — `tools/profile_monde.py` (nouveau)

Répond à « où part le temps de tick, sur le VRAI monde, pour prioriser ». Monte
le monde `config="full"` VIA le serveur (`SimServer.cmd_init` — fidèle au F5,
zéro duplication du pré-vieillissement), le grandit jusqu'à `--week N` (défaut
262 ≈ an 6 printemps), puis sort **(1)** le ms/tick ABSOLU non instrumenté et
**(2)** la table cProfile triée par temps propre = la carte « qui coûte quoi ».
Régime HORS-LIGNE, sans Godot ni pont → cProfile externe au moteur → golden
INTACT par construction. C'est aussi le **bras PERF du futur banc de D67**.

**Table an 6 (VM, ~1,96 s/tick)** : `empreintes.py _plots_in_radius` (0,50 s) +
`light_index.py covering` (0,36 s) + `light.py compute` (0,34 s, cumul 1,40 s =
la phase entière) + `_point_in_capsule`/`_point_in_swept_rect` + `at_plot`. La
géométrie lumière+empreintes ≈ **la moitié du tick** → chiffre et VALIDE la
prémisse de D67 (couper les émetteurs d'ombre des petites plantes).

## ② Capture des pires ticks côté serveur

`tools/simserver/perf.py` : `diagnostic(engine, ms)` = dump LÉGER (semaine, N,
segments, RSS, répartition par tuile / par espèce) construit directement depuis
`game_state`, `len(p.segments)` O(1) ; `WorstTicks(k=5)` garde le top-K en
mémoire (borné → coût run-éternel nul) et écrit sur disque (`perf_dumps/`,
gitignoré) chaque **record absolu**. `commands.py` : init du traqueur dans
`cmd_init`, alimentation après le chrono dans `cmd_step_week` (dump construit
UNIQUEMENT si le tick entre dans le top-K → coût nul sur les ticks ordinaires),
nouvelle commande `cmd_perf_report`. `server.py` : dispatch `perf_report`.
Serveur-only → golden NEUTRE. Testé : top-K trié, 3 fichiers pour 3 records.

## ③ Presse-papier enrichi côté Godot

Touche **C** → `SimBridge.PerfReport()` (synchrone, désormais sûr grâce au
verrou) → rapport formaté (métriques client live + serveur + top-K pires ticks +
état courant, répartition tuile/espèce/segments) → `DisplayServer.ClipboardSet`.
`WorldView.Controls.cs` (touche), `WorldView.Hud.cs` (`CopyPerfReport` +
`AppendDump` + légende + `using System.Text`). `dotnet build` vert.

## Nettoyage — test de déterminisme (dette pré-existante)

`test_sim_server` échouait **déjà au HEAD** 239/245 : les 6 tests « byte-
identiques » comparaient le bloc `perf` (`ms_tick`/`rss_mo`, ajouté au snapshot
en D66④) sans le masquer — non déterministe par nature, faisait échouer à tort
alors que la SIMULATION est déterministe. Correctif dans le harness
(`tests/simserver/harness.py`) : `_scrub()` neutralise `ms_tick`/`rss_mo` du
`snapshot` avant enregistrement de `raw_lines` (seul usage = déterminisme),
`n_plants` conservé. **Suite → 245/245 verte.**

## État

Golden final `84d35983…` (INTACT). `test_sim_server` 245/245. Fichiers touchés
en zone verte sauf `WorldView.Hud.cs` = 🟡 311 LDC pur (responsabilité unique
« HUD debug », toléré ; candidat à extraire `CopyPerfReport`/`AppendDump` en
partial via `/refactor` → **D68**). Pointeur vers `profile_monde.py` ajouté à
**D67** (bras PERF du futur banc). **Reste F5 Nico** : rejouer le scénario du
crash (heatmap F6 + panneau de voix en turbo) → plus de `Réponse non-JSON` ;
touche C ; dumps dans `data/code/perf_dumps/`.
