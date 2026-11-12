# ① Le tiroir par familles

**Lire avant** : `CLAUDE.md`, `00_etat.md`, doc de conception §3.5 et §4.
**Nature** : C#. **Golden : INTACT**.

## Objectif
Un panneau qui montre tous les gestes ouverts, rangés par familles, d'où l'on
choisit un geste ou on le met en case.

## État du code (vérifié le 2026-11-12 ; revérifier, le sprint ① a pu le bouger)
- `world/WorldView.Palette.cs` (189 LDC) : `CanvasLayer` « Palette » (Layer 6),
  `VBoxContainer` en (10,150), `_slots[10]` (index dans `Gestes[]` ou −1),
  `RebuildPaletteIcons`, `CycleSlots`, menu clic droit `_editMenu` /
  `OnEditMenuChoisi`, `ApplyGestesDebloques` (lit `player.gestes_debloques`).
- `world/PaletteLayout.cs` : persistance `user://palette.json` (par verbe).
- `world/GesteIcon.cs` (269 LDC) : `Button` 44 px, dessin procédural par famille.
- `world/WorldView.Actions.cs` : `Gestes[]`, `SelectGeste(idx)`, `_gesteIndex`.
- `world/WorldView.Controls.cs` (212 LDC) : touches 1-9/0 → cases ; `Tab` → `CycleSlots`.
- Le snapshot porte `player.familles` et `player.gestes_pressentis` (sprint ①,
  forme exacte : lire `tools/simserver/serialize.py` et `version.py`).
- Panneaux de consultation existants (modèle de style) : `world/ConsultationPanel.cs`.

## À faire
1. **Fichier neuf `world/WorldView.Tiroir.cs`** (partial) + si besoin un contrôle
   `world/TiroirPanel.cs` : panneau ancré à droite de la barre, fermé par défaut.
   Une rangée par famille (ordre du pont), chaque rangée = les `GesteIcon` des
   gestes OUVERTS de la famille. Les familles sans geste ouvert ni pressenti ne
   s'affichent pas. Pas de texte permanent : le nom de la famille et du geste
   n'apparaît qu'au survol (philo #5).
2. **Ouverture** : un bouton en bas de la barre + une touche libre (vérifier dans
   `WorldView.Controls.cs` ; proposer `Q` ou `²` si libres, sinon une autre) ;
   `Échap` ou un clic hors du tiroir le ferme. Le tiroir ne met pas le jeu en pause.
3. **Clic gauche** sur un geste du tiroir : il devient le geste actif **même s'il
   n'a pas de case** (aujourd'hui la sélection passe par les cases : découpler
   « geste actif » de « case active »). Le tiroir se ferme.
4. **Clic droit** sur un geste du tiroir : menu « mettre en case 1…0 » ; persister
   par `PaletteLayout`. Le clic droit sur une case de la barre garde son menu.
5. La barre met en évidence le geste actif s'il y est ; sinon le bouton du tiroir
   porte l'icône du geste actif.
6. Reconstruire le tiroir seulement quand l'ensemble des gestes ouverts change
   (empreinte, comme la barre) — jamais par image ni par snapshot identique.

## Vérification
`dotnet build` vert ; captures VM tiroir ouvert/fermé sur le banc `acces_gestes`
(ou `palette_gestes`) ; golden inchangé.

## À ne pas faire
- Pas de silhouettes (tronçon ③), pas de réglages (②), pas de nouvelles icônes.
- Ne pas casser les touches 1-0 ni `Tab`.
