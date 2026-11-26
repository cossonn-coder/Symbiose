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
- **Séquence « style homogène »** (conçue le 2026-11-25, `conception_reliquats_plantes.md`) —
  trois sprints sans F5 intermédiaire, F5 complet de Nico à la fin :
  - **S1 reliquats plantes** — **CLOS côté code le 2026-11-25** (①→⑥, golden intact, F5 consolidé dans son `00_etat.md`, à jouer après S3 ; restes : recette dédiée plantain, framboisier caduc au moteur, myrtille fruitière = D134) → `sprints/rendu/splatting/sprint_reliquats_plantes/`
    (×32 confirmé par capture puis corrigé sous un budget de précuisson de 1 Go, 3 classes de
    taille, tous les détails des feuilles cuits, trèfle/thym/lavande/fétuque, portraits non-arbres) ;
  - **S2 arbres** — **CLOS côté code le 2026-11-26** (①→⑥, golden `bce813af…` intact, F5 consolidé S2 dans son `00_etat.md`, à jouer après S3 ; restes : rendu ×8-×32 des aiguilles du sapin = recette « rameau aplati » à cuire, figuier en cépée = moteur) (`conception_bois_arbres.md`) → `sprints/rendu/splatting/sprint_bois_arbres/` : RENDU seul (moteur intact), tube lissé sans angles abrupts +
    écorce cuite par essence, brins/rubans des graminées (même technique), masses ×4 des
    arbres, portraits d'arbres (sapin, bouleau, cerisier, figuier), fleurs d'arbre ×4 clairsemées ;
  - **S3 = (b) + (g)** — **CLOS côté code le 2026-11-26** (①→⑤, golden `bce813af…` intact ; restes : à-coup 1ʳᵉ arrivée ×32, roche de falaise ×16-×32, ripisylve non capturée, phases du chargement à recaler au PC) (`conception_lisiere_chargement.md`) → `sprints/rendu/splatting/sprint_lisiere_chargement/` : kit de lisière en splats + rameau aplati du sapin, arbres de lisière sur le bois de S2, atlas par palier ×8-×32, écran de chargement en mycélium (carte des âges, mycorhize), liste F5 exhaustive S1-S3.
  - **SÉQUENCE CLOSE côté code le 2026-11-26.** **Prochain = F5 complet de Nico** sur la liste exhaustive S1+S2+S3 (`sprints/rendu/splatting/sprint_lisiere_chargement/00_etat.md` §« F5 EXHAUSTIF »), puis le proof of concept ×64.
  - **Premiers retours F5 de Nico (2026-11-26, pont 0.6.26, PC i5-4200H / HD 4600)** :
    - « l'écorce n'apparaît qu'à partir de ×4 » : c'est le seuil posé au ② (`EcorceReductionMax` =
      2 dans `DecorLayer.Charpente.cs`, `EcorceMinPx` côté jardin). Seules les bandes ×4 (et ×8-×32
      au ③) sont cuites ; réduites pour ×0,5-×2, elles donnaient un bouleau gris tacheté. Piste :
      cuire aussi les bandes d'écorce aux petits paliers (×0,5/×1/×2), comme le ③ l'a fait vers le haut ;
    - « les tuiles, les maisons d'auxiliaires, les événements météo, entre autres, ne sont pas encore
      en splats » : c'est le reste du programme, familles (c)-(f). Le style n'est donc pas encore
      homogène PARTOUT, alors que c'était la condition du F5 complet.
- **Après S1-S3 : proof of concept ×64** sur une plante entière (chanvre), mesure du coût (sonde
  d'une feuille au ③ de S1). Un palier ×64 suppose que sol, faune, paillage… soient eux aussi
  cuits par palier (familles c-e).
- (b) décor de lisière (`visuals/DecorLayer.*`, même kit indexé) — S3, **CLOS côté code le 2026-11-26**.
- (c) faune + champignons (`FauneSilhouettes`, `MacroLife`, `Carpophore*`) — à concevoir.
- (d) structures + maison (`CompostStructure`, `ContainerStructure`, `SupportRenderer`,
  `HabitatAuxiliaire`, `HouseNode`) — à concevoir.
- (e) sol, litière, eau, neige, météo (`world/Sol*`, `*Litter*`, `Mulch*`, `Puddle*`,
  `SnowLayer`, `WeatherLayer`) — à concevoir ; surface continue, méthode à inventer.
- (f) icônes de gestes et de faune en petits objets splats (D8, F5 de lisibilité d'abord).
- (g) **écran de chargement** (Nico 2026-11-25 : « devenu moche ») — S3, **CLOS côté code le 2026-11-26** : un **filament de
  mycélium qui s'arborise petit à petit, en splats, et sert de barre de progression** (philo #5
  = pendant le jeu seulement ; on charge planches splats, portraits, cuisson du cadre).
- Horizon : vraie 3D temps réel (splats dans Godot, addon gdgs ou rendu C#), banc de
  vérité à faire sur le nouveau PC de Nico (carte 8 Go probable) — les recettes de (a)-(f)
  resservent telles quelles.
