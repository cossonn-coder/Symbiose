# Sprint UI voix narratives — état partagé

> **Conception FIGÉE** → source de vérité = `docs/narration/voix/conception_voix_narratives_ui.md`
> (la lire d'abord ; elle-même s'appuie sur `docs/narration/voix/conception_voix_narratives.md`, le doc
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
| ① | Pont : 3 hooks maîtrise + révélation page palier + 4 commandes read-only + verbe `acheter_magazine` | `01_pont.md` | ✅ fait (pont `0.5.11`, golden intact) |
| ② | `SimBridge` C# (1 méthode/commande) + nœud `VoicePanel` + hub-maison cliquable (non-voix grisées) | `02_ossature_ui.md` | ✅ fait (`dotnet build` vert, golden intact) |
| ③ | Panneau Carnet (filtrable par concept) + panneau Encyclopédie (index → fiche N1/N2/N3) | `03_carnet_encyclopedie.md` | ✅ fait (`dotnet build` vert, golden intact) |
| ④ | Panneau Pages (coffret grenier) + panneau Magazine (offres → fiche → achat bout-en-bout) | `04_pages_magazine.md` | ✅ fait (`dotnet build` vert, golden intact) |
| F5 | Validation visuelle Godot (hub, 4 panneaux, achat) | — | ⬜ Nico |

## §REPRISE
**SPRINT MOTEUR/UI TERMINÉ — reste F5 Nico.** Tous les tronçons ①→④ sont clos ;
la seule case restante est la validation visuelle Godot (F5), que Nico seul peut
faire (Godot n'est pas sur la VM).

**④ CLOS** (C# pur, couche vue). Livré :
- `world/PagesPanel.cs` : spécialisation Pages — lecteur PUR du coffret grenier
  (`Bridge.Pages()` → `pages` = list {id, voix, concept, texte} dans l'ORDRE du
  corpus). En-tête « voix · concept » (registre éditorial), corps VERBATIM en
  italique (crochets échappés `[`→`[lb]`). Aucune révélation déclenchée (robinet
  « récompense » au palier = côté pont ①). Vide → message neutre. 42 LDC 🟢.
- `world/MagazinePanel.cs` : spécialisation Magazine — offres (`MagazineOffres()`)
  ↔ fiche produit (`MagazineFiche` = {espece, niveau_max, niveaux}, VERBATIM) ↔
  ACHAT bout-en-bout via `AcheterMagazine` (verbe `acheter_magazine`, chemin
  Vigueur unique Q3). Le pont gate offre + fonds : succès → offre retirée +
  Vigueur du bilan rafraîchie + feedback ; refus → message sobre, aucune mutation.
  La vue ne pré-valide RIEN. Bandeau Vigueur affiché après le 1er achat (info
  primaire = HUD, D54). 139 LDC 🟢.
- `world/WorldView.Hub.cs` : switch `OuvrirVoicePanel` étendu (`magazine`→
  `MagazinePanel`, `pages`→`PagesPanel`).

`dotnet build Symbiose.csproj` (racine) = **vert** (0 err / 0 warn). Golden
`ae445d3f…` **INTACT** (aucun Python touché). F5 = Nico.

---
**③ CLOS** (C# pur, couche vue). Livré :
- `world/VoicePanel.cs` : point d'extension `Remplir()` (virtual, appelé en fin
  d'`Ouvrir`) + `Bridge` (protected) injecté par `InjecterPont()`. Le panneau de
  base garde son placeholder « à venir » (Magazine/Pages, jusqu'au ④).
- `world/CarnetPanel.cs` : spécialisation Carnet — sélecteur de concept
  (`OptionButton`, liste = concepts présents lus du carnet complet, ordre ledger
  préservé + « (tous) ») → re-appelle `Bridge.Carnet(filtreConcept)` (le PONT
  filtre). Entrées VERBATIM ; registre `interprétatif` → italique BBCode
  (crochets du verbatim échappés `[`→`[lb]`, aucun texte modifié).
- `world/EncyclopediePanel.cs` : spécialisation Encyclopédie — index (`index` du
  pont, un bouton/espèce) ↔ fiche (`fiche` = {espece, niveau_max, niveaux}),
  niveaux 1..niveau_max VERBATIM (clés JSON "1"/"2"/"3"), titres de rubrique
  N1/N2/N3 = étiquettes de mise en page (pas des voix). `fiche=null` → message
  neutre, pas de crash. Bouton « ◀ Retour à l'index ».
- `world/WorldView.Hub.cs` : `OuvrirVoicePanel(titre, fonction)` instancie la
  spécialisation (`carnet`→`CarnetPanel`, `encyclopedie`→`EncyclopediePanel`,
  autres→`VoicePanel` base), injecte `_bridge` avant `Ouvrir`.

`dotnet build Symbiose.csproj` = **vert** (0 err / 0 warn). Golden `ae445d3f…`
**INTACT** (aucun Python touché). Fichiers ③ tous 🟢 (70-93 LDC). F5 = Nico.

**④ FAIT** (voir §REPRISE en tête) — plus de tronçon restant, reste F5 Nico.

---
**② CLOS** (C# pur, couche vue). Livré :
- `core/SimBridge.cs` : **une méthode par commande voix** — `Carnet(filtreConcept)`,
  `Encyclopedie(espece)`, `Pages()`, `MagazineOffres()`, `MagazineFiche(espece)`,
  `AcheterMagazine(espece)` (passe par `Action("acheter_magazine", …)`, chemin
  Vigueur unique Q3). Verbatim, zéro reformulation (194 LDC = 🟢).
- `world/VoicePanel.cs` : nœud réutilisable, `CanvasLayer` plein écran,
  **pause-aware** (mémorise `GetTree().Paused`, restaure à la fermeture),
  `ProcessMode=Always`, squelette titre + zone défilante `Contenu` + bouton
  Fermer. Contenu vide (« à venir ») — ③④ le peupleront.
- `world/WorldView.Hub.cs` (partial) : maison cliquable (`ClicSurMaison` teste
  l'empreinte via `ScreenToWorld`) → menu **5 fonctions** ; Carnet / Encyclopédie /
  Magazine / **Pages du grenier** actives (ouvrent un `VoicePanel` titré) ;
  Atelier / Semis intérieur / Foyer **grisés « (à venir) »** (D54). Un seul menu /
  un seul panneau à la fois.
- `world/WorldView.Controls.cs` : clic gauche teste la maison AVANT `TryAction`.

`dotnet build Symbiose.csproj` = **vert** (0 err / 0 warn). Golden `ae445d3f…`
**INTACT** (aucun Python touché). F5 visuel = Nico (Godot pas sur la VM).

**PROCHAIN = ③** (`03_carnet_encyclopedie.md`) : panneau Carnet (liste filtrable
par concept) + panneau Encyclopédie (index → fiche N1/N2/N3). Lire `CLAUDE.md` +
ce fichier + `03_carnet_encyclopedie.md` ; `dotnet build` = filet C#.

---
**① CLOS** (pont `0.5.11`, golden `ae445d3f…` INTACT, 219/219 pont + toutes suites
vertes). Ce qui a été livré côté Python (`tools/simserver/`) :
- **Chaîne de maîtrise** dans un module dédié `maitrise_pont.py` : hook A
  `observer` (espèces vivantes post-tick + concepts eau/lumière/météo/pollinisation
  lus du log via `evenements`), hook B `detecter` (crédit de palier), révélation
  page « récompense » au palier 3. Branchée dans `cmd_step_week` après `consigner`,
  avant `log.clear()`. Hook C `noter_geste` dans `cmd_action` (`_noter_geste_maitrise`,
  résout la zone (tile,r,c) depuis {r,c} ou {x_cm,y_cm}).
- **4 commandes read-only** dans `VoixMixin` (`voix.py`) : `carnet`/`encyclopedie`/
  `pages`/`magazine`, ajoutées au dispatch de `server.py`. Verbatim, zéro synthèse.
- **Verbe `acheter_magazine`** dans `_do_action` (chemin Vigueur unique,
  `result.achete` + bilan rafraîchi).
- Test = section 18 `tests/simserver/voix.py` (registrée dans `test_sim_server.py`).

⚠️ **Effet de bord ANNONCÉ** (design correct, pas un bug) : la chaîne crédite de
VRAIS paliers ⇒ `vigueur_max` monte (palier_bonus) et `cout_action` remise les
coûts. 5 assertions de coût ABSOLU des suites pont (actions/taille/planter) ont été
rendues ROBUSTES (débit = `cost` annoncé, ratio urgence 1.5, régen « ≥ +10 »).
`actions.py` = **359 LDC** (bande 🟡 vigilance, une seule responsabilité) — scission
possible plus tard (extraire le helper hook-C).

Reliquats HORS sprint = **D54** (HUD primaire philo #5, page d'accueil pictos,
notifs temps réel, robinets pages hasard/fouille + marqueurs bouture/oiseau/vent,
entrées hub Atelier/Semis/Foyer, corpus encyclo paliers 4-5).
