# ④ Vue Godot — gènes lisibles, lignées, banc F5 `lignees`

> Lire d'abord : `CLAUDE.md`, `00_etat.md`, puis
> `docs/vegetal/genetique/conception_genetique_infinitesimale.md` §7.
> Golden attendu : **INTACT** (pont, voix et vue seulement).

## Objectif
Que Nico **voie** la génétique : dispersion des plantes, lignées fixées contre populations
mélangées, et (en debug) les valeurs dans leur unité.

## À faire
1. **Pont** (`tools/simserver/serialize.py` ≈ l. 249 exporte `genes`) : ajouter `F` par
   plante et, une fois par snapshot (pas par plante), la table des unités des caractères.
   Lecture pure. Incrémenter `ENGINE_VERSION` (`tools/simserver/version.py`) avec sa note.
   Le golden ne voit pas le pont : comparer le snapshot JSON avant/après sur un monde
   (mémoire « refactor du pont : golden aveugle »).
2. **Survol de debug, touche G** (`world/WorldView.Genes.cs`) : afficher chaque caractère dans
   son unité (« levée −2,1 °C », « floraison +1 sem. », « autofécondation 93 % ») et la
   lignée (« lignée fixée » si F ≥ 0.75, « lignée mélangée » si F ≤ 0.25, sinon « en voie de
   fixation »). Le survol reste un **outil de debug** (philo #5).
3. **Voix** : concept « lignée » dans l'encyclopédie (corpus `sim/encyclopedie_corpus/
   concepts.py`) et le carnet (concept + `CONCEPT_DE`, cf.
   `docs/narration/voix/conception_voix_narratives.md`). Le carnet note quand le joueur
   **sème une graine qu'il a récoltée** (si l'événement existe déjà, l'enrichir ; sinon un
   marqueur au geste `planter` d'une graine à lignée). Descriptif sous le palier,
   interprétatif au palier de maîtrise du concept.
4. **Banc F5 `lignees`** (registre `data/code/bancs/`, patron d'un banc existant, ex.
   `bancs/diversite.py`) : une tuile, une rangée de tomates et une de courgettes nées de
   plusieurs générations (pré-calcul déterministe au banc), plus une rangée de basilics semés
   depuis le pool. Le banc forcé ouvre le survol G.
5. **`dotnet build Symbiose.csproj`** vert. **Capture VM** (`tools/capture_vm.sh`) du banc,
   **regarder les PNG**, planche dans `planche/` du sprint.
6. **Recette F5** dans `00_etat.md` : ce que Nico doit voir (tomates qui se ressemblent,
   courgettes dispersées, survol en unités).
7. **Clôture du sprint** : `DETTE.md` D139 (sprint ① clos côté code), `BACKLOG.md`, entrée
   `journal/` + pointeur `journal.md`.

## Ne PAS faire
- Toucher au moteur (`data/code/plants`, `fields`, `sim`) sauf les corpus de voix.
- Afficher des chiffres hors du survol de debug.
- Ne jamais lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.

## Fin de tronçon
Sprint CLOS côté code, F5 attendu. `00_etat.md` §REPRISE = recette F5. Commit, puis
enchaîner sur `sprint_niche_thermique`.
