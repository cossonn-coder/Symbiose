# Brief DA Symbiose : la grammaire des plantes 16 bits

> **Source** : brief rédigé par Nico le 2026-10-29, gravé tel quel à la conception D112
> (sprint `sprints/rendu/pixelart/sprint_casse_ecran/`). C'est la **référence visuelle** de
> tous les tronçons de rendu. Les adaptations à Symbiose (iso 2:1, soleil réel, palette
> indexée…) vivent dans `conception_casse_ecran.md` §2 — ce fichier-ci ne se modifie pas.

Oct 29, 2026 · Nico

À lire avant de dessiner ou de générer le moindre sprite végétal : trois captures SNES donnent la grammaire visuelle à reproduire (construction, lumière, palette), jamais des sprites ou des personnages à recopier.

## L'essence en 8 règles

Une plante SNES se lit à deux distances : de loin, une masse de valeur (clair contre sombre) à la silhouette nette ; de près, un motif minuscule répété. Les huit règles suivantes produisent cette double lecture.

1. **Motif, pas contour.** Aucune plante n'est un contour rempli. C'est un petit motif (feuille 3×4 px, brin 1×4 px, grain 2×3 px) estampillé en grand nombre ; la silhouette naît de la répartition des tons.
2. **3 à 5 tons par matière.** Creux sombre, ton moyen, ton clair, éclat. L'éclat ne touche que le haut-gauche de chaque motif, sur 1 à 4 px.
3. **La teinte tourne avec la valeur.** Dans la canopée de jour, l'ombre est un vert bleuté (teinte ≈ 133°) et l'éclat un vert-jaune (≈ 78 à 87°). Éclaircir une seule teinte donne un rendu plat.
4. **L'ombre est colorée, jamais noire.** Le pixel le plus sombre mesuré est #071010, un vert-noir. La nuit, l'ombre est un bleu profond (de #071934 à #142c66).
5. **Chaud contre froid.** Nuit : or (#d1c342) sur bleu-violet. Jour : vert saturé sur brun chaud dans la clairière, olive doux et terne en forêt.
6. **Le sol est une texture, pas un aplat.** Deux à quatre tons voisins en bruit dithéré, avec des patchs plus clairs ou plus sombres alignés sur une grille de 16 px et au bord piqueté.
7. **Contour sélectif.** Les masses (canopée, buissons) n'ont aucun contour. Les petits objets (fleurs, pots, pierres) ont un trait fin d'une teinte plus sombre de leur propre couleur, jamais noir.
8. **Vue oblique, tri par Y.** Troncs vus de côté, canopée par-dessus, base du tronc en éventail de racines, halo d'ancrage sombre et dithéré sur le sol.

## Les trois références

Les trois captures sont trois dialectes du même langage. Symbiose n'en copie aucun : chacun sert un usage précis.

| Capture | Ambiance | Principe dominant | Usage proposé dans Symbiose |
| --- | --- | --- | --- |
| 1. Campement nocturne autour d'un feu (Chrono Trigger, 1193×676, ≈ 4,7 px écran par pixel logique) | Nuit, bleu profond, feu or | Lumière d'abord : masses sombres et liseré chaud sur les arêtes | Nuit, éclairages locaux, ombres teintées |
| 2. Combat en forêt (Chrono Trigger, 634×480, ≈ 2,5 px par pixel logique, image floue) | Jour, olive doux et terne | Texture d'abord : sol, herbe et buissons faits du même grain en chevrons | Prairies, couvert dense, succession pionnière |
| 3. Clairière fleurie (Secret of Mana, 677×585, ≈ 2,6 px par pixel logique) | Jour, vert saturé sur brun chaud | Objet d'abord : chaque plante est une icône lisible à 3 ou 4 tons | Construction de chaque espèce prise individuellement |

Répartition proposée, à valider : le dialecte 3 pour toute plante que le joueur doit reconnaître seule, le 2 pour les couvertures végétales denses, le 1 pour la nuit. Les huit règles ci-dessus valent pour les trois. *(Validée par Nico le 2026-10-29.)*

Les captures sont des agrandissements compressés : les valeurs hexadécimales plus bas sont des moyennes quantifiées, fiables à ±10 % environ. Les tailles en pixels logiques supposent une largeur d'origine de 256 px, soit une tuile de 16 px d'environ 75 px écran sur la capture 1 et 42 px sur la capture 3 (le pas des rosettes jaunes, mesuré, le confirme).

## Anatomie des plantes

Chaque plante se construit en cinq couches, dans cet ordre : silhouette, motif estampillé, rampe de tons, accent de lumière, ancrage au sol. Les recettes donnent ces cinq couches par type. Les tailles sont en pixels logiques, à ±20 % près.

### Arbre de jour (capture 3)

C'est le modèle de construction d'un arbre : trois blocs superposés, canopée, tronc, empattement.

- **Canopée.** Une nappe de feuilles individuelles, chacune un ovale pointu d'environ 3×4 px incliné à 45°. Au moins quatre orientations (verticale, ↗, →, ↘), mélangées sans régularité. Chaque feuille porte trois tons : ombre, moyen, éclat.
- **Profondeur.** Les interstices entre feuilles sont d'un vert très sombre (#115920, #124c20), jamais un fond uni. Compter environ une feuille éclatante pour trois ou quatre moyennes, avec plus de creux sombres vers le bas de la masse.
- **Bord bas.** Frange festonnée, presque horizontale, qui coupe le tronc net. Dans la capture, le haut de la canopée sort de l'écran : l'arbre est plus haut que la vue.
- **Tronc.** Rectangle brun d'environ 30 px de large, strié à la verticale, du ton sombre (#4f351a) au ton clair (≈ #a1774f). Les stries sont des suites de pixels verticaux sur 2 ou 3 tons, pas des lignes.
- **Empattement.** Quatre ou cinq racines en doigts qui s'écartent en éventail depuis la base (largeur totale ≈ 45 à 50 px, longueur 15 à 25 px). Dessus plus clair, dessous sombre, un trou d'ombre entre chaque doigt.
- **Lierre.** Quelques traits verts d'1 px, à petites feuilles de 2 px, suivent le relief du tronc et des racines en surimpression.
- **Ancrage.** Halo de sol plus sombre (#2c3c1e vers #537c44) autour de la base, bord dithéré, large de 1,5 à 2 fois le tronc.

### Arbre de nuit (capture 1)

Le volume tient presque entièrement au bord de la masse. L'intérieur reste vide.

- **Canopée.** Masse quasi noire (#071010 à #081110), sans aucun détail interne.
- **Liseré.** Une bande irrégulière de 6 à 8 px, faite de pixels or-olive (#b3a734, #867821, #58552d) mêlés en damier à du teal sombre (#0b2a33), puis 4 à 6 px de transition du teal vers le noir. Le contour extérieur est déchiqueté, en lobes de 6 à 10 px.
- **Troncs.** Fûts verticaux bleu nuit (#071f3f, #162950) avec des bandes gris-violet (#2e3856, #40414f, #725f4f). Un filet d'or d'1 à 2 px (#a18435, #d1c342) suit la courbure, côté lumière seulement.
- **Racines.** Nervures fines et courbes, dorées sur leur arête haute, bleues et sombres entre elles.

### Masse buissonnante (captures 2 et 3)

La forme vient d'un changement de valeur de deux ou trois crans, jamais d'une ligne.

- **Couvert olive (capture 2).** Pas de contour. La masse est faite du même grain en chevrons que le sol (2×3 px), en plus sombre et plus dense. Rampe : #302806 (creux), #454c10, #616225, #878c44, #aab164 (dessus éclairé). Le bord haut est le plus clair.
- **Buisson vif (capture 3).** Feuilles dentelées empilées en écailles, vert saturé : #3b662b, #527e42, #5f8f41, #9fc339.

### Touffe d'herbe (captures 2 et 1)

- **Jour (capture 2).** Trois à cinq grains elliptiques obliques (≈ 2×3 px), éclat en haut (#8ea04f, jusqu'à #a4b465) et ombre dessous (#455314), sur un fond #657731. Les grains se serrent en chevrons dans un bloc d'une à trois tuiles. Le bord est irrégulier parce qu'on retire des tuiles du bloc, pas parce qu'on le dessine.
- **Nuit (capture 1).** Aucun brin vert. Des traits d'1 à 2 px de large et 3 à 5 px de haut, légèrement inclinés, en or terne (#8b7a45) ou or éclairé (#d1bb46), par groupes de 6 à 12 sur le fond bleu. Les groupes s'espacent quand on s'éloigne du feu.

### Gazon et sol (captures 3, 2 et 1)

- **Capture 3.** Base #537c44 avec un bruit doux de deux ou trois tons voisins (#568943, #60804a, #698951). Patchs plus clairs (#7d9b4f) en rectangles multiples de 16 px, au bord dithéré ; sous les arbres, #2c3c1e. La terre est une tache ronde dithérée (#8e6b4a, #9c724d, #a1774f, #b28250), au bord piqueté de vert.
- **Capture 2.** Gazon en tissage diagonal olive (#434b11, #636222, #7d7736, #868f46), sans aplat.
- **Capture 1.** Sol bleu (#071934, #082553, #0b2a60, #142c66) avec un bruit vertical de 2 à 3 px de haut. Le halo du feu est fait de rayons dithérés d'or (#7e6331, #857735, #ae8429, #d1bb46, #f5e281) qui s'éteignent dans le bleu sur un rayon d'environ 45 px.

### Fleurs (captures 3 et 2)

Aucune fleur n'a de pétales détaillés : elles se lisent comme des taches de couleur pure posées sur du vert.

| Fleur | Construction | Taille | Tons |
| --- | --- | --- | --- |
| Épi jaune (capture 3) | Trois pétales en flamme, verticaux, sur deux feuilles vertes en V ; fin contour sombre | ≈ 14×13 px | #f4e559 éclat, #e5cf49 corps, ombre orangée sur le flanc droit ; feuilles #4d7237 et #5f8b4a |
| Trio de fleurs rondes (capture 3) | Trois fleurs rondes de 4 px, éclat jaune en haut-gauche, ombre orange en bas-droite, minuscule point central gris-vert, disposées en triangle sur quatre ou cinq feuilles pointues. Pas de 16 px en grille régulière, par blocs de 2×3 | ≈ 14×14 px | fleurs #f4e559 et #e5cf49 ; feuilles #4a7237 (ombre), #5c824b, #89a84d (éclat) |
| Confettis (capture 2) | Points de 2 à 3 px, magenta vif ou violet, sans forme de pétale, espacés de 5 à 6 px en quinconce lâche sur une herbe claire. Un patch = une tuile environ | 12 à 20 px, 8 à 20 points | magenta #d72dcd (moyenne mesurée), violet, vert clair autour |
| Pot fleuri (capture 3) | Pot de terre cuite rond garni de petits points jaunes, contour sombre. Objet posé sur le sol, à traiter comme un plant cultivé | ≈ 16 px | pot #a77a51, #a06a5d, #6e4e4e |

La nuit (capture 1) ne montre aucune fleur colorée : seulement de l'or.

### Grimpantes et mousse (capture 3)

- **Lierre.** Traits verts d'1 px à petites feuilles de 2 px qui suivent le relief du tronc et des racines. C'est une couche séparée, posée sur l'hôte, qui ne masque jamais sa matière.
- **Mousse.** Patchs vert sombre, au bord dithéré, autour des racines et au pied du tronc.

### Pierres et décor minéral (capture 3)

- **Rochers.** Ovales gris de 10 à 14 px : trois tons et un éclat en haut-gauche, une ombre sous le bord bas, aucun contour noir. Posés sur un patch d'herbe plus claire.
- **Boules crème (#c7c797).** Groupes de trois à cinq : une grande d'environ 14 px et des petites d'environ 5 px, à deux tons (crème, gris pâle) avec quelques taches vertes. Leur nature est ambiguë (cailloux ou touffes cotonneuses) : les traiter comme décor, pas comme plante.

## Palettes mesurées

Chaque matière tient en 3 à 6 tons, du plus sombre au plus clair. Valeurs quantifiées sur les captures, à ±10 % près ; la capture 2 est floue, ses valeurs sont les moins fiables.

| Matière | Rampe (sombre vers clair) | Capture |
| --- | --- | --- |
| Canopée de jour | #115920 · #1f691e · #2f821e · #4fb023 · #81d51b · éclat isolé #b0f800 | 3 |
| Tronc et racines | #4f351a · #5e3e26 · #745238 · #a1774f | 3 |
| Gazon | #2c3c1e · #537c44 · #568943 · #60804a · #7d9b4f | 3 |
| Terre | #8e6b4a · #9c724d · #a1774f · #b28250 | 3 |
| Buisson vif | #3b662b · #527e42 · #5f8f41 · #9fc339 | 3 |
| Fleur jaune | feuilles #4a7237 · #5c824b · fleur #e5cf49 · #f4e559 | 3 |
| Décor crème | #c7c797 | 3 |
| Gazon et couvert olive | #302806 · #454c10 · #636222 · #7d7736 · #868f46 · #b0ae63 | 2 |
| Touffe claire | #455314 · #576824 · #657731 · #8ea04f | 2 |
| Confettis de fleurs | magenta #d72dcd, violet, vert clair | 2 |
| Canopée de nuit | noir #071010 · #081110 · teal #0b2a33 · #58552d · #867821 · #b3a734 | 1 |
| Troncs de nuit | #071f3f · #162950 · #2e3856 · #40414f · #725f4f · #a18435 · #d1c342 | 1 |
| Sol de nuit | #071934 · #082553 · #0b2a60 · #142c66 | 1 |
| Brins d'herbe de nuit | #8b7a45 · #d1bb46 | 1 |
| Halo du feu | #7e6331 · #857735 · #ae8429 · #d1bb46 · #f5e281 | 1 |

La rampe de la canopée de jour montre le décalage de teinte : #115920 est à 133°, #2f821e à 110°, #81d51b à 87°, #b0f800 à 78°. Reproduire ce mouvement vers le jaune dans les clairs et vers le bleu-vert dans les ombres.

## Règles transversales

- **Échelle.** Travailler en pixels logiques, sur une largeur de 256 px et une tuile de 16 px. Une plante isolée occupe une à trois tuiles ; un arbre en occupe plusieurs (tronc ≈ 30 px, empattement ≈ 48 px).
- **Lumière.** Le jour, source en haut-gauche : éclat sur le bord haut-gauche de chaque motif, ombre en bas-droite. Pas de longue ombre portée : l'ancrage se fait par un halo sombre au pied. La nuit, un liseré chaud sur les seuls bords tournés vers la source.
- **Nuit et jour.** La nuit n'est pas la palette du jour assombrie : c'est une autre rampe, bleue et or (capture 1). Changer de rampe entre jour et nuit, ne pas poser un voile noir.
- **Dithering.** Trois usages distincts, à ne pas mélanger : damier à 50 % sur 4 à 6 px pour les transitions de bord (capture 1) ; tissage diagonal en chevrons pour les textures de sol (capture 2) ; bruit aléatoire doux sur 2 ou 3 tons pour le gazon (capture 3). Jamais de dégradé lisse ni de lissage.
- **Contour.** Aucun sur les masses. Sur les petits objets, une teinte plus sombre de l'objet lui-même.
- **Grille.** Les patchs de sol, les blocs de touffes et les grilles de fleurs sont des multiples de 16 px. L'irrégularité vient des tuiles retirées et du bord dithéré, pas de courbes tracées.
- **Ordre de dessin.** Tri par Y. La canopée recouvre le tronc et tout ce qui passe derrière.
- **Variation.** Deux individus d'une même espèce diffèrent par l'orientation des motifs et par les tuiles retirées, jamais par un changement de rampe.
- **Discipline de palette.** La SNES limite chaque objet à une sous-palette de 16 couleurs, transparence comprise. Les rampes ci-dessus y tiennent une à une. Garder cette limite comme discipline, pas comme règle stricte.

## Application à Symbiose

Une espèce est une recette, pas un dessin : une rampe, un motif, un squelette, un accent, un ancrage. Variation et croissance passent par ces paramètres.

1. **Fiche de recette par espèce.** Rampe de 3 à 5 tons (hex), motif (forme, taille, orientations), squelette (tronc, tige, rosette, touffe), accent (fleur, liseré, lierre), ancrage (halo, mousse).
2. **Ordre de génération d'un sprite.** a) Blob de silhouette sur la grille. b) Estampillage du motif de haut en bas, en alternant les orientations. c) Éclat en haut-gauche sur chaque motif. d) Creux sombres dans les interstices. e) Contour sélectif pour les petits objets. f) Halo d'ancrage dithéré.
3. **Croissance.** Une plante jeune porte moins de motifs estampillés, sur la même rampe. Seule l'espèce change de rampe.
4. **Grimpantes.** Les dessiner comme une couche séparée posée sur le sprite de l'hôte, sur le modèle du lierre de la capture 3.
5. **Rendu Godot.** Filtre Nearest, mipmaps coupés, zoom entier uniquement, aucune rotation de sprite.

### Interdits

- Un aplat uni à l'intérieur d'une masse (canopée, buisson, gazon).
- Le noir pur (#000000) ou une ombre noire semi-transparente.
- Un contour noir.
- Un dégradé lisse, du lissage, une rotation ou une échelle non entière.
- Plus de cinq tons par matière (six avec un éclat isolé).
- Recopier un sprite, un personnage ou une scène des jeux de référence : on reprend la grammaire, jamais les dessins.

### Checklist avant de valider un sprite

- [ ] À 1:1 puis à l'échelle entière, sans lissage, la texture reste nette.
- [ ] En silhouette floue, l'espèce reste reconnaissable parmi les autres.
- [ ] Cinq tons au plus par matière.
- [ ] La teinte dérive : ombres vers le bleu-vert, éclats vers le jaune.
- [ ] L'éclat est en haut-gauche sur tous les motifs.
- [ ] Aucun contour noir, aucun aplat.
- [ ] Le pied est ancré (halo, racines).
- [ ] Deux individus côte à côte ne sont pas identiques.
