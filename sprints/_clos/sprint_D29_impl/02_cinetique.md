# Sprint D29·i2 — Cinétique hormonale dans le tick (mapping §C.4) (Python)

> **Kickoff autosuffisant.** Démarrage à froid : tu reprends sans contexte
> préalable. Lis ce fichier en entier, puis les sources citées, puis exécute.
> Carte blanche (conception figée) : implémente sans re-valider chaque étape,
> rends compte après. Français + pédagogie (Nico vient du C/Python embarqué,
> expert simulation ; débutant Godot/C# en frontend). **Pré-requis : i1 fait.**

## Ce que c'est, en une phrase

Cœur du sprint. La boucle de croissance **lit les 2 scalaires** posés en i1 et en
**fait émerger l'architecture** (port plus bas/large, feuillage dense, mise à fruit)
+ la **cinétique** (débourrement quand l'apex est coupé, rétablissement de la
dominance, bornes). On ne **branche pas encore** l'action `tailler` (i3) : ici on
**injecte l'état hormonal directement** dans les tests pour valider le mapping et la
dynamique — comme le tronçon i1 du D12 injectait les preuves par API avant de
brancher la détection.

**Le golden écolo NE bouge PAS** (`c950f06c…` / `b005d9ba…`). C'est **le** critère
de design #1 (§C.3) : au repos `dominance_apicale=1.0` / `ramification=0.0`, et
**tout** mapping est écrit pour que `f(repos)=identité` (×1 / +0). Le golden est une
succession **sans joueur** → personne ne taille → tous les scalaires restent au
repos → le tick lit un **no-op strict**. **Si un hash bouge, le mapping n'est pas
neutre au repos = bug de design**, pas un re-figeage.

## Lis d'abord, dans cet ordre

1. `data/code/CONCEPTION_HORMONES.md` — **§C.3** (repos = identité, critère #1, à
   re-vérifier à chaque choc), **§C.4** (le mapping complet : tableau variable →
   modulation, + les 4 étapes de cinétique), **§G** (les placeholders nommés :
   `DEBOURR_RATE`, `DOMINANCE_RECOVERY`, `RAMIF_MAX`, `K_R`, `K_H`, seuil mise à
   fruit — tu les **nommes** comme constantes, valeurs **post-test**, pas de
   réglage fin). **§C.1/C.2** pour rappel de la sémantique des 2 scalaires.
2. `sprints/sprint_D29_impl/00_etat.md` — découpage + le **point ouvert i2** (forme
   du modèle de mise à fruit / point d'insertion repro).
3. Code — **les seams exacts à moduler** (lecture déjà faite par le tick) :
   - `data/code/plants/base.py:292` `height_at` (× growth_factor × gène) — y appliquer
     `× (1 − K_H·ramification)`.
   - `data/code/plants/base.py:300` `canopy_radius_at` — y appliquer `× (1 + K_R·ramification)`.
   - `data/code/plants/base.py:312` `foliage_density_at` — `↑ avec ramification`, borné ≤ 1.
   - `data/code/sim/engine.py:306` la maj de `growth_factor` (`_tick`*) — redirection :
     croissance verticale bloquée → alimente `ramification` ; **et** la cinétique
     (étapes §C.4 ci-dessous) s'écrit là, une fois par tick et par plante.
   - `data/code/sim/reproduction.py` — point d'insertion du **modèle de mise à fruit**
     (`reproduction_rate` effectif ↑ au-delà d'un seuil de `ramification`).

## Périmètre

### A. Constantes (placeholders nommés, valeurs post-test)
En tête de module (engine ou un petit bloc dédié), constantes neutres-au-repos :
`DEBOURR_RATE`, `DOMINANCE_RECOVERY`, `RAMIF_MAX`, `K_R`, `K_H`, `SEUIL_MISE_A_FRUIT`.
Choisis des valeurs **plausibles** (cinétique sur ~N semaines) mais documente
qu'elles sont **à calibrer jeu en main** — ce ne sont pas des chiffres figés.

### B. Mapping empreinte (§C.4, sur les classmethods de base.py)
Chaque modulation **DOIT** donner l'identité à `ramification=0` :
- `height_at` : `× (1 − K_H·ramification)` → ×1 au repos.
- `canopy_radius_at` : `× (1 + K_R·ramification)` → ×1 au repos.
- `foliage_density_at` : `↑ avec ramification`, clamp `≤ 1` ; inchangé au repos.
Garde-fou : factorise un helper si tu veux, mais **n'introduis aucune lecture de
`ramification` qui ne soit pas multipliée par 0 au repos**.

### C. Cinétique (§C.4, dans le tick — `sim/engine.py`)
Une fois par plante par tick, **sans RNG** (déterminisme philo #3 ; variabilité
éventuelle via `_hash_noise(position, seed)` uniquement) :
1. potentiel de débourrement `p = 1 − dominance_apicale` (≥ 0).
2. `ramification = min(RAMIF_MAX, ramification + DEBOURR_RATE · p)`.
3. `dominance_apicale = min(1.0, dominance_apicale + DOMINANCE_RECOVERY · (1 − dominance_apicale))`.
4. clamps : `dominance_apicale ∈ [0,1]`, `ramification ∈ [0, RAMIF_MAX]`.
**Au repos** (`dom=1`) : `p=0` → ramif inchangée, dom reste 1 → **no-op strict**.
**Gate `reponse_taille`** : la cinétique/mapping ne s'appliquent que si l'espèce
n'est pas `"insensible"` — une insensible reste rigoureusement identité même si on
lui forçait un scalaire (double sécurité golden).

### D. Mise à fruit (point ouvert — défaut sobre, signaler)
Au-delà de `SEUIL_MISE_A_FRUIT` de `ramification`, le `reproduction_rate` effectif
monte (le bois latéral porte les fruits, §A.3). **Défaut sobre** : modèle linéaire
borné inséré dans `reproduction.py`, neutre sous le seuil et à `ramification=0`.
Documente le choix d'insertion dans `00_etat.md` (c'est le point ouvert i2).

### E. Test — `tests/test_hormones.py` (étendre i1)
**Injecte l'état hormonal à la main** (pas de `tailler` encore) :
1. `ramification=0` / `dom=1` → `height_at`/`canopy_radius_at`/`foliage_density_at`
   **identiques** à avant (capture des valeurs de référence).
2. `dom=0` → après N ticks : `ramification` monte puis sature à `RAMIF_MAX` ; `dom`
   remonte vers 1.0 (rétablissement) ; débourrement s'arrête quand `dom→1`.
3. `ramification>0` → radius ↑, height ↓, foliage ↑ (bornés), repro ↑ au-delà du seuil.
4. Espèce `"insensible"` avec scalaires forcés → **identité** (gate respectée).
5. **Déterminisme** : même état + mêmes ticks → mêmes trajectoires (2 runs égaux).

## Hors périmètre (NE PAS faire ici)
Action `tailler` (i3). Migration Tomato/AppleTree (i3). Marqueur `🌿` (plus tard).
Aucun gain/coût Vigueur (i3). Ne **pas** rouvrir D19 (organes fins).

## Vérification (success criteria)
```
cd data/code
python3 -m tests.test_hormones      # étendu, doit passer
python3 -m tests.test_golden        # DOIT rester c950f06c… / b005d9ba…  (INTACT — critère dur)
python3 -m tests.test_genetique && python3 -m tests.test_auxiliaires
python3 main.py                     # tourne sans crash
```
Si le golden bouge : un mapping n'est pas neutre au repos → corrige le mapping, **ne
re-fige jamais**. Mets à jour `00_etat.md` (i2 ✅ + point ouvert tranché), commit,
`/clear`, lance `03_action_tailler.md`.
