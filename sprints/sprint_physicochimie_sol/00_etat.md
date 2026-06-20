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
| ② | N/P/K socle (champs posés, uptake lit encore `fertilite`) | NPK §2.1 | NEUTRE | ⬜ |
| ③ | Bascule uptake **Liebig** (retrait `fertilite`, lessivage diff., CEC, signature) | NPK §2.3 | **LARGE** | ⬜ |
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

**Suite** : lancer `02_npk_socle.md` (champs N/P/K posés, uptake lit encore
`fertilite` → golden NEUTRE). Cf. `CONCEPTION_SOL_NUTRIMENTS_NPK.md` §2.1.
