# CONCEPTION — REFONTE DE L'ACCÈS AUX GESTES

> Figée le 2026-11-12 (`/conception`, arbitrages R1→R9 de Nico).
> Prolonge et corrige `conception_palette_gestes.md` (2026-07-10) et le §1 de
> `docs/joueur/interface/conception_retours_ui_fenetrage.md` (cases de la palette).
> Ferme D133 ; reprend D118 (b) (c) (d) (e).
> **Trois sprints enchaînés**, golden intact partout :
> `sprint_acces_gestes` → `sprint_palette_tiroir` → `sprint_icones_curseur`
> (tous sous `sprints/joueur/gestes/`).

## 1. Constat (audit au code, 2026-11-12)

### 1.1 Le déblocage tourne en rond
Point fixe calculé sur `GESTE_UNLOCK` + `GESTES_BASE` (`sim/actions/deblocage.py`),
les marqueurs d'outil de l'Atelier (`sim/outils.py`), `OBJETS_TOUCHES`
(`sim/actions/couts.py`) et les concepts que le tick fait découvrir (eau, lumière,
météo, pollinisation) : **20 gestes gatés sur 32 ne s'ouvrent jamais en jeu normal**.

Cause unique : une technique n'est découverte (palier 0 → 1) que par
`decouvrir_a_usage` (`tools/simserver/maitrise_pont.py`), c'est-à-dire en
réussissant un geste qui la touche. Or les gestes d'entrée de ces techniques
exigent `("maitrise", <technique>, 1)`. Poule et œuf. Le cas n'avait été levé que
pour le sécateur (Atelier, D82).

- **Jamais ouverts** : `poser_bac`, `poser_pile`, `composter`, `retourner`,
  `epandre`, `empiler_bois`, `pailler`, `broyer`, `poser_pot`, `poser_bac_culture`,
  `deplacer_pot`, `planter_conteneur`, `poser_tuteur`, `poser_treillis`,
  `poser_pergola`, `palisser`, `poser_perchoir` (D133), `greffer`, `poser_ruche`,
  `recolter_miel`.
- **Ouverts normalement** : `couper`, `tailler`, `bouturer`, `abattre`, `receper`,
  `eteter`, `endiguer`, `deriver`, `entailler`, `poser_voile`, `poser_cloche`,
  `poser_ombriere`.
- **Aggravant** : la lettre `lettre_bac_compost_odette` offre un bac, mais
  `composter` exige `("action", "poser_bac")` : le bac offert reste inutilisable.

### 1.2 Dix gestes du moteur n'existent pas dans la vue
`Gestes[]` (`world/WorldView.Actions.cs`) ignore : `poser_tuteur`, `poser_treillis`,
`poser_pergola`, `palisser` (aucune route au pont non plus) ; `poser_voile`,
`poser_cloche`, `poser_ombriere` (ouvrables, mais ni route ni palette) ;
`poser_ruche`, `recolter_miel` (route au pont, pas de palette). `grelinette` passe
par Maj + bêcher.

### 1.3 Ergonomie (retours F5 de Nico)
Trouver un geste est à refaire ; on ne sait pas qu'un geste existe ; les réglages
sont cachés derrière S (graine), B (substrat), N (paillis) ; les icônes
(`GesteIcon.cs`, couleurs brutes) sont hors DA ; le curseur ne dit pas quel geste
est en main. Plus D118 (b) : un geste choisi au clic droit n'est pas sélectionné ;
(c) : une plante contre la maison, c'est le hub qui prend le clic.

## 2. Décisions (R1→R9)

| # | Décision |
|---|---|
| R1 | Refonte complète : déblocage + organisation + icônes et curseur. Plusieurs sprints. |
| R2 | Chaque technique a **au moins une porte qui ne passe pas par ses propres gestes**. Quatre portes : Atelier, geste de base voisin, observation, **courrier**. |
| R3 | Tout l'accès est refait : trouver, savoir que ça existe, réglages visibles, icônes DA, curseur à l'icône du geste, **curseur animé à l'exécution**. |
| R4 | Gestes **pressentis** : silhouette + phrase d'ambiance. Jamais la piste explicite. |
| R5 | **Barre de favoris** (10 cases, touches 1 à 0) + **tiroir par familles** + réglages affichés près du geste choisi. **Ctrl+molette** fait défiler la barre (la molette seule reste le zoom). |
| R6 | Icônes **dessinées par le code**, pixel art, palette maître ; 3 à 4 images d'animation, partagées par famille. |
| R7 | Table des portes du §3.2 acceptée comme point de départ ; jugement de Nico après test. |
| R8 | Les **macros sortent de l'interface** (Nico ne s'en sert pas). Le code reste (`WorldView.Macros.cs`, `sim/actions/palette.py`), rien n'est supprimé ; les touches K et J sont débranchées. |
| R9 | Ctrl+molette = défilement de la barre ; à réévaluer au F5. |

## 3. Modèle du déblocage

### 3.1 Principe : une porte DÉCOUVRE la technique
On ne remplace pas `GESTE_UNLOCK` : sa grammaire (OU de conditions, `et`,
`maitrise`, `action`, `evenement`) est saine et les chaînes internes à une famille
(poser un bac ouvre composter, recéper ouvre étêter) restent. On ajoute l'étage qui
manquait : une table **`PORTES_TECHNIQUE`** — technique → liste de conditions
alternatives, même grammaire. Quand une porte est franchie, la technique est
**découverte** (palier 1, par `observer`), et les conditions
`("maitrise", <technique>, 1)` existantes deviennent vraies d'elles-mêmes.

Deux formes de condition neuves :
- `("stock", nature, seuil)` : le joueur a au moins `seuil` de ce mulch en stock ;
- `("compte", verbe, n)` : le joueur a réussi `n` fois ce geste (compteur d'état
  joueur, incrémenté au même endroit que `marquer_action`).

**Posséder vaut avoir posé** : une structure offerte (lettre) pose le même marqueur
d'action que le geste de pose (`poser_bac` pour le bac d'Odette).

**Garde-fou permanent** : un test (`tests/test_atteignabilite.py`) refait le point
fixe du §1.1 sur les tables réelles et échoue si un geste de `COUTS` n'est ni de
base ni atteignable. L'impasse ne peut plus revenir sans casser la suite.

### 3.2 Table des portes (point de départ, calibrage F5)

| Technique | Gestes | Portes |
|---|---|---|
| `compostage` | poser_bac, poser_pile, composter, retourner, epandre, empiler_bois | `("compte", "glaner", 3)` · lettre d'Odette (bac offert → marqueur `poser_bac` + technique) |
| `paillage` | pailler | `("stock", "feuilles", 1 dose)` — on a de quoi pailler |
| `broyage` | broyer | Atelier : broyeur (`posseder_broyeur`) ; `broyer` passe de `("maitrise","paillage",1)` à `("action","posseder_broyeur")` |
| `jardinage_hors_sol` | poser_pot, poser_bac_culture, deplacer_pot, planter_conteneur | Atelier : pots (`posseder_pots`) · une lettre |
| `palissage` | poser_tuteur, poser_treillis, poser_pergola, palisser | Atelier : tuteurs (`posseder_tuteurs`) · observation `grimpante_sans_appui` · lettre de Gaston |
| `perchoir` | poser_perchoir | observation `merle_seme` · `("action","poser_tuteur")` (existant) |
| `greffe` | greffer | lettre d'un voisin arboriculteur **et** greffoir à l'Atelier (`posseder_greffoir`) |
| `apiculture` | poser_ruche, recolter_miel | lettre (essaim offert) · `("maitrise","pollinisation",2)` |
| `protection-climatique` | poser_voile, poser_cloche, poser_ombriere | inchangé (`("maitrise","météo",1)`) · Atelier : voile (`posseder_voile`) |

Les techniques déjà ouvrables (taille, bouture, essartage, taillis, trogne,
terrassement) ne changent pas.

**Observations** (voie expérimentale, marqueurs posés au-dessus du tick, jamais
dans le tick) :
- `merle_seme` : le tick écrit déjà une ligne « 🐦 Merle : … » (`sim/zoochorie.py`) ;
  le hook d'observation du pont (`maitrise_pont._observer`) la lit et pose le marqueur.
- `grimpante_sans_appui` : le joueur survole une grimpante dont la tige pousse
  libre (`sim/grimpe.py`, `sim/growth/tige_libre.py`). Le point d'accroche exact
  est laissé au tronçon (survol `observer_espece` ou lecture de l'état post-tick).

### 3.3 Le courrier enseigne
Récompense neuve dans `sim/quetes.py` : `("technique", objet)` → `observer`
(palier 1) puis `evaluer_deblocages`. Une lettre peut aussi **porter une structure
et la technique** (Odette). Lettres neuves (texte dans la voix des voisins
existants : Marcel, Léa, Amélie, Bertrand, Gaston, Odette) : palissage (Gaston),
greffe, apiculture (essaim), pots. Chaque lettre garde un désir à combler ; la
technique est la récompense, jamais un don sans contrepartie.

### 3.4 Trois états : inconnu, pressenti, ouvert
`gestes_pressentis(game_state, player)` — **calculé, jamais stocké** — renvoie les
gestes fermés dont le joueur a entrevu l'existence :
- sa technique est découverte mais le geste est encore fermé (chaîne interne) ;
- ou un **indice** de sa technique est vrai (table `INDICES_TECHNIQUE`, même
  grammaire) : une lettre active en parle, l'outil a été vu à l'Atelier, un concept
  voisin est découvert (pollinisation → apiculture), un geste voisin a été fait une
  fois (glaner → compostage, bouturer → greffe).

Chaque technique porte **une phrase d'ambiance** (`PHRASE_PRESSENTI`, dans
`sim/geste_corpus.py` ou un module frère) : une voix intérieure à la première
personne, sans consigne (« Ces feuilles que je ramasse, il doit bien y avoir mieux
à en faire qu'un tas. »). Jamais « va à l'Atelier ».

Philo #6 : ce n'est pas un arbre de compétences. Rien n'apparaît avant que le
jardin, l'Atelier ou un voisin l'ait évoqué ; la phrase n'indique pas le chemin.

### 3.5 Familles
Table `FAMILLE_GESTE` côté Python (vérité unique, exposée au pont) — huit familles,
ordre d'affichage du tiroir :
1. **main** : recolter, manger, glaner, ecraser, favoriser_auxiliaire
2. **sol** : becher, grelinette, creuser, drainer, deraciner
3. **semis** : planter, bouturer, greffer, planter_conteneur
4. **taille** : pincer, arracher, couper, tailler
5. **eau** : arroser
6. **compost** : poser_bac, poser_pile, composter, retourner, epandre, empiler_bois, pailler, broyer
7. **structures** : poser_pot, poser_bac_culture, deplacer_pot, poser_tuteur, poser_treillis, poser_pergola, palisser, poser_perchoir, poser_voile, poser_cloche, poser_ombriere, poser_ruche, recolter_miel
8. **paysage** : abattre, receper, eteter, endiguer, deriver, entailler

Un test vérifie que chaque geste de `COUTS` a exactement une famille.

## 4. La palette (vue)

- **Barre de favoris** : les 10 cases actuelles (`_slots`, `PaletteLayout`),
  touches 1 à 9 puis 0, `Tab`, et **Ctrl+molette** pour faire défiler le geste actif.
- **Tiroir** : un panneau qui s'ouvre d'un bouton en bas de la barre (et d'une
  touche), rangé par familles. Il montre **tous** les gestes ouverts (icône pleine)
  et pressentis (silhouette). Clic gauche sur un geste ouvert : il devient le geste
  actif, sans exiger de case. Clic droit : menu « mettre en case n ». Survol d'un
  pressenti : la phrase d'ambiance. Les inconnus n'apparaissent pas.
- **Réglages contextuels** : quand le geste actif a un réglage, une rangée
  s'affiche à côté de la barre — graines disponibles pour `planter` et
  `planter_conteneur`, substrats pour `poser_pot`/`poser_bac_culture`, natures de
  mulch (avec stock) pour `pailler`. Clic pour choisir ; les touches S, B, N
  disparaissent.
- **D118 (b)** : choisir un geste dans un menu le sélectionne aussitôt.
- **D118 (c)** : la plante au premier plan passe avant le hub de la maison.
- **Macros** : K et J débranchées, code conservé (R8).
- **Notification** : un geste qui s'ouvre ou devient pressenti fait battre le
  bouton du tiroir (animation = signal, DA SNES).

## 5. Icônes et curseur (vue)

- **Icônes** : grilles de caractères cuites une fois en texture, comme la main de
  `WorldView.Curseur.cs`. 16×16 logiques, affichées ×2 ou ×3 (multiple entier),
  couleurs prises **dans la palette maître** (plus aucune couleur brute). Une icône
  par geste (45). La silhouette d'un pressenti = la même grille en une seule teinte
  sombre.
- **Curseur** : geste actif → le curseur système devient l'icône du geste
  (`Input.SetCustomMouseCursor`, point chaud sur la partie active de l'outil).
  Aucun geste → la main gantée actuelle.
- **Animation à l'exécution** : 3 à 4 images, jouées une fois quand le pont répond
  `applied` ; un **refus** joue un court « non » (secousse de 2 images), sans texte.
  Animations **par famille de mouvement**, pas par geste : verser (arroser),
  couper (pincer, couper, tailler, greffer, bouturer), frapper/creuser (bêcher,
  creuser, drainer, déraciner, entailler, abattre, recéper, étêter), poser (toutes
  les poses), ramasser (récolter, glaner, manger, récolter le miel), remuer
  (retourner, composter, épandre, pailler, broyer), écraser. Immobile hors action
  (animation = signal, jamais décor).
- **Vérification** : planche de toutes les icônes et de toutes les images
  d'animation au banc de capture VM (`tools/capture_vm.sh`), regardée avant F5.

## 6. Philosophie et coût

- **#1/#2** : aucun effet sur les plantes ; tout est état joueur et vue.
- **#3** : aucune part d'aléa ; les observations lisent le journal du tick.
- **#5** : icônes muettes ; la phrase d'ambiance n'apparaît qu'au survol.
- **#6** : pressenti sans consigne ; quatre portes diégétiques, pas d'arbre.
- **Interconnexion** : le déblocage relie gestes ↔ courrier ↔ Atelier ↔ faune
  (merle) ↔ grimpantes ↔ maîtrise.
- **Golden** : intact dans les trois sprints (état joueur opt-in, hooks au-dessus
  du tick, vue). S'il bouge, c'est une fuite dans le tick : on annule.
- **Perf** : nulle dans le tick. `evaluer_deblocages` et `gestes_pressentis` sont
  appelés aux événements (geste, lettre, palier) et au snapshot ; tables de
  quelques dizaines d'entrées.

## 7. Découpage

| Sprint | Tronçons | Pont |
|---|---|---|
| **① `sprint_acces_gestes`** | 01 portes + atteignabilité · 02 Atelier, courrier, observations · 03 pressentis, familles, routes au pont · 04 vue minimale + banc | bump au 03 |
| **② `sprint_palette_tiroir`** | 01 tiroir par familles · 02 réglages contextuels · 03 pressentis, Ctrl+molette, D118 (b)(c), macros débranchées, banc | — |
| **③ `sprint_icones_curseur`** | 01 moteur d'icônes + planche · 02 les 45 icônes · 03 curseur du geste · 04 animations d'exécution et de refus | — |

## 8. Hors périmètre (reste en dette)
- Calibrage des seuils des portes et des coûts d'Atelier : après F5.
- Textes d'encyclopédie des outils neufs au-delà de la fiche de base.
- DA des autres panneaux hors palette (D118 : `WorldView.Hud`, `SkyPanel`…).
