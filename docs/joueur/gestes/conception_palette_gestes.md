# CONCEPTION — PALETTE DE GESTES PERSONNALISABLE

> Figé le 2026-07-10 (`/conception`, après arbitrages D1→D11).
> Sprint : `sprints/joueur/gestes/sprint_palette_gestes/`. Découpage : 5 tronçons perf-first,
> vue Godot en dernier (règle projet). Golden : NEUTRE partout (état/données +
> gestes event-driven au-dessus du tick — le smoke n'invoque aucun geste).

## 1. Intention

Le joueur compose lui-même son **jeu d'outils à portée de main**, à la manière
d'une **palette de peinture** : une sélection choisie de gestes (et de
**combinaisons de gestes**), puisée dans un **catalogue de base** enrichi de
gestes **débloqués** par la pratique et le savoir.

Cela remplace l'accès actuel — touches `1..9` (qui ne couvrent que les 9
premiers des 24 gestes) + `Tab` cyclique + modificateurs `S`/`B`/`N` — devenu
ingérable au fil des sprints (le HUD debug reconnaît lui-même que « la liste
débordait »).

Ce sprint pose **le cadre d'accès et de déblocage** ET **implémente deux gestes
neufs** (bouture, greffe) qui incarnent la voie « déblocage par savoir ».

## 2. Ce qui existe (relevé à froid, 2026-07-10)

- **24 gestes** codés en dur dans `world/WorldView.Actions.cs` (`Gestes[]`),
  ordre calé sur la table `sim/actions/couts.COUTS`. Kinds de cible :
  `p` (plante) / `q` / `t` (tuile) / `m` (plot milieu) / `x` / `a` / `s` (structure) /
  `E` / `P` / `C` / `U` / `D` — dont deux **gestes à 2 temps** (`deplacer_pot`,
  `epandre` : saisir → poser).
- **AUCUN gating** aujourd'hui : les 24 gestes sont disponibles dès le départ.
- Dispatch moteur : `sim/actions/gestes.py` (+ `compost.py`, `conteneurs.py`,
  `supports.py`, `ruche.py`, `paillage.py`…), coûts via `couts.cout_action`.
- Maîtrise (D12) : `game_state["maitrise"][player]`, paliers 0..5 par objet
  (famille / concept / technique / outil). Débloque déjà terrain, magazine,
  carnet interprétatif, Vigueur max — **mais PAS de gestes** aujourd'hui.
- Corpus narratif des gestes : `sim/geste_corpus.py` (fiche 3 niveaux par geste).
- Acquis moteur réutilisables : `sim/clonal.py` (clone génétique exact →
  BOUTURE), `plants/genetics.species_compatible(a,b)` (même famille → gate
  GREFFE), `GENE_NAMES` (10 gènes, scindables aérien/racinaire).

## 3. Modèle arbitré (D1→D11)

### 3.1 Combinaisons = macros joueur (D1, D5)
Une combinaison est une **macro enregistrée par le joueur** = une **séquence de
gestes rejouée sur la MÊME cible/point** au clic (ex. planter → pailler →
arroser ICI). **Chaque sous-geste paie sa Vigueur** (philo #1 préservée : une
macro ne gomme pas l'usure de la solution facile). Écarté : le « pinceau balayé »
sur une zone (viderait la Vigueur d'un coup, gommerait l'usure du geste).

### 3.2 Déblocage hybride en CASCADE, toujours SOFT/diégétique (D2, D12)
Le déblocage n'est **pas une table plate** mais une **arborescence narrative**
en cascade — `outil → geste rudimentaire → palier → geste savant` — jamais un
gating dur type skill-tree (respecte philo #6). **Trois voies** :
- **(a) par connaissance / maîtrise** — un geste savant se **révèle au palier**
  du concept/technique concerné (éventuellement à une condition **COMPOSÉE** =
  plusieurs paliers en ET) ;
- **(b) par action réalisée** — faire ou poser X **ouvre** le geste Y (poser un
  bac ouvre composter/retourner ; poser une pile ouvre empiler_bois…) ;
- **(c) par découverte EXPÉRIMENTALE émergente** — le joueur **reproduit un
  phénomène écologique** et le geste correspondant s'ouvre parce qu'il en a la
  maîtrise pratique (méthode scientifique, philo #6 : observer → tenter →
  réussir → comprendre). Détecté par un **marqueur au ledger** (un événement
  écologique réussi), pas par une case cochée.

**Chaîne canonique (exemple Nico, D12)** — la taille et la bouture :
1. le **sécateur** (outil possédé/utilisé) débloque **`couper`** (geste
   rudimentaire, brut) ;
2. **couper une branche** (action réalisée, voie b) débloque **`tailler`**
   (geste fin, ciblé) ET ouvre le **palier de maîtrise « taille »** ;
3. **`tailler` niveau 2 ET `planter` niveau 2** (condition composée, voie a)
   débloquent **`bouturer`** — ou d'abord une **page secrète** qui enseigne la
   bouture (le déblocage transite par une voix narrative, lien
   `CONCEPTION_VOIX_NARRATIVES`) ;
4. **voie c en parallèle** : si le joueur **plante une branche taillée** et la
   **garde humide** jusqu'à ce qu'elle **s'enracine** spontanément, il débloque
   **`bouturer`** par la pratique — il a reproduit le phénomène.

`couper` est donc un **geste rudimentaire NEUF**, ancêtre de `tailler` (brut vs
savant). La table `GESTE_UNLOCK` (§3.3) doit supporter : conditions **simples**
(palier ≥ n / action faite), conditions **composées** (ET de paliers) et
conditions d'**événement écologique émergent** (marqueur au ledger). Un
déblocage peut avoir **plusieurs conditions alternatives** (OU) — bouturer
s'ouvre par la voie a OU la voie c.

### 3.3 État de déblocage côté Python, persisté (D3, D6)
`game_state["gestes_debloques"][player]` = ensemble de verbes ouverts, **par
avatar**, **persisté dans la save JSON** (comme maîtrise/encyclopédie). Une table
**data-driven** `GESTE_UNLOCK` décrit, pour chaque geste GATED, sa condition
d'ouverture (palier d'un objet maîtrise, OU action déclenchante). Un **hook
d'évaluation** (event-driven, hors tick) ouvre les gestes dont la condition est
remplie et émet une **notification diégétique**. La palette Godot **LIT**
l'ensemble exposé au snapshot. Périmètre = **vue + données/état Python légers**,
**aucune logique de simulation** → golden NEUTRE.

### 3.4 Set de BASE vs gestes GATED (D9)
- **BASE** (toujours dispo, calibrage F5 ajustable) : `planter`, `arroser`,
  `recolter`, `manger`, `tailler`, `ecraser`, `becher` (ameublir),
  `favoriser_auxiliaire`.
- **GATED** : taille (`couper` [geste rudimentaire NEUF, débloque par sécateur] →
  `tailler` [débloqué en coupant une branche]), compost (`poser_bac`/`poser_pile`/
  `composter`/`empiler_bois`/`retourner`/`epandre`), conteneurs (`poser_pot`/
  `poser_bac_culture`/`deplacer_pot`/`planter_conteneur`), supports (`poser_tuteur`/
  `poser_treillis`/`poser_pergola`/`palisser`), paillage (`pailler`/`broyer`),
  ruche (`poser_ruche`/`recolter_miel`), plus les gestes savants neufs `bouturer`,
  `greffer`.
- **Nuance** : `tailler` était BASE dans l'arbitrage initial (D9) mais passe GATED
  avec D12 (la chaîne sécateur→couper→tailler). `couper` = geste brut (coupe sans
  choisir la cible fine) ; `tailler` = geste savant (écimage/égourmandage ciblé au
  segment). Calibrage F5 ajustable.

### 3.5 Bouture (D7) — clone génétique
Geste `bouturer` **à 2 temps** (mère bouturable → plot cible). Réutilise le
modèle `sim/clonal.py` : le ramet naît **vecteur de gènes COPIÉ** de la mère
(pas de brassage sexué) + expression plastique héritée ; coût = **bouffée de
`stress_memory`** sur la mère (puise son énergie propre, philo #1/#2, jamais de
malus direct). Gate : flag d'espèce `bouturable` + mère assez mûre/vigoureuse.
Déterministe (philo #3). **Débloqué** (D12) par la **voie savoir** (condition
composée `tailler` niv. 2 ET `planter` niv. 2, éventuellement via page secrète)
**OU** par la **voie expérimentale émergente** — une branche taillée plantée et
maintenue humide qui **s'enracine spontanément** émet un marqueur au ledger qui
ouvre le geste. Les deux voies convergent vers le même geste (OU de conditions).

### 3.6 Greffe (D7, D8) — modèle aérien/racinaire
Geste `greffer` **à 2 temps** (greffon → porte-greffe). Gate =
`species_compatible` (même **famille** botanique). Le **porte-greffe** adopte la
`plant_class` + les **gènes AÉRIENS** du greffon (`hauteur`, `phenologie_florale`,
`resistance_pathogene`, et ce qui régit fleur/fruit) et **conserve ses gènes
RACINAIRES** (`tolerance_secheresse`, `tolerance_asphyxie`, `tolerance_ombre`,
`vigueur`) + son **établissement** (âge/racines → démarrage rapide). Ni RNG ni
malus direct. Débloqué par la voie savoir (palier greffe, ≥ bouture).

### 3.7 Palette UI (D10, D11)
- **Disposition : colonne verticale sur le bord GAUCHE** de l'écran, **une icône
  par geste** (pictogramme muet, philo #5 — pas de texte en HUD primaire).
- Remplace les touches `1..9` + `Tab`. Les slots sont **curables « façon paint »**
  (le joueur choisit quels gestes sont à portée). La palette **lit
  `gestes_debloques`** du snapshot : seuls les gestes ouverts apparaissent (les
  verrouillés masqués ou grisés — calibrage F5).
- **Layout persisté** : `game_state["palette"][player]` = slots curés + macros,
  par avatar, un seul save (règle projet).

## 4. Découpage en tronçons (perf-first, vue en dernier)

| # | Tronçon | Golden | Pont |
|---|---------|--------|------|
| ① | Déblocage (Python) : `gestes_debloques` + table `GESTE_UNLOCK` + hook + expo snapshot | NEUTRE | +bump (expo) |
| ② | Bouture (moteur + voix) : geste `bouturer`, flag `bouturable`, réutilise clonal | NEUTRE | +bump (route) |
| ③ | Greffe (moteur + voix) : geste `greffer`, gate `species_compatible`, aérien/racinaire | NEUTRE | +bump (route) |
| ④ | Palette UI (C#) : colonne gauche + icônes, lit `gestes_debloques`, câble tous les gestes | intact | — |
| ⑤ | Macros + persistance layout + banc d'observation F5 | intact | +bump (persist) |

**Golden partout NEUTRE/INTACT** : les ajouts moteur (①②③) sont de l'état, des
données et des gestes **event-driven au-dessus du tick** ; le smoke (2 tuiles ×
4 ans, succession spontanée pure) **n'invoque aucun geste** → son hash ne peut
pas bouger. Si le hash bouge, c'est un bug (fuite dans le tick) → on annule.

## 5. Invariants respectés

- **Philo #1/#2** : bouture/greffe passent par un état physiologique
  (`stress_memory`, établissement), jamais un bonus/malus direct sur la plante ;
  chaque sous-geste d'une macro paie sa Vigueur (usure préservée).
- **Philo #3** : bouture/greffe déterministes (hash, pas de RNG live).
- **Philo #5** : palette = icônes muettes, pas de chiffres en HUD primaire.
- **Philo #6** : déblocage SOFT/diégétique (notification, révélation par la
  pratique), jamais un skill-tree dur, pas de tutoriel imposé.
- **Interconnexion** : le déblocage relie les gestes à la maîtrise (D12), au
  compost/conteneurs/supports déjà en place ; bouture/greffe relient
  génétique ↔ catalogue ↔ voix narratives.
- **Voix narratives** : bouture et greffe reçoivent leurs fiches
  (`geste_corpus.py` + technique/concept carnet) — un geste sans sa voix est muet.

## 6. Coût perf

Négligeable. Couche vue/UX + état persisté ; le hook de déblocage est
**event-driven** (déclenché par un franchissement de palier ou une action, pas
par tick). Une macro = N appels de gestes séquencés côté pont, **aucun calcul de
simulation supplémentaire par tick**. Bouture/greffe sont event-driven comme
tous les gestes.
