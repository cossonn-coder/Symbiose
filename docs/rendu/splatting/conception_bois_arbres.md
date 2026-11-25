# Conception — bois lissé, écorces cuites et arbres en splats (S2 du style homogène)

> Conçue en `/conception` le 2026-11-25 avec Nico. Deuxième sprint de la séquence « style
> homogène » (`conception_reliquats_plantes.md` §2 : S1 reliquats → **S2 arbres** → S3 lisière
> + chargement). Sprint : `sprints/rendu/splatting/sprint_bois_arbres/`.
> **Rendu seul (E4) : `data/code/` n'est jamais modifié, golden `bce813af…` intact.**

## 1. Pourquoi — constat en image

Captures VM du 2026-11-25 (n=1 image par cas, hors dépôt) :
- **Pommier** (`verger_floraison`, ×4 → ×16) : tronc en pile de rectangles dont la largeur change
  par MARCHES ; branches en bâtons droits ; une branche partie DERRIÈRE le tronc est peinte devant
  lui (le bois est trié par épaisseur, `PlantRenderer.cs:552`, pas par profondeur) ; ×4 : fleurs
  éparses.
- **Sapin** (`houppiers`, ×1, ×4) : poteau à touffes éparses, aucun cône — EN JEU, pas seulement
  au portrait.
- **Charme** (×16) : tronc en 3 bandes plates, bas coupé carré, racines = triangles plats.

Cause : chaque segment du moteur (40-50 cm, la charpente) est un `DrawLine` à bouts carrés
(`DrawEcorce`, `PlantRenderer.Motifs.cs:177`) : âme + 2 flancs orientés + stries au hash. Au
sprint (a) ③, des tronçons d'écorce cuits posés bout à bout montraient des JOINTS ; un cylindre
d'un seul tenant était propre (`sprint_precuisson_splats/mesures/couture_bois.png`).

## 2. Décisions

| | Décision | Raison |
|---|---|---|
| **B1** (Nico) | **Courbe interpolante passant par TOUS les nœuds** du moteur, et une **géométrie unique du bois** (« point sur l'axe ») lue par tous : rameaux dérivés, fruits, clic `manger`, sécateur et surbrillance, neige sur branche, ombre. | « Aucun angle abrupt » ; des joints seulement arrondis laisseraient un coude tous les 45 cm. Si le dessin courbe et que les lecteurs restent droits, un fruit flotte à côté de sa branche et le sécateur coupe à côté. |
| **B2** (Nico) | **Écorce cuite en splats pour les 12 essences × 3 âges** (rameau lisse / branche / tronc à rhytidome), l'âge choisi par l'épaisseur du bois. | Biologie réelle : le rhytidome se forme avec l'âge ; le bouleau blanc noircit à la base ; un rameau est lisse partout. |
| **B3** (Nico) | **Cône du sapin par la VUE** : étages de rameaux dérivés de plus en plus courts vers le haut. Moteur intact. | Rendu seul (E4). Une vraie architecture de conifère au moteur reste possible plus tard (non ouverte en dette). |
| C1 | Le bois se trie par **profondeur** (iso), pas par épaisseur. | Une branche derrière le tronc doit passer derrière. |
| C2 | Une seule primitive **« ruban texturé »** pour le bois, les brins et les rubans des graminées (E9), **indépendante de `PlantRenderer`**. | `PoserBrin` calcule déjà ses bords point par point ; S3 (lisière) réutilisera la primitive. |
| C3 | **Orientation des flancs = géométrie du tube** ; l'écorce cuite n'apporte que les **tons** (relief : crevasses, plaques, lenticelles). Le mécanisme (petit shader de composition dans le pinceau, ou variantes cuites par rotation) est tranché par une **maquette mesurée** au ②. | Un pixel est un CODE (palette + ton + orientation, `PaletteIndexee.cs`) éclairé par le soleil réel ; l'orientation d'un flanc dépend de l'angle de la branche à l'écran, une texture ne peut pas la porter figée. |
| C4 | **Pied évasé** (empattement) à la place des racines-triangles ; **col de branche** aux fourches. | Les deux existent en vrai et donnent des fourches arrondies. |
| C5 | Fleurs d'arbre ×4 en **bouquets cuits** (plus une à une) ; masses ×4 : **constater d'abord en été** (les gerbes portent déjà les touffes splat depuis (a) ⑤), ne corriger que ce que la capture montre. | Le ×4 « clairsemé » vient du plafond des fleurs une à une. |

## 3. Modèle

### 3.1 Axes (vue seule)
- Le pont transmet déjà `parent` (`data/code/tools/simserver/segments_pont.py`, et en delta
  `pont_delta.py` : index 0 de la trame). **Vérifié au code :** `core/PontDelta.cs` recopie la
  trame à partir de l'index 1 (`c + 1`, ligne 158) et `core/PlantStructure.cs` (`ParseSegment`
  et la lecture `segs_lus`) ne lit pas `parent`. Il faut l'ajouter des deux côtés C# (format du
  cache `segs_lus` : `Pas` 10 → 11), et tenir le miroir `tests/simserver/delta.py` s'il lit ce
  format.
- Un **axe** = une chaîne de segments où chaque nœud continue sur l'enfant le plus aligné (à
  égalité : le plus épais). Les autres enfants ouvrent un axe neuf qui naît DANS le tube porteur.
- La courbe d'un axe passe par chaque nœud (spline interpolante, type Catmull-Rom centripète,
  échantillonnée au pas d'écran). Largeur interpolée en continu entre les épaisseurs des segments.
- Tout est mémoïsé par référence de `_structure` (clé auto-invalidante, comme `BoisDuHouppier`) :
  jamais recalculé dans une frame.

### 3.2 Tube
- Triangle strip le long de la courbe, avec coordonnées de texture : **u** en travers (−1 → 1),
  **v = longueur d'arc en cm depuis la base de l'axe** → le motif garde son échelle à tous les
  paliers et ne se coupe jamais le long d'un axe.
- Col de branche : l'axe enfant commence légèrement à l'intérieur du porteur avec une largeur
  renflée qui rejoint la sienne. Pied : évasement du tronc sur ses premiers cm.
- Tri des axes et des morceaux de tube par profondeur iso.
- Le tube n'existe qu'au pinceau (cuisson) et au repli (dessin direct) : **aucun coût par image**
  pour une plante cuite.

### 3.3 Écorces cuites
- Outil splat (`tools/splat/`) : un cylindre sculpté, **périodique en longueur par construction**,
  par essence × âge, photographié de face → une **bande de tons** (et, selon la maquette C3, un
  indice de travers). Format, palier et résolution : à fixer au ②, mesurés.
- Âge par épaisseur (seuils au ②, dans la continuité de `EcorcePleineCm` de
  `PlantRenderer.Arbres.cs`) ; le passage d'un âge à l'autre le long d'un axe se fait par un fondu
  sur quelques cm, jamais par une marche.
- Essences : les 12 de `RecettesArbres` (pommier écailleux en plaques, cerisier lisse brun-rouge à
  lenticelles en bandes, noyer gris crevassé en losanges, chêne crevassé en long, hêtre gris uni,
  bouleau blanc à lenticelles noires et base noire crevassée, charme gris cannelé, noisetier
  brun-rouge lustré, aulne brun sombre fissuré, saule gris-brun en réseau, figuier gris lisse,
  sapin gris argent à poches de résine). Les couleurs restent celles de la fiche (`Ecorce`).

### 3.4 Graminées
- `PoserBrin` (`PlantRenderer.Graminees.cs:44`) et les rubans du chaume (`PoserRubans`,
  `PortChaume.cs`) passent par le ruban texturé : nervures parallèles, cœur plus clair. Le vent
  plie toujours le brin point par point (la géométrie reste celle de la vue).

### 3.5 Arbres ×4, sapin, portraits
- ×4 : fleurs d'arbre en bouquets cuits (recette splat d'un bouquet de corolles, densité réglée sur
  `Floraison`) ; masses : capture d'été d'abord.
- Sapin : étages de rameaux dérivés (`RecettesRameaux["FirTree"]`, `PlantRenderer.Rameaux.cs`),
  longueur décroissante avec la hauteur sur le tronc → cône. Même règle au portrait.
- Portraits (`tools/splat/portraits/arbres.js`, `cuire_portraits.js`) : écorces du ② (bouleau
  blanc), sapin conique, cerisier en fleurs et en cerises, figuier (port buissonnant, feuilles
  palmées).

## 4. Tronçons

| # | Tronçon | Golden |
|---|---|---|
| ① | Axes et tube lissé (tons actuels), parent lu, géométrie unique, pied, cols, tri par profondeur ; rapport C enrichi (plantes en repli, ms de cuisson) | intact |
| ② | Maquette C3 puis écorces cuites 12 × 3 et plaquage | intact |
| ③ | Ruban texturé des graminées + petit bois dérivé en tube | intact |
| ④ | Arbres ×4 : bouquets de fleurs cuits, masses constatées l'été | intact |
| ⑤ | Cône du sapin en jeu + portraits d'arbres | intact |
| ⑥ | Revue des paliers ×0,5 → ×32 (12 essences + graminées, été et hiver nu), finitions, F5 consolidé, clôture | intact |

Ordre : ① avant tout (géométrie dont tout dépend) ; ② sur le tube de ① ; ③ réutilise la primitive ;
④⑤ indépendants entre eux, après ② (le portrait du bouleau utilise son écorce) ; ⑥ revue.

## 5. Coût et garde-fous

- **Référence PC de Nico** (rapport C du 2026-11-25, `full` seed 42, an 2, ×32, turbo, n=1 run) :
  FPS 23 [charge 86-94 %] · 87 draw calls · 53 827 primitives · précuisson 599/1024 Mo · 4 en repli ·
  11 évincées. S2 ne doit pas la dégrader : le bois cuit ne coûte rien par image ; une plante en
  REPLI paie les triangles du tube → mesure au ① (triangles et ms de pinceau d'un arbre ×32).
- Poids : bandes d'écorce = petites textures (36 bandes) ; `assets/splats/` 65 Mo, **alerte à 200 Mo**.
- Déterminisme : zéro `Random`, hash seulement ; deux cuissons = mêmes octets.
- Interrupteur conservé : Maj+F11 / `SYMBIOSE_SPLATS=0` → l'ancien dessin intact derrière chaque crochet.
- Interdits : `data/code/` (sauf lecture), `test_epaisseur_500ans`, DeepSeek dans les sous-agents,
  `tools/splat/vendor/`.
- Taille des fichiers : la primitive et les axes dans des fichiers neufs (≤ 300 LDC chacun) ; on
  n'alourdit pas `PlantRenderer.cs`.
