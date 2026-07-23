# T2 — Chrome & navigation (légende, launcher, retour accueil)

**Sprint :** `sprint_ui_retours_fenetrage`.
**Nature :** pure VUE C#/Godot. **Golden : INCHANGÉ** (aucune touche moteur).
**Doc de conception :** `docs/joueur/interface/conception_retours_ui_fenetrage.md` §2-3-5.
**Prérequis de lecture :** `CLAUDE.md` + `00_etat.md` + ce fichier.

Trois retouches de chrome indépendantes mais du même registre (HUD / launcher / nav),
regroupées en un tronçon pour ne pas payer trois amorçages à froid.

## Item 2 — Légende clavier escamotable (F1, masquée par défaut)
**État.** `world/WorldView.Hud.cs:155` crée un `Label legend` (`PROVISOIRE`) pleine
largeur à `Position = (16, 1080 − 96)`, qui **recouvre le bas du champ de jeu**. Il est
enfant du CanvasLayer HUD, toujours visible.

**Cible.** La légende devient **escamotable** :
- Garder le `Label legend` mais `Visible = false` par défaut.
- Toggle par **F1** (touche libre — pris : F3/F4/F6/F7, H, I, O, M, G, A, C, S, B, N).
  Câbler dans `world/WorldView.Controls.cs` (`_UnhandledInput`).
- Facultatif : un discret rappel « F1 : aide » minuscule dans un coin non recouvrant,
  si Nico le juge utile (sinon rien — la page d'accueil pictogrammes viendra plus tard).

Aucune diégétisation ici (D54-a complet = plus tard). Geste minimal : sortir le texte
du champ.

## Item 3 — Launcher pleine hauteur
**État.** `world/WorldView.Selecteur.cs:103` : `vbox.AddChild(UiScroll.Envelopper(_liste,
360f));` plafonne la liste défilante à 360 px. Panneau ancré TopLeft (16,16).

**Cible.** Relever le plafond pour que la liste puisse descendre jusqu'en bas d'écran.
Calculer une hauteur max = hauteur d'écran (1080) − marge haute (16) − hauteur estimée
des widgets fixes (titre + filtre nom + filtre catégorie + boutons Paramètres/Lancer) −
marge basse. Passer cette valeur à `UiScroll.Envelopper`. Si `UiScroll.Envelopper` ne
prend qu'une hauteur fixe, l'appeler avec la nouvelle valeur ; garder le comportement
« défile si débordement ». Rester robuste à la résolution projet 1920×1080.

## Item 5 — Retour à l'accueil (Échap → immédiat)
**État.** Le launcher `_selecteur` (CanvasLayer) est **détruit** (`QueueFree`) au
« Lancer » (`Selecteur.cs:169`), puis `StartSimulation` monte ~20 couches. `_ExitTree`
(`WorldView.cs:372`) attend les requêtes en vol puis `_bridge.Quit()` (ferme proprement
le pont).

**Cible.** **Échap → retour immédiat à l'accueil** via `GetTree().ReloadCurrentScene()` :
le rechargement déclenche `_ExitTree` (pont fermé proprement) puis re-`_Ready` →
nouveau pont + `BuildSelecteur`. Pas de démontage manuel des couches, pas de
confirmation (bancs rejouables, abandon assumé ; auto-save = passage de saison seul).

**Précédence (IMPORTANT).** Échap = `ui_cancel`. Gérer dans `_UnhandledInput` :
1. Si un **panneau est ouvert** (ConsultationPanel / VoicePanel — vérifier l'état
   d'ouverture existant, ex. `IsInstanceValid` d'un panneau actif), Échap le **ferme**
   et s'arrête là.
2. Sinon, Échap → `GetTree().ReloadCurrentScene()`.
Ne déclencher le rechargement **que** si la simulation est démarrée (`_started`), pas
pendant l'écran de sélection lui-même.

## Fichiers à toucher
- `world/WorldView.Hud.cs` — `legend.Visible = false` par défaut.
- `world/WorldView.Controls.cs` — F1 (toggle legend) ; Échap (précédence panneau →
  sinon `ReloadCurrentScene`).
- `world/WorldView.Selecteur.cs` (et/ou `world/UiScroll.cs`) — hauteur de la liste.

## Golden
**INCHANGÉ.** Aucune touche `data/code/`. `python3 -m tests.test_golden` identique.
Build C# VERT.

## Ne PAS faire
- Pas de confirmation avant le retour accueil (décision D4).
- Ne pas démonter à la main les couches de monde (le rechargement de scène s'en charge).
- Ne pas déclencher Échap→accueil quand un panneau est ouvert (le fermer d'abord).
- Ne pas supprimer le `Label legend` (le rendre escamotable, pas le retirer).

## Points F5 (Nico)
- F1 affiche/masque l'aide clavier ; champ dégagé par défaut.
- Launcher : la liste descend jusqu'en bas et défile si elle déborde.
- Échap en jeu → retour à l'accueil (pont redémarré, nouveau choix de monde) ; Échap
  quand un panneau est ouvert → ferme le panneau seulement.

## En fin de tronçon
MAJ `00_etat.md` (Avancement T2) puis commit.
