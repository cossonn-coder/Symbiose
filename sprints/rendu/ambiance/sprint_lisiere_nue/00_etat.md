# Sprint LISIÈRE NUE (D124) — état partagé

**Conception** : `docs/rendu/ambiance/conception_lisiere_nue.md` (figée le 2026-11-02).
**Où on en est** : ①, ② et ③ faits (③ non commité à l'écriture de cette ligne), reste le F5 de Nico et la clôture.

## Décisions clés (Nico, 2026-11-02)

- Branches derrière la couronne, révélées par le dégarnissement ; neige et givre dessus.
- Fleurs en colonies réalistes, vérité moteur ; les pollinisateurs y mangent et s'y voient.
- Couronne d'hiver réaliste : feuilles sèches sur hêtre, charme, chêne ; bouleau nu.
- Damier de l'assise cassé.
- Cadence ok mais vigilance : tick an 2 ≤ +10 %, draw calls constants, rien de reconstruit par semaine.

## Carte des tronçons

| # | Kickoff | Golden | État |
|---|---|---|---|
| ① | `01_colonies_moteur.md` — colonies, nourriture, pont 0.6.4, mesure sur 3 ans | intact, vérifié (`ac48b170…`) | **fait** |
| ② | `02_vue_fleurs_damier.md` — fleurs en colonies, butineurs de bord, damier | intact, vérifié (`ac48b170…`) | **fait**, F5 à faire |
| ③ | `03_vue_branches.md` — branches, couronne d'hiver, protocole F5 | intact, vérifié (`ac48b170…`) | **fait**, F5 à faire |

## Bilan ① (pour le tronçon ②)

**Format du pont 0.6.4.** Chaque secteur du bloc `ceinture` garde ses 10 champs et gagne :

```json
"floraison": {"blanc": 1.0, "jaune": 0.0},
"colonies": [{"u": 374.2, "depth": 383.6, "ru": 183.1, "rd": 163.8,
              "couleur": "blanc", "graine": 1424507651, "butineurs": 6}]
```

- `u`, `depth` : centre en cm, repère de `DecorLayer.EdgePoint(cote, u, depth)`. `ru` le long du bord, `rd` en profondeur : demi-axes en cm.
- `graine` : pour les bords irréguliers côté vue. La géométrie du moteur est une ellipse lisse.
- `floraison` : identique sur les 4 secteurs, lire le premier. Horloge = `week_in_year` du snapshot. Fenêtres : jaune wiy 4-14, blanc wiy 7-19.
- `butineurs` : 0 à 10, 0 sans floraison. Seuls `floraison` et `butineurs` changent par semaine.
- Le bloc part chaque semaine, mais `MemeProfil` (`DecorLayer.Pont.cs`) ne compare que ses champs : le décor ne se reconstruit pas. Pour ②, y ajouter les colonies en comparant la géométrie, jamais `butineurs`.
- Forêt, falaise : `colonies` vide. Rivière : 0 ou 1 colonie, côté jardin (depth 70-100 cm, `rd` 50-70) ; elle peut frôler la berge, à couper à la peinture.

**Code.** `fields/fleurs_lisiere.py` (géométrie, floraison, nourriture, compte de vue), `BordureMixin.maj_fleurs_bord` (carte mémoïsée, scalaire par semaine), `eco.fleurs_bord` lu par `_make_nectar_grid`. Effet de bord voulu : le miel des ruches en profite, il lit la même grille.

**Écarts au kickoff.**
- `bancs/mesure_calendrier` lit un banc sans ceinture : il ne peut pas voir les colonies. Mesure faite par `mesures/mesure_butineurs_bord.py`.
- Liste clairsemée de plots plutôt que grille pleine, même sens, moins de travail.

**Mesures** (`mesures/apres_moteur.md`) : tick an 2 +4,7 % [n=2 par côté, VM, une mesure sous charge 7,13], plantes an 3 660 → 690 [seed 42, n=1 graine].

**D119 (c) reste ouverte** : pommier × butineurs en an 1 de 0/2 à 1/2 semaines [`full`, seed 42, n=1 graine, marge 0,002 sur le seuil], pollen toujours 0 pendant la floraison. Le pommier fleurit avant les colonies et par temps froid ; nourrir plus n'y change rien. À trancher par Nico : population de départ (touche le golden) ou fenêtre plus précoce.

**Tests.** `tests/test_fleurs_lisiere` vert. `test_parasite` rouge aussi sur l'arbre d'avant : pas lié. `registry.py` à 304 LDC (301 avant) : zone de vigilance.

## Bilan ② (pour le tronçon ③)

**Code.** `DecorLayer.Colonies.cs` (lecture, semis, floraison), `ForagerLayer.Bord.cs` (insectes, `TempsCourt`), `DrawAssise` en nappes de bruit (`BruitValeur`, `BordFond`). Le shader reçoit `f_blanc`, `f_jaune`, `i_fleur_jaune` ; `lisiere()` prend l'`id` de palette, utile au ③ pour la marcescence. `DrawArbreKit` non touché.

**Écarts au kickoff.**
- Banc F10 sans pont : colonies fixes et fenêtres recopiées (`ColoniesBanc*`, `FloraisonBanc`), sinon le banc n'aurait aucune fleur. Jamais utilisés en jeu. Pas d'insectes sur ce banc.
- Insectes de ×1 à ×4 (le jardin : ×4 seulement) ; aucun à ×0,5. Hors `_entries` : ni survol, ni piqûre, ni pollen. Espèce au hash : le pont ne donne qu'un compte.
- En plus : rang du fond, limite de bande et couture de friche (`mesures/apres_vue.md`). La friche ne prolonge plus son fond au-delà de sa bande.

**Mesures** (`mesures/apres_vue.md`) : draw calls ×0,5 78 → 78, ×1 79 → 80 [n=1 run par côté, VM] ; sommets ×0,5 +13 %, ×1 +11 % [seed 42, s12, VM].

## Bilan ③

**Code.** `DecorLayer.Branches.cs` (nouveau, 93 LDC) : charpentières puis axe, formes par `TreePort`, tout ramené dans l'ellipse de l'enveloppe. Dans `decor_indexe.gdshader` : `DEGARNI_MAX` 0,85 → 1,02, l'enveloppe (orientation 9, classe feuillu) part 1,4 fois plus vite, touches rousses de 2×2 px. Uniform `i_bouleau` dans `DecorLayer.Saison.cs` : l'id d'un bouquet vient de l'atlas, donc constant à tout palier ; le plan du rideau passe par R.

**Écarts au kickoff.**
- Palier ×0,5 allégé d'emblée (3 charpentières, sans fourche, axe en un seul polygone). Fourches ajoutées à ×1 et plus, sinon l'arbre nu n'a que quelques traits.
- L'axe est posé après les charpentières : il couvre leurs racines carrées, visibles à ×2.
- `hauteur` sature à environ 88 px au-dessus du pied : le gradient ne joue que dans le bas des couronnes. Suffisant, non modifié (les brumes le lisent aussi).
- Feuilles sèches tombées à `degarni` < 0,6 : à un seuil plus bas, elles se lisaient en baies rouges sur le vert tendre.
- Règle shader « tout sauf le bouleau » : l'aulne (teinte charme) et le noyer (teinte chêne) gardent donc des feuilles sèches, le saule (teinte bouleau) est nu. Réalisme discutable pour l'aulne, à juger au F5.

**Mesures** (`perf_vm.sh -b full -w 12 -k 3 -n 5`, seed 42, llvmpipe, FPS non transposables au PC) :

| Palier | Draw calls avant → après | Sommets du décor avant → après | FPS avant → après |
|---|---|---|---|
| ×0,5 | 79 → 78 à 83 [n=1 → n=3 runs, VM] | 42 126 → 43 764 (+3,9 %) [seed 42, s12, VM] | 8,6 → 7,3 à 8,6 [n=1 → n=3 runs, VM, charge 0,5 → 2 à 5] |
| ×1 | 81 → 80 [n=1 → n=2 runs, VM] | 101 538 → 104 904 (+3,3 %) [seed 42, s12, VM] | 8,0 → 7,4 à 8,2 [n=1 → n=2 runs, VM, charge 1,8 → 4 à 6] |

Sommets ×2 108 534 → 114 798, ×4 111 516 → 117 780 [seed 42, s12, VM]. Cette graine compte peu de feuillus : terrain à 4 forêts non mesuré. Draw calls : les écarts suivent le nombre d'objets du jardin, la maille reste une seule. Aucune donnée ajoutée par semaine.

**Captures lues** (`smoke -B`, bord N ; ×1 s20 s34 s40 s46 s55 s62, ×0,5 s20 s36 s46, ×2 s46, neige et gelée à ×1 s46) :
- s20 : couronnes pleines, branches invisibles. ×0,5 : un point clair minuscule dans une couronne, à l'œil au F5.
- s34 : les bouleaux, en avance, montrent déjà leurs branches dans l'orange ; hêtres et chênes encore pleins.
- s36 ×0,5 : couronnes rousses trouées, charpente visible, bois encore dense.
- s40, s46 : plus aucun disque. Bouleaux nus ; chênes et hêtres en branches avec des points roux. À ×0,5 les points se lisent bien, à ×2 certains flottent loin d'une branche.
- Neige : plaques blanches sur charpentières et axes, troncs non touchés. Gelée : givre sur les branches, plus la trame de brume froide, très marquée.
- s55 (printemps) : couronnes qui se reforment, aucun point roux. s62 : couronnes pleines.
- Aperçu non traité : sous la neige, l'ombre au pied reste un aplat sombre sans neige.

## F5 (ressenti, 2 minutes)

Lancer une partie, avancer sur une année, regarder la lisière, sans plus :

1. **Printemps** : les taches de fleurs font-elles naturel, sans quadrillage ? Des insectes dessus en zoomant ? Le givre sur la prairie n'est-il pas trop marqué ?
2. **Été** : prairie sans rectangles, contour de la friche correct ?
3. **Automne** : les branches apparaissent-elles peu à peu ?
4. **Hiver** : un vrai bois nu ? Les feuilles sèches plaisent-elles ou font-elles des points parasites ? La neige sur les branches se voit-elle ?

## Ce qui reste

F5 de Nico, puis clôture (journal, `DETTE.md` D124, `BACKLOG.md`). D119 (c) reste ouverte, voir le bilan ①.
Garde-fous : ne JAMAIS lancer `tests/test_epaisseur_500ans.py` ; mesures ≤ 3 ans de jeu.
`test_succession` et `test_edaphique` étaient rouges avant le sprint AUTOMNE VISIBLE.

## §REPRISE

Code des 3 tronçons fait. Lire `CLAUDE.md` + ce fichier, puis clôture du sprint après le §F5.
