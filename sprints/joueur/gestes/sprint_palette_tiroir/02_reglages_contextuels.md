# ② Réglages contextuels : graines, substrats, paillis

**Lire avant** : `CLAUDE.md`, `00_etat.md`, doc de conception §4.
**Nature** : C#. **Golden : INTACT**.

## Objectif
Les choix cachés derrière les touches S, B, N deviennent une rangée visible et
cliquable à côté de la barre, quand le geste actif en a besoin.

## État du code (vérifié le 2026-11-12)
- `world/WorldView.Actions.cs` : `CycleSeed()` (espèce pour `planter`, d'après
  `player.seeds` du snapshot), `Substrats[]` + `CycleSubstrat()` (pots/bacs),
  `Natures[]` + `CycleNature()` (pailler).
- `world/WorldView.Controls.cs` : `Key.S`, `Key.B`, `Key.N` appellent ces cycles.
- `world/WorldView.Hud.cs` (vers la ligne 292) écrit le réglage courant en texte de
  debug.
- Le stock de mulch par nature est au snapshot (bloc `paillage` ; lire
  `serialize.py`). Les icônes d'espèces existent-elles côté vue ? À vérifier ; à
  défaut, une pastille de la couleur de l'espèce + nom au survol.

## À faire
1. **Fichier neuf `world/WorldView.Reglages.cs`** : une rangée horizontale à droite
   de la barre, visible seulement si le geste actif a un réglage :
   - `planter`, `planter_conteneur` → les graines en banque (lots non vides) ;
   - `poser_pot`, `poser_bac_culture` → les substrats ;
   - `pailler` → les natures de mulch, estompées si le stock est vide (sans chiffre).
   Clic = choix ; le choix courant est encadré.
2. Brancher la rangée sur les index existants (`_seedIndex`, `_substratIndex`,
   `_natureIndex` ou leurs équivalents) : une seule source d'état.
3. **Retirer** les raccourcis S, B, N de `Controls.cs` et leur mention du HUD/aide
   (les méthodes `Cycle*` peuvent rester si la rangée s'en sert). Vérifier qu'aucune
   de ces touches n'a pris un autre sens entre-temps.
4. Banque vide ou stock vide : la rangée le montre (case vide estompée), le geste
   reste sélectionnable ; le refus vient du moteur, comme aujourd'hui.

## Vérification
`dotnet build` vert ; captures VM avec `planter` actif puis `pailler` actif
(`tools/capture_vm.sh -g <case>`), golden inchangé.

## À ne pas faire
- Pas de chiffres en HUD (stock, nombre de graines) hors mode debug.
- Ne pas changer ce que le pont reçoit (mêmes `params`).
