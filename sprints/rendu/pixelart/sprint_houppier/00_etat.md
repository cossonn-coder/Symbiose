# Sprint HOUPPIER (arbres + lierre, D118) — état

**Conception figée le 2026-11-05** : `docs/rendu/pixelart/conception_houppier.md`. 5 tronçons, à exécuter par `/sprint-auto sprint_houppier`. Golden `a10b7225…` attendu intact partout, aucun re-figeage prévu.

## Tronçons

| # | Kickoff | État |
|---|---|---|
| ① | `01_grimpantes_tenue.md` | **fait**, golden `a10b7225…` intact, F5 à faire |
| ② | `02_grimpantes_sans_fin.md` | **fait**, golden `a10b7225…` intact, F5 à faire |
| ③ | `03_fruits_arbres.md` | **fait**, golden `a10b7225…` intact, F5 à faire |
| ④ | `04_gerbes_cuisson.md` | à faire |
| ⑤ | `05_houppier_vue.md` | à faire |

## Sujet

Retour F5 de Nico, 2026-11-05 (D118) : arbres, beaucoup plus de feuilles dans le houppier et de petites branches pour les porter (précise le point (4) de D118, « masses ovales en pompon sur rameaux verts »). Et D118 (a) : lierre qui régresse ; attendu de Nico : hors coupe, il continue de grandir et de grossir.

## Constats vérifiés (2026-11-05, HEAD `20dbea5`, golden `a10b7225…`)

**Arbres**

- Le moteur plafonne à 70 segments (90 pour le figuier), dont 19 à 33 apex à 10-25 ans sauf jeunes ports [`mesure_arbres`, seed 42, sans lumière, VM] ; 31 à 77 % des segments portent des feuilles [mêmes conditions]. Un segment fait 40-50 cm : c'est la charpente, il n'y a aucun rameau fin.
- Vue : ×4 = une ellipse par paquet de 3 feuilles (`DrawMassesFeuillage`) → les pompons. ×2 = touffes le long des segments feuillés, 2 touffes voisines à 28 cm (`AjouterTouffeAutour`) → bouts garnis, milieu vide. Bois : `Lignification` = apex 0 → `ApexColor` vert vif sur tout le segment apex de 40-50 cm → les rameaux fluo.
- `Hash01(…, i, …)` est indexé sur l'indice du segment. `_rebuild` réindexe à chaque coupe : les présences au hash sautent. Peu visible aujourd'hui, très visible si on densifie.
- Cuisson d'un arbre aujourd'hui, ms par coup de pinceau : ×2 0,35 à 3,48 ; ×4 0,96 à 6,98 ; ×8 7,25 à 78,35 (figuier) [`foret_ports`, an 10, n=1 coup par espèce, 3 à 11 espèces selon le cadre, VM, charge 1 à 5]. ×16 non mesuré, aucun arbre cuit dans le cadre.
- `foret_ports` n'est pas un banc lisible : la maison et les bords du monde gênent (figuier à 1275,775 ; arbres à x 2275 > 2000).

**Lierre** [`accroches_adultes`, seed 42, n=1 run, VM, 156 semaines, ablations en mémoire, charge 2 à 10]

- Base : longueur totale 132 à 252 cm, hauteur 89 cm en s156, 8 chutes de plus de 15 % en une semaine.
- Causes : plafond `max_segments` 40 × `emit_length_cm` 8 = 320 cm de bois au mieux, coupe chaque semaine dès le plafond, apex compris ; tempête 5 fois, −342 cm ; neige 3 fois, −91 cm. Cladoptose : aucune sur ce run de base.
- Essais : `emit` 20 + `cap` 80 + `wood_persistence` 4000 → s156 1 097 cm, hauteur 302, 2 chutes. Épaisseur max 0,98 → 1,27 cm en 3 ans, `girth_max_cm` 1,5 par défaut.
- Golden identique avec lierre et jasmin patchés (emit 20, cap 80, wp 4000, fragilité 0,3, girth 6) [smoke].
- **Non résolu** : jasmin aux mêmes réglages 857 → 436 cm entre s26 et s156, 5 chutes [mêmes conditions], cause non isolée. Lierre à 302 et jasmin à 251 cm dépassent leur treillis de 180 cm, à vérifier.

## Décisions arrêtées (Nico, 2026-11-05)

1. **Rameaux et brindilles dans la vue seule**, à la cuisson, dans `canopy_r`, table par espèce. **Audit demandé** du coût s'ils étaient au moteur.
2. **Clé de hash stable** : la base du segment, plus son indice.
3. **Lierre : girth relevé vers 6 cm [choix], bois moins cassant.**
4. **Grimpantes sans fin de pousse** : au sommet de l'appui elles continuent, cherchent un support à proximité (arbre, autre plante, mur) et s'y accrochent. Au-delà d'une longueur sans support, la tige plie vers le sol ; cette longueur dépend de la lignification et de la dureté du bois ou de la fibre. La partie effondrée meurt.
5. **Jasmin dans le sprint.**
6. Questions de Nico à instruire : cuire au chargement, ou tout précuire et monter en RAM au lancement ? Fruits non vus à la dernière mise à jour. Fleurs qui manquent de détails.

## Audit : rameaux en vrais segments moteur (patch mémoire, rien d'écrit)

| Plafond, longueur de segment | Segments par arbre | `grow_plant` ms/arbre/sem | Cladoptose ms/arbre/passe | Plantes en JSON, `full` |
|---|---|---|---|---|
| Actuel (70, 40-50 cm) | 71 | 0,73 | 0,62 | 223 Ko |
| 200, 20 cm | 198 | 2,40 | 2,05 | 344 Ko |
| 400, 12 cm | 400 | 4,36 | 6,48 | 530 Ko |
| 800, 8 cm | 800 | 14,81 | 36,69 | 892 Ko |

[11 arbres à 20 ans, sans lumière pour les deux colonnes de temps, 6 arbres vieillis de 20 ans dans `full` pour le JSON, seed 42, n=1 run, VM, charge jusqu'à 19 sur la ligne 800, CPU `process_time`]

`full` an 2, plafond 400 contre actuel [seed 42, n=1 run par côté, VM, charge 3 à 17] : tick médian 890 → 1 031 ms, soit +16 % avec 736 plantes contre 627 ; pommier 405 → 261 cm, rayon 285 → 141 ; golden changé (`2979f0ff…`). Verdict : au plafond 400 le CPU reste supportable ; l'obstacle est le recalibrage des 11 arbres, l'écologie déplacée, le golden et le JSON ×2,4. Correction de la réponse précédente, qui présentait le calcul d'ombre comme l'obstacle principal.

## Constats sur fruits et cuisson

- **Fruits** : parmi les 11 arbres, seul le pommier a `fruitier` (cerisier, figuier, noyer non). `full` : un pommier, 8 à 10 fruits de s7 à s22 et de s59 à s74, plus 1 ou 2 tomates [seed 42, n=1 run, VM]. Fiche : pommes en sept.-oct. (s23-s30). Le rendu fonctionne : pomme vue à ×4 en s15 [n=1 capture], grosse, tout en haut.
- **Cuisson** : image propre à chaque individu, `SetStructure` salit un arbre à chaque snapshot (seuls les ports ont `DessinInchange`). `KitTouffe` existe déjà : pièces générées une fois, en codes de palette, teinte libre. `BakeQueue` : cuisson limitée au cadre et à sa marge.

## Arbitrages rendus (Nico, 2026-11-05)

7. **Rameaux en vue seule confirmés** après l'audit.
8. **Précuisson** : pièces (gerbes) à l'écran de chargement + cadre de départ cuit avant d'ouvrir le jeu + recuisson seulement si le dessin change.
9. **Fruits et fleurs dans le sprint** : cerisier, figuier, noyer fruitiers, fleurs des arbres sur les brindilles, date du pommier corrigée. Fleurs herbacées : restent à D118.
10. **Cap 80 conservé** (OK du 2026-11-05) : plateau de longueur accepté.

## Instruit après arbitrages (2026-11-05, patchs mémoire, rien d'écrit)

**Jasmin : cause réduite à deux réglages.** À emit 20, cap 80, wp 4000, fragilité 0,3, girth 6, il ne chute plus : 985 cm en s26, 1 142 en s156 [`accroches_adultes`, seed 42, n=1 run, VM, charge 2 à 6]. L'essai à 857 → 436 n'avait ni la fragilité ni le girth : l'un des deux, ou les deux, supprime la chute, non séparés.

**Lierre aux mêmes réglages : encore 866 → 670 cm** [mêmes conditions], plafonné par `max_height`/`max_extent` (zmax figé à 302). Plafonds relevés à 2000 : lierre 1 262 → 1 342 cm, jasmin 1 337 → 1 526 cm entre s26 et s156 [mêmes conditions] ; épaisseur max 3,03 → 4,18 cm [mêmes conditions]. Longueur en plateau au cap 80 (× 20 cm = 1 600 cm au mieux) : élagage cumulé lierre 4 232 cm, jasmin 3 039 cm [mêmes conditions].

**Treillis : dépassement confirmé.** zmax 251 à 302 cm pour un treillis de 180 : au sommet, `_apex_z_floor` repasse à `MIN_APEX_Z` et l'apex monte sans appui jusqu'à `max_height`. La décision 4 traite ce cas.

**Trous de la recherche d'appui** : `chercher_support` ne scanne que les plantes libres et mesure depuis le pied (`plant.x_cm`), pas l'apex ; rayon 75 cm. Deux lianes pourraient s'accrocher l'une à l'autre : à exclure.

**Fruits** : `fruitier=True` sur cerisier, figuier, noyer, figuier en `self` → golden identique `a10b7225…` [smoke]. Figuier `nectar = 0` et mode `insect` par défaut : sans `self`, 0 fruit attendu (non mesuré), et la figue commune se passe de pollinisation. `full`, 2 ans : cerisier 9-10 fruits, apparus entre s9 et s12, tombés entre s25 et s28, pommier 8-10, apparus entre s5 et s8, tombés entre s21 et s24 [seed 42, n=1 run, relevé toutes les 4 semaines, VM, charge 3 à 5] ; figuier et noyer absents de `full` sur ces 2 ans → banc requis, noyer `maturity_years` 15.

**Date des fruits : cause isolée.** `FRUIT_DMAT` 0,08 commun à toutes (mûr en ~12,5 semaines, chute à ~16). Le pommier ne peut pas arriver à l'automne, le cerisier reste trop longtemps. Levier : durée de maturation par espèce, défaut = valeur actuelle (tomate, framboise, fraise, courgette inchangées).

## Bilan ① Tenue (2026-11-05)

Réglages posés sur `Ivy` et `Jasmine` (vérifié : portés par les classes). Golden `a10b7225…` intact, `test_bancs_grimpe`, `test_grimpe` 10/10, `test_squelette_herbacees` 42/42, `test_sim_server` 321/321, build C# vert.

Tous les chiffres : [`accroches_adultes`, seed 42, n=1 run, VM].

| | Avant s156 | Après s52 → s156 |
|---|---|---|
| Lierre, longueur | 234 cm | 1 303 → 1 342 cm |
| Jasmin, longueur | 270 cm | 1 294 → 1 526 cm |
| Épaisseur max, les deux | 1,27 cm | 3,30 → 4,18 cm |
| Chutes > 15 %, lierre | 8 | 1 (neige, s128) |
| Chutes > 15 %, jasmin | 6 | 3 (tempête s53 et s81 ; s112 élagage + ombre) |

Creux restants, attendus du plateau : lierre 977 cm [s130], jasmin 1 000 cm [s130]. Coupes cumulées : élagage lierre 4 229, jasmin 3 039 cm. Nouveau : la cladoptose coupe, lierre 459, jasmin 441 cm (0 avant).

**Tick du banc** : médiane 99,8 et 101,8 ms contre 97,5 et 98,0 ms, soit +2 à +4 % [n=2 runs par côté, charge 2 à 3, `process_time`].

**Vue (`PlantRenderer.Lianes.cs`), hors prescription stricte** :
- `(int)` → `RoundToInt` sur le nombre de feuilles par segment : à emit 20 la troncature perdait des feuilles (jasmin ×4 : une tous les 20 cm contre 8).
- `TigeMaxCm` lierre 1,6 → 6, jasmin 0,5 → 2 [choix] : sinon le grossissement du moteur ne se voyait pas.

**Effets de bord à arbitrer ou traités plus loin** :
- `canopy_r` et `root_r` : lierre 61 → 103 cm, jasmin 65 → 108 cm en s156 ; hauteur 89 → 320 et 125 → 440 cm. `canopy_r` est le disque de l'extension maximale : une seule longue branche donne tout le disque d'ombre, nettement visible à ×4. Effet sur les voisines non mesuré.
- Rameaux raides qui partent en l'air loin du treillis, port en buisson plus qu'en nappe [captures ×4 et ×8].
- **Sans appui** (supports retirés en mémoire) : lierre 320 cm et jasmin 412 cm de haut en s156, contre 56 et 10 cm avant. Une liane libre tient debout jusqu'au ② (`L_crit`). Le ② doit le vérifier explicitement.
- Pied nu : 93 à 98 % de la longueur reste feuillée, `IsLeafy` coupe au-dessus de 2,5 cm. Laissé tel quel, un vieux lierre a le pied nu.

## Bilan ② Grimpantes sans fin (2026-11-05)

Neuf : `sim/growth/tige_libre.py` (L_crit, pliage, effondrement, biais de relais), `relais_appui` dans `sim/grimpe.py`, `relais_compatible` dans `world/support.py`, cause `effondrement` dans `mort_des_branches`, banc `liane_relais` (`bancs/lianes.py`, départ s20), `tests/bancs/test_liane_relais.py`. Golden `a10b7225…` intact, `test_liane_relais`, `test_bancs_grimpe`, `test_grimpe` 10/10, `test_squelette_herbacees` 42/42, `test_bois_mort` 42/42, `test_sim_server` 321/321. Aucun C# touché, build non concerné.

Réglages [choix] : `rigidite_tige` lierre 120, jasmin 80 ; marge d'effondrement 1,5 ; `PLIAGE_Z` −0,7 ; relais toutes les 4 semaines.

Tous les chiffres : [seed 42, n=1 run, 156 semaines, VM, charge 1 à 3].

| `liane_relais` | zmax dès s4 | Appui en s156 | Longueur s156 |
|---|---|---|---|
| Lierre, treillis seul | 205 cm (320 au ①) | treillis | 1 159 cm |
| Jasmin, treillis seul | 177 cm | treillis | 1 160 cm |
| Lierre, treillis + mur | 207 cm | mur, passé en s27 au plus tard | 1 247 cm |
| Jasmin, treillis + mur | 198 cm | treillis : le mur lui reste fermé | 1 207 cm |
| Lierre, treillis + arbre | 253 cm | pommier, dès s21 | 1 172 cm |
| Jasmin, treillis + arbre | 274 cm | pommier, dès s65 | 1 263 cm |
| Lierre, sans appui | 162 cm (320 au ①) | aucun | 1 164 cm |
| Jasmin, sans appui | 135 cm (412 au ①) | aucun | 690 cm |

Effondrements : jasmin sans appui 30 sur 156 semaines, lierre sans appui 7, et 0 sur les six pieds accrochés. Au plafond de 80 segments, `_elaguer` coupe d'abord les bouts les plus profonds : sur une liane accrochée, le pliage et l'effondrement ne se voient pas à 3 ans, à regarder au F5.

`accroches_adultes`, à comparer au ① : lierre 1 330 → 1 151 cm, 1 chute > 15 %, zmax 203 cm ; jasmin 1 278 → 1 505 cm, 2 chutes, zmax 175 cm. Épaisseur max inchangée, 4,18 cm.

Hôte : vitalité du pommier sous le lierre 1,0 sur 3 ans. Sous le jasmin, minimum 0,733, sans preuve que le jasmin en soit la cause. Aucun étranglement constaté à 3 ans.

Tick du banc : médiane 98,2 et 97,8 ms → 100,2 et 99,1 ms, soit +1 à +2 % [n=2 runs par côté, charge 1 à 3, `process_time`].

**Écarts au kickoff, vérifiés** :
- **Haricot** : digests DIFFÉRENTS sur `accroches_adultes`. Le critère ne pouvait pas tenir : la liane change de port, donc l'ombre et le sol du haricot. Le vrai test d'inertie est vert : `rigidite_tige` coupé en mémoire, haricot ET lianes bit-identiques à HEAD sur 156 semaines.
- **`DROOP_Z` ne plie pas** : un plancher laisse telle quelle une pointe qui monte. Ajout de `plier()`, qui courbe vers `PLIAGE_Z`.
- **`d` au départ de la partie libre** : le pipe model y additionne toutes les tiges, 4,18 cm au collet d'une liane sans appui, donc 3 m de tenue. `epaisseur_tige` retire la part du faisceau.
- **`axe_porteur` non respecté** : il protège le chemin vers le point le plus haut, celui qui doit tomber. La coupe part du point de pliage ; le collet et le bois sous l'appui ne sont jamais touchés.
- **`support_compatible`** refuse tout au sarmenteux : le jasmin n'aurait jamais relayé. `relais_compatible` lui ouvre structures et plantes, pas le mur.
- **Scan depuis tous les apex au-dessus de l'appui**, pas le seul plus haut : le jasmin n'atteignait jamais l'arbre.
- **Repère 2 m à 1 cm non retenu** : à 200, le lierre sur treillis gardait 320 cm et ne pliait jamais. 120 [choix] est à juger au F5.
- **Pré-croissance** : `pre_croitre` joue aussi `effondrer`, sinon une liane pré-vieillie arrive avec ses tiges pliées jusqu'au sol.

**Rapprochement gardé** (`vers_relais`) : jasmin, pointes au-dessus de 180 cm à 48 cm de l'appui contre 66 sans le biais, en médiane ; lierre 49 contre 48, mais 546 relevés contre 260. Seul le relais l'active, l'accroche initiale ne change pas.

**Limites et trous laissés** :
- Distance au TRONC pour un hôte : une pointe dans la couronne, à 111 cm du tronc, ne relaie pas. Le banc pose donc l'arbre du côté où pousse le jasmin.
- Le relais ne part que d'une liane déjà accrochée. Une liane libre reste à `chercher_support`, qui mesure depuis le pied.
- `_hote_candidats` garde `id(other)` et admet une grimpante comme hôte (préexistant, hors périmètre). Le relais, lui, utilise un rang stable et exclut les grimpantes.
- Longueur libre mesurée sur la seule hauteur : un rameau parti loin du treillis mais sous 180 cm reste « appuyé ».
- Pont : `dx_cm`/`dy_cm` peuvent dépasser 75 cm après un relais. Non vérifié côté dessin.

**À juger au F5** : port en cascade et `rigidite_tige` ; montée sur l'arbre et le mur ; `canopy_r` ; le banc n'est pas encore très lisible à ×2. Capture : `tools/capture_vm.sh -b liane_relais -w 104 -z 2 -c 1680,1000`.

## Bilan ③ Fruits des arbres (2026-11-05)

Neuf : levier `fruit_semaines_maturation` (`familles.py`, lu par `_tick_fruits`, défaut `FRUIT_DMAT`), `fruitier` sur cerisier, figuier, noyer, figuier en `self`, banc `verger_mur` (`bancs/verger_mur.py`), `tests/bancs/test_verger_mur.py`, phrases de fruits des 4 fiches (`ligneux.py`). `test_fruits.py` suit la durée du pommier. Golden `a10b7225…` intact, `test_verger_mur`, `test_fruits` 24/24, `test_sim_server` 321/321, automate, attraction, floraison, vent, catalogue, biotique verts. Aucun C#, build non concerné.

Durées [choix] : cerisier 7, figuier 9, noyer 9, pommier 17 semaines. Maturité commune inchangée pour tomate, fraise, framboise, courgette.

`verger_mur`, nouaison → premier fruit mûr → dernière semaine sur l'arbre [seeds 42, 7, 1516, 3 ans chacune, VM] :

| Espèce | Nouaison | Mûr | Sur l'arbre jusqu'à | Fiche | Fruits/an |
|---|---|---|---|---|---|
| Cerisier | s9-12 | s16-19 | s17-20 | juin-juil. (s11-19) | 4 à 10 |
| Figuier | s15-17 | s23-25 | s25-27 | août-oct. (s20-32) | 10 |
| Pommier | s8-11 | s24-27 | s29-32 | sept.-oct. (s24-32) | 1 à 10 |
| Noyer | s20-21 | s28-29 | s30-31 | sept.-oct. | 0 à 6, voir plus bas |

Figuier repassé en `insect` : 0 fruit en 52 semaines [seed 42], le constat du kickoff tient.

**Noyer : il noue mal, avant et après deux pieds.** Un noyer seul : 1, 1, 1 fruits [seed 42, an 1 à 3], 0, 0, 3 [seed 7], 0, 0, 1 [seed 1516]. Deux noyers à 450 cm, gardés au banc : 0 à 6 par pied, 5 années-pied sur 6 sans fruit au seed 1516 [mêmes seeds]. Dose reçue 0,004 à 1,6, contre 48 à 110 pour un pommier en insectes [mêmes runs]. `frac_nouaison` non touché, comme prescrit. Cause de la faiblesse du vent local non isolée (hypothèse non testée : l'arbre s'abrite lui-même). Un noyer ne portera donc souvent presque rien : à arbitrer.

**Effet en jeu, `full`, seed 42, 3 ans, avant → après** [n=1 run par côté, VM] :
- Fruits : pommier mûr s19-22 → s23-26, sur l'arbre jusqu'à s22-25 → s28-31 ; cerisier 0 → 9-10 fruits, mûr s16-18. Le pommier de `full` noue plus tôt qu'au banc (s7-10) : mûr dès s23, une semaine avant la fiche [seed 42].
- Figuier, noyer : absents de `full`, ou pas mûrs. Rien en jeu sur 3 ans.
- Litière `fruit` tombée, par an : 1,5 → 2,85 à 3,0.
- Faune sur le plot de l'arbre, an 2 : merle au cerisier s20 0,177 → 0,219, s24 0,169 → 0,204 ; cloporte s28 0,116 → 0,186. Pommier, pic du merle déplacé, s26 0,233 → 0,204. Moyenne par tuile : aucun écart lisible [s26, s36].
- Population s26, 154, 567, 708 plantes : identique à l'unité, 2 arbres.
- Tick médian 1 032 → 871 ms [charge 2 à 8, inégale entre les deux runs] : aucun surcoût visible, comparaison non fiable au-delà.

**Automate** : `but_satisfait` exige désormais un fruit mûr sur ces arbres, vérifié à la lecture. Aucun objectif de l'automate ne vise ces arbres aujourd'hui, donc pas exercé ; suites `test_automate_*` vertes.

**Écarts au kickoff et à la conception** :
- Noyer 9 semaines, pas « long » (conception §4). Le moteur le fait fleurir tard (défaut 60 degrés-jours, s13-18, fiche : mai) : une durée longue le ferait mûrir après la fiche. Avancer sa floraison serait l'autre levier, hors périmètre.
- Cerisier 7 et non 6 : à 6, le fruit ne reste mûr qu'une semaine, cumul flottant compris.
- `butineurs présents` : la pré-charge d'abeilles meurt avant les fleurs (0,002 en s12) ; le banc pose 3 rondelles `pollinisateur`, habitat réel.
- Arbres à 15-16 ans : à 6 ans un pommier a 8 segments, trop peu de sites.

**Trous vus, non traités** :
- Un arbre mort garde ses fruits, gelés sur le cadavre : `_tick_fruits` saute les morts (pommier mort en s133, seed 1516, 6 fruits, cause non cherchée). Préexistant, à voir au dessin (⑤).
- Titre de la page `P03` (« L'ombre du fruitier ») sans rapport avec son texte (paille). Préexistant.

**À juger au F5** : les 4 arbres portent à la bonne saison ; taille et couleur des cerises, figues et noix, non vérifiées ici (dessin au ⑤). Banc : `init config="verger_mur"` ; semaines à regarder, an 1 : s17 cerises, s25 figues et pommes, s29 noix.

## Hors périmètre sauf avis contraire

Reste de D118 : piquants d'ortie, fleurs, point de pollen, gestes, DA hors plantes.

## REPRISE

Lire `CLAUDE.md` + ce fichier, puis `visuals/PlantRenderer.Assemblee.cs`, `PaliersHauts.cs`, `Organs.cs`. ①, ② et ③ faits (voir Bilans). Prochaine étape : `/sprint-auto sprint_houppier`, tronçon ④. Sondes : recopiées au §Audit, le scratchpad ne survit pas.
