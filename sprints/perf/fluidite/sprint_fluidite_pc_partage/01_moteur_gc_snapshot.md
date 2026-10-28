# ① Moteur bit-identique — ramasse-miettes + `_snapshot` mémoïsé

Lire d'abord : `CLAUDE.md`, `00_etat.md` de ce dossier,
`docs/perf/fluidite/conception_fluidite_pc_partage.md` §3-4.
**Golden INCHANGÉ** `fecccded…` (`cd data/code && python3 -m tests.test_golden`).
NE JAMAIS lancer `test_epaisseur_500ans`. Pas d'appel DeepSeek (kickoff complet).

## Objectif
Réduire le temps Python d'une semaine HORS formules : (a) ramasse-miettes, (b) `_snapshot`.
Aucun résultat de simulation ne doit changer.

## (a) Ramasse-miettes
- Mesure de départ (VM, s85-100, mode delta) [n=1 run] : 25-47 ms/semaine de GC, collecte
  gen2 toutes les ~7 semaines à 151-224 ms, ~200 k objets, seuils (2000, 10, 10). Script
  de mesure reproductible : enveloppe `gc.callbacks` (start/stop) autour de
  `srv.cmd_step_week({"delta": True})`, monde `full` graine 1521550718 — écris-le dans
  `data/code/tools/` (outil gardé, règle « conserver le code ») ou étends
  `tools/banc_cadence.py` d'une colonne `gc ms`.
- Levier : `gc.freeze()` une fois le monde monté (fin de `cmd_init`,
  `tools/simserver/commands.py:114`, ou juste après dans le serveur — **pas dans `sim/`**,
  le moteur reste pur) + seuil gen0 relevé (essaie 2000 → 20 000-50 000, garde la valeur
  mesurée la meilleure). Le réglage doit être actif dans `SimServer` piloté par
  `tools/banc_cadence.py` (il construit `SimServer` et appelle `cmd_init`).
- **Risque déterminisme vérifié AU CODE** : `sim/grimpe.py:87-101` trie avec `id(other)`
  comme départage ; `fields/light.py:209` indexe par `id(plant)` (lookup, sans risque).
  Les adresses dépendent de l'allocation, que le GC modifie. Le golden (in-process, sans
  le réglage serveur) NE suffit donc PAS : **compare l'état du monde servi** sur ≥ 40
  semaines `full` (graine 1521550718), réglage ON vs OFF, deux processus séparés
  (populations par espèce + hash JSON du snapshot complet chaque semaine). Si ça diverge :
  ne pas toucher `grimpe.py` dans ce tronçon (ce serait changer la sim) → renoncer au
  réglage qui diverge, consigner dans `00_etat.md` et en dette D116.

## (b) `_snapshot` (`tools/simserver/serialize.py:108`)
- 201-508 ms/semaine [VM, n=1 run]. **Profile d'abord DANS `_snapshot`** (cProfile sur
  ~5 semaines s90+, mode delta) : quels champs par plante coûtent (`leaf_symptoms`,
  organes/fruits, `segv.segments`, delta…).
- Levier : mémoïser l'entrée d'une plante (ou ses morceaux coûteux) avec une **clé
  auto-invalidante** dérivée de l'état déjà porté par l'instance (ex. semaine de dernière
  mutation, tuple des grandeurs lues) — jamais un drapeau « sale » à poser à la main dans
  `sim/`. Si le gros du coût exige de toucher `sim/` (piste notée en D116 :
  `leaf_symptoms` → `category_density` par plot), ne le fais que bit-identique et golden
  intact ; sinon consigne et passe.
- Le contenu de la réponse doit rester **identique à l'octet** : compare le JSON
  (`sort_keys`, séparateurs compacts) avant/après sur ≥ 20 semaines, modes complet ET
  delta. Lance aussi `tests/simserver/delta.py` (section 23) et les tests du pont.
- Cible −40 % du `_snapshot` ; si non tenue, rapporte le chiffre obtenu.

## Mesure de fin
`python3 -m tools.banc_cadence --runs 3 --semaines 104` avant/après (tick, snapshot, gc,
max par an) ; charge VM notée. Libellés de chiffres avec leur limite entre crochets.

## Ne PAS faire
Toucher une formule, l'ordre d'une addition, la population ; re-figer le golden ; changer
le protocole (pont reste 0.6.0) ; toucher C#.

## Fin de tronçon
`00_etat.md` (§① : avant/après, réglage GC retenu, gain `_snapshot`), commit.
