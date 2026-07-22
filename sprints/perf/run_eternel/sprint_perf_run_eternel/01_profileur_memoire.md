# Tronçon ① — Profileur mémoire par catégorie + colmatage

> Kickoff autosuffisant. Lire d'abord `CLAUDE.md` (racine) + `00_etat.md` (ce dossier) +
> `docs/perf/run_eternel/conception_perf_run_eternel.md` §2/§7. Lancement depuis `data/code/`.

## Objectif
**Prouver la cause du crash mémoire** avant tout correctif. Le monde complet (8 tuiles)
plante après quelques années ; Nico soupçonne une fuite « indépendante des plantes ».
Cette hypothèse doit être **prouvée ou réfutée** par un profil mémoire **par catégorie
d'objets** sur ~12 ans / 8 tuiles. PUIS, si (et seulement si) une catégorie croît
**linéairement indépendamment de N** (nombre de plantes), la **borner** (cap/FIFO/prune)
sans changer le comportement (golden intact).

## Livrable
`tools/profile_memoire.py` — outil LECTURE SEULE, déterministe, exécutable :
`python3 -m tools.profile_memoire [annees] [tuiles]` (défaut 12 ans, 8 tuiles).

### Ce que l'outil fait
1. Construit le monde complet **8 tuiles** (pas le smoke 2 tuiles). S'inspirer de
   `tools/profile_tick.py` (`_build_engine` avec `build_world` du golden) mais avec la
   config « full » 8 tuiles. Regarder comment `tools/simserver/commands.py` construit le
   monde `config="full"` (20×20 m) pour répliquer la même fabrique.
2. Ticke année par année (`engine.tick_semaine()` × 52). À intervalles réguliers (ex.
   chaque année), échantillonne la mémoire **PAR CATÉGORIE** via un comptage explicite
   d'objets (`gc.get_objects()` filtré par type, ou compteurs ciblés). Catégories à
   suivre au minimum :
   - **plantes** vivantes + squelettes (`tile.plants`) ;
   - **segments** de structure (somme des `PlantStructure`/`Segment`) ;
   - **seedbank** : taille cumulée des dicts `species[r][c]` et `data[r][c]` (nombre
     d'entrées, pas la densité) ;
   - **grilles ecofields** (nombre de `GridField` × rows × cols — devrait être CONSTANT) ;
   - **journal des voix** (`game_state["journal"]`, entries) — devrait plafonner à 200 ;
   - **log** (`game_state["log"]`) — mesurer AVEC et SANS purge type serveur.
   Reporter aussi le RSS process (via `tracemalloc` ou `resource.getrusage`).
3. Imprime un **tableau** année × catégorie : ce qui croît linéairement saute aux yeux.
   Marque explicitement toute catégorie dont la croissance est **découplée de N plantes**
   (croît alors que N stagne) — c'est LA fuite recherchée.

### Suspects nommés (point de départ du diagnostic, à confirmer par les chiffres)
- **`SeedBank.species[r][c]`** : dict `classe → {density, genes}` par plot, alimenté par
  `add_species`. Il n'est peut-être **jamais purgé** des espèces à densité retombée à ~0
  → sur TOUS les plots (8 tuiles × centaines de plots) il tend vers ~27 espèces × GeneStat.
  Vérifier : la densité décroît (`decay`) mais l'ENTRÉE reste-t-elle dans le dict ? Si oui,
  c'est un accumulateur borné-mais-gros, candidat au RSS mesuré.
- **`SeedBank.data[r][c]`** (archétypes) : même question.
- Toute **liste appendée par tick** jamais purgée (grep `.append(` dans `fields/`, `sim/`
  hors `log`). Le `log` (`boucle.py:540`) EST purgé côté serveur (`commands.py:156`) — le
  vérifier, ne pas le recompter comme fuite.

## Colmatage (CONDITIONNEL — seulement si le profil révèle une fuite indépendante de N)
Si une catégorie croît linéairement **sans** que N croisse, la borner avec le **même
patron que le reste du moteur** (cf. `sim/journal.py` FIFO, `_elaguer` segments) :
- dict seedbank par plot : **purger l'entrée** d'une espèce dont la densité (et le poids
  GeneStat) est retombée sous un epsilon → l'entrée disparaît, le pool féral « oublie »
  une espèce éteinte localement (biologiquement juste : une graine trop vieille meurt).
- liste non bornée : cap FIFO ou fenêtre glissante.
Le colmatage **DOIT préserver le golden bit-à-bit** : la purge ne touche que des entrées
**inertes** (densité ~0, déjà sans effet sur les tirages). Le vérifier
(`python3 -m tests.test_golden` → hash inchangé). Si le colmatage bouge le golden, c'est
qu'il retire quelque chose d'ACTIF → revoir le seuil, ne PAS re-figer.

## Golden attendu
**INTACT** — hash `061934db09ad646a01f19b8f4d0b677f13438e87bce2f8531527be425e7c22a8`.
L'outil est lecture seule ; le colmatage ne borne que de l'inerte. Vérifier en fin de
tronçon : `python3 -m tests.test_golden`.

## Ce qu'il NE faut PAS faire
- Ne PAS toucher la logique du tick (croissance, lumière, succession) — ce tronçon est
  diagnostic + colmatage inerte.
- Ne PAS borner la population des plantes ici — c'est le tronçon ③ (émergent).
- Ne PAS lancer `test_epaisseur_500ans` (interdit projet — long, inutile).
- Ne PAS introduire de RNG ni changer un ordre d'itération.

## Fin de tronçon
Mettre à jour `00_etat.md` : ce que le profil a PROUVÉ (nom de la fuite ou « pas de fuite
indépendante de N → le RSS suit N, donc ③ suffira »), colmatage éventuel appliqué, golden
confirmé intact. Commit. Ce résultat CONDITIONNE la lecture du crash pour la suite.
