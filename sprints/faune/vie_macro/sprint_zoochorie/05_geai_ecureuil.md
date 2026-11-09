# ⑤ Le geai et l'écureuil plantent ce qu'ils oublient (D42)

Lire d'abord : `CLAUDE.md`, `00_etat.md`, doc
`docs/faune/vie_macro/conception_zoochorie.md` §4.5, §4.8. Faits : ① grain sauvage,
② chute unifiée + chêne/hêtre fruitiers + glandée, ③ noisetier, ④ `sim/zoochorie.py`
(prise saturante, tampon monde, grille perchoir, trait `mange_par`).

## Objectif
Deux guildes neuves qui **cueillent les fruits à coque sur l'arbre**, les
**cachent** et en **oublient** : le geai en terrain découvert et de loin (il fait
entrer la forêt de la ceinture), l'écureuil près des arbres.

## Guildes (`fields/population/registry.py`)
Deux `TrophicSpec` neuves, **catégorie neuve `disperseur`** (personne ne la lit :
vérifier par grep de `category_density(` qu'aucun effet ne la consomme, et mettre à
jour la liste des catégories admises dans `tests/test_faune_dediee.py` l.~80). Sels
neufs dans la série `_SALT_*` (valeurs libres, vérifier l'unicité). Ordre : avant
les super-prédateurs (ils ne sont proies de personne dans ce tronçon).
- **geai** : habitat = couronnes ligneuses (plots foliaires d'arbres ≥ 300 cm) +
  `lisiere_w` fort (≈ 0,35, il niche en forêt et vient au jardin) ; ressource =
  fruits à coque mûrs sur les arbres (chêne, hêtre, noyer, noisetier) de la tuile,
  normalisée ; fenêtre de jour large (résident). Pas de prédateur ici.
- **ecureuil** : habitat = couronnes ligneuses **connexes** (un plot foliaire dont
  ≥ 2 voisins sont aussi foliaires d'un ligneux — l'écureuil circule par les
  cimes) + `lisiere_w` modéré ; ressource = mêmes fruits à coque, poids fort sur
  noisetier et noyer ; hiver : actif (il vit de ses caches) — fenêtre large.
Fonctions de ressource/habitat dans `fields/population/resources.py` (patron
`_merle_food_grid` / `_base_habitat_grid`), exportées comme les autres.
Encyclopédie faune : entrées `geai`, `ecureuil` dans `fields/faune_encyclo.py`
(blurb + liens d'interconnexion **symétriques** : chêne, hêtre, noyer, noisetier,
rapace pour l'écureuil seulement si on l'ajoute plus tard — sinon pas de lien).

## Caches (`sim/zoochorie.py`)
Même mécanique de prise que le merle (④), espèces lues par `mange_par` :
chêne `("geai", "ecureuil")`, hêtre idem, noyer idem, noisetier idem. Cohortes
`maturite >= 1.0`. Glandée : une année forte dépasse l'appétit → plus de fruits
tombent au pied (chemin ②) : c'est la satiation, ne rien ajouter.
- Graines : `n = prise × P_OUBLI` (geai ≈ 0,1, écureuil ≈ 0,1, placeholders).
- **Geai** : dépôt pondéré par la grille **découvert** du monde : lumière-sol
  (`eco.lumiere`) haute × (1 − couverture du sol) × (1 + bonus si un repère vertical
  — ligneux, support, mort debout — est à ≤ 2 plots). Peut changer de tuile (tampon
  monde du ④).
- **Écureuil** : dépôt dans un rayon `R_ECUREUIL_CM` ≈ 1500 cm autour de l'arbre
  source, pondéré par l'**anneau de lisière des couronnes** (plots non foliaires à
  ≤ 2 plots d'un plot foliaire ligneux).
- Origines `"geai"`, `"ecureuil"`.

## Apport de la ceinture
Un secteur `foret` de `game_state["ceinture"]` (`fields/peripherie.py`,
`ESSENCES_FORET`) envoie à l'automne des grains portés par le geai : chêne toujours
(chênaie-hêtraie normande) + l'essence du secteur si elle est à fruits à coque
(`hetre`). Intensité ∝ `densite_ligneuse` × densité moyenne de geai de la tuile ×
`facteur_glandee` de l'espèce, `origine="ceinture"` côté encyclopédie mais déposé par
le geai (grille découvert, bande de plots côté secteur prioritaire). Gènes :
`founder_genes` (`fields/seedbank.py`). Sans ceinture : rien (golden).

## Ne PAS faire
- Pas de mulot (⑥), pas de prédation des grains.
- Ne mettre ces guildes dans aucune catégorie existante (`auxiliaire` changerait la
  régulation des ravageurs ; `herbivore_vertebre` déclencherait les dégâts racinaires
  du campagnol).
- Ne JAMAIS lancer `test_epaisseur_500ans`.

## Tests
`tests/test_geai_ecureuil.py` : (a) chêne mûr + geai : glands pris, grains `geai` en
terrain découvert, aucun sous couronne dense ; (b) écureuil absent sans couronnes
connexes, présent avec un bosquet ; (c) grains `ecureuil` dans l'anneau de lisière,
dans le rayon ; (d) ceinture `foret` : grains de chêne apparaissent à l'automne, rien
sans ceinture ; (e) année de glandée : la prise sature, la chute au pied augmente.
Lancer `test_population`, `test_faune_dediee`, `test_peripherie*`.

## Golden
`a10b7225…` **INCHANGÉ** attendu : catégorie non lue, pas de ceinture, pas de fruit à
coque mûr au smoke. Le champ `geai` vivra peut-être sur la couronne du jeune pommier
(habitat) : sans lecteur, aucun effet. Si le hash bouge : chercher le lecteur caché,
ne pas re-figer.

## Perf
+2 guildes : `full` 5 ans, tick médian an 3-5, ≤ +10 %.

## F5
Aucun (vue au ⑧).
