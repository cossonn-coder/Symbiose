# Sprint DÉPART DU JARDIN (D140 A+B+C) — état

> Conception FIGÉE le 2026-11-18 : `docs/vegetal/genetique/conception_depart_jardin.md`
> (à lire en entier). Hors périmètre : trèfle (D140 D, non mesuré — Nico), éclaboussures
> de pluie et Ctrl+molette des graines (D140 E-F).

## But
Un jardin qui démarre vivant et réaliste : pâturin anémophile et autogame, gènes muets
gratuits, limites de froid physiquement possibles, mort par froid consignée, monde `full`
ouvert mi-mai avec une plante mûre de chaque espèce, semis d'intérieur et repiquage.

## Décisions clés (Nico, 2026-11-18)
- A : pâturin = vent + autofécondation ≈ 0,9. B : caractère non exprimé (aucun lecteur
  pour l'espèce) = coût nul, gène porté et hérité.
- C : ouverture `full` en **semaine 10** (juste après les saints de glace) ; **au moins
  une plante MATURE de chaque espèce du catalogue**, arbres compris (âge = première
  fructification) ; garde-fou catalogue ⊂ `full` ; semis (existe) + graines déjà
  semées ; pot dans la maison (chaud, peu de lumière) + geste `repiquer` (choc de
  repiquage ∝ racines à l'étroit) ; repiquage différé = choix du joueur, l'automate
  repique quand les nuits passent au-dessus de la limite de froid.
- Gel impossible au-dessus de ≈ −0,5 °C ; tournesol non sensible au froid sans gel ;
  rythme du froid sans gel (`FROID_LESION_K`) inchangé.

## Faits vérifiés au code (2026-11-18)
- `full` = 15 espèces sur 52 ; départ via `BANC_WEEK_DEPART.get(config, 1)` (commands.py).
- 68 cultivées repiquées s1 mortes en 2 semaines [seed 42] ; nuits s1-s9 entre −2,8 et
  +5 °C, > 7 °C dès s10.
- `lim_gel` tomate +2,8 °C, basilic +1,2, poivron −4,4 (gène `rusticite_froid` de variété).
- Semis (`planter` → `GrainEnAttente` + `bell(T_sol)`) et pots (`deplacer_pot`) existent.

## Golden
Départ `db4d6b75…`. ① **RE-FIGÉ annoncé** · ② **RE-FIGÉ annoncé** (si tendres du smoke
touchés) · ③④⑤⑥ **INTACT**.

## Tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_paturin_genes_muets.md` — pâturin + gènes muets | à faire |
| ② | `02_froid_tendres.md` — borne du gel, audit des tendres, chronique | à faire |
| ③ | `03_monde_full_complet.md` — semaine 10, 52 espèces mûres, garde-fou, perf | à faire |
| ④ | `04_semis_interieur_repiquer.md` — pot dans la maison + `repiquer` | à faire |
| ⑤ | `05_automate_repiquage.md` — repiquage différé par l'automate | à faire |
| ⑥ | `06_vue_banc.md` — palette, pots visibles, banc `depart_jardin`, clôture | à faire |

## REPRISE
Lire `CLAUDE.md`, ce fichier, puis le kickoff du premier tronçon « à faire ».
