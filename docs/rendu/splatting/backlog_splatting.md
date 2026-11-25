# Backlog — rendu en gaussian splats

Programme « tout en splats » (conception `conception_precuisson_splats.md`, D7,
Nico 2026-11-20) — un sprint par famille, F5 entre chaque :

- **(a) plantes** — **CLOS côté code le 2026-11-25** → `sprints/rendu/splatting/sprint_precuisson_splats/`
  (①→⑦ + ④bis ⑤bis, golden `bce813af…` intact). Reliquats : bois non livré (couture
  visible, ③) ; reste dessiné listé au ④bis (trèfle, brins de graminées, masses de
  buisson…) ; portraits ratés au ⑥ (sapin sans cône, bouleau brun, tournesol à tête
  minuscule, thym, molène sans hampe, rossolis générique, cerisier sans fleurs ni
  fruits, myrtille sans baies, chanvre, lavande, tuteur trop présent sur haricot /
  jasmin / lierre).
  **Retour F5 partiel de Nico (2026-11-25, ④⑤ poussés)** : « les splats sont beaux,
  globalement positif ». Reliquats à reprendre :
  - **×32 : les splats disparaissent, les anciens dessins reviennent**. Piste lue au
    code (NON vérifiée par capture) : les pièces ne se posent que si la plante est
    PRÉCUITE (`SplatsIci` = `Indexe` = `IsBrush && PaletteIndexee.Active`,
    `PlantRenderer.Assemblee.cs:61`) ; or `PlantBaker.Begin` renonce à précuire dès
    qu'une pose dépasse `MaxSidePx` 2048 px ou que l'atlas des poses dépasse
    `MaxAtlasPx` 4096 px (`visuals/PlantBaker.cs`) → à ×32 la plante passe en dessin
    direct, sans splats. À confirmer par une capture ×32, puis décider : poser les
    pièces aussi en dessin direct, ou relever les plafonds ;
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
