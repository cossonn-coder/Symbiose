# Sprint PERF VUE — état partagé

> Conception FIGÉE le 2026-10-19 (`/conception`, après le F5 raté de D106) →
> [`docs/perf/lod/conception_perf_vue.md`](../../../../docs/perf/lod/conception_perf_vue.md)
> (LIRE AVANT TOUT TRONÇON : mesures F5, diagnostic vérifié, décisions 1-8, table des tailles).
> **Golden jamais re-figé** : référence `22768f33…` (`cd data/code && python3 -m tests.test_golden`).
> Seul code Python touché : le peintre de vie macro (②, perception pure) + version du pont.
> Suite prévue : sprint « plante assemblée » (Nico, 2026-10-19).

## Décisions clés (Nico, 2026-10-19)
- **Critère nominal** (PC Nico : i5-4200H 2 cœurs, iGPU HD 4600, `gl_compatibility`) : à 60 s par
  semaine, **60 FPS à ×4** avec vent et animations à vitesse normale ; 30 FPS de ×0,5 à ×2.
- **Mode test accéléré** : au plus vite selon la machine, aucune image > 100 ms.
- **Étalonnage** : un run du banc sur le PC de Nico en fin de ① ; ensuite validation par mesure,
  F5 final = ressenti seul.
- **Vie macro** : 1 individu par espèce et par tuile + points chauds + grappes coloniales ;
  taille réelle, visible au palier où ≥ 1 px ; lombric jamais ; pixels fixes, animés sur signal ;
  un lot par tuile ; champ de population intact.
- **D109 (d)** au minimum ; **pleine résolution** mesurée seulement.

## Carte des tronçons
| # | Kickoff | Contenu | Golden | État |
|---|---|---|---|---|
| ① | `01_banc_etalonnage.md` | banc du jardin réel + instrument + étalonnage PC | intact | à faire |
| ② | `02_vie_macro.md` | peintre D2 + points chauds + taille réelle, lot par tuile, fuite | intact (pont 0.5.45) | à faire |
| ③ | `03_ombres_lot.md` | ombres en lot par tuile | intact | à faire |
| ④ | `04_cadence_acoups.md` | cadence adaptative, priorité serveur, à-coups, D109 | intact | à faire |
| ⑤ | `05_vue_bilan.md` | pleine résolution mesurée, bilan converti PC, F5 ressenti | intact | à faire |

## Mesures
(à remplir par ① : tableau de référence VM ; puis rapport d'étalonnage de Nico)

## §REPRISE
Lire `CLAUDE.md` + ce fichier + la conception, puis le prochain kickoff « à faire ».
Lancement : `/sprint-auto sprint_perf_vue`.
