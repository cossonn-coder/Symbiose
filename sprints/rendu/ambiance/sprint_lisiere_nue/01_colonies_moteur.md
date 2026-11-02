# ① Colonies de fleurs au moteur + nourriture des butineurs + pont — golden INTACT attendu

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, `docs/rendu/ambiance/conception_lisiere_nue.md` §3.1 à §3.3.

## Objectif

Les colonies existent en Python, nourrissent les pollinisateurs, et le pont les transmet à la vue.

## À faire

1. **Géométrie** : fonction pure (seed, côté, type) qui rend les colonies d'un secteur, dans le repère que la vue sait lire
   (vérifier `DecorLayer.EdgePoint` : `u` le long du bord, `depth` vers l'extérieur, comparé à `fields/peripherie.rect_secteur`).
   Hash déterministe, zéro RNG vivant. Module neuf en couche `fields` (`fields/peripherie.py` est déjà gros : vérifier
   avec `tools/compte_ldc.py`). Mémoïser : une ceinture change rarement.
2. **Floraison** : facteur par couleur selon `week_in_year`, sur `data/code/calendrier.py`.
3. **Nourriture** : grille de proximité aux colonies, patron `BordureMixin.maj_lisiere` (mémoïsée sur signature, `None` sans
   ceinture, appelée `sim/engine/boucle.py` avant `tick_populations`). Ajoutée à la ressource dans `_make_nectar_grid`
   (`fields/population/registry.py`), pondérée par `attractivite`, avec le plafond existant. Pas de recalcul par plot chaque
   semaine : grille statique × scalaire. Vérifier comment passer la semaine à `resource_fn(eco, tile, plants)`.
   Vérifier aussi que l'invariant « floraison nulle ⇒ champ nul » reste vrai hors saison.
4. **Pont** (`tools/simserver/peripherie_route.ceinture_block`, pas `serialize.py` qui est à 398 LDC) : colonies par secteur,
   floraison courante par couleur, compte de butineurs par colonie dérivé de la population réelle (hint pur, borné, sans écriture).
   Version 0.6.4 dans `tools/simserver/version.py`. Adapter les tests qui vérifient la version.
5. **Tests** `tests/test_fleurs_lisiere.py` : déterminisme ; sans ceinture rien ne change ; pas de fleur hors saison ; aucune colonie
   en forêt ou falaise ; butineurs nourris près d'une colonie, pas près d'un bord sans colonie.
6. **Mesure** `mesures/apres_moteur.md`, monde `full`, seed 42, 3 ans maximum, chiffres marqués `[n=…, VM]` :
   - `bancs/mesure_calendrier.py` : le pommier croise-t-il des butineurs en an 1 (avant : 0/2 semaines de floraison [n=3 ans, VM]) ?
   - `tools/banc_cadence` : tick an 2 et plantes max, avant/après en alternance ; budget ≤ +10 %. Plantes en an 3.
   - Si le budget saute à cause de la population : réduire la nourriture, le signaler.

## Golden

**INTACT attendu** : le smoke n'a pas de ceinture (`commands.py` ne la pose qu'en `full`/`propre`). S'il bouge, c'est un bug : ne pas figer.

## NE PAS

Ajouter une espèce au catalogue. Donner une population de départ aux butineurs. Toucher au C#. Lancer `tests/test_epaisseur_500ans.py`.
