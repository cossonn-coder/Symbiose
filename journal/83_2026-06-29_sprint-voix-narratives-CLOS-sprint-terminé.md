# 2026-06-29 — Sprint VOIX NARRATIVES (①→⑥) — SPRINT TERMINÉ

> Exécution autonome `/sprint-auto sprints/sprint_voix_narratives` (orchestrateur
> + 6 sous-agents au contexte frais). Conception figée préalable = entrée 82 /
> `docs/conception/CONCEPTION_VOIX_NARRATIVES.md`. **Golden INTACT bit-identique
> sur TOUT le sprint** (`db5e7c66…`) — c'était l'invariant sacré du sprint :
> les 4 voix sont des **lecteurs read-only hors tick**, donc zéro effet écolo.

## En une phrase
On implémente en Python pur les 4 voix narratives (carnet, encyclopédie, pages
secrètes, magazine) comme lecteurs read-only par-dessus un ledger d'événements
partagé (`sim/journal.py`), alimenté **hors tick** par le driver — donc le
golden écologique reste INTACT.

## Tronçons clos

- **① `sim/evenements.py` (refactor pur)** — extraction de `_evenements()` +
  regex hors `maitrise_detection.py` vers un module `sim/` commun ; ajout du type
  `Evenement(kind, tile_id, pos, espece, cause)` et de la 2ᵉ API `evenements(log)`
  élargie pour le carnet (germination/stagnation/reproduction/mort/nouaison/
  abscission/ravageur, disambiguation 🍂/🍎/❄/🌊). **Choix** : conserver les kinds
  historiques (`avance/stagne/repro`) côté `_evenements` pour ne pas casser
  `detecter()` ni `test_maitrise_detection[8]` — les deux API partagent les regex.
  Golden `db5e7c66…` + population `9ba39ab7…` intacts, `test_maitrise_detection`
  20/20, `test_evenements` 18/18. TODO nommés : `floraison`/`acclimatation`/mort
  `gel/annual/monocarpie` pas encore émis par le parseur (pas de marqueur source).

- **② Ledger `sim/journal.py` + `consigner` câblé** — état joueur **opt-in**
  `gs["journal"][player]={"entries":[…],"resume":{…}}` (miroir de `maitrise`/
  `vigueur`), `JOURNAL_MAX=200` (D12.4), bornage FIFO repliant l'ancien dans
  `resume[(kind,cause)]`. Hook `consigner(gs, player, log, semaine)` câblé dans le
  DRIVER `tools/simserver/commands.py::cmd_step_week` **après** `tick_semaine()` et
  **avant** `log.clear()` ; semaine = `gs["week"]-1`. Sans joueur ⇒ pas de clé ⇒
  no-op golden. `test_journal` 15/15. **`detecter` (D12) laissé NON câblé** :
  signature jumelle, même emplacement, trivial — mais il fait progresser les
  paliers en jeu réel → décision **D12** que Nico doit prendre sciemment, pas un
  effet de bord du tronçon ledger (kickoff autorisait « si trivial sinon ne pas
  forcer »).

- **③ Carnet (`sim/carnet.py`)** — lecteur read-only `carnet_lire(gs, player,
  filtre)` → `{semaine, zone, concept, registre, texte}`. Table `CONCEPT_DE` +
  gabarits **2 registres** (descriptif au début / interprétatif au **palier 3 du
  concept**, `SEUIL_CARNET=3`, réglage anticipé `SEUIL_ANTICIPE=1` via flag
  options). D43 inclus (`acclimatation → adaptation`). Corpus §5 recopié verbatim.
  `test_carnet` 19/19, golden intact.

- **④ Encyclopédie (`sim/encyclopedie.py` + `encyclopedie_corpus.py`)** — fiche
  **3 niveaux** débloquée par palier 1/2/3 (basique → bio → effets écosystémiques),
  **tronquée** à `min(palier, 3)` ; palier 0 → `None`. `encyclopedie_index` trié
  ordre catalogue. Corpus §6 recopié verbatim, **bijection parfaite catalogue↔fiches**
  (23 cultivées + 5 pérennes = 28). Découpage propre données (200 ldc) / logique
  (18 ldc). `test_encyclopedie` 18/18, golden intact.

- **⑤ Pages secrètes (`sim/pages.py` + `pages_corpus.py`)** — lore pur, **ZÉRO
  effet mécanique**. État opt-in `gs["pages"][player]=set(...)`, `pages_trouvees`
  (lecture pure) + `reveler_page` à **3 robinets** : *récompense* (page due du
  concept de `contexte`), *fouille* (1ʳᵉ due globale), *hasard* (`_hash_noise`
  déterministe, canal dédié `_SALT_PAGE`). Épuisable → `None`. Corpus §7 recopié
  verbatim (P01..P20, 5 voix). `test_pages` 47/47, golden intact. Câblage
  event-driven au driver (récompense via `detecter`, fouille via action grenier)
  + sérialisation `set↔list` au save = **D24**.

- **⑥ Magazine (`sim/magazine.py`)** — 4ᵉ voix + 4ᵉ canal d'acquisition d'espèces.
  `magazine_offres(gs, player, saison)` = espèces **sœurs** des familles dont un
  membre est au **palier 3**, moins la banque joueur, tri stable, gate Vigueur.
  `acheter_au_magazine` = gate strict → `vigueur.spend(COUT_MAGAZINE=120)` payé en
  entier → `PlayerSeedBank.add(Seed)`. `magazine_fiche` réutilise le corpus de ④
  (niveau ≤ 2, argument de vente). Banque = `gs["player_seed_bank"]` (vérifié
  `main.py`/`simserver`), Vigueur = `gs["vigueur"][player]` ; écriture HORS TICK
  uniquement → golden + population intacts. Filtre `saison` accepté mais inactif
  (aucune fenêtre de semis dans `plants/` — pas de calendrier inventé). `test_magazine`
  23/23.

## Invariant tenu
Golden smoke `db5e7c660f040e4b084d0fbc76350d25b0dbd169edf15699619c5de9b3ce207f`
et population `9ba39ab7…` **bit-identiques de ① à ⑥** — aucun re-figeage, jamais.
Tests neufs : evenements 18/18, journal 15/15, carnet 19/19, encyclopédie 18/18,
pages 47/47, magazine 23/23 ; maitrise_detection 20/20 (refactor pur ① préservé).
C# non touché (les 4 voix vivent côté Python `sim/`, hors tick).

## Reste (renvoyé hors sprint)
- **D24** — UI Godot des 4 voix (coffret grenier, kiosque magazine, pages du
  carnet) + protocole pont pour exposer ces lectures à Godot + câblage event-driven
  de `reveler_page` (récompense/fouille) + sérialisation `set↔list` des pages au save.
- **D12** — câblage de `maitrise_detection.detecter` dans la boucle serveur (jumeau
  de `consigner`) : sans lui les paliers ne progressent pas en jeu réel, donc
  carnet/encyclopédie/magazine restent en mode initial. **Décision pour Nico.**
- **D12.4** — calibrage numérique (`JOURNAL_MAX`, `COUT_MAGAZINE`, `SEUIL_CARNET`).
- Marqueurs rares bouture/oiseau/vent + émission source de `floraison`/`acclimatation`
  (parseur ① prêt, gabarits carnet prêts, mais pas encore loggés au tick).
- Aucun point **F5** : tout est Python pur hors tick, aucune vue.
