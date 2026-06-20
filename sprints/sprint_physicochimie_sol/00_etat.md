# SPRINT PHYSICO-CHIMIE DU SOL — état partagé

> Conception figée (3 docs par volet) :
> `docs/conception/CONCEPTION_SOL_PH.md` (porte l'ordre global §6),
> `docs/conception/CONCEPTION_SOL_NUTRIMENTS_NPK.md`,
> `docs/conception/CONCEPTION_SOL_STRUCTURE.md`.
> Branche suggérée : `sprint/physicochimie-sol`. Python depuis `data/code/`.
> Boucle : lancer `0N` → coder → vérifier golden → MàJ ce fichier → commit → `/clear`
> → écrire `0N+1` → lancer. **Vérifier git à jour avant de démarrer.**

## Objectif

Donner au sol une vraie chimie : **pH** (maître-régulateur), **nutriments N/P/K
distincts** (`fertilite` supprimé, loi de Liebig) et **structure/compaction**
(`structure_sol`, dette D30 absorbée). Tout émerge par flux → contrainte → réponse
(philo #2/#3/#5).

## Décisions (2026-06-19, avec Nico) — voie FIDÈLE

- Nutriments : **NPK COMPLET** (`n`/`p`/`k`), `fertilite` **supprimé net**,
  croissance = **loi du minimum de Liebig**.
- pH : champ hérité du `soil_type`, dérive décennale ; lockout en cloche (P étroit
  + chlorose alcaline) ; fenêtres d'espèce = **noyau démonstrateur** ; amendements
  = **rondelles `chaux`/`soufre`**.
- **Faim d'azote DANS le sprint** : bois/BRF **+ substrat usé de culture de
  champignons** (crochet futur acteur champignon).
- CEC dérivée (`soil_type`+`om_stable`) ; `SOIL_SIGNATURE` rendu explicite.
- Structure : **Option B `structure_sol`** (champ dédié), pas l'option A sobre.
- Golden : **tactique neutre-d'abord** (validée au thermique), gros re-figé isolé
  au tronçon 3.

## Tronçons (ordre global)

| # | Tronçon | Doc | Dérive golden | Statut |
|---|---------|-----|---------------|--------|
| ① | pH socle (champ hérité + dérive, aucun lecteur) | pH §2.1 | NEUTRE | ✅ |
| ② | N/P/K socle (champs posés, uptake lit encore `fertilite`) | NPK §2.1 | NEUTRE | ✅ |
| ③ | Bascule uptake **Liebig** (retrait `fertilite`, lessivage diff., CEC, signature) | NPK §2.3 | **LARGE → `87ed27ae…`** | ✅ |
| ④ | pH → lockout (cloches dispo + chlorose) | pH §2.2 | maîtrisé | ⬜ |
| ⑤ | Fenêtres pH par espèce (noyau) + indicatrices acidité | pH §2.3 | ~neutre | ⬜ |
| ⑥ | Amendements pH (rondelles `chaux`/`soufre`) | pH §2.4 | NEUTRE | ⬜ |
| ⑦ | Faim d'azote (bois/BRF + substrat usé champignons) | NPK §2.7 | maîtrisé | ⬜ |
| ⑧ | Structure `structure_sol` (infiltration/asphyxie/uptake) | structure §2 | maîtrisé | ⬜ |
| ⑨ | Vue : overlays nouveaux champs + indices visuels (chlorose) | — | NEUTRE (vue) | ⬜ |

## §REPRISE

**① CLOS le 2026-06-20.** Champ `ph` (GridField par plot) ajouté à `EcoFields`,
**hérité du `soil_type`** (table `PH_PAR_SOL` : terre 6.8 / argile 7.0 / sable 5.8
/ roche 7.6) et dérivant lentement (`tick_ph`, lerp inertie 0.02 ; calcul PUR isolé
dans `fields/ecofields/ph.py` façon thermique). Acidification par litière (`om_fresh`
÷ `LITIERE_REF`) + lessivage (humidité÷3, faute de drainage par plot). `cec=0`
(volet NPK absent). Câblé dans `boucle.py` étape 4c (après décompo). **Aucun lecteur**
→ **golden NEUTRE, hash inchangé `f7e1a9b4…`**. `soil_type` ajouté au dataclass
`EcoFields` + param `init_eco` ; câblé dans `test_golden.build_world` et `main.build_tile`
(simserver hérite via ces fabriques). Exposé dans `get_field` (overlay debug gratuit).

Vérifié : héritage terre≠sable, dérive lente (~0.05 sur 10 ticks), plot avec litière
s'acidifie plus que le plot nu. `main.py` OK, golden PASS.

⚠️ **Taille** : `container.py` 387 ldc de code (+10 d'orchestration : champ, init,
registre, méthode déléguante). Il était DÉJÀ à 377 avant ① (au-dessus du seuil ~350).
Le calcul est dans `ph.py` (§7 conception respecté). Un éclatement d'`EcoFields`
serait un chantier à part — à arbitrer avec Nico, hors périmètre du sprint.

**① CLOS** (détail conservé ci-dessus).

**② CLOS le 2026-06-20.** Trois `GridField` `n`/`p`/`k` ajoutés au dataclass
`EcoFields`, **hérités du `soil_type`** (table `NUTRIENT_INIT_PAR_SOL` dans
`constants.py` : terre (1.0, 0.8, 0.9) / argile (0.9, 0.9, 1.1) / sable
(0.5, 0.4, 0.4) / roche (0.4, 0.6, 0.5)), `max_val=3.0` comme l'ancien
`fertilite`. Init dans `__post_init__` après le bloc `ph`. **Aucun tick, aucun
lecteur, aucun écrivain** : `fertilite`, l'uptake, la minéralisation, `soil_memory`
et les signatures restent INTACTS. Exposés dans `get_field` (`"n"`/`"p"`/`"k"`,
overlay debug gratuit). **Golden NEUTRE, hash inchangé `f7e1a9b4…`**. Vérifié :
héritage différencié terre≠argile≠sable≠roche, valeurs constantes (pas de dérive).

⚠️ **Taille** : `container.py` passé à **398 ldc** de code (387 → 398, +11 :
3 champs + bloc d'init + 3 entrées `get_field`). Déjà au-dessus du seuil ~350
avant ② (cf. ①). Pas de calcul à isoler ce coup-ci (champs inertes). Éclatement
d'`EcoFields` = chantier à part, à arbitrer avec Nico hors périmètre sprint.

**③ CLOS le 2026-06-20 — golden RE-FIGÉ LARGE `87ed27aec24f6ca5…`** (porté
FIDÈLE : Liebig NE gate PAS `_avancer_stades`, n/p/k reprennent les rôles de
`fertilite`). `fertilite` **supprimé net** du dataclass / `get_field` /
`__post_init__` / `summary` / `__repr__`. Bascule dans `container.py` :
- `fertilite_index(r,c) = (n+p+k)/3` (grandeur lisse dérivée pour les lecteurs).
- `tick_diffusion` diffuse n/p/k (inertie `FERTILITY_INERTIA`).
- `tick_decomposition` : minéralisation **splittée par tissu** (`split_miner`,
  helper pur `nutriments.py`) ; lessivage **différencié par nutriment & CEC**
  (`leach_factor("N"|"P"|"K", cec)`, `cec_norm_at(soil_type, om_stable/5)`).
- `plant_uptake` : branche `fertilite` retirée ; bloc **BESOIN N/P/K plafonné
  par le champ** (= loi du minimum, prélèvement borné par la dispo réelle).
- `soil_memory`/`vitalite`/`succession` relisent `fertilite_index` (seuils
  intacts) ; `vigueur_plante.qi_local` lit `min(n,p,k)` (Liebig diégétique).
- `init_eco(fertilite=…)` conservé en **param de COMPAT** : si fourni, pose
  n=p=k uniforme ; sinon héritage `soil_type` (tronçon ②).
Consommateurs redirigés `"fertilite"→"n"` : `compost.EPANDRE_W`, `aleas`
(Pucerons), `boucle.py` repr, effets `inject_field` (Fabaceae+Urticaceae =
fixation N §2.6, adventices×3, compagnes), `simserver/fields`, `diag_fields_span`.
**NON touché** (décision cadrage) : `cultivees.py:205` add_rondelle `"fertilite"`
(= label de rondelle, pas un champ).

**Dérive golden inspectée & cohérente** (terre 40 sem) : n 1.0→~0.05 (mobile,
lessive + uptake), p 0.8→~0.73 (quasi immobile, minéralisé → stable), k 0.9→~0.21
(intermédiaire). Argile (CEC 0.8) retient bien mieux. **N devient le limiteur de
Liebig = attendu.** `population_hash` INCHANGÉ.

**Suites** : toutes PASS (structures 65/65, vigueur 135, croissance 67, genetique
20, maitrise 35, signes 8, + competition/planter/eau/fruits/lifecycle/catalogue_lot2/
population/attraction/ruche/evergreen/biennial/faune_dediee/alarme/auxiliaires).
**SAUF `test_senescence`** : rouge, mais **régression PRÉ-EXISTANTE** (bisection
git → commit `4b70032`, thermique ⑦ Neige+Orage : précipitations gorgent le sol →
pommier isolé asphyxié à 2.7 ans vs 59.8 attendus). **Indépendant de ③** (courbe
hum/mort identique fertilite-ancien vs NPK-nouveau, vérifié par `git stash`).
**Tracé en DETTE D39** (décision Nico 2026-06-20 : tracer + clôturer ③).

⚠️ **Taille** : `container.py` **420 ldc** de code (398 → 420, +22 : bascule
décompo splittée + lessivage CEC + bloc uptake BESOIN + `fertilite_index`).
Toujours au-dessus du seuil ~350 (cf. ①②). Calcul pur isolé dans `nutriments.py`
(10 ldc). Éclatement d'`EcoFields` = chantier à part, hors périmètre sprint.

**Suite** : lancer `04_ph_lockout.md` — cloches `dispo_i(ph)` + chlorose alcaline,
greffe dans `plant_uptake`. Cf. `CONCEPTION_SOL_PH.md` §2.2.
