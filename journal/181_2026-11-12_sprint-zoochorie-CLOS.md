# 2026-11-12 — Sprint ZOOCHORIE (D42) — CLOS côté code

Sprint : `sprints/faune/vie_macro/sprint_zoochorie/` (`/sprint-auto`, ①→⑧).
Conception : `docs/faune/vie_macro/conception_zoochorie.md`.
Golden `a10b7225…` → **re-figé au ⑥ seulement** (`b4a921f8…`, mulot proie du rapace
et de la couleuvre, annoncé) ; ⑦ et ⑧ inchangés.

## Tronçons
- ① grain sauvage (`GrainEnAttente` : dormance, péremption, plafond par plot).
- ② chute unifiée : fruit tombé → grains au pied ; chêne/hêtre fruitiers, glandée.
- ③ noisetier `HazelTree` + 5 voix.
- ④ merle : prise saturante, semis sous les perchoirs, geste `poser_perchoir` (pont 0.6.11).
- ⑤ geai et écureuil : caches oubliées, apport de la ceinture.
- ⑥ mulot : prédateur des grains, caches courtes ; golden re-figé `b4a921f8…`.
- ⑦ voix `dispersion`, banc `nucleation`, calibrage ; critère D130 raté → D132.
- ⑧ vue Godot : geai / écureuil / mulot (icônes, couleurs, heatmaps F6), noisetier dans
  les 8 tables d'arbre, fiches gland / faîne / noisette, perchoir en T + glyphe + geste
  dans la palette ; `nucleation` ouvre le geste (forçage de banc). `dotnet build` vert.

## Décisions et écarts
- Pas d'altitude ni de nuit inventées côté vue : la bête est placée par son habitat moteur.
- En jeu le geste perchoir ne s'ouvre jamais (`poser_tuteur` sans route, maîtrise `perchoir`
  jamais créditée) → **D133**. Reliquats §7 → **D134**. Relève du verger → **D132**.

## Reste
F5 de Nico sur le banc `nucleation` (§REPRISE du `00_etat.md`).
