# CONCEPTION — Rendu visible : paliers d'information + travail limité à l'écran (D106)

> Figée le 2026-10-16 (`/conception D106`). **Vue C# pure** : aucune touche à
> `data/code/`, pont inchangé (à revérifier), **golden jamais re-figé**
> (référence `22768f33…`). Sprint : `sprints/perf/lod/sprint_rendu_visible/`
> (7 tronçons). Suites de : `conception_perf_rendu_plantes.md` (LOD silhouette,
> 2026-07-09) et `docs/rendu/pixelart/conception_jardin_vivant.md` (pré-cuisson T2,
> onde T3), commit `73a3f24` (semaine étalée en 7 familles).

## 1. Problème

Nico (F5 2026-10-15) : « n'afficher que ce qui est visible + une petite marge qui
anticipe le mouvement dans n'importe quelle direction » ; « en dézoomant moins de
détails, en zoomant plus de détails ». Et c'est lent : 5-6 FPS en vue d'ensemble
sur la VM, coût **antérieur** au sprint jardin vivant.

## 2. Diagnostic mesuré (2026-10-16, VM llvmpipe, `full` seed 42, 1920×1080)

Godot sous Xvfb **en temps réel** (`--print-fps`) + sonde temporaire masquant une
couche par nom (jetée, à industrialiser en T1).

| Cas | FPS | Lecture |
|---|---|---|
| ×0,5 tout affiché | 5,2-5,5 [3 runs] | ~190 ms/frame |
| ×0,5 sans `Ground` | 11,7-12,0 [3 runs] | **le sol ≈ 105 ms** |
| ×0,5 sans décor / plantes / ombres / vie macro | dans le bruit [n=1-2 chacun] | pas coupables |
| tout le monde masqué (×0,5 et ×4) | 20-26 [n=3, bruités] | **plancher fixe ~40 ms** |
| ×4 tout affiché | 12-13 [4 runs] | aucune couche seule ne pèse |

- **Sol** : ~2400 nœuds (1188 `Sprite2D` « dessus » + 1188 `Polygon2D` « flancs »
  D57, alternés dans `world/WorldView.Monde.cs` + `WorldView.Relief.cs`). L'alternance
  sprite/polygone casse le lot (batch) de Godot à chaque nœud → ~2400 envois GPU/frame.
- **Plancher fixe** : le profil C# (`dotnet-trace`) est dominé par le survol par frame
  (`WorldMouseCanvas` appelé depuis ~10 sites → `Viewport.GetMousePosition`,
  `UpdateCurseur`, `UpdateContainerLabel`, `FindPlot`). En partie **biais VM**
  (aller-retour X11) ; reste : ciel/vignette/météo plein écran, HUD.
- **VM ≠ PC de Nico** (i5-4200H + iGPU HD 4600) → la métrique de vérification
  portable est le **nombre d'envois GPU par frame** (moniteurs Godot), pas les FPS VM.

## 3. Principe pédagogique clé

Depuis la pré-cuisson (jardin vivant T2), une plante coûte **un quad texturé par
frame** quel que soit son détail. Le détail par palier se paie **à la cuisson**
(CPU, file à budget) et en **mémoire vidéo**, pas à l'affichage. Godot élimine déjà
seul du dessin les items hors écran : le culling « métier » sert à couper le
**travail C#** (application de semaine, cuisson, animation).

## 4. Décisions (Nico 2026-10-16)

- **D1 Objectif** (critère de fin, sur le PC de Nico, monde `full`) : **60 FPS à ×4
  et au-delà**, **30 FPS de ×0,5 à ×2**.
- **D2 Semaine paresseuse hors champ** : hors marge on ne fait que stocker la donnée
  de la plante ; on l'applique à son entrée dans la marge (file à budget) ou dès
  qu'on la consulte (dossier, clic).
- **D3/D4 Paliers = information, échelle CUMULATIVE** (art neuf, chaque palier garde
  les précédents et ajoute UNE catégorie) :

| Palier | Information | Visible |
|---|---|---|
| ×0,5 | présence + saison | tache teintée famille ; automne / nu en hiver |
| ×1 | port | silhouette du port (arbre, buisson, rosette, tapis, couchée, grimpante) + hauteur relative |
| ×2 | santé globale | teinte de vigueur (franc / pâle / fané / sénescent) ; floraison en taches |
| ×4 | architecture | bois (segments) + masses de feuillage ; fleurs/fruits en points |
| ×8 | organes | feuille d'espèce, fleur par famille, fruits |
| ×16 | symptômes fins | nervures, encoches de grêle, nécroses, taches de maladie, morsures, givre |
| ×32 | intime | nervures secondaires, étamines, poils / pruine |

  Données déjà au snapshot : `vitalite`, `strate`, `floraison`, `automne`, `fruits`,
  `leaf_symptoms`, segments. Les plantes restent **toujours visibles, même à ×0,5**.
- **D5 Plancher = tapis par plot** : une plante dont l'emprise projetée est trop petite
  pour être lisible au palier courant est rendue dans le **tapis de son plot** (pas
  individuellement, ni cuite) ; les grandes restent individuelles. **Un seul langage
  de tapis** : fusion avec `visuals/CouvertureLayer.cs` (tapis `couverture_sol`,
  aujourd'hui MinZoom ×1) — jamais deux tapis verts superposés.
- **D6 Périmètre** : marge proportionnelle + travail hors champ coupé pour **toutes**
  les couches ici ; paliers d'information faune / champignons / litière → sprint B.
- **Hors périmètre assumé** : ombres et vie macro (mesurées non coupables, déjà LOD
  ×4 + culling pour la vie macro, ombre enfant de sa plante) ; pas de quadtree
  (quelques centaines d'éléments, balayage linéaire).

## 5. Mécaniques de vue

- **Marge proportionnelle avec hystérésis** : rectangle visible agrandi de 25 % de
  sa taille de chaque côté pour **entrer**, 50 % pour **sortir** (pas de va-et-vient
  au bord) ; test sur l'**emprise** projetée de l'objet, plus sur son centre
  (remplace la marge fixe 400 cm de `CullPlants`, énorme à ×32).
- **Sol en un lot** : un maillage par tuile (dessus + flancs entrelacés dans l'ordre
  de peinture actuel, damier en couleur de sommet), **image identique au pixel**,
  reconstruit seulement quand le relief change ou à la rotation.
- **Plancher fixe** : souris lue **une fois** par frame (cache), survol recalculé
  seulement si souris ou caméra bougent ; couches plein écran redessinées seulement
  quand leur état change.
- **Cellules d'atlas par pose** (mémoire vent : 116 Mo vs 12,8 Mo à ×8 [51 plantes,
  n=1]) : boîte serrée par pose au lieu de l'union des 8.

## 6. Tronçons

T1 instrument · T2 sol en un lot · T3 plancher fixe · T4 marge + semaine paresseuse ·
T5 paliers bas ×0,5-×2 + tapis · T6 paliers hauts ×4-×32 + cellules par pose ·
T7 banc F5 + bilan. Golden intact partout. Ordre = mesurer → gains sûrs → art.
