# ① Moteur — floraison retypée (forçage thermique événementiel)

> Kickoff autosuffisant. Lis d'abord `CLAUDE.md` (racine) + `00_etat.md` (ce
> dossier) + `docs/vegetal/floraison/conception_floraison_fructification.md`.
> Source de vérité = Python `data/code/`. Lance tout depuis `data/code/`.

## Objectif
Remplacer le modèle de floraison **double-porte** (forçage GDD + photopériode) par
un **forçage thermique ÉVÉNEMENTIEL** : la floraison est armée au *franchissement*
d'un seuil de chaleur cumulée propre à l'espèce, puis dure `bloom_duration`
semaines. Ça corrige la grappe D84 (floraison à contretemps + fugace) : les
seuils bas placent chaque espèce dans SA saison, la durée bornée tue la fugacité,
la porte photopériode disparaît (c'est elle qui créait le recouvrement nul de
S34). Voir CONCEPTION §1 (diagnostic) et §2 (modèle).

## Modèle à coder (CONCEPTION §2)
Dans `sim/engine/floraison.py::_tick_floraison`, par plante vivante :
```
si week_in_year == 1:  plant.gdd_accum = 0.0 ;  plant.bloom_week = -1
plant.gdd_accum += max(0.0, temp - T_BASE_FLORAISON)     # temp = eco.temperature.at_plot(r,c)
g = plant.gene("phenologie_florale")
gdd_eff = cls.bloom_forcing_gdd - FLORA_GENE_SHIFT * (g - 1.0)
si plant.bloom_week < 0 et is_seed_bearing(plant) et plant.gdd_accum >= gdd_eff:
    plant.bloom_week = week_in_year                       # franchissement → armement 1×/an
en_fleur = (plant.bloom_week >= 0) et (week_in_year < plant.bloom_week + cls.bloom_duration)
cible = 1.0 si en_fleur sinon 0.0
taux = FLORAISON_MONTEE si cible > plant.floraison sinon FLORAISON_DESCENTE
plant.floraison += (cible - plant.floraison) * taux
```
- **Retirer** la porte photopériode (`daylength`, `bloom_daylen_min/max`) et
  l'ancien `gdd_floraison`.
- **Conserver** `FLORAISON_MONTEE=0.35`, `FLORAISON_DESCENTE=0.50`,
  `T_BASE_FLORAISON=6.0`, la garde de maturité `is_seed_bearing`, le gène-tempo.
- **Recalibrer** `FLORA_GENE_SHIFT` : `200 → ~20` (à seuils bas, 200 rendrait un
  pied g=1.2 négatif ; ~20 donne ±1-2 sem à ±σ=0.10). Documente le nouveau chiffre
  dans le commentaire (garde-fou pédagogique CLAUDE.md).

## Fichiers à toucher
1. **`plants/base/instance.py`** — ajouter l'état `bloom_week: int = -1` à côté de
   `gdd_accum` (~ligne 143). Commentaire : semaine de franchissement du forçage,
   reset annuel, `-1` = pas encore fleuri cette année. Hors `_PLANT_ATTRS`.
2. **`plants/base/familles.py`** (~lignes 74-80) — **remplacer** `gdd_floraison` /
   `bloom_daylen_min` / `bloom_daylen_max` par les défauts :
   - `bloom_forcing_gdd: float = 60.0` (mi-été, franchit ~S22-23) ;
   - `bloom_duration: int = 6`.
   Commentaire mis à jour (forçage thermique par saison-cible ; bas→printemps,
   haut→automne).
3. **`sim/engine/floraison.py`** — réécrire `_tick_floraison` (modèle ci-dessus).
   Mettre à jour le docstring de tête (plus de double porte : forçage
   événementiel). Retirer l'import `daylength` s'il n'est plus utilisé.
4. **`plants/perennials.py`** — `AppleTree` : **retirer** `gdd_floraison = 130.0`
   (lignes 197-207, patch caduc) ; poser `bloom_forcing_gdd = 8.0` + `bloom_duration
   = 3` (printemps, ~S15). `CherryTree`, `Fig` : `bloom_forcing_gdd` printanier
   (~8-12), `bloom_duration = 3-4`. Les ligneux anémophiles à chatons (chêne,
   bouleau, noyer, charme, hêtre, sapin) : garde le défaut ou un seuil printanier
   bas (~15) — ils comptent peu (pas `fruitier`), mais restent cohérents.
5. **`plants/species/*.py`** — poser `bloom_forcing_gdd` + `bloom_duration` par
   espèce selon la table CONCEPTION §2.4 (printemps précoce : Violette S.violet,
   Fraise Strawberry ~10 / durée 4 ; été : Tomate, Courgette Zucchini, Tournesol
   Sunflower, Bourrache Borage, Phacélie Phacelia, Consoude Comfrey ~40-86 / durée
   6-10 ; automne : Armoise Mugwort ~180 / durée 5). Pour les espèces sans enjeu
   fort, le défaut familles.py (60/6) suffit — ne surcharge que là où la
   saison-cible est claire.

## Tests (garde décisive)
- **`tests/test_desync_phenologie.py`** et **`tests/test_fruits.py`** forcent
  `plant.floraison` / l'âge directement → vérifie qu'ils tournent encore ;
  ADAPTE ce qui référence l'ancien modèle (portes, `gdd_floraison`,
  `bloom_daylen_*`). La désync se teste toujours (σ>0 des semaines de floraison
  via le gène) mais sur le **nouveau** chemin (`bloom_week` étalé par
  `FLORA_GENE_SHIFT`).
- **Test neuf** (fichier existant ou `tests/test_floraison_forcage.py`) :
  1. **placement** — sous la météo réelle, un pommier mûr (âge ≥ 5,
     `bloom_forcing_gdd` printanier) arme `bloom_week` au **printemps** (S13-17),
     PAS en automne ; une espèce été-cible arme en été ; une automne-cible en
     automne ;
  2. **étalement** — une cohorte de même espèce avec gènes dispersés (σ>0) a un
     **spread > 0** des `bloom_week` ;
  3. **neutralité g=1** — un pied g=1.0 arme exactement à `bloom_forcing_gdd`.
- **NE LANCE JAMAIS** `test_epaisseur_500ans` (interdit, long et inutile).

## Golden (`tests/test_golden.py`, hash dans `tests/golden_hash.txt`)
- Le pommier du smoke est **< 5 ans** (maturity_years=5, smoke 4 ans) →
  `is_seed_bearing` False → `floraison` reste 0 → **potentiellement NEUTRE**.
- **MAIS** des annuelles `fruitier=True` qui atteignent le stade mature dans le
  smoke pourraient désormais **fleurir puis nouer** (avant : jamais, gates
  disjointes) → litière `fruit` → eco → **hash qui dérive**.
- **Procédure** : lance `python3 -m tests.test_golden`. S'il PASSE → golden
  **NEUTRE**, ne touche pas le hash. S'il DÉRIVE → **re-figeage maîtrisé
  AUTORISÉ** (prévu par cette conception) : vérifie que la dérive est cohérente
  (une fruitière mûre noue au bon moment → fruits → litière), consigne la cause
  exacte (quelle espèce, quelle semaine) dans `00_etat.md` et le message de
  commit, puis re-fige le hash. **Aucune autre source de dérive tolérée** (si le
  golden bouge pour une raison non-floraison, c'est un bug → corrige, ne fige
  pas).

## Ce qu'il NE faut PAS faire
- Pas de mécanisme photopériodique jour-court (approximé par seuil élevé, §2.5).
- Pas de dormance/chill.
- Ne touche pas `semiologie.senescence` (miroir de sénescence, hors sujet).
- Ne touche pas la nouaison (`decompo._tick_fruits`) — c'est le tronçon ②.
- Ne renomme pas `phenologie_florale`.

## En finissant
Mets à jour `00_etat.md` (tronçon ① fait, golden neutre/re-figé + hash, décisions
de calibrage retenues) et commit (fichiers nommés, message style projet, terminé
par `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`). Puis tronçon ②.
