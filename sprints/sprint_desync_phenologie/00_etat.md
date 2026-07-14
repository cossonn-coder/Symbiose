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

## §REPRISE — exécution (`/sprint-auto sprint_desync_phenologie`)
Conception CLOSE. 3 kickoffs autosuffisants écrits. Enchaîner :
1. **① `01_desync_moteur.md`** — FAIT (non commité). Golden `240f1021…`. Voir §① ci-dessus.
2. **② `02_pont_signaux.md`** — export `floraison` + `automne` par-plante (PONT).
   Golden **INTACT** (hints hors `_PLANT_ATTRS`). Réutiliser `semaine_abscission`
   (déjà factorisé dans `decompo.py` par ①).
3. **③ `03_vue_godot.md`** — fleurs ∝ `floraison`, teinte ∝ `automne`, LOD →×1
   (C#). Golden intact, `dotnet build` vert, **points F5 à consigner pour Nico**.

Statut : ① ✅ (non commité) · ② ⏳ · ③ ⏳.
