## 2026-06-14 — Sprint décompo & compost · sous-sprint ② · **Phases B & C** : squelette persistant + abscission — golden RE-FIGÉ LARGE (maîtrisé) — ② CLOS

Suite directe de la phase A. Le mort ne disparaît plus : il **persiste comme
squelette** et rend sa matière au sol en deux temps (tissus mous tout de suite,
bois lentement), et les caducs **larguent leur feuillage en automne**.

**État post-mortem** (`plants/base.py`) : `morte`, `stade_mort` (`""`/`seche`/
`couchee`), `bois_restant`, `semaines_mort` — inertes tant que la plante vit
(`is_alive ≡ health > 0` inchangé). **`deposer_mort(plant, eco)`**
(`sim/effects.py`, **idempotent** sur `morte`) remplace les `add_necromass` aux
sites de mort : dépose la fraction molle `biomass × (1 − frac_bois)` en
`tissu_mort`, marque `morte`, charge `bois_restant = biomass × frac_bois`.
`frac_bois_mort` = `FRAC_BOIS_MORT`=0.45 **seulement** pour les ligneuses
(`age_curve`), 0 sinon (une herbacée n'a pas de tronc à fragmenter).

**Squelette persistant** : la mort ne retire **plus** la plante de `tile.plants`.
Nouveau `_tick_skeletons` (`engine.py`, étape 16b, **APRÈS tous les sites de
mort** du tick) : `seche`→`couchee` après `T_SECHE`=6 sem, fragmente
`bois_restant × FRAG_RATE(0.04) × decomp_speed(r,c)` en litière `bois`/sem (la
bioturbation des vers accélère), et c'est le **seul point de retrait** (filtre
`is_alive or (morte and bois_restant>1e-9)` → herbacées retirées le tick même,
ligneuses une fois le bois épuisé). Bornage garanti, zéro accumulation.

**RISQUE #1 tranché = `SILHOUETTE_SECHE`=0.30** (`light.py`) : un squelette
debout (`seche`) projette une ombre de **tronc nu dégressif** (pas la canopée
pleine) ; couché ou herbacée retiré → rien. **Abscission d'automne (C.1)** :
`_abscission` (étape 15b, semaines `ABSCISSION_WEEKS`=(38,39)) — les caducs
**vivants** larguent `current_height × NECROMASS_PER_CM × ABSCISSION_FRAC(0.15)`
en `feuille`. **`ecraser`-squelette (C.2)** : sur un mort, `seche`→`couchee` +
largue `bois_restant × ECRASER_FRAG_BOOST(0.50)` d'un coup (on shoote dans le
tronc sec, il se casse). `deraciner` route aussi par `deposer_mort`.

**Golden RE-FIGÉ LARGE — maîtrisé, déterministe h1==h2** :
- smoke `tests/test_golden.py` : `f75d1c21… → 908f591bee5b45736bc3e542253c3807a81e5551fcb0e50ab8703446df5d11b6`
- champ population `tests/test_population.py` : `9f351303… → 435e6f72c220a2d19daed00712d09dc6c2d5d6f129066bd7ea3f37b99f557a61`

**Cause de la dérive (diagnostiquée par diff COMPLET old↔new via `git stash`)** —
la dérive est large (toute la trajectoire de succession bouge) mais **entièrement
explicable et conforme au design** :
1. **PRINCIPALE** — *toute* mort dépose désormais sa nécromasse. L'ancien
   `_resoudre_conflits` (étape 12, AVANT `apply_disturbances`) finissait par un
   filtre **inconditionnel** `tile.plants=[… if is_alive]` qui balayait
   **silencieusement, sans dépôt**, les morts survenues *entre* la sénescence et
   les conflits — typiquement la **Tomate tuée par le mildiou familial dès la
   semaine 3** de chaque printemps (elle était retirée sans rendre de matière au
   sol). En retirant ce filtre (phase B), la morte persiste jusqu'à
   `apply_disturbances` qui la dépose. Résultat : +nécromasse `herbace` aux plots
   Tomate (2,2) de T0 **et** T1 chaque printemps → cascade fertilité → succession
   sur 2 ans (≈ l'essentiel de la dérive). **C'est la correction d'un trou** (le
   design ① / phase A dit « toute mort dépose ses tissus mous »), pas une
   régression.
2. **SECONDAIRE** — abscission du pommier (`feuille` aux semaines 38/39 puis 90/91).
3. **Fragmentation `bois`** : **0 occurrence** dans le golden (aucune ligneuse n'y
   meurt — le pommier survit les 2 ans). La fragmentation est validée ailleurs par
   `test_senescence` (pommier mort de sénescence à 59.8 ans, exit 0, sans casse).
4. **Silhouette** : jamais déclenchée par le golden (aucun squelette n'y persiste
   d'un tick au suivant).

**Tests verts** : golden, population, vigueur 135, croissance 67, competition 14,
eau 20, génétique 20, maîtrise 35, maîtrise_detection 20, auxiliaires, signes 8,
ombre_maison 4, phototropisme 11, planter 18, sim_server 113, **sénescence**
(exerce la fragmentation ligneuse + la silhouette) ; `main.py 5` exit 0 (30 ans
= inutilement long pour un anti-crash, le grand monde 8 tuiles coûte ~minutes —
dette perf D32 LightField).

**Sous-sprint ② CLOS** (A + B + C). **Suivant** : ③ organes-fruits traçables
(`manger` ciblé, maturité, chute — absorbe D19), puis ④ attraction animale, ⑤
structures posables (bac à compost / pile à bois), ⑥ vue Godot (différé). Écrire
`03_*.md` avant d'attaquer ③. Reprise : `00_etat.md` §REPRISE.
