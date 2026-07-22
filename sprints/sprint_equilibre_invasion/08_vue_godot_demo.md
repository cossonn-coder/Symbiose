# Tronçon ⑧ — Vue Godot (pailler/broyer + rendu mulch/BRF + abri faune) + démo sud

**Prérequis** : `CLAUDE.md`, `00_etat.md`, `docs/faune/trophique/conception_equilibre_invasion.md`
§8/§9. Rappel : Godot est une VUE (Option B), le moteur reste Python. Patrons :
`world/WorldView.cs` (+ partials), `visuals/PlantRenderer.cs`,
`visuals/FieldOverlay.cs`, `visuals/MacroLife.cs`, `core/SimBridge.cs`,
`world/WorldView.Controls.cs`. **Règle projet** : tout sprint finit par sa vue
Godot (golden intact). Filet de compilation : `dotnet build Symbiose.csproj`
(F5 visuel = Nico).

## Objectif
Rendre le levier paillage JOUABLE et OBSERVABLE :
1. **Gestes cliquables** : `pailler` (zone) et `broyer` (bois) via le protocole
   d'actions du pont (bump `ENGINE_VERSION`) → `SimBridge` → commande serveur.
2. **Rendu du mulch au sol** : texture de paillage par plot selon la profondeur
   et la **nature** (BRF ligneux / paille dorée / aiguilles) — pixel-art, filtre
   Nearest. Exposé au snapshot par le pont (bloc `paillage` par plot : profondeur
   + nature).
3. **Abri faune visible** : la vie macro (`MacroLife`) s'agrège sur les zones
   paillées (déjà émergent côté moteur ⑥ — ici on s'assure que le rendu le montre).
4. **Démo (D7)** : `data/code/main.py::build_world_full` gagne une **planche plein
   sud paillée** avec **tomate/basilic/poivron/tournesol** (démonstrateur du
   levier ; ce sont les cultures qui mouraient sans mulch).

## Fichiers à toucher
- **Python** : `tools/simserver/serialize.py` (+ `version.py`) — exposer le champ
  `paillage` (profondeur+nature) par plot dans le snapshot ; commandes d'action
  `pailler`/`broyer` dans `tools/simserver/commands.py` + `server.py` ; bump
  protocole. `data/code/main.py` — planche sud paillée (hors golden smoke).
- **C#** : `core/SimBridge.cs` (nouvelles actions), `world/WorldView.Controls.cs`
  (bind clics/touches), un rendu de mulch (nouveau `visuals/MulchLayer.cs` ou
  extension de la couche sol), `visuals/MacroLife.cs` (abri).

## Golden
**INTACT** (côté Python : serialize/commands = pont, hors tick ; `build_world_full`
hors golden smoke). Vérifier `test_golden`/`test_population` inchangés +
`test_sim_server` vert (masquer les champs non déterministes déjà gérés) +
`dotnet build` vert.

## NE PAS
- Pas de logique de simulation en C# (Option B). Pas de GDScript. Pas de fraction
  de zoom. Ne pas planter la démo dans le monde smoke/golden.

## Vérif / F5 (Nico)
`config="full"` → planche sud paillée visible ; pailler/broyer au clic ; le mulch
freine les adventices sur la planche (comparer à une planche nue) ; la faune
s'abrite sous le mulch en plein soleil ; `config="propre"` pour observer les
cultivées seules. Clôture du sprint : maj `00_etat.md`, `DETTE.md` (D69 →
implémenté), `journal.md`.
