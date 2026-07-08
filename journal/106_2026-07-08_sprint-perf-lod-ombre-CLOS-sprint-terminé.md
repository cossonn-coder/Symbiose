# 2026-07-08 — Sprint PERF : LOD des émetteurs d'ombre (D67, ①→③) — SPRINT TERMINÉ

> `/sprint-auto sprint_perf_lod_ombre`. Retour à la perf pure après D69 (invasion).
> Golden départ `33c0ea6f…` → final `24ec11e7…` (re-figé maîtrisé au ②, annoncé).

## Objectif

`LightField.compute` pèse ~½ tick à l'an 6 (table `profile_monde`). D66② avait
coupé « combien d'obstacles je VISITE par échantillon » (spatial hash, bit-identique) ;
D67 coupe « combien d'obstacles EXISTENT » = **LOD asymétrique** : sous un seuil de
*pouvoir ombrageant*, une plante **REÇOIT** toujours la lumière mais n'**ÉMET** plus
d'ombre. Approximation de modèle → PAS bit-identique → golden re-figé maîtrisé.

## Tronçons

- **① Découplage dormant + bras fidélité — golden INTACT `33c0ea6f…`.**
  `fields/light.py:compute` sépare `receivers` (TOUTES les vivantes, réception
  inchangée) et `emitters` (pouvoir `h × canopy_radius × foliage_density ≥
  SHADING_POWER_MIN`, ordre de `infos` préservé). La boucle « lumière reçue » itère
  `receivers` ; `order`/`ObstacleIndex` et le scatter sol itèrent `emitters` ; cache
  géométrique laissé sur `infos` (sur-ensemble correct). Constante `SHADING_POWER_MIN`
  = **0.0** au départ = **LOD dormant** (`emitters == infos` ordre exact → bit-identique,
  invariant D3). Banc `tools/diag_lod_ombre.py` (5 critères D6 : trajectoire N + bande
  D5, dérive `light_received` à monde figé, coups vis B carence lumineuse, gain ms/tick
  net, nouvelles plantes/saison), hors-ligne lecture seule. Test `tests/test_lod_ombre.py`
  (invariant dormant 0.0 ≡ 1e-9 bit-à-bit + mécanisme actif GLOBAL : seuil élevé ⇒
  `emitters<receivers` ⇒ reçue↑ ET sol↑ sur la scène — assertion agrégée car sur une
  tuile 3 semis coupés peuvent n'ombrer que le sol). Commit `cc72a28`.

- **② Calibrage + activation — golden RE-FIGÉ MAÎTRISÉ `33c0ea6f…`→`24ec11e7…`.**
  Calibrage piloté par le banc (script batch jetable : grandit OFF une fois, sonde
  la distribution, balaie 4 seuils an 6). **Distribution du pouvoir à l'an 6**
  (config=full, 636 plantes vivantes) : falaise nette **p80=37.4** (semis, ~80 % des
  plantes) → **p90=262** (structurantes), max 7651. `SHADING_POWER_MIN = 37.5` =
  plus grand seuil coupant TOUT le cluster de semis sans mordre sur les structurantes.
  Mesures @37.5 : N plateau **587→689** (bande D5 [521, 704] → DANS) ; gain
  **+17.9 % ms/tick** (567→~465 ms net à l'équilibre propre) ; dérive `light_received`
  **moy 0.68 %** (négligeable ; max 131 % = 1 seule plante de sous-étage sensible,
  identique à tous les seuils = dérive localisée, PAS systémique) ; **vis B préservée**
  (139 coups vs 112 off — non effondrée). S=299 écarté (+6 % de gain seulement mais ×3
  dérive et vis B ÷2 → mord les structurantes ; « le gain marginal ne vaut plus la
  dérive »). **`population_hash` INCHANGÉ** `1aa4997d…` : contrairement à l'anticipation
  du kickoff, le scénario du test population n'exerce pas la dérive LOD → golden = seul
  hash bougé. Commit `336c329`.

- **③ Vue Godot — golden INTACT `24ec11e7…`, pont additif 0.5.21.**
  `serialize.py:_snapshot` expose `emitteur: bool` par plante vivante = miroir EXACT
  de la métrique `fields/light.py` (densité réutilisée, pas de recalcul → lecture pure
  d'un dérivé, golden NEUTRE). `version.py` : `ENGINE_VERSION 0.5.20→0.5.21` (additif,
  binaire pré-0.5.21 ignore le champ). C# : `WorldView.Snapshot.cs` lit `emitteur`
  (défaut `true` si absent = compat) ; `WorldView.Controls.cs` toggle debug **F9**
  (F3/F4/F6/F7 déjà prises) ; `PlantRenderer.cs` teinte `SelfModulate` bleu-gris des
  NON-émettrices sous le toggle (n'entre pas en conflit avec les fondus naissance/mort).
  `test_sim_server` **247/247**, `dotnet build` vert (0/0). Commit `4f82511`.

## Vérifications finales

- Golden final **`24ec11e7…`**, `population_hash` `1aa4997d…` (inchangé).
- Suites vertes : `test_golden`, `test_lod_ombre`, `test_ombre_maison`,
  `test_phototropisme`, `test_scatter_lumiere_sol`, `test_sim_server` 247/247.
- `dotnet build Symbiose.csproj` vert (0 erreur / 0 avertissement).
- Refactor auto-léger **no-op** : tous les fichiers touchés ≤ 300 LDC pur 🟢
  (serialize 260, PlantRenderer 248, light 225, Snapshot 218, Controls 150,
  diag_lod_ombre 141, test_lod_ombre 75).

## Incidents d'exécution (orchestrateur)

- 1er sous-agent ① coupé par une limite de session en plein travail (light.py +
  test partiels, banc manquant). L'orchestrateur a repris : light.py était complet
  et correct, le test légèrement trop strict (assertion « reçue↑ » par tuile) →
  corrigé en agrégat de scène ; banc écrit par l'orchestrateur.
- Sous-agent ② revenu sans écrire sur disque (git propre) → calibrage refait par
  l'orchestrateur via script batch efficace (OFF grandi une fois).

## Reste F5 = Nico

- **F4** : le ms/tick doit BAISSER au fil des années vs avant D67 (~+18 % au ②).
- **F9** (toggle debug neuf) : teinte les semis sous-seuil que le LOD écarte des
  boucles géométriques (posture « affichage technique »).

**D67 ✅ FAIT (Python complet + vue Godot).** LightField poste #1 depuis `761bbe9`
allégé de ~18 %.
