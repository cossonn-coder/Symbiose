## 2026-10-29 — Conception CE QUI EST CASSÉ À L'ÉCRAN (D112) — FIGÉE

`/conception D112`, accord Nico. Sprint `sprints/rendu/pixelart/sprint_casse_ecran/`
(7 tronçons, golden `fecccded…` intact partout). Doc
`docs/rendu/pixelart/conception_casse_ecran.md` ; **brief DA de Nico** gravé tel quel dans
`docs/rendu/pixelart/etude_brief_da_16bits.md` (8 règles, 3 dialectes, rampes mesurées).

- **Constats au code** : bêtes dessinées en rectangles (pas absentes) ; maison en verre =
  `PlantZIndex` qui prime sur le YSort ; heatmap vent présente quand `eco.vent` est calculé ;
  ×2 plus beau que ×4 = deux moteurs de dessin (kit estampillé ≤ ×2, segments ≥ ×4) ;
  le kit éclaire le bas des touffes et ignore le soleil ; F11 = Bayer plein écran.
- **Décisions** : périmètre = tout D112 (Nico) ; bug de vent en longue partie hors
  périmètre (Nico) ; une recette par espèce identique à tous les paliers ; masses sans
  contour, petits objets à contour teinté ; éclat côté **soleil réel** (Nico) ; **palette
  indexée** + LUT par matière (0 recuisson au soleil, F11 débranché) ; dialectes SoM
  (plante seule) / CT forêt (couverts, lisière) validés (Nico) ; nuit → D117 (Nico).
- **Tronçons** : ① charte + banc de mesure · ② défauts (b n e d h) · ③ palette indexée +
  soleil, paliers bas · ④ paliers hauts même grammaire · ⑤ faune en icônes · ⑥ lisière et
  décor animés · ⑦ bilan.
