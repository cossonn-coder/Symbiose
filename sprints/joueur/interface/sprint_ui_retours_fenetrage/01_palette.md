# T1 — Palette de gestes gérable

**Sprint :** `sprint_ui_retours_fenetrage` (retours UI/HUD post-fenêtrage).
**Nature :** pure VUE C#/Godot. **Golden : INCHANGÉ** (aucune touche moteur).
**Doc de conception :** `docs/joueur/interface/conception_retours_ui_fenetrage.md` §1.
**Prérequis de lecture :** `CLAUDE.md` + `00_etat.md` de ce dossier + ce fichier.

## Objectif
Transformer la palette de gestes en une palette **gérable** : masquer les gestes non
débloqués, plafonner à **10 slots** (touches **1-9 puis 0**), remplir automatiquement
dans l'ordre parmi les débloqués, permettre l'**édition clic droit** du contenu des
slots, et **persister le layout globalement**.

## État actuel (vérifié le 2026-07-23)
- `world/WorldView.Palette.cs` : colonne verticale gauche (CanvasLayer Layer 6, pos
  10,150). Crée UNE icône `GesteIcon` par entrée de `Gestes[]` (~28), les indices
  alignés sur `Gestes[]` et `_gesteIndex`. Lit `gestes_debloques` du snapshot via
  `ApplyGestesDebloques(...)` et **grise** (`icon.Verrouille = !ouvert`) les verrouillés
  (ne les masque PAS). `RebuildPaletteVisibility()` applique ouvert/verrouillé/actif.
- `world/WorldView.Actions.cs:27` : `private static readonly (string Verb, string Nom,
  char Kind)[] Gestes = { … }` (~28 gestes).
- `world/WorldView.Controls.cs:42` : `if (k.PhysicalKeycode >= Key.Key1 && … <= Key.Key9)
  SelectGeste((int)(k.PhysicalKeycode − Key.Key1));` → touches 1..9 = index BRUT dans
  `Gestes[]`. `Tab` = `CyclePalette(+1)`. `SelectGeste(idx)`/`UpdatePaletteSelection()`
  synchronisent `_gesteIndex` ↔ palette.
- `GesteIcon` porte `Verrouille`, `Actif`, `Init(verb, nom, kind)`.

## Modèle cible
1. **Slots.** Introduire un tableau `_slots` de **10** entrées, chacune = l'INDEX d'un
   geste dans `Gestes[]` (ou −1 = vide). La palette dessine **un GesteIcon par slot
   occupé** (au plus 10), plus rien pour `Gestes[]` brut.
2. **Masquer, pas griser.** Un geste non débloqué n'occupe aucun slot. Retirer le mode
   « grisé visible » (le champ `Verrouille` peut rester, mais aucun slot n'affiche un
   verrouillé).
3. **Remplissage auto.** Fonction `AutoRemplirSlots()` : parcourt `Gestes[]` dans
   l'ordre ; pour chaque geste DÉBLOQUÉ **non déjà présent** dans `_slots`, l'assigne au
   premier slot libre, jusqu'à épuisement des slots. Les gestes débloqués au-delà du
   10ᵉ restent hors palette (invisibles) tant qu'ils ne sont pas assignés à la main.
   Un slot dont le geste est devenu **non débloqué** (changement de monde/maîtrise) est
   vidé.
4. **Touches 1-9 + 0.** Remap `WorldView.Controls.cs` : `Key.Key1..Key.Key9` → slots
   0..8 ; `Key.Key0` → slot 9. La touche sélectionne le geste **du slot** (via
   `_slots[slot]`), pas l'index brut. Slot vide → no-op. `Tab` : faire cycler sur les
   **slots occupés** (pas sur `Gestes[]` brut).
5. **Édition clic droit.** Sur `GesteIcon`, capter le clic droit (bouton droit) →
   `PopupMenu` listant les gestes **débloqués absents** de la palette (à assigner à ce
   slot) + une entrée « vider ». Assigner/vider met à jour `_slots`, reconstruit la
   colonne, **persiste** (cf. 6).
6. **Persistance globale.** Sérialiser `_slots` (par VERBE, pas par index — robuste aux
   futurs réordonnancements de `Gestes[]`) dans un fichier `user://palette.json`.
   Recharger au montage (`BuildPalette`) ; un verbe persisté inconnu ou non débloqué est
   ignoré. Après chargement, appeler `AutoRemplirSlots()` pour compléter les slots
   restés libres. Helper minimal (lecture/écriture JSON via `FileAccess` + `Json`).

## Fichiers à toucher
- `world/WorldView.Palette.cs` — modèle slot, masquage, auto-remplissage, clic droit,
  (dé)sérialisation. **Surveiller la taille** (`tools/compte_ldc.py`) : si le fichier
  dépasse la bande 300/400 LDC, scinder la persistance dans un petit fichier dédié
  (ex. `world/PaletteLayout.cs`) — un fichier = une responsabilité.
- `world/WorldView.Controls.cs` — remap touches 1-9+0 vers slots ; `Tab` sur slots.
- `world/GesteIcon.cs` — exposer le clic droit (signal ou `_GuiInput`) si nécessaire.

## Golden
**INCHANGÉ.** Aucune touche `data/code/`. Vérifier `python3 -m tests.test_golden`
depuis `data/code/` avant/après (doit rester identique). Build C# : `dotnet build
Symbiose.csproj` VERT (0 warning/0 erreur).

## Ne PAS faire
- Ne pas toucher au moteur ni au pont (aucun champ snapshot nouveau ici).
- Ne pas remettre le mode grisé (Nico veut masquer).
- Ne pas faire bouger le layout tout seul quand la palette est pleine (pas de FIFO) :
  débordement = invisible jusqu'à assignation manuelle (décision D2).
- Ne pas persister par index de `Gestes[]` (fragile) — persister par verbe.

## Points F5 (Nico)
- Peu de gestes débloqués → seuls ceux-là dans la palette, touches 1..N.
- Beaucoup débloqués (>10) → 10 premiers visibles ; clic droit pour assigner un 11ᵉ.
- Clic droit → menu, assignation/vidage, layout conservé après un retour accueil (T2).

## En fin de tronçon
MAJ `00_etat.md` (section Avancement T1 : ce qui est fait, hash golden inchangé, build,
points F5) puis commit.
