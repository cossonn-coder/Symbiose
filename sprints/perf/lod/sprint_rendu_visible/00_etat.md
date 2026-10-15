# Sprint RENDU VISIBLE (D106) — état partagé

> Conception FIGÉE le 2026-10-16 (`/conception D106`) →
> [`docs/perf/lod/conception_rendu_visible.md`](../../../../docs/perf/lod/conception_rendu_visible.md)
> (LIRE AVANT TOUT TRONÇON : diagnostic chiffré + décisions D1-D6 + échelle des paliers).
> **Vue C# pure** : `data/code/` intouché, **golden jamais re-figé** (référence
> `22768f33…`, à vérifier en tête de T1 : `cd data/code && python3 -m tests.test_golden`).

## Décisions clés (Nico)
- **D1 critère de fin** (PC Nico, HD 4600, `full`) : 60 FPS à ≥ ×4, 30 FPS à ×0,5-×2.
- **D2** semaine appliquée paresseusement hors marge (à l'entrée ou à la consultation).
- **D4** échelle cumulative : ×0,5 présence+saison · ×1 port · ×2 santé · ×4 architecture ·
  ×8 organes · ×16 symptômes fins · ×32 intime. Art NEUF, plantes toujours visibles.
- **D5** plante trop petite au palier → **tapis de son plot** ; un seul tapis (fusion
  `CouvertureLayer`).
- **D6** marge + travail hors champ pour toutes les couches ; paliers faune → sprint B.

## Carte des tronçons
| # | Kickoff | Contenu | Golden | État |
|---|---|---|---|---|
| T1 | `01_instrument.md` | F4 draw calls + bascule couches + `tools/perf_vm.sh` | intact | à faire |
| T2 | `02_sol_un_lot.md` | sol = 1 maillage/tuile, image identique | intact | à faire |
| T3 | `03_plancher_fixe.md` | souris 1×/frame, survol paresseux, plein écran à la demande | intact | à faire |
| T4 | `04_marge_paresseuse.md` | marge proportionnelle + hystérésis, semaine paresseuse | intact | à faire |
| T5 | `05_paliers_bas.md` | ×0,5/×1/×2 + tapis par plot | intact | à faire |
| T6 | `06_paliers_hauts.md` | ×4/×8/×16/×32 + cellules d'atlas par pose | intact | à faire |
| T7 | `07_banc_bilan.md` | planche des paliers F5 + bilan contre D1 | intact | à faire |

## Mesures de référence (VM llvmpipe, 2026-10-16)
×0,5 : 5,2-5,5 FPS [3 runs] ; sans sol 11,7-12,0 [3 runs] ; ×4 : 12-13 FPS [4 runs] ;
tout masqué 20-26 FPS [n=3, bruités]. ⚠️ Vérifier `uptime` avant de mesurer (load 17 vu
une fois → runs aberrants). Métrique portable = draw calls/frame (T1).

## Règles communes à tous les tronçons
- `dotnet build Symbiose.csproj` vert ; golden PASS ; **jamais** `test_epaisseur_500ans`.
- Taille : `python3 tools/compte_ldc.py <fichiers>` ≤ 300 (🟡 ≤ 400 signalé).
- Captures VM : `tools/capture_vm.sh` (cf. sprint jardin vivant `00_etat.md` §T0) ; FPS
  temps réel : `tools/perf_vm.sh` (créé en T1).
- Pas d'appel DeepSeek en routine (CLAUDE.md).

## §REPRISE
Prochaine étape : `/sprint-auto sprint_rendu_visible` → T1.
