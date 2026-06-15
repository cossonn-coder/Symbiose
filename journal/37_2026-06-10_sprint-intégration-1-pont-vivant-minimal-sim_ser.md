## 2026-06-10 — Sprint Intégration·1 : pont vivant minimal `sim_server.py` ↔ `SimBridge.cs`

Première tranche du sprint Intégration (Option B) : **le tube est prouvé côté
Python**. Le moteur tourne en sous-process et dialogue en JSON ligne-délimité,
maître/esclave strict (Godot envoie, Python répond — jamais de message spontané).

**Livré.** `tools/sim_server.py` (adaptateur stdlib pure : importe le moteur
comme `main.py`, zéro modification de logique → **golden intact par
construction**, vérifié `16a1b937…`). Protocole v0 : `init(seed,config)` →
`engine_version` + monde statique (tuiles + maison) ; `step_week`/`snapshot` →
snapshot (horloge + plantes vivantes : `tile`, `species`, `x_cm`/`y_cm` locaux,
`stage`, `height_cm`, segments via `structure_to_dict()` — le format
Croissance·6, pas un 2ᵉ schéma) ; `quit`/EOF → arrêt propre ; commande
malformée → `ok:false` et le serveur survit. `tests/test_sim_server.py` :
**20/20** dont **déterminisme** (2 runs même seed → réponses byte-identiques).
Côté C# : `core/SimBridge.cs` (`System.Diagnostics.Process`, pipes redirigés
sauf stderr → tracebacks visibles dans la console Godot ; API synchrone +
`SmokeTest()`) ; toggle `RunSimBridgeTest` dans `TileGrid._Ready`.

**Décision : snapshot complet VALIDÉ, pas de diffs** (question ouverte du
kickoff tranchée par la mesure) : ~51 Ko/snapshot à l'an 5 sur 2 tuiles
(le bois domine, ~250 o/segment, borné `MAX_SEGMENTS`) ; extrapolé 8 tuiles
≈ 200 Ko pour 1 snapshot/60 s réel — négligeable.

**Décisions secondaires.** `ENGINE_VERSION="0.1.0"` locale au serveur (à
centraliser au sprint save global) ; `init` réutilise la fabrique du golden
(`build_world`, monde smoke 2 tuiles — complet en tranche 2) ; `week` snapshot
= compteur moteur brut ; ceinture `redirect_stdout(stderr)` autour du tick
(stdout réservé au protocole).

**Statut.** Tranche 1 **CLOSE** — confirmée par Nico dans Godot le jour même
(F5 → moteur lancé, semaine 5 / printemps, 17 plantes vivantes listées, arrêt
propre ; GTX 950M / Compatibility). Le visuel à l'écran reste l'ancienne démo
(tuiles opaques + spécimens `structure.json`) — c'est l'objet de la tranche 2
« monde statique rendu » (D2/D3/D8), kickoff `02_*.md` à écrire.

---
