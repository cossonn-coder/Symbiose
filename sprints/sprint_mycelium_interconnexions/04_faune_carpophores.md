# ④ Faune fongivore + carpophores

> Lire d'abord `00_etat.md` + `docs/faune/mycelium/conception_mycelium_interconnexions.md`
> (§1.1, §2 ligne « Nourriture faune », §3.4). Prérequis : ①②③ FAITS. On NOURRIT la
> faune fongivore (champ) et on fait APPARAÎTRE les carpophores (perception). **Re-
> figeage golden (population) attendu et MAÎTRISÉ ; carpophores golden-NEUTRES.**

## Objectif
Une fraction du `mycelium` **gonfle la guilde `detritivore`** (collemboles fongivores)
— interconnexion champignon ↔ faune. En parallèle, des **carpophores** (sprites
échantillonnés, DÉRIVÉS du champ, sans état) rendent le réseau VISIBLE après pluie,
en automne, sur le bois colonisé.

## À faire

### A. Faune fongivore (`fields/population.py`, `tick_populations`)
- Patron = l'attraction du `fruit` (`population.py` ~L100-113, `FRUIT_AUX_GAIN` /
  `FRAC_AUX_POURRI`). Ajouter un terme : là où `mycelium` est haut, **ajouter une
  fraction à la guilde `detritivore`** (meilleur fit collemboles ; `auxiliaire` en
  repli si `detritivore` n'est pas mobilisable proprement).
  `populations["detritivore"].add(r, c, FONGIVORE_GAIN × mycelium_norm)` (borné par
  `POP_MAX` du champ). Knob `FONGIVORE_GAIN` (placeholder).
- L'`EcoFields` doit être accessible depuis `tick_populations` pour lire `mycelium`
  (vérifier la signature ; `tile`/`eco` déjà passés). Lecture seule du champ.

### B. Carpophores échantillonnés (perception, golden-NEUTRE)
- Patron `sample_sprites` (vie macro, sprites bornés déterministes). Échantillonner
  des positions de carpophores là où `mycelium` est dense **+** pic d'humidité récent
  **+** saison favorable (automne). **Aucun état propre** : recalculés du champ à
  chaque snapshot (comme la vie macro). Zéro RNG (hash spatial déterministe).
- Exposer au snapshot (`tools/simserver/serialize.py`) une liste `carpophores`
  (positions + densité), comme les sprites macro — la VUE (⑥) les dessinera. Liste
  VIDE si mycélium nul → golden/pont neutres.

## Couches
`population.py` (fields) lit `mycelium` (fields) — OK. Carpophores = échantillonnage
pur + exposition pont (lecture). Aucune remontée de couche.

## Définition de done
- Terme fongivore dans `tick_populations` (`detritivore` ∝ mycélium), knob
  `FONGIVORE_GAIN`. Carpophores échantillonnés + exposés au snapshot (liste).
- `tests/test_population.py`/`test_mycelium.py` étendu : à mycélium FORT, la densité
  `detritivore` locale MONTE vs mycélium nul ; bornée `POP_MAX` ; carpophores
  échantillonnés DÉTERMINISTES (h1==h2, mêmes positions à seed/week égaux) ; liste
  carpophores VIDE quand mycélium nul. Indépendance position/semaine conservée.
- **Golden population RE-FIGÉ** : nouveau hash `test_population.py`. Dérive
  **localisée à la guilde `detritivore`** sous mycélium. L'ANALYSER, re-figer, noter
  `ancien → nouveau` + explication dans `00_etat.md`. Smoke `test_golden.py` : viser
  inchangé (la faune n'entre pas dans le hash smoke — VÉRIFIER ; sinon re-figer aussi,
  expliqué). Carpophores = NEUTRES (perception).
- MAJ `00_etat.md` (④ → FAIT + hash) puis commit.

## Pièges
- Carpophores = **perception PURE** : aucun retour sur la simulation (ils ne nourrissent
  pas, ne décomposent pas — c'est le CHAMP qui fait tout). S'ils touchent un champ, le
  golden bouge à tort.
- Choisir `detritivore` en connaissance des guildes existantes (`build_population_specs`)
  — si l'ajout perturbe l'équilibre proie/prédateur, calibrer `FONGIVORE_GAIN` bas.
- Déterminisme de l'échantillonnage : trier les positions, hash spatial stable, zéro
  `random`.
