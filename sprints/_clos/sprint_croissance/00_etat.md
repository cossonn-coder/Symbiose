# Sprint Croissance procédurale (D29 réorienté) — état partagé

> État léger partagé entre tronçons (≤ ~25 lignes utiles). Mis à jour en fin de
> chaque sous-sprint. Conception figée : `data/code/CONCEPTION_CROISSANCE.md`.

## Ce qu'on construit
Remplacer l'affichage par sprites figés par une **vraie morphogénèse** : chaque
plante possède une **structure de segments** (branches), en **Python** (source de
vérité, déterministe), dont la croissance est pilotée par l'**auxine le long de la
structure** + la **lumière** (`LightField`). L'empreinte (`height_at`/`canopy_radius_at`
…) sera **dérivée de la structure** (contrat inchangé, seule la source change). Rendu
**tout procédural** (branches + organes en pixels) côté Godot. **Profil de croissance
PAR ESPÈCE** (vitesse + `port_archetype`) à décrire pour les 14 espèces. Absorbe D29
hormones (le modèle « 2 scalaires » est mort ; `tailler` devient un appelant du seam).

## Stratégie golden (re-figeage MAÎTRISÉ, pas « intact »)
Le moteur permanent change le comportement de **toutes** les plantes → le golden
**sera re-figé**, mais **localisé et incrémental** : la structure est **construite
inerte d'abord** (tronçon 1, golden INTACT car non lue), **puis câblée à l'empreinte**
(tronçon 2, **re-figeage**), **espèce par espèce** (démonstratrice d'abord). On valide
(visuel + numérique vs gabarit `growth_stages`/`age_curve`) **avant** de figer.

## Découpage (sprint GROS → 6 tronçons ; révisable par Nico)
- **1 — Structure + croissance Python (cœur), INERTE.** ✅ `Segment` (base+dir+length
  +`has_bud`) sur `PlantInstance` (1 apex au collet) ; `sim/growth.py` (auxine le long
  de la structure, allongement/émission, débourrement, **bornage** : retrait d'apex à
  `MAX_REACH`, senescence du bois sans apex, plafond `MAX_SEGMENTS` dur, **rejet de
  souche** → run éternel), appelé par l'engine après la physiologie. Déterministe
  (`_hash_noise`, zéro RNG). `tests/test_croissance.py` **19/19**. **Golden INTACT**
  (structure non lue). Phototropisme **stubé neutre** (apex droit, jitter latéral) →
  tronçon 2. ⚠️ Golden **réduit à 10 ans** (2026-06-05, la croissance alourdit le tick ;
  sénescence pommier ~70 ans **non exercée pour l'instant**) → re-capturé **`6369c30b…`**
  (≠ ancien `c950f06c…`). Le hash `c950f06c…` cité dans `01_*.md` est donc périmé.
- **2 — Profil par espèce + dérivation d'empreinte.** ✅ Schéma §E posé sur
  `PlantBase` (attributs de classe, défauts = ex-constantes de module → espèces non
  migrées inchangées) ; `grow_plant` lit le profil depuis `plant.plant_class`.
  **Tomate migrée** (`procedural_growth=True`) : `height_at`/`canopy_radius_at`/
  `root_radius_at` lisent un **cache `inst.footprint`** recalculé en fin de
  `grow_plant` (repli à la volée si None). `foliage_density_at` garde l'ancien chemin
  (feuilles = tronçon 5). Racines = `PROC_ROOT_RATIO·canopy` (k=1.0). `test_croissance`
  **33/33** (5 structure tronçon 1 intacts + allure tomate + témoin Basil).
  **Golden NON re-figé** : il reste **`6369c30b…`** (engine) / **`b005d9ba…`** (pop),
  inchangés — LÉGITIME, pas une fuite (cf. ⚠️ ci-dessous). Suite complète verte
  (genetique 20, maitrise 35+20, signes 8, vigueur 103, main.py OK).
  > ⚠️ **2 imprécisions du kickoff `02_*.md` corrigées** : (a) il citait les stades
  > de Bourse-à-pasteur (~40 cm) comme ceux de la tomate → recalibré sur la VRAIE
  > tomate **~150 cm** (choix Nico, §E.3). (b) Il prédisait un **re-figeage** ; en
  > fait la tomate **meurt à w2-3 dans le scénario golden** (froid de démarrage
  > t≈4.4 °C < seuil 5 °C + mildiou familial Solanaceae -1 santé/sem → morte avant
  > de pousser ; **comportement préexistant**, identique au tronçon 1). À ses tailles
  > (≤35 cm → 1 seul plot) l'empreinte procédurale ne perturbe **rien** → golden
  > intact. La vraie couverture du procédural = le **test d'allure** (montée monotone
  > 3→150, couronne 18→49), pas le golden. (c) `apical_dominance_base` dut passer à
  > **2.2** (>1) car `AUXIN_DECAY`/seuil (modules, fixes) ne permettent pas de tenir
  > une flèche de ~19 segments sous 1.0 → attribut redéfini en « force » (1.0=nominal).
- **3 — Seam `atteindre_segment` + `tailler`.** ✅ Seam continu (§F) posé dans
  `sim/growth.py` (doux = baisse d'auxine ; net ≥ `COUPE_NETTE` = écimage du sous-arbre,
  collet protégé ; pur structurel, zéro RNG/Vigueur). `tailler` branchée dans
  `sim/actions.py` (binaire calqué sur `deraciner` : coût `MODERE` via `cout_action`,
  gain ∝ maturité × `GAIN_TAILLE_RATIO`, appelle le seam → débourrement ÉMERGENT au
  tick suivant). **Golden INTACT** (`6369c30b…` engine, pop & vigueur_hash inchangés —
  `tailler` jamais appelée par le scénario). `test_croissance` **43/43** (+4 seam :
  écimage→débourrement, doux, collet protégé, déterminisme), `test_vigueur` **110/110**
  (+7 : contrat coût/binaire/gain/objets de `tailler`). **Absorbe D29 hormones**
  (modèle scalaire `dominance_apicale`/`reponse_taille` définitivement jeté).
  Points tranchés : `COUPE_NETTE=0.8`, `GAIN_TAILLE_RATIO=0.3`, `_segment_cible`
  (apex = cime z max ; branche = apex latéral le plus profond, repli meneur ; collet→None).
  > **Périmètre réduit vs kickoff initial** : la démonstratrice **pommier** (`etale`,
  > fructification latérale) est sortie → **tronçon 3bis** dédié (re-figerait le golden,
  > exige l'override `PerennialWoody` + calibrage `age_curve`). Ici on démontre sur la
  > **tomate** (déjà procédurale), golden intact.
- **3bis — Migration procédurale du pommier.** ✅ 1re LIGNEUSE migrée
  (`procedural_growth=True`). **Override `PerennialWoody` résolu** : `height_at`/
  `canopy_radius_at`/`root_radius_at` délèguent à `super()` (voie procédurale §G)
  quand le flag est levé ; arbres non migrés (Fig/Cherry/Walnut/Oak) inchangés à
  l'`age_curve`. **Plafonds par espèce promus** sur `PlantBase` : `emit_length_cm`
  (défaut 8) + `max_segments` (défaut 40) = ex-constantes module → espèces non
  migrées identiques. `grow_plant` les passe à `_elongate_emit`/`_elaguer`.
  **Profil pommier calibré** (sonde 520 ticks, growth_factor=1.0, cycle réel) :
  `growth_speed=0.83`, `apical_dominance_base=2.0`, `branch_angle=70`,
  `emit_length_cm=50`, `max_segments=70`, `wood_persistence=4000`,
  `foliage_halfwidth=50`, `max_height_cm=700`, `max_extent_cm=350`,
  `organ_site="lateral"`, `port_archetype="etale"` → an 10 isolé **h≈351 / cr≈197**
  (cible 350/200), montée monotone, bornée (≤55 seg < 70). ⚠️ **Survie** : à
  `foliage_halfwidth=30` la jeune flèche (couronne=fhw, racines=k·couronne, k=1)
  tient dans 1 plot → `_apply_uptake` concentre le prélèvement sur le plot-foyer →
  `drought_memory>0.6` → **mort par stress hydrique vers l'an 3**. `fhw=50` élargit
  les racines (plusieurs plots) → prélèvement dilué → pommier **vivant sain les 10
  ans** (santé 3). Levier existant, pas de `PROC_ROOT_RATIO` par espèce.
  **Golden re-figé `5a5f1cee…`** (ex `6369c30b…`) : dérive **localisée** (diff par
  tuile = SEUL le Pommier (0,7) change, T1/T2 byte-identiques ; `drought_memory`
  0.21→0.34, sous le seuil). `population` (`b005d9ba…`) & `vigueur_hash`
  (`e63b9d7f…`) **intacts**. `test_croissance` **57/57** (+14 : allure pommier,
  déterminisme, témoin ligneux Fig non migré).
- **4 — Rendu pixel structure (Godot).** ✅ **Pont JSON read-only** :
  `tools/export_structure.py` (mêmes spécimens/SEED que `render_structure.py`) dump
  `tools/structure.json` déterministe (Tomate 40 seg, Pommier an3/7/10 — an10
  h≈351/cr≈197). **Golden INTACT** (`5a5f1cee…`) : l'exporteur ne LIT que
  `grow_plant`/empreinte. Côté C# (namespace `Symbiose`) : `core/PlantStructure.cs`
  = miroir `record struct Segment` (Base/Dir/Length/Thickness/IsApex) + DTO
  `PlantStructure` + chargeur `Json.ParseString` lisant `res://data/code/tools/
  structure.json` (source unique, pas de copie). `visuals/PlantRenderer.cs` =
  `Node2D._Draw` : `Iso()` = portage EXACT de `_iso` (cos30/sin30/`PxPerCm`=0.42
  `[Export]`), `DrawLine(antialiased:false)` trié épaisseur ↓, apex vert/bois brun,
  largeur arrondie au pixel ; LOD §H.3 = silhouette de couronne si `ZoomPalier≤4`
  (stub `[Export]`=16, caméra non câblée). `TileGrid` spawne 4 plantes de démo
  (`[Export] ShowPlantDemo`). **Pas d'organes** (tronçon 5). ⚠️ Compilation C# **non
  vérifiée** (pas de `dotnet` CLI ici) → à confirmer dans Godot par Nico ; rendu
  visuel à valider à l'œil (les 4 spécimens au-dessus de la grille).
- **5 — Organes procéduraux — RISQUE N°1.** ✅ **Prototype PYTHON SVG fait**
  (2026-06-07, choix Nico : Python d'abord, port Godot différé D24). Générateur
  d'organes dans `tools/render_structure.py` (`_draw_organs` + helpers), **pur RENDU
  read-only, golden + suite INTACTS** (hash `16a1b937…` inchangé), **déterministe**
  (zéro RNG, tout via `_hash_noise`). Structuré « specs 3D → projection iso » pour
  portage Godot futur. **Feuilles** le long des rameaux feuillés (`_is_leafy` :
  apex ou bois fin ≤1.6 cm ; tronc nu), **couleur saisonnière** (printemps clair /
  été plein / automne jaune-rouge tiré au hash / hiver persistant foncé ;
  `foliage_density_at` gère deciduous+hiver→0). **Fleurs/fruits** selon
  `organ_site` (`terminal`=bouts d'apex / `lateral`=rameaux hors meneur) ×
  `REPRO_BY_SEASON` (Tomato : fleur→tomate rouge ; AppleTree : fleur→pomme verte→
  pomme mûre), plafonnés (`MAX_FRUITS`=10). Palette par espèce (`ORGAN_PALETTE`).
  Câblé dans la **maquette maison** (`_panel_sector`, saison réelle) ET l'**aperçu**
  (`_panel`, été). **Couvre les 2 espèces procédurales** (Tomato, AppleTree — seules
  migrées `procedural_growth`). Organes **non exportés** dans `maquette_secteurs.json`
  (reconstructibles §J). ⚠️ Maquette : la tomate (non caduque) garde son feuillage
  l'hiver (grow_plant seul ne la tue pas) — artefact de maquette, pas un bug moteur.
  **Itérable** : forme des feuilles (ellipses), densité, palettes = leviers
  d'ajustement esthétique à l'œil. → outil seul.
- **6 — Save de la structure.** ✅ FAIT (2026-06-07). **Contrat de sérialisation
  borné** (le système de save GLOBAL n'existe pas encore → on livre la sérialisation
  round-trip de la structure, prête pour le futur save ; choix Nico). `plants/base.py` :
  `Segment.to_dict()`/`from_dict()` (9 champs structurels ; `base`/`dir` listes JSON →
  tuples au chargement) + `PlantInstance.structure_to_dict()`/`restore_structure()`
  (liste de segments ; invalide le cache d'empreinte → recalculé à la reprise).
  **Allègement §J satisfait par CONSTRUCTION** : les organes (feuilles/fleurs/fruits)
  sont régénérés par le rendu (tronçon 5), JAMAIS stockés → seul le bois est
  sérialisé. **Pures additions** (méthodes neuves) → **golden INTACT** (`16a1b937…`).
  `test_croissance` **67/67** (+10 sérial : round-trip fidèle, base/dir en tuples,
  organes exclus, **structure restaurée pousse à l'identique** sur 40 ticks, empreinte
  dérivée identique à la reprise). **Sprint croissance CLOS côté Python.**
  ⏭ Reste hors sprint : système de save GLOBAL (transversal : structure + sol +
  populations + génétique + vigueur + maîtrise + seed d'origine + `engine_version`)
  → sprint dédié futur ; portage C# (D24).

## Plus tard (hors chantier, ligne BACKLOG)
Déclencheurs naturels du seam (grêle/chenille/vent → `atteindre_segment`) ; marqueur
`🌿` (succès maîtrise §9.5) ; profil de croissance du **reste du catalogue** (§E.4) ;
portage C# (D24) ; structure racinaire réelle (gated, §8 = rayon dérivé).

## Décisions déjà actées (conception — `CONCEPTION_CROISSANCE.md` §B)
Segments / Python source de vérité / accumulation **bornée** / auxine le long des
segments / phototropisme `LightField` / empreinte **dérivée** (contrat inchangé) /
organes **tout procéduraux** / racines **rayon dérivé**. Intensité **continue**,
moteur **permanent**, déclencheurs naturels **plus tard**.

## Points ouverts (à trancher dans le tronçon concerné, défaut sobre + signaler)
- **1** ✅ tranché : `Segment` = **base+dir+length** (extrémité dérivée) + `has_bud`
  (bourgeon axillaire, §D.3) ; boucle = **module dédié `sim/growth.py`** appelé par
  l'engine (§9c, après `_update_physiology`). Bornage : portée `MAX_REACH_CM` +
  senescence + plafond dur + rejet de souche (leviers de module, calibrage = tronçon 2).
- **2** ✅ tranché : cache d'empreinte = **dict `inst.footprint` recalculé 1×/tick**
  en fin de `grow_plant` (défaut sobre ; repli à la volée si None), **pas**
  d'invalidation paresseuse. Bascule par espèce = **flag `procedural_growth`**.
  `canopy_radius` sans organes = `max_horiz + foliage_halfwidth` (couronne non nulle
  même droit). `root_radius` = **k·canopy** (k=`PROC_ROOT_RATIO`=1.0). `foliage_density`
  = ancien chemin (→ tronçon 5). Ordre de migration = **tomate seule** ce tronçon.
- **3** ✅ défaut tranché : `cible="branche"` = retrait de l'**apex latéral le plus
  profond** (non-meneur) → la flèche n'est pas touchée, donc la dominance reste
  ~inchangée (elle émerge du choix de cible, pas d'une mécanique dédiée). Repli sur le
  meneur s'il n'y a aucun latéral. Heuristique alternative encore possible (calibrage).
