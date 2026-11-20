# Backlog — rendu en gaussian splats

Programme « tout en splats » (conception `conception_precuisson_splats.md`, D7,
Nico 2026-11-20) — un sprint par famille, F5 entre chaque :

- **(a) plantes** — CONÇU le 2026-11-20 → `sprints/rendu/splatting/sprint_precuisson_splats/`
  (7 tronçons, golden intact), prêt pour `/sprint-auto sprint_precuisson_splats`.
- (b) décor de lisière (`visuals/DecorLayer.*`, même kit indexé) — à concevoir après le F5 de (a).
- (c) faune + champignons (`FauneSilhouettes`, `MacroLife`, `Carpophore*`) — à concevoir.
- (d) structures + maison (`CompostStructure`, `ContainerStructure`, `SupportRenderer`,
  `HabitatAuxiliaire`, `HouseNode`) — à concevoir.
- (e) sol, litière, eau, neige, météo (`world/Sol*`, `*Litter*`, `Mulch*`, `Puddle*`,
  `SnowLayer`, `WeatherLayer`) — à concevoir ; surface continue, méthode à inventer.
- (f) icônes de gestes et de faune en petits objets splats (D8, F5 de lisibilité d'abord).
- Horizon : vraie 3D temps réel (splats dans Godot, addon gdgs ou rendu C#), banc de
  vérité à faire sur le nouveau PC de Nico (carte 8 Go probable) — les recettes de (a)-(f)
  resservent telles quelles.
