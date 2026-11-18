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
Départ `db4d6b75…` → après ① **`98a050cf…`** (re-figé : divergence 100 % due à B —
A seul et la dérivation `_POLLEN_VIBRE_BOURDON` sont bit-identiques ; coût allégé dès s1
chez achillée, haricot, phacélie, pommier, tournesol, trèfle (gènes muets `pollen`,
`limite_froid`, `fixation_azote`, `allelopathie`) ; 1ʳᵉ divergence du log en s9 ;
`population_hash`/`vigueur_hash` intacts). ① **RE-FIGÉ annoncé** · ② **RE-FIGÉ annoncé** (si tendres du smoke
touchés) · ③④⑤⑥ **INTACT**.

## Tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_paturin_genes_muets.md` — pâturin + gènes muets | **FAIT** 2026-11-18 (golden re-figé `98a050cf…`) |
| ② | `02_froid_tendres.md` — borne du gel, audit des tendres, chronique | à faire |
| ③ | `03_monde_full_complet.md` — semaine 10, 52 espèces mûres, garde-fou, perf | à faire |
| ④ | `04_semis_interieur_repiquer.md` — pot dans la maison + `repiquer` | à faire |
| ⑤ | `05_automate_repiquage.md` — repiquage différé par l'automate | à faire |
| ⑥ | `06_vue_banc.md` — palette, pots visibles, banc `depart_jardin`, clôture | à faire |

## Acquis du ①
- Registre `plants/caracteres.py` : champ `exprime` (prédicat sur la classe, None = toutes)
  + `couteux_exprimes(cls)` mémoïsé par espèce, lu par `cout_genetique`. Muets possibles :
  `nectar` (nectar d'espèce 0), `taille_fleur`/`guide_nectar` (ni nectar ni anthères
  poricides), `pollen` (ni vent ni poricide — la phacélie aussi !), `limite_froid`
  (`t_froid_lesion` None), `fixation_azote`, `allelopathie` (effets déclarés). Universels
  vérifiés au code : `rusticite_froid`, `limite_chaud`, `parfum` (ravageurs),
  `coriacite_feuille`, `mycorhization`.
- `FAMILLES_ANTHERES_PORICIDES` (caracteres.py) = source unique ; `registry._POLLEN_VIBRE_BOURDON`
  en dérive.
- Pâturin : `pollination_mode = "wind"`, autofécondation neutre 0,9 → fécondation ≥ 0,9.
- Test : `tests/test_genes_muets.py` (18/18).

## REPRISE
Lire `CLAUDE.md`, ce fichier, puis le kickoff du premier tronçon « à faire » (②).
