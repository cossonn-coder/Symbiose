## 2026-10-30 — Sprint CE QUI EST CASSÉ À L'ÉCRAN (D112) — CLOS côté code (①→⑦)

`/sprint-auto sprint_casse_ecran`. Golden `fecccded…` **jamais re-figé**, pont 0.6.1,
`dotnet build` vert. État et mesures : `sprints/rendu/pixelart/sprint_casse_ecran/00_etat.md`.

- ① charte des rampes (`RampesDa.cs`) + banc de mesure `tools/mesure_da.py` (ligne de base).
- ② défauts : maison opaque (deux plans), H sur la lisière devant, jauges Maj+F3, vent en
  tête de F6, touche U = psilocybe.
- ③ palette indexée + LUT, éclat côté soleil réel, F11 post-process débranché, ombres teintées.
- ④ paliers ×4→×32 dans la même grammaire (motifs UV-mappés, dômes, bois strié).
- ⑤ faune en icônes pixel-art indexées (atlas à la demande, 1 DrawMesh par couche).
- ⑥ lisière en dialecte forêt, animée au vent en shader, éclairée au soleil.
- ⑦ bilan : planche complète lue ; correctif `texelFetch` dans `palette_indexee.gdshader`
  (atlas faune lu au texel voisin : 2 480 px faux à ×4, contour perdu) ; banc final vs ①
  [n=1 capture par cellule] : quasi-noir faune 3/8 → 0/8, voisins identiques 10/138 → 0/136,
  éclat côté soleil ×4 7/15 → 11/14, aplats ×16 6/6 → 3/10 ; perf A/B avec le départ
  (worktree) : régime établi dans le bruit, **à-coups de zoom +20 %** [n=1 vs n=2, VM] → D112 (o).
- Reste : **F5 de Nico** (8 points, §F5) ; restes (o)→(s) en D112 ; nuit = D117.
