# ① Instruments + banc en 3 phases — un seul F5 qui dit OÙ part le CPU au PC

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, `docs/perf/fluidite/conception_fluidite_pc.md`
(§2 constats, §3 décisions). **Golden** : intact (`fecccded…`) — aucun changement moteur.
NE JAMAIS lancer `test_epaisseur_500ans`.

## Objectif
Nico fera **un seul F5** au PC (protocole écrit au ④). Ce run doit trancher : le tick PC de
1,8-1,95 s vient-il de la contention avec Godot ou d'un moteur vraiment lent ? Et les
40-50 ms/image inexpliquées viennent-elles du moteur qui tourne à côté ? Ce tronçon ne
corrige AUCUN levier de cadence : il mesure et répare les instruments.

## À faire
1. **Banc E en 3 phases** (extension du banc d'étalonnage existant, `world/WorldView.Etalonnage.cs`,
   arguments `ArgCapture(...)` ; même déroulé de montage que `--capture-banc-semaine` /
   `--capture-banc-cadence`). Un argument de capture neuf (nom au choix, documenté dans
   l'en-tête du fichier et dans `tools/perf_vm.sh`) enchaîne, au même point de banc :
   - **A — normal** : comme aujourd'hui (cadence demandée, rendu actif) ;
   - **B — rendu suspendu** : les steps continuent à la même cadence, mais Godot ne dessine
     plus (piste à vérifier : `RenderingServer.RenderLoopEnabled = false`, rétabli après) ;
   - **C — moteur en pause** : rendu actif, AUCUN step en vol (cadence arrêtée, planification
     ou pause) ; on mesure la vue seule.
   Pour chaque phase, le rapport donne au minimum : s/sem obtenues (A, B), tick moteur moyen et
   pics (côté serveur), step vu par la vue, parse JSON, lecture plantes, FPS, images > 100 ms,
   rendu CPU, somme des postes, **inexpliqué = moyenne − postes − rendu CPU**, « butineurs
   _Draw ». Durées de phase réglables (défaut raisonnable : ~20-30 s chacune, B au moins
   6 steps). En B il n'y a pas d'images : ne rapporter que la chaîne du step.
   La touche E sans arguments garde son comportement actuel.
2. **Ménage des instruments** (`world/WorldView.PerfMesure.cs`, `WorldView.PerfReport.cs`,
   `visuals/PerfPostes.cs`) :
   - le rendu CPU est **dans l'attribution** : la ligne « non attribué » devient « inexpliqué
     (hors postes et rendu CPU) » ;
   - **TimeProcess** (176-197 ms/image > durée moyenne d'image, incohérent) : comprendre ce que
     ce moniteur Godot mesure ; s'il n'a pas de sens par image, le retirer du rapport (dire
     pourquoi en commentaire) plutôt que l'afficher faux ;
   - ligne `[machine]` : ne plus écrire « banc VM (capture) » quand les arguments de capture
     tournent au PC (`CaptureActive` = `CaptureBanc != null`, vrai aussi au PC) → « banc
     (arguments de capture) » + la machine telle que détectée ;
   - **version de Python** et exécutable lancés par le pont, dans le rapport (sans changer le
     protocole si une info existe déjà ; sinon ajout opt-in, bump du pont, tests de version
     `tests/simserver/*` alignés) ;
   - libellé HUD figé `WorldView.Build` (« pont 0.5.30 — 2026-07-18 ») : afficher la version
     réelle du pont (reçue du serveur) ou, à défaut, une constante juste.
3. **PollenLot redessiné à chaque image** (`visuals/PollenLot.cs` `_Process`) : trouver ce qui
   l'invalide (pistes : `GetCanvasTransform()` qui varie d'un epsilon chaque image, projection
   `WorldToScreen(0,0)` qui bouge avec le relief/la caméra) et le corriger (comparaison avec
   tolérance, ou vrai signal). Vérifier aussi `ForagerLayer` (`QueueRedraw` à chaque snapshot).
   Mesurer les appels/s avant/après au banc VM.
4. **Oracles de tests périmés** (rouges AVANT ce sprint, D116 d) :
   - `data/code/tests/test_peripherie_pont.py` attend le pont 0.5.41 → le rendre indépendant de
     la version (ou aligné sur la constante du pont) ;
   - `data/code/tests/test_population.py` (référence `population_hash.txt` périmée, obtenu
     `a60c4a31…`) : retrouver le commit qui l'a fait dériver ; ne recaler la référence que si
     la dérive est expliquée par un changement voulu (le noter dans `00_etat.md`) ;
   - `data/code/tests/test_vent.py` 52/54 (⑥ assèchement ×2) : **investiguer** ; si c'est une
     vraie régression moteur, NE PAS corriger le moteur ici → nouvelle entrée `DETTE.md`
     (règle « une fermée, une ouverte » : la fermer contre D116 d) ; si c'est l'oracle qui est
     faux, le corriger en expliquant.
5. **Mesure VM** : banc 3 phases `-A 1 -W 90 -S 1521550718` (n ≥ 2 runs, charge notée) pour
   valider que le rapport est complet et cohérent (VM llvmpipe : les absolus ne valent pas le
   PC). Noter dans `00_etat.md` les chiffres avec leurs limites entre crochets.

## Ne PAS faire
- Optimiser le moteur, le pont ou la vue pour la cadence (c'est la 2ᵉ conception).
- Changer la priorité du processus Python, le nombre de threads, ou brider la population.
- Lancer `test_epaisseur_500ans`.

## Fin de tronçon
`dotnet build Symbiose.csproj` vert ; golden intact ; suites touchées vertes (ou rouge
expliqué + dette) ; LDC des fichiers touchés ≤ 300 (sinon partial) ; `00_etat.md` mis à jour ;
commit.
