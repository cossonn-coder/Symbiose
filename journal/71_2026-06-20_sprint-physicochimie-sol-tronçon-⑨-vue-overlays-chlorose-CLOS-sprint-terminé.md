# 2026-06-20 — Sprint PHYSICO-CHIMIE DU SOL · tronçon ⑨ (vue Godot, C#) — SPRINT TERMINÉ

**Vue Godot de la chimie du sol : 5 overlays debug neufs (pH/N/P/K/structure_sol)
+ indice diégétique de chlorose alcaline (jaunissement foliaire des acidophiles).**
Dernier tronçon, clôt le sprint PHYSICO-CHIMIE. 100 % vue (golden NEUTRE, snapshot
hors hash), F5 validé par Nico.

## Contexte

Le moteur Python expose depuis ①–⑧ cinq champs neufs (`ph`, `n`, `p`, `k`,
`structure_sol`) et un prédicat de chlorose (`vigueur_plante.qi_local` :
`ph_opt < SEUIL_ACIDOPHILE` ET `ph_local > CHLOROSE_PH`). Côté vue il restait à
(A) donner des palettes lisibles à ces champs dans la heatmap debug F6 et retirer
l'entrée morte `fertilite` (supprimée du moteur au ③), et (B) traduire la chlorose
en signal foliaire visible.

## Fork de conception (tranché avec Nico)

**Chlorose = Option 1 (flag moteur), PAS Option 2 (recalcul C#).** Nico avait
d'abord choisi Option 2 ; mon ancrage a révélé que la grille `ph` n'arrive au
client QUE via l'overlay debug F6 (`WorldView.cs:376`, requête `fields` à la
demande) — donc pas d'indice diégétique PERMANENT sans machinerie de cache côté
client. J'ai remonté le tradeoff (CLAUDE.md §1) ; Nico a basculé sur Option 1 :
le moteur émet un `bool` par plante dans le snapshot, zéro requête neuve, zéro
duplication du prédicat. La suggestion du kickoff de poser `ph_opt` dans
`PlantCatalogue.cs` était caduque (fichier = vestige mort du portage C# abandonné).

## Ce qui est fait

**Partie A — overlays (`visuals/FieldOverlay.cs`)** : +5 palettes —
`ph` (4.0→8.5, rouge acide → violet alcalin), `n`/`p`/`k` (0→3, beige pauvre →
vert/ocre/magenta riche), `structure_sol` (0→1, brun compacté → vert grumeleux).
Entrée morte `fertilite` retirée ; commentaire de provenance des bornes MàJ.

**Partie B — chlorose (Option 1)** :
1. `data/code/tools/simserver/serialize.py` — `_snapshot` importe
   `SEUIL_ACIDOPHILE, CHLOROSE_PH`, lit `eco = gs["eco"][tile.tile_id]` dans la
   boucle tuiles, et pose `base["chlorose"] = bool` par plante vivante (prédicat
   MIROIR de `qi_local` : `ph_loc` = moyenne `eco.ph.at_plot` sur
   `root_plots`/repli foyer).
2. `visuals/PlantRenderer.cs` — `ChloroseTint` (`d8d24a`) + `ChloroseAmount` 0.6 ;
   flag `_chlorose` + `SetChlorose()` (early-out) + helper `Chlorotic(green)`
   (lerp vert→jaune). Appliqué à l'apex (`DrawSegments`) et à la silhouette LOD
   (`DrawCanopySilhouette`).
3. `visuals/PlantRenderer.Organs.cs` — `Chlorotic()` sur la couleur des feuilles.
4. `world/WorldView.Snapshot.cs` — lit `chlorose` du snapshot (tolérant pré-⑨),
   `SetChlorose` câblé sur les 2 branches (plante qui a poussé / nouveau nœud).

## Vérifs

- `dotnet build Symbiose.csproj` : **0 erreur, 0 avertissement**.
- Golden Python : **`e209e8d854300aa8…` INCHANGÉ** — golden NEUTRE (aucun
  acidophile au smoke ; le snapshot n'entre pas dans le hash).
- **F5 validé par Nico** : F6 cycle pH/N/P/K/structure_sol lisibles + légende ;
  myrtille acidophile en sol alcalin → jaunit.

## Sprint PHYSICO-CHIMIE DU SOL — bilan

①→⑨ TOUS CLOS. Le sol a désormais une vraie chimie émergente :
- **pH** maître-régulateur (champ hérité du `soil_type`, dérive décennale,
  lockout en cloche, amendements rondelles `chaux`/`soufre` réversibles).
- **NPK distincts** (`fertilite` supprimé net, loi du minimum de Liebig,
  lessivage différencié par nutriment & CEC, minéralisation splittée par tissu).
- **Fenêtres pH par espèce** (`ph_opt`/`ph_tol`, défauts neutres) + chlorose
  alcaline + myrtille démonstratrice (famille `Ericaceae`).
- **Faim d'azote** (immobilisation réversible par bois/BRF + crochet substrat
  champignons).
- **structure_sol** (dette D30 absorbée, Option B : infiltration/asphyxie/uptake,
  gestes `becher`/`grelinette`).
- **Vue** : 5 overlays debug + indice de chlorose diégétique.

3 re-figeages golden localisés et maîtrisés (③ Liebig `87ed27ae…`, ④ lockout
`d8856261…`, ⑧ structure `e209e8d8…` + `population_hash cd21704b…`) ; ⑤⑥⑦⑨ NEUTRES.

## Dette signalée (hors périmètre, à arbitrer)

- **`container.py` ~443 LDC pur** > seuil ~350 (constat constant ①–⑧) →
  éclatement d'`EcoFields` en paquet = chantier refactor dédié.
- **D39** : `test_senescence` rouge (asphyxie pommier ~2.7 ans) = régression
  PRÉ-EXISTANTE (thermique ⑦, commit `4b70032`), indépendante de tout le sprint.
- **Indicatrices oseille/prêle DIFFÉRÉES** (⑤) : même mécanique que la myrtille,
  zéro impact smoke → enrichissement catalogue à part.

## Suite actée (retour livrable, Nico 2026-06-20)

Généraliser l'indice foliaire à TOUS les stresseurs (ravageurs, excès d'humidité,
sécheresse…) = **nouveau sprint dédié « sémiologie foliaire »**, tracé en **dette
D33** (granularité = vocabulaire PAR CAUSE ; chlorose = 1re brique). À CONCEVOIR
en conversation d'abord, PAS de dev immédiat (règle retour-livrable).
