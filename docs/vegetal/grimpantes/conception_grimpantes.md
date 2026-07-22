# CONCEPTION — Plantes grimpantes (mécanique de grimpe, couche A)

> **Statut : FIGÉ 2026-07-03** (`/conception`, dette **D49**). Volet A seul :
> la GRIMPE. Le volet B (rampantes/traçantes clonales) est **hors périmètre**
> → dette **D62**. Source de vérité = Python (`data/code/`). La vue Godot est
> le tronçon ⑥ de ce même sprint (couche A d'abord, puis rendu).

## §0 — Le problème et le piège à éviter

Une plante grimpante n'investit pas dans du bois autoportant : elle fabrique
une **tige longue et souple** et s'appuie sur autrui pour atteindre la lumière.
Aujourd'hui la strate `"grimpante"` du moteur n'est qu'une **empreinte**
(hauteur 150, `empreintes.py:63`) — aucune mécanique de grimpe.

**Piège philo #2 (interdit) :** écrire « support → +hauteur » est un bonus
direct. La hauteur atteinte doit **émerger d'une géométrie**, jamais d'une règle
qui récompense.

## §1 — Ancrage dans le code réel (vérifié en phase A)

1. **Le haricot (`Bean`) est déjà procédural** (`procedural_growth=True`,
   Fabaceae). Sa hauteur = `footprint_value("height")` = **max(z) des extrémités
   de segments** (`base/instance.py:176-204`) ; sa canopée = extension
   horizontale max. → **il n'existe aucun « scalaire de longueur » à réutiliser**
   (le brief initial le supposait) : la géométrie par segment *est* le modèle.
2. **L'apex a déjà un plancher de verticalité** `MIN_APEX_Z` (0.30) dans
   `_phototropic_bias` (`growth/geometrie.py:88-115`) : si la composante z de la
   direction tombe sous le plancher, l'apex est redressé « jamais à plat ».
   → **c'est le hook exact** de la grimpe : moduler ce plancher selon le support.
3. **`current_height` est lu par plusieurs consommateurs** hors lumière :
   nécromasse d'abscission (`engine/decompo.py:85`), nécromasse + `establishment`
   de perturbation (`effects/perturbations.py:34,382`), abri faune
   (`fields/abri.py:64`), occupation de pot (`container.py:209`), pont.
   → une « hauteur effective » qui **diverge** de la biomasse réelle fausse tous
   ces consommateurs (une grimpante affalée a une grande biomasse mais une
   faible hauteur debout). **On refuse donc tout clamp** : la hauteur reste
   honnête, on **façonne la vraie géométrie**.
4. **`StakeSlot` (`world/tile.py:18-56`) n'est PAS un tuteur de grimpe** : c'est
   le porte-**rondelles** du jeu de plateau (0-9 tiges × 3 rondelles homogènes).
   Aucune position, aucune hauteur. La phrase de D49 « 10 tuteurs/tuile » est une
   **erreur d'inventaire**. Les tuteurs/treillis/pergolas sont des **structures
   NEUVES** (position + hauteur), à modeler comme les bac/pile posables.
5. **Mur maison** : existe (`world/building.py:31-32`, hauteur 600, `wall_albedo`
   0.35 = effet espalier). Support réel et gratuit.
6. **Golden** : `Bean` est semé en (4,2) (`tests/test_golden.py:76`) → toute
   modif de sa croissance re-fige. `Sunflower` en (0,1) est **hors du rayon
   d'accroche** de Bean → aucune accroche vivante ne se déclenche dans le golden.

## §2 — Modèle géométrique de la hauteur (décision A)

Deux nouveaux traits sur `PlantBase` (défauts **inertes** → non-grimpantes
inchangées, golden neutre pour elles) :

| trait | type | défaut | sens |
|-------|------|--------|------|
| `hauteur_autoportante` | `float\|None` | `None` | cm que la tige tient SANS appui. `None` = non-grimpante (mécanique inerte). |
| `mode_grimpe` | `str\|None` | `None` | `None`/`crampon`/`vrille_volubile`/`sarmenteux`. |

État par instance (`PlantInstance`) : `support` — persistant, l'accroche n'est
**pas recalculée** chaque tick (perf). Valeurs : `None` (libre) / une référence
de support (structure, mur, ou plante-hôte) + sa hauteur d'appui.

**Loi d'apex** (dans la croissance, réutilise `_phototropic_bias`/`MIN_APEX_Z`) :

- **Non-grimpante** (`mode_grimpe is None`) → comportement actuel INCHANGÉ.
- **Grimpante libre, sous `hauteur_autoportante`** → comportement normal (elle se
  tient droite tant qu'elle est courte).
- **Grimpante libre, au-dessus de `hauteur_autoportante`** → le **plancher de
  verticalité s'effondre** : l'apex perd sa composante z (biais gravitaire vers
  le bas, `z → ~0` voire négatif). Émergent : `max_z` plafonne autour de
  `hauteur_autoportante`, `max_horiz` grossit → **port affalé/étalé**, canopée
  basse, la plante se fait ombrager. Rien n'est « puni » : elle a juste raté un
  appui.
- **Grimpante accrochée à un support de hauteur `H`** → biais d'apex **vers
  l'axe vertical du support** (plancher de verticalité renforcé), tant que
  `max_z < min(H, capacité_propre)`. Émergent : elle grimpe le long du support
  jusqu'à son sommet → hauteur effective élevée → accès lumière → photosynthèse.

`height_at` reste **exactement** `max(z)` de la structure : jamais de clamp,
jamais de divergence. Tous les consommateurs de `current_height` restent justes.

## §3 — Modes d'accroche (`mode_grimpe`)

Ce qui diffère mécaniquement = **quels supports sont valides**, pas la physique
fine de la vrille (esthétique = couche B / rendu ⑥).

| mode | plantes | support requis |
|------|---------|----------------|
| `crampon` | LIERRE | s'agrippe à toute surface : **mur nu** OK (espalier), tuteur/treillis/pergola OK, tronc d'hôte OK |
| `vrille_volubile` | HARICOT, + futures courge/kiwi/vigne/akébia/glycine | support **fin** : tuteur/treillis/pergola/tige d'hôte OK ; **mur nu inaccessible** (sans treillis) |
| `sarmenteux` | JASMIN | ne s'accroche pas seul → exige le geste **`palisser`** (④) sur un support adjacent |

## §4 — Supports (décision A2, panoplie complète)

**Structure posable NEUVE** `Support` (nouveau `world/support.py`, patron des
bac/pile posables) : `type` ∈ {`tuteur`,`treillis`,`pergola`}, position
(`x_cm,y_cm`), `height_cm`, rattachée à la tuile. Placeholders calibrage :

| support | height_cm | finesse | note |
|---------|-----------|---------|------|
| tuteur  | ~200 | fin | pieu unique |
| treillis | ~200 | fin + surface | grille verticale, tous modes |
| pergola | ~250 | surface haute | **projette de l'ombre** dans le `LightField` (occulteur, comme une canopée) ; une grimpante à son sommet contribue à cette ombre — rétroaction lumière normale |
| **mur maison** | 600 | surface | existe (`building.py`), `crampon` direct (espalier), `sarmenteux` via `palisser` |
| **plante-hôte** | = hauteur de l'hôte | tige | §5 |

**Compatibilité** = table `mode_grimpe × type_support` (helper pur, testable) :
`crampon` accepte tout ; `vrille_volubile` refuse le mur nu ; `sarmenteux`
n'accepte QUE par `palisser`.

**Recherche d'accroche (② — seul coût perf récurrent)** : uniquement pour les
grimpantes **libres et au-dessus de `hauteur_autoportante`** ; rayon **borné**
(plot-foyer + 8 voisins, ~50 cm) ; on retient le support compatible **le plus
proche**, départage **déterministe** (distance puis `id` — zéro RNG, philo #3).
L'accroche est un **état persistant** → plus de recherche ensuite. Ordre de
grandeur ~quelques centaines de tests/tick vs ~160 k ops du `LightField` →
négligeable (réflexe D32 : élaguer, ne pas balayer).

## §5 — Plante-hôte vivante comme support (③)

Une grimpante libre peut s'accrocher à une **plante voisine plus haute** de tige
compatible (crampon : tronc ; vrille_volubile : tige) à portée. Alors :

- **Hauteur d'appui = hauteur courante de l'hôte** (relue chaque tick, l'hôte
  grandit → la grimpante **suit**, émergent).
- **L'hôte meurt** (`health=0` / retiré) → **détachement** : la grimpante
  redevient libre (retombe, ou cherche un autre support).
- **Étranglement (émergent, PAS de règle dédiée)** : une fois haute, la canopée
  de la grimpante (à ~sa position, proche de l'hôte) projette son ombre **normale**
  dans le `LightField`, qui tombe sur l'hôte plus bas → une grimpante vigoureuse
  peut **ombrager son propre tuteur vivant** jusqu'au déclin. Le tri
  hauteur-décroissante du `LightField` (auto-ombrage exclu, `light.py:164`) traite
  bien deux plantes distinctes. C'est de l'émergence pure (#2), et ça préfigure
  la compétition de D62.
- **Mutualisme gratuit** : haricot (Fabaceae, fixe N) sur une haute (tournesol)
  = « trois sœurs » émergentes, **sans** règle de compagnonnage.

## §6 — Gestes joueur & maîtrise (④)

Event-driven (`sim/actions.py`, hors tick) → **golden intact**.

- `poser_tuteur` / `poser_treillis` / `poser_pergola` : déposent un `Support` au
  plot ciblé, phase planification, coût via `cout_action` (`MODÉRÉ`).
- `palisser` : attache **manuellement** une grimpante `sarmenteux` (jasmin) à un
  support adjacent (c'est ce dont ce mode a besoin). Coût `MODÉRÉ`.
- **Maîtrise** (D12) : objets déclarés — outil `tuteur`, technique `palissage`
  (patron des objets outil/technique existants). Non câblés au tick.
- **Verse/vent** (D37) : une grimpante **accrochée** résiste à la verse (le
  support la porte) ; libre, elle est déjà prostrée. Le tuteur **ne casse pas**
  sous la grimpante (écarté, simplicité).

## §7 — Catalogue (décision A3, démo réduite)

Ce sprint prouve la mécanique sur **3 espèces couvrant les 3 modes** ; le reste
part en **D26** (courge, kiwi, vigne, akébia, glycine — chacune avec ses 5 voix).

| espèce | famille (NEUVE ?) | mode | notes |
|--------|-------------------|------|-------|
| **Haricot** | Fabaceae (existe) | `vrille_volubile` | déjà au catalogue, `hauteur_autoportante`~35 ; démonstrateur coût 0 |
| **Lierre** (`Hedera`) | Araliaceae (**neuve**) | `crampon` | pérenne sempervirent, sciaphile, monte au mur nu |
| **Jasmin** (`Jasminum`) | Oleaceae (**neuve**) | `sarmenteux` | démontre `palisser` |

Chaque espèce NEUVE = **5 voix** (encyclopédie 3 niveaux, carnet via
`CONCEPT_DE`, page secrète si lore, magazine famille, marqueurs d'événements) +
extension `SOIL_SIGNATURE` de la nouvelle famille (D26 patron).

## §8 — Découpage (6 tronçons perf-first) & golden

| # | contenu | golden |
|---|---------|--------|
| ① | traits + état `support` + **affalement** géométrique sans support (loi d'apex) | **RE-FIGÉ maîtrisé** : le haricot s'affale (`growth_factor`/`shade_memory`) — `a6c2f651…` → nouveau hash **annoncé** |
| ② | `Support` posable (tuteur/treillis/pergola) + mur + recherche d'accroche bornée + biais de grimpe | NEUTRE vs ① (haricot=vrille_volubile, mur nu refusé ; aucun tuteur posé dans le golden) |
| ③ | plante-hôte vivante + détachement à la mort + étranglement émergent | NEUTRE (Bean(4,2) : aucune haute à portée — vérifié §1.6) |
| ④ | gestes `poser_*` + `palisser` + maîtrise (outil/technique) + résistance verse | INTACT (event-driven, hors tick) |
| ⑤ | catalogue lierre + jasmin + 5 voix + `SOIL_SIGNATURE` | NEUTRE (non semées dans le golden) |
| ⑥ | **vue Godot** : rendu supports + accroche + vrilles (`CONCEPTION_RENDU_FEUILLAGE §7/E6`) + pont (supports au snapshot, bump `ENGINE_VERSION`) | INTACT (vue pure) |

**Bonus de la décision A pour la vue** : comme la hauteur émerge de la vraie
géométrie des segments, une grimpante qui grimpe a déjà ses segments **montés le
long du support dans le snapshot**, et une affalée a ses segments **au sol** —
`PlantRenderer` les dessine correctement **sans code spécifique**. Le tronçon ⑥
n'ajoute que : le rendu des **structures-support**, un indice d'**accroche**, et
le détail esthétique des **vrilles**.

## §10 — Banc d'essai d'observation `grimpantes` (demande Nico 2026-07-03)

Pour **observer** la grimpe au F5 sans dérouler des années, on ajoute un **banc
d'essai** `grimpantes` au registre `BANCS` (paquet `bancs/`, patron `base.py`).
Un banc est un monde d'observation paramétré qui **ne touche JAMAIS le golden**
(jamais monté pour `smoke`/`full`). Composition demandée :

- **Haricot planté juste à côté d'un tournesol** → exerce directement l'accroche
  sur **plante-hôte vivante** (③) : le haricot grimpe le tournesol, le suit, puis
  peut l'ombrager (étranglement émergent). C'est LA démonstration visuelle du ③.
- **Champ de Solanaceae au sud** : tuile plantée de **tomates + basilic +
  poivrons** côté sud (grand `origin_y_cm`) — secteur ensoleillé/chaud (espalier
  du mur sud), conditions favorables aux frileuses (`t_germ_opt` élevé).
- **Départ début printemps** : **automatique** — `cmd_init` pose `week=1`,
  `week_in_year=((week-1)%52)+1=1`, et `SAISONS["printemps"]=range(1,14)` →
  wiy 1 = **début du printemps**. Aucun mécanisme neuf requis.
- Ajouter lierre (mur) + jasmin (palissé) au banc **après** le tronçon ⑤ pour
  montrer les 3 modes ; le cœur (haricot↑tournesol + champ sud) marche dès ③.

Le banc est monté au **tronçon ⑥** (instrument d'observation F5). Golden NEUTRE
(les bancs ne sont jamais montés pour `smoke`/`full`).

## §9 — Ce que ce sprint ne fait PAS
- Pas de rampantes/traçantes clonales (stolons/rhizomes/drageons) → **D62**.
- Pas de clamp/divergence sur `height_at` (§1.3).
- Pas de réutilisation de `StakeSlot` (§1.4).
- Pas les 7 espèces complètes (glycine/courge/kiwi/vigne/akébia → **D26**).
- Pas de casse de tuteur en tempête (§6).
