# CONCEPTION — UI Godot des voix narratives (D24 · brique voix)

> **Conception FIGÉE** le 2026-07-01 (skill `/conception`, phase B). Aucun code
> touché à la rédaction. Ce doc est la **source de vérité** du sprint
> `sprint_voix_narratives_ui` (kickoffs `sprints/sprint_voix_narratives_ui/`).
>
> **Amont** : le MOTEUR des 4 voix est **100 % fait en Python** (sprint VOIX
> NARRATIVES ①→⑥, 2026-06-29, golden `db5e7c66…` intact) — `sim/journal.py`
> (ledger), `sim/carnet.py`, `sim/encyclopedie.py`, `sim/magazine.py`,
> `sim/pages.py` + corpus. Source moteur : **`docs/narration/voix/conception_voix_narratives.md`** (à
> lire d'abord). Ce doc-ci ne conçoit QUE la **couche présentation** : commandes du
> pont + panneaux Godot de consultation + la **chaîne de maîtrise** qui alimente les
> voix.

---

## 0. Cadrage (arbitré avec Nico, sessions 1-2)

| # | Question | Décision |
|---|---|---|
| Périmètre | Que fait ce sprint ? | **Brancher les 4 voix sur le pont + UI de consultation.** Rien d'autre. |
| Q1 | Maîtrise : quoi câbler ? | **Chaîne complète 3 hooks** (observer + detecter + noter_geste), cf. §1 |
| Q2 | Déclencheur d'ouverture | **Hub-maison cliquable d'emblée** (clic maison → menu 5 fonctions) |
| Q3 | Achat magazine | **Via `cmd_action`** (verbe `acheter_magazine`, chemin Vigueur unique) ; lecture = commandes read-only |
| A | Menu hub | Carnet / Encyclopédie / Magazine / Pages **actifs** ; Atelier / Semis / Foyer **grisés « à venir »** (→ dette) |
| B | Révélation des pages | **Robinet « récompense » au palier** (atteindre palier 3 → `reveler_page(robinet="récompense", {concept})`). Hasard/fouille = dette |

**HORS sprint (versés en dette D54)** : refonte du HUD primaire (philo #5),
page d'accueil pictogrammes, notifications temps réel en saison, robinets
`hasard`/`fouille` des pages + marqueurs `bouture`/`oiseau`/`vent`, corpus
encyclopédie paliers 4-5.

---

## 1. INVARIANT — téléonomie / « Godot bête »

**À graver dans CHAQUE kickoff.** L'UI restitue le texte des voix **verbatim**
depuis Python. **AUCUNE synthèse, aucun conseil, aucune phrase générée côté C#.**
Le registre est une responsabilité du **corpus Python** :

- encyclopédie + carnet = voix **naturaliste téléonomique** (décrit ce qui EST,
  n'attribue pas d'intention) ;
- pages secrètes = voix **téléologique assumée** (lore, « la plante cherche la
  lumière ») — mais c'est le corpus qui le porte, pas le renderer.

Concrètement : un panneau prend une `list`/`dict` renvoyée par le pont et
l'affiche. Il ne concatène jamais deux champs en une phrase, ne reformule pas, ne
trie pas « intelligemment ». Le seul travail C# = **mise en page** (listes,
onglets, défilement, filtre par clé exacte).

---

## 2. La chaîne de MAÎTRISE (tronçon ①) — 3 hooks dans le pont

Sans maîtrise, les voix restent **muettes** : encyclopédie/magazine/carnet
interprétatif sont tous gatés par un palier ≥ 1 (découverte) ou ≥ 3 (interprétatif
/ sœurs du magazine). Câbler `detecter()` **seul** ne suffit pas — `detecter()` ne
crédite que des objets **déjà découverts**. Il faut les **3** hooks. Tous vivent
dans le pont `data/code/tools/simserver/`, jamais dans le tick moteur (golden
intact).

### Hook A — `observer` (découverte, après tick)
`observer(gs, player, objet)` — façade de `sim/actions/progression.py`, **exportée
par `sim.actions`** → `decouvrir` 0→1 + gain Vigueur. À appeler après chaque
`step_week` :
- **espèces** : sur chaque espèce d'une plante VIVANTE du monde post-tick
  → débloque la fiche encyclopédie niveau 1 ;
- **concepts** : à la 1ʳᵉ observation du phénomène — stagnation `sec`→`eau`,
  `ombre`→`lumière`, `froid`→`météo` (mapping `CONCEPT_PAR_STAGNATION` de
  `maitrise_detection`), reproduction `biparental`→`pollinisation`.

### Hook B — `detecter` (crédit de succès, après tick, avant `log.clear()`)
`detecter(gs, player, log, semaine)` (`sim/maitrise_detection.py:153`, renvoie
`[(objet, palier)]`) — appelé juste à côté de `consigner()` (`commands.py:143`),
**après le tick, avant que le log soit vidé**. Lit le même `log` en lecture seule →
ordre indifférent vs `consigner`. C'est lui qui fait monter les paliers (donc
ouvre le niveau 2/3 des fiches, les sœurs du magazine, le carnet interprétatif).

### Hook C — `noter_geste` (imputation, dans `cmd_action`)
`noter_geste(gs, player, semaine, zone)` — appelé dans `cmd_action` (`actions.py`)
avec `zone=(tile_id, r, c)` du plot agi, pour que `detecter` **impute** au joueur la
levée d'une stagnation ou une reproduction provoquée par son geste.

### Déjà câblé — NE PAS refaire
- `marquer_replante` (dans le tick, `succession.py:158`, germination) ;
- `consigner()` (`commands.py:143`, alimente le ledger).
- Convention : `semaine` consignée = `gs["week"] - 1` (le tick a déjà incrémenté).

### Révélation des pages au palier (micro-déc. B)
Quand `detecter` renvoie un objet atteignant le **palier 3**, appeler
`reveler_page(gs, player, robinet="récompense", contexte={"concept": <objet>})`.
Seul robinet de ce sprint (hasard/fouille → D54).

---

## 3. Signatures des 4 voix (read-only sauf achat) — commandes du pont

Toutes ces fonctions EXISTENT (vérifiées le 2026-07-01). Les commandes du pont ne
font que les appeler et sérialiser le retour.

**Carnet** (`sim/carnet.py`) :
- `carnet_lire(gs, player, filtre=None)` → `list[{semaine, zone, concept,
  registre, texte}]` ; `filtre` = `{"concept"|"zone"|"saison"}`.

**Encyclopédie** (`sim/encyclopedie.py`) :
- `encyclopedie_index(gs, player)` → `list[str]` (espèces palier ≥ 1, ordre corpus) ;
- `encyclopedie_lire(gs, player, espece)` → `{espece, niveau_max(1..3),
  niveaux:{n:texte}}` ou `None`.

**Magazine** (`sim/magazine.py`) :
- `magazine_offres(gs, player, saison=None)` → `list[str]` (sœurs palier ≥ 3 hors
  banque ; `saison` inactif, TODO catalogue) ;
- `magazine_fiche(espece)` → `{espece, niveau_max, niveaux}` (**PAS de gs/player**) ;
- `acheter_au_magazine(gs, player, espece, saison=None)` → `bool` (gate offre →
  `vigueur.spend(COUT_MAGAZINE=120)` → `bank.add`).

**Pages** (`sim/pages.py`) :
- `pages_trouvees(gs, player)` → `set` ;
- `reveler_page(gs, player, robinet, contexte=None)` → `id|None` ;
- corpus `pages_corpus.PAGES` : `id → {voix, concept, palier_theme, robinet,
  texte}` ; `ORDRE`.

---

## 4. Le pont (mécanique vérifiée)

- `server.py:25` = dict **`dispatch`** (`init`/`step_week`/`snapshot`/`action`/
  `fields`/`list_bancs`) → **ajouter ici** les commandes read-only
  `carnet`/`encyclopedie`/`pages`/`magazine`. Framing : 1 ligne JSON = 1 réponse,
  `flush` obligatoire.
- `cmd_action` (`actions.py:31`) : `verb`/`target`/`params` → `{ok, result,
  snapshot}`. `bilan()` renvoie déjà `vigueur`/`vigueur_max` → support idéal du
  verbe **`acheter_magazine`** (chemin Vigueur unique, Q3). L'achat passe par
  `acheter_au_magazine` (mute Vigueur + banque) puis renvoie un `bilan`-like.
- `CommandsMixin` (`commands.py`) importe déjà `journal as J` ; ajouter imports
  `carnet`/`encyclopedie`/`magazine`/`pages` + `from sim.actions import observer` +
  `from sim import maitrise_detection`.
- **Bump `ENGINE_VERSION`** (`tools/simserver/version.py`) : commandes neuves =
  protocole étendu. Golden **intact** (le pont vit hors du golden hors-serveur ; le
  moteur n'est pas touché).

---

## 5. Architecture C# (couche vue)

- `core/SimBridge.cs` : pipe stdin/stdout synchrone, 1 requête en vol,
  `Request(GDict)`. Méthodes existantes Init/StepWeek/GetSnapshot/Action/Fields/
  ListBancs → **ajouter une méthode par commande voix**.
- HUD actuel : `world/WorldView.Hud.cs` (provisoire, « sautera au sprint UI »).
  Maison = placeholder `Polygon2D` (D4). **Pas encore de système de panneaux** → le
  sprint en pose un.
- **Nœud `VoicePanel` réutilisable** : `CanvasLayer` plein écran, **pause-aware**
  (consultation en temps figé — cohérent avec la boucle hybride : on lit le carnet
  la partie en pause). Un panneau = un onglet/contenu, alimenté par une méthode
  `SimBridge`.
- **Hub-maison cliquable** (Q2) : clic sur la maison → menu 5 fonctions.
  Carnet/Encyclopédie/Magazine/Pages actifs ; Atelier/Semis/Foyer **grisés
  « à venir »** (micro-déc. A → dette D54).

---

## 6. Découpage FIGÉ — 4 tronçons + F5

Chaque tronçon est **autosuffisant** (démarrage à froid). Golden **intact** partout
(pont opt-in joueur hors golden ; C# = couche vue). Golden de réf = celui du jour
du sprint.

- **① Pont (Python `tools/`)** : les **3 hooks** maîtrise (observer / detecter /
  noter_geste) + révélation page robinet « récompense » au palier ; commandes
  read-only `carnet`/`encyclopedie`/`pages`/`magazine` ; verbe `cmd_action`
  `acheter_magazine`. Test = script pont JSON (init → quelques `step_week` →
  interrogation des 4 voix + achat). Bump `ENGINE_VERSION`. Golden intact.
- **② `SimBridge` C# + ossature UI** : une méthode `SimBridge` par commande voix ;
  nœud `VoicePanel` réutilisable (CanvasLayer plein écran, pause-aware) ;
  hub-maison cliquable (menu 5 entrées, non-voix grisées). `dotnet build` vert.
  Panneaux encore vides (branchés au ③④).
- **③ Panneau Carnet + panneau Encyclopédie** : Carnet = liste filtrable par
  concept (verbatim, 2 registres selon le palier — déjà décidé côté Python) ;
  Encyclopédie = index → fiche N1/N2/N3. `dotnet build` vert.
- **④ Panneau Pages + panneau Magazine** : Pages = coffret du grenier, voix
  multiples (affichage verbatim du corpus) ; Magazine = offres → fiche → **achat
  bout-en-bout** via `cmd_action acheter_magazine` (Vigueur débitée, graine ajoutée
  à la banque, `bilan` rafraîchi). `dotnet build` vert.
- **F5 final = Nico** (Godot pas sur la VM ; les tronçons C# sont validés au
  `dotnet build`, le F5 visuel reste manuel).

---

## 7. Ce que le sprint NE fait PAS (→ dette D54)

- HUD primaire diégétique (philo #5) — reste barres/texte provisoires.
- Page d'accueil pictogrammes silencieux (premier lancement).
- Notifications temps réel pendant la saison (hiérarchisées).
- Pages : robinets `hasard` (seed, semaine) et `fouille` + marqueurs
  d'événements rares `bouture`/`oiseau`/`vent` au ledger.
- Menu hub : entrées Atelier / Semis intérieur / Foyer (Vigueur) — grisées ici.
- Corpus encyclopédie paliers 4-5 (expertise / transcendant).
- `magazine_offres(saison=…)` : filtre saisonnier inactif (TODO catalogue).

Ces reliquats sont regroupés sous **D54** ; ce sprint clôt la **brique voix** de
**D24** et solde la partie « UI » de D12.5 / D13 / D14 / D18 / D43.
