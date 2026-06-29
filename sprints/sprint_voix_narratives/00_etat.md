# Sprint VOIX NARRATIVES — état partagé

> **Conception FIGÉE** → source de vérité = `docs/conception/CONCEPTION_VOIX_NARRATIVES.md`
> (la lire d'abord, §0→§8). Ce fichier = état léger + carte des sous-sprints, mis à
> jour en fin de **chaque** tronçon. Boucle projet : `0N` → coder → vérifier golden
> (doit rester INTACT) → MAJ ce fichier → commit → `/clear` → `0N+1`.

## En une phrase
On implémente en **Python pur** les 4 voix narratives (carnet, encyclopédie, pages
secrètes, magazine) comme **lecteurs read-only** par-dessus un **ledger d'événements
partagé** (`sim/journal.py`), lui-même alimenté **hors tick** par le driver — donc le
**golden écologique reste INTACT à chaque tronçon** (zéro effet dans le tick).

## Invariant GOLDEN (vaut pour TOUS les tronçons)
- `tests/test_golden.py` (smoke `tests/golden_hash.txt`) **et** `tests/population_hash.txt`
  **doivent rester bit-identiques** du début à la fin. Le golden tourne le moteur
  *sans joueur* → aucune clé `journal`/`pages` → no-op strict (miroir de `maitrise`/
  `vigueur`). **Si le golden bouge, c'est un BUG (fuite dans le tick), STOP** — ne
  jamais re-figer.
- `tests/test_maitrise_detection.py` doit aussi rester **vert** après ① (refactor pur).

## Décisions structurantes (détail dans le doc)
- **Substrat = ledger partagé** : un seul flux d'`Evenement` typés parsé depuis le
  `log` du tick. Extraction de `_evenements()` (`sim/maitrise_detection.py`) vers un
  module commun **`sim/evenements.py`** (① refactor pur).
- **État joueur opt-in** : `gs["journal"][player]={"entries":[…],"resume":{…}}` et
  `gs["pages"][player]=set(...)`. Pas de joueur ⇒ pas de clé ⇒ no-op golden.
- **Point d'entrée hors tick** : `journal.consigner(gs, player, log, semaine)` appelé
  par le DRIVER **après** `tick_semaine()` et **avant** que le serveur ne vide le log
  (`tools/simserver/commands.py::cmd_step_week`, ~L132-133). `engine` ne l'importe
  JAMAIS.
- **Encyclopédie 3 niveaux** sur paliers 1/2/3 (A) ; **carnet** bascule interprétatif
  au **palier 3 du concept** (B, `SEUIL_CARNET=3`) ; **magazine** sœurs au **palier 3
  famille** (C). Tout lit l'état `maitrise` déjà implémenté (`sim/maitrise.py`).
- **Pages = lore pur, ZÉRO effet mécanique**, 3 robinets (hasard/récompense/fouille).

## Carte des sous-sprints (6, ordre = dépendances)
| # | Sujet | Kickoff | État |
|---|-------|---------|------|
| ① | Extraire `sim/evenements.py` (refactor pur) + élargir le parseur | `01_evenements.md` | ✅ FAIT |
| ② | Ledger `sim/journal.py` + `consigner` + câblage driver | `02_journal.md` | ✅ FAIT |
| ③ | Carnet (`carnet_lire`, `CONCEPT_DE`, gabarits 2 registres) + D43 | `03_carnet.md` | ✅ FAIT |
| ④ | Encyclopédie (`encyclopedie_index`/`_lire`, fiche tronquée) | `04_encyclopedie.md` | ✅ FAIT |
| ⑤ | Pages secrètes (`pages_trouvees`/`reveler_page`, 3 robinets) | `05_pages.md` | ✅ FAIT |
| ⑥ | Magazine (`magazine_offres`/`acheter_au_magazine`) | `06_magazine.md` | ⬜ à faire |

Dépendances : ① avant tout ; ② dépend de ① ; ③④⑤⑥ dépendent de ② mais sont
indépendants entre eux (déroulés en série pour un golden vérifié à chaque cran).

## Conventions
- Source de vérité = Python `data/code/`. Lancement depuis `data/code/`
  (`python3 main.py`, `python3 -m tests.test_golden`, `python3 -m tests.test_population`,
  `python3 -m tests.test_maitrise_detection`).
- Couches : `evenements`/`journal` sont au niveau `sim`, AU-DESSUS du tick (comme
  `maitrise_detection`, `vigueur`). `engine`/`fields`/`plants` ne les importent jamais.
- **Corpus = livrable éditorial** (doc §5/§6/§7) : recopier fidèlement les gabarits/
  fiches/pages du doc dans des modules de données Python. Ne pas réinventer le texte.
- Placeholders calibrage → **D12.4** : `JOURNAL_MAX=200`, `COUT_MAGAZINE` (élevé),
  `SEUIL_CARNET=3`. Knobs nommés en tête de module.
- Tout garder (scripts de mesure inclus). Un fichier à la fois sauf synchro cohérente
  avant commit. Français + commentaires pédagogiques au cœur des fichiers.

## Hors périmètre (renvoyé, cf. doc §4)
UI Godot des 4 voix (coffret grenier, kiosque magazine, pages du carnet) = **dette
D24** ; protocole pont/commandes serveur pour exposer ces lectures à Godot = D24 aussi ;
D15 (extension terrain) ; calibrage numérique D12.4 ; marqueurs rares bouture/oiseau/
vent (robinet *hasard* s'ancre provisoirement sur `_hash_noise` au passage de saison).

## Avancement / REPRISE

**① FAIT** (refactor pur, golden INTACT) :
- Créé `data/code/sim/evenements.py` (module PUR, niveau `sim`, 119 ldc) : type
  partagé `Evenement(kind, tile_id, pos, espece, cause)` + **deux API** :
  - `_evenements(log)` — déplacé TEL QUEL depuis `maitrise_detection` (kinds
    `avance/stagne/repro`), ré-importé par `maitrise_detection` → comportement
    inchangé (choix : NE PAS renommer les kinds historiques, sinon `detecter()` +
    `test_maitrise_detection[8]` cassent ; refactor strictement pur).
  - `evenements(log) -> list[Evenement]` — NOUVEAU, élargi pour le carnet ② :
    kinds `germination/stagnation/reproduction/mort/nouaison/abscission/ravageur`.
- `maitrise_detection.py` : regex/`_CLE_DE_NOM`/`_raison_stagnation`/`_evenements`
  RETIRÉS (déplacés), réimport `from sim.evenements import _evenements`.
  `_CLE_DE_CLASSE` reste (naturalisation férale).
- Élargissements parseur : **`🌊 noyé`** (stagnation, absente de l'ancien parseur),
  morts `🪦` (sénescence/asphyxie) + `✗` (conflit), `🍎 Nouaison`, `🍂 Abscission`,
  `🐛` ravageur (aléa sans pos/espèce). **Disambiguation** 🍂 (Abscission ≠
  Nécromasse/Chute fruit), 🍎 (Nouaison ≠ header Récolte), ❄ (stagne froid ≠
  header gel).
- **TODO nommés** (pas de marqueur source dans le log → non parsés, conforme
  kickoff) : `floraison` (header `🌸` seul, pas de ligne per-plante), `acclimatation`
  (signe de rendu `sim/semiologie.py`, jamais émis au log), mort `gel`/annual/
  monocarpie (cause non distinguable proprement). À brancher si le moteur émet
  un jour ces marqueurs.
- Tests : `tests/test_evenements.py` NOUVEAU (18/18 — parité historique +
  kinds élargis + disambiguation). `test_maitrise_detection` 20/20 vert.
  **Golden `db5e7c66…` + population `9ba39ab7…` bit-identiques** (inchangés).

**② FAIT** (ledger hors tick, golden INTACT) :
- Créé `data/code/sim/journal.py` (module niveau `sim`, ~50 ldc) : `JOURNAL_MAX=200`
  (knob D12.4 en tête), `ensure_player(gs, player)` OPT-IN (miroir de
  `maitrise.ensure_player_maitrise`), `consigner(gs, player, log, semaine)` qui lit
  `evenements.evenements(log)` (① élargi) et appende des entrées
  `{semaine, zone, kind, cause, espece}`. `zone = (tile_id, r, c)` ou `(tile_id,)` si
  l'événement n'a pas de pos (ravageur de saison). Bornage `_appender` : au-delà de
  `JOURNAL_MAX`, la plus ancienne se replie dans `resume[(kind, cause)] += 1` (FIFO).
  PUR : aucun RNG, aucun champ écolo touché.
- Câblage driver `tools/simserver/commands.py::cmd_step_week` : import
  `from sim import journal as J` ; appel `J.consigner(gs, gs["current_player"],
  gs["log"], gs["week"] - 1)` APRÈS `tick_semaine()` et AVANT `gs["log"].clear()`.
  `week` est déjà incrémenté par le tick (boucle.py:422) → la semaine simulée est
  `week - 1`. Le serveur a déjà un joueur (`current_player="joueur_1"`) → ledger se
  remplit en jeu réel ; golden hors serveur → aucune clé `journal` → intact.
- Tests : `tests/test_journal.py` NOUVEAU (15/15 — opt-in no-op, accumulation datée +
  isolation par avatar, bornage→resume). `test_evenements` 18/18, `test_maitrise_detection`
  20/20 verts. **Golden `db5e7c66…` + population `9ba39ab7…` bit-identiques** (inchangés).

**DÉCISION `detecter` : NON câblé** (choix assumé, signalé à Nico). `maitrise_detection.detecter`
a la même signature que `consigner` et irait au même endroit (trivial à brancher), MAIS
ce n'est PAS neutre côté gameplay : il crédite des preuves et fait progresser les paliers
en jeu réel, ce qui pilote ensuite carnet/encyclopédie/magazine. C'est une décision D12
que Nico doit prendre sciemment, pas un effet de bord du tronçon « ledger ». Le golden
n'est pas concerné (tourne hors serveur), donc rien ne presse. À trancher quand Nico veut
activer la progression de maîtrise en F5.

**③ FAIT** (carnet, lecteur read-only, golden INTACT) :
- Créé `data/code/sim/carnet.py` (niveau `sim`, 128 ldc) : `carnet_lire(gs, player,
  filtre=None)` → liste d'entrées `{semaine, zone, concept, registre, texte}` dans
  l'ordre du ledger. PUR (lecture `journal` ② + `maitrise.palier` D12, aucun RNG,
  aucun champ écolo). Sans tranche journal → `[]` (golden-safe).
- Tables recopiées VERBATIM du doc §5 : `CONCEPT_DE[(kind, cause)]` (§5.0, incl.
  D43 `acclimatation→adaptation`) + `GABARIT[(kind, cause, registre)]` (§5.1, les
  2 colonnes descriptif/interprétatif). Knobs en tête : `SEUIL_CARNET=3`,
  `SEUIL_ANTICIPE=1` (D12.4).
- **Registre = palier du CONCEPT** (pas de l'espèce, décision B), recalculé À LA
  CONSULTATION (révélation rétroactive). Réglage d'aide « interprétatif anticipé »
  lu via flag OPTIONNEL `gs["options"][player]["carnet_anticipe"]` (défaut NON,
  TODO(options) pour le menu réel).
- **Décisions/écarts assumés** (signalés) : (a) cas spécial « levée (reprise) » →
  concept = SA cause (`_CONCEPT_LEVEE`, doc §5.0 « = cause levée ») ; reproduction
  (3 causes auto/biparental/introgr.) → même concept+gabarit (cause neutralisée).
  (b) Slot `{l}` = libellé FACTUEL « sur T0 en (r,c) » dérivé de la zone, PAS un
  « coin nord-est » (géométrie tuile hors périmètre ③, l'UI Godot D24 enjolivera).
  (c) Paire (kind,cause) hors table → `CONCEPT_FALLBACK="observation"` + gabarit
  générique (jamais de crash, kickoff « Pièges »). (d) `acclimatation`/`floraison`
  jamais émis par le parseur ① (signe de rendu / header sans @pos) → gabarits
  présents mais déclenchés par injection directe dans les tests (corpus éditorial
  complet, prêt si le moteur émet un jour ces marqueurs).
- Tests : `tests/test_carnet.py` NOUVEAU (19/19 — sans joueur→[], bascule registre
  au palier 3 du concept, espèce≠concept, réglage anticipé, D43, filtre concept/
  zone/saison). `test_golden` + `test_population` bit-identiques (`db5e7c66…` /
  `9ba39ab7…`), `test_maitrise_detection` 20/20. C# non concerné.

**④ FAIT** (encyclopédie, lecteur read-only, golden INTACT) :
- Découpage DONNÉE / LOGIQUE (un fichier = une responsabilité) :
  - Créé `data/code/sim/encyclopedie_corpus.py` (DONNÉE pure, 200 ldc, aucun import
    moteur) : `FICHES[espèce] = {1: N1, 2: N2, 3: N3}` — **28 fiches × 3 niveaux**
    recopiées VERBATIM du doc §6 (N1 silhouette / N2 biologie / N3 écosystémique).
    Dépassement éventuel du seuil toléré car corpus éditorial (CLAUDE.md « garde-fou,
    pas dogme ») — ici 200 < 350 de toute façon.
  - Créé `data/code/sim/encyclopedie.py` (LOGIQUE, 18 ldc pur) : `encyclopedie_index(
    gs, player) -> list[espèce]` (palier ≥ 1, tri stable = ordre du corpus) +
    `encyclopedie_lire(gs, player, espèce) -> {espece, niveau_max, niveaux}` tronquée
    à `min(palier, NIVEAU_MAX=3)` (décision A figée : paliers 4/5 NE débloquent PAS de
    N4). Palier 0 → `None` ; sans joueur/maîtrise → `[]`/`None`. PUR (lit
    `maitrise.palier` D12, n'écrit RIEN, aucun RNG, aucune clé créée → no-op golden).
- **Alignement des clés VÉRIFIÉ** : les 28 clés du corpus = EXACTEMENT les 28 espèces
  catalogue (`PLANT_CATALOGUE` 23 + `PERENNIAL_CATALOGUE` 5), bijection testée.
- Tests : `tests/test_encyclopedie.py` NOUVEAU (18/18 — sans joueur→[]/None, troncature
  1/2/3 + plafond 4/5→3, palier 0 absent/None, bijection clés↔catalogue, 3 niveaux non
  vides par fiche). `test_golden` + `test_population` bit-identiques (`db5e7c66…` /
  `9ba39ab7…`), `test_maitrise_detection` 20/20, `test_carnet` 19/19 (régression voisine).
  **C# non concerné** (aucun `.cs`, protocole pont inchangé — exposition Godot = D24).

**⑤ FAIT** (pages secrètes, lore pur ZÉRO effet mécanique, golden INTACT) :
- Découpage DONNÉE / LOGIQUE (un fichier = une responsabilité) :
  - Créé `data/code/sim/pages_corpus.py` (DONNÉE pure, aucun import moteur) :
    `PAGES[id] = {id, titre, voix, concept, palier_theme, robinet, texte}` — **20
    pages P01..P20** recopiées VERBATIM du doc §7 (5 voix A→E, pastiche en style).
    + `ORDRE` (ids dans l'ordre du corpus, tri stable). Titres extraits dans `_TITRES`.
  - Créé `data/code/sim/pages.py` (LOGIQUE pure) : `ensure_player` opt-in (set vide),
    `pages_trouvees(gs, player) -> set` (lecture pure, ne crée aucune clé →
    no-op golden), `reveler_page(gs, player, robinet, contexte) -> id|None` — **3
    robinets** : *récompense* (`contexte["concept"]` → 1ʳᵉ page DUE de ce concept),
    *fouille* (1ʳᵉ page due GLOBALE), *hasard* (`_hash_noise(seed, semaine, _SALT_PAGE,
    0)` ∈ [0,1] → index dans le pool des dues, DÉTERMINISTE). « Due » = non trouvées
    triées `palier_theme` croissant (stable sur `ORDRE`). Épuisable → `None`.
    Robinet inconnu → `None` (jamais de crash). SEULE écriture = ajout au set.
- **Décisions/écarts assumés** (signalés) : (a) signature réelle `_hash_noise(seed,
  week, r, c)` prend 4 ENTIERS ; le doc écrit `_hash_noise(seed, semaine, "page")` —
  la chaîne `"page"` devient un SALT constant `_SALT_PAGE=0x9A6E5` (canal dédié,
  décorrélé des guildes/carpophores, miroir de `_SALT_CARPOPHORE`). (b) `contexte`
  porte `{"concept": …}` (récompense) ou `{"seed": …, "semaine": …}` (hasard) ;
  ignoré pour *fouille*. (c) Sérialisation `set ↔ list` au save JSON = TODO D24 (save
  pas encore câblé, juste documenté). (d) Robinet *hasard* tire dans le pool des
  DUES (trié) → même seed+semaine+même état ⟹ même page (philo #3). PAS branché au
  driver/serveur (ni *récompense* via `detecter`, ni *fouille* via action grenier) :
  c'est event-driven, le câblage = D24 / décision Nico (cf. note `detecter` non
  câblé du ②). Aucun appel ⇒ aucune clé `pages` ⇒ golden no-op.
- Tests : `tests/test_pages.py` NOUVEAU (47/47 — sans joueur→set()/aucune clé,
  récompense par concept + ordre palier_theme + épuisé→None, fouille globale +
  épuise 20, hasard DÉTERMINISTE + épuisable, jamais de re-révélation, ZÉRO effet
  mécanique vérifié sur gs jouet, corpus 20 entrées champs complets). `test_golden`
  + `test_population` bit-identiques (`db5e7c66…` / `9ba39ab7…`), `test_maitrise_detection`
  20/20. **C# non concerné** (aucun `.cs`, protocole pont inchangé — exposition Godot = D24).

**PROCHAIN = ⑥** (`06_magazine.md`) : magazine de botanique (`magazine_offres`/
`acheter_au_magazine`, sœurs au palier 3 famille décision C, numéro saisonnier,
`vigueur.spend(COUT_MAGAZINE)` → `PlayerSeedBank.add`). Event-driven hors tick.
Golden INTACT.
