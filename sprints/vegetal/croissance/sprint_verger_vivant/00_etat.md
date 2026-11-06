# Sprint VERGER VIVANT (D129) — état

**Conception figée le 2026-11-05** : `docs/vegetal/croissance/conception_verger_vivant.md`. 4 tronçons, à exécuter par `/sprint-auto sprint_verger_vivant`. Golden `a10b7225…` attendu intact partout, aucun re-figeage prévu.

## Tronçons

| # | Kickoff | État |
|---|---|---|
| ① | `01_bourgeons_dormants.md` | **fait** (commité `951c294`, golden intact) |
| ② | `02_floraison_realiste.md` | **fait** (commité `3b706bd`, golden intact) |
| ③ | `03_fruits_cohortes.md` | **fait** (commité `67e9f0b`, golden intact, pont 0.6.9) |
| ④ | `04_vue_fleurs_fruits.md` | **fait** (non commité, golden intact, vue seule, F5 à faire) |

## Décisions (Nico, 2026-11-05)

1. Bourgeons dormants : réveil quand la couronne est sous son plafond, arbre vivant et éclairé, après toute perte.
2. Limites de fruits relevées **dans le moteur** (cohortes avec un nombre).
3. Noyer : dose anémophile recalibrée, après correction de sa floraison.
4. Fleurs nombreuses et belles, densité continue dans la vue.
5. Floraison réaliste dans le moteur (ordre, date, durée, pic).

## Constats de départ (2026-11-05, HEAD `b55ee3f`, patchs mémoire)

- Déclin : un seul `has_bud` par segment, jamais renouvelé ; sans tempête, sans neige et sans ombre, les arbres restent au plafond [`verger_mur`, seed 42, n=1 run par variante, 5 ans, VM].
- Patch brut (un bourgeon toutes les 4 semaines, sous 85 % du plafond) : cerisier de `full` an 5, 17 segments, 1 apex, 4 fruits → 34, 17, 10 ; tick médian 1 017 → 1 051 ms [`full`, seed 42, n=1 run par côté, VM, charge < 1] ; golden identique [smoke].
- Banc trop serré : pommier à 0,23-0,35 de lumière, mort en an 4 même avec le patch [`verger_mur`, n=1 run].
- Noyer : `pollen_recu` 0,01 à 0,41 par an ; floraison s11-s17 [mêmes conditions].
- Fleurs : pic 0,73 ; vue en tout ou rien à 0,5.
- Hors sprint : humidité du sol en hausse (2,5 à 2,8), asphyxie des aulnes de `full` → D127.

## §REPRISE

①②③ commités, ④ fait côté code (à commiter par l'orchestrateur). Sprint clos sous réserve du F5 de Nico (§F5 du bilan ④). Réglages : constantes de `visuals/PlantRenderer.FleursArbre.cs`, `GerbesFleurs.cs`, `PiecesFleur.cs`, `FruitsArbre.cs`, `PetalLayer.cs`.

## Bilans

### ① Bourgeons dormants + banc espacé (2026-11-06)

**Code** : `sim/growth/dormance.py` (neuf, 51 LDC) — `peut_reveiller` (vitalité > 0, couronne < 85 % de `max_segments`, fenêtre d'1 semaine sur 4 déphasée par `form_seed`) puis `reveiller_bourgeon` (remet `has_bud` sur UN segment : collet exclu, ni apex ni bourgeon, auxine sous le seuil, choix par `_hash_noise(form_seed, semaine, indice)`). Branché dans `grow_plant` (`phases.py`, 184 LDC) entre l'élongation et `_debourrement`, ligneux procéduraux seuls, hors hiver. Pur, sans `eco`, imports dans `sim/growth` seulement.
**Gate anti-boucle** : lumière LOCALE au point de réveil (lumière de la plante × transmission des grappes plus hautes, formule de `lumiere_pointes`) ≥ 1,5 × seuil de cladoptose de l'arbre. Mesure, ancien banc serré, réveil en jeu ON/OFF sur le même arbre de départ : cladoptoses/an pommier ombragé (0,27-0,33 de lumière) 7/7/3/1 dans les deux cas, figuier (0,29) 6/7/7/5 dans les deux cas [seed 42, n=1 run par côté, 5 ans, VM] → aucune boucle casse-repousse.
**Pré-croissance** : la dormance s'y applique (même `grow_plant`, plein soleil) → les arbres de départ changent : pommier de `full` 47 segments/20 apex → 70/35, cerisier 70/27 → 69/30 [seed 42, n=1, VM]. Choix : même port qu'en jeu (couper la dormance en pré-croissance demanderait un drapeau dans `grow_plant`).
**Banc `verger_mur`** : tuile 40×40 (monde entier). Cerisier, pommier, figuier au sud de la maison à 8 m les uns des autres ; deux noyers au nord-est côte à côte, 4,5 m (pollen 600 cm). Lumière s10-s35 : pommier 0,94-0,98 (avant 0,27-0,32), figuier 1,0 (avant 0,29-0,34), cerisier 0,98-1,0 ; noyers 0,64-0,83 [seed 42, n=1 run, 5 ans, VM]. Oracle `test_verger_mur` vert (noyer : 5,25 de fruits tombés contre 2,85). Tick du banc ~500 ms (avant ~180 : tuile 3,3× plus grande).
**Effet, `verger_mur`** (segments/apex/fruits max de l'an, an 1→5) [seed 42, n=1 run, VM] :
- avant : cerisier 64/23/9 → 12/1/1 ; pommier mort an 4 ; figuier 41→10 segments, vitalité 0,47 ; noyers 1-3 fruits.
- après : cerisier 58/19/8 → 39/15/10 ; pommier 56→54 segments, 9 fruits/an, vivant ; figuier 74→90 segments, 10 fruits/an ; noyers 41→21 et 60→18 segments, 4-8 fruits/an.
**Effet, `full`** : cerisier an 5 17 segments/1 apex/4 fruits → 38/13/10 ; pommier 55/14/10 → 60/24/9 [seed 42, n=1 run par côté, VM].
**Tick médian `full`** (ms, an 1→5) : avant 549/889/1073/1100/988, après 552/918/1132/1117/1006, soit +0 à +5 % [seed 42, n=1 run par côté lancés en parallèle, VM, charge 2-4 sur 16 cœurs]. Couronnes plus fournies = plus de segments à éclairer.
**Suites** : golden `a10b7225…` INTACT ; `test_croissance` 134/134, `test_bois_mort` 42/42, `test_dormance` (neuf) 7/7, `test_verger_mur`, `test_phototropisme`, `test_competition`, `test_quetes`, `test_grimpe`, `test_desync_phenologie`, `test_fruits`, `test_squelette_herbacees`, bancs grimpe/planche/liane : verts. Pas de C#.
**Reste / à savoir** : les noyers du banc fondent encore, par le VENT (102 segments cassés en 3 ans pour les deux, contre 25 par l'ombre [n=1 run]) : coin nord-est exposé, `CASSE_*` hors périmètre. Un bourgeon par 4 semaines ne suit pas une tempête. À regarder au ② (noyer) ou en dette si Nico veut un verger abrité.

### ② Floraison réaliste (2026-11-06)

**Code** : levier d'espèce `floraison_montee` (`plants/base/familles.py`, défaut `None` = `FLORAISON_MONTEE` 0,35 commune, herbacées inchangées) lu par `sim/engine/floraison.py` à la montée seulement. Leviers dans `plants/perennials/fruitiers.py` :
- cerisier : seuil 12 → 5, durée 3, montée 0,6 (mi-avril, avant le pommier) [odg, `fiches_arbres.md` « avr., avant les feuilles »] ;
- pommier : seuil 8 → 15, durée 3, montée 0,6 (fin avril - mi-mai) [odg, fiche « avr.-mai » ; pommiers à cidre normands début-mi-mai] ;
- noyer : défaut 60/6 → seuil 28, durée 2, montée 0,7 (mai, chatons 1-2 semaines) [odg, fiche « mai » ; Franquette mi-fin mai]. Dichogamie non modélisée ;
- figuier : inchangé (conception §5).
Sources : fiches du projet + connaissances générales (pépiniéristes, Ctifl), **non revérifiées en ligne**.

**Effet, `verger_mur`** (semaine d'armement, pic de `floraison`), an 1/2/3 [seed 42, n=1 run par côté, VM] :
- avant : cerisier s6/s6/s8 pic 0,73 ; pommier s5/s5/s7 pic 0,73 (avant le cerisier) ; noyer s13/s12/s13 pic 0,92, 6 semaines au-dessus de 0,35.
- après : cerisier s3/s4/s6 pic 0,94 ; pommier s6/s7/s8 pic 0,94 (toujours après le cerisier) ; noyer s9/s8/s10 pic 0,91, 2 semaines ≥ 0,7.
**Couplages** [mêmes conditions] : butineurs, `pollen_recu` max annuel cerisier 20,9/29,1/21,8 → 20,9/29,1/20,1 ; pommier 17,1/17,1/7,2 → 17,1/17,1/7,2 (recouvrement intact malgré la date plus précoce). Noyer (vent) 1,89-2,91 et 0,49-0,76 → 0,52-1,89 et 0,14-0,49 : environ ÷2, noix max/an 7-8 et 4-5 → 3-7 et 1-3. **À recaler au ③** (point 5 du kickoff ③).
**Nouaison** : pic plus haut → la fanaison sous `SEUIL_NOUAISON` 0,2 prend 3 semaines au lieu de 2 ; le pommier noue s11-13, le noyer s12-14 (avant s19-23). Maturations recalées pour tenir les fenêtres de fiche de `test_verger_mur` : pommier 17 → 15 semaines (sinon chute en s34), noyer 9 → 15 (le 9 compensait la floraison de juin ; sinon mûr dès s20). Résultat (mûr dès, dernier sur l'arbre) : cerisier s15-s19, pommier s27-s31, figuier s24-s27, noyer s27-s32 [seed 42, 3 ans, n=1].
**Écart signalé, non traité** : les autres ligneux anémophiles (chêne, hêtre, bouleau, charme, sapin, aulne) gardent le défaut 60/6, soit une floraison de juin sur 6 semaines, alors que la fiche les place en avril-mai (aulne févr.-mars, inatteignable : le forçage repart à 0 au 20 mars). Hors périmètre du verger ; toucher leurs dates change leur nouaison au vent. Candidat dette.
**Gène-tempo** : avec un seuil de 5, un cerisier à `phenologie_florale` > 1,25 a un seuil négatif et fleurit dès s1 (≈ 2,5 σ).
**Suites** : golden `a10b7225…` INTACT ; `test_desync_phenologie` 7/7, `test_floraison_forcage` 9/9, `test_flore_spontanee`, `test_fruits` 24/24, `test_catalogue_lot2` 20/20, `test_vent` 54/54, `test_croissance` 134/134, `test_dormance` 7/7, `bancs.test_verger_mur` : verts. Pas de C#.

### ③ Fruits par cohorte + noyer (2026-11-06)

**Code** : `Fruit.nombre` (défaut 1, `plants/base/stades.py`) ; `organ_sites(plant, plafond=MAX_ORGANS)`, `None` = tous les apex. Leviers d'espèce (`familles.py`, défaut `None` = comportement d'avant) : `fruits_par_site`, `fruit_masse`, `anemo_dose`. `sim/engine/decompo.py` : `nouer` (sans levier : 1 fruit sur `round(frac × sites)` sites ≤ 10 ; avec levier : `round(frac × fruits_par_site × apex)` fruits répartis sur tous les apex) et `deposer_fruits` (`nombre × masse`). `manger` retire un fruit, la cohorte part avec le dernier. Pont 0.6.9 : `nombre` par fruit (pleine terre et conteneurs), `fruit_index` vise toujours une cohorte. Lecteurs vérifiés au `grep` : la faune lit la litière `fruit` du sol, jamais `plant.fruits` ; l'automate teste `maturite` ; le ledger ignore `Chute fruit`. Pas de C#.
**Leviers** `[odg]`, de mémoire et non revérifiés en ligne ; 1 unité de litière ≈ 250 g de MS (FEUILLE_PAR_PLOT 0,30 par plot de 0,25 m², soit ~300 g/m²/an) :
- cerisier : 90 par site, 0,005 (≈ 2 000-3 000 cerises de 7 g) ;
- pommier : 10 par site, 0,09 (≈ 200-300 pommes de 150 g) ;
- figuier : 8 par site, 0,04 (≈ 200-300 figues) ;
- noyer : 60 par site, 0,05 (≈ 1 000-1 500 noix à nouaison pleine).
**Écart au kickoff (décision)** : la litière fruit d'un arbre tombe sous **toute la couronne** (plots de la tuile, comme l'abscission), plus au pied. Sinon on aurait 10 à 40 unités sur un seul plot, alors que le signal faune sature à 0,45. Les herbacées déposent toujours au pied. Conséquence : `test_verger_mur` ne compte plus que la part du plot du tronc (0,38 à 1,64, > 0, vert).
**Noyer** : `anemo_dose` 6 → 12 (espèce seule, `ANEMO_DOSE_COEF` intact). Part nouée an 1/2/3 sur `verger_mur` [seed 42, n=1 run par dose, VM] :
- dose 6 : noyer sous le vent 0,46/0,34/0,65 ; noyer au vent 0,18/0,12/0,33 ;
- dose 12 : sous le vent 0,63/0,51/0,79 ; au vent 0,31/0,21/0,50 ;
- dose 15 : sous le vent 0,68/0,57/0,83 ; au vent 0,36/0,25/0,55.
Un noyer seul (le voisin retiré) reçoit au pollen près la dose du noyer au vent : celui-ci ne reçoit que son propre pollen. Avec ce modèle de panache, les deux arbres d'une paire ne peuvent pas nouer à moitié si un isolé reste à 0,2-0,35. Cible lue ainsi : l'arbre sous le vent ≥ 0,5, l'isolé ~0,2-0,35, d'où 12. Ce choix compense exactement le ÷2 du ②.
**Effet, fruits max par arbre et par an** (an 1/2/3) :
- `verger_mur` [seed 42, n=1 run par côté, VM] : cerisier 9/10/10 → 2 009/2 001/2 237 ; pommier 0/9/9 → 0/218/158 ; figuier 10 → 280/232/168 ; noyer sous le vent 5/3/7 → 747/520/617 ; noyer au vent 2/1/3 → 396/281/416.
- `full` [mêmes conditions] : cerisier 0/10/10 → 0/2 054/2 052 ; pommier 9/9/10 → 296/274/249.
**Garde-fou de masse** (an 1→3) [mêmes conditions] :
- `verger_mur` : litière fruit 3,9-5,9/an → 78-84/an, contre 112-135 de feuilles (ratio 0,6-0,7). Sol, fin an 3 : N 629 → 631, om_stable 238 → 243, om_active 63 → 86 (+38 %, le seul écart notable : la MO fraîche des fruits). Faune quasi identique (cloporte 8,9 → 9,0, merle 6,7 → 6,8).
- `full` : fruit 1,7-3,0 → 27-35, contre 83-102 de feuilles. Fin an 3 : N 505,5 → 505,8, om_stable 304,5 → 306,6, om_active 824 → 833 ; faune identique à 0,1 près.
Pas de dérive du sol ni de la faune : les masses physiques sont gardées.
**Coût** : tick médian, A/B en parallèle (leviers coupés contre actifs, même processus) [seed 42, n=1 run par côté, VM, charge 2-4] : `verger_mur` 487/494 → 502/504 ms (+2-3 %) ; `full` 548/927/1 062 → 552/940/1 062 ms (+0-1 %). Snapshot JSON `verger_mur` +0 à +4 % (152 → 162 ko au pic) ; `full` +0,2 %.
**Suites** : golden `a10b7225…` INTACT ; `test_fruits` 30/30 (une section cohortes ajoutée, chute mesurée sur la tuile) ; `test_sim_server` 322/322 (version 0.6.9, clé `nombre` > 1 sur le pommier de `full`) ; `test_verger_mur`, `test_catalogue_lot2`, `test_floraison_forcage` 9/9, `test_vent` 54/54, `test_desync_phenologie` 7/7, `test_automate_planif` 24/24, `test_squelette_herbacees`, `bancs.test_planche_especes`, `bancs.test_biotique` 12/12 : verts.
**Pour le ④** : (a) `RayonFruit` normalise par 0,15 : les fruits d'arbre se dessinent petits (cerise ×0,18 de rayon, jusqu'au pixel plancher). Normaliser par espèce, ou ignorer `masse` pour les arbres qui ont une fiche. (b) Dessiner `nombre` avec un plafond. (c) Jusqu'à 38 cohortes par arbre, contre 10 avant.
**Taille** : `serialize.py` 394 LDC (392 avant, déjà en bande de vigilance, responsabilité unique) ; `decompo.py` 145.

### ④ Vue : fleurs et fruits (2026-11-06)

**Code** (vue seule, moteur et pont non touchés) :
- `PlantRenderer.FleursArbre.cs` (neuf) : densité continue `(floraison − 0,15) / 0,7` × 0,85 des bouts de bois ; boutons à la montée (tous fermés sous 0,5, tous ouverts à 0,9) ; détecteur de pic `_floraisonPic` (copié au pinceau) pour savoir si la floraison fane ; bouquets cerisier 3-5, pommier 3-5, au bout et au milieu des brindilles, 1 500 fleurs au plus à ×8+.
- `PlantRenderer.GerbesFleurs.cs` (neuf) : de ×0,5 à ×4, une gerbe de 4 à 14 fleurs par tracé, trois couches (fleurs, cœurs dès ×2, boutons), même atlas que les gerbes de feuilles.
- `PlantRenderer.PiecesFleur.cs` (neuf) : ×8/×16/×32, une fleur = une pièce de 13, 25, 49 px (5 pétales à plat, liseré, cœur, étamines dès ×16 ; bouton). Couleurs : cerisier blanc pur, bouton blanc verdâtre ; pommier blanc rosé, liseré rose, bouton rose franc.
- `PetalLayer.cs` (neuf, branché dans `WorldView.Compost.cs`/`Snapshot.cs`) : pétales au sol sous la couronne, quantité `(1 − f/pic) × min(1, f/0,05)`, semis emboîté au hash, ~6 semaines.
- `PlantRenderer.FruitsArbre.cs` (neuf, sorti de `Houppier.cs`) : `nombre` lu (`FruitData.Nombre`, `PlantStructure.cs`), 500 fruits au plus par arbre en gardant la proportion entre cohortes, grappes (cerise 3 sur queue de 4 cm, pomme 2, figue 1, noix 2), queues dessinées dès ×8, rayon = fiche × maturité (nouaison 45 %) au lieu de la masse rapportée à 0,15. Clic `manger` et `DistanceFruitPort` relisent les fruits dessinés.
- Clé de recuisson (`CleStable.cs`) : `Nombre` par cohorte et drapeau « fane » ajoutés.

**Écarts au kickoff** :
- Prescription « `KitFleuron` enrichi » **non tenue telle quelle** : des fleurs une à une ne blanchissaient pas le houppier (544 fleurs à ×2, couronne encore verte [capture]). Remplacée par les gerbes de fleurs (×0,5-×4) et des pièces d'atlas (×8+). Le kit n'est pas modifié.
- Premier essai ×8+ en disques de triangles : primitives 66 k → 138 k, FPS 9,1 → 4,6 [`verger_mur` ×8, s5, n=1 relevé de 5 s par côté] ; d'où les pièces.
- Pétales : un jeu chargé en pleine défloraison ne montre ses pétales qu'à la semaine suivante (le pic n'a pas été vu). Même limite pour les boutons (une semaine de boutons possible à la descente).

**Coût de cuisson, cerisier, ms par coup de pinceau** [`verger_mur`, seed 42, `SYMBIOSE_COUT_CUISSON`, n=1 coup par run, VM, charge 1 à 4] :
- pic des fleurs (s5) : ×1 1,3-1,8 → 1,5-1,9 [n=4 avant, 6 après] ; ×2 3,3-3,7 → 3,0-3,7 [idem] ; ×4 5,4-6,4 → 3,8-4,2 [idem] (l'ancien point par fleur à ×4 coûtait plus que les gerbes).
- pleins fruits (s14, ~2 000 cerises) : ×1 2,2 → 3,9-4,0 ; ×2 3,1-3,6 → 5,1-5,3 ; ×4 3,9-4,3 → 6,7-6,9 [n=2 runs par côté] : +2 à +3 ms, prix des 500 fruits.
- ×8 et plus : arbre en dessin direct, pas de cuisson.

**FPS ×8/×16, cadré sur le cerisier** [`perf_vm.sh`, n=5 relevés de 1 s, VM llvmpipe, charge 1 à 3,6] : pic s5 ×8 9,1 → 8,1, ×16 10,1 → 9,1 (objets 3 500 → 9 500) ; fruits s14 ×8 7,1 → 6,6, ×16 8,2 → 8,1.

**Effet vu en capture** (Xvfb, seed 42) : cerisier au pic blanc à ×1, ×2, ×4 ; bouquets à ×8 ; cinq pétales, cœur et étamines à ×16/×32 ; pommier en boutons roses puis blanc rosé ; pétales au sol après le pic (vus avec `-w 4 -T 3`) ; cerises par grappes sur leurs queues à ×8, figues nombreuses, noix vertes (peu lisibles dans le feuillage, palette du ⑤). Cueillette `-C` cerisier ×4 : position → index 25/25, deux clics `manger` réels réussis.

**Suites** : golden `a10b7225…` INTACT ; `dotnet build` vert, 0 avertissement. Fichiers neufs tous ≤ 130 LDC ; `Organs.cs` 311 LDC (🟡, déjà signalé au houppier ⑤, −1 ligne ici).

**§F5 pour Nico** (`init config="verger_mur"`, an 1 ; la semaine de l'en-tête suit l'état moteur) :
- s4-s6 printemps : cerisier qui blanchit, au pic en s5 ; ×1, ×2, ×4 : paraît-il blanc ? ×8, ×16 : bouquets, pétales, étamines.
- s7-s8 : pommier en boutons roses (s7) puis blanc rosé (s8-s9) ; sous le cerisier, pétales au sol qui s'éclaircissent jusqu'à ~s11.
- s13-s16 : cerises par grappes de 2-3, nombre, taille ; clic `manger` sur plusieurs grappes.
- s23-s26 : figues ; s27-s31 : noix ; an 2 s24-s30 : pommes (pas de pomme l'an 1 sur ce banc).
- Fluidité réelle ×8-×16 en pleine floraison sur le PC.

## §F5 (sprint clos côté code le 2026-11-06)

Sur `verger_mur`, an 1 : s5 cerisier au pic (blanc de ×1 à ×32) ; s7-s9 pommier, boutons roses puis fleurs blanc rosé, pétales au sol sous le cerisier ; s13-s16 cerises en grappes, à manger au clic ; s24 figues ; s28 noix ; an 2 pommes. Fluidité à juger à ×8-×16 au PC. Sur 5 ans, les couronnes doivent rester fournies.
