# Sprint SOL NOURRICIER (D120) — état partagé

**Conception FIGÉE le 2026-10-30** (`/conception D120`, Nico : oui à Q1-Q3). Doc :
`docs/champs/sol/conception_sol_nourricier.md`. Golden de départ `fecccded…`
(`python3 -m tests.test_golden` depuis `data/code/`) : **re-figé au ① puis au ②
(annoncé)**, intact ③④⑤. Filet C# : `dotnet build Symbiose.csproj`.
Mesures : `mesure_faim.py` (plantes + NPK), `sonde_betes.py` (bêtes), référence
avant sprint `faim42.log` (seed 42) — lancer depuis `data/code/` avec `PYTHONPATH=.`.

## Diagnostic de départ [seed 42, n=1 run]
NPK médian 1,01/1,01/1,01 → 0,03/0,40/0,01 en 91 sem. ; croissance aveugle à N/P/K
(vitalité 0,81-0,93 avec qi 0,00) ; voix plante dite dès s0 (seuil 1,2) ; 75-100 % des
bêtes « affamées » à populations stables ; hérisson sur 619/1 188 plots (→ D119).

## Décisions clés
- Recharge lente vers l'équilibre de la roche (`NUTRIENT_INIT_PAR_SOL`) ; lessivage
  passif seulement là où l'eau draine.
- Carence = croissance escomptée (patron allélopathie sur `growth_factor`), continue,
  avec plancher ; pas de mort (D41).
- Voix plante = 1 − facteur de nutrition (même source) ; voix bête = déficit de la
  population face à sa nourriture (grille de rendu, bit-identique).
- Mare NE remplie et peuplée dans `full` (aulne, sphaigne, rossolis, moustique, libellule).

## Tronçons
| # | Kickoff | Golden | État |
|---|---|---|---|
| ① | `01_recharge_sol.md` | re-figé annoncé | à faire |
| ② | `02_croissance_nutrition.md` | re-figé annoncé | à faire |
| ③ | `03_voix_justes.md` | inchangé | à faire |
| ④ | `04_mare_nord_est.md` | inchangé | à faire |
| ⑤ | `05_vue_mare_voix.md` | inchangé | à faire |

## Notes de tronçon
(chaque tronçon : fait, mesures avant/après, hash golden, écarts au kickoff)

## §REPRISE
Lire `CLAUDE.md` + ce fichier + le kickoff du premier tronçon « à faire ».
Lancement : `/sprint-auto sprint_sol_nourricier`.
