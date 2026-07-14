# 2026-07-14 — Sprint DÉSYNCHRONISATION PHÉNOLOGIQUE — CLOS (`/sprint-auto`)

Exécution autonome des 3 tronçons figés (`sprints/sprint_desync_phenologie/`,
conception FIGÉE 2026-07-14, doc `docs/conception/CONCEPTION_DESYNC_PHENOLOGIE.md`).
Problème : floraison / abscission / sénescence semblaient **synchrones** (tout le
jardin bascule au passage de saison) + feuilles et segments masqués sous ×4/×8.
Cause double : trois horloges moteur **globales ou placeholder** et une **VUE qui
re-synchronise** (couleur feuille + fleurs season-gated côté C#). Correctif :
un **gène-tempo partagé** (`phenologie_florale`, `g>1` = précoce partout,
héritable, déterministe sans RNG — philo #3) + débranchement de la vue de la
saison globale + détail au segment/organe dès ×1.

## Tronçons livrés (①→③)

- **① SIM désync** (`35d80d8`) — les 3 horloges pilotées par `(g−1)` du gène
  `phenologie_florale` : floraison `FLORA_GENE_SHIFT 40→200` ; abscission
  par-individu via helper factorisé `semaine_abscission(plant)` (fenêtre [34,39],
  dépôt unique annuel) remplaçant `ABSCISSION_WEEKS` global ; onset de sénescence
  par-individu `clamp(0.70−0.5·(g−1), 0.05, 0.95)` + **miroir exact** dans
  `sim/semiologie.py`. Test neuf `tests/test_desync_phenologie.py` (7/7 : σ>0 sur
  les 3 horloges au niveau formule, robuste au climat + neutralité g=1). **Golden
  RE-FIGÉ LARGE MAÎTRISÉ ANNONCÉ** `da2729c5…` → **`240f10219e…`** : le seul caduc
  du smoke (Pommier, g≈1.199, précoce) largue à sa semaine propre (w36 au lieu de
  38-39) + hachage litière/eco/vitalité ; dérive cohérente, plante g=1.0 inchangée
  (`test_senescence` onset 49 intact). `ABSCISSION_WEEKS` devenu inutilisé dans
  `boucle.py` (retiré de l'import, conservé dans l'API publique des constantes).
- **② PONT** (`0d0ea46`) — deux hints **pur-rendu** par-plante dans
  `tools/simserver/serialize.py` (hors `_PLANT_ATTRS`) : `base["floraison"]` =
  `round(p.floraison,3)` (scalaire moteur porté au pont) et `base["automne"]` =
  rampe [0,1] montante sur `AUTOMNE_RAMP=6` sem avant la semaine d'abscission
  propre du caduc (réutilise `semaine_abscission` de ①, **zéro duplication** ;
  persistants → 0.0). `foliage_density_at` **non touché** (sert `fields/light.py`).
  **Golden INTACT** `240f10219e…` (hints hors du digest).
- **③ VUE Godot** (`bff7d3a`) — vue C# débranchée de la saison globale :
  `core/PlantStructure.cs` lit `Floraison`/`Automne` du snapshot (défaut 0,
  tolérant) ; fleurs portées par `Floraison ≥ 0.5` (remplace le proxy season-gated
  `Organ=="flower"`) ; `LeafColor` = mélange continu `Leaf.Lerp(autumn, Automne)`
  par-plante (remplace le `switch(season)` global → plus de flip du jardin au
  passage de saison ; pioche automnale toujours au hash par-feuille) ; LOD
  `SegmentDetailMinZoom 4→1`, `OrganDetailMinZoom 8→1` (détail feuilles+segments
  dès ×1, silhouette gardée à ×0.5 seul). Helper orphelin `Scaled` retiré ;
  `CurrentSeason` débranché du rendu mais conservé (aucun autre consommateur
  cassé). **Golden INTACT** `240f10219e…`, `dotnet build` **vert** (0/0).

## Bilan

**Golden final `240f10219e59119ee0f7a4af8d41f4cfe29b280dec4d32b76013ae6f43a80d87`**
(1 seul re-figeage maîtrisé, au ①, comme annoncé). Refactor auto-léger : **no-op**
— aucun fichier touché en zone rouge (max = `PlantRenderer.Organs.cs` 307 LDC pur,
déjà en zone jaune tolérée avant le sprint).

**Interconnexions** (règle projet) : abscission et sénescence héritables via le
gène-tempo (darwinien) ; les clones (bouture/ramets) restent synchrones (gènes
copiés) = feature voulue ; le signe de sénescence se désync tout seul dès ① (miroir
sémiologie), la vue ne fait plus que refléter le moteur par-plante.

**Reste F5 Nico** : détail (feuilles+segments) lisible dès ×1 sur aire large /
plantes minuscules (sinon remonter un cran le seuil) ; FPS tenu à ×1 sur scène
chargée (culling = filet déjà présent) ; désync visible (fleurs à semaines
différentes selon les pieds, feuillage qui rougit/tombe étalé) ; **plus de flip de
tout le jardin** au passage de saison.
