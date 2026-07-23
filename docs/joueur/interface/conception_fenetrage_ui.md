# Conception — Fenêtrage UI : launcher de bancs + panneau de consultation unifié

**Date figée :** 2026-07-23
**Type/thème :** `joueur/interface`
**Nature :** vue C#/Godot, avec une **petite touche Python** ciblée (métadonnées de bancs + options d'init). Aucune mécanique écologique.
**Golden :** INCHANGÉ sur les 3 tronçons (les défauts reproduisent le comportement actuel ; `smoke`/`full` ne passent aucune des nouvelles options).

---

## 0. Intention

Deux ajustements ergonomiques demandés par Nico, réunis en un sprint car de même
famille (gestion de fenêtres / panneaux) :

- **Volet A — le launcher (hors-jeu).** L'écran de sélection de monde devient un
  panneau ancré **en haut à gauche**, **défilable** et **filtrable**, doté d'un
  bouton **« Paramètres »** (options de simulation). Règle transversale : **toute
  fenêtre défile si son contenu déborde**.
- **Volet B — le panneau de consultation (in-game).** Les surfaces d'information
  (carnet, encyclopédie, magazine, pages) et la fenêtre de l'automate sont
  réunies à **un seul emplacement** — celui de la fenêtre automate (tiers droit)
  — en **navigation par onglets**.

C'est du **confort et de la cohérence spatiale**, pas de l'écologie. La philo
bio (#1/#2/#6/#7) n'est pas concernée ; les points de vigilance sont #3
(déterminisme), #4 (run éternel, vocabulaire non-roguelike) et #5 (pas de HUD
chiffré permanent).

---

## 1. État de l'existant (lu le 2026-07-23)

- **Launcher** — `world/WorldView.Selecteur.cs` : `CanvasLayer`, panneau
  **centré**, `OptionButton` (dropdown) listant full/smoke/propre +
  `_bridge.ListBancs()`, bouton « Lancer ». Pas de scroll, pas de filtre, pas de
  Paramètres.
- **Panneau automate** — `world/WorldView.Automate.cs` : `CanvasLayer` ancré
  **à droite** (ColorRect pos (1142,100) size 772×872 sur écran 1920).
  `RichTextLabel` `ScrollActive`. **HUD LIVE** : lit le bloc `automate` du
  snapshot à chaque tick, touche A on/off, filtre catégories propre (F / Maj+F).
  **Ne met PAS en pause.** Statut : instrument de **dev** (même rang que
  l'overlay F6), « pas une fonctionnalité de jeu ».
- **VoicePanel** — `world/VoicePanel.cs` : `CanvasLayer` **centré** (720×560),
  contient déjà un `ScrollContainer`. **PAUSE-AWARE** (met la sim en pause à
  l'ouverture, restaure à la fermeture). Spécialisations `CarnetPanel`,
  `EncyclopediePanel`, `MagazinePanel`, `PagesPanel`, `AtelierPanel` : chacune
  surcharge `Remplir()` et lit son contenu via `Bridge` (invariant « Godot
  bête »).
- **Hub** — `world/WorldView.Hub.cs` : clic maison → menu centré (5 fonctions,
  4 voix + Atelier actifs, Semis/Foyer grisés) → `OuvrirVoicePanel(titre,
  fonction)`.
- **Pont** — `cmd_list_bancs` (`data/code/tools/simserver/commands.py`) renvoie
  `{"bancs": sorted(BANCS)}` : **noms seuls**, aucune catégorie. Les bancs sont
  regroupés par module (`bancs/climatique.py`, `edaphique.py`, `hydrologie.py`,
  `biotique.py`, `succession.py`, `luxuriance.py`, `diversite.py`,
  `modele_spatial.py`, `palette_gestes.py`) mais ce thème n'est pas exposé.
- **Backends des options d'init** — DÉJÀ présents :
  - carnet anticipé → `sim/carnet.py` lit
    `game_state["options"][player]["carnet_anticipe"]` (`_reglage_anticipe` →
    `_seuil`, `SEUIL_ANTICIPE = 1` défini). Il suffit de poser le flag.
  - encyclopédie de démarrage → l'encyclopédie est **dérivée du palier de
    maîtrise** (`sim/encyclopedie.py::_decouverte` = `maitrise.palier ≥ 1`).
    « vierge/amorcée/fournie » = amorcer les paliers à l'init. **Palier 1 = fiche
    niveau 1 SANS faire basculer le carnet en interprétatif** (seuil 3) — donc
    l'amorçage encyclopédique ne fuit pas vers le carnet.

---

## 2. Décisions arrêtées

| # | Décision | Rationale |
|---|----------|-----------|
| A1 | **Paramètres v1 = confort/debug + options d'init.** Params modèle éco (agressivité invasion, létalité…) EXCLUS. | Nico veut de vraies options, pas des boutons factices. (c) violerait #3/#4 et rouvrirait D64/D69. |
| A2 | **Pause PAR ONGLET.** Onglet voix → sim en pause ; onglet Automate → sim tourne (live). Changer d'onglet (dé)pause. | Résout la tension pause/live : les voix se lisent en pause, l'automate se regarde jouer. |
| A3 | **Filtre launcher = nom + catégorie.** | Utile quand la liste grandit ; la catégorie = module d'origine du banc. |
| A4 | **D59 ABSORBÉE.** | L'emplacement automate (tiers droit) EST la cible de D59 (« menu maison à droite »). |
| A6 | **Onglets in-game = Carnet · Encyclopédie · Magazine · Pages · Atelier (+ Automate DEV-GATED).** L'Automate n'apparaît que si branché (touche A). | Préserve dev vs diégétique : l'onglet dev reste invisible tant qu'on ne l'invoque pas. |
| A7 | **Paramètres = launcher UNIQUEMENT (v1).** | Les options d'init n'ont de sens qu'avant de monter un monde. Toggles confort in-game restent sur leurs touches (F6/F7/O/I). |
| A8 | **Micro-UX.** Clic maison → onglet Carnet ; A → ouvre/bascule sur Automate, re-appui A sur Automate = ferme. Le menu hub intermédiaire DISPARAÎT (clic maison ouvre directement le conteneur à onglets). | Un seul point d'ancrage, moins de clics. |
| A9 | **Foyer / Semis intérieur** : deviendront des onglets **quand ils seront implémentés** (reliquat D54), pas d'onglet désactivé en v1. | On n'affiche pas de fonction morte. |

---

## 3. Respect de la philosophie

- **#3 déterminisme** — aucune option n'introduit d'aléa. Les options d'init
  amorcent un état de départ (paliers, flag carnet) puis la sim reste
  déterministe (seed + hash). Un banc reste rejouable à l'identique.
- **#4 run éternel** — le launcher est un outil de **test/dev**, pas un menu
  roguelike. Vocabulaire : « choisir un monde / un banc », jamais « new game »,
  « run », « partie ». Le jardin joué reste unique et persistant.
- **#5 HUD** — le panneau de consultation reste un dispositif d'information
  diégétique (carnet, encyclopédie). L'onglet Automate et le panneau Paramètres
  sont des surfaces techniques, gardées hors du HUD primaire de découverte
  (Automate dev-gated ; Paramètres au launcher). Pas de HUD de chiffres permanent
  recréé.

---

## 4. Découpage — 3 tronçons (perf-first, golden inchangé partout)

### T1 — Launcher haut-gauche défilable + filtrable
- `world/WorldView.Selecteur.cs` : panneau ancré **haut-gauche** (`LayoutPreset.TopLeft`
  + marge), **liste défilante** (`ScrollContainer` + `VBoxContainer` de boutons,
  ou `ItemList`) remplaçant l'`OptionButton`, **barre de filtre** au-dessus
  (`LineEdit` nom + sélecteur de catégorie). Présélection = `Config` conservée.
- **Patron réutilisable** « conteneur défilable si débordement » : petit helper
  (méthode statique ou nœud dédié) réemployé par le launcher, Paramètres (T2) et
  le conteneur à onglets (T3). Règle transversale « toute fenêtre défile ».
- **Python** : `cmd_list_bancs` renvoie `[{"nom", "categorie"}]` (catégorie =
  module d'origine du banc, exposée par une table dans `bancs/__init__.py` ou
  dérivée du `__module__` des fabriques). Bump de version du pont. `list_bancs`
  ne touche PAS le moteur → golden intact.
- **F5** : le launcher s'ouvre en haut à gauche, défile, filtre par nom et par
  catégorie, lance le banc sélectionné.
- **Golden : INCHANGÉ.**

### T2 — Bouton + panneau Paramètres (launcher)
- Bouton « Paramètres » dans le launcher → sous-panneau **défilable** (patron T1).
- **Options confort** (leviers réels d'aujourd'hui) : vitesse de sim
  (`SecondsPerWeek`, plage 30-180 s), toggles overlays debug (les mêmes que
  F6/F7/O/I). Appliqués à la vue.
- **Options d'init** : encyclopédie de démarrage (vierge / amorcée / fournie) +
  carnet interprétatif anticipé (OUI/NON, défaut NON). Mémorisées et passées à
  `StartSimulation` → `cmd_init`.
- **Python** : `cmd_init` accepte des champs OPTIONNELS
  `{carnet_anticipe: bool, encyclo_demarrage: "vierge"|"amorcee"|"fournie"}` →
  pose `game_state["options"][player]["carnet_anticipe"]` + amorce les paliers de
  maîtrise (mécanisme existant du debug maîtrise, appliqué à l'init). **Défauts =
  comportement actuel** (champs absents → rien) → golden intact (`smoke`/`full`
  ne les passent pas).
- **F5** : Paramètres s'ouvre/défile ; changer la vitesse agit ; monter un banc
  « encyclo fournie » remplit l'encyclopédie ; « carnet anticipé » bascule le
  carnet en interprétatif dès palier 1.
- **Golden : INCHANGÉ.**

### T3 — Panneau de consultation unifié à onglets (Volet B, tronçon VUE final)
- **Refactor** : `VoicePanel` conserve le **chrome** (voile plein écran, cadre,
  bouton fermer, gestion de pause) et héberge désormais un **`TabContainer`**.
  Les spécialisations (`CarnetPanel`, `EncyclopediePanel`, `MagazinePanel`,
  `PagesPanel`, `AtelierPanel`) deviennent des **contenus `Control`** hébergés
  comme onglets, plus des `CanvasLayer` autonomes. Le pattern
  `Remplir()`/`InjecterPont(Bridge)` est **préservé** (chaque contenu peuple sa
  zone via le pont). Le contenu de chaque onglet est **construit une fois** et
  masqué/affiché par le `TabContainer` (jamais reconstruit au changement
  d'onglet).
- **Emplacement** = celui de l'automate (tiers droit, non centré) → **D59
  absorbée**.
- **Onglet Automate** : le contenu de `WorldView.Automate.cs` (RichTextLabel +
  filtre F/Maj+F) migre comme onglet, **dev-gated** (présent uniquement quand
  l'automate a été branché par la touche A). Il reste un HUD live.
- **Pause PAR ONGLET** (A2) : le conteneur met la sim en pause quand l'onglet
  actif est une voix, la laisse tourner quand c'est l'Automate. La bascule
  d'onglet applique l'état de pause correspondant ; la fermeture restaure l'état
  d'avant ouverture (comme aujourd'hui).
- **Routage** (A8) : le hub `WorldView.Hub.cs` n'ouvre plus un menu intermédiaire
  — clic maison → conteneur sur onglet **Carnet**. Touche A → conteneur sur
  onglet **Automate** ; re-appui A alors qu'Automate est actif = ferme.
- **Perf** : `TabContainer` garde les enfants vivants (bascule de visibilité) →
  aucune reconstruction. L'onglet Automate ne lit le bloc snapshot que s'il est
  **visible et actif** (sinon on n'assemble pas son texte).
- **F5** : clic maison ouvre le panneau à droite sur Carnet ; les onglets
  basculent ; le carnet/l'encyclopédie mettent en pause, l'Automate tourne ;
  l'onglet Automate n'existe qu'après un appui A.
- **Golden : INCHANGÉ.**

---

## 5. Ce qu'on NE fait PAS

- Pas de params du modèle écologique dans Paramètres (A1).
- Pas d'onglet Paramètres in-game (A7) ni d'onglets Foyer/Semis (A9 → D54).
- Pas de reconstruction des contenus lourds au changement d'onglet (perf).
- Pas de vocabulaire roguelike dans le launcher (#4).
- Pas de nouvelle mécanique moteur : les options d'init réutilisent des backends
  existants ; `list_bancs` ne touche pas le moteur.

---

## 6. Livraison (Phase C)

- **Fermer D59** (absorbée par T3).
- **D54** : consigner les reliquats (onglets Foyer/Semis à l'implémentation,
  éventuel Paramètres in-game v2).
- MAJ `DETTE.md`, `BACKLOG.md`, `journal.md`.

---

## 7. Rattachement à l'existant

- **D59** — menu maison à droite : **absorbée** par T3.
- **D54** — reliquats UI voix (page d'accueil pictogrammes, Foyer/Semis) :
  distincte du launcher de bancs (outil de dev ≠ première expérience joueur).
- **D60** — filtre par type de l'encyclopédie : même esprit de filtre réemployé
  au launcher (T1).
- **Sprint bancs d'essai** (clos 2026-06-23, `data/code/bancs/`) — substrat du
  Volet A ; T1 en expose les catégories.
- **Bloc voix narratives** (figé 2026-06-29) + **sprint UI voix** (clos
  2026-07-01) — contenu des onglets, ré-hébergé sans réécriture.
