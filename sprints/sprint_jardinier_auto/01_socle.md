# ① Socle du jardinier automate

> Kickoff autosuffisant. Lire d'abord `CLAUDE.md` + `00_etat.md` +
> `docs/conception/CONCEPTION_JARDINIER_AUTOMATE.md`. Lancer depuis `data/code/`.

## Objectif
Poser le **paquet `tools/jardinier_auto/`** et sa **boucle de décision** en 5
étapes (percevoir → diagnostiquer → proposer → prioriser → exécuter), invoquée
**entre deux ticks** côté appelant. Câbler **deux gestes seulement** (`arroser`,
`recolter`), perception `omniscient`, tutelle = plantes cultivées. Poser le
**journal minimal** et les **verrous de déterminisme**.

## Invariant (à ne JAMAIS violer)
L'automate n'est **jamais** appelé depuis `tick_semaine`. Il s'intercale APRÈS
`engine.tick_semaine()`, côté appelant. Le moteur ne change pas d'une ligne.
→ **golden `tests/test_golden.py` INTACT (bit-identique)**.

## Fichiers à CRÉER (paquet, un fichier = une responsabilité, ≤ 300 LDC)
- `tools/jardinier_auto/__init__.py` — ré-exporte l'API publique (`ProfilAutomate`,
  `JardinierAutomate`, presets `LIBRE`/`BRIDE`).
- `tools/jardinier_auto/profil.py` — dataclass `ProfilAutomate` (frozen) avec les
  6 axes du §4 de la conception + presets `LIBRE`/`BRIDE`. **Tous les axes présents
  dès ①** même si seuls certains sont lus ici (les autres tronçons les câbleront).
- `tools/jardinier_auto/perception.py` — profil `omniscient` : fonctions pures qui,
  pour une plante, lisent `plant.vitalite`, `maturite(plant)`,
  `eco.humidite.at_plot(*plant.position)`, `eco.light_received(plant)`,
  `qi_local(plant, eco)`. `semiologique` = stub levant `NotImplementedError`
  (câblé au ⑦).
- `tools/jardinier_auto/diagnostic.py` — `facteur_limitant(percept) -> str|None` :
  renvoie le facteur dominant. En ① deux facteurs suffisent : `"hydrique"` (humidité
  basse) et `"organe_mur"` (maturité pleine / présence de fruits mûrs). Seuils =
  constantes nommées en tête de fichier (calibrage post-test).
- `tools/jardinier_auto/regles.py` — liste ORDONNÉE de règles priorisées. En ①,
  deux règles : `hydrique → arroser`, `organe_mur → recolter`. Une règle =
  `(nom_facteur, verbe, sélecteur_cible, priorité)`.
- `tools/jardinier_auto/execution.py` — traduit un geste choisi en appel
  `sim.actions.*` (import `from sim import actions as ACT`). Câble UNIQUEMENT
  `arroser(gs, player, eco, r, c)` et `recolter(gs, player, plant, eco)`.
- `tools/jardinier_auto/trace.py` — journal minimal : `consigner(entry)` +
  structure d'entrée `{semaine, tile_id, cible, facteur_limitant, geste, resultat}`.
  Stocké sous `game_state["automate_journal"]` (liste). Sérialisable JSON.
- `tools/jardinier_auto/boucle.py` — classe `JardinierAutomate(profil)` avec
  `jouer_tick(engine)` : parcourt `engine.tiles` puis `tile.plants` (listes,
  déterministe), filtre les cultivées sous tutelle, diagnostique, propose, priorise
  (tri stable, clé de départage `(tile_id, plant.y_cm, plant.x_cm)`), exécute,
  consigne.

## Modèle / points précis
- **Tutelle cultivées** : une plante est cultivée si son attribut le marque. Vérifier
  le champ réel (`plant.cultive` ou équivalent posé par `planter`/succession —
  chercher dans `plants/base/` et `maitrise_detection.marquer_replante`). Si aucun
  attribut fiable n'existe, se rabattre sur « toutes les plantes vivantes » ET le
  **signaler dans `00_etat.md`** comme point à durcir (ne PAS inventer d'attribut).
- **Perception `omniscient`** : lecture pure, aucune écriture de champ.
- **`arroser`/`recolter`** : signatures exactes dans `sim/actions/gestes.py`.
  `arroser(gs, player, eco, r, c, urgence=False)` ; `recolter(gs, player, plant,
  eco)` renvoie un ratio ∈ [0,1]. `player = game_state["current_player"]`.
- **Profil ① = `LIBRE`** par défaut (paie_vigueur=False → pas de contrainte de
  budget ; les gestes restent appelés normalement, la Vigueur du joueur peut passer
  négative — c'est le mode libre, borné au ③). `part_recoltee` non encore appliqué
  (câblé ②) → récolte simple.

## Appelant de test (headless)
- Créer `tools/bancs/automate_demo.py` : monte un petit monde (réutiliser le patron
  de `main.py` ou d'un banc existant type `diag_population`), instancie
  `JardinierAutomate(LIBRE)`, boucle `for _ in range(N): engine.tick_semaine();
  automate.jouer_tick(engine)`, imprime le journal. **N'imprime PAS 500 ans** — une
  poignée d'années suffit.

## Verrous de déterminisme (tests — CRÉER `tests/test_automate_determinisme.py`)
1. **Golden intact** : `python3 -m tests.test_golden` → hash INCHANGÉ (l'automate
   n'est pas branché dans le golden). C'est le test décisif de H2.
2. **Rejeu identique** : deux instances neuves du même monde + même profil, jouées
   N ticks → **même hash d'état final** (ou même sérialisation du journal).
3. **Automate OFF = golden** : vérifier qu'importer le paquet et ne pas l'appeler ne
   change rien (aucun effet de bord à l'import).

## Golden attendu
**INCHANGÉ, bit-identique.** Si le golden bouge, c'est un bug (fuite dans le tick) —
annuler, ne jamais re-figer.

## Ce qu'il NE faut PAS faire
- NE PAS toucher `sim/`, `fields/`, `plants/`, `world/`, `engine/` (le moteur).
- NE PAS créer de geste. NE PAS appeler l'automate depuis le tick.
- NE PAS câbler pailler/tailler/deraciner/objectifs/impasses (tronçons suivants).
- NE PAS introduire de RNG. NE PAS lancer `test_epaisseur_500ans`.
- NE PAS dépasser 300 LDC par fichier (scinder si besoin).

## Vérif de sortie
`python3 -m tests.test_golden` (intact) + `python3 -m tests.test_automate_determinisme`
(vert) + `python3 -m bancs.automate_demo` (tourne, journal lisible). Mettre à jour
`00_etat.md` (§REPRISE : ① fait, attribut de tutelle réel utilisé, prochain = ②).
