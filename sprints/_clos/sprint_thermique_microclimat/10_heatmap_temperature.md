# Tronçon ⑩ — Heatmap de la température du SOL (debug, F7) — DERNIER du sprint

> Sprint thermique-microclimat. Conception : `docs/champs/climat/conception_thermique_microclimat.md`.
> Kickoff **autosuffisant** (relançable à froid).
> Pré-requis : ⑨ CLOS (rendu météo : `WeatherLayer` ambiance écran + `SnowLayer`
> manteau par tuile ; snapshot 0.5.0 expose `weather` + `temperature[tile]`).
> **VUE PURE → golden NEUTRE par construction** (zéro fichier Python touché).

## Objectif

La **carte de température du sol SPATIALISÉE** (`temperature[tile].t_sol`, grille
rows×cols issue du tronçon ⑤) existe au pont mais ne se VOIT pas en heatmap. La
heatmap debug actuelle (F6, `FieldOverlay`) affiche le champ `temperature` du
serveur, qui est la **T de l'AIR hebdo, UNIFORME** (le HUD l'annonce déjà :
« air hebdo (uniforme — temp. du sol : à venir) » — cf. `WorldView.Hud.cs::
UpdateFieldHud`, branche `if (nom == "temperature")`). Ce tronçon dessine enfin
la **vraie carte thermique du sol**, plot par plot (coin chaud/sec vs frais/
ombragé/humide) — l'« à venir » devient « là ».

C'est de la VUE pure : on lit `temperature[tile].t_sol` du snapshot, déjà calculé.
**Aucune modification Python.** Filet : `dotnet build Symbiose.csproj` (F5 = Nico).

## Pourquoi un overlay SÉPARÉ (et pas un champ de plus dans F6)

`FieldOverlay` (F6) est alimenté par la commande serveur **`fields`** (machine de
requêtes maître/esclave dédiée, `WorldView.Hud.cs`/`_Process`), au format
`{tile: {rows, cols, values:[…]}}`. Le `t_sol`, lui, arrive **dans le snapshot**
(bloc `temperature[tile].t_sol = [[…], …]`, grille 2D row-major), à chaque semaine,
SANS requête. Mélanger les deux sources dans `FieldOverlay` casserait son contrat
(une seule grille « courante » venue de `fields`). → **overlay dédié**, alimenté
par `ApplySnapshot` comme `SnowLayer`/`LitterLayer` (le bon patron pour une donnée
du snapshot). Les deux heatmaps COEXISTENT : F6 = air uniforme (introspection
champs), **F7 = sol spatialisé** (snapshot). C'est voulu — elles disent deux choses.

## Données disponibles (snapshot 0.5.0, déjà au pont)

```
snap["temperature"][tile] = {
    "snow":  float 0..1,        # manteau — déjà rendu par SnowLayer (⑨), PAS ici
    "t_sol": [[°C, …], …],      # grille rows×cols de la T de SURFACE (⑤) — ⑩
}
```

`t_sol` est une **liste de lignes** (row-major) : `t_sol.Count` = rows,
`t_sol[r].Count` = cols, `t_sol[r][c]` = °C du plot (r,c). (Même forme que celle
dont `SnowLayer` déduit déjà rows×cols.)

## Modèle de rendu (calque exact de `FieldOverlay`)

`visuals/SoilTempOverlay.cs` (neuf) — `Node2D`, ZIndex 3 (comme `FieldOverlay` :
au-dessus du sol/ombre, sous vie macro/plantes), `Visible = false` par défaut.
- `SetTemperature(GDict temperature, Dictionary<string,Vector2> origins)` : mémorise
  la grille + origins, calcule `GridMin/GridMax` (pour la légende), `QueueRedraw`.
- `_Draw()` : pour chaque tuile, pour chaque plot (r,c), un **losange** projeté
  `WorldToScreen(org + (c+0.5, r+0.5)·PlotCm)` teinté par interpolation entre les
  pôles de la palette **temperature** — **RÉUTILISER** `FieldOverlay.PaletteOf("temperature")`
  (froid `#3a6fd8` → chaud `#d83a3a`, **échelle FIXE −5..35 °C**). Mêmes offsets de
  losange (`n/e/s/o` = ±TileWPx/2, ±TileHPx/2) et même `Alpha = 0.7` que
  `FieldOverlay._Draw` — copier la boucle, seule la SOURCE de la grille change
  (snapshot `t_sol[r][c]` au lieu de `values[r*cols+c]` de la commande `fields`).

> Échelle FIXE −5..35 °C (pas auto) : une carte météo comparable d'une semaine à
> l'autre, exactement comme le champ `temperature` de `FieldOverlay` (leçon t6·C3 :
> l'auto-échelle étale le bruit d'un champ quasi uniforme sur toute la palette).
> Clamp aux bornes (une canicule à 36 °C sature au pôle chaud, n'extrapole pas).

## Câblage

- **`visuals/SoilTempOverlay.cs`** (neuf) — l'overlay (ci-dessus). Namespace `Symbiose`.
- **`world/WorldView.Meteo.cs`** — champ `private SoilTempOverlay _soilTempOverlay;`
  + instanciation dans `BuildMeteoLayers()` (calquer `_fieldOverlay` : `new …{ ZIndex=3,
    Visible=false }; AddChild(…)`) + helper `ApplySoilTemp(GDict temperature) =>
    _soilTempOverlay?.SetTemperature(temperature, _origins);`.
- **`world/WorldView.Snapshot.cs`** — dans la branche `if (snap.ContainsKey("temperature"))`
  qui existe déjà (⑨), AJOUTER l'appel `ApplySoilTemp(snap["temperature"]…)` à côté de
  `ApplySnow(…)` (même bloc, même GDict — un seul `ContainsKey`).
- **`world/WorldView.Controls.cs`** — nouvelle touche **F7** (LIBRE, vérifié) :
  `case Key.F7: ToggleSoilTemp(); break;` (sous le `case Key.F6:`).
- **`world/WorldView.Hud.cs`** OU `WorldView.Meteo.cs` — `ToggleSoilTemp()` (calquer
  `ToggleFieldOverlay` : flip `Visible`, un `GD.Print`). **Légende** : optionnelle au
  début — soit un mini-Label « carte T sol (debug, F7) : froid −5 … chaud 35 °C » réutilisant
  la rampe BBCode de `UpdateFieldHud`, soit rien (la palette F6 sert déjà de clé de
  lecture). Garder MINIMAL ; enrichir si Nico le demande au F5.
- **`world/WorldView.cs`** — bump `Build` (« thermique ⑩ — heatmap T sol (F7) »).
- **`world/WorldView.Hud.cs`** — mettre à jour la ligne `legend.Text` (ajouter « F7
  carte T sol ») et, dans `UpdateFieldHud`, RETIRER (ou nuancer) le « temp. du sol :
  à venir » de la branche `temperature` (c'est désormais ARRIVÉ via F7).

## Étapes

1. `visuals/SoilTempOverlay.cs` : copier la boucle `_Draw` de `FieldOverlay`,
   changer la source (snapshot `t_sol[r][c]`), figer la palette temperature.
2. `BuildMeteoLayers()` : instancier `_soilTempOverlay` (ZIndex 3, caché).
3. Brancher `ApplySoilTemp` dans la branche `temperature` existante (⑨).
4. Touche **F7** + `ToggleSoilTemp` ; legend.Text + nuance du HUD `temperature`.
5. **Filet** : `dotnet build Symbiose.csproj` → 0 erreur, 0 warning neuf.
   **AUCUN fichier Python touché** → golden NEUTRE, NE PAS le re-figer (le mentionner).

## Invariant golden

- **NEUTRE absolu** : ⑩ ne touche QUE du C#/Godot. Snapshot 0.5.0 et moteur
  inchangés → `tests/test_golden.py` ne peut pas bouger. Tenté de modifier
  `data/code/` → on déborde : s'arrêter, en parler à Nico.

## Validation

- `dotnet build Symbiose.csproj` : 0 erreur, 0 warning neuf.
- F5 (Nico) : F7 affiche la carte thermique du SOL ; en plein été un coin
  sud/sec/ensoleillé est plus ROUGE qu'un coin nord/ombragé/humide (≠ l'aplat
  uniforme de F6 `temperature`) ; zoom/pan/rotation suivent (repère monde, comme
  F6) ; F7 de nouveau → carte masquée, coût nul.

## À faire en fin de tronçon (= fin de SPRINT)

- Mettre à jour `00_etat.md` (⑩ ✅ + NEUTRE vue + fichiers + build OK ; F5 délégué).
- **SPRINT THERMIQUE & MICROCLIMAT CLOS** : récap dans `00_etat.md` (les 10 tronçons,
  les knobs introduits, les goldens successifs, la dette ouverte : D37 vent continu,
  D38 rosée/hygrométrie, container.py 372 ldc à éclater, `test_pommier_fruite`
  préexistant à traiter hors sprint).
- **Mettre à jour `journal.md`** (entrée de clôture du sprint — mémoire partagée).
- Commit : `feat(thermique) : tronçon ⑩ heatmap T sol debug (F7) — vue (golden NEUTRE) ; SPRINT CLOS`.
- Proposer à Nico la suite (BACKLOG.md / DETTE.md), PAS d'enchaînement automatique.
