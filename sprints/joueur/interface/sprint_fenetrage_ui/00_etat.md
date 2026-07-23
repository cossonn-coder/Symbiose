# Sprint « fenêtrage UI » — état vivant

**Type/thème :** `joueur/interface` (nouveau thème).
**Nature :** pure vue C#/Godot (nuance : le filtre launcher PEUT toucher Python — voir Q3).
**Golden attendu :** INCHANGÉ sur tous les tronçons (aucune touche moteur).
**Statut :** FIGÉ 2026-07-23 — prêt pour `/sprint-auto`. Doc : `docs/joueur/interface/conception_fenetrage_ui.md`. Kickoffs : 01_launcher · 02_parametres · 03_panneau_onglets.

## Origine
Amorce Nico 2026-07-23, deux volets :
- **Volet A — launcher de bancs (hors-jeu)** : haut-gauche, défilable, filtrable, + bouton « Paramètres » ; règle transversale « toute fenêtre défile si débordement ».
- **Volet B — panneau de consultation (in-game)** : carnet/encyclo/magazine/pages/automate réunis à UN emplacement (celui de l'automate) en ONGLETS.

## Constats de code (lus le 2026-07-23)
- `WorldView.Selecteur.cs` — launcher actuel = `CanvasLayer`, panneau **CENTRÉ**, `OptionButton` (dropdown) full/smoke/propre + `_bridge.ListBancs()`, bouton Lancer. **Pas de scroll, pas de filtre, pas de bouton Paramètres.**
- `WorldView.Automate.cs` — panneau automate = `CanvasLayer` ancré **DROITE** (ColorRect pos (1142,100) size 772×872 sur écran 1920). `RichTextLabel` ScrollActive. **HUD LIVE** (lit le bloc `automate` du snapshot à chaque tick), touche A on/off, filtre catégories propre (F/Maj+F). N'est **PAS** un VoicePanel, **ne met PAS en pause**. Statut = **instrument de DEV** (même rang que F6), « pas une fonctionnalité de jeu ».
- `VoicePanel.cs` — `CanvasLayer` **CENTRÉ** (720×560), déjà un `ScrollContainer`. **PAUSE-AWARE** (met la sim en pause à l'ouverture, restaure à la fermeture). Spécialisations : CarnetPanel/EncyclopediePanel/MagazinePanel/PagesPanel/AtelierPanel (chacune surcharge `Remplir()`, lit via `Bridge`).
- `WorldView.Hub.cs` — clic maison → menu centré → `OuvrirVoicePanel(titre, fonction)` (un VoicePanel actif à la fois).
- `cmd_list_bancs` (commands.py) → `{"bancs": sorted(BANCS)}` = **noms seuls**, aucune catégorie/description. Les bancs sont regroupés par MODULE (climatique/edaphique/hydrologie/biotique/succession/…) mais ce thème n'est PAS exposé.
- **Options « Paramètres » : quasi aucune n'a de backend.** Réels/câblés aujourd'hui : `SecondsPerWeek` (Export), toggles debug (F6/F7 overlays, H fantôme maison, O ombres, I vie macro). Verbosité notifications / encyclopédie de démarrage / carnet anticipé = **conçues mais NON implémentées** (grep vide).

## Constats de conception (à trancher avec Nico)
- **D59 ABSORBÉE.** « Menu maison à droite » = exactement l'emplacement automate (x=1142, tiers droit). Volet B la réalise. → à confirmer, puis fermer D59.
- **TENSION PAUSE (centrale).** Voix = pause à l'ouverture (« on lit en pause ») ; automate = HUD LIVE (on regarde jouer). Les réunir dans un conteneur qui met en pause à l'ouverture EMPÊCHE l'onglet automate de montrer le jeu vivant. → Q2.
- **DEV vs DIÉGÉTIQUE.** Automate = instrument dev (comme F6). Le mêler aux voix diégétiques dans un conteneur in-game brouille les deux registres (philo #5/#6). Contexte : le build actuel est un banc d'observation, donc toléré, mais à assumer explicitement. → Q2.
- **Filtre launcher = pas strictement pure-vue SI par catégorie.** Filtre par nom (substring) = pur C#. Filtre par catégorie/thème = petite touche Python (métadonnées dans le registre + `list_bancs`). → Q3.
- **« Paramètres sur tous les éléments » à cadrer.** 3 familles : (a) confort/debug ; (b) conditions initiales de banc ; (c) params modèle éco → (c) viole #3/#4, rouvre D64/D69, HORS sprint. → Q1.

## Décisions arrêtées (1er lot, 2026-07-23)
- **D-A1 Paramètres v1 = confort/debug + options d'init** (encyclo de démarrage, carnet anticipé). Famille (c) params modèle éco EXCLUE (#3/#4, D64/D69). Rationale : Nico veut de vraies options utilisables, pas des boutons factices.
- **D-A2 Pause PAR ONGLET.** Onglet voix → sim en pause (comportement actuel VoicePanel) ; onglet Automate → sim tourne (HUD live). Changer d'onglet (dé)pause. Résout la tension pause/live.
- **D-A3 Filtre launcher = nom + catégorie.** Exige d'exposer la catégorie par banc via `list_bancs` (petite touche Python, golden intact).
- **D-A4 D59 ABSORBÉE** par Volet B (emplacement automate = tiers droit = cible D59). À fermer en fin de sprint.
- **D-A5 Backends d'init CONFIRMÉS existants** : `carnet_anticipe` → `game_state["options"][player]` lu par `sim/carnet.py::_seuil` (SEUIL_ANTICIPE=1 déjà défini) ; encyclo de démarrage = amorçage des paliers de maîtrise à l'init (encyclopédie dérivée de `maitrise.palier>=1`, cf. `sim/encyclopedie.py::_decouverte`). Palier 1 = fiche niveau 1 SANS basculer le carnet interprétatif (seuil 3). Aucune mécanique neuve.

## Décisions arrêtées (2e lot, 2026-07-23)
- **D-A6 Onglets in-game = Carnet · Encyclopédie · Magazine · Pages · Atelier (+ Automate DEV-GATED).** L'onglet Automate n'apparaît QUE si l'automate a été branché (touche A). Atelier conservé comme onglet (fonction hub active). Grisées Semis/Foyer (« à venir ») NON représentées en onglet → restent reliquat D54.
- **D-A7 Paramètres = launcher UNIQUEMENT (v1).** Les options d'init n'ont de sens qu'avant de monter un monde. Toggles confort in-game restent sur leurs touches actuelles (F6/F7/O/I). Pas d'onglet Paramètres in-game.
- **D-A8 Micro-UX tranchée (défauts).** Clic maison → conteneur sur onglet **Carnet**. Touche A → ouvre/bascule sur onglet **Automate** ; re-appui A alors qu'Automate est actif = ferme (toggle). L'intermédiaire « menu hub » (liste des 5 fonctions) DISPARAÎT : clic maison ouvre directement le conteneur à onglets.

## Découpage FIGÉ — 1 sprint `fenetrage_ui`, 3 tronçons (perf-first, golden INCHANGÉ partout)
- **T1 — Launcher haut-gauche défilable + filtrable.** `WorldView.Selecteur.cs` : panneau ancré haut-gauche, liste scrollable (remplace l'OptionButton), barre de filtre (nom + catégorie). Patron réutilisable « conteneur défilable si débordement ». Python : `cmd_list_bancs` renvoie `[{nom, categorie}]` (catégorie = module d'origine) + bump pont. Golden intact (list_bancs ne touche pas le moteur).
- **T2 — Bouton + panneau Paramètres (launcher).** Options confort câblées (vitesse sim, toggles overlays debug) + options d'init (encyclo démarrage vierge/amorcée/fournie ; carnet anticipé O/N). Python : `cmd_init` accepte `{carnet_anticipe, encyclo_demarrage}` → pose le flag options + amorce les paliers (mécanisme existant). Défauts = comportement actuel → golden intact.
- **T3 — Panneau de consultation unifié à onglets (Volet B, tronçon VUE final).** Refactor `VoicePanel` → conteneur chrome (pause/voile/fermer) hébergeant un `TabContainer` ; les spécialisations deviennent des contenus `Control` (pattern `Remplir()`/`InjecterPont` préservé). Emplacement = automate (droite, D59 absorbée). Onglet Automate = contenu migré de `WorldView.Automate.cs`, dev-gated. Pause PAR ONGLET. Perf : TabContainer garde les enfants vivants (visibilité), lecture snapshot automate seulement si onglet visible+actif.

## Livraison (Phase C, après tronçons)
Fermer **D59** ; consigner reliquats (Semis/Foyer onglets, éventuel Paramètres in-game) en **D54** ; MAJ `DETTE.md` + `BACKLOG.md` + `journal.md`.

## Décision complémentaire (2026-07-23)
- **A9 précisée** : Foyer / Semis intérieur redeviendront des ONGLETS du conteneur quand ils seront implémentés (Nico) — reliquat D54, pas d'onglet mort en v1.

## §REPRISE
Conception FIGÉE. Doc + 3 kickoffs écrits, commités. Thème `joueur/interface` créé (README + ligne ARBORESCENCE §4 + fragment backlog). D59 marquée absorbée dans DETTE. Prochaine étape : `/sprint-auto sprint_fenetrage_ui`. En fin de sprint : fermer D59, verser reliquats D54, MAJ journal.
