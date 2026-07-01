# Sprint UI voix narratives — état partagé

> **Conception FIGÉE** → source de vérité = `docs/conception/CONCEPTION_VOIX_NARRATIVES_UI.md`
> (la lire d'abord ; elle-même s'appuie sur `CONCEPTION_VOIX_NARRATIVES.md`, le doc
> MOTEUR). Ce fichier = état léger + carte des sous-sprints, mis à jour en fin de
> **chaque** tronçon. Boucle projet : `0N` → coder → golden → MAJ ce fichier →
> commit → `/clear` → `0N+1`.

## En une phrase
Le MOTEUR des 4 voix est **100 % fait en Python** (`sim/journal.py`, `carnet.py`,
`encyclopedie.py`, `magazine.py`, `pages.py` + corpus, golden `db5e7c66…` du sprint
VOIX). Il reste à **le rendre jouable** : brancher les 4 voix sur le **pont** (+ la
chaîne de maîtrise qui les alimente) et poser la **couche de présentation Godot**
(hub-maison cliquable + panneaux de consultation).

## INVARIANT — téléonomie / « Godot bête » (graver dans CHAQUE tronçon)
L'UI restitue le texte des voix **verbatim** depuis Python. **AUCUNE synthèse /
conseil / phrase générée côté C#.** Le registre (naturaliste téléonomique pour
encyclopédie+carnet ; téléologique assumé pour les pages) est porté par le **corpus
Python**. Le C# ne fait que de la **mise en page** (listes, onglets, défilement,
filtre par clé exacte).

## Décisions structurantes (détail dans le doc de conception §0-§5)
- **Q1 maîtrise = chaîne complète 3 hooks** (`observer` découverte + `detecter`
  crédit palier + `noter_geste` imputation). Câbler `detecter` SEUL est insuffisant
  (il ne crédite que le DÉJÀ découvert → voix muettes sans `observer`).
- **Q2 = hub-maison cliquable d'emblée** (clic maison → menu 5 fonctions).
- **Q3 = achat magazine via `cmd_action`** (verbe `acheter_magazine`, chemin
  Vigueur unique) ; toute LECTURE = commandes pont read-only.
- **Micro-A** : menu hub Carnet/Encyclopédie/Magazine/Pages actifs ;
  Atelier/Semis/Foyer **grisés « à venir »** (→ D54).
- **Micro-B** : pages révélées par robinet **« récompense »** au palier 3
  (`reveler_page(robinet="récompense", {concept})`). Hasard/fouille → D54.
- **Golden INTACT partout** : le pont vit hors du golden hors-serveur (opt-in
  joueur) ; le C# est une couche vue ; le tick moteur n'est PAS touché. Golden de
  réf du sprint = **`ae445d3f a2df9b8d95b45f663552f75de113eb540ed9066e81eb8d034b1a8e3c`**.
- **Bump `ENGINE_VERSION`** au ① (commandes de pont neuves = protocole étendu).

## Faits VÉRIFIÉS dans le code (2026-07-01, base des kickoffs)
- Modules voix : `sim/carnet.py:237 carnet_lire`, `sim/encyclopedie.py:50/62
  encyclopedie_index/_lire`, `sim/magazine.py:85/126/160 magazine_offres/
  acheter_au_magazine/magazine_fiche`, `sim/pages.py:69/87 pages_trouvees/
  reveler_page`.
- Hooks maîtrise : `sim/actions/progression.py:28 observer` (exporté par
  `sim.actions`), `sim/maitrise_detection.py:98/110/153 noter_geste/marquer_replante/
  detecter`.
- Pont : `tools/simserver/server.py:25` dict `dispatch` ; `commands.py:143` =
  `consigner()` (log lu avant `log.clear()`, `J.` déjà importé) ; `actions.py:31
  cmd_action` (`bilan()` renvoie `vigueur`/`vigueur_max`).
- C# : `core/SimBridge.cs` (Init/StepWeek/GetSnapshot/Action/Fields/ListBancs),
  `world/WorldView.Hud.cs` (HUD provisoire), maison = placeholder `Polygon2D` (D4).

## Carte des sous-sprints (4 + F5, ordre = dépendance)
| # | Sujet | Kickoff | État |
|---|-------|---------|------|
| ① | Pont : 3 hooks maîtrise + révélation page palier + 4 commandes read-only + verbe `acheter_magazine` | `01_pont.md` | ⬜ à faire |
| ② | `SimBridge` C# (1 méthode/commande) + nœud `VoicePanel` + hub-maison cliquable (non-voix grisées) | `02_ossature_ui.md` | ⬜ à faire |
| ③ | Panneau Carnet (filtrable par concept) + panneau Encyclopédie (index → fiche N1/N2/N3) | `03_carnet_encyclopedie.md` | ⬜ à faire |
| ④ | Panneau Pages (coffret grenier) + panneau Magazine (offres → fiche → achat bout-en-bout) | `04_pages_magazine.md` | ⬜ à faire |
| F5 | Validation visuelle Godot (hub, 4 panneaux, achat) | — | ⬜ Nico |

## §REPRISE
Sprint NON commencé. Lire `CLAUDE.md` + ce fichier + `01_pont.md`, lancer
`python3 -m tests.test_golden` AVANT (doit afficher `ae445d3f…`), puis coder ①.
Reliquats HORS sprint = **D54** (HUD primaire philo #5, page d'accueil pictos,
notifs temps réel, robinets pages hasard/fouille + marqueurs bouture/oiseau/vent,
entrées hub Atelier/Semis/Foyer, corpus encyclo paliers 4-5).
