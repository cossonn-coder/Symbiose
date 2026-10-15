# T4 — Canicule et pluie/orage : la réponse de CHAQUE plante

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (infra T2 + onde T3), `docs/rendu/pixelart/conception_jardin_vivant.md` §5.

## Objectif
Le temps qu'il fait se lit **sur les plantes**, et pas uniformément : sous
canicule, la plante exposée et assoiffée pend ses feuilles, l'abritée tient
(hétérogénéité D104, philo #7). Sous pluie/orage, le feuillage s'alourdit et
luit, puis se relève après. Trois temps : avant (préavis déjà existant :
encart ciel `sim/ciel.py`) → pendant → après (traces brèves).

## Contexte vérifié
- Catalogue météo `data/code/sim/weather.py:120-128` : `Canicule` (global,
  sem 16-26), `Pluie prolongée` (global), `Orage` (local, convectif + vent),
  `Grêle` (local) ; snapshot `weather.kind/intensity/scope`.
- Réponse par plante : `leaf_symptoms` = liste `[{cause, intensity}]` triée
  (`sim/semiologie.py:203-248`) ; causes : `asphyxie`, `secheresse`,
  `maladie`, `ravageurs`, `gel`, `grele`, `chlorose`, `ombre`, `senescence`…
  Déjà mappées en teinte/désaturation par `PlantRenderer.Palette.cs`.
- `visuals/WeatherLayer.cs` (précipitations écran, 197 LDC) ; `PuddleLayer.cs`
  (flaques au sol).

## À faire (intention)
- **Variantes de pose cuites** (infra T2, × 8 flexions de T3) — PAS une
  déformation par frame :
  - **canicule** : si `weather.kind == "Canicule"` ET la plante porte
    `secheresse` (intensité i) → feuilles qui pendent/se referment ∝ i (angle
    des feuilles/limbe réduit au dessin). Plante sans `secheresse` = intacte.
  - **pluie/orage** : feuillage alourdi (légère retombée des extrémités) +
    reflets humides (1-2 px clairs de la palette) pendant l'épisode et un
    court « après » (se ressuie sur quelques secondes de jeu).
- La variante s'ajoute aux clés d'invalidation T2 (une plante ne recuit que si
  sa variante change), toujours via la **file à budget** (jamais toutes à la
  fois — le début d'une canicule salit tout le jardin : étaler).
- `WeatherLayer` : pluie inclinée par le vent réel (T3), gouttes qui
  éclaboussent au sol par endroits (palette, Bayer) ; orage : un éclair = seul
  flash autorisé, bref.
- Animations = signal : sans épisode, aucune de ces animations ne tourne.

## Critère de réussite
Banc T0 : forcer une canicule et une pluie (bancs / commandes de debug
existants, sinon un argument de capture) → PNG où des plantes voisines
répondent **différemment** selon leur état. Mesures (Mo de variantes, pic de
file au début de l'épisode) dans `00_etat.md`. `dotnet build` vert, golden
intact. Question F5 Nico : « on sent la chaleur / la pluie sur les plantes ? ».

## NE PAS
- Lire un état météo inventé : tout vient du snapshot (`weather`, `leaf_symptoms`).
- Appliquer la même réponse à toutes les plantes (c'est tout l'intérêt).
- Toucher au moteur Python / golden ; GDScript ; `test_epaisseur_500ans` ;
  fichiers > 400 LDC (variantes dans un fichier dédié, ex. `PlantRenderer.Meteo.cs`).
