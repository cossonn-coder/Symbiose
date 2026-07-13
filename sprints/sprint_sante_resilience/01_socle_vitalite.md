# ① Socle vitalité continue

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + ce fichier. Source de
> vérité = `data/code/` (lancement depuis `data/code/`). Doc de référence :
> `docs/conception/CONCEPTION_SANTE_RESILIENCE.md` §1, §2.3, §4.

## Objectif

Remplacer l'attribut plat `health: int 0–3` par une **vitalité continue
`vitalite ∈ [0,1]`**, avec une property `etat` qui la discrétise en
{sain/affaibli/malade/mort}. Introduire la **primitive d'érosion `erode()`** qui
divise le dégât par la constitution d'espèce `resilience_base` — **absente au ①**
(`getattr(..., 1.0)` → no-op), posée au tronçon ②. **AUCUN gène ajouté nulle part**
(`GENE_NAMES` reste intact — resilience n'est PAS un gène, c'est une base d'espèce).

## Modèle (rappel doc §1)

- `vitalite = 1.0` neuf, `0.0` mort. `is_alive = vitalite > 0`.
- `VITALITE_STEP = 1/3` : convertit les anciens décréments/gains entiers `±1` en
  `±1/3` → à résilience neutre, `vitalite` **suit exactement** `health/3` d'antan.
- Property `etat` (seuils miroir de `k/3`) : sain `> 2.5/3`, affaibli `(1.5/3,
  2.5/3]`, malade `(0, 1.5/3]`, mort `≤ 0`. Expose une constante ou un petit enum
  lisible ; les lecteurs discrets (`health == 3`) deviennent `etat == "sain"` (ou
  `vitalite >= SEUIL_SAIN`).
- **`erode(amount)`** (méthode d'instance) : `vitalite = max(0, vitalite - amount /
  getattr(self.plant_class, "resilience_base", 1.0))`. Au ①, aucune espèce ne
  définit `resilience_base` → `getattr` renvoie **1.0** (no-op). Le ② pose la
  table complète → la division différencie.

## Fichiers à toucher

1. **`plants/base/instance.py`**
   - Renommer le champ `health: int = 3` → `vitalite: float = 1.0` (ligne ~30).
   - `is_alive` (ligne ~294) : `return self.vitalite > 0`.
   - `regress()` (ligne ~306) : `self.vitalite = 0`.
   - `__repr__` (ligne ~324) : `vitalité={self.vitalite:.2f}`.
   - Ajouter property **`etat`** (str "sain"/"affaibli"/"malade"/"mort") + les
     seuils en constantes de module. Ajouter méthode **`erode(amount)`** (divise
     par `getattr(self.plant_class, "resilience_base", 1.0)`). PAS de gène, PAS
     de helper `_resilience_eff`.
2. **`sim/effects/resolution.py`** (`ReduceHealth`, ligne ~240) : remplacer
   `m.plant.health = max(0, m.plant.health - m.amount)` par
   `m.plant.erode(m.amount * VITALITE_STEP)`. La marque de symptôme (`if m.cause`)
   et le log (`status`/`etat`) suivent (`vitalite`/`etat`). **`PropagateDisease`**
   (ligne ~292) : `m.target_plant.erode(VITALITE_STEP)`.
3. **`sim/engine/mortalite.py`** :
   - Sénescence (ligne ~80) : décrément DIRECT (hors `erode`, hors résilience) →
     `plant.vitalite = max(0.0, plant.vitalite - VITALITE_STEP)`.
   - Asphyxie (ligne ~99) : passe par `erode` → `plant.erode(VITALITE_STEP)`
     (la médiation `tolerance_asphyxie` reste en amont sur la *pression*).
   - Guérison (lignes ~106-122) : `if plant.etat != "sain" and sen < HEAL_SEN_CUTOFF`
     … `plant.vitalite = min(1.0, plant.vitalite + heal_amount)`. **Garder
     `gene("vigueur")` et `cout_defense()`** dans le taux (décision : vigueur =
     récupération). Le tirage `_hash_noise < heal` devient un GAIN continu :
     applique `+ VITALITE_STEP` quand le tirage passe (conserve la dynamique
     paliers d'antan à l'identique) — NE PAS transformer heal en gain fractionnaire
     ici (on garde le pas 1/3 pour la neutralité d'échelle ; la finesse continue
     vient des dégâts médiés, pas de la guérison).
   - Médiés `_mediated_damage` (~375) et `_wind_damage` (~428) : remplacer
     `lost = min(p.health, int(effective / DAMAGE_STEP))` +
     `ReduceHealth(p, lost,…)` par un `ReduceHealth` d'amount **continu** =
     `effective / DAMAGE_STEP` (SANS `int()` ni `min(p.health,…)` — `erode` borne
     déjà à 0). ⚠️ Ici l'amount du `ReduceHealth` n'est PAS multiplié par
     `VITALITE_STEP` deux fois : la résolution applique `amount * VITALITE_STEP`.
     Donc passe `amount = effective / DAMAGE_STEP` et laisse la résolution scaler.
     Les tests de mort (`if p.health == 0`) → `if not p.is_alive`.
4. **`sim/effects/perturbations.py`** : `damping_off` (~121) `ReduceHealth(plant,
   plant.health,…)` → l'amount « tue » : passe `plant.vitalite / VITALITE_STEP`
   (pour que `× VITALITE_STEP` en résolution ramène à la vitalité entière → mort
   nette). `background_mortality` (~465) `int(plant.health*0.7)` : recalcule en
   continu → perte = `plant.vitalite * 0.3 / VITALITE_STEP` (même effet ×0.7).
   `_cap_chronique` : le cap `amount=1` reste `1` (→ `×VITALITE_STEP` = 1/3 en
   résolution) — inchangé conceptuellement.
5. **`sim/vigueur_plante.py`** : `sante()` (ligne ~43) `return plant.vitalite`
   (déjà [0,1] ; supprimer `/HEALTH_MAX`). `HEALTH_MAX` peut rester ou être retiré
   s'il n'est plus lu ailleurs (vérifier).
6. **`sim/engine/croissance.py`** : photosynthèse (ligne ~204)
   `health_factor = plant.vitalite`.
7. **`fields/population/resources.py`** : 5 occurrences `p.health / 3.0` →
   `p.vitalite`.
8. **`sim/maitrise_detection.py`** (ligne ~245) : `p.health == 3` →
   `p.etat == "sain"`.
9. **`sim/actions/gestes.py`** : `plant.health = 0` (~209 déraciner) → `vitalite`;
   `plant.health -= 1` (~386 écimage NET) → `plant.erode(VITALITE_STEP)`
   (c'est un coup mécanique subi, cohérent avec `erode`; OU décrément direct —
   choisis `erode` pour homogénéité, le no-op ① le rend identique).
10. **`sim/actions/greffe.py`** (`scion.health = 0`) → `scion.vitalite = 0`.
11. **`plants/base/instance.py`** (aleas) & `sim/engine/aleas.py` (~148-153) :
    `ReduceHealth(p, 1,…)` inchangé (amount 1 → 1/3 en résolution) ; `if p.health
    == 0` → `if not p.is_alive`.
12. **`tests/test_golden.py`** (ligne 51) : `_PLANT_ATTRS` remplace `"health"` par
    `"vitalite"`. Les valeurs figées deviennent des floats → **re-figer** (§Golden).

> Cherche AUSSI toute autre occurrence résiduelle : `grep -rn "\.health" --include=*.py`
> (hors `*_memory`, `health_factor`, tests). N'en laisse aucune.

## Constante `VITALITE_STEP`

Pose `VITALITE_STEP = 1.0 / 3.0` là où vivent les constantes de santé
(`fields/ecofields/constants.py` à côté de `SEN_RATE`/`HEAL_RATE`, ou un module
`plants` — au choix cohérent avec les imports existants). Importe-la où nécessaire.

## Golden — RE-FIGÉ #1 (annoncé)

Dérive attendue, **localisée et prouvable** :
- Les dégâts médiés (gel/grêle/vent) perdent leur **plancher entier** → érosion
  fractionnaire là où l'ancien `int()` arrondissait à 0 ou à un pas entier.
- `_PLANT_ATTRS` passe de `health` (int) à `vitalite` (float).

Procédure : lance `python3 -m tests.test_golden`, observe la dérive, **re-fige**
le hash, et **PROUVE la localisation** dans le message de commit : la dérive doit
se cantonner aux plantes ayant subi un dégât médié / une convalescence ; le reste
suit `vitalite == ancien_health/3`. Si la dérive touche des plantes JAMAIS
blessées → BUG de conversion d'échelle, corrige (ne fige pas).

Mets à jour le hash dans `00_etat.md` (§REPRISE) et le message de commit.

## Ce qu'il NE faut PAS faire

- **Aucun `resilience_base` défini ici** (tronçon ②). `erode()` reste no-op via
  `getattr` défaut 1.0. **Ne touche pas à `GENE_NAMES`** (resilience n'est pas un gène).
- **Ne pas transformer la guérison en gain fractionnaire** (garder le pas 1/3) —
  sinon la dérive golden fuit hors des voies attendues.
- **Ne pas toucher au canal campagnol** (`root_herbivory`, tronçon ③).
- Ne pas lancer `test_epaisseur_500ans` (interdit — long/inutile).

## Vérif de sortie

`python3 main.py` tourne sans crash ; `python3 -m tests.test_golden` vert (hash
re-figé) ; suites ciblées `tests/` qui lisent la santé passent (adapter les tests
qui écrivent `p.health = …` → `p.vitalite`, ex. `test_maitrise_detection.py`).
