# Conception : les formes des plantes (reste de D118 (A))

Figée le 2026-11-04 avec Nico. Sprint : `sprints/rendu/pixelart/sprint_formes_plantes/`.
Précédents : `docs/rendu/ambiance/conception_automne_visible.md` (11 arbres), `docs/vegetal/catalogue/conception_trefle_dominant.md` (prairie), `docs/rendu/pixelart/etude_brief_da_16bits.md` (grammaire).

## 1. Le problème

Nico, F5 du 2026-10-30 : « les plantes ressemblent à des plantes mais pas à leur modèle naturel ; toutes se ressemblent en mode plante générique ».

La cause n'est pas le dessin, c'est le squelette. Vérifié à `67b2ea6` :

- 39 espèces sur 40 ont le même squelette après un an : 17 segments, 84,5 cm [`grow_plant` seul, sans lumière ni gènes, seed 42 ; la tomate à part]. Les paramètres de croissance sont les défauts de `PlantBase`, sauf `max_height_cm` et `max_extent_cm` du lierre et du jasmin. La vue dessine ce squelette avec des touffes.
- Le bois dessiné n'a aucun rapport avec la hauteur moteur :

| Espèce, `full` an 2 [seed 42, n=1 run, VM, sans automate] | Bois (cm) | `height_cm` |
|---|---|---|
| Sphaigne | 89 | 4 |
| Trèfle (corrigé à l'écran par D126) | 82 | 8 |
| Basilic | 86 | 16 |
| Bourse-à-pasteur | 96 | 33 |
| Tournesol | 88 | 119 |
| Haricot | 80 | 145 |

- Captures `pluie_continue` et `floraison_saisons`, ×4, s26 : même tige et 2 ou 3 touffes en bonsaï pour chaque espèce.

Restent 36 espèces. Les 11 arbres et les 4 de prairie (trèfle, dactyle, fétuque, plantain) sont faits.

## 2. Décisions de Nico

- **F1 Port dessiné par la vue.** 33 espèces passent à des ports dessinés depuis une fiche, sans dessiner leurs segments. Tomate, lierre et jasmin (`procedural_growth`) gardent leurs segments, avec feuilles et fleurs revues.
- **F2 Taille : clic sur la plante, coupe visible.** Le pied dessiné se rabat puis repousse. Arbres, tomate, lierre et jasmin gardent la taille au segment.
- **F3 Formes seules.** Les 36 espèces, leurs fleurs, feuilles et vrilles en grammaire SNES, et des ombres à la vraie hauteur. Le reste de D118 demeure dans une D118 réduite. La perf est un garde-fou par tronçon.
- **F4 Plus de squelette pour les herbacées à port** (ajouté le 2026-11-04 après le rapport perf de l'an 8). Voir §4.6.

## 3. Pourquoi la vue, pas le moteur

Ces segments ne pèsent presque pas dans l'écologie (ils coûtent en revanche du CPU, §4.6) : l'empreinte des espèces non migrées suit leurs stades. Patcher en mémoire `max_height_cm`, `max_extent_cm`, `emit_length_cm` et `max_segments` laisse le golden identique [smoke] et la population identique [`full`, seed 42, 2 ans, n=1 run par côté, VM].

Régler les segments ne donnerait pas la forme : le patch laisse le tournesol à 37 cm de bois pour 112 cm de hauteur [`full` an 2, n=1 run, VM], et une rosette n'est pas un axe qui s'allonge. Migrer ces espèces en `procedural_growth` déplacerait leur empreinte, donc toute l'écologie.

**Limite assumée** : la forme ne naît pas de la croissance. Elle suit `height_cm`, le stade, la floraison, les fruits et la santé donnés par le moteur. Pas de phototropisme visible sur ces espèces.

## 4. Le modèle retenu

### 4.1 Fiche → recette

`docs/vegetal/croissance/fiches_herbacees.md`, même format que `fiches_arbres.md` : port, taille adulte, tige, disposition et forme des feuilles, limbe et nervation, couleur, fleur, fruit, vrilles, ce qui se voit au pied, ce qui distingue l'espèce à ×1, ×4 et ×8. Chiffres marqués `[odg]` ou `[choix]`.

Une ligne de table C# par espèce traduit la fiche : le port, ses paramètres, la feuille, la fleur, le fruit. **Aucune fonction par espèce** ; si une espèce en réclame une, c'est un 8ᵉ port à justifier.

### 4.2 Les 7 ports

| Port | Lecture | Espèces |
|---|---|---|
| Rosette, ± hampe | Feuilles en étoile au sol, hampe florale selon l'espèce et l'âge | pissenlit, mâche, bourse-à-pasteur, molène, drosera, carotte, ail |
| Tige à feuilles étagées | Axes dressés, feuilles opposées ou alternes qui rapetissent vers le haut, sommet fleuri | tournesol, ortie, basilic, poivron, phacélie, bourrache, moutarde, armoise, chanvre, achillée, consoude, menthe |
| Chaume | Brins qui partent de la base, feuille-ruban, épi ou panicule ; nœuds pour le bambou | blé, seigle, pâturin, bambou |
| Couvre-sol rampant | Tapis bas, stolons ou coussin ; pas de tige lisible | fraisier, violette, minette, sphaigne |
| Buisson ou coussin | Masse ligneuse ronde ou cannes arquées | thym, lavande, myrtille, framboisier |
| Grande rampante | Grandes feuilles palmées au sol, grosse fleur | courgette |
| Volubile | Tige qui spirale autour de son support, sinon tas au sol | haricot |

Restent sur leurs segments : tomate, lierre, jasmin.

Molène et carotte sont bisannuelles : rosette l'an 1, hampe l'an 2. Le port lit le stade.

### 4.3 Ce que le port reçoit et remplace

Reçoit : `height_cm`, stade, `foliage_density`, `feuillage`, `automne`, organe, floraison, `fruits`, santé, sémiologie, météo, mort. Il réutilise le chemin de `PlantRenderer.Prairie.cs` : un lot de triangles par plante, couleurs par `Ton`, positions au hash de l'individu, marques sur les feuilles de devant.

Remplace, comme la prairie : les mesures de port, l'ombre, le picking, la raideur au vent et la boîte de cuisson suivent le port dessiné, plus les segments. **Les ombres retrouvent la vraie hauteur** par ce biais.

Les fruits restent ceux du moteur, placés sur le port au hash de leur index. La récolte est déjà désignée par position : à vérifier sur chaque port fruitier.

La hauteur moteur saute au changement de stade (`height_at`). Le ② mesure l'ampleur. Si le saut se voit, la vue rejoint `height_cm` par pas ; rien côté moteur.

### 4.4 La taille (F2)

Python reste la vérité : `tailler` et `arracher` notent la semaine de coupe dès que le geste est payé, `pincer` note la sienne (rien à retirer une fois le squelette parti, §4.6). Le pont envoie, pour les espèces non migrées seulement et si non nuls, deux hints décroissants (patron de `feuillage`) :

- `rabattu` ∈ [0,1], retour à 0 en 8 semaines `[choix]` : hauteur × (1 − 0,6 × rabattu), moins de feuilles.
- `pince` ∈ [0,1], retour à 0 en 12 semaines `[choix]` : hauteur × (1 − 0,15 × pince), rayon × (1 + 0,2 × pince), plus touffu. Le basilic pincé ramifie.

Le clic vise toute la plante, sans `target.segment` et sans surlignage de segment, repli serveur déjà en place. Les 4 de prairie en bénéficient : la limite D127 « taille armée sur trèfle » se ferme.

**Limite assumée** : la coupe est visible, mais `height_at` ne bouge pas : ombre et lumière de la plante restent celles de son stade, comme aujourd'hui.

### 4.5 Grammaire

Le brief s'applique, dialecte 3 (« chaque plante est une icône lisible à 3 ou 4 tons ») : motif estampillé plutôt que contour rempli, 3 à 5 tons, éclat côté soleil, ombre colorée, contour sélectif sur fleurs et fruits. Repris de D118 (B) : fleurs, spires du haricot, ovales vert uni et nervures grossières à ×32.

### 4.6 Plus de squelette pour les herbacées à port (F4)

Une fois dessinées sans leurs segments, ces espèces n'ont plus de raison de les faire pousser.

| `full`, an 3 [seed 42, n=1 run par côté, VM, charge plus haute côté « sans »] | Avec | Sans |
|---|---|---|
| CPU sur l'année | 120 s | 71 s |
| Tick médian | 2 264 ms | 1 365 ms |
| Segments | 15 468 | 1 299 |
| Plantes / espèces en fin d'année | 694 / 20 | 694 / 20 |

Golden identique au même essai [smoke, `grow_plant` coupé en mémoire]. Origine du gain non isolée : le rapport PC ne donne que 5 à 14 % à `grow_plant` [n=5 ticks, échantillonnés, PC].

**Correction au bilan du ⑤ : ce tableau surestime le gain, ne pas en tirer −41 %.** Son A/B était à charges différentes. Re-mesuré en parallèle à charge comparable, le gain en an 3 est d'environ −8 % au tick et −12 % à la semaine avec snapshot [`full`, seed 42, n=2 runs par côté, charge 5 à 10, CPU `process_time`], −1 % et −1 % en an 1, −4 % et −5 % en an 2 [mêmes runs]. Le nombre de segments, lui, est confirmé [n=3 runs par côté].

**Concernées** : `not procedural_growth and not ligneux and mode_grimpe is None`, **sauf fraisier et courgette**, restés à squelette (écart décidé au ⑤) : `organ_sites` compte leurs apex, le collet seul leur donnerait 1 fruit à vie. Soit 30 espèces. Les ligneux non migrés (thym, lavande, myrtille, framboisier) et le haricot gardent leurs segments : bois sec, chute des arbustes et `sim/grimpe.py` les lisent.

**Reste vrai** : le collet demeure et continue de vieillir, car `sim/actions/gestes.py` déduit l'âge du pied de `s.age_weeks`. Une plante garde un segment, donc la structure du snapshot reste valide.

**Ce qui change volontairement** : une taille d'herbacée ne retire plus de segment. Pour garder le retour au sol, la masse déposée se déduit de la hauteur rabattue, même ordre de grandeur qu'aujourd'hui, à mesurer. Pas d'effet attendu sans geste. **Bilan du ⑤** : pas d'effet sans geste, digests identiques sur 156 semaines [`full`, seed 42, n=3 runs par côté] ; sous automate curatif, masse cumulée sur 3 ans 3,87 → 31,68, soit ×8 [n=1 run par côté], à valider par Nico.

## 5. Philo de design

- **#1, #2** : aucun effet sur la simulation ; la coupe reste un geste coûteux, et son hint ne fait que la montrer.
- **#3** : zéro RNG, tout au hash de l'individu.
- **#5** : l'espèce se lit dans sa forme, sans étiquette ni chiffre.
- **Pas de nouvelle espèce** : pas de voix à écrire.

## 6. Mesure et perf

Le calibrage se valide par mesure, le F5 ne juge que le ressenti.

- **Banc** `planche_especes` : les 40 espèces adultes séparées.
- **`tools/mesure_silhouettes.py`** : masques des sprites (`mesure_da --ref`), comparés par paires.
- **Paire confondue** : mêmes proportions et même gabarit à 15 % près, recouvrement des masques > 0,7 (grille 16×16 à ×4, 4×4 à ×1), et teinte moyenne ΔE OKLab < 0,05 `[choix, recalibré au ① : mesures/avant.md]`.
- **Cible** : 0 paire confondue à ×4, au plus 3 à ×1 `[choix]`. Avant : 28 à ×4, 14 à ×1 [seed 42, n=1 capture, VM].
- **Effet en jeu** : captures de `full`, pas seulement du banc.
- **Hauteur dessinée** : `height_cm` à ±20 % ou ±15 cm, le plus large, par port `[choix, recalibré au ①]`. Avant : 30 espèces sur 40 hors tolérance à ×4 [seed 42, n=1 capture, VM].
- **`tools/mesure_da.py`** sur chaque port : tons, noir, contour, aplat.

Perf, à chaque tronçon sur `full`, `tools/perf_vm.sh` avant/après :

- draw calls constants ;
- FPS non dégradés ;
- durée de cuisson par plante ≤ +10 % ;
- boîtes de cuisson plus petites attendues, à mesurer (une violette ne réserve plus 85 cm d'atlas) ;
- recuisson seulement si ce qui est dessiné a changé (aujourd'hui `SetStructure` invalide à chaque appel).

Moteur : deux entiers par plante, écrits à la coupe. Le tronçon squelette vise le gain du §4.6, re-mesuré des deux côtés à charge comparable.

## 7. Hors périmètre

D118 réduite : encart météo, heatmap vent, mention des Options, ombres OFF par défaut, reliquats D112 (p)(q)(r)(s), scintillement de glace, rivière Est, perf ×32 et à-coups de zoom, D110 (c)(f).

Hors du tronçon squelette : les ligneux non migrés et le haricot. Migrer ou alléger leurs segments relève de D118 (D).
