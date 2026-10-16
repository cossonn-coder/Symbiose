# Backlog — pistes rendu pixel-art

> Section de [`BACKLOG.md`](../../../BACKLOG.md) reprise **verbatim**.

### Pistes RENDU PIXEL-ART 16-bits (Chrono Trigger) — recherche web (2026-06-23)
> Axe DISTINCT des précédents : ici la source de vérité est la couche **Godot/C#**
> (`world/WorldView*`, `visuals/PlantRenderer*`, overlays), pas `data/code/`. État
> actuel : sol = losanges placeholder en **aplats unis** (`WorldView.Monde.cs`,
> `SoilColor`), aucune transition / ramp / dithering ; `default_texture_filter=0`
> (Nearest) ✓. Aucune de ces techniques n'existe encore côté rendu de sol.
- [ ] **Dual-grid autotiling** — transitions terre↔argile↔sable avec **5 tuiles**
  (grille graphique décalée d'½ plot lisant 4 voisins logiques) au lieu des 47 du
  blob. Se branche sur le `t["soil"]` du snapshot. Déterministe, pur voisinage.
  Réf. Excalibur / redblobgames / BorisTheBrave.
- [ ] **Dithering ordonné (matrice de Bayer)** — déterministe par pixel. Double
  emploi : casser le banding des rampes ET **afficher les champs scalaires** (humidité,
  fertilité) en texture de sol lisible **sans HUD chiffré** (philo #5) — alternative
  diégétique aux heatmaps debug `FieldOverlay`. (Floyd-Steinberg = séquentiel →
  réserver à la génération d'asset hors-ligne.)
- [ ] **Palette : ramps + hue-shifting** — remplacer les aplats unis (1 couleur/sol,
  1 couleur/organe) par des rampes 3-5 valeurs, ombre décalée vers le froid plutôt
  que vers le noir. Fondation des deux pistes ci-dessus.
- [ ] **⚠️ Alerte archi : iso losange vs grille carrée SNES** — tout le corpus
  pixel-art suppose une grille carrée top-down ; Symbiose rend en **iso 2:1**
  (78×39 px/plot). Chrono Trigger est top-down 3/4 carré, pas iso pur. À TRANCHER
  avant tout dev pixel-art : assumer l'iso (tuiles diamant) ou se rapprocher du carré.
- [ ] **Cache de sprite `PlantRenderer`** (perf) — « rendre une fois sur une
  surface/texture puis blitter » si le rendu procédural redessine trop souvent.
- [ ] **États visuels du sol par paliers** (D108, à concevoir `/conception`) — le
  sol devient lisible : paliers statiques par plot (craquelé, imbibé, herbacé, nu,
  litière…) au franchissement de seuils avec hystérésis, variantes d'atlas dans le
  maillage par tuile. Prérequis : T2 du sprint RENDU VISIBLE
  (`sprints/perf/lod/sprint_rendu_visible/`).
