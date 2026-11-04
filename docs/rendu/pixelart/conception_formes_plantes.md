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

## 3. Pourquoi la vue, pas le moteur

Ces segments ne pèsent presque pas dans la simulation : l'empreinte des espèces non migrées suit leurs stades. Patcher en mémoire `max_height_cm`, `max_extent_cm`, `emit_length_cm` et `max_segments` laisse le golden identique [smoke] et la population identique [`full`, seed 42, 2 ans, n=1 run par côté, VM].

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

Python reste la vérité : `tailler` et `arracher` notent la semaine de coupe s'ils ont retiré du bois, `pincer` note la sienne. Le pont envoie, pour les espèces non migrées seulement et si non nuls, deux hints décroissants (patron de `feuillage`) :

- `rabattu` ∈ [0,1], retour à 0 en 8 semaines `[choix]` : hauteur × (1 − 0,6 × rabattu), moins de feuilles.
- `pince` ∈ [0,1], retour à 0 en 12 semaines `[choix]` : hauteur × (1 − 0,15 × pince), rayon × (1 + 0,2 × pince), plus touffu. Le basilic pincé ramifie.

Le clic vise toute la plante, sans `target.segment` et sans surlignage de segment, repli serveur déjà en place. Les 4 de prairie en bénéficient : la limite D127 « taille armée sur trèfle » se ferme.

**Limite assumée** : la coupe est visible, mais `height_at` ne bouge pas : ombre et lumière de la plante restent celles de son stade, comme aujourd'hui.

### 4.5 Grammaire

Le brief s'applique, dialecte 3 (« chaque plante est une icône lisible à 3 ou 4 tons ») : motif estampillé plutôt que contour rempli, 3 à 5 tons, éclat côté soleil, ombre colorée, contour sélectif sur fleurs et fruits. Repris de D118 (B) : fleurs, spires du haricot, ovales vert uni et nervures grossières à ×32.

## 5. Philo de design

- **#1, #2** : aucun effet sur la simulation ; la coupe reste un geste coûteux, et son hint ne fait que la montrer.
- **#3** : zéro RNG, tout au hash de l'individu.
- **#5** : l'espèce se lit dans sa forme, sans étiquette ni chiffre.
- **Pas de nouvelle espèce** : pas de voix à écrire.

## 6. Mesure et perf

Le calibrage se valide par mesure, le F5 ne juge que le ressenti.

- **Banc** `planche_especes` : les 40 espèces adultes séparées.
- **`tools/mesure_silhouettes.py`** : masques des sprites (`mesure_da --ref`), comparés par paires.
- **Paire confondue** : mêmes proportions et même gabarit à 15 % près, recouvrement des masques > 0,7, et teinte moyenne ΔE OKLab < 0,05 `[choix, à recalibrer au ① sur la mesure « avant »]`.
- **Cible** : 0 paire confondue à ×4, au plus 3 à ×1 `[choix]`.
- **Effet en jeu** : captures de `full`, pas seulement du banc.
- **Hauteur dessinée** : `height_cm` à ±20 % par port `[choix]`.
- **`tools/mesure_da.py`** sur chaque port : tons, noir, contour, aplat.

Perf, à chaque tronçon sur `full`, `tools/perf_vm.sh` avant/après :

- draw calls constants ;
- FPS non dégradés ;
- durée de cuisson par plante ≤ +10 % ;
- boîtes de cuisson plus petites attendues, à mesurer (une violette ne réserve plus 85 cm d'atlas) ;
- recuisson seulement si ce qui est dessiné a changé (aujourd'hui `SetStructure` invalide à chaque appel).

Moteur : deux entiers par plante, écrits à la coupe. Tick inchangé attendu.

## 7. Hors périmètre

D118 réduite : encart météo, heatmap vent, mention des Options, ombres OFF par défaut, reliquats D112 (p)(q)(r)(s), scintillement de glace, rivière Est, perf ×32 et à-coups de zoom, D110 (c)(f).

Opportunité notée, non traitée : les segments de ces 33 espèces ne servent plus à l'écran, or ils pèsent 6 887 segments sur 7 258 [`full` an 2, seed 42, n=1 run, VM]. Les retirer du pont, voire du moteur, relève de D118 (D) et de la perf, et demande de revoir `sim/grimpe.py`, `diam_pondere` et la chute des arbustes.
