# Sprint REFACTOR GLOBAL — état partagé

> État léger, mis à jour en **fin de chaque tronçon**. Lire ce fichier +
> le `0N_*.md` du tronçon courant suffit à reprendre à froid.

## But du sprint

Refactor de tout le dépôt (Python + C# + docs) pour s'y retrouver :
regrouper les fichiers par nature, supprimer les fossiles, et faire passer
**chaque fichier sous ~500 lignes de CODE PUR** (commentaires pédagogiques
exclus du décompte et **conservés au cœur des fichiers**).

## Invariants ABSOLUS (toute la durée du sprint)

1. **Golden jamais re-figé.** `cd data/code && python3 -m tests.test_golden`
   reste vert et le hash golden **ne bouge pas** : un refactor ne change
   AUCUN comportement. Si le hash bouge → on s'est trompé, on revient.
2. **Build Godot OK** après tout tronçon C# (compile sans erreur).
3. **~500 lignes de code pur max par fichier.** Convention de comptage =
   `tools/compte_ldc.py` (livré au SS①). Exception tolérée seulement si
   signalée + justifiée à Nico.
4. **Commentaires pédagogiques préservés et centraux** — jamais sacrifiés
   pour gagner des lignes.
5. **Granularité pragmatique** : un fichier = une classe / un concept
   cohérent (PAS une-fonction-par-fichier). Python éclaté → paquet avec
   `__init__.py` qui ré-exporte l'API publique (imports existants intacts).
6. **Avant chaque tronçon : git à jour.** Un commit par tronçon, puis
   `/clear`. Pas de suppression de code utile (cf décision ci-dessous).

## Décisions actées (2026-06-15, conversation kickoff)

- **Suppression** : seulement les fossiles (non modifiés depuis avril ET
  inutiles). Tout ce qui date de mai/juin = rangé/archivé, jamais supprimé.
- **Racine conservatrice** : Python reste dans `data/code/`, Godot à la
  racine (chemins `res://`, `.csproj`, pont `SimBridge` inchangés).
- **`docs/desktop/`** : gardé tel quel (usage propre : export app desktop).
- **Journal** : éclaté par sprint + `journal.md` = index de pointeurs.
- **Seuil 500** : recalibré en clôture (SS⑦) sur le max empirique mesuré.

## Tronçons

| SS | Titre | Risque | Statut |
|----|-------|--------|--------|
| ① | Déchets & docs/conception + helper comptage | nul | ✅ CLOS (2026-06-15) |
| ② | Journal éclaté (index + par sprint) | faible | ✅ CLOS (2026-06-15) |
| ③ | Python cœur sim 1 (engine, ecofields, effects) | élevé | ✅ CLOS (2026-06-15) |
| ④ | Python cœur sim 2 (actions, base, species, growth) | élevé | ✅ CLOS (2026-06-15) |
| ⑤ | Python outils & tests (sim_server, render, 2 tests) | moyen | ✅ CLOS (2026-06-15) |
| ⑥ | C# WorldView (1759 l) | moyen | ✅ CLOS (2026-06-16) — build vert + F5 identique |
| ⑦ | C# reste & finition + grave règles dans CLAUDE.md | moyen | ✅ CLOS (2026-06-16) — build vert + golden inchangé + F5 à valider |

## SPRINT CLOS (2026-06-16)

**Tous les tronçons ①–⑦ clos.** Seuil empirique final **N = 337** lignes de
code pur (`data/code/fields/ecofields/container.py`) — garde-fou gravé dans
`CLAUDE.md` à **~350** (max 337 + soupçon de marge). Golden **inchangé tout le
sprint** : `908f591bee…`. Build C# vert. ⚠️ Reste à Nico : **F5** de validation
visuelle finale (purge C# + éclatements = refactor pur, aucun comportement
touché).
**Outillage** : `dotnet` SDK 8.0.422 sur la VM (`~/.dotnet`, dans `~/.bashrc`,
non chargé en shell non-interactif → `export PATH="$HOME/.dotnet:$PATH"` avant
`dotnet build Symbiose.csproj`).

> **Recalibrage de portée (acté avec Nico, SS③)** : le seuil 500 est un garde-fou,
> pas un dogme — l'objectif réel est **un fichier = une responsabilité cohérente**,
> fichiers courts pour relire vite (tokens / concentration). PAS une-fonction-par-
> fichier (cohésion + coût d'amorçage). On éclate donc **tous** les gros modules,
> y compris ceux déjà sous 500 lignes de code pur — découpe par concept.

## Journal de bord (rempli en fin de tronçon)

- **SS① CLOS (2026-06-15)** — golden inchangé `908f591bee…` (aucun code moteur
  touché, vérifié avant/après).
  - **Helper** : `tools/compte_ldc.py` (nouveau dossier `tools/` racine = outil
    *du dépôt*, pas du moteur ; `tokenize` pour Python, repli ligne-à-ligne pour
    C#). Testé sur `.py` et `.cs`. `--seuil` (défaut 500), tri sur code pur ⚠.
  - **Fossiles purgés** : `sortie.txt` (19 Mo, avril), CV PDF (avril), 6 SVG
    maquettes régénérables (juin mais sorties de `render_structure.py` → ajoutées
    à `.gitignore`). ⚠️ **À signaler Nico** : les SVG dataient de juin (règle
    « mai/juin = ne pas supprimer ») mais le kickoff §B les classe régénérables ;
    choix de les sortir du suivi + gitignore.
  - **Conception regroupée** : 11 `CONCEPTION_*.md` → `docs/conception/` (`git mv`).
    `CONCEPTION_MAITRISE` (561 l) scindé → `maitrise/01_modele` (204) +
    `02_succes_par_axe` (100) + `03_taxonomie_objets` (140) + index (22). Contenu
    intégral préservé. **Pointeurs `data/code/CONCEPTION_` → `docs/conception/`
    corrigés** dans docstrings .py (commentaires only, golden intact) + doc vivante
    (DETTE/BACKLOG/journal/dette_kickoffs/decompo). Archives `_clos/` et
    `journal_archive/` laissées telles quelles.
  - **Sprints clos archivés** sous `sprints/_clos/` (22 entrées). Gardés en place :
    refactor_global (courant), integration_godot (t7 active), decomposition_compost
    (⑥ différé = doute), dette_kickoffs, sprint_1/2/3/4 (C# futurs), etude_sol_vivant
    (référencée Sprint 3).
  - **`integration_godot/00_etat.md`** (707 l, sprint actif) scindé : historique
    tranches 1-6 → `_avancement_t1_t3.md` (120) + `_avancement_t4_t6.md` (439) ;
    `00_etat.md` ramené à 176 l (en-tête + Tranche 7 + REPRISE, flux de reprise
    préservé).
  - **docs/desktop/** : laissé tel quel (tous < 500), RAS.
- **SS② CLOS (2026-06-15)** — golden inchangé `908f591bee…` (aucun code moteur
  touché). `journal.md` (2385 l) éclaté → **`journal/` 41 fichiers** (entrées
  inline, numérotées 13→53, convention `NN_date_slug.md`) + `journal.md` réduit
  à un **index de pointeurs (89 l)**.
  - **Extraction par script déterministe** (copie verbatim, zéro reformulation) :
    découpe aux frontières `## YYYY-MM-DD`. Complétude prouvée : 1948 lignes
    non-blanches identiques source↔fichiers (seule normalisation = lignes
    blanches inter-entrées collapsées). Tous < 500 l (max 82).
  - **`journal_archive/` LAISSÉ tel quel** (décision tranchée) : déjà éclaté
    même convention, nommé emplacement historique stable dans `CLAUDE.md` ET
    référencé par sprints clos (`sprints/_clos/`, mémoire figée) → unification
    casserait des pointeurs historiques, donc pas « propre ». Deux dossiers à
    sémantique claire : `journal_archive/` (01-12, avant refactor structurel) +
    `journal/` (13-53, le reste).
  - **Liens** : aucune ancre profonde `journal.md#section` externe. 53 liens de
    l'index vérifiés (0 cassé). Renvois « voir `journal.md` » (CLAUDE.md l.81/330,
    BACKLOG, _clos) restent valides : `journal.md` existe comme index.
  - ⚠️ **À signaler Nico** : `CLAUDE.md` l.330 dit « `journal.md` (entrées
    récentes) + `journal_archive/` » — désormais légèrement imprécis (les entrées
    récentes sont dans `journal/`, pointées par l'index). Laissé tel quel
    (surgical / un fichier à la fois) ; à rafraîchir au SS⑦ qui grave les règles
    dans CLAUDE.md.
- **SS③ CLOS (2026-06-15)** — golden inchangé `908f591bee…` (vérifié après CHAQUE
  module), `main.py` tourne, **19/19 suites vertes**. Trois modules cœur éclatés en
  paquets (API ré-exportée par les `__init__` → **zéro appelant modifié**) :
  - `sim/engine.py` (967 l / 604 code) → `sim/engine/` : `calendrier` (saisons/phases),
    `aleas` (météo/ravageur + dégât médié), `croissance`/`mortalite`/`decompo`
    (**mixins** : la grosse classe `Engine` scindée par héritage, `self` préservé,
    ordre du tick intact), `boucle` (l'orchestrateur `tick_semaine` + runners).
  - `fields/ecofields.py` (863 l / 459 code) → `fields/ecofields/` : `constants`
    (calibration), `litiere` (`Parcelle`/`Structure`), `container` (`EcoFields` 337 code).
  - `sim/effects.py` (703 l / 403 code) → `sim/effects/` : `mutations` (dataclasses),
    `resolution` (resolve/apply_mutations/callbacks 208 code), `perturbations`
    (mortalités, herbivorie, `deposer_mort`, `apply_disturbances`).
  - **Max code pur après découpe = 337** (container) ; tous < 500.
  - ⚠️ **À signaler Nico** : la redistribution des imports a laissé tomber des
    imports **morts pré-existants** (utilisés seulement dans des commentaires ou plus
    du tout) : engine `Tile`/`PlantInstance`/`Tomato`/`Basil`/`Bean`/`Clover`/
    `Sunflower`/`Pepper`/`InjectField`/`init_eco`/`inject_patch`/`EcoFields`/
    `WeatherEvent` ; effects `RONDELLE_TYPES`/`HERBIVORY_BASE`/`EcoFields`(TYPE_CHECKING).
    Aucun n'était utilisé (golden + 19 suites le confirment).
  - **Décision portée** : recalibrée avec Nico en cours de tronçon (cf. §Reprise) —
    on découpe désormais TOUS les gros fichiers, pas seulement les > 500 code pur.
- **SS④ CLOS (2026-06-15)** — golden inchangé `908f591bee…` (vérifié après CHAQUE
  module), `main.py` tourne, **19/19 suites vertes**, imports outils (`sim_server`,
  `render_structure`, `export_structure`) OK. Quatre modules éclatés en paquets (API
  ré-exportée par les `__init__` → **zéro appelant modifié** ; `plants/__init__.py` et
  `sim/__init__.py` intacts) :
  - `plants/base.py` (738 l / 407 code) → `plants/base/` : `empreintes`
    (`_plots_in_radius` + défauts par strate), `effets` (registre), `stades`
    (`GrowthStage`/`Segment`/`Fruit`/`organ_sites`), `instance` (`PlantInstance`/
    `ConflictNotification`), `familles` (`PlantBase` + 5 familles, 163 code). Ordre de
    couches interne : empreintes/effets/stades ← instance ← familles.
  - `plants/species.py` (654 l / 561 code ⚠ le seul > 500) → `plants/species/` :
    `adventices` (4 archétypes succession), `cultivees` (6 légumes, 308 code),
    `compagnes` (Achillée, Phacélie). Pur data.
  - `sim/growth.py` (503 l / 252 code) → `sim/growth/` : `constantes` (leviers de
    module), `geometrie` (géométrie 3D + topologie + phototropisme PURS, dont
    `_phototropic_bias`), `seam` (`f_lignification` + `atteindre_segment`), `phases`
    (4 phases §D + étiolement + `grow_plant`, 124 code).
  - `sim/actions.py` (775 l / 306 code) → `sim/actions/` : `couts` (paliers + seam
    `cout_action`/`f_globale`/`f_objets`), `progression` (`observer`/`crediter_succes`),
    `gestes` (10 gestes vivant/milieu, 153 code), `compost` (structures ⑤). `maturite`
    ré-exporté par l'`__init__` (compat `ACT.maturite`).
  - **Max code pur après découpe = 308** (cultivees) ; tous < 500.
  - **API préservée vérifiée** : grep des accès `ACT.`/`A.`/`G.` (constantes ET privés
    `_phototropic_bias`/`_objets_action`/`_cle_espece`) → tous ré-exportés par les
    `__init__`. `species.py` était le seul fichier réellement > 500 code pur ; les 3
    autres sous 500 ont été éclatés au titre du recalibrage de portée (SS③).
- **SS⑤ CLOS (2026-06-15)** — golden inchangé `908f591bee…`, **19/19 suites vertes**
  (golden, pont 123/123, Vigueur 135/135, + 16 autres), `vigueur_hash.txt` intact,
  pont vérifié en vrai sous-process (aller-retour réel). 4 cibles éclatées, chacune
  gardant son **point d'entrée historique mince** (chemin/nom inchangés) :
  - `tools/sim_server.py` (779 l / 480 code) → entrée mince (docstring protocole +
    bootstrap sys.path + `__main__`) + paquet `tools/simserver/` : `version`
    (ENGINE_VERSION + historique), `commands` (CommandsMixin init/step/snapshot/fields),
    `actions` (ActionsMixin cmd_action/_do_action/_plant_at/_plot_at, 300 code),
    `serialize` (SerializeMixin _world_static/_snapshot), `server` (SimServer mixins +
    boucle `main`). **Pont Godot intact** : `SimBridge.cs` invoque toujours
    `tools/sim_server.py` ; `.spec` non touché (Analysis suit les imports statiques,
    `tests.test_golden`/`main` déjà en hiddenimports). Classe scindée par MIXINS
    (comme Engine SS③).
  - `tools/render_structure.py` (592 l / 371 code) → entrée mince (CLI + ré-exports) +
    paquet `tools/maquette/` : `iso` (projection + convex_hull), `organes`
    (feuilles/fleurs/fruits + **REPRO_BY_SEASON**), `apercu` (render structure),
    `secteurs` (maquette saisonnière). API ré-exportée vérifiée : `tools/simserver`
    importe `REPRO_BY_SEASON`, `tools/export_structure` importe `SECTEURS_MAQ`/
    `SAISON_WEEK_MAQ`/`SAISONS_ORDRE`/`MAQ_SPECIES`/`_grow_sector` → tous OK.
  - `tests/test_vigueur.py` (899 l / 653 code) → entrée orchestratrice (même ordre) +
    paquet `tests/vigueur/` : `harness` (check/_results/helpers partagés), `contrats`,
    `gestes`, `facades`, `manger`, `macro`, `maitrise_seam`, `golden_traj`. `HASH_FILE`
    pointe toujours `tests/vigueur_hash.txt`. 135/135 inchangé.
  - `tests/test_sim_server.py` (825 l / 617 code) → entrée orchestratrice + paquet
    `tests/simserver/` : `harness` (ServerProc/check/run_scenario), `base` (§1-6),
    `actions` (§7), `taille` (§8+8b), `organes` (§9), `macro` (§10), `fields` (§11),
    `planter` (§12), `structures` (§13). 123/123 inchangé.
  - **Max code pur après découpe = 308** (cultivees, inchangé) ; toutes les nouvelles
    pièces SS⑤ < 320 (sim_server/actions 300, gestes 213, maquette/secteurs 171).
  - **Tests/outils ne participent pas au hash golden** (vérifié : golden re-lancé,
    identique). Les 6 SVG de maquette restent gitignorés (SS①).
- **SS⑥ FAIT (2026-06-16) — build VÉRIFIÉ VERT, F5 visuel en attente Nico.**
  `dotnet` SDK 8.0.422 installé sur la VM (local user `~/.dotnet`) : `dotnet
  build Symbiose.csproj` → **La génération a réussi, 0 avertissement, 0 erreur**
  (Godot.NET.Sdk 4.6.0 restauré depuis NuGet, `Symbiose.dll` produit).
  `world/WorldView.cs`
  (1759 l / **1106 code pur** ⚠) éclaté en **9 fichiers `partial class`** par
  CONCEPT (la scène `WorldView.tscn` pointe toujours la même classe — refactor
  pur, aucun comportement touché) :
  - `WorldView.cs` (193 code) — en-tête complet + état central + `_Ready`/
    `_ExitTree`/`_Process`/`OnSeasonEnd` (cycle de vie + boucle hybride).
  - `WorldView.Projection.cs` (35) — calibration statique + `WorldToScreen`/
    `WorldToScreenOffset`/`ScreenToWorld` + `_orientation`.
  - `WorldView.Controls.cs` (109) — `_UnhandledInput` + bascules (phase, mode,
    étiquettes, maison, ombres, vie macro) + `ApplyHouseGhost`.
  - `WorldView.Monde.cs` (144) — palettes + sol (`BuildGround`…) + maison
    (`BuildHouse`/`RoofPane`) + géométrie ombre maison.
  - `WorldView.Soleil.cs` (81) — modèle solaire + `UpdateSun`/`UpdateHouseShadow`.
  - `WorldView.Snapshot.cs` (130) — diff plantes `ApplySnapshot` + tags + saison.
  - `WorldView.Actions.cs` (184) — 8 gestes + picking (`FindPlant`/`FindPlot`/
    `FindSegmentGlobal`) + surbrillance taille + survol.
  - `WorldView.Hud.cs` (211, le plus gros) — HUD provisoire + overlay heatmap
    (toggle/cycle/légende).
  - `WorldView.Camera.cs` (82) — caméra D35 (pan/zoom/rotation) + `RebuildWorld`.
  - **Choix : `partial` partout**, PAS d'extraction de vraies classes
    (`CameraController`…) : les blocs sont fortement couplés à l'état partagé
    (`_plantNodes`, `_world`, `_phase`…) ; les extraire changerait la structure
    et risquerait le « rendu inchangé ». `partial` = recollage compilateur, zéro
    risque sémantique.
  - **Vérifs statiques (faute de compilateur)** : accolades équilibrées (9/9) ;
    **146 membres** identiques à l'original (diff git : 0 perdu, 0 ajouté,
    0 dupliqué) ; `using` adéquats par fichier (aucun manquant, aucun inutile →
    pas de CS8019). Max code pur après découpe = **211** (Hud) ; tous < 500.
  - ⚠️ **À FAIRE Nico** : **F5** (rendu/caméra/ombre/actions identiques — le
    build est déjà vert). Si visuellement OK → merge `refactor/ss6-worldview`
    sur `main`. Sinon, me signaler ce qui diffère.
- **SS⑦ CLOS (2026-06-16) — build VÉRIFIÉ VERT, golden inchangé `908f591bee…`,
  F5 final en attente Nico.** Dernier tronçon, sprint clos. Branche
  `refactor/ss7-finition`.
  - **Partie A — purge C# mort (Option B).** 15 stubs vides (15 l chacun, datés
    du « Snapshot initial » 2026-05-29) + `Main.cs/.tscn` + `world/TileGrid.cs/
    .tscn` supprimés (`git rm`, **historique préservé**). Protocole de sûreté
    suivi : grep par nom de classe (.cs) ET par chemin (.tscn/.uid/.godot) →
    **zéro référence en code/scène** (toutes les mentions restantes sont dans
    docs/journaux historiques). Scène principale confirmée = `WorldView.tscn`,
    rien n'instancie `Main.tscn`/`TileGrid.tscn`. **Décision Nico** (AskUser, vu
    tension règle « mai/juin = jamais supprimer » : `TileGrid.cs` = 202 l, juin) :
    `git rm` tout, l'historique git récupère. `ui/` devient vide (disparaît) ;
    `plants/` garde `species/`.
  - **Partie B — éclatements** (1 fichier = 1 classe / 1 concept ; namespace
    `Symbiose`, chemins `res://` intacts, `.uid` régénérés par Godot au F5) :
    `PlantData.cs` → `GrowthStage`/`PlantData`/`PlantInstance` ;
    `TileData.cs` → `Tile`/`StakeSlot`/`ConflictNotification`/`RondelleRules` ;
    `GridField.cs` → `GridField`/`LightField`/`EcoFields` ;
    `PlantRenderer.cs` → `PlantRenderer` + `.Organs.cs` (partial) + `PlantShadow.cs` ;
    `PlantCatalogue.cs` (604 code, **seul > 500**) → shell (types+registre+helpers)
    + partials `.Cultivees.cs`/`.Succession.cs`/`.Indicatrices.cs` (`Build()`
    délègue à `BuildCultivated/Succession/Indicators`). Build vérifié vert après
    CHAQUE groupe.
  - **Mesure réelle code pur** (≠ total du kickoff) : seul `PlantCatalogue.cs`
    dépassait 500 (604) ; `GridField.cs`=422, `PlantRenderer.cs`=328 éclatés au
    titre du recalibrage de portée (concepts distincts). `PlantRenderer` gardé
    en 1 classe cohésive + partial organes + classe `PlantShadow` extraite.
  - **Partie C — règles gravées** dans `CLAUDE.md` : Fonctionnels (C#) réécrits
    (nouveaux fichiers), bloc « stubs supprimés (Option B) », règle de taille
    (garde-fou ~350 code pur, max empirique 337, `compte_ldc.py`, un fichier =
    une responsabilité), arbo cible (docs/conception, journal éclaté), + fix
    imprécision SS② sur `journal.md` (index → `journal/`).
  - **Partie D — recalibrage** : `compte_ldc.py` sur tout le dépôt (.py+.cs) →
    max **337** = `fields/ecofields/container.py`. Côté C# max = `WorldView.Hud.cs`
    (211). **Aucun fichier > 350**. Seuil gravé **N≈350** (337 + marge).
  - ⚠️ **À signaler Nico** : seuil descendu de ~500 → ~350 (recalibrage prévu
    dès SS①). Mémoire `feedback_taille_fichiers` à rafraîchir. **À FAIRE : F5**
    (refactor pur ; si OK → merge `refactor/ss7-finition` sur `main`).
