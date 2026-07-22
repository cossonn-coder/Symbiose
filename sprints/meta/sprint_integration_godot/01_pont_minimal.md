# Tranche 1 — Pont vivant minimal (`sim_server.py` ↔ `SimBridge.cs`)

> **Kickoff autosuffisant.** Lire d'abord `00_etat.md` (conception actée Option B).
> But de la tranche : **prouver le tube** — Python tourne en sous-process, Godot
> lui parle, une semaine de simulation avance et un snapshot revient. Aucun rendu
> joli ici (c'est la tranche 2). Ampleur : **moyen** (2 fichiers neufs + 1 test).

## 📖 Pédagogie — ce qu'on construit et pourquoi ça marche

**Un sous-process avec pipes, c'est un UART logiciel.** Godot lance
`python3 tools/sim_server.py` comme processus enfant et garde deux tuyaux :
`stdin` (Godot → Python) et `stdout` (Python → Godot). C'est exactement le
schéma carte-mère ↔ microcontrôleur sur liaison série : un lien point à point,
fiable, ordonné. Pas de socket, pas de port réseau, rien à configurer — l'OS
fournit le transport.

**JSON ligne-délimité = framing par délimiteur.** Sur un flux série, il faut
savoir où une trame s'arrête. Ici le délimiteur est `\n` : **1 ligne = 1 message
JSON complet**. Côté Python, `for line in sys.stdin:` ; côté C#,
`ReadLine()`. Pas de longueur préfixée, pas d'échappement à gérer (JSON
n'émet jamais de `\n` littéral dans une chaîne sérialisée compacte). Débuggable
au clavier : on peut taper les commandes à la main.

**Maître/esclave strict.** Godot est **maître** : il envoie une commande, attend
LA réponse, puis continue (protocole requête/réponse synchrone, comme SPI).
Python ne parle **jamais** spontanément → pas de concurrence, pas de
réordonnancement, déterminisme préservé. Si un jour la sim doit pousser des
événements, on ajoutera un champ `events` DANS la réponse, pas un canal séparé.

**Pourquoi Python n'est pas modifié.** Le serveur est un **adaptateur** : il
importe le moteur (comme `main.py` ou `tests/test_golden.py` le font) et expose
ses fonctions. Si Godot a besoin d'une donnée absente, on l'ajoute **au
snapshot** (lecture), jamais à la logique du tick → golden intact par
construction.

## Protocole v0 (à figer dans cette tranche)

Requête (1 ligne) → réponse (1 ligne). Champ `cmd` obligatoire.

```json
→ {"cmd": "init", "seed": 42}
← {"ok": true, "engine_version": "...", "world": {...statique : tuiles, maison, layout...}}

→ {"cmd": "step_week"}
← {"ok": true, "snapshot": {...état hebdo...}}

→ {"cmd": "snapshot"}
← {"ok": true, "snapshot": {...}}

→ {"cmd": "quit"}
← {"ok": true}
```

- **Erreur** : `{"ok": false, "error": "message lisible"}` — le serveur ne
  crashe jamais sur une commande malformée (il répond et continue).
- `engine_version` dès le v0 (même philosophie que le save JSON).
- **Snapshot v0 minimal** (sobre, on étoffera tranche par tranche) : `week`,
  `year`, `season`, et par plante vivante : `species`, `x_cm`, `y_cm`, `stage`,
  `height_cm` + la **structure de segments** via `structure_to_dict()` (déjà
  livrée au tronçon Croissance·6 — on réutilise, on n'invente pas un 2ᵉ format).
  Le schéma plante reprend celui de `tools/export_structure.py` →
  `structure.json` (continuité avec `PlantStructure.cs` qui sait déjà le lire).

## Livrables

1. **`data/code/tools/sim_server.py`** (Python, stdlib pure) :
   - Boucle `for line in sys.stdin` → `json.loads` → dispatch → `print(json.dumps(...), flush=True)`.
   - ⚠️ **`flush=True` obligatoire** (sinon la réponse reste dans le buffer et
     Godot attend indéfiniment — le piège n°1 des pipes).
   - ⚠️ **`stdout` réservé au protocole** : tout print de debug du moteur doit
     aller sur `stderr` (vérifier que le moteur ne print pas sur stdout pendant
     un tick ; s'il le fait, rediriger pendant l'appel).
   - `init` construit le monde **comme le golden smoke test** (réutiliser la
     même fabrique : 2 tuiles d'abord, le monde complet 8 tuiles + maison
     viendra en tranche 2 si trop lourd à valider d'un coup — défaut sobre).
2. **`data/code/tests/test_sim_server.py`** (golden du pont) :
   - Lance le serveur en `subprocess`, joue `init(seed) → step_week ×N →
     snapshot`, vérifie : réponses bien formées, semaine qui avance, et
     **déterminisme** (2 runs même seed → snapshots identiques).
   - Commande malformée → `ok:false` et le serveur survit.
3. **`core/SimBridge.cs`** (C#, namespace `Symbiose`) :
   - `System.Diagnostics.Process` (`RedirectStandardInput/Output`,
     `UseShellExecute=false`) — PAS `OS.Execute` (bloquant, pas de dialogue).
   - API : `Init(seed)`, `StepWeek()`, `GetSnapshot()` — **synchrones** pour
     cette tranche (un `await`/thread viendra quand l'UI devra rester fluide).
   - Parse via `Json.ParseString` (cohérent avec `PlantStructure.cs`).
   - Chemin du process : `python3` + chemin absolu dérivé de
     `ProjectSettings.GlobalizePath("res://data/code/tools/sim_server.py")`
     (le binaire gelé remplacera ce couple en tranche 6 — un seul point à
     changer).
4. **Preuve visible côté Godot** (minimal assumé) : un nœud de test (scène ou
   bouton dans `TileGrid`) qui fait `Init → StepWeek ×4 → GetSnapshot` et
   `GD.Print` le résumé (semaine, nb plantes). **Pas de rendu** — le tube
   d'abord.

## Critères de succès (vérifiables)

- [ ] `python3 -m tests.test_sim_server` vert (dont déterminisme 2 runs).
- [ ] `python3 -m tests.test_golden` **inchangé** (`16a1b937…`) — le moteur
      n'a pas bougé.
- [ ] Test au clavier : `python3 tools/sim_server.py` puis coller les commandes
      JSON à la main → réponses correctes.
- [ ] Nico, dans Godot : F5 → la console affiche le résumé après 4 semaines
      (compilation C# à confirmer par Nico, pas de `dotnet` ici).

## Points ouverts (défaut sobre + signaler)

- **Taille du snapshot complet** : à **mesurer** ici (octets/semaine) — c'est
  la donnée qui tranchera « complet vs diffs » (cf. 00_etat). Pas d'optimisation
  avant mesure.
- **Monde du `init`** : smoke (2 tuiles) ou complet (8 + maison) ? Défaut :
  paramètre `config` du `init`, smoke par défaut dans le test, complet pour
  Godot si le timing le permet.
- **Arrêt propre** : si Godot meurt sans `quit`, Python doit mourir aussi
  (détecter EOF sur stdin → exit). À couvrir dans le test.

## Boucle de travail (rappel)

Travailler → tests + golden verts → mettre à jour `00_etat.md` (tranche 1 ✅ +
décisions prises + mesure de taille du snapshot) → **entrée `journal.md`** →
commit → `/clear` → tranche 2.
