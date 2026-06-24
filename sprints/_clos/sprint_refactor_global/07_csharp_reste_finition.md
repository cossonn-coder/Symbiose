# SS⑦ — C# reste, purge des morts & finition du sprint

> Lire `00_etat.md`. **Dernier tronçon.** Risque moyen (filet =
> `dotnet build` + F5). Clôt le sprint : grave les règles permanentes et
> recalibre le golden de taille.

## Partie A — Purge du C# mort (Option B actée)

Godot n'est qu'une VUE : le portage C# intégral de la simulation est
**abandonné**. Les stubs vides de 15 lignes en sont les vestiges → à
supprimer (`git rm` ; mtime à vérifier, mais ce sont des fossiles de
l'ancien plan). Candidats repérés (confirmer « 15 l + jamais référencés »
avant rm) :

- `core/` : `GameManager.cs`, `EcologySystem.cs`, `TurnSystem.cs`,
  `SeedBankSystem.cs` (+ `.uid`)
- `plants/` : `GrowthComponent.cs`, `PlantInstance.cs`, `PlantPhysiology.cs`
- `ui/` : `EcoHUD.cs`, `NotificationQueue.cs`, `TurnPanel.cs`
- `visuals/` : `LightOverlay.cs`, `PlantAnimator.cs`, `WindAnimator.cs`
- `world/` : `SoilField.cs`
- `Main.cs` + `Main.tscn` (scène morte, principale = `WorldView.tscn`) —
  **vérifier** qu'aucun `res://` ne pointe Main.tscn avant rm.
- `world/TileGrid.cs` + `TileGrid.tscn` : remplacés par WorldView — vérifier
  qu'aucun code/scène ne les instancie encore (grep `TileGrid`) avant rm.

> Pour chaque suppression : `grep -rn "<NomClasse>" --include=*.cs
> --include=*.tscn .` (hors `.godot`). Zéro référence → rm. Sinon, garder
> et signaler à Nico.

## Partie B — Éclater les fichiers C# restants > 500 l

| Fichier | Lignes | Découpe |
|---------|--------|---------|
| `core/PlantCatalogue.cs` | 709 | données : un fichier par groupe d'espèces, ou ressources externes ré-agrégées |
| `core/GridField.cs` | 555 | séparer GridField / LightField / EcoFields (le `.md` dit qu'il les contient tous) |
| `visuals/PlantRenderer.cs` | 541 | rendu branches / LOD silhouette / utilitaires |

Et appliquer la préférence **un fichier = une classe** aux fichiers
multi-classes (même < 500 l) :
- `core/PlantData.cs` → `GrowthStage` / `PlantData` / `PlantInstance`
- `core/TileData.cs` → `Tile` / `StakeSlot` / `ConflictNotification`

Namespace `Symbiose` conservé partout (chemins `res://` inchangés).

## Partie C — Graver les règles permanentes

Mettre à jour **`CLAUDE.md`** (section « Garde-fous spécifiques ») :
- Ajouter la règle : **« Aucun fichier > N lignes de code pur »** où `N` =
  max empirique mesuré (Partie D). Commentaires pédagogiques exclus du
  décompte et **exigés au cœur des fichiers**. Exception = signalée +
  justifiée à Nico.
- Préférence **un fichier = une classe / concept cohérent**.
- Pointer vers l'arbo cible (docs/conception, journal éclaté).

## Partie D — Recalibrage du golden de taille

```
python3 data/code/tools/compte_ldc.py $(git ls-files '*.py' '*.cs') | sort
```
Relever le **plus long fichier en lignes de code pur** sur tout le dépôt
refactoré → c'est le nouveau seuil empirique `N`. Le reporter dans
`CLAUDE.md` (Partie C) et dans `00_etat.md`. Annoncer la valeur à Nico.

## Vérification finale (tout le sprint)

```
dotnet build Symbiose.csproj                 # OK
cd data/code && python3 -m tests.test_golden # vert + hash inchangé depuis le début
```
+ F5 Godot : le jeu tourne comme avant.

## Définition de fait

- [ ] Stubs morts + Main/TileGrid supprimés (références vérifiées nulles).
- [ ] Plus AUCUN fichier > 500 l code dans tout le dépôt (`compte_ldc`).
- [ ] `CLAUDE.md` grave la règle (avec `N` empirique) + l'arbo cible.
- [ ] `dotnet build` OK, golden vert/hash inchangé, F5 OK.
- [ ] `00_etat.md` : sprint clôturé + `N` noté ; MAJ `journal/` (entrée du
      sprint refactor). Commit final.

## Commit suggéré

`refactor(sprint·global) : SS⑦ — purge C# mort, fichiers restants éclatés, règle taille gravée (N=<…>) — SPRINT CLOS`
