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
| ② | `02_regulateur_banc_partage.md` | régulateur de cadence (15 FPS si semaine en retard, plein en Planification / caméra qui bouge) + banc de partage (4 sous-phases A : régulateur off/on × priorité BelowNormal/Normal) | intact | **fait** (1a7eeeb) |
| ③ | `03_hauts_paliers.md` | hauts paliers : mesurer l'envoi au GPU (mémoire vidéo, textures créées par image) au cran ×4↔×32, levier si trouvé | intact | **fait** (9828dee ; mesure, levier inerte retiré) |
| ④ | `04_bilan_protocole.md` | bilan VM + protocole d'un run PC + clôture | intact | **fait** (2026-10-28, non commité) |

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

## §3 — ③ hauts paliers : envoi au GPU au cran (2026-10-28)
**Fait** (vue C# seule, golden `fecccded…` intact, pont inchangé, `dotnet build` vert) :
- `world/WorldView.ZoomGpu.cs` (neuf) : photo de compteurs CUMULÉS à chaque image de la
  fenêtre du cran → par cran, ligne « GPU fenêtre … | pire image … » au rapport Z (touche Z
  et `perf_vm.sh -Z`) : mémoire vidéo / textures / tampons (`Performance.Monitor.RenderVideoMemUsed`,
  `RenderTextureMemUsed`, `RenderBufferMemUsed` — noms vérifiés dans GodotSharp 4.6), pages
  d'atlas neuves (dont dédiées, ms de création) / resservies / détruites (dont dédiées),
  rendus de page, cuissons, Mpx cuits ; + pic de mémoire vidéo de la fenêtre.
- Compteurs ajoutés : `AtlasPages` (`CreeesTotal`, `CreationUsTotal`, `ReutiliseesTotal`,
  `DetruitesTotal`, `Rendus`, `DedieesCreeesTotal`, `DedieesDetruitesTotal`),
  `PlantBaker.PixelsCuits`. `WorldView.ZoomJournal.cs` branché (aucune colonne retirée).

**Mesure** (`perf_vm.sh -Z 4 -S 1521550718 -w 90 -c 1650,950`, automne an 2, 590 plantes)
[n=3 allers-retours, VM llvmpipe, charge 1-10 : temps peu fiables, volumes transposables] :
- Bas paliers : 1 page partagée 2048² neuve par cran ou presque (+32 Mo textures ;
  création 11-363 ms d'UN bloc, dans le poste « cuisson » donc attribuée), 0,02-0,7 Mpx cuits.
- **×8+ : le va-et-vient = pages DÉDIÉES** (une cible de rendu à la taille exacte d'une grande
  plante) : ×4→×8 6 neuves dont 5 dédiées ; ×8→×16 4 dédiées neuves + 9 dédiées détruites ;
  ×16→×32 10 dédiées détruites (−272 Mo) ; ×32→×16 5 dédiées neuves (+128 Mo, 5,6 Mpx) ;
  ×8→×4 3-5 dédiées détruites (−40 à −68 Mo).
- Sur la VM les pires images ne portent souvent AUCUN mouvement GPU (rendu llvmpipe ~200 ms
  partout) : la VM ne peut pas relier le pic au volume ; le run PC le peut.

**Levier essayé puis RETIRÉ (inerte)** : toute page partagée vidée en réserve + élagage étalé
(1 page / 500 ms). Résultat [n=1 aller-retour] : rafales de destruction inchangées (9-13
par cran) — ce sont des pages dédiées, hors réserve ; et en 4 s par palier les pages
partagées ne se vident pas. Code retiré, seule l'instrumentation reste.

**Écart au kickoff** : le kickoff soupçonnait la cuisson en images plus grandes en
général ; la mesure isole les **pages dédiées** (création ET destruction en rafale) aux ×8+.
**Prochaine hypothèse** (à trancher au ④ sur le rapport Z PC, colonnes GPU) : le non-attribué
du PC (×8→×4 453 ms dont 10 attribués) = destruction des pages dédiées dans la même image
(QueueFree → libération des cibles de rendu hors postes). Levier candidat si confirmé : file
de destruction étalée pour les pages dédiées, et/ou budget de pixels cuits par image à ×8+.
Note D116 posée dans `DETTE.md`.

## §4 — ④ bilan VM + protocole PC (2026-10-28)
Golden `fecccded…` intact (vérifié en fin de tronçon), `dotnet build` vert, aucun code touché.

### Bilan VM du sprint (avant → après ①→③)
[VM llvmpipe, graine 1521550718 `full` ; « avant » = « Bilan VM du sprint » de
`sprint_fluidite_pc_leviers/00_etat.md` ou mesure « avant » du ① ; charges VM différentes]
| mesure | avant | après | limite |
|---|---|---|---|
| A (1 s demandée), s/sem — A1 = régulateur OFF | 2,10 | 2,01 | [n=1 run chacun, charge 0,9→4,5] |
| A3 (régulateur 15, = le jeu livré), s/sem | — | 1,82 | [n=1 run, VM ; régulé 0 %] |
| B (rendu suspendu), s/sem | 1,32 | 1,56 | [n=1 run chacun ; B joué ~s133-149 (an 3), monde plus gros : ~20 700 seg.] |
| B : tick moteur moy. | 833 ms | 940 ms | [idem] |
| C (moteur en pause) : moy. image | 208,5 ms | 193,0 ms | [n=1 run, bruit VM ±10] |
| C : draw calls | 648 | 519 | [n=1 run chacun] |
| régulateur engagé (A3 / A4) | — | 0 % / 1 % | [n=1 run, VM : delta Godot plafonné, cf. §2] |
| balayage zoom 12 crans : pire image moyenne | 249 ms | 263 ms | [n=1 aller-retour chacun, charge 3,8→4,3] |
| headless an 1 (`--delta`), gc moy/max | 39/217 ms (① avant) | 4/95 ms (gc off même run : 30/202) | [n=3 runs, charge 1→9 : peu fiable] |
| headless an 1 (`--delta`), `_snapshot` moy/max | 196/423 ms (① avant) | 166/384 ms | [idem] |
| headless an 1 (`--delta`), tick moy/max | 872/1 679 ms (① avant) | 1 014/1 600 ms | [idem : charge montée à 9] |
| headless an 1 complet (sans `--delta`), tick / snapshot / gc moy. | — | 739 / 124 / 2 ms | [n=3 runs, charge 4,3→1,1] |

Lecture : sur la VM, rien ne départage les 4 sous-phases (1,82-2,02 s/sem, images 212-217 ms
[n=1 run]) : priorité Normal refusée sous Linux (A2/A4 = BelowNormal en fait) et régulateur
~jamais engagé. Seuls résultats VM solides : GC sans pics (moy. 30 → 4 ms/sem, pire 202 → 95 ms
[n=3+3 runs même session, charge 1→9]) et `_snapshot` −15 % (§1). Hauts paliers : même
signature qu'au ③ (×8→×16 : 11 pages dédiées détruites ; ×16→×32 : 10, −272 Mo), pires images
VM sans mouvement GPU (rendu llvmpipe partout). **Tout se tranche au run PC.**

### §F5 — protocole d'UN run PC
1. Godot → Projet → Paramètres → Run → **Main Run Args** :
```
--capture-banc=full --capture-seed=1521550718 --capture-etalonnage=25 --capture-banc-3phases=25,25,20 --capture-banc-partage=20 --capture-banc-cadence=1 --capture-banc-semaine=90
```
   F5, ne rien toucher jusqu'à `[banc] FIN` (~4-5 min sur la VM, amorçage compris ; au PC
   probablement moins), puis copier **tout le rapport console** à partir de `── phase C`
   jusqu'à `[banc] FIN` (le bloc « synthèse partage » est indispensable).
2. Vider les Main Run Args, 2ᵉ F5 : en Planification, molette **×0,5 → ×32 → ×0,5** en
   marquant ~2 s par palier (sans bouger la souris entre crans), puis **touche Z** → copier
   le rapport (lignes « GPU fenêtre … | pire image … » comprises).

### Comment lire le run PC pour décider
- **Régulateur** (A3 contre A1, BelowNormal tous deux) : si A3 ≤ 2 s/sem et nettement sous
  A1 → régulateur **gardé tel quel** (c'est le défaut livré). Si A3 ≈ A1 avec « régulé »
  ≥ 20 % → l'hypothèse « le rendu vole le CPU / le TDP » est **réfutée** : régulateur
  inoffensif, on le garde ou on le retire (choix Nico), la cadence doit venir du moteur.
- **Régulateur jamais engagé** (« régulé » ≈ 0 % en A3/A4 alors que s/sem > 1,2) → le
  constat VM du §2 (`_timeAccum` en retard sur l'horloge) vaut aussi au PC : passer la
  condition « semaine due » à l'horloge murale (petit tronçon vue), puis refaire ce run.
- **Priorité** (A2 contre A1, A4 contre A3) : si Normal gagne ≥ 0,3 s/sem sans faire
  monter « img moy » de plus de ~10 ms ni le p99 au-delà de 100 ms → **priorité Normal par
  défaut** ; si le gain se paie en images (> 100 ms en hausse) → BelowNormal reste. Vérifier
  que la ligne `(priorité : Normal posée)` apparaît (sinon « non applicable » = rien testé).
- **Cible** : la meilleure sous-phase ≤ 2 s/sem **et** p99 < 100 ms → D116 cadence close.
  Sinon le reste se joue côté moteur (tick) ou avec l'enchaînement anticipé (écarté par
  Nico pour 2 s de latence — ne se rouvre qu'avec son accord).
- **Hauts paliers** (rapport Z) : pour ×8→×4, ×16→×8, ×16→×32, comparer la pire image et sa
  colonne « détruites … dont N dédiées ». Si la pire image porte les destructions de pages
  dédiées et que le non-attribué ≈ la pire image → levier candidat (file de destruction
  étalée des pages dédiées, note D116). Si la pire image n'a aucun mouvement GPU → piste
  pages dédiées réfutée au PC aussi, la cause reste hors instruments.

### Questions F5 (ressenti seul)
1. En Saison, quand le moteur est en retard, la vue passe à 15 FPS : gênant à l'œil ?
2. La caméra (molette, glisser, rotation) reste-t-elle fluide (plein régime ~1 s après) ?
3. L'à-coup aux hauts zooms (×8 ↔ ×32) : plus, moins ou pareil qu'avant ?
4. HUD « pont 0.6.0 » inchangé, rien d'autre ne change à l'écran.

## §REPRISE
①②③ commités (80ea965, 1a7eeeb, 9828dee) ; ④ fait (bilan VM, protocole PC, note D116,
BACKLOG ; non commité, journal laissé à l'orchestrateur). **Sprint clos côté code.**
Prochain : **le run PC de Nico** (§4 « §F5 — protocole d'UN run PC »), lu avec §4 « Comment
lire le run PC » → décision régulateur / priorité / condition « due » / pages dédiées.
