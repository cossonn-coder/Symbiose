# Sprint FLUIDITÉ PC (D116 + lisière D112 c/j) — carnet de conception

> Phase : **B — exécution** (`/sprint-auto`). Conception figée le 2026-10-26 ; ① ② FAITS. Sprint précédent : `sprints/perf/fluidite/sprint_fluidite_an2/00_etat.md`
> (golden `fecccded…`, pont 0.5.57). Mesures PC de référence : `DETTE.md` D116.

## Cible (Nico, 2026-10-26)
PC (i5-4200H, 2 cœurs / 4 threads, HD 4600), an 2, 1 s/sem demandée → **≤ 2 s/sem effectives**,
**aucune image > 100 ms**, automate compris. Aujourd'hui : 3,33-3,75 s/sem, 105-108 images
> 100 ms sur 271-310 [n=3 runs, PC].

## Constats de la phase A (vérifiés au code / mesurés sur VM le 2026-10-26)
1. **« Non attribué » contient le rendu CPU** : `PerfPostes.TotalMs()` ne compte que les postes
   C# ; le rendu CPU (27-34 ms/image) n'y est pas (`WorldView.PerfMesure.cs:157-159`). Ancien
   rapport PC moteur AU REPOS (perf_vue, 2026-07) : non attribué 30,6 ≈ rendu CPU 28,7 ms
   [n=1 run, PC]. Le vrai inexpliqué D116 ≈ 70-81 − 27-34 ≈ **40-50 ms/image**, et il
   n'apparaît qu'avec le moteur en marche → contention présumée (toujours NON mesurée).
2. **« butineurs _Draw » 5-7 ms/image avec 0 butineur** : en hiver `ForagerLayer` et
   `PollenLot` sortent en tête de fonction (aucune entrée, pollen vidé à la saison) → une
   fonction quasi vide chronométrée à plusieurs ms = fil principal **déchedulé pendant la
   mesure** (2ᵉ indice de contention). L'invalidation par image (8-10 appels/s) reste à
   trouver mais coûte ~0 en soi.
3. **Moteur PC 1,7× plus lent que la VM headless**, alors qu'en juillet le PC était ~1,3×
   plus RAPIDE (headless) → le tick au PC est mesuré SOUS la charge de Godot ; vitesse PC
   moteur seul **inconnue**.
4. Profil tick s98 (VM, cProfile ×3 ticks, 637 pl.) : tick_light 21 % · tick_populations 14 %
   · _apply_uptake 9 % · apply_disturbances 7 % · grow_plant 6 % · _update_physiology 5 %
   · succession 4 % · décomposition 4 % [n=1 run, cProfile gonfle le Python pur].
5. **Pont, mesure delta (s96-102, VM)** : 0 % de plantes identiques d'une semaine à l'autre ;
   segments = 70 % des octets plantes (plantes = 56 % de la réponse 2,3 Mo). Dans ~99 % des
   segments le SEUL champ qui bouge est `age_weeks` (+1/sem) ; `length_cm` bouge dans ~24 %
   des segments, `genes` (9 % des octets plantes) ne bouge jamais. Un « diff par plante » est
   donc inutile ; un diff par segment exigerait `age_weeks` → semaine de naissance.
6. **Lisière** (capture VM ×0,5, graine 1521550718 = prairie N / prairie E / friche S /
   forêt O) : masse sombre de forêt sur une partie du bord O seulement, aplats verts rayés
   ailleurs, aucune rivière ni falaise (falaise 2,7 % des terrains). Au démarrage :
   `Build(Seed)` (`WorldView.cs:311`) puis `ApplySnapshot` → `SetCeinture` (`Snapshot.cs:137`)
   → la ceinture DOIT arriver ; le besoin de F10 n'est pas expliqué à la lecture.
7. HUD : « pont 0.5.30 — 2026-07-18 » affiché alors que le pont est 0.5.57 (étiquette figée).

8. Captures ×2 (bords O et S) : grands aplats unis (la « forêt » O = polygone sombre sans
   arbre en lisière), **coutures en fils fins** entre triangles, aucune texture ; friche =
   quelques points de fleurs + bouleaux. Le monde est déjà rendu dans un SubViewport 960×540
   (pixellisé ×2) : le défaut est le DESSIN (aplats, coutures), pas l'absence de pixellisation.
9. LDC : `DecorLayer.cs` 298 code (512 total) → plein ; tout motif neuf va dans un partial neuf.

## Décisions arrêtées (Nico, 2026-10-26)
- **Méthode : diagnostic PC d'abord.** Ce sprint instrumente (un seul F5 = rapport en 3 phases :
  normal / rendu suspendu pendant les steps / moteur en pause) et corrige les instruments ; les
  LEVIERS (moteur, vue) se conçoivent dans une 2ᵉ `/conception` sur les chiffres PC.
- **F10 = bug d'affichage** (au démarrage le décor est faux, F10 ×2 le remet) — à reproduire.
- **Lisière refaite en DA SNES** (pas seulement corrigée) dans ce sprint.
- Q3 (cadence vs images si les deux ne tiennent pas) : REPORTÉE à la 2ᵉ conception (chiffres).

- **DA lisière (Nico)** : niveau de détail des zooms ×1 / ×0,5, **assets en patchwork** (kit de
  pièces pixel-art précuites, assemblées au hash) ; pas d'ombre de lisière sur le jardin.

## Carte des tronçons (FIGÉE 2026-10-26)
| # | Kickoff | Contenu | Golden | État |
|---|---|---|---|---|
| ① | `01_instruments_banc3.md` | banc E 3 phases (normal / rendu suspendu / moteur en pause) + ménage instruments + PollenLot + oracles périmés | intact | **FAIT** |
| ② | `02_lisiere_bug_coutures.md` | bug « il faut F10 » reproduit/corrigé + coutures | intact | **FAIT** (F10 non reproduit → trace console ; coutures corrigées) |
| ③ | `03_lisiere_kit_foret.md` | atlas patchwork + prairie/friche + forêt | intact | à faire |
| ④ | `04_lisiere_eau_roche_bilan.md` | rivière + falaise + bilan VM + protocole PC (1 run) + clôture | intact | à faire |

## Bilan ① (2026-10-26) — golden intact `fecccded…`, pont **0.5.58**, `dotnet build` vert
- **Banc 3 phases** : `--capture-banc-3phases=A,B,C` (`perf_vm.sh -3 25,25,20 -A 1 -W 90`),
  `world/WorldView.Banc3Phases.cs`. Ordre **C → A → B** (écart au kickoff, mesuré : en A→B→C la
  phase C voyait un jardin 24 sem. plus tard + la cuisson qui rattrapait B). B = `RenderLoopEnabled
  = false` + `Engine.MaxFps = 60` (sans vsync la boucle tournait à vide) + file de cuisson figée
  (`BakeQueue.Suspendue`, sinon pages « cuites » jamais rendues). B s'allonge jusqu'à 6 steps.
  Synthèse A↔B / A↔C en fin de rapport. La phase C bloque les steps et fait rejouer la journée.
- **Instruments** : rendu CPU dans le bilan (« inexpliqué = moyenne − postes − rendu CPU ») ;
  `TimeProcess` retiré (Godot y publie le MAX du process de la seconde, pas une valeur par image) ;
  `[machine]` dit « banc (arguments de capture) » ; ligne `[moteur]` = lanceur + pont + Python
  (init du pont 0.5.58 : `python {version, implementation, executable}`) ; HUD : version du pont
  reçue du serveur (`WorldView.Build` ne la porte plus).
- **PollenLot / « butineurs _Draw » (constat 2 RÉFUTÉ)** : aucune invalidation parasite — au banc,
  `GetCanvasTransform`/projection ne changent qu'au cadrage [n=2 runs instrumentés, VM]. Le
  « 0 butineur » était lu en FIN de mesure : au début ~53 butineurs volent (redessin 24 Hz légitime)
  + ~270 fleurs pollinisées. Le rapport donne maintenant butineurs et fleurs **début→fin**. En hiver
  vrai (0 butineur, 0 pollen) : **0 appel/s** [n=1 run, VM]. Ajout : `ForagerLayer` ne se redessine
  plus au snapshot s'il n'a rien à tracer. Avant : 5 appels/s à 4 FPS ; après, phase A : 4 appels/s
  à 3,9-4,4 FPS [n=1 run avant / n=2 runs après, VM].
- **Oracles** : `test_population` recalé `a60c4a31…` — dérive EXPLIQUÉE par 3 commits moteur
  voulus, chacun ayant re-figé le golden (`db10b96` effondrement météo ①, `a9c1b82` bilan hydrique
  ①, `b30806d` nectar par espèce ⑦ ; parcours commit par commit). `test_vent` 54/54 : oracle faux
  (posait l'humidité-sol, `fungal_disease` lit `wetness_memory` depuis `8de6e21`) → feuillage
  mouillé posé, pas de régression moteur, pas de dette. `test_peripherie_pont` : « ≥ 0.5.41 ».
  `test_sim_server` 289/289. → **D116 (d) fermable**.
- **Mesure VM** (`-3 25,25,20 -A 1 -W 90 -S 1521550718`, charge 4-6 → peu fiable, llvmpipe) :
  A 2,51-2,79 s/sem, tick moteur 1124-1204 ms ; B 1,79 s/sem, tick 867-872 ms ; C moyenne
  196-201 ms/image, inexpliqué 63-71 ms ; A moyenne 226-254 ms, inexpliqué 85-90 ms [n=2 runs, VM].
  Même sur 16 threads, le rendu llvmpipe ralentit le moteur ~1,3× [n=2 runs, VM] — les absolus ne
  valent pas le PC.
- Taille : `core/SimBridge.cs` 324 LDC (🟡, une responsabilité : le pont) ; reste ≤ 300.

## Bilan ② (2026-10-26) — golden intact `fecccded…`, `dotnet build` vert, pont inchangé (0.5.58)
- **Bug « il faut F10 ×2 » : NON reproduit sur VM.** Nouvel argument `--capture-decor-f10=<s>`
  (`capture_vm.sh -D SEC`) qui rejoue F10 ×2 après s secondes. Même image à la même frame
  avec/sans F10 ×2 : graine 1521550718 ×0,5 (écart = animation du jardin), graine 42 ×0,5
  (4 px), rotation D35 1 + 1 semaine turbo (0 px) [n=1 run par cas, VM]. Pistes (a)(b)(c)
  réfutées au code et à la mesure : à l'ouverture, `Build(Seed)` pose un profil de repli,
  `ApplySnapshot` le remplace par le pont AVANT la 1re image ; tous les snapshots `full`
  portent `ceinture` ; projection pure (orientation seule). → **ligne console** posée
  (`DecorLayer.Banc.cs` `TracerSource`) : `[DecorLayer] profil pont : N … · E … · S … · O …`,
  écrite seulement quand source ou motif change.
- **Coutures : cause observée = arrondi des sommets au pixel** (`snap_2d_vertices_to_pixel`
  du SubViewport). Snap coupé (essai jetable) → pointillés disparus. Mécanisme : la frange et
  le seuil étaient EMPILÉS sur le fond, avec des bords latéraux colinéaires aux extrémités
  différentes ; arrondis, ils divergent d'½ px et le fond transparaît en pointillé le long des
  pentes iso. Un 1er essai (pas chevauchants de 10 cm) n'a fait que DÉPLACER les pointillés —
  abandonné. Correctif : bandes JOINTIVES (seuil | frange | fond) dans `DrawSecteur`, et eau /
  liserés jointifs dans `DrawRiviere`. Même nombre de triangles, toujours 1 lot.
  Falaise : aucun empilement colinéaire (strates aux sommets partagés), non touchée.
- **Captures** (`captures_02/`) : `coutures_x05_avant_apres.png` (bord O ×0,5, gauche avant :
  2 lignes pointillées + pointillés dans le seuil ; droite après : aucun) ;
  `bord_O_x2_avant_apres.png` (×2, haut avant : ~6 fils, bas après : aucun) ;
  `riviere_x2_avant.png` / `_apres.png` (banc `peripherie` ×2 : pointillés bleus dans les
  liserés puis disparus). Restent des RAIES de teinte (jitter par pas) = style → ③.
- **Trouvé pour ③ (non corrigé, style/hash)** : `BuildFromBridge` tire `SeedSecteur` de
  `ceinture|{cote}|{type}` SANS le seed du terrain → tous les terrains ont la même lisière
  pour un même type de bord (philo #7) ; et le hash djb2 des arbres brasse mal : forêt O de
  la graine 1521550718 = 13 arbres, TOUS des bouleaux, TOUS au bout SO du bord (densité moteur
  0,635) — c'est la « masse sombre sans arbre » du constat 6. Le kit patchwork ③ doit
  semer avec un hash brassé (cf. D92) et une graine qui inclut le seed du terrain.
- LDC : `DecorLayer.cs` 299, `DecorLayer.Banc.cs` 34, `WorldView.Capture.cs` 151.
- **F5 Nico** : (1) au démarrage, lire la 1re ligne `[DecorLayer] profil …` dans la console
  Godot : `pont` attendu. Si le décor est faux, noter cette ligne puis celle qui suit F10 ×2 ;
  (2) les fils fins de couture doivent avoir disparu (×0,5 à ×4).

## §REPRISE
Conception FIGÉE → doc `docs/perf/fluidite/conception_fluidite_pc.md`. Exécution :
`/sprint-auto sprint_fluidite_pc` — **tronçon suivant = ③ `03_lisiere_kit_foret.md`** (lire « Trouvé pour ③ » du bilan ②).
Pour le protocole PC du ④ : lancer le jeu avec `-- --capture-banc=full --capture-seed=1521550718
--capture-etalonnage=25 --capture-banc-3phases=25,25,20 --capture-banc-cadence=1
--capture-banc-semaine=90` (mêmes arguments que `perf_vm.sh -3 … -A 1 -W 90`), rapport au
presse-papier puis le jeu quitte. Après le sprint :
Nico fait 1 run PC → 2ᵉ `/conception D116` (leviers moteur/vue + arbitrage cadence ↔ images).
