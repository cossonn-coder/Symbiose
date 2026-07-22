# ① Structure + carte du tri

**Préalable** : lire `00_etat.md`. **Rien n'est déplacé dans ce tronçon** — on
crée l'arborescence vide et la carte qui fera foi pour les tronçons suivants.

## Livrables

1. L'arborescence de dossiers vides sous `docs/`, chacun avec un `README.md`
   d'**une ligne** décrivant le thème (sert d'ancre git et de description).
2. `docs/ARBORESCENCE.md` — la carte : types → thèmes → fichiers, **plus** la
   table « ancien chemin → nouveau chemin » (clé de lecture de l'historique,
   cf. décision 4 de `00_etat.md`).

## Taxonomie — 8 types, niveau 2 = thème

```
docs/
├── ARBORESCENCE.md
├── meta/          transverse projet, non-feature
│   ├── (vision, architecture, historique_decisions, instructions)
│   ├── amorce/        archives d'amorçage du projet
│   ├── calibrage/     santé/équilibre global du système
│   └── agent/         protocole de délégation (tronçon ⑥)
├── champs/        les champs de simulation
│   ├── sol/  lumiere/  eau/  climat/
├── vegetal/       physiologie et populations végétales
│   ├── croissance/  genetique/  sante/  floraison/
│   ├── allelopathie/  grimpantes/  catalogue/
├── faune/         vie animale et fongique
│   ├── vie_macro/  trophique/  pollinisation/  mycelium/
├── joueur/        mécaniques joueur
│   ├── vigueur/  maitrise/  gestes/  outils/  automate/
├── narration/     voix et dispositifs informationnels
│   ├── voix/  semiologie/  ledger/
├── rendu/         vue Godot, pixel-art
│   ├── pixelart/  ambiance/  feuillage/  spatial/
└── perf/          performance
    ├── run_eternel/  lod/  scatter/
```

## Mapping des 56 `docs/conception/CONCEPTION_*.md` (tranché — appliquer tel quel)

Nom cible = `conception_<sujet minuscule>.md` dans le dossier indiqué.

| Doc source | Destination |
|---|---|
| ACQUISITION_OUTILS | `joueur/outils/` |
| ALLELOPATHIE | `vegetal/allelopathie/` |
| BUGS_EMERGENCE | `meta/calibrage/` |
| CALIBRATION_REALISTE | `meta/calibrage/` |
| CATALOGUE_ENRICHI | `vegetal/catalogue/` |
| COMPETITION_INTRAPLOT | `vegetal/catalogue/` |
| COMPLETUDE_ECOSYSTEME | `meta/calibrage/` |
| CROISSANCE | `vegetal/croissance/` |
| DECOMPOSITION_COMPOST | `champs/sol/` |
| DESYNC_PHENOLOGIE | `vegetal/floraison/` |
| DIVERSITE_FONDATRICE | `vegetal/genetique/` |
| ECRASEMENT | `joueur/gestes/` |
| EPAISSEUR_SOL | `champs/sol/` |
| EQUILIBRE_INVASION | `faune/trophique/` |
| FAUNE_DEDIEE | `faune/vie_macro/` |
| FLORAISON_FRUCTIFICATION | `vegetal/floraison/` |
| GERMINATION_THERMIQUE | `vegetal/floraison/` |
| GRIMPANTES | `vegetal/grimpantes/` |
| HORMONES | `vegetal/croissance/` |
| HYDROLOGIE_MARECAGE | `champs/eau/` |
| JARDINIER_AUTOMATE | `joueur/automate/` |
| LUXURIANCE_STRATIFICATION | `vegetal/grimpantes/` |
| MAISON_OMBRE | `champs/lumiere/` |
| MAITRISE | `joueur/maitrise/` |
| METEO | `champs/climat/` |
| METEO_CHAMPS | `champs/climat/` |
| MODELE_SPATIAL | `rendu/spatial/` |
| MYCELIUM_INTERCONNEXIONS | `faune/mycelium/` |
| PALETTE_GESTES | `joueur/gestes/` |
| PERF_LOD_OMBRE | `perf/lod/` |
| PERF_RENDU_PLANTES | `perf/lod/` |
| PERF_RUN_ETERNEL | `perf/run_eternel/` |
| PERF_SCATTER_RECUE | `perf/scatter/` |
| PLANTER_ARROSER | `joueur/gestes/` |
| PLASTICITE_EXPRESSION | `vegetal/genetique/` |
| POLLINISATION_CYCLE_VIE | `faune/pollinisation/` |
| POTS_BACS_SUBSTRATS | `joueur/outils/` |
| RENDU_AMBIANCE | `rendu/ambiance/` |
| RENDU_FEUILLAGE | `rendu/feuillage/` |
| RENDU_PIXELART | `rendu/pixelart/` |
| SAISONNALITE_VIE_MACRO | `faune/vie_macro/` |
| SANTE_RESILIENCE | `vegetal/sante/` |
| SEMIOLOGIE_FOLIAIRE | `narration/semiologie/` |
| SEMIOLOGIE_VISUELLE | `narration/semiologie/` |
| SOL_NUTRIMENTS_NPK | `champs/sol/` |
| SOL_PH | `champs/sol/` |
| SOL_STRUCTURE | `champs/sol/` |
| SOMMET_TROPHIQUE | `faune/trophique/` |
| THERMIQUE_MICROCLIMAT | `champs/climat/` |
| USURE_LETALITE | `vegetal/sante/` |
| VENT_EVAPOTRANSPIRATION | `champs/climat/` |
| VIE_MACRO | `faune/vie_macro/` |
| VIE_MACRO_IDENTIFIABLE | `faune/vie_macro/` |
| VIGUEUR | `joueur/vigueur/` |
| VOIX_NARRATIVES | `narration/voix/` |
| VOIX_NARRATIVES_UI | `narration/voix/` |

**Autres sources** (traitées au tronçon ②) :

| Source | Destination |
|---|---|
| `docs/conception/maitrise/0{1,2,3}_*.md` | `joueur/maitrise/` (noms conservés) |
| `docs/desktop/vision.md` | `meta/vision.md` |
| `docs/desktop/architecture.md` | `meta/architecture.md` |
| `docs/desktop/historique_decisions.md` | `meta/historique_decisions.md` |
| `docs/desktop/instructions.md` | `meta/instructions.md` |
| `docs/amorce/*` (5 fichiers) | `meta/amorce/` (noms en minuscules) |
| `sprints/etude_sol_vivant.md` | `champs/sol/etude_sol_vivant.md` |
| `sprints/etude_physicochimie_sol.md` | `champs/sol/etude_physicochimie_sol.md` |

## Thèmes créés vides (remplis au fil de l'eau)

`champs/lumiere/` (n'aura MAISON_OMBRE qu'au ②, + extraction Z7 au ④),
`narration/ledger/`, `meta/agent/`. Chacun reçoit son `README.md` d'une ligne.

## Vérification

- `find docs -type d | sort` reflète l'arbre ci-dessus.
- Chaque dossier feuille contient un `README.md` non vide.
- `docs/ARBORESCENCE.md` liste les 56 docs avec leur destination.
- `cd data/code && python3 -m tests.test_golden` → **inchangé** (rien touché).

## Commit

`docs(rangement) ① : arborescence 8 types + carte ARBORESCENCE.md`

Puis cocher ① dans `00_etat.md`.
