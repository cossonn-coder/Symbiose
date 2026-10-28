# Sprint FLUIDITÉ PC — PARTAGE (3ᵉ `/conception D116`) — carnet de conception

> Phase : **CONCEPTION FIGÉE le 2026-10-28** (OK Nico) → prêt pour `/sprint-auto`.
> Doc : `docs/perf/fluidite/conception_fluidite_pc_partage.md` (LIRE AVANT TOUT TRONÇON).
> NE JAMAIS lancer `test_epaisseur_500ans`. Golden jamais re-figé dans ce sprint.
> Entrée : run PC du 2026-10-27 → `sprints/perf/fluidite/sprint_fluidite_pc_leviers/00_etat.md`
> (fin du fichier). Golden `fecccded…` (à préserver), pont 0.6.0.
> Cible inchangée : PC Nico (i5-4200H, 2 cœurs / 4 threads), an 2, 1 s/sem demandée →
> **≤ 2 s/sem effectives en A**, aucune image > 100 ms.

## Point de départ (PC, 2026-10-27, s90 ×4) [n=1 run, PC]
- A (normal) **2,78 s/sem** : tick 1 819 ms, pont 726 ms, images 59,6 ms moy.
- B (rendu suspendu) 1,19 s/sem : tick 842 ms → le moteur seul tient la cible.
- C (moteur en pause) 30,9 ms/image, 32 FPS.
- Il faut −0,78 s en A. Le rendu multiplie le tick par ~2,2.
- Zoom ×4 ↔ ×32 : jusqu'à 453 ms (×8→×4), la plus grande part n'est attribuée à aucun poste.

## Mesure d'ouverture (VM, 2026-10-28, `full` graine 1521550718, s85-100, mode delta) [n=1 run, VM, charge 0,3→5]
- Par semaine : tick 881-1 686 ms · `_snapshot` 201-508 ms · `json.dumps` 54-123 ms.
- Ramasse-miettes Python : 25-47 ms par semaine, plus une collecte complète (génération 2)
  toutes les ~7 semaines (s86, s93, s100) qui monte à 151-224 ms. ~190-205 k objets suivis.
- `_snapshot` ≈ 20-30 % du temps Python d'une semaine : c'est le plus gros poste hors tick.

## Leviers recensés (chiffrés, NON tranchés)
1. **Ramasse-miettes** (`gc.freeze` après l'init, seuils relevés) — résultat identique au
   bit près. Gain ~3 % par semaine, supprime les pics de 150-220 ms [estimation VM].
2. **`_snapshot` mémoïsé par plante** (ne recalcule que les plantes changées, comme le delta
   du pont) — vise −40 % du `_snapshot` [hypothèse, non mesurée].
3. **Régulateur de cadence en Saison** : si la semaine est en retard, la vue plafonne ses FPS
   (plancher à trancher) pour rendre CPU **et** budget de puissance au moteur (iGPU Haswell :
   CPU et GPU partagent le TDP et le cache L3 → hypothèse forte pour le « rendu double le
   tick », NON mesurée). Rétabli plein FPS en Planification et quand la caméra bouge.
4. **Banc de partage** : balayage dans UN run PC (plafond FPS 0/20/15 × priorité moteur
   BelowNormal/Normal) → courbe cadence ↔ images.
5. **Enchaînement anticipé du step** (le moteur repart pendant que la vue lit la semaine) —
   gain ~200-300 ms en A [estimation], un geste cliqué attend au pire une semaine de plus.
6. **Hauts paliers** : instrumenter l'envoi au GPU (mémoire vidéo, textures créées par image)
   au changement de palier, puis levier si trouvé — tronçon vue.


## Décisions arrêtées (Nico, 2026-10-28)
- **Pas de carte graphique dédiée** (Intel HD 4600 seule) : pas de levier « autre GPU » ;
  on fait au mieux avec cette machine.
- **Plancher 15 FPS accepté** en Saison quand le moteur est en retard (levier 3).
- **Enchaînement anticipé (levier 5) REJETÉ pour ce sprint** : jusqu'à ~2 s de latence sur un
  geste, jugé trop long → inscrit en dette (note D116), seulement si 1-4 ne suffisent pas.

## Carte des tronçons (FIGÉE 2026-10-28)
| # | Kickoff | Contenu | Golden | État |
|---|---|---|---|---|
| ① | `01_moteur_gc_snapshot.md` | moteur bit-identique : `gc.freeze` + seuils, `_snapshot` mémoïsé par plante ; banc headless n=3 | intact | **fait** (80ea965) |
| ② | `02_regulateur_banc_partage.md` | régulateur de cadence (15 FPS si semaine en retard, plein en Planification / caméra qui bouge) + banc de partage (4 sous-phases A : régulateur off/on × priorité BelowNormal/Normal) | intact | **fait** (non commité) |
| ③ | `03_hauts_paliers.md` | hauts paliers : mesurer l'envoi au GPU (mémoire vidéo, textures créées par image) au cran ×4↔×32, levier si trouvé | intact | à faire |
| ④ | `04_bilan_protocole.md` | bilan VM + protocole d'un run PC + clôture | intact | à faire |

## §1 — ① moteur : ramasse-miettes + `_snapshot` (2026-10-28)
**Fait** (tout dans `tools/`, rien dans `sim/`, pont 0.6.0 inchangé, golden `fecccded…` intact) :
- `tools/simserver/gc_pont.py` (neuf) : `regler_gc()` en fin de `cmd_init` →
  `gc.unfreeze` + `collect` + `freeze` (le monde d'un init précédent est libéré) + seuil
  gen0 2000 → **50 000** (retenu : 20 000 laisse 15 ms/sem [n=1 run]).
- `pont_delta.plante` : chemin rapide par segment — tuple BRUT (base, dir, longueur,
  épaisseur, parent, apex, naissance) égal à celui de l'envoi précédent ⇒ recopie sans
  arrondi ni cache ; recopies cumulées en un seul entier. `segments_pont.entree(s)` ajouté
  (`entrees` le réutilise).
- Outils gardés : `tools/verif_pont_identique.py` (empreinte par semaine delta + complet
  + populations, hors bloc `perf`) ; `tools/banc_cadence.py` + colonne `gc`, `--delta`, `--gc on|off`.

**Identité** : 100 semaines `full` graine 1521550718, 5 processus (HEAD ×2, neuf gc off,
neuf gc on ×2) → empreintes delta ET complet identiques chaque semaine. Le départage par
`id()` de `sim/grimpe.py` n'a rien changé [sur ce run de 100 sem.] → aucune dette.
`tests.test_sim_server` 300 ✅ (dont section 23 delta).

**Mesures** (`banc_cadence --runs 3 --semaines 104 --delta`, an 1) [n=3 runs, VM, charge 2,8→10 : peu fiable] :
| | tick moy/max | snapshot moy/max | gc moy/max |
|---|---|---|---|
| avant (HEAD) | 872/1 679 ms | 196/423 ms | 39/217 ms |
| après (gc 50k) | 1 001/1 780 ms [charge plus haute] | 166/360 ms | 2/73 ms |
- GC : **−37 ms/sem, pire semaine 217 → 73 ms** (pics gen2 supprimés).
- `_snapshot` : **−15 %** [n=3, charge variable] — **cible −40 % NON tenue**. A/B même
  processus de la seule partie segments-delta : 48-62 → 37-44 ms/sem (−22 à −29 %)
  [n=15 sem., 2 passes]. Le reste de `_snapshot` (profil s90, 5 sem.) : `leaf_symptoms`
  ~18 %, `peindre_presence` ~13 %, construction des dicts + grilles par plot ~16 % —
  ces entrées changent chaque semaine (mémoires, densités de champs) : aucune clé
  auto-invalidante bon marché sans toucher `sim/`, non fait.
- Tick : non comparable (charge VM montée pendant les runs « après »).

## §2 — ② régulateur de cadence + banc de partage (2026-10-28)
**Fait** (vue C# seule, golden `fecccded…` intact, pont inchangé, `dotnet build` vert) :
- `world/WorldView.Regulateur.cs` (neuf) : `RegulerCadence` appelé dans `_Process` juste
  après `AvancerEtalonnage` → `Engine.MaxFps = 15` si Saison ∧ `_pendingStep != null` ∧
  `_timeAccum ≥ SpwCourant` ∧ pas de caméra depuis 1 s ; sinon plafond d'origine (lu à la
  1ʳᵉ image). Ne touche rien pendant la phase B (`_b3RenduCoupe`). `SpwCourant` remplace le
  calcul de `spw` dans `_Process` (une seule règle). `NoterCameraBouge()` dans
  `UpdateCameraPan` / `StepZoom` / `RotateView` (pas de glisser caméra au code). F4 : état
  « régulé 15 FPS / libre » ; rapport de banc : ligne « régulateur ON/OFF : x % du temps régulé ».
- `core/SimBridge.cs` : `PoserPriorite(bool normale)` (BelowNormal ↔ Normal à chaud ; refus
  → « non applicable »). Défaut du jeu inchangé (BelowNormal). Fichier à 345 LDC 🟡.
- `world/WorldView.BancPartage.cs` (neuf) : `--capture-banc-partage=SEC` → A devient
  A1..A4 (OFF/15 × BelowNormal/Normal), tableau côte à côte + rappel C et B ; réglages du jeu
  rétablis avant B et à l'abandon. `Banc3Phases.cs` branché (4 points), `PerfMesure.cs` garde
  le p99. `tools/perf_vm.sh -P SEC` (implique `-3` par défaut).
- **Argument exact du run PC** : `--capture-banc=full --capture-seed=1521550718
  --capture-etalonnage=25 --capture-banc-3phases=25,25,20 --capture-banc-partage=20
  --capture-banc-cadence=1 --capture-banc-semaine=90`

**Mesure VM** (`perf_vm.sh -3 25,25,20 -P 20 -A 1 -W 90 -S 1521550718`) [n=1 run, VM llvmpipe, charge 8-10 : peu fiable] :
| | s/sem | tick | step vu | img moy | p99 | FPS | régulé |
|---|---|---|---|---|---|---|---|
| A1 OFF·BelowNormal | 2,01 | 1 097 | 1 756 | 223 | 424 | 4,5 | 0 % |
| A2 OFF·Normal* | 1,83 | 1 033 | 1 705 | 216 | 303 | 4,6 | 0 % |
| A3 15·BelowNormal | 1,83 | 1 045 | 1 772 | 218 | 331 | 4,6 | 0 % |
| A4 15·Normal* | 2,02 | 1 085 | 1 960 | 220 | 287 | 4,5 | 1 % |
C 199 ms/image, 5,0 FPS · B 1,67 s/sem, tick 958 ms. *Normal refusé sous Linux
(« Permission denied ») → A2/A4 sont en fait BelowNormal : leurs écarts avec A1/A3 sont du bruit.
- Le banc tourne de bout en bout, le régulateur s'engage (A4 1 %) et se dégage ; rien d'autre
  n'est prouvé sur la VM.
- **Écart au kickoff** : sur la VM le régulateur ne s'engage presque jamais. Explication la plus
  probable (déduite des chiffres, non vérifiée au code Godot) : avec des images de ~220 ms, le
  `delta` de Godot semble plafonné à ~133 ms (8 pas physiques de 1/60 s). `_timeAccum` avance
  alors ~0,6 fois moins vite que l'horloge murale, donc la semaine « due » arrive juste quand le
  step revient : « retard step en vol » vaut 0,0-1,4 s en A alors qu'on obtient ~2 s/sem pour
  1 demandée. Au PC (~60 ms par image) ce plafond n'agit pas, donc le régulateur devrait
  s'engager. Si le run PC montre « régulé ≈ 0 % » avec s/sem > 1, il faut passer la
  condition « due » à l'horloge murale (à trancher au ④).
- Bruit en sortie de Godot (`Can't emit non-existing signal`, `Pages in use…`) après
  `[banc] FIN` : bruit d'arrêt, le rapport est complet.

## §REPRISE
① commité (80ea965), ② fait (non commité par le sous-agent). Prochain : tronçon ③ `03_hauts_paliers.md`.
Chaque tronçon ajoute ici sa section §N (fait, mesures, écarts) et met à jour la carte.
