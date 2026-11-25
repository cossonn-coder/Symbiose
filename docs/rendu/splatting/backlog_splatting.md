# Backlog — rendu en gaussian splats

Programme « tout en splats » (conception `conception_precuisson_splats.md`, D7,
Nico 2026-11-20) — un sprint par famille, F5 entre chaque :

- **(a) plantes** — CONÇU le 2026-11-20 → `sprints/rendu/splatting/sprint_precuisson_splats/`
  (7 tronçons, golden intact), prêt pour `/sprint-auto sprint_precuisson_splats`.
  **Retour F5 partiel de Nico (2026-11-25, ④⑤ poussés)** : « les splats sont beaux,
  globalement positif ». Reliquats à reprendre :
  - **×32 : les splats disparaissent, les anciens dessins reviennent** (cause non
    cherchée — le ④ couvrait ×4→×32 ; à diagnostiquer au code + capture VM) ;
  - **trèfle** : fleurs en splats, mais feuilles toujours dessinées grossièrement sur
    une tache verte (connu : reliquat ④bis n°1, pas de recette 3-4 folioles à 3 cm).
    Les autres reliquats dessinés du ④bis (brins de graminées, masses de buisson,
    bois…) sont du même ordre.
  - **F5 complet DIFFÉRÉ** : Nico fera un rapport d'observation complet quand le
    style splat sera homogène partout ; Claude lui fournira alors la liste exhaustive
    de ce qu'il faut vérifier.
- (b) décor de lisière (`visuals/DecorLayer.*`, même kit indexé) — à concevoir après le F5 de (a).
- (c) faune + champignons (`FauneSilhouettes`, `MacroLife`, `Carpophore*`) — à concevoir.
- (d) structures + maison (`CompostStructure`, `ContainerStructure`, `SupportRenderer`,
  `HabitatAuxiliaire`, `HouseNode`) — à concevoir.
- (e) sol, litière, eau, neige, météo (`world/Sol*`, `*Litter*`, `Mulch*`, `Puddle*`,
  `SnowLayer`, `WeatherLayer`) — à concevoir ; surface continue, méthode à inventer.
- (f) icônes de gestes et de faune en petits objets splats (D8, F5 de lisibilité d'abord).
- (g) **écran de chargement** (Nico 2026-11-25 : « devenu moche ») : un logo qui
  représente la symbiose, en gaussian splats, + une **barre de chargement** (on charge
  maintenant des assets : planches splats, portraits). À concevoir avec le reste du
  style homogène.
- Horizon : vraie 3D temps réel (splats dans Godot, addon gdgs ou rendu C#), banc de
  vérité à faire sur le nouveau PC de Nico (carte 8 Go probable) — les recettes de (a)-(f)
  resservent telles quelles.
