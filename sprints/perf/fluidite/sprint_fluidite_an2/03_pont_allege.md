# ③ Pont allégé — un snapshot plus petit et plus vite écrit

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, le doc de conception.
**Golden** : intact (perception pure, hors tick). Version de pont incrémentée
(`ENGINE_VERSION` dans `data/code/tools/simserver/version.py`, + son historique ; les tests
`tests/simserver/*` qui vérifient la version suivent).

## Constat (HEAD `5c69ac6`, s81-91, graine 1521550718, `full`) [n=1 run]
- `_snapshot()` ≈ 183 ms an 2 ; réponse compacte ≈ 1,5 Mo ; parse JSON côté Godot 150-297 ms.
- Les **segments** font ~75 % du poids des plantes ; chaque segment porte `auxin` en flottant
  plein (ex. `0.41558888448000003`) que **la vue ne lit pas** (vérifié : aucune occurrence de
  `auxin` dans les `.cs` hors `.godot/`). `age_weeks` EST lu (`core/PlantStructure.cs:250`,
  lignification/maturité des feuilles) → à garder.
- Toutes les plantes changent de géométrie chaque semaine (> 1 cm pour 589/590) : **pas de
  delta par plante** (exclu par la conception).

## À faire
1. **Retirer `auxin` du snapshot seulement** : filtrer dans la sérialisation
   (`tools/simserver/serialize.py`, deux appels `structure_to_dict()` : plantes du sol l.~136,
   conteneurs l.~817). **Ne pas toucher `PlantInstance.structure_to_dict()`** (utilisé par
   `tests/test_croissance.py`, `tests/simserver/taille.py`, `tools/profile_monde.py`, la
   restauration de structure). Inventorier d'abord au `grep` tout lecteur de `"auxin"` dans
   les snapshots (tests, `sprints/**/mesures/*.py`, outils) et les adapter.
2. **Arrondir les flottants à la précision perceptible**, champ par champ, dans la
   sérialisation (positions cm à 0,1 ; directions à 1e-3 ; jauges [0,1] à 1e-3 — à justifier
   si autre). Vérifier qu'aucune comparaison côté vue/tests ne suppose la valeur pleine.
3. **Coût de `_snapshot()`** : re-profiler (cProfile sur `srv._snapshot()` seul, s90) et
   supprimer les recalculs (ex. perceptions recalculées pour chaque plante alors qu'elles
   dépendent du plot). `sort_keys=True` du `json.dumps` (`server.py:105`) : mesurer son coût ;
   ne le retirer que si aucun test ne compare des sorties textuelles.
4. Cible : **taille et temps de `_snapshot()` −40 %** [banc ①, n ≥ 3 runs].

## Ne PAS faire
- Changer la sémantique d'une clé lue par la vue, ou retirer une clé lue en C#.
- Toucher au moteur (`sim/`, `fields/`, `plants/`) ou au golden.

## Fin de tronçon
`python3 -m tests.test_sim_server` (et `tests/simserver/*`) verts ; golden intact ;
`dotnet build Symbiose.csproj` vert (lecture tolérante si une clé disparaît) ; mesures
consignées dans `00_etat.md` ; commit.
