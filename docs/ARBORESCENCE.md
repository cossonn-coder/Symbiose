# ARBORESCENCE — carte de la documentation Symbiose

**Rôle de ce fichier** : dire où vit chaque document, et où il vivait avant.
C'est la **clé de lecture de tout l'historique** — les 126 entrées de `journal/`
et `journal_archive/` ne sont **pas** réécrites (décision 4 du sprint de
rangement) : elles citent les anciens chemins, et cette table les traduit.

**État** : arborescence créée au tronçon ① du sprint de rangement documentaire
(2026-07-22). Les déplacements eux-mêmes ont lieu au tronçon ② — tant qu'il
n'est pas passé, la colonne « ancien chemin » décrit encore la réalité du dépôt.

---

## 1. Principe de rangement

Deux niveaux, et deux seulement :

```
docs/<type de feature>/<thème de feature>/<document>.md
```

- **Type** (8, fermé) : `meta · champs · vegetal · faune · joueur · narration ·
  rendu · perf`. On n'en ajoute pas sans décision explicite de Nico.
- **Thème** : ouvert — un nouveau sujet peut créer son thème, avec son
  `README.md` d'une ligne.
- Chaque dossier porte un `README.md` d'**une ligne** qui dit ce qu'il contient.
  Il sert d'ancre git (git ne versionne pas les dossiers vides) et de
  description lisible depuis une liste de fichiers.
- Noms de fichiers en **`snake_case` sans accents** ; contenu en **français
  accentué**.

## 2. Les 8 types

| Type | Ce qu'il contient |
|---|---|
| `meta/` | Transverse projet, non-feature : vision, architecture, historique des décisions, instructions, amorce, calibrage global, protocole d'agent. |
| `champs/` | Les champs de simulation — le **milieu** sur lequel le joueur agit (philo #1) : sol, lumière, eau, climat. |
| `vegetal/` | Physiologie et populations végétales : croissance, génétique, santé, floraison, allélopathie, grimpantes, catalogue. |
| `faune/` | Vie animale et fongique : vie macro, trophique, pollinisation, mycélium. |
| `joueur/` | Mécaniques joueur : vigueur, maîtrise, gestes, outils, automate. |
| `narration/` | Voix diégétiques et dispositifs informationnels : voix, sémiologie, ledger. |
| `rendu/` | Vue Godot : pixel-art, ambiance, feuillage, modèle spatial. |
| `perf/` | Performance : run éternel, LOD, scatter. |

## 3. Ce qui ne bouge pas — et pourquoi

- **`CLAUDE.md` reste à la racine.** C'est le fichier d'instructions auto-chargé
  par Claude Code, pas un document de philosophie. Jamais déplacé.
- **`journal/` + `journal_archive/` restent canoniques.** La valeur de ces 126
  entrées est leur **chronologie**. Chaque thème reçoit au tronçon ③ un fichier
  de **renvois** (liens vers les entrées qui le concernent), pas un fragment
  recopié.
- **`DETTE.md` reste canonique.** Les identifiants `Dxx` sont cités dans le code
  et dans les sprints ; les démembrer coûterait plus que ça ne rapporte. Même
  traitement que le journal : renvois par thème.
- **`BACKLOG.md` est le seul pivot éclaté physiquement** par thème (tronçon ③).

---

## 4. Carte type → thème → documents

### `meta/` — transverse projet

| Thème | Documents |
|---|---|
| *(racine)* | `vision.md`, `architecture.md`, `historique_decisions.md`, `instructions.md` |
| `amorce/` | `amorce_conception_automate.md`, `audit_champs.md`, `brief_champs_conception.md`, `brief_claude.md`, `brief_claude_web.md` |
| `calibrage/` | `conception_bugs_emergence.md`, `conception_calibration_realiste.md`, `conception_completude_ecosysteme.md` |
| `agent/` | *(vide — `deepseek_protocol.md` au tronçon ⑥)* |

### `champs/` — champs de simulation

| Thème | Documents |
|---|---|
| `sol/` | `conception_decomposition_compost.md`, `conception_epaisseur_sol.md`, `conception_sol_nutriments_npk.md`, `conception_sol_ph.md`, `conception_sol_structure.md`, `etude_sol_vivant.md`, `etude_physicochimie_sol.md` |
| `lumiere/` | `conception_maison_ombre.md` *(+ extraction Z7 au tronçon ④)* |
| `eau/` | `conception_hydrologie_marecage.md` |
| `climat/` | `conception_meteo.md`, `conception_meteo_champs.md`, `conception_thermique_microclimat.md`, `conception_vent_evapotranspiration.md` |

### `vegetal/` — physiologie et populations végétales

| Thème | Documents |
|---|---|
| `croissance/` | `conception_croissance.md`, `conception_hormones.md` |
| `genetique/` | `conception_diversite_fondatrice.md`, `conception_plasticite_expression.md` |
| `sante/` | `conception_sante_resilience.md`, `conception_usure_letalite.md` |
| `floraison/` | `conception_desync_phenologie.md`, `conception_floraison_fructification.md`, `conception_germination_thermique.md` |
| `allelopathie/` | `conception_allelopathie.md` |
| `grimpantes/` | `conception_grimpantes.md`, `conception_luxuriance_stratification.md` |
| `catalogue/` | `conception_catalogue_enrichi.md`, `conception_competition_intraplot.md` |

### `faune/` — vie animale et fongique

| Thème | Documents |
|---|---|
| `vie_macro/` | `conception_faune_dediee.md`, `conception_saisonnalite_vie_macro.md`, `conception_vie_macro.md`, `conception_vie_macro_identifiable.md` |
| `trophique/` | `conception_equilibre_invasion.md`, `conception_sommet_trophique.md` |
| `pollinisation/` | `conception_pollinisation_cycle_vie.md` |
| `mycelium/` | `conception_mycelium_interconnexions.md` |

### `joueur/` — mécaniques joueur

| Thème | Documents |
|---|---|
| `vigueur/` | `conception_vigueur.md` |
| `maitrise/` | `conception_maitrise.md`, `01_modele.md`, `02_succes_par_axe.md`, `03_taxonomie_objets.md` |
| `gestes/` | `conception_ecrasement.md`, `conception_palette_gestes.md`, `conception_planter_arroser.md` |
| `outils/` | `conception_acquisition_outils.md`, `conception_pots_bacs_substrats.md` |
| `automate/` | `conception_jardinier_automate.md` |

### `narration/` — voix et dispositifs informationnels

| Thème | Documents |
|---|---|
| `voix/` | `conception_voix_narratives.md`, `conception_voix_narratives_ui.md` |
| `semiologie/` | `conception_semiologie_foliaire.md`, `conception_semiologie_visuelle.md` |
| `ledger/` | *(vide — se remplit au fil de l'eau)* |

### `rendu/` — vue Godot

| Thème | Documents |
|---|---|
| `pixelart/` | `conception_rendu_pixelart.md` |
| `ambiance/` | `conception_rendu_ambiance.md` |
| `feuillage/` | `conception_rendu_feuillage.md` |
| `spatial/` | `conception_modele_spatial.md` |

### `perf/` — performance

| Thème | Documents |
|---|---|
| `run_eternel/` | `conception_perf_run_eternel.md` |
| `lod/` | `conception_perf_lod_ombre.md`, `conception_perf_rendu_plantes.md` |
| `scatter/` | `conception_perf_scatter_recue.md` |

---

## 5. Table de traduction — ancien chemin → nouveau chemin

Sert à relire les 126 entrées de journal, les sprints clos et les commits
antérieurs au 2026-07-22 sans se perdre.

### 5.1 Les 56 conceptions (`docs/conception/CONCEPTION_*.md`)

| Ancien chemin | Nouveau chemin |
|---|---|
| `docs/conception/CONCEPTION_ACQUISITION_OUTILS.md` | `docs/joueur/outils/conception_acquisition_outils.md` |
| `docs/conception/CONCEPTION_ALLELOPATHIE.md` | `docs/vegetal/allelopathie/conception_allelopathie.md` |
| `docs/conception/CONCEPTION_BUGS_EMERGENCE.md` | `docs/meta/calibrage/conception_bugs_emergence.md` |
| `docs/conception/CONCEPTION_CALIBRATION_REALISTE.md` | `docs/meta/calibrage/conception_calibration_realiste.md` |
| `docs/conception/CONCEPTION_CATALOGUE_ENRICHI.md` | `docs/vegetal/catalogue/conception_catalogue_enrichi.md` |
| `docs/conception/CONCEPTION_COMPETITION_INTRAPLOT.md` | `docs/vegetal/catalogue/conception_competition_intraplot.md` |
| `docs/conception/CONCEPTION_COMPLETUDE_ECOSYSTEME.md` | `docs/meta/calibrage/conception_completude_ecosysteme.md` |
| `docs/conception/CONCEPTION_CROISSANCE.md` | `docs/vegetal/croissance/conception_croissance.md` |
| `docs/conception/CONCEPTION_DECOMPOSITION_COMPOST.md` | `docs/champs/sol/conception_decomposition_compost.md` |
| `docs/conception/CONCEPTION_DESYNC_PHENOLOGIE.md` | `docs/vegetal/floraison/conception_desync_phenologie.md` |
| `docs/conception/CONCEPTION_DIVERSITE_FONDATRICE.md` | `docs/vegetal/genetique/conception_diversite_fondatrice.md` |
| `docs/conception/CONCEPTION_ECRASEMENT.md` | `docs/joueur/gestes/conception_ecrasement.md` |
| `docs/conception/CONCEPTION_EPAISSEUR_SOL.md` | `docs/champs/sol/conception_epaisseur_sol.md` |
| `docs/conception/CONCEPTION_EQUILIBRE_INVASION.md` | `docs/faune/trophique/conception_equilibre_invasion.md` |
| `docs/conception/CONCEPTION_FAUNE_DEDIEE.md` | `docs/faune/vie_macro/conception_faune_dediee.md` |
| `docs/conception/CONCEPTION_FLORAISON_FRUCTIFICATION.md` | `docs/vegetal/floraison/conception_floraison_fructification.md` |
| `docs/conception/CONCEPTION_GERMINATION_THERMIQUE.md` | `docs/vegetal/floraison/conception_germination_thermique.md` |
| `docs/conception/CONCEPTION_GRIMPANTES.md` | `docs/vegetal/grimpantes/conception_grimpantes.md` |
| `docs/conception/CONCEPTION_HORMONES.md` | `docs/vegetal/croissance/conception_hormones.md` |
| `docs/conception/CONCEPTION_HYDROLOGIE_MARECAGE.md` | `docs/champs/eau/conception_hydrologie_marecage.md` |
| `docs/conception/CONCEPTION_JARDINIER_AUTOMATE.md` | `docs/joueur/automate/conception_jardinier_automate.md` |
| `docs/conception/CONCEPTION_LUXURIANCE_STRATIFICATION.md` | `docs/vegetal/grimpantes/conception_luxuriance_stratification.md` |
| `docs/conception/CONCEPTION_MAISON_OMBRE.md` | `docs/champs/lumiere/conception_maison_ombre.md` |
| `docs/conception/CONCEPTION_MAITRISE.md` | `docs/joueur/maitrise/conception_maitrise.md` |
| `docs/conception/CONCEPTION_METEO.md` | `docs/champs/climat/conception_meteo.md` |
| `docs/conception/CONCEPTION_METEO_CHAMPS.md` | `docs/champs/climat/conception_meteo_champs.md` |
| `docs/conception/CONCEPTION_MODELE_SPATIAL.md` | `docs/rendu/spatial/conception_modele_spatial.md` |
| `docs/conception/CONCEPTION_MYCELIUM_INTERCONNEXIONS.md` | `docs/faune/mycelium/conception_mycelium_interconnexions.md` |
| `docs/conception/CONCEPTION_PALETTE_GESTES.md` | `docs/joueur/gestes/conception_palette_gestes.md` |
| `docs/conception/CONCEPTION_PERF_LOD_OMBRE.md` | `docs/perf/lod/conception_perf_lod_ombre.md` |
| `docs/conception/CONCEPTION_PERF_RENDU_PLANTES.md` | `docs/perf/lod/conception_perf_rendu_plantes.md` |
| `docs/conception/CONCEPTION_PERF_RUN_ETERNEL.md` | `docs/perf/run_eternel/conception_perf_run_eternel.md` |
| `docs/conception/CONCEPTION_PERF_SCATTER_RECUE.md` | `docs/perf/scatter/conception_perf_scatter_recue.md` |
| `docs/conception/CONCEPTION_PLANTER_ARROSER.md` | `docs/joueur/gestes/conception_planter_arroser.md` |
| `docs/conception/CONCEPTION_PLASTICITE_EXPRESSION.md` | `docs/vegetal/genetique/conception_plasticite_expression.md` |
| `docs/conception/CONCEPTION_POLLINISATION_CYCLE_VIE.md` | `docs/faune/pollinisation/conception_pollinisation_cycle_vie.md` |
| `docs/conception/CONCEPTION_POTS_BACS_SUBSTRATS.md` | `docs/joueur/outils/conception_pots_bacs_substrats.md` |
| `docs/conception/CONCEPTION_RENDU_AMBIANCE.md` | `docs/rendu/ambiance/conception_rendu_ambiance.md` |
| `docs/conception/CONCEPTION_RENDU_FEUILLAGE.md` | `docs/rendu/feuillage/conception_rendu_feuillage.md` |
| `docs/conception/CONCEPTION_RENDU_PIXELART.md` | `docs/rendu/pixelart/conception_rendu_pixelart.md` |
| `docs/conception/CONCEPTION_SAISONNALITE_VIE_MACRO.md` | `docs/faune/vie_macro/conception_saisonnalite_vie_macro.md` |
| `docs/conception/CONCEPTION_SANTE_RESILIENCE.md` | `docs/vegetal/sante/conception_sante_resilience.md` |
| `docs/conception/CONCEPTION_SEMIOLOGIE_FOLIAIRE.md` | `docs/narration/semiologie/conception_semiologie_foliaire.md` |
| `docs/conception/CONCEPTION_SEMIOLOGIE_VISUELLE.md` | `docs/narration/semiologie/conception_semiologie_visuelle.md` |
| `docs/conception/CONCEPTION_SOL_NUTRIMENTS_NPK.md` | `docs/champs/sol/conception_sol_nutriments_npk.md` |
| `docs/conception/CONCEPTION_SOL_PH.md` | `docs/champs/sol/conception_sol_ph.md` |
| `docs/conception/CONCEPTION_SOL_STRUCTURE.md` | `docs/champs/sol/conception_sol_structure.md` |
| `docs/conception/CONCEPTION_SOMMET_TROPHIQUE.md` | `docs/faune/trophique/conception_sommet_trophique.md` |
| `docs/conception/CONCEPTION_THERMIQUE_MICROCLIMAT.md` | `docs/champs/climat/conception_thermique_microclimat.md` |
| `docs/conception/CONCEPTION_USURE_LETALITE.md` | `docs/vegetal/sante/conception_usure_letalite.md` |
| `docs/conception/CONCEPTION_VENT_EVAPOTRANSPIRATION.md` | `docs/champs/climat/conception_vent_evapotranspiration.md` |
| `docs/conception/CONCEPTION_VIE_MACRO.md` | `docs/faune/vie_macro/conception_vie_macro.md` |
| `docs/conception/CONCEPTION_VIE_MACRO_IDENTIFIABLE.md` | `docs/faune/vie_macro/conception_vie_macro_identifiable.md` |
| `docs/conception/CONCEPTION_VIGUEUR.md` | `docs/joueur/vigueur/conception_vigueur.md` |
| `docs/conception/CONCEPTION_VOIX_NARRATIVES.md` | `docs/narration/voix/conception_voix_narratives.md` |
| `docs/conception/CONCEPTION_VOIX_NARRATIVES_UI.md` | `docs/narration/voix/conception_voix_narratives_ui.md` |

### 5.2 Autres sources

| Ancien chemin | Nouveau chemin |
|---|---|
| `docs/conception/maitrise/01_modele.md` | `docs/joueur/maitrise/01_modele.md` |
| `docs/conception/maitrise/02_succes_par_axe.md` | `docs/joueur/maitrise/02_succes_par_axe.md` |
| `docs/conception/maitrise/03_taxonomie_objets.md` | `docs/joueur/maitrise/03_taxonomie_objets.md` |
| `docs/desktop/vision.md` | `docs/meta/vision.md` |
| `docs/desktop/architecture.md` | `docs/meta/architecture.md` |
| `docs/desktop/historique_decisions.md` | `docs/meta/historique_decisions.md` |
| `docs/desktop/instructions.md` | `docs/meta/instructions.md` |
| `docs/amorce/amorce_conception_automate.md` | `docs/meta/amorce/amorce_conception_automate.md` |
| `docs/amorce/audit_champs.md` | `docs/meta/amorce/audit_champs.md` |
| `docs/amorce/BRIEF_CHAMPS_CONCEPTION.md` | `docs/meta/amorce/brief_champs_conception.md` |
| `docs/amorce/brief_claude.md` | `docs/meta/amorce/brief_claude.md` |
| `docs/amorce/BRIEF_CLAUDE_WEB.md` | `docs/meta/amorce/brief_claude_web.md` |
| `sprints/etude_sol_vivant.md` | `docs/champs/sol/etude_sol_vivant.md` |
| `sprints/etude_physicochimie_sol.md` | `docs/champs/sol/etude_physicochimie_sol.md` |

**Après le tronçon ②**, `docs/conception/`, `docs/desktop/` et `docs/amorce/`
n'existent plus. Toute référence à ces chemins dans un fichier **vivant**
(`CLAUDE.md`, `BACKLOG.md`, `DETTE.md`, `journal.md`, skills `.claude/skills/`,
commentaire de `world/SolTexture.cs`) est réparée au tronçon ④. Les références
dans `journal/` et `journal_archive/` sont laissées telles quelles : cette table
est leur traduction.

---

## 6. Où ranger un document neuf

1. Quel **type** ? Si aucun des 8 ne convient, ce n'est probablement pas un doc
   de feature → `meta/`. On n'ouvre pas un 9ᵉ type sans Nico.
2. Quel **thème** ? S'il n'existe pas, on le crée avec son `README.md` d'une
   ligne — et on ajoute la ligne correspondante au §4 de ce fichier.
3. Nom de fichier en `snake_case` sans accents, préfixé `conception_` pour une
   conception, `etude_` pour une étude préparatoire.
