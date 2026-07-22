# ⑧ — Vue Godot (relief+altitude, flaque, marais, sphaigne/aulne/faune, gestes)

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + CE fichier. Conception :
> `docs/champs/eau/conception_hydrologie_marecage.md` §7. Prérequis : ①→⑦ faits (les
> blocs snapshot existent). **PUR-VUE, golden NEUTRE. F5 = Nico.**

## Objectif
Rendre visible tout ce que le moteur a posé : le micro-relief, les flaques, les
marécages, la guilde marécageuse. Aucun moteur touché (hors lecture snapshot déjà
faite aux tronçons précédents).

## Fichiers (C#, à la racine du repo — Godot est une VUE)
- `world/WorldView.Relief.cs` (D57) : intégrer `altitude` à la base du relief —
  `surface = altitude + epaisseur` (le terrain a des creux/bosses même sans humus).
  Réutiliser `ReliefRisePx`/l'exagération commune.
- NOUVEAU calque flaque (ex. `visuals/PuddleLayer.cs`) : lit le bloc `eau_surface`
  → lame d'eau translucide bleutée réfléchissante ∝ profondeur, au-dessus du plot
  (recalée sur le relief via l'offset D57).
- Rendu marais : `marais_memory` haut → assombrir/teinter le sol (tourbe) — soit
  dans `WorldView.Monde`/`Relief`, soit un overlay dédié.
- `visuals/MacroLife.cs` : moustiques (nuée fine) + libellules (vol stationnaire)
  — sprites échantillonnés (blocs faune du snapshot ④).
- Sphaigne (tapis couvre-sol) + aulne (silhouette d'arbre) : `PlantRenderer` /
  placeholders selon l'espèce (⑤).
- Gestes `creuser`/`drainer` : brancher au picking existant (curseurs), feedback.
- Overlays debug F6 : ajouter `altitude`, `eau_surface`, `marais` (palettes dédiées,
  cf. D45).

## Golden
**NEUTRE** (pur-vue, C# hors golden Python). `python3 -m tests.test_golden`
inchangé. `dotnet build Symbiose.csproj` VERT (filet de compilation).

## Ce qu'il NE faut PAS faire
- Ne pas recalculer d'hydrologie côté C# (tout vient du snapshot).
- Ne pas disperser l'offset de relief (helper unique `ReliefRisePx`, D57).
- Respecter la bande de taille (un partial/calque dédié par responsabilité).

## F5 (Nico)
- Le micro-relief altitude se lit-il (cuvettes/bosses) ? Les flaques brillent-elles
  dans les creux ? Le marais « noircit »-il ? Sphaigne/aulne/moustiques/libellules
  crédibles ? Gestes creuser/drainer lisibles ? Calibrage exagération + palettes.
