# Backlog — SYMBIOSE

> **Index de pointeurs.** Depuis le tronçon ③ du sprint de rangement
> documentaire (2026-07-22), le backlog est **éclaté par thème** sous
> `docs/<type>/<theme>/backlog_<theme>.md` — même convention que
> [`journal.md`](journal.md). Ce fichier ne contient plus d'entrée de sprint :
> il dit où elles vivent. Pour ajouter un sprint au backlog, écrire sa ligne
> dans le fragment de son thème (et créer le fragment si le thème n'en a pas).
>
> Chaque sprint à venir possède un **kickoff autosuffisant** sous
> `sprints/<type>/<theme>/` — les sprints actifs suivent la **même taxonomie**
> que `docs/` depuis le tronçon ⑤ (cf. `docs/ARBORESCENCE.md` §7). À l'ouverture
> d'une nouvelle session, donner à Claude l'instruction « lis
> `sprints/<type>/<theme>/sprint_X/00_etat.md` » suffit à reprendre sans le
> contexte de la session précédente.
>
> Dette technique → [`DETTE.md`](DETTE.md) · Journal → [`journal.md`](journal.md)
> · Carte de la documentation → [`docs/ARBORESCENCE.md`](docs/ARBORESCENCE.md)

## Sprint en cours

*Aucun en exécution.*

Dernier sprint clos : **PÉRIPHÉRIE — le jardin n'est pas une île** (D73,
2026-07-26, `/sprint-auto` ①→⑦ + passe `/refactor`) — la périphérie cesse d'être
un décor : **ceinture de 4 secteurs cardinaux en vérité Python**
(`fields/peripherie.py`, **D92 refermée** — 4 côtés identiques 96,0 % → **2,7 %**,
falaise 0 % → **52,0 %** sur 300 000 seeds), **cinq flux entrants** (ombre de
lisière · abri poreux + champ neuf `eco.turbulence` · pluie de graines · nappe de
berge en condition aux limites · corridor `eco.lisiere` + `lisiere_w` par guilde),
**sept gestes** de paysage (`abattre`/`receper`/`eteter` gatés hache/serpe,
`endiguer`/`deriver`/`entailler` + `creuser` étendu au secteur) avec asymétrie de
réversibilité (trogne 5 ans · taillis 10 · canopée 30 · entaille **jamais** ·
ouvrage rompt à 8), bois rendu en **parcelles de litière `bois`** aux plots du
bord, érosion sur `structure_sol`/`om_stable`, **saule** au catalogue avec ses
5 voix, et `DecorLayer` qui **CONSOMME** le snapshot (couture D58·T4 consommée,
clic hors jardin → `cote`, protocole **0.5.41**) ;
`sprints/champs/peripherie/sprint_peripherie/00_etat.md` (golden `57c166d8…`
**INCHANGÉ du premier au dernier tronçon** — ceinture opt-in, aucun re-figeage ;
`dotnet build` vert ; perf dans le bruit ; reste **F5 Nico**, 6+6 points de
calibrage). **D73 CLOSE**, D92 absorbée, D93 périmée, D94 confirmée,
**D95→D99 ouvertes**.

Sprint clos précédent : **système de quêtes** (D79, 2026-07-24, `/sprint-auto`
①→⑤) — module MOTEUR joueur neuf `sim/quetes.py` (opt-in, conditions cumulées par
hook geste + conditions d'état sur snapshot hors tick, déclenchement déterministe
par palier/saison, plafond 6) + corpus de **lettres anonymes** `sim/quetes_corpus.py`
(voix épistolaire, progression diégétique #5) + récompenses (simples + rares :
vivace déjà enracinée par vraie croissance, structure gratuite ; outil différé
→ **D93**) + pont `courrier` + panneau C# `CourrierPanel` au hub + banc F5
`bancs/courrier.py` ; `sprints/joueur/automate/sprint_quetes/00_etat.md`
(golden INTACT `57c166d8…` de bout en bout, `dotnet build` vert, pont 0.5.40,
`test_quetes` 52/52, reste F5 Nico). **D79 CLOSE**.

(Sprints clos plus anciens : voir [`journal.md`](journal.md) — mémoire d'inoculum
du sol D10, migration des arbres D91, lisibilité du décor D83…)

## Backlog par thème

| Thème | Fragment |
|---|---|
| `champs/climat` | [climat](docs/champs/climat/backlog_climat.md) |
| `champs/eau` | [eau](docs/champs/eau/backlog_eau.md) |
| `champs/lumiere` | [lumière](docs/champs/lumiere/backlog_lumiere.md) |
| `champs/peripherie` | [périphérie](docs/champs/peripherie/backlog_peripherie.md) |
| `champs/sol` | [sol](docs/champs/sol/backlog_sol.md) |
| `faune/mycelium` | [mycélium](docs/faune/mycelium/backlog_mycelium.md) |
| `faune/pollinisation` | [pollinisation](docs/faune/pollinisation/backlog_pollinisation.md) |
| `faune/trophique` | [réseau trophique](docs/faune/trophique/backlog_trophique.md) |
| `faune/vie_macro` | [vie macroscopique](docs/faune/vie_macro/backlog_vie_macro.md) |
| `joueur/automate` | [jardinier automate](docs/joueur/automate/backlog_automate.md) |
| `joueur/gestes` | [gestes](docs/joueur/gestes/backlog_gestes.md) |
| `joueur/interface` | [fenêtrage UI](docs/joueur/interface/backlog_interface.md) |
| `joueur/maitrise` | [maîtrise](docs/joueur/maitrise/backlog_maitrise.md) |
| `joueur/outils` | [outils & conteneurs](docs/joueur/outils/backlog_outils.md) |
| `joueur/vigueur` | [Vigueur](docs/joueur/vigueur/backlog_vigueur.md) |
| `meta` | [transverse projet & portage C#](docs/meta/backlog_meta.md) |
| `meta/calibrage` | [calibrage global & bancs d'essai](docs/meta/calibrage/backlog_calibrage.md) |
| `narration/voix` | [voix narratives](docs/narration/voix/backlog_voix.md) |
| `perf/lod` | [LOD](docs/perf/lod/backlog_lod.md) |
| `perf/run_eternel` | [run éternel](docs/perf/run_eternel/backlog_run_eternel.md) |
| `perf/scatter` | [scatter](docs/perf/scatter/backlog_scatter.md) |
| `rendu/ambiance` | [ambiance](docs/rendu/ambiance/backlog_ambiance.md) |
| `rendu/spatial` | [modèle spatial & vue](docs/rendu/spatial/backlog_spatial.md) |
| `vegetal/allelopathie` | [allélopathie](docs/vegetal/allelopathie/backlog_allelopathie.md) |
| `vegetal/catalogue` | [catalogue](docs/vegetal/catalogue/backlog_catalogue.md) |
| `vegetal/croissance` | [croissance](docs/vegetal/croissance/backlog_croissance.md) |
| `vegetal/floraison` | [floraison](docs/vegetal/floraison/backlog_floraison.md) |
| `vegetal/genetique` | [génétique](docs/vegetal/genetique/backlog_genetique.md) |
| `vegetal/grimpantes` | [grimpantes & luxuriance](docs/vegetal/grimpantes/backlog_grimpantes.md) |
| `vegetal/sante` | [santé](docs/vegetal/sante/backlog_sante.md) |
| `champs/sol` | [pistes de génération de terrain](docs/champs/sol/backlog_generation_terrain.md) |
| `rendu/pixelart` | [pistes rendu pixel-art](docs/rendu/pixelart/backlog_pixelart.md) |
| `meta` | [archives + idées longue traîne](docs/meta/backlog_historique.md) |

## Kickoffs de dette dormante — `sprints/dette_kickoffs/`

> Écrits le 2026-06-06 : **un kickoff autosuffisant par dette sans sprint** (les
> dettes C# ont déjà les leurs : sprint_1/2/3/4). Carte + ordre recommandé + choix
> de design à trancher dans **`sprints/dette_kickoffs/00_index.md`**.

| Dette | Kickoff |
|---|---|
| D13 — Magazine de botanique | `sprints/dette_kickoffs/D13_magazine_botanique.md` |
| D14 — Carnet auto | `sprints/dette_kickoffs/D14_carnet_auto.md` |
| D15 — Extension du terrain par maîtrise | `sprints/dette_kickoffs/D15_extension_terrain.md` |
| D12.2 — Table palier→déblocage (après D13/D14/D15) | `sprints/dette_kickoffs/D12_2_table_deblocage.md` |
| D18 — Pages secrètes | `sprints/dette_kickoffs/D18_pages_secretes.md` |
| D19 — Organes comestibles (manger) | `sprints/dette_kickoffs/D19_organes_comestibles.md` |
| D23 — Catalogue d'arbres pérennes étendu | `sprints/dette_kickoffs/D23_catalogue_arbres.md` |
| D26 — Diversification écologique | `sprints/dette_kickoffs/D26_diversification_ecologique.md` |
| D30 — Champ structure/compaction du sol | `sprints/dette_kickoffs/D30_structure_compaction_sol.md` |
| D32 — Optimisation du LightField (perf) | `sprints/dette_kickoffs/D32_optim_lightfield.md` |
