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
| ① | pH socle (champ hérité + dérive, aucun lecteur) | pH §2.1 | NEUTRE | ⬜ |
| ② | N/P/K socle (champs posés, uptake lit encore `fertilite`) | NPK §2.1 | NEUTRE | ⬜ |
| ③ | Bascule uptake **Liebig** (retrait `fertilite`, lessivage diff., CEC, signature) | NPK §2.3 | **LARGE** | ⬜ |
| ④ | pH → lockout (cloches dispo + chlorose) | pH §2.2 | maîtrisé | ⬜ |
| ⑤ | Fenêtres pH par espèce (noyau) + indicatrices acidité | pH §2.3 | ~neutre | ⬜ |
| ⑥ | Amendements pH (rondelles `chaux`/`soufre`) | pH §2.4 | NEUTRE | ⬜ |
| ⑦ | Faim d'azote (bois/BRF + substrat usé champignons) | NPK §2.7 | maîtrisé | ⬜ |
| ⑧ | Structure `structure_sol` (infiltration/asphyxie/uptake) | structure §2 | maîtrisé | ⬜ |
| ⑨ | Vue : overlays nouveaux champs + indices visuels (chlorose) | — | NEUTRE (vue) | ⬜ |

## §REPRISE

Sprint non démarré. Conception figée le 2026-06-19, aucun code écrit. Commencer par
vérifier que git est à jour, créer la branche, puis lancer `01_ph_socle.md`.
