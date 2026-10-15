# T7 — Banc F5 des paliers + bilan contre l'objectif

> Lire `CLAUDE.md`, `00_etat.md` (mesures de T1 à T6), `docs/perf/lod/conception_rendu_visible.md`.
> Vue C# pure. Golden intact. Dernier tronçon (règle « vue Godot toujours en fin »).

## Objectif
1. **Planche des paliers** (banc F5) : une touche libre (vérifier `WorldView.Controls.cs`)
   qui, sur la plante sous le curseur (ou la plus proche du centre), fait défiler la caméra
   ×0,5 → ×32 centrée sur elle, ~3 s par palier, encart « palier ×N · information »
   (texte du tableau de la conception). Re-touche = arrêt, caméra restaurée. Option banc
   VM équivalente (`capture_vm.sh`) pour produire la planche en PNG.
2. **Bilan perf** : tableau final dans `00_etat.md` — VM (`perf_vm.sh`, ×0,5/×1/×2/×4/×8/
   ×16/×32, FPS + draw calls, n≥2) comparé à la référence de T1 ; et colonne « PC Nico »
   laissée à remplir au F5 avec la grille D1 (≥ 30 FPS ×0,5-×2 ; ≥ 60 FPS ≥ ×4).
3. **Clôture** : `DETTE.md` D106 → close (ou reste précis si D1 non atteint au F5),
   `BACKLOG.md`, `journal.md` (entrée du sprint), `docs/perf/lod/journal_lod.md`,
   `docs/perf/lod/backlog_lod.md`. Refactor auto-léger si un fichier a dépassé la bande.

## Ne pas faire
Pas de nouvelle optimisation ici : si D1 n'est pas atteint, écrire le constat chiffré et
la piste suivante en dette, ne pas la coder.

## Fin de tronçon
Commit. Message à Nico : la question F5 unique — « en dézoom c'est fluide et lisible, en
zoom c'est riche ; et F4 à ×0,5 et ×4 donne combien ? ».
