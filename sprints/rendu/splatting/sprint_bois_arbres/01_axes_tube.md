# ① Axes et tube lissé — kickoff

Lire d'abord : `CLAUDE.md`, `00_etat.md` (ce dossier), `docs/rendu/splatting/conception_bois_arbres.md`
(§2 décisions B1, C1, C2, C4 ; §3.1-3.2 modèle).
Golden attendu : **`bce813af…` INTACT** (vue seule). `dotnet build Symbiose.csproj` vert, 0 avertissement.

## Objectif
Le bois des plantes dessinées par segments (`DrawSegments`, `PlantRenderer.cs:543` : arbres et
plantes sans fiche ; `DrawSkeleton` pour les squelettes) devient un **tube continu, lisse**, qui
passe par tous les nœuds du moteur, sans aucune marche de largeur ni angle, avec pied évasé et cols
de branche, trié par profondeur. Pas encore de texture : on garde les tons et les flancs orientés
d'aujourd'hui (`DrawEcorce`, `PlantRenderer.Motifs.cs:177`) appliqués le long du tube.

## À faire
1. **Lire `parent`** côté C# (faits vérifiés au code le 2026-11-25) :
   - `core/PontDelta.cs` recopie la trame delta à partir de l'index 1 (`c + 1`, l. 158) : l'index 0
     = `parent` (`data/code/tools/simserver/pont_delta.py` l. 21) est perdu. Étendre le format
     `segs_lus` (`Pas` 10 → 11) en gardant TOUS ses lecteurs cohérents (grep `segs_lus`, `PontDelta.Pas` :
     `core/PlantStructure.cs`, `core/PlanteLue.cs`, la soustraction des semaines l. 179 qui suppose
     l'âge en DERNIER).
   - `ParseSegment` (`core/PlantStructure.cs`, chemin JSON historique) : lire `parent`.
   - `Segment` gagne `int Parent` (−1 = racine). Vérifier au grep tous les `new Segment(`.
   - Vérifier si `tests/simserver/delta.py` reproduit le format C# ; sinon rien à y faire.
2. **Axes** (fichier neuf, ex. `visuals/BoisAxes.cs`, ≤ 300 LDC, indépendant de `PlantRenderer`) :
   chaîne par nœud vers l'enfant le plus aligné (égalité : le plus épais) ; autres enfants = axes
   neufs. Courbe interpolante passant par chaque nœud (Catmull-Rom centripète ou équivalent sans
   dépassement) ; largeur continue. Mémoïsé par référence de `_structure`.
3. **Ruban** (fichier neuf, ex. `visuals/RubanTexture.cs`, indépendant de `PlantRenderer`, servira
   aux graminées ③ et à la lisière S3) : triangle strip le long d'une polyligne avec largeur par
   point ; u en travers, v = longueur d'arc en cm. Au ① il est peint en tons (3 bandes orientées
   comme `DrawEcorce`) ; la texture vient au ②.
4. **Pied et cols** : évasement du tronc près du sol (remplace les racines-triangles de
   `DrawAncrage`, `Motifs.cs:217` — garder le halo de sol si utile) ; axe enfant qui naît dans le
   porteur avec un renflement.
5. **Tri par profondeur** (iso) au lieu de l'épaisseur.
6. **Géométrie unique** : une fonction « point sur l'axe » (segment, t) qui renvoie le point de la
   COURBE. La faire lire par TOUS les lecteurs de la géométrie du bois : rameaux dérivés
   (`BoisDuHouppier`, `PlantRenderer.Rameaux.cs:84`), fruits (`PointDuFruit`, `Organs.cs:430`), clic
   (`FindSegmentNear`, `PlantRenderer.cs:475`, et `PlantRenderer.Clic.cs`), surbrillance
   (`DrawHighlight`), neige (`DrawSnowOnBranch`, `Froid.cs:122`), feuilles génériques. Inventaire au
   grep (`s.Base + s.Dir`, `Segments`) avant de coder ; signaler tout lecteur non migré.
7. **Rapport C / F4** : ajouter la liste des plantes en repli (espèce) et le temps de pinceau max
   par cuisson (ms) — le rapport du PC de Nico ne permettait pas de savoir si les replis sont des
   arbres (`BudgetCuisson.cs`, `PlantBaker.cs`).
8. Interrupteur : l'ancien bois reste derrière Maj+F11 / `SYMBIOSE_SPLATS=0` (ou un drapeau voisin) pour
   comparer avant/après.

## Mesures et captures (lues au Read avant de conclure ; `uptime` avant tout temps)
- `tools/capture_vm.sh -b verger_floraison -c 60,60 -w 0 -l 2 -n 170` (planche ×0,5→×32) avant/après ;
  `-b houppiers` (12 essences, places dans `data/code/bancs/houppiers.py`) à ×4 et ×16 ; un squelette.
- Taille : banc de la clé stable `-Y AppleTree` (coupe une branche) → la surbrillance suit la courbe,
  la coupe tombe où on vise.
- Triangles d'un arbre (pommier 10 ans, chêne) et ms de pinceau ×16/×32 ; frame `full` ×8 avant/après
  [VM, n=1, non transposable au PC].
- Captures dans `mesures/01_*`.

## Ne PAS faire
- Toucher `data/code/` (le pont Python envoie déjà `parent`).
- Lianes (`PlantRenderer.Lianes.cs`) et ports à fiche : hors périmètre (les signaler s'ils montrent le même défaut).
- Recalculer les axes dans une frame. `test_epaisseur_500ans`. DeepSeek.

## Fin
Mettre à jour `00_etat.md` (compte rendu ①, mesures, écarts), commit.
