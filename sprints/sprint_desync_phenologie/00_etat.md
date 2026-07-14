# Sprint DÉSYNCHRONISATION PHÉNOLOGIQUE (+ rendu feuilles/segments dès ×1)

> **Phase : CONCEPTION FIGÉE — prêt pour `/sprint-auto`.** Doc + 3 kickoffs
> (`01`/`02`/`03`) écrits. Aucun tronçon implémenté. Reprise à froid = lire
> `CLAUDE.md` + ce fichier + `docs/conception/CONCEPTION_DESYNC_PHENOLOGIE.md`.

## Sujet (Nico, 2026-07-14)
1. **Rendu** : feuilles ET segments dès le zoom ×1 (aujourd'hui masqués < ×4/×8).
2. **Culling** : ne rendre que l'écran + proche → **DÉJÀ FAIT** (`CullPlants`).
3. **Sim** : désynchroniser floraison / fanaison / sénescence (investiguer pourquoi synchrone).
4. **Ajout Nico** : vérifier que le passage de saison n'est pas un déclencheur
   d'affichage → **C'EST LE CAS** (couleur feuille + fleurs season-gated côté vue).

## Arbitrages tranchés (Q1-Q3, tous = reco)
- Q1 périmètre = **les trois horloges** (floraison + abscission + onset sénescence).
- Q2 mécanisme = **un gène tempo partagé** (réutiliser `phenologie_florale`,
  `g>1` = précoce partout ; héritable, darwinien, philo #3 sans RNG).
- Q3 rendu = **détail complet dès ×1** + culling filet + vérif F5.

## Diagnostic (FAIT — détail dans le doc §1/§1bis)
- **Floraison** : gène `phenologie_florale` existe mais `FLORA_GENE_SHIFT=40`
  (placeholder) → étalement ±0.3 sem, imperceptible. Recalibrer.
- **Abscission** : `ABSCISSION_WEEKS=(38,39)` GLOBAL (`decompo.py::_abscission`,
  garde `boucle.py:472`). Zéro variance.
- **Sénescence** : onset `SENESCENCE_ONSET=0.70×L` FIXE (`mortalite.py`), miroir
  dans `semiologie.py::senescence`. Mort déjà dispersée par hash, mais onset synchrone.
- **VUE re-synchronise** : `PlantRenderer.Organs.cs:261` couleur feuille sur
  `WorldView.CurrentSeason` (global) ; fleurs `Organs.cs:298` sur proxy
  `base["organ"]=repro.get(saison)` (`serialize.py:182`) — le scalaire moteur
  `floraison` N'EST PAS exporté. MAIS `leaf_symptoms` (dont sénescence,
  `serialize.py:170`) EST par-plante → le signe de sénescence se désync tout seul
  dès ① (miroir sémio). Reste à débrancher : **fleurs** + **teinte automnale**.

## Découpage FIGÉ (3 tronçons, vue en dernier)
- **① SIM désync** — kickoff `01_desync_moteur.md` **ÉCRIT**. Golden re-figé LARGE.
  Modèle (doc §2) : `FLORA_GENE_SHIFT 40→200` ; abscission par-plante
  `w=round(38−15·(g−1))` bornée [34,39], dépôt unique annuel ; onset
  `clamp(0.70−0.5·(g−1),0.05,0.95)` + MIROIR semiologie. Test d'étalement (spread>0).
- **② PONT** — kickoff `02_pont_signaux.md` **À ÉCRIRE**. Python
  `tools/simserver/serialize.py` (+ helper phénophase) : exporter
  `base["floraison"]=round(p.floraison,3)` et `base["automne"]` = ramp [0,1] vers
  la semaine d'abscission propre (même formule `w` que ①, tempo gène). **Golden
  INTACT** (hints ; NE PAS toucher `foliage_density_at` — sert `fields/light.py`).
- **③ VUE** — kickoff `03_vue_godot.md` **À ÉCRIRE**. C# `PlantRenderer.Organs.cs`
  (+ lecture snapshot dans `PlantStructure`) : fleurs dessinées ∝ `floraison`
  (remplace `_structure.Organ=="flower"` season-proxy) ; `LeafColor` mélange
  été→automne ∝ `automne` par-plante + fondu densité en fin (remplace le switch
  `season` global) ; `SegmentDetailMinZoom 4→1`, `OrganDetailMinZoom 8→1`
  (`PlantRenderer.cs:44,54`), silhouette gardée à ×0.5 seul. **Golden intact.**
  Vérif F5 : détail ×1 + perf (culling) + désync visible + pas de flip saison.

## Décisions clés
- Ne PAS renommer `phenologie_florale` (golden/churn) — sémantique élargie « tempo ».
- Ne PAS toucher la porte photopériode ni `foliage_density_at` (sim/light).
- Clones (bouture/ramets) restent synchrones (gènes copiés) = correct, feature.
- Zoom paliers `{0.5,1,2,4,8,16,32}` (`WorldView.Camera.cs:22`).

## Coût perf
- Sim/pont : ~nul. Rendu ×1 : à mesurer F5, culling = filet déjà présent.

## ① FAIT (non commité) — désync moteur des 3 horloges
- **Floraison** : `FLORA_GENE_SHIFT 40→200` (`sim/engine/floraison.py`).
- **Abscission** : semaine par-individu `semaine_abscission(plant)` (helper factorisé
  dans `sim/engine/decompo.py`, réutilisable par ② pour la rampe `automne`) ;
  constantes `ABSCISSION_BASE/JITTER/MIN/MAX` (`fields/ecofields/constants.py`) ;
  garde `boucle.py` = fenêtre complète [34,39] + passe `week_in_year` ; dépôt UNIQUE
  annuel. `ABSCISSION_WEEKS` conservé (import public), retiré de `boucle.py`.
- **Sénescence** : onset par-individu `clamp(0.70−0.5·(g−1),0.05,0.95)` dans
  `mortalite.py` + **MIROIR EXACT** dans `sim/semiologie.py::senescence` ; constante
  `SEN_ONSET_JITTER=0.5`. Neutre à g=1.0 (redonne les valeurs de base).
- **Golden RE-FIGÉ** (attendu/annoncé) : `da2729c5…` → **`240f10219e59119ee0f7a4af8d41f4cfe29b280dec4d32b76013ae6f43a80d87`**.
  Raison : le seul caduc du smoke (Pommier, gène 1.199 = précoce) largue désormais
  à sa semaine propre (w36 au lieu du RDV global 38-39, dépôt unique) + digest haché
  (litière/eco/vitalité). Dérive cohérente : plante g=1.0 (test_senescence, onset 49)
  INCHANGÉE.
- **Test d'étalement** : `tests/test_desync_phenologie.py` (7/7) — σ>0 sur les 3
  horloges (seuil floraison σ=20 GDD, abscission σ=1.2 sem, onset σ=0.05) +
  neutralité g=1. Régressions vérifiées : signes/fruits/senescence/evenements/
  evergreen/lifecycle/diversite/plasticite/biennial tous OK. `main.py` tourne (long).
- **Reste F5 Nico** : rien pour ① (moteur pur, pas de C#). Effet visible = tronçons ②③.

## ② FAIT (non commité) — pont : signaux phénologiques par-plante
- **Export `floraison`** : `base["floraison"] = round(p.floraison, 3)` (scalaire moteur
  déjà porté par l'instance) dans le bloc par-plante de `tools/simserver/serialize.py`,
  après `base["organ_site"]`. Hint PUR RENDU (③ dessinera les fleurs ∝ ce scalaire).
- **Export `automne`** : phénophase de coloration ∈ [0,1] par-plante = rampe montante
  sur `AUTOMNE_RAMP` (=6) semaines avant la semaine d'abscission PROPRE du caduc. Ne
  concerne QUE les caducs (`cls.deciduous`) ; persistants → 0.0. **Réutilise
  `semaine_abscission(plant)`** (helper ①, importé de `sim.engine.decompo`) — ZÉRO
  duplication de formule. Signature réelle du helper = `(plant)`, pas `(g)` comme
  esquissé dans le kickoff §A/§C (je me suis aligné sur le code livré par ①).
- **Constante** `AUTOMNE_RAMP = 6` posée dans `fields/ecofields/constants.py` près des
  `ABSCISSION_*`, importée dans `serialize.py`.
- `foliage_density_at` **NON touché** (sert `fields/light.py`).
- **Golden INCHANGÉ** : `240f10219e59119ee0f7a4af8d41f4cfe29b280dec4d32b76013ae6f43a80d87`
  (hints hors `_PLANT_ATTRS`, snapshot non figé). ② golden-NEUTRE par construction.
- **Vérif snapshot vivant** (banc démo, automne) : `floraison ∈ [0,1]` par pied
  (Phacelia 0.087, Clover 0.144…) ; `automne` = 0 en été/persistants, rampe réelle
  intermédiaire (AppleTree caduc précoce : 0.5 @w32 → 1.0 @w37, clampé). Déterministe.
- **Reste F5 Nico** : rien pour ② (Python pur, pas de C#). Effet visible = tronçon ③.

## ③ FAIT (non commité) — vue Godot : fleurs & teinte automnale par-plante + détail dès ×1
- **DTO** : deux champs `Floraison`/`Automne` (float, [0,1]) ajoutés à `PlantStructure`
  + lecture TOLÉRANTE (`ContainsKey`, défaut 0f) dans `FromSnapshot`
  (`core/PlantStructure.cs`). Snapshot pré-② → 0f = été neutre, aucune fleur.
- **Fleurs** : porte `_structure.Organ == "flower"` (proxy season-gated global)
  REMPLACÉE par `_structure.Floraison >= FloraisonSeuil` (=0.5, nouvelle constante).
  Chaque pied fleurit à SA semaine propre (gène tempo). Silhouette famille inchangée.
  Un seul chemin : le proxy `Organ` n'est plus consulté pour les fleurs (② prérequis).
- **Teinte automnale** : `LeafColor` — le `switch (season)` global (flip printemps/
  été/automne/hiver) REMPLACÉ par un mélange CONTINU `pal.Leaf.Lerp(autumn, automne)`
  piloté par `_structure.Automne` par-plante ; teinte automnale toujours piochée au
  HASH par-feuille dans `AutumnLeaves` (variété inter-limbes conservée). `automne=0`
  → été plein (identité). Printemps clair (×1.25) & hiver foncé (×0.7) ABANDONNÉS
  côté vue (c'étaient les flips globaux, cause du bug ; l'hiver caduc = densité 0,
  géré par `FoliageDensity`, indépendant). `SymptomTint`/repli T3 intacts (composés
  APRÈS la teinte de base, ordre préservé). `DrawOrgans` lit `float automne` au lieu
  de `string season`. Helper `Scaled` (orphelin de mon changement) retiré.
- **LOD** : `SegmentDetailMinZoom 4→1`, `OrganDetailMinZoom 8→1`
  (`visuals/PlantRenderer.cs`). Détail complet (segments + organes) dès ×1 ; seul
  ×0.5 garde la silhouette de couronne. `MacroLife.MinZoom` et `CullPlants` NON touchés.
- **Fichiers touchés** : `core/PlantStructure.cs`, `visuals/PlantRenderer.Organs.cs`,
  `visuals/PlantRenderer.cs`. 100 % C# — moteur Python NON touché.
- **`dotnet build Symbiose.csproj`** : **VERT** (0 avertissement, 0 erreur).
- **Golden INCHANGÉ** : `240f10219e59119ee0f7a4af8d41f4cfe29b280dec4d32b76013ae6f43a80d87`
  (③ = C# pur, ne touche pas le moteur).
- **Reste F5 Nico** (à valider, NON auto-validé) : (1) détail lisible dès ×1 sur aire
  large × plantes minuscules — sinon remonter un seuil d'un cran ; (2) FPS tenu à ×1
  sur scène chargée (culling = filet) ; (3) désync VISIBLE = fleurs qui sortent à des
  semaines différentes selon les pieds, feuillage qui rougit/tombe étalé ; (4) PLUS de
  flip de tout le jardin au tick du passage de saison.

## §REPRISE — exécution (`/sprint-auto sprint_desync_phenologie`)
Sprint **TERMINÉ côté implémentation** (①②③ tous FAITS, non commités). Enchaîner :
1. **① `01_desync_moteur.md`** — FAIT (non commité). Golden re-figé `240f1021…`. Voir §①.
2. **② `02_pont_signaux.md`** — FAIT (non commité). Export `floraison` + `automne`
   par-plante. Golden **INCHANGÉ** `240f1021…`. Voir §②.
3. **③ `03_vue_godot.md`** — FAIT (non commité). Fleurs ∝ `floraison`, teinte ∝
   `automne`, LOD →×1 (C#). Golden intact `240f1021…`, `dotnet build` VERT. Voir §③.

Statut : ① ✅ (non commité) · ② ✅ (non commité) · ③ ✅ (non commité).
**Reste : commit (Nico) + vérif F5 (points §③).**
