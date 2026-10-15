# T6 — Paliers hauts ×4 · ×8 · ×16 · ×32 + cellules d'atlas par pose

> Lire `CLAUDE.md`, `00_etat.md` (dont ce que T5 a posé), `docs/perf/lod/conception_rendu_visible.md`
> §4-§5. Vue C# pure. Golden intact.

## Objectif
1. Prolonger l'échelle cumulative de T5 :
   - **×4 architecture** : bois (segments) + **masses** de feuillage ; fleurs/fruits en points.
   - **×8 organes** : feuille à la forme de l'espèce, fleur par famille, fruits.
   - **×16 symptômes fins** : nervures, encoches de grêle, bords nécrosés (`gel`, `seche`),
     taches (`maladie`), morsures (`ravageurs`), givre détaillé — depuis `leaf_symptoms`.
   - **×32 intime** : nervures secondaires, étamines, poils / pruine (texture de surface,
     table par espèce côté vue, cosmétique, déterministe).
   Beaucoup existe déjà sous des seuils épars (`LeafShapeMinZoom`, `LeafOutlineMinZoom`,
   `FlowerShapeMinZoom`, symptômes de `.Organs`/`.Froid`/`.Meteo`) : les **ranger** sur
   l'échelle (un palier = une information) et ajouter ce qui manque ; supprimer les seuils
   devenus redondants SEULEMENT s'ils sont remplacés (pas de code mort laissé ; ne rien
   jeter qui sert encore).
2. **Cellules d'atlas par pose** (`visuals/PlantBaker.cs`, `PlantRenderer.Bake.cs`) :
   aujourd'hui la boîte d'atlas = union de la pose droite et de la plus couchée, × jusqu'à
   8 poses → 116 Mo au vent vs 12,8 Mo au calme à ×8 [51 plantes, n=1]. Chaque pose
   reçoit sa **boîte serrée** (+ son décalage d'ancrage pour que la plante ne saute pas
   d'une pose à l'autre). Garder `MaxSidePx`/`MaxAtlasPx` et le repli « dessin direct ».

## Règles
- Écrire dans le(s) partial(s) de paliers créé(s) en T5 ; aucun fichier > 400 LDC,
  `.Organs.cs` ne grossit pas.
- Coût de cuisson : mesurer le temps du pinceau par plante à ×16/×32 sur un arbre
  (référence T2 jardin vivant : ~0,06 ms/segment) ; si un palier fait exploser la file,
  simplifier le dessin plutôt que relever le budget.

## Vérification
- Captures VM d'une même plante (fruitier + herbacée + plante malade/grêlée — bancs
  `effondrement` seed 12345 pour la grêle) à ×4, ×8, ×16, ×32 : chaque palier ajoute
  son information, rien ne disparaît en zoomant.
- Mémoire du cache au vent à ×8 (`-v 0.9`) avant/après ; FPS ×4 et ×16 (`perf_vm.sh`).
- Pas de saut de pose visible au vent (captures successives).

## Ne pas faire
Pas d'insectes posés ni de faune (sprint B). Pas de nouvelle donnée moteur.

## Fin de tronçon
Maj `00_etat.md`, commit. Point F5 : « zoomer = voir plus ? » à chaque cran.
