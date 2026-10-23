# ① Banc de cadence — mesurer avant d'optimiser

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, `docs/perf/fluidite/conception_fluidite_an2.md`.
**Golden** : intact (instruments seulement, hors tick). Vérifier `fecccded…` en fin de tronçon.

## Objectif
Une **référence sérieuse et reproductible** de la fluidité an 2, et **la cause du
ralentissement « automate »** que Nico voit au F5 (côté Python l'automate ne coûte que
~24 ms/tick [n=1 run] : chercher ailleurs — vue, onglet, pont).

## À faire
1. **Banc headless** `data/code/tools/banc_cadence.py` (NOUVEAU, lecture seule) :
   monte `full` via `SimServer.cmd_init` (comme `tools/profile_monde.py`), option automate
   (`cmd_automate({"op":"on","profil":{"desherbage":"curatif"}})` — profil par défaut de la
   touche A, cf. `world/WorldView.Automate.cs`), puis `cmd_step_week` en boucle ; par semaine :
   tick moteur (`srv._last_ms_tick`), durée `jouer_tick` de l'automate, durée `_snapshot()`,
   taille JSON compacte de la réponse, plantes vivantes. Sortie : moyenne/max par an.
   `--runs N` (défaut 3) lancés **en série**, `--seed`, `--semaines`, `--automate`.
   Avertir si la charge VM (`/proc/loadavg`) > 4 (même règle que `tools/perf_vm.sh`).
   Pas de cProfile dedans (fausse les temps absolus) ; `tools/profile_monde.py` reste l'outil
   de répartition.
2. **Banc E avec automate** : option `-a` de `tools/perf_vm.sh` → argument de capture
   (même mécanique que `--capture-banc-cadence`, cf. `ArgCapture` dans
   `world/WorldView.Etalonnage.cs`) qui branche l'automate au début du banc. Deux variantes
   à couvrir : **onglet Automate ouvert** (ce que fait la touche A : `OuvrirConsultation`)
   et **automate branché onglet fermé**. Le rapport du banc (touche E au PC aussi) doit
   **dire si l'automate est branché et si l'onglet est visible**.
3. **Mesures** (n ≥ 3 runs par cas, en série, charge VM < 4) :
   - headless sans/avec automate, 156 semaines, graine 1521550718 ;
   - banc E `-A 1 -W 90` : OFF / automate onglet fermé / automate onglet ouvert.
   Remplir le tableau de `00_etat.md` (§Mesures) avec les limites entre crochets.
4. **Diagnostic automate** : comparer les postes du rapport E (étalement par famille,
   cuisson, rendu CPU, retard de cadence, GC) entre les 3 cas. Nommer la cause **mesurée**
   (ex. : panneau de consultation qui redimensionne le viewport, `Rendre()` du journal,
   vie macro dérangée par les gestes…). Si la cause est triviale et purement vue, la
   corriger ici ; sinon la décrire pour le ④.
5. Éclaircir l'écart de graine du banc E (`-S 1521550718` affiché « seed 1521550720 »).

## Ne PAS faire
- Optimiser quoi que ce soit dans le moteur (②) ou le pont (③).
- Lancer `test_epaisseur_500ans`.

## Fin de tronçon
`dotnet build Symbiose.csproj` vert ; golden intact ; `00_etat.md` mis à jour (mesures,
cause automate, état ①) ; commit.
