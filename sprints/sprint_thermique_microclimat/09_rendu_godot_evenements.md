# Tronçon ⑨ — Rendu Godot des événements météo (pluie/neige/vent/grêle/orage + manteau)

> Sprint thermique-microclimat. Conception : `docs/conception/CONCEPTION_THERMIQUE_MICROCLIMAT.md`.
> Kickoff **autosuffisant** (relançable à froid).
> Pré-requis : ⑧ CLOS (snapshot expose `weather` + `temperature` par tuile,
> protocole **0.5.0** ; golden NEUTRE inchangé `5fddfe54…`).

## Objectif

La météo vit côté MOTEUR (①→⑦) et arrive maintenant au pont (⑧), mais **rien ne se
voit** dans Godot : le ciel ne change pas, la pluie/neige ne tombe pas, le manteau
n'apparaît pas. Ce tronçon **DESSINE** l'événement météo courant + le manteau
neigeux par tuile, en lisant les blocs du snapshot. **C'est de la VUE pure** : zéro
modification Python → **golden NEUTRE par construction** (le moteur n'est pas
touché). Filet de compilation : `dotnet build Symbiose.csproj` (le F5 visuel reste
à Nico — Godot n'est pas sur la VM).

C'est le pendant « vue » des tronçons rendu précédents (litière `LitterLayer`, vie
macro `MacroLife`, butineurs `ForagerLayer`, piqûre `PiqureFlash`) : un nouveau
layer alimenté par `ApplySnapshot`, lecture TOLÉRANTE (snapshot pré-0.5.0 sans le
bloc → jardin sans météo, aucun crash).

## Données disponibles (snapshot 0.5.0, déjà au pont)

```
snap["weather"] = {
    "kind": "Pluie prolongée"|"Neige"|"Orage"|"Grêle"|"Tempête"|"Canicule"|… ,
    "intensity": float (σ, ~0..3),
    "scope": "global"|"local",          # Orage/Grêle = local (patch)
    "nebulosite": float 0..1,           # couvre le ciel (assombrir + désaturer)
    "t_air": float °C,
    "signs": [ {kind, in_weeks, signs:[…], signed:bool}, … ],   # préavis (⑩/HUD, pas ⑨)
}
snap["temperature"][tile] = {
    "snow": float 0..1,                 # manteau neigeux PAR TUILE → voile blanc
    "t_sol": [[…]],                     # grille rows×cols (réservé à ⑩ heatmap, PAS ⑨)
}
```

⑨ consomme `weather.kind`/`intensity`/`nebulosite` (ambiance globale) + `temperature[tile].snow`
(voile par tuile). `t_sol` et `signs` sont pour ⑩/HUD — **ne pas les toucher ici**.

## Modèle de rendu

### A. Ambiance globale (un CanvasLayer plein écran, repère ÉCRAN)

L'événement est global (météo uniforme sur le monde, comme T_air) → un overlay
**plein écran** au-dessus du monde, sous le HUD. Deux effets superposés :

- **Nébulosité** → assombrir/désaturer : un `ColorRect` plein écran gris-bleu dont
  l'alpha ∝ `nebulosite` (ciel clair 0.10 ≈ invisible ; Pluie 0.90 / Tempête 0.80
  ≈ jour gris). Transition douce (tween d'alpha sur ~1 s au changement de snapshot,
  pas de saut brutal — cohérent avec les fondus naissance/mort).
- **Précipitations/vent** selon `kind` (intensité ∝ `intensity`, plafonnée) :
  - **Pluie prolongée / Orage** : traits verticaux/inclinés qui tombent (un
    `GpuParticles2D` ou simple draw de segments défilants). Orage += flashs
    d'éclair brefs (un `ColorRect` blanc pulsé) + inclinaison (vent).
  - **Neige** : flocons lents qui dérivent.
  - **Grêle** : grains rapides, rebond bref au sol (local mais on peut rendre
    global simple au début — affiner si Nico veut le patch localisé).
  - **Tempête** : stries de vent horizontales rapides, pas de gouttes.
  - **Canicule / Sécheresse / Beau temps / Gelée / Redoux** : pas de
    précipitation (Canicule = voile chaud léger optionnel, surtout `nebulosite`
    basse → ciel franc). **Démarrer minimal** : ne rendre que pluie/neige/grêle/
    orage/tempête, le reste = juste la nébulosité.

> **Pédagogie Godot** (Nico découvre) : un `CanvasLayer` se dessine en coordonnées
> ÉCRAN, **indépendant de la caméra** (zoom/pan du monde ne le bougent pas) — exactement
> ce qu'on veut pour une ambiance « devant la vitre ». À comparer au monde
> (`Node2D _objects`) qui, lui, vit en coordonnées MONDE et suit la caméra. Le HUD
> (`WorldView.Hud.cs`) est déjà un CanvasLayer : s'en inspirer pour la couche.
> `GpuParticles2D` = système de particules GPU (pluie/neige) ; si trop d'inconnu,
> commencer par un `_Draw()` manuel de N traits défilants (plus simple à lire).

### B. Manteau neigeux par tuile (repère MONDE, sous les plantes)

`temperature[tile].snow ∈ [0,1]` → **voile blanc** sur la tuile (∝ snow). Même
esprit que `LitterLayer` (batch par tuile, repère monde, sous les plantes/YSort) :
un `Polygon2D`/`ColorRect` blanc semi-transparent couvrant l'emprise de la tuile
(`_origins[tile]` + dimensions), alpha ∝ snow. À snow=0 → invisible (cas nominal
hors hiver). Optionnel : teinter aussi le sol plutôt qu'un calque — choisir le plus
simple. Le manteau est SOUS les plantes (elles dépassent de la neige).

### C. Câblage dans `ApplySnapshot` (WorldView.Snapshot.cs)

Sur le modèle des blocs existants (lecture tolérante `ContainsKey`) :

```csharp
if (snap.ContainsKey("weather"))
    _weatherLayer?.SetWeather(snap["weather"].AsGodotDictionary());
if (snap.ContainsKey("temperature"))
    _snowLayer?.SetSnow(snap["temperature"].AsGodotDictionary(), _origins);
```

## Fichiers (un fichier = une responsabilité, < ~350 ldc pur)

- **`visuals/WeatherLayer.cs`** (neuf) — CanvasLayer d'ambiance globale : `SetWeather(GDict)`
  (nébulosité + précip selon kind/intensity). Namespace `Symbiose`, chemin `res://`.
- **`visuals/SnowLayer.cs`** (neuf) OU partial `WorldView.Meteo.cs` — voile manteau
  par tuile (repère monde). Si très court et couplé à `_origins`/`_objects`, un
  partial `WorldView.Meteo.cs` (méthode `ApplySnow`) évite un nœud de plus — choisir
  à l'implémentation, garder cohérent avec `LitterLayer` (qui est un nœud séparé).
- **`world/WorldView.Snapshot.cs`** — 2 branches `ContainsKey` (§C).
- **`world/WorldView.cs`** (ou le partial d'init des layers) — instancier
  `_weatherLayer`/`_snowLayer` comme `_macroLife`/`_foragerLayer`/`_litterLayer`
  (chercher où ils sont créés/ajoutés et calquer : même parent, même ordre Z).

## Étapes

1. Repérer l'instanciation des layers existants (`_macroLife`, `_litterLayer`,
   `_foragerLayer`) dans `WorldView.cs`/partials → calquer pour `_weatherLayer`/`_snowLayer`
   (parent, Z-index : ambiance AU-DESSUS du monde sous le HUD ; manteau SOUS les plantes).
2. `visuals/WeatherLayer.cs` : ambiance globale (nébulosité + précip). Démarrer
   minimal (nébulosité + pluie + neige), enrichir orage/grêle/tempête ensuite.
3. Manteau neigeux par tuile (§B) — fichier neuf ou partial `WorldView.Meteo.cs`.
4. Brancher les 2 blocs dans `ApplySnapshot` (§C), lecture tolérante.
5. **Filet** : `dotnet build Symbiose.csproj` → 0 erreur (le F5 visuel = Nico).
   **AUCUN fichier Python touché** → ne PAS relancer le golden au sens « re-figer » :
   il est NEUTRE par construction (rien côté moteur). Le mentionner, ne pas le re-figer.

## Invariant golden

- **NEUTRE absolu** : ⑨ ne touche QUE du C#/Godot (la vue). Le moteur Python et le
  snapshot 0.5.0 sont inchangés → `tests/test_golden.py` ne peut pas bouger (rien
  à relancer côté moteur). Si on est tenté de modifier `data/code/` → c'est qu'on
  déborde du tronçon : s'arrêter, en parler à Nico.

## Validation

- `dotnet build Symbiose.csproj` : 0 erreur, 0 warning neuf.
- F5 (Nico) : par temps de Pluie/Neige/Orage l'ambiance change (ciel gris,
  précipitations) ; le manteau apparaît en hiver enneigé ; Beau temps ≈ inchangé ;
  zoom/pan ne décrochent pas l'ambiance (CanvasLayer écran) ; le manteau suit les
  tuiles (repère monde).

## À faire en fin de tronçon

- Mettre à jour `00_etat.md` (⑨ ✅ + confirmation NEUTRE vue + fichiers neufs +
  build OK ; F5 délégué à Nico).
- Commit : `feat(thermique) : tronçon ⑨ rendu Godot des événements météo + manteau — vue (golden NEUTRE)`.
- Écrire le kickoff `10_heatmap_temperature.md` avant le `/clear` (overlay debug F6
  `FieldOverlay` : heatmap de `temperature[tile].t_sol` + un canal manteau/t_air ;
  vue pure, NEUTRE, filet `dotnet build`).
```
