# ④ Vue Godot : la chronique dans le rapport C

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`. **Prérequis** : ② fait.
**Golden : INTACT** (C# seul).

## Objectif
La touche C copie aussi la chronique, pour les runs longs de Nico au PC.

## À faire
1. `world/WorldView.PerfReport.cs` : si `rep` contient `"chronique"`, ajouter
   son `texte` tel quel, sous un en-tête `[chronique]`, après `AppendAnnees`.
   Aucune mise en forme côté C# (le formateur est Python, ②). Pont plus ancien
   sans la clé → rien, sans erreur.
2. `dotnet build Symbiose.csproj` sans nouvel avertissement.
3. Clôture du sprint : `00_etat.md`, `journal.md` + entrée `journal/`,
   `DETTE.md` (D127 : outillage livré ; ce qui reste), `BACKLOG.md`.

## F5 (Nico)
Lancer un run turbo (par ex. `verger_mur`), appuyer sur C après quelques années,
coller le rapport : la section `[chronique]` liste les effectifs, les causes et
les disparitions.

## Ne pas faire
Recalculer quoi que ce soit côté C# ; toucher au moteur.
