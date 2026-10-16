# 2026-10-16 — Sprint RENDU VISIBLE (D106) — CLOS

`/sprint-auto`, T1→T7. Vue C# pure, `data/code/` intouché. **Golden `22768f33…`
jamais re-figé**, `dotnet build` vert à chaque tronçon. Doc :
`docs/perf/lod/conception_rendu_visible.md` ; état, mesures et bilan :
`sprints/perf/lod/sprint_rendu_visible/00_etat.md`.

- **T1 instrument** (`a5fa36b`) : F4 affiche frame ms (horloge murale — le
  `delta` Godot surestimait les FPS), draw calls, objets, primitives ; Maj+F4
  cycle 8 cas de masquage ; `tools/perf_vm.sh` (+ `lib_vm_godot.sh` partagé).
- **T2 sol en un lot** (`7868373`) : ~2400 nœuds → 1 maillage par tuile,
  damier en shader de fragment, arrondi au pixel par sommet reproduit côté CPU ;
  0 pixel de différence sol seul [10 captures]. ×0,5 : 3825 → 1456 draw calls.
- **T3 plancher fixe** (`8d49ab9`) : `GetMousePosition` (aller-retour X11, 75 %
  des échantillons C#) remplacé par la position des événements ; survol
  recalculé seulement sur changement ; météo au repos ne repeint plus l'écran.
- **T4 marge + semaine paresseuse** (`4b6e402`) : `MargeVue` unique (+25 % pour
  entrer / +50 % pour sortir), plante hors marge mise à jour à son entrée ;
  `BakeQueue` borné à la marge ; trou au bord au pan corrigé. ×8 : maj plantes
  ~54 → 13-15 ms/semaine [2 runs].
- **T5 paliers bas** (`7912b1a`) : ×0,5 tache d'espèce + saison, ×1 port,
  ×2 santé + fleurs ; plante < 3 px → tapis de son plot fusionné à
  `couverture_sol`. Rayon et hauteur lus sur les segments (snapshot sans
  `CanopyRadiusCm`, `height_cm` ≠ bois dessiné).
- **T6 paliers hauts** (`25c5679`) : ×4 masses, ×8 feuille/fleur/fruit d'espèce,
  ×16 nervures + dégâts (grêle, gel, nécrose `secheresse`, givre), ×32 étamines
  et poils ; cellules d'atlas par pose (pied fixe au vent). Prémisse réfutée :
  gain mémoire ~11 % [n=1] seulement — c'est le nombre de poses qui coûte.
- **T7 banc + bilan** (`5d9fd6e`) : touche **L** = planche des paliers
  ×0,5 → ×32 sur la plante visée. VM [2 runs × 9 cas] : ×0,5 5,1-5,4 →
  11,2-13,2 FPS ; ×4 15-16 ; ×8-×32 ~20 ; aucun gel. Arbres invisibles des
  bancs floraison : **pas une régression** (banc `vieillir()` sans segments,
  rattaché à D105).

Dette : **D106 → CLOSE** (archive lot F) ; **D109** ouverte (reliquats :
`AllelopathieLayer` ZIndex, vie macro non paresseuse, poses atteignables par le
vent, regroupement des plantes cuites si D1 échoue à ×4) ; **D105** annotée ;
**D108** ouverte en cours de sprint (états visuels du sol, à concevoir).
Reste **F5 Nico** : critère D1 sur son PC (colonne à remplir dans `00_etat.md`)
+ « en dézoom c'est fluide et lisible, en zoom c'est riche ».
