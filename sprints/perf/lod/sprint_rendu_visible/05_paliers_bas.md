# T5 — Paliers bas ×0,5 · ×1 · ×2 + tapis par plot

> Lire `CLAUDE.md`, `00_etat.md`, `docs/perf/lod/conception_rendu_visible.md` §3-§4
> (D3, D4, D5 — l'échelle des paliers fait foi). Vue C# pure. Golden intact.

## Objectif
Refaire le dessin des plantes aux trois paliers éloignés pour que **chacun porte SON
information** (échelle cumulative : un palier garde ce que montrent les plus éloignés) :
- **×0,5 présence + saison** : tache (couronne) teintée par **famille** ; teinte d'automne
  (`automne`), nu en hiver pour les caducs ; mort = gris bois.
- **×1 port** : silhouette du port (arbre, buisson, rosette, tapis, couchée, grimpante)
  à hauteur relative juste — un arbre se distingue d'un buisson au premier regard.
- **×2 santé globale** : teinte de vigueur à partir de `vitalite` et des symptômes
  dominants (franc / pâle-chlorose / fané / sénescent) ; floraison (`floraison`) en
  taches de couleur de fleur.
Et le **tapis par plot (D5)** : une plante dont l'emprise projetée est sous un seuil de
lisibilité au palier courant (point de départ ~3 px internes, constante nommée réglable)
n'est NI cuite NI affichée individuellement : elle contribue au **tapis de son plot**.

## Code concerné (lire avant)
- `visuals/PlantRenderer.cs` : `SegmentDetailMinZoom`/`OrganDetailMinZoom` (= 1 depuis la
  désync ③), `DrawCanopySilhouette` (2 polygones), boucle segments ; partials
  `.Organs/.Leaf/.Flower/.Froid/.Meteo/.Wind/.Bake/.Palette`. `.Organs.cs` est 🟡 (~319 LDC) :
  écrire les paliers dans un **partial neuf** (ex. `PlantRenderer.Paliers.cs`), ne pas
  gonfler l'existant.
- Pré-cuisson : `PlantRenderer.Bake.cs` (boîte englobante selon le palier), `PlantBaker`,
  `BakeQueue` ; la pompe `RedrawAllPlants` au changement de palier (`StepZoom`) recuit.
- Données par plante (snapshot, `data/code/tools/simserver/serialize.py` ~l.110-270) :
  `vitalite`, `strate`, `floraison`, `automne`, `fruits`, `leaf_symptoms`, segments,
  `height_cm`, `footprint_cm`. Famille / port : chercher où la vue les connaît
  (`core/PlantCatalogue*.cs`, chaînes `rosette`/`buisson`/`tapis`/`couchee` du renderer).
  **Si une donnée manque, l'énoncer et s'arrêter** (le pont n'est pas dans ce sprint).
- Tapis existant : `visuals/CouvertureLayer.cs` (`couverture_sol` par plot, MinZoom ×1).

## Tapis — un seul langage
Le tapis des petites plantes et le tapis `couverture_sol` sont **un seul** tapis : même
couche, un patch par plot dont la teinte vient des petites plantes agrégées (famille
dominante, saison) et dont la densité combine leur emprise cumulée et `cov`. Jamais deux
voiles verts superposés. Agrégation = lecture pure des payloads (déterministe, zéro
Random, recalculée au snapshot et au changement de palier, pas par frame).
Le picking reste par plante (`FindPlant`/`FindSegmentGlobal` itèrent les nœuds même
invisibles) : cliquer dans un tapis sélectionne la plante la plus proche — à vérifier.

## Vérification
- Captures VM ×0,5, ×1, ×2 sur `full` et sur un banc dense (`effondrement` ou `lux…`,
  liste : registre `BANCS`) : chaque palier montre son information ; aucune zone où des
  plantes existent n'est vide ; pas de double tapis.
- `tools/perf_vm.sh` ×0,5 : FPS et draw calls avant/après ; nombre d'images cuites (cache).
- Cuisson d'un palier complet (dézoom ×1 → ×0,5) : durée de vidage de la file mesurée.

## Ne pas faire
Pas de paliers ≥ ×4 (T6). Pas de faune (sprint B). Aucun bonus/malus — on montre l'état
moteur, on n'invente rien (philo #5).

## Fin de tronçon
Maj `00_etat.md` (seuil du tapis, mesures), commit. Point F5 : « au dézoom, je lis où ça
pousse, quel port, qui va bien ? »
