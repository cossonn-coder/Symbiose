# ④ Vue — appliquer la semaine sans retenir la cadence ni geler l'image

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (mesures ①②③ + **cause « automate » du ①**),
le doc de conception. **Golden** : intact (vue C# pure ; pas de Python sauf si ① l'a exigé).
Filet : `dotnet build Symbiose.csproj` ; mesure : `tools/perf_vm.sh -E 30 -A 1 -W 90`
(+ `-a` du ①), n ≥ 3 runs, charge VM < 4. Le F5 visuel reste à Nico.

## Constat (banc E VM, HEAD `5c69ac6`) [n=1 run, 30 s]
Demandé 1 s/sem → **2,73 s/sem** ; « semaine en application » 13,9 s sur 30, « step en vol »
2,9 s ; cuisson : budget 4 ms/image, pics 60-74 ms ; application ~1 ms/plante sur le thread
principal [mesure VM 2026-10-15] en tranches de 6 ms/image (`BudgetPlantesUs`,
`world/WorldView.Etalement.cs`).

## Leviers (INTENTION — vérifier au code avant de graver)
1. **Chevaucher calcul et application.** Aujourd'hui le step suivant ne part que si
   `PipeFree && _etale == null` (`world/WorldView.cs:627`) : tick + application s'additionnent.
   Faire partir le step N+1 **pendant** l'application de N (au plus UN snapshot en attente ;
   un snapshot plus frais remplace celui en attente, jamais deux étalements à la fois).
   **Avant**, retrouver pourquoi la garde `_etale == null` existe (`git log -S "_etale == null"`,
   commentaires de `WorldView.Attente.cs` / `BancAccelere.cs` / `Tapis.cs`) et préserver son
   intention. Les gestes joueur (snapshot synchrone qui remplace l'étalement) restent prioritaires.
2. **Lire les plantes hors du thread principal.** `MajPlante` (`world/WorldView.Snapshot.cs`)
   appelle `StructureLoader.FromSnapshot(p)` et lit symptômes/vitalité/etc. sur le thread
   principal. Pré-digérer ces lectures **sur le thread du pool, juste après le parse JSON**
   (dans la tâche du step — `SimBridge.StepWeek` ou son appelant `Task.Run`), en données C#
   pures ; le thread principal n'applique plus que des structures prêtes. Règle : le thread
   du pool ne touche **aucun nœud de scène** ni aucun état de `WorldView` — seulement le
   dictionnaire qu'il vient de parser (même règle (a) que le pipe).
3. **Cuisson sous budget.** `BakeQueue.ProcessFile` (`visuals/BakeQueue.cs`) ne teste le budget
   qu'après la 1ʳᵉ plante : une seule `Baker.Begin` lourde fait 60-74 ms. Mesurer ce qui coûte
   (préparation d'atlas ? très gros arbre ? `CommitRendered` / `ReleaseOffscreen` ?) et le
   découper ou l'étaler — sans jamais afficher de trou (garder l'ancienne image).
4. **Cause « automate » du ①** : la corriger ici si elle n'a pas été soldée au ①.

## Cible
Banc E VM `-A 1 -W 90` : **semaine effective ≤ 1,5 s** et p99 des postes CPU (hors rendu GPU
logiciel) ≤ 100 ms, automate OFF et ON (onglet ouvert). Rapporter aussi FPS/draw calls pour
vérifier qu'on ne dégrade pas le rendu.

## Ne PAS faire
- Toucher au YSort par plante, au LOD, à la DA (hors sujet).
- Laisser le thread du pool écrire dans la scène.
- Supprimer l'étalement (règle Nico 2026-10-15 : jamais tout le jardin dans la même image).

## Fin de tronçon
`dotnet build` vert ; golden intact ; mesures avant/après (n ≥ 3) dans `00_etat.md` ;
fichiers > 300 LDC signalés (`tools/compte_ldc.py`) ; commit.
