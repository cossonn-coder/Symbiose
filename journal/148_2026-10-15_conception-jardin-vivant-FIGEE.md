# 2026-10-15 — Conception JARDIN VIVANT (sprint A) — FIGÉE

`/conception`, chantier « beauté » ouvert après le tri des dettes. Objectif fini :
un jardin **beau et jouable** pour amis/famille, style **mignon SNES** (Chrono
Trigger / FF VI). Doc : `docs/rendu/pixelart/conception_jardin_vivant.md` ;
sprint : `sprints/rendu/pixelart/sprint_jardin_vivant/` (6 tronçons, golden
`22768f33…` jamais re-figé — pure vue + un export de pont).

Décisions Nico :
- **Animation = signal d'état** (corrige « tout animé a minima ») : calme + grand
  beau = jardin quasi immobile ; fumée de cheminée seulement en hiver (sprint B).
- **Dessiner juste** : feuilles colorées par le calendrier de CHAQUE plante
  (`automne` par plante), fleur par famille/espèce, faune et champignons justes.
- **Sprites procéduraux par instance** (étiolement, symptômes propres).
- **8 poses = 8 degrés de flexion** choisis par une **onde de vent cohérente qui
  appuie** + balancement propre décalé par plante (désynchro).
- **Re-cuisson jamais simultanée** : file à budget par frame, visibles d'abord.
- Palette ~32 couleurs + tramage Bayer (SNES).
- **2 sprints** (tranché par Claude, délégué par Nico) : A = palette, plantes,
  vent, météo ; B = faune, champignons, fumée/eau (réutilise la pré-cuisson).
- T0 = banc de capture VM (Godot sous Xvfb → PNG) pour que l'agent vérifie ses
  images avant le F5 ; le F5 de Nico ne juge plus que le ressenti.
