## 2026-06-13 — Sprint planter/arroser · Session B : `arroser` + modèle « eau » (asphyxie) — golden RE-FIGÉ T0+T1 (maîtrisé)

Second geste de base + le **miroir HAUT de la sécheresse**. `arroser` apporte
de l'eau au plot ; au tick, l'apport **redescend** (évaporation × drainage) et un
**excès soutenu** finit par asphyxier — symétrique exact de la gradation
sécheresse existante (`drought_memory`).

**Geste `arroser(gs, player, eco, r, c, urgence=False)`** (`sim/actions.py`) :
`+DOSE_ARROSAGE` (0.5) sur l'humidité du plot, **cumulatif, plafonné à 3.0** ;
coût **`MODERE`** binaire (refus si Vigueur insuffisante, champ INTACT), **×
`URGENCE_MULT`** en réaction de saison (cf gradation préparation/réaction de la
philo météo). Nouvelles entrées `COUTS["arroser"]=MODERE` /
`OBJETS_TOUCHES["arroser"]=("arrosage","arrosoir")`.

**Modèle eau au tick** (`fields/ecofields.py`) :
- **Drainage par sol** : `DRAINAGE_PAR_SOL` (terre 0.993 = référence/fallback,
  argile 0.997 retient, sable 0.985, roche 0.975). `tick_hydrology(soil_type)`
  prend le coefficient du sol — l'argile garde l'eau plus longtemps que la terre.
- **Asphyxie palier 1 (uptake)** : au-dessus de `HUM_EXCES` (2.3) l'uptake d'eau
  baisse ∝ excès jusqu'à un **plancher** (`ASPHYXIE_UPTAKE_FLOOR` 0.5 : racines
  réduites, pas mortes). **Réversible** (effet sur l'excès courant, pas mémoire).
- **Asphyxie palier 2 (santé)** : `asphyxie_memory` (miroir de `drought_memory`,
  même lerp 0.05) monte sous engorgement soutenu ; au-delà de
  `ASPHYXIE_HEALTH_SEUIL` (0.10), tirage **déterministe** `_hash_noise` (canal
  `week*7`) → santé ↓, possible **mort « asphyxié »**. Réversible : assécher fait
  retomber la mémoire.
- **Stagnation « noyé »** : `ok_hum` borné par le HAUT à `HUM_NOYE` (2.6) → la
  croissance se bloque aussi par excès d'eau (message « noyé », miroir « sec »).

`asphyxie_memory` ajouté à `PlantInstance` mais **PAS au digest golden** (état
interne, comme `drought_memory`).

**⚠️ Re-figeage MAÎTRISÉ — T0 a bougé AUSSI** (`16a1b937…` → `7ee907d3…`). La
conception §5 supposait « T0 terre n'atteint jamais `HUM_EXCES`, reste bit-à-bit
identique ». **Prémisse FAUSSE** : la terre culmine à **2.636** (semaine 46) par
accumulation `soil_memory` + rétention → l'asphyxie palier 1 mord aussi sur T0.
Je n'ai PAS re-figé en silence (le sprint l'interdit quand T0 bouge) : surfacé à
Nico, qui a choisi l'**Option A** — accepter l'asphyxie **globale**, re-figer
**T0+T1**, **garder le calibrage figé** (`HUM_EXCES`=2.3, on ne le remonte pas
pour épargner la terre). Dérive **tracée et attribuée à 100 % au modèle eau**
(rien en semaine 1 ; cascade palier-1 → uptake → fertilité/humidité résiduelles →
croissance → ~5 santé/stade ; aucune fuite vers d'autres systèmes). Contraste
qualitatif **préservé** : T0 terre ~10 % des semaines > 2.3 (2/208 > 2.6), T1
argile ~43 % (69/208 > 2.6) — argile ≫ terre, comme attendu.

**Garanties :** `test_eau` **20/20** (arroser champ/coûts/refus, transitoire,
drainage terre vs argile, asphyxie uptake réversible, asphyxie santé réversible,
stagnation noyé). `test_senescence` PASS — **fixture migrée** terre/hum 1.5 (l'ancien
argile/hum 2.5 tuait désormais le pommier asphyxié à 27 ans avant la sénescence à
49+ ; c'était la fixture à corriger, pas le modèle — pommier meurt bien de
sénescence à 59.8 ans). Golden re-figé `7ee907d3…`, `main.py` tourne propre.

**Reste sprint :** Session C (pont `sim_server.py` route planter/arroser +
banque-joueur exposée au snapshot, bump `ENGINE_VERSION` 0.3.2→0.3.3).
