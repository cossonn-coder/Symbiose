# T3 — Panneau de consultation unifié à onglets (Volet B, tronçon VUE final)

> Kickoff autosuffisant. Lire d'abord `CLAUDE.md` + `00_etat.md` (décisions
> A2/A4/A6/A8/A9). Conception : `docs/joueur/interface/conception_fenetrage_ui.md`
> §4-T3. Tronçon **le plus lourd** (refactor). Golden inchangé (pure vue).

## Objectif
Réunir les surfaces de consultation (Carnet, Encyclopédie, Magazine, Pages,
Atelier) **et** la fenêtre de l'automate dans **un seul conteneur à onglets**, à
**l'emplacement de l'automate** (tiers droit). Le menu hub intermédiaire
disparaît : clic maison → conteneur directement.

## Contexte de départ (état lu 2026-07-23)
- `world/VoicePanel.cs` : `CanvasLayer` **centré** (720×560), **pause-aware**
  (mémorise `GetTree().Paused` à l'ouverture, met en pause, restaure à la
  fermeture), voile plein écran, en-tête (titre + « Fermer ✕ »),
  `ScrollContainer` → `Contenu` (VBox). Point d'extension `Remplir()` (virtual) ;
  pont injecté par `InjecterPont(SimBridge)`.
- Spécialisations : `CarnetPanel`, `EncyclopediePanel`, `MagazinePanel`,
  `PagesPanel`, `AtelierPanel` (chacune surcharge `Remplir()`, lit via `Bridge`).
- `world/WorldView.Hub.cs` : `ClicSurMaison` → `OuvrirHubMaison` (menu centré des
  5 fonctions) → `OuvrirVoicePanel(titre, fonction)` (switch fonction → panel).
- `world/WorldView.Automate.cs` : `CanvasLayer` **droite** (ColorRect pos
  (1142,100) size 772×872), `RichTextLabel` LIVE (lit le bloc `automate` du
  snapshot chaque tick via `ApplyAutomate`, appelé depuis `ApplySnapshot`), touche
  A `ToggleAutomate`, filtre catégories F `CycleAutomateCat` / Maj+F
  `ToggleAutomateCat`. **Ne met pas en pause.**
- `world/WorldView.Controls.cs` : `Key.A` → `ToggleAutomate` ; `Key.F` →
  cycle/toggle filtre automate ; clic maison géré avant `TryAction`.

## Architecture cible

### Refactor VoicePanel → conteneur à onglets
- `VoicePanel` garde le **chrome** : voile, cadre, bouton fermer, **gestion de
  pause**, injection pont. Il héberge un **`TabContainer`** à la place du
  `ScrollContainer` unique.
- Les spécialisations deviennent des **contenus** (un `Control` défilable par
  onglet) ajoutés au `TabContainer`, plus des sous-classes de `CanvasLayer`.
  Deux voies acceptables — choisir la moins invasive :
  - **(préférée)** extraire le corps de chaque spécialisation en un nœud contenu
    (`Control` avec `ScrollContainer`+`Contenu`, méthode `Remplir()`,
    `InjecterPont`), le chrome `CanvasLayer` remontant dans le conteneur ; ou
  - garder les classes et n'en réutiliser que la logique de peuplement dans des
    contenus d'onglet.
  **Préserver le pattern `Remplir()`/`InjecterPont`** — l'invariant « Godot bête »
  (aucun texte de voix fabriqué en C#, tout vient du pont) est intangible.
- **Emplacement** : ancrer le conteneur au **tiers droit** (aligné sur la zone
  automate, pos ~(1142,100), ~772×872), **non centré** → **D59 absorbée**.
- Le contenu de chaque onglet est **construit une fois** ; le `TabContainer`
  masque/affiche (jamais de reconstruction au changement d'onglet).

### Onglets (A6)
Ordre : **Carnet · Encyclopédie · Magazine · Pages · Atelier**. L'onglet
**Automate** est **dev-gated** : présent uniquement quand l'automate a été
branché (touche A). Foyer/Semis : PAS d'onglet en v1 (A9 → D54).

### Onglet Automate
- Migrer le contenu de `WorldView.Automate.cs` (RichTextLabel + filtre F/Maj+F +
  `ApplyAutomate`) comme **contenu d'onglet**. Il reste un **HUD live** : quand
  cet onglet est visible+actif, il lit le bloc `automate` du snapshot ; sinon on
  n'assemble pas son texte (perf). `ToggleAutomate` (A) fait toujours brancher/
  débrancher côté serveur ET crée/retire l'onglet.

### Pause PAR ONGLET (A2)
- Le conteneur (dé)pause selon l'onglet actif : onglet **voix/atelier** →
  `GetTree().Paused = true` ; onglet **Automate** → `Paused = false` (la sim
  tourne, l'automate joue et on le regarde). Brancher sur le signal de changement
  d'onglet du `TabContainer` (`TabChanged`).
- À la **fermeture**, restaurer l'état de pause d'**avant ouverture** (mémorisé
  comme aujourd'hui). Ne jamais dépauser aveuglément.

### Routage (A8)
- `WorldView.Hub.cs` : clic maison → **plus de menu intermédiaire** → ouvre le
  conteneur sur l'onglet **Carnet**. Retirer/inactiver `OuvrirHubMaison` (menu
  des 5 fonctions) ; conserver `ClicSurMaison`.
- Touche A (`WorldView.Controls.cs` + `WorldView.Automate.cs`) : ouvre le
  conteneur sur l'onglet **Automate** (le crée s'il manque) ; re-appui A alors
  que l'onglet Automate est **actif** = **ferme** le conteneur.
- Un seul conteneur actif à la fois (comme le `_voicePanel` actuel).

## Golden
**INCHANGÉ** — pure vue, aucune touche moteur. Lancer
`python3 -m tests.test_golden` (data/code/), vérifier le hash, ne PAS re-figer.

## Filet de compilation
`dotnet build Symbiose.csproj` doit passer.

## Garde-fou taille (CLAUDE.md)
Le refactor déplace du code — surveiller `tools/compte_ldc.py` sur les fichiers
touchés. Si un fichier passe >400 LDC, scinder par responsabilité (un
contenu/onglet par fichier plutôt qu'un gros VoicePanel).

## Ce qu'il NE faut PAS faire
- Ne PAS fabriquer de texte de voix en C# (invariant « Godot bête »).
- Ne PAS reconstruire les contenus au changement d'onglet.
- Ne PAS centrer le conteneur (emplacement = automate, droite).
- Ne PAS afficher l'onglet Automate en permanence (dev-gated).
- Ne PAS créer d'onglets Foyer/Semis/Paramètres (A7/A9).
- Ne PAS re-figer le golden.

## F5 (Nico)
Clic maison → panneau à droite sur Carnet ; les onglets basculent ; Carnet/
Encyclopédie mettent en pause, l'onglet Automate (après un appui A) laisse la sim
tourner ; A ré-appuyé sur Automate ferme.

## Après T3 (livraison, Phase C)
Fermer **D59** ; consigner reliquats (Foyer/Semis, Paramètres in-game) en **D54** ;
MAJ `DETTE.md` + `BACKLOG.md` + `journal.md`.
