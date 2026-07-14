# Tronçon ① — Désynchronisation des trois horloges phénologiques (MOTEUR)

> Kickoff autosuffisant. Lis `CLAUDE.md` (racine) + `00_etat.md` (ce dossier) +
> `docs/conception/CONCEPTION_DESYNC_PHENOLOGIE.md` (§2), puis exécute.
> Lancement des tests depuis `data/code/`.

## Objectif
Étaler par individu **floraison**, **fanaison (abscission)** et **onset de
sénescence**, via le gène héritable existant `phenologie_florale` réutilisé
comme **tempo de vie** (`g > 1` = individu précoce partout). Tout l'effet est
∝ `(g − 1)` → **à g = 1.0 la sim est strictement identique** (mais le golden
DÉRIVE quand même car ses plantes ont `g ≠ 1`, cf. §Golden).

## Principe (NE PAS dévier)
- **Un seul gène**, aucun gène neuf, aucun système parallèle. On lit
  `plant.gene("phenologie_florale")` (accesseur `plants/base/instance.py:173`).
- **Déterministe** (philo #3) : le gène vient déjà d'un hash de position
  (`founder_genes`/`child_genes`). **Aucun RNG vivant, aucun `random`.**
- Convention de signe **partagée** : `g > 1` ⇒ **précoce** (fleurit tôt / largue
  tôt / sénesce tôt). Respecte-la sur les trois sites, sinon le chronotype
  devient incohérent.

## A. Floraison — recalibrer le décalage
Fichier `sim/engine/floraison.py`. Formule INCHANGÉE, seule la constante monte :
```
FLORA_GENE_SHIFT : 40.0 → 200.0   # départ de calibrage (doc §2.1)
```
Rien d'autre à toucher ici (`gdd_eff = cls.gdd_floraison − FLORA_GENE_SHIFT·(g−1)`
existe déjà). Mets à jour le commentaire de la constante : la valeur mordait
imperceptiblement (±0.3 sem) ; ~200 donne ±~1.6 sem à ±σ.

## B. Fanaison (abscission) — semaine par-individu
Fichiers `sim/engine/decompo.py::_abscission` + son garde dans
`sim/engine/boucle.py` (~ligne 472) + constantes `fields/ecofields/constants.py`.

1. Constantes (près de `ABSCISSION_WEEKS`) :
   ```
   ABSCISSION_BASE   = 38     # semaine-pivot (dans l'automne 27..39)
   ABSCISSION_JITTER = 15.0   # départ ; ±σ(0.10) ⇒ ±1.5 sem
   ABSCISSION_MIN, ABSCISSION_MAX = 34, 39   # fenêtre d'automne bornée
   ```
   `ABSCISSION_WEEKS` peut rester (non utilisé) ou être retiré ; si tu le retires,
   corrige l'import `boucle.py:26`.
2. Garde dans `boucle.py` : remplacer
   `if saison == "automne" and week_in_year in ABSCISSION_WEEKS:` par un
   déclenchement sur **toute la fenêtre** :
   `if saison == "automne" and ABSCISSION_MIN <= week_in_year <= ABSCISSION_MAX:`
   et passer `week_in_year` à `_abscission`.
3. Dans `_abscission(self, tile, eco, week_in_year)` : pour chaque caduque
   vivante, calculer sa semaine propre
   ```
   g = plant.gene("phenologie_florale")
   w = round(ABSCISSION_BASE - ABSCISSION_JITTER * (g - 1.0))
   w = max(ABSCISSION_MIN, min(ABSCISSION_MAX, w))
   ```
   et ne larguer **que si `week_in_year == w`**. Dépôt **unique annuel** :
   `masse = plant.current_height * NECROMASS_PER_CM * ABSCISSION_FRAC` (garder
   `ABSCISSION_FRAC`, une seule fois par an au lieu de 2 → l'ordre de grandeur
   du total reste proche ; le re-figeage absorbe l'écart). Log inchangé (🍂).

## C. Sénescence — onset par-individu (+ MIROIR sémiologie)
Fichiers `sim/engine/mortalite.py::_tick_senescence_health` + **miroir**
`sim/semiologie.py::senescence` + constante `fields/ecofields/constants.py`.

1. Constante (près de `SENESCENCE_ONSET`) :
   ```
   SEN_ONSET_JITTER = 0.5   # départ ; ±σ(0.10) ⇒ ±0.05 de fraction de longévité
   ```
2. Dans `mortalite.py`, avant le calcul de `sen`, remplacer `SENESCENCE_ONSET`
   par un onset propre :
   ```
   g = plant.gene("phenologie_florale")
   onset = max(0.05, min(0.95, SENESCENCE_ONSET - SEN_ONSET_JITTER * (g - 1.0)))
   denom = (1.0 - onset) * L
   sen = max(0.0, min(1.0, (plant.age_years - onset * L) / denom))
   ```
3. **MIROIR OBLIGATOIRE** : `sim/semiologie.py::senescence` recalcule la MÊME
   pression pour le signe visuel (« Miroir EXACT de la pression D27 »). Applique-y
   le **même** `onset` jitteré (même gène, même formule). Si tu ne le fais pas,
   le signe de sénescence et la mort divergeront (bug sémio). Importe
   `SEN_ONSET_JITTER` au besoin.

## Golden — RE-FIGEAGE LARGE ATTENDU (annoncé)
Les plantes du golden (`tests/test_golden.py`, `semer_fondateur`) ont `g ≠ 1` →
la désync mord → le digest **change** (floraison→nouaison→litière/eco ;
abscission→litière feuille ; onset→`vitalite` haché). C'est **prévu et légitime**
(dérive localisée = les knobs mordent enfin sur la variance fondatrice, philo #3
préservée). **Procédure** :
1. Lancer `python3 -m tests.test_golden` → il ÉCHOUE (digest changé).
2. **Inspecter** la dérive : elle doit rester **cohérente** (dates de floraison
   étalées entre plantes, largage de feuille à des semaines différentes, onsets
   décalés). Si une plante g=1.0 apparaissait, ELLE ne devrait pas bouger.
3. Re-figer : régénère `tests/golden_hash.txt` (mécanisme habituel du test).
4. Noter le nouveau hash dans `00_etat.md` et le message de commit.

## Test d'étalement (garde INDÉPENDANTE du golden)
Le golden re-figé ne PROUVE pas la désync (il constate juste un changement).
Ajoute une vérif ciblée — nouveau petit test OU assertion dans un banc — qui
sème ~10 individus d'une même espèce (variance fondatrice) et vérifie que
**l'écart-type des semaines de première floraison (floraison franchissant 0.5)
est > 0** sur un cycle. Idem esprit pour abscission (semaines de largage
distinctes). Objectif : capter une régression si un futur refactor ré-annulait
la désync. Garde-le court, déterministe, SEED fixe.

## Ne PAS faire
- Ne PAS renommer `phenologie_florale`.
- Ne PAS toucher la porte photopériode (`bloom_daylen_*`).
- Ne PAS introduire de RNG (`random`, `np.random`) — tout dérive du gène.
- Ne PAS lancer `test_epaisseur_500ans` (interdit : long et inutile).
- Ne PAS re-figer le golden sans avoir inspecté la dérive (elle doit être
  cohérente, pas un artefact).

## Vérif de sortie
- `python3 main.py` tourne sans crash.
- `python3 -m tests.test_golden` PASSE après re-figeage.
- Le test d'étalement PASSE (spread > 0).
- Mettre à jour `00_etat.md` (§REPRISE + nouveau golden hash) puis commit.
