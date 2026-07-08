# Tronçon 01 — Scatter de la boucle lumière-REÇUE

> Kickoff AUTOSUFFISANT. Lis `CLAUDE.md` + `00_etat.md` + ce fichier, rien d'autre
> n'est nécessaire. **Optimisation PURE, bit-identique, golden INCHANGÉ.**
> Détail complet dans `docs/conception/CONCEPTION_PERF_SCATTER_RECUE.md`.

## Objectif

Convertir la boucle **lumière-reçue par plante** de `fields/light.py:compute`
d'un **gather** (chaque échantillon interroge `ObstacleIndex.covering` avec un
`reach` dimensionné par l'ombre la plus longue de la tuile → 40 % du tick) en
**scatter** émetteur→échantillons (chaque émetteur ne visite que la bbox de sa
capsule), **exactement comme D32 l'a fait pour la boucle lumière-SOL**.

## Contexte précis

Dans `fields/light.py`, méthode `LightField.compute` :
- La boucle **lumière-sol** (par plot) est DÉJÀ en scatter (itère `emitters`,
  bbox de capsule par émetteur) — c'est le MODÈLE à imiter.
- La boucle **lumière-reçue** (celle qui remplit `self.received[id(p)]`, avec
  `order = sorted(emitters…)`, `index = ObstacleIndex(order)`, puis `for … in
  receivers:` avec 5 échantillons × les tranches `slices` et l'appel
  `index.covering(sx, sy, max_len)`) est restée en **gather**. C'est ELLE qu'on
  renverse.

## Fichiers à toucher

1. **`fields/light_index.py`** — ajouter une classe `ReceiverIndex` (miroir de
   `ObstacleIndex`) : buckets de plots (pas = `PLOT_CM`) indexant des
   **échantillons** par leur cellule. Chaque échantillon stocké = tuple
   `(ph, ref, sx, sy)` où `ph` = hauteur du récepteur (pour le test `qh > ph`),
   `ref` = clé du récepteur (`id(p)` ou l'index dans `receivers`), `(sx, sy)` =
   position continue de l'échantillon. Méthode `covering(qx, qy, xmin, xmax,
   ymin, ymax)` OU `in_bbox(...)` renvoyant les échantillons dont la cellule
   tombe dans la bbox `[xmin,xmax]×[ymin,ymax]` (scanne les cellules de la bbox,
   `buckets.get`, `extend`). Fichier actuellement à 31 LDC → large marge.

2. **`fields/light.py`** — récrire la boucle reçue en scatter (voir algo ci-dessous).
   Fichier à 225 LDC (🟢) → reste dans la bande.

3. **`tests/test_scatter_lumiere_recue.py`** (NOUVEAU) — verrou d'équivalence,
   calqué **ligne à ligne** sur `tests/test_scatter_lumiere_sol.py` mais comparant
   `self.received` (gather reconstruit vs scatter de `compute`) en **égalité `==`
   bit-à-bit**, sur : monde smoke réel grandi, les 4 saisons, avec ET sans maison.

## Algorithme scatter (à implémenter dans `compute`, boucle reçue)

Pré-requis inchangés : `receivers`, `emitters`, `order = sorted(emitters, key=
lambda t: t[3], reverse=True)`, géométrie maison (`ox, oy, hx0…hy1, h_height`),
`slices`, `total_w`, `CANOPY_SAMPLE_FRAC`, `LIGHT_FLOOR`.

Pour chaque récepteur, préparer ses 5 échantillons **une fois** :
`d = pr*CANOPY_SAMPLE_FRAC` ; `samples = ((px,py),(px+d,py),(px-d,py),(px,py+d),(px,py-d))`.

Structure d'accumulation : `acc[ref] = 0.0` pour chaque récepteur.

**Boucle externe sur les tranches** `for sdx, sdy, inv_tan, w in slices:` :
1. `h_len = h_height * inv_tan`. Construire la liste des échantillons ACTIFS de la
   tranche = tous les échantillons NON masqués par la maison :
   masqué ssi `house is not None and _point_in_swept_rect(sx+ox, sy+oy, hx0,hy0,
   hx1,hy1, sdx, sdy, h_len)`. Un échantillon masqué → att = 0 (exclu de la
   moyenne, comme le `continue` du gather).
2. `att[(ref, k)] = 1.0` pour chaque échantillon actif `k∈0..4` (les masqués
   n'entrent pas). Construire un `ReceiverIndex` sur les échantillons actifs.
3. `for q, qx, qy, qh, qr, qd in order:` (déjà hauteur décroissante) :
   - si `qd <= 0.0` : continue.
   - `length = qh * inv_tan` ; bbox de la capsule :
     `bx = qx + sdx*length ; by = qy + sdy*length` ;
     `xmin = min(qx,bx) - qr ; xmax = max(qx,bx) + qr` ; idem y.
   - récupérer les échantillons candidats via l'index (cellules de la bbox).
   - pour chaque candidat `(ph, ref, sx, sy)` :
       si `qh <= ph` : continue  (auto-ombrage exclu, MÊME test que gather) ;
       si `_point_in_capsule(sx, sy, qx, qy, sdx, sdy, length, qr)` :
           `att[(ref,k)] *= (1.0 - qd)`.
4. Par récepteur : `att_sum = Σ` de ses att actifs ; `light_slice =
   max(LIGHT_FLOOR, att_sum / 5)` (diviser par **5 = len(samples)**, PAS par le
   nombre d'actifs — réplique le gather où les masqués comptent comme 0) ;
   `acc[ref] += light_slice * w`.

Après les tranches : `self.received[ref] = acc[ref] / total_w` pour chaque récepteur.

⚠️ **Cas `not slices`** (nuit polaire, déjà géré avant) : inchangé.
⚠️ L'ordre de multiplication par échantillon DOIT être l'ordre de `order`
   (hauteur décroissante) → c'est garanti en itérant `order` tel quel. NE PAS
   re-trier les candidats autrement.

## Golden attendu

**INCHANGÉ** — `python3 -m tests.test_golden` doit rendre `24ec11e7…`
(exactement le hash actuel). Si le hash bouge, le scatter n'est PAS bit-identique
→ bug d'indexation bbox/cellule → corriger, ne JAMAIS re-figer.

## Vérifications (dans l'ordre)

1. `python3 -m tests.test_scatter_lumiere_recue`  → PASS (équivalence bit-à-bit).
2. `python3 -m tests.test_scatter_lumiere_sol`     → PASS (non-régression sol).
3. `python3 -m tests.test_golden`                  → hash `24ec11e7…` INCHANGÉ.
4. Suites lumière/ombre existantes vertes (`test_lod_ombre`, `test_ombre_maison`,
   `test_phototropisme` si présentes) — lancer `python3 -m tests.<nom>`.
5. Mesure gain : `python3 -m tools.profile_monde --week 104` — `covering` doit
   chuter dans la table cProfile (idéalement sortir du top), tick lourd en baisse.
   Consigner le chiffre avant/après dans `00_etat.md`.

## Ce qu'il NE faut PAS faire

- NE PAS toucher la boucle lumière-SOL (déjà scatter, verrou D32).
- NE PAS fusionner les deux boucles (sol + reçue) en une passe — tentant mais
  risqué pour la bit-identité ; garder DEUX passes claires (fusion = optim future).
- NE PAS modifier `SHADING_POWER_MIN`, le LOD, ni le cache géométrique.
- NE PAS toucher `sim/clonal.py` (cap démographique = hors périmètre, dette D71).
- NE PAS relever la bande de taille : si `light.py` dépasse, scinder l'index.
- Zéro RNG, zéro changement de comportement observable (philo #3).

## LDC

Après coup : `python3 tools/compte_ldc.py data/code/fields/light.py
data/code/fields/light_index.py` — les deux doivent rester 🟢 (≤300). Sinon scinder.
