# T1 — Launcher haut-gauche défilable + filtrable

> Kickoff autosuffisant. Lire d'abord `CLAUDE.md` (garde-fous, philo #1-#7,
> source de vérité Python) + `00_etat.md` (décisions A1-A9). Conception complète :
> `docs/joueur/interface/conception_fenetrage_ui.md`.

## Objectif
Transformer l'écran de sélection de monde (`world/WorldView.Selecteur.cs`) : d'un
panneau **centré** à `OptionButton` (dropdown) → un panneau ancré **en haut à
gauche**, avec une **liste défilante** et une **barre de filtre** (nom +
catégorie). Poser au passage un **patron réutilisable** « conteneur défilable si
débordement » (réemployé par T2 et T3). Exposer la **catégorie** de chaque banc
via le pont.

## Contexte de départ (état lu 2026-07-23)
- `WorldView.Selecteur.cs` : `CanvasLayer` « Selecteur », `PanelContainer` centré
  (`LayoutPreset.Center`), `VBoxContainer` min 260px, `Label` « Choisir un
  monde », `OptionButton` (full/smoke/propre + `_bridge.ListBancs()`), bouton
  « Lancer » → `StartSimulation(config)` puis `QueueFree`. Présélection = `Config`
  (défaut « full »).
- `SimBridge.ListBancs()` (`core/SimBridge.cs:390`) → commande `list_bancs`,
  renvoie aujourd'hui un `string[]` de noms.
- `cmd_list_bancs` (`data/code/tools/simserver/commands.py:182`) →
  `{"ok": True, "bancs": sorted(BANCS)}`. Registre `BANCS` dans
  `data/code/bancs/__init__.py` (dict nom→fabrique, 20 entrées). Les fabriques
  viennent de modules thématiques (`climatique`, `edaphique`, `hydrologie`,
  `biotique`, `succession`, `luxuriance`, `diversite`, `modele_spatial`,
  `palette_gestes`).

## À faire

### Python (source de vérité d'abord)
1. Dans `data/code/bancs/__init__.py` : exposer la **catégorie** de chaque banc.
   Le plus robuste = dériver de `fabrique.__module__` (ex.
   `bancs.climatique` → `"climatique"`) plutôt qu'une table à maintenir à la main.
   Prévoir un repli `"divers"` si le module n'est pas résolvable.
2. `cmd_list_bancs` (`tools/simserver/commands.py`) : renvoyer
   `{"ok": True, "bancs": [{"nom": n, "categorie": c}, ...]}` **trié par nom**
   (déterminisme d'affichage). Garder l'ordre stable.
3. `tools/simserver/version.py` : bump de version + ligne de changelog (« bancs
   avec catégorie »).
4. Vérifier qu'aucun appelant Python de `cmd_list_bancs` ne casse (grep) — c'est
   une commande lue par la vue, pas par le moteur.

### C#
5. `SimBridge.ListBancs()` : adapter la signature pour renvoyer nom+catégorie
   (ex. un `Godot.Collections.Array` de dicts, ou un petit `record`/tuple
   `(string Nom, string Categorie)[]`). Rester défensif : si le pont est ancien
   et renvoie des chaînes nues, mapper vers catégorie `"divers"` (compat binaire
   gelé).
6. `WorldView.Selecteur.cs` :
   - Ancrer le panneau **en haut à gauche** (`LayoutPreset.TopLeft` + une marge,
     ex. `Position = (16, 16)`), largeur fixe raisonnable (~320px), hauteur
     bornée.
   - Remplacer l'`OptionButton` par une **liste défilante** : `ScrollContainer`
     (hauteur max bornée) contenant un `VBoxContainer` de `Button` (un par
     entrée), OU un `ItemList`. Chaque entrée affiche le nom (la catégorie peut
     être un préfixe/tag). full/smoke/propre restent en tête.
   - **Barre de filtre** au-dessus : un `LineEdit` (filtre par sous-chaîne du
     nom, insensible à la casse) + un moyen de filtrer par **catégorie**
     (`OptionButton` des catégories distinctes, avec « toutes » par défaut). Le
     filtre recompose la liste affichée (source = liste complète mémorisée, on ne
     re-interroge pas le pont à chaque frappe).
   - Conserver la présélection sur `Config` et le bouton « Lancer » →
     `StartSimulation(nomSélectionné)` + `QueueFree` du sélecteur.
7. **Patron réutilisable** : extraire une petite fonction/helper « envelopper un
   Control dans un ScrollContainer qui défile si débordement » (ex. dans un
   nouveau `world/UiScroll.cs` ou méthode statique), utilisée ici et réutilisable
   par T2/T3. Garder ça minimal (une responsabilité).

## Modèle / détails
- Catégorie = `fabrique.__module__.rsplit(".", 1)[-1]` côté Python.
- Filtre : `nom.ToLower().Contains(saisie.ToLower())` ET
  (`catégorie == choisie` OU choisie == « toutes »).
- Vocabulaire (#4) : « Choisir un monde / un banc », jamais « partie », « run »,
  « new game ».

## Golden
**INCHANGÉ.** `cmd_list_bancs` lit le registre, ne touche pas le moteur ;
`smoke`/`full` ne sont pas des bancs. Lancer `python3 -m tests.test_golden`
depuis `data/code/` et vérifier le hash consigné (ne PAS le re-figer).

## Filet de compilation
`dotnet build Symbiose.csproj` doit passer (SDK sur la VM). Le F5 visuel reste à
Nico.

## Ce qu'il NE faut PAS faire
- Ne pas coder en dur la liste des bancs côté C# (le registre Python reste source
  unique — un menu périmé est le piège que le sprint bancs a éliminé).
- Ne pas ajouter le bouton « Paramètres » ici (c'est T2).
- Ne pas re-interroger le pont à chaque frappe de filtre.
- Ne pas re-figer le golden.

## F5 (Nico)
Le launcher s'ouvre en haut à gauche, défile si la liste déborde, filtre par nom
et par catégorie, lance le banc choisi.
