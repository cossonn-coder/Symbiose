# Tronçon ② — N/P/K socle (trois champs posés, uptake lit encore `fertilite`)

> Sprint physico-chimie du sol. Conception : `docs/conception/CONCEPTION_SOL_NUTRIMENTS_NPK.md`
> (§0, §1, §2.1, §3). Kickoff **autosuffisant** (relançable à froid).
> Tronçon ① (champ `ph`) déjà CLOS — même tactique « neutre-d'abord » à appliquer ici.

## Objectif

Éclater le proxy unique `fertilite` **en préparation** : poser trois `GridField`
distincts **`n`** / **`p`** / **`k`** (azote / phosphore / potasse), **initialisés
par héritage du `soil_type`** (table `NUTRIENT_INIT_PAR_SOL`, conception §3). C'est
le socle du volet NPK.

**Périmètre strict** : les trois champs sont **posés mais écrits ET lus par
PERSONNE**. L'uptake, la minéralisation (`tick_decomposition`), `soil_memory` et
les signatures continuent d'utiliser **`fertilite` inchangé**. → golden **NEUTRE**
(on ajoute trois champs inertes, exactement comme `ph` au ①).

⚠️ **NE PAS** faire dans ce tronçon (réservé au ③, le gros re-figé) : retrait de
`fertilite`, split de la minéralisation N/P/K, loi de Liebig, lessivage différencié,
CEC, `SOIL_SIGNATURE` explicite. Si tu touches à un seul lecteur/écrivain existant,
le golden bougera → c'est qu'on a débordé sur ③.

## Modèle (ce tronçon)

```
n[r,c] init = NUTRIENT_INIT_PAR_SOL[soil_type][0]
p[r,c] init = NUTRIENT_INIT_PAR_SOL[soil_type][1]
k[r,c] init = NUTRIENT_INIT_PAR_SOL[soil_type][2]
```

Pas de tick, pas de dérive : les champs restent à leur valeur d'init (aucun
écrivain avant ③). Plage ~[0, 3] comme l'ancien `fertilite` (max_val=3.0 par
défaut du GridField).

## Étapes (calquer EXACTEMENT le ① déjà fait)

1. **`fields/ecofields/constants.py`** — ajouter la seule constante d'init du socle
   (conception §3) :
   ```python
   NUTRIENT_INIT_PAR_SOL = {  # (N, P, K) hérités de la roche-mère
       "terre": (1.0, 0.8, 0.9), "argile": (0.9, 0.9, 1.1),
       "sable": (0.5, 0.4, 0.4), "roche": (0.4, 0.6, 0.5)}
   ```
   (Ne PAS encore ajouter `NPK_RELEASE`/`BESOIN`/`LEACHING`/`MICRO_BOOST`/`CEC_*`/
   `FIXATION_N` — tout ça est pour ③/⑦.)

2. **`fields/ecofields/container.py`** :
   - Ajouter trois champs `n: GridField`, `p: GridField`, `k: GridField` au
     dataclass (modèle = le champ `ph` du ①).
   - **Init par héritage** dans `__post_init__` : chaque champ à
     `NUTRIENT_INIT_PAR_SOL[self.soil_type][i]` (fallback `"terre"`), via
     `GridField(rows, cols, initial=..., max_val=3.0)`. `self.soil_type` existe
     déjà (ajouté au ①).
   - Les exposer dans `get_field` (`"n"`, `"p"`, `"k"` → overlay debug gratuit).
   - **Aucun tick**, aucune méthode neuve : pas de calcul à isoler ce coup-ci.
   - ⚠️ `container.py` est déjà à **387 ldc** (le plus dense, au-dessus du seuil
     ~350 avant même ②). Ajouter 3 champs = ~6 lignes d'orchestration de plus
     (déclarations + init + registre). **Le signaler à Nico** (comme au ①). Si ça
     gêne, envisager d'extraire l'init des champs hérités du sol dans un petit
     helper — mais NE PAS lancer un éclatement d'`EcoFields` sans accord (chantier
     à part, hors périmètre sprint).

3. **PAS de `boucle.py`** : aucun tick à câbler (les champs sont inertes au ②).

4. **`init_eco`** : déjà OK (le param `soil_type` posé au ① suffit ; les fabriques
   `test_golden.build_world` et `main.build_tile` le passent déjà).

5. **Golden** — `python3 -m tests.test_golden`. Doit **PASSER INCHANGÉ**
   (hash `f7e1a9b4…`). Si le golden bouge → un champ NPK est lu/écrit par accident.
   **Ne PAS re-figer.**

## Invariant golden

- **NEUTRE** : hash de référence **identique** (`f7e1a9b4…`, inchangé depuis le
  catalogue, confirmé toujours stable après ①). Trois champs posés, zéro lecteur,
  zéro écrivain.

## Validation

- `python3 -m tests.test_golden` PASS **sans re-figeage**.
- `python3 main.py` tourne sans crash.
- Petit script : `n`/`p`/`k` hérités différemment selon `soil_type`
  (terre (1.0, 0.8, 0.9) ≠ sable (0.5, 0.4, 0.4)) et apparaissent dans
  `get_field`. Aucune dérive (valeurs constantes, pas de tick).

## À faire en fin de tronçon

- Mettre à jour `00_etat.md` (statut ② ✅, golden **inchangé**, note taille).
- Commit : `feat(sol) : tronçon ② champs N/P/K hérités du soil_type, inertes — golden NEUTRE (aucun lecteur, fertilite intact)`.
- Écrire le kickoff `03_bascule_liebig.md` avant le `/clear` — **LE gros re-figé** :
  retrait de `fertilite`, minéralisation splittée (§2.2), loi de Liebig (§2.3),
  lessivage différencié (§2.4), CEC dérivée (§2.5), `SOIL_SIGNATURE` explicite
  (§2.6), réalim `soil_memory` (§2.8). Prévenir Nico que ③ re-fige LARGE
  (annoncer, vérifier la dérive localisée).
