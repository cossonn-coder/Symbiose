# 2026-07-23 — Sprint FENÊTRAGE UI — CLOS (`/sprint-auto`, T1→T3)

Sprint **pure vue C#/Godot** (avec petites touches Python au pont, jamais le
moteur) : deux volets d'ergonomie des fenêtres. **Golden `57c166d8…` INTACT sur
les 3 tronçons** (aucune touche moteur ; `list_bancs`/`init` sont event-driven
hors tick), `dotnet build` VERT partout, pont `0.5.35 → 0.5.37`.

## Volet A — launcher de bancs (hors-jeu)

**T1 — launcher haut-gauche défilable + filtrable** (`d4e3682`).
`WorldView.Selecteur.cs` réécrit : panneau réancré **haut-gauche**, liste
défilante de boutons toggle (`ButtonGroup` = sélection visible) remplaçant
l'`OptionButton`, barre de filtre **par nom** (`LineEdit`, substring) **+ par
catégorie** (`OptionButton`). Nouveau helper réutilisable `world/UiScroll.cs`
(`Envelopper` = scroll si débordement, patron « toute fenêtre défile si
débordement », réemployé en T2/T3). Python (vérité) : `bancs/__init__.py` gagne
`banc_categorie(nom)` (catégorie dérivée du **module de la fabrique**, repli
`divers`) ; `cmd_list_bancs` renvoie `[{nom, categorie}]` trié. Pont
**0.5.36**. `SimBridge.ListBancs()` défensif (binaire pré-0.5.36 → `divers`).

**T2 — bouton + panneau Paramètres du launcher** (`f450587`).
Nouveau partial `world/WorldView.Parametres.cs` : bouton « Paramètres… » →
sous-panneau défilable avec **options confort** (vitesse sim `SecondsPerWeek`,
ombres — zéro duplication, réutilise `ToggleShadows`) et **options d'init**
(encyclo de démarrage `vierge`/`amorcée`/`fournie`, carnet anticipé O/N).
Python : `cmd_init` accepte `carnet_anticipe` + `encyclo_demarrage` optionnels →
pose le flag `game_state["options"][player]` (déjà lu par `sim/carnet`) et amorce
les paliers via le mécanisme existant `maitrise.decouvrir` (**palier 1 = fiche
N1 sans bascule interprétatif**, seuil 3 préservé). Défauts = comportement
actuel → golden intact. Pont **0.5.37**. **Écart de périmètre assumé (D-A7)** :
les overlays debug **runtime-only** (heatmaps F6/F7, macro I, LOD F9) dépendent
de couches construites *après* le lancement → pas de cible au launcher
pré-simulation → laissés sur leurs touches in-game. Consigné → D54(j).

## Volet B — panneau de consultation (in-game)

**T3 — panneau de consultation unifié à onglets** (`21f20b5`).
Refactor `VoicePanel` → contenu d'onglet défilable ; chrome (pause/voile/fermer)
remonté dans nouveau `ConsultationPanel.cs` hébergeant un **`TabContainer`**
ancré **tiers droit** (= emplacement automate, **D59 absorbée**). Onglets
**Carnet · Encyclopédie · Magazine · Pages · Atelier** (+ **Automate DEV-GATED**,
n'apparaît qu'après touche A). Rendu automate extrait dans nouveau
`AutomateContent.cs` (HUD live, feed **gaté sur visibilité** = perf) ;
`WorldView.Automate.cs` réduit à la glue. **Pause PAR ONGLET** (D-A2) : onglet
voix → sim en pause + voile ; onglet Automate → sim tourne, monde interactif.
Micro-UX A8 : **clic maison → onglet Carnet direct** (le menu hub intermédiaire
disparaît) ; A ouvre/bascule/ferme l'onglet Automate. Les 5 spécialisations voix
**non touchées** (pattern `Remplir()`/`InjecterPont` préservé).

## Livraison (Phase C)

- **D59 fermée** (✅ FAIT 2026-07-23, absorbée par T3).
- **Reliquats versés en D54** : (h) onglets Semis/Foyer quand implémentés (A9) ;
  (i) Paramètres in-game (v1 = launcher seul, D-A7) ; (j) overlays debug
  runtime-only restant sur leurs touches.
- **Refactor auto-léger : no-op** — tous les fichiers touchés 🟢 (max LDC pur =
  259, `core/SimBridge.cs`).
- Backlog `docs/joueur/interface/backlog_interface.md` → ✅ FAIT.

**Reste F5 Nico** : (A) launcher haut-gauche — défilement au débordement, filtres
nom+catégorie, lancement ; panneau Paramètres — vitesse agit, ombres OFF au
démarrage, « encyclo fournie » → encyclopédie remplie, « carnet anticipé » ON →
interprétatif dès palier 1. (B) conteneur à onglets à droite ouvert sur Carnet,
bascule d'onglets, pause voix vs Automate live, A ajoute/ferme l'onglet Automate,
filtre F/Maj+F, achats magazine/atelier intacts.
