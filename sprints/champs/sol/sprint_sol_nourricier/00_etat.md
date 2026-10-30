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
| ① | `01_recharge_sol.md` | re-figé `7791bfb8…` | **FAIT** 2026-10-30 |
| ② | `02_croissance_nutrition.md` | re-figé annoncé | à faire |
| ③ | `03_voix_justes.md` | inchangé | à faire |
| ④ | `04_mare_nord_est.md` | inchangé | à faire |
| ⑤ | `05_vue_mare_voix.md` | inchangé | à faire |

## Notes de tronçon
(chaque tronçon : fait, mesures avant/après, hash golden, écarts au kickoff)

### ① Recharge + lessivage lié à l'eau — FAIT (2026-10-30, non commité)
- `nutriments.py` : `equilibre_roche(soil_type)`, `recharge(stock, eq, taux)` (purs) ;
  `leach_factor(…, drainage_norm=1.0)` pondère la part passive par l'eau drainée.
- `matiere_organique.tick_decomposition(recharge_roche=True)` : lessivage × drainage,
  puis recharge APRÈS lessivage et AVANT l'uptake (étape 8) → rien n'annule la recharge
  avant lecture. Équilibre = `soil_type` (roche), jamais la valeur initiale du plot.
- `constants.py` : `RECHARGE_DEMI_VIE_ANS = {N 0.2, P 0.5, K 0.25}` → `RECHARGE`.
- **Écart conception (à valider par Nico)** : les demi-vies visées (N 1 an, K 2-3 ans,
  P 5 ans) ne tiennent PAS la cible ≥ 40 % : avec elles, NPK méd. an 2 [seeds 42/1/2,
  n=3] N 0,12-0,30 / K 0,05-0,38 (≈ 12-17 % d'éq. pour N). Le prélèvement de ~700-1 000
  plantes impose `stock ≈ eq − prélèvement/RECHARGE` → remontée ~5-10× plus rapide
  retenue (N ≈ 10 sem., K ≈ 13 sem., P ≈ 26 sem., hiérarchie N > K > P gardée).
- **Conteneurs** : `world/container.py` passe `recharge_roche=False` (pas de roche
  sous un pot → le substrat s'épuise vraiment ; non prévu au kickoff).
- Mesures (`mesure_faim.py`, 156 sem.) — NPK méd. tuiles brut, s104 (an 2) :
  avant [seed 42] 0,03/0,29/0,01 ; après 42 : 0,62/0,37/0,61 · 1 : 0,73/0,65/0,73 ·
  2 : 0,47/0,55/0,61. Ratio stock/équilibre roche (méd. tuiles), minimum sur an 2
  (s104-s156) [seeds 42/1/2, n=3] : N ≥ 0,48 · P ≥ 0,61 · K ≥ 0,56 → cible ≥ 0,40 tenue
  (aussi en an 1, min N 0,42 seed 2 s78). Jachère : test_lessivage cas 8, N 0,10 → éq.
  comblé ≥ 50 % en 52 sem. (cible tenue largement avec 10 sem. de demi-vie).
- Effet en jeu : plantes plus nombreuses (an 2 seed 42 : 702 → 988) ; mais `qi méd`
  retombe ~0,00-0,03 en an 3 et « faim » reste la voix dominante (P cité surtout) —
  attendu, c'est l'objet de ②/③.
- Golden `fecccded…` → **`7791bfb8cb5d1342084a21fb6bb5250eeaf536e76e187cdb88cd420b6038088e`**
  (n/p/k du smoke changent — objet du tronçon). `population_hash.txt` re-figé avec
  (`a60c4a31…` → `b3ff9d4b…`, même cause). Suites `tests/test_*.py` toutes vertes.
- Tests adaptés : `test_lessivage` (cas 1-7 isolent le lessivage avec
  `recharge_roche=False` ; cas 2/6 réécrits : sans drainage rien ne part ; + cas 8-9
  recharge). `test_scatter_lumiere_sol` : sa référence gather ignorait le LOD émetteur
  D67 (`SHADING_POWER_MIN`) — bug latent du test révélé par le nouveau monde, corrigé.
- **Pré-existants (hors ①, constatés avant modif)** : `tests/bancs/test_edaphique`
  plante (IndexError, témoin carence sans plante) ; `tests/bancs/test_succession` 4/6.
  ⚠ pour ② : le banc `carence_npk` (n=p=k 0,05) va désormais REMONTER vers l'éq. en
  12 sem. (oracle « n < 0,3 » faux) → le banc devra couper la recharge ou se réviser.

## §REPRISE
Lire `CLAUDE.md` + ce fichier + le kickoff du premier tronçon « à faire » (② après
commit de ①). Golden courant `7791bfb8…`.
Lancement : `/sprint-auto sprint_sol_nourricier`.
