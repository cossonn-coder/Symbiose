# Dette D30 — Champ « structure / compaction du sol » (bonus d'aération)

> **Kickoff autosuffisant.** Démarrage à froid : lis ce fichier en entier, puis les
> sources citées, puis exécute. Français + pédagogie (Nico : C/Python embarqué +
> simulation, expert ; débutant Godot/C#). **Conception légère AVANT code** : ce
> sprint tranche d'abord **un** choix de design (le champ support), puis pose un
> bonus écologique minimal. Ampleur **petite**.

## Ce que c'est, en une phrase
Donner un **support moteur au bénéfice d'aération du sol** (décompactage par la
grelinette, infiltration, brassage) — aujourd'hui le **malus** du bêchage existe
(il tape `microbiome` + `vers_de_terre`) mais le **bonus** symétrique de la
grelinette **n'a aucun champ où s'inscrire** : `grelinette` est livrée en « jumeau
qui préserve » (no-op écolo). On ferme l'asymétrie.

## L'état du moteur aujourd'hui (vérifié)
- `sim/actions.py` a déjà les **deux gestes** (livrés au sprint D31.3, 2026-06-04) :
  - `becher` (coût `FAIBLE`) : ↓ `vers_de_terre` d'un quantum + ↓ `microbiome` de
    `BECHAGE_MICROBIOME_MALUS` (= 0.5). Le « fausse bonne idée » : effet immédiat,
    dette biologique différée.
  - `grelinette` (coût `MODÉRÉ`) : **no-op écologique** aujourd'hui — elle ne fait
    que coûter de la Vigueur. Le commentaire dans le code dit « aération → D30 ».
- Les champs de sol vivent dans `fields/ecofields.py` (`EcoFields`) : `humidite`,
  `fertilite`, `microbiome`, `soil_memory`/`_fast`/`_deep`, `om_fresh/active/stable`,
  et **`vers_de_terre`** (champ de population, ajouté à D31). Tous sont des
  `GridField` (432 plots) diffusés/tickés chaque semaine.
- `vers_de_terre` fournit **déjà** un couplage minimal : bioturbation → léger bonus
  de décomposition/minéralisation (`WORM_DECOMP_BONUS`, câblé à D31.2).
- Spec de référence : `data/code/CONCEPTION_VIGUEUR.md` **§3.6** (couple
  biner/grelinette, tableau des gestes de sol) et **§ « champ structure/compaction »**
  (~l.231) qui pose explicitement la question ci-dessous.

## 🔵 Choix de design à trancher (LE point du sprint)
La spec Vigueur laisse **un seul vrai choix ouvert** : *par quel champ passe le
bonus d'aération ?* Deux options propres, plus une mixte.

### Option A — Amplifier `vers_de_terre` (réutiliser l'existant) — ⭐ recommandé
La grelinette **booste la population de vers** (sol aéré = habitat favorable), et le
bénéfice agronomique transite par le couplage `vers_de_terre → décomposition` qui
**existe déjà** (`WORM_DECOMP_BONUS`). Le bêchage fait l'inverse (il tue des vers,
déjà codé).
- **Pour** : zéro nouveau champ, zéro nouvelle voie dans le tick, **golden facile à
  re-figer** (un seul levier bouge). Écologiquement honnête : l'aération *est* en
  grande partie un service rendu par la faune du sol. Symétrie pédagogique parfaite
  (bêcher ↓ vers, grelinette ↑ vers → le joueur lit la même jauge).
- **Contre** : confle « structure physique » et « biologie » en une seule variable.
  L'infiltration d'eau (un effet *physique*, pas biologique) reste non modélisée.

### Option B — Champ dédié `structure_sol` (neuf)
Un `GridField` `structure_sol ∈ [0,1]` (0 = compacté, 1 = grumeleux/aéré). Grelinette
↑, bêchage ↑ court puis ↓ (re-tassement), racines ↑ lentement, pluie battante ↓.
Il module l'**infiltration** (couple à `humidite`) et l'**uptake racinaire**.
- **Pour** : modèle le plus fidèle ; sépare physique et biologie ; ouvre des
  mécaniques futures (semelle de labour, paillage, plantes décompactantes type
  radis/luzerne — tu as déjà `MedicagoLupulina`).
- **Contre** : **nouvelle voie dans le tick** → re-figeage golden plus large, plus
  de calibrage, plus de surface de bug. Surdimensionné si l'aération n'est qu'un
  détail de gameplay pour l'instant.

### Option C — Proxy via `humidite` (infiltration seule)
La grelinette améliore l'infiltration → modélisée comme un léger gain de rétention
sur `humidite`. **Pour** : minuscule. **Contre** : sémantiquement faux (l'aération
n'est pas de l'humidité), et `humidite` est déjà très sollicité — risque d'effets de
bord. **Déconseillé** sauf si tu veux le strict minimum.

> **Ma recommandation : Option A.** Elle respecte la philo #2 (flux → réponse
> biologique émergente, jamais de bonus direct sur la plante : ici le bonus passe
> par les vers, pas par la plante), elle est golden-douce, et elle boucle le couple
> bêcher/grelinette que tu as déjà à moitié posé. **Garde l'Option B en backlog** :
> si un jour tu veux l'infiltration physique / les plantes décompactantes, ce sera
> le moment d'introduire `structure_sol`. Décision = la tienne.

## Périmètre (sous Option A — à adapter si tu choisis B/C)
1. **Conception** : une courte section dans `CONCEPTION_VIGUEUR.md` (ou un
   `CONCEPTION_SOL_STRUCTURE.md` si tu préfères isoler) qui acte le choix et le
   mécanisme : *grelinette → +quantum `vers_de_terre` (habitat favorisé) ; le
   bénéfice agronomique passe par `WORM_DECOMP_BONUS` existant.*
2. **Impl. minimale** dans `sim/actions.py::grelinette` : ajouter le **bonus
   symétrique** du malus de `becher` — un `+quantum` sur `vers_de_terre`
   (constante `GRELINETTE_VERS_BONUS`, défaut sobre, à calibrer). Rien d'autre :
   pas de nouvelle voie de tick, le couplage `vers→décompo` fait le reste.
3. **Golden** : `grelinette` est **event-driven, hors tick** (geste joueur), comme
   tous les gestes Vigueur → **golden écolo INTACT** (`6369c30b…` engine,
   `b005d9ba…` pop), à **vérifier inchangés**. Le test à étendre est le golden
   **joueur** (`tests/test_vigueur.py`) : un cas « grelinette ↑ vers / bêchage ↓
   vers » sur le même plot, contraste prouvé.

## Hors périmètre
Le **système complet** structure/infiltration/horizons (= Option B élargie),
plantes décompactantes, semelle de labour, portage C# (→ D24). Si tu choisis A,
tout ça reste explicitement en backlog.

## Vérification (success criteria)
```
cd data/code
python3 -m tests.test_vigueur     # étendu (contraste grelinette↑ / bêchage↓ sur vers) — passe
python3 -m tests.test_golden      # INCHANGÉ (6369c30b…) — geste hors tick
python3 -m tests.test_population  # INCHANGÉ (b005d9ba…)
python3 main.py                   # tourne
```
Critère dur : la grelinette **inscrit un bénéfice** (le bonus de vers), le couple
bêcher/grelinette est **symétrique et lisible**, et **aucun golden de tick ne
bouge**. Mets à jour `DETTE.md` D30 (mécanisme acté + champ retenu) et `00_etat`
si tu en crées un.
