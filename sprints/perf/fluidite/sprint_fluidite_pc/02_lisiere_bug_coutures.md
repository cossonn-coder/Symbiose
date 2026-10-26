# ② Lisière : le bug « il faut F10 » + les coutures

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, `docs/perf/fluidite/conception_fluidite_pc.md`
(§2.6-7, §4). **Golden** : intact (vue C# seule).

## Objectif
Au F5, **la périphérie s'affiche mal au démarrage et Nico doit appuyer deux fois sur F10**
(banc décor ON puis OFF) pour la voir juste (D112 c). Le reproduire, en trouver la cause, la
corriger. Supprimer les **fils de couture** visibles entre triangles du décor (captures ×0,5
et ×2 du `00_etat.md`).

## Repères (lus au code le 2026-10-26, à revérifier)
- Construction : `world/WorldView.cs` crée `DecorLayer` puis `_decorLayer.Build(Seed)` ; plus
  loin `ApplySnapshot(snap, fade: false)` → `ApplyCeinture` (`WorldView.Snapshot.cs`) →
  `DecorLayer.SetCeinture` (`visuals/DecorLayer.Pont.cs`) → `Build(_seed)` si `_built`.
- F10 → `DecorLayer.ToggleBanc()` (`DecorLayer.Banc.cs`) → `Build(_seed)` → `QueueRedraw`.
- Le décor est INERTE : `_Process` ne redessine qu'aux bascules de LOD (`MaxZoom`, `DetailZoom`).

## À faire
1. **Reproduire** en capture VM (`tools/capture_vm.sh -b full -z 0.5 …`, graine 1521550718 et
   42) : image au démarrage contre image après une reconstruction forcée équivalente à F10 ×2
   (ajouter un argument de capture qui la déclenche après N images si besoin). Comparer.
   Regarder aussi après une semaine appliquée (chemin étalé `ApplySnapshotEtale`) et après une
   rotation D35.
2. **Pistes** (non vérifiées) : (a) la projection (`WorldToScreen`) dépend d'un état posé APRÈS
   le premier `_Draw` (relief/altitude, caméra, origine) et le décor inerte ne se redessine pas ;
   (b) un chemin de snapshot sans bloc `ceinture` → `SetCeinture(null)` → repli `BuildProfile`
   (faux motifs) ; (c) l'ordre `Build` / `SetCeinture` / `_built`. Nommer la cause **observée**.
3. **Corriger** la cause (redessin sur le bon signal, pas un redessin à chaque image).
4. **Coutures** : les fils fins entre triangles du lot (`LotTriangles`) — sommets non partagés,
   bords d'aplats adjacents, anticrénelage. Les faire disparaître sans multiplier les draw calls.
5. Si la cause n'est PAS reproductible sur VM : poser au démarrage une ligne console
   `[DecorLayer]` (source du profil : banc / pont / repli, motifs des 4 côtés) et le dire dans
   les points F5 de `00_etat.md`.

## Ne PAS faire
- Refaire le style (③/④). Toucher `fields/peripherie.py` ou le pont.

## Fin de tronçon
`dotnet build` vert ; captures avant/après dans `00_etat.md` (chemins + ce qu'on y voit) ;
golden intact ; LDC ≤ 300 par fichier touché ; commit.
