# SPRINT THERMIQUE & MICROCLIMAT — état partagé

> Conception figée : `docs/conception/CONCEPTION_THERMIQUE_MICROCLIMAT.md`.
> Branche : `sprint/thermique-microclimat`. Lancement Python depuis `data/code/`.

## Objectif

Spatialiser la thermique (aujourd'hui uniforme) en la couplant au `LightField` :
T sol vs air, soleil vs ombre, évaporation différenciée, gel localisé, effet
thermique de la pluie/nuages. Tout émerge des champs déjà calculés (philo #2/#3).

## Décisions (2026-06-18, avec Nico)

- Couplage **COMPLET** : T_sol → évaporation **et** croissance **et** gel.
- **Refroidissement évaporatif** activé (chaleur latente → cercle vicieux sécheresse).
- **Inertie thermique légère** (lerp) dès ①.
- **Neige + Orage** ajoutés au catalogue (⑦).
- **Vent continu** et **rosée/hygrométrie** reportés en dette (D37, D38).
- Découpage grain **maximum** : 10 tronçons.

## Tronçons

| # | Tronçon | Dérive golden | Statut |
|---|---------|---------------|--------|
| ① | Socle T_sol diurne (surchauffe solaire + inertie lerp) + évaporation branchée | hydrologie | ✅ |
| ② | Refroidissement évaporatif (chaleur latente) | température/hydro | ✅ |
| ③ | Isolation par le couvert (litière) | température légère | ✅ |
| ④ | Nébulosité (effet thermique pluie/nuages, diurne) | température/météo | ✅ |
| ⑤ | T ressentie (mix air/sol) → croissance | croissance | ✅ |
| ⑥ | Gel nocturne localisé (couvert + nébulosité + neige protègent) | NEUTRE (smoke ne gèle pas) | ✅ |
| ⑦ | Catalogue : Neige + Orage + effets | météo (tirages) — LARGE | ✅ |
| ⑧ | Snapshot météo + carte température (Python) | NEUTRE | ⬜ |
| ⑨ | Rendu Godot des événements (pluie/neige/vent/grêle/orage) | NEUTRE (vue) | ⬜ |
| ⑩ | Heatmap température debug F6 (`FieldOverlay`) | NEUTRE (vue) | ⬜ |

## §REPRISE

**① CLOS (2026-06-18).** Champ `temperature_sol` + helper pur `fields/ecofields/thermique.py`
(container déjà à 359 ldc → calcul sorti du conteneur, méthode `tick_thermique`
déléguant). `tick_hydrology` lit désormais `temperature_sol`. Appel inséré en 2b
dans `boucle.py` (entre lumière et hydrologie). Golden **RE-FIGÉ** :
`50a6fd2d32a0341314e151994f8c24a2f0a535a9b513f459129ebcc6474cfdf4`.

⚠️ **Dérive plus large que l'invariant du kickoff** (décidée acceptée avec Nico) :
spatialiser l'évaporation cascade humidité→drought→croissance→santé→**succession**
(nombre de plantes spontanées + rondelle pollinisateur changent). PAS un bug
d'isolation (croissance/gel lisent toujours T_air) — couplage physique réel via
l'humidité. `GAIN_SOLAIRE=15` placeholder, calibrage post-test. **Conséquence pour
②→⑥ : chaque tronçon moteur cascadera de même** ; ne pas s'attendre à une dérive
« localisée » au sens strict, mais à une dérive *causalement traçable* au mécanisme.
Suites ciblées non thermiques INCHANGÉES (génétique/croissance/eau/population/…).

**② CLOS (2026-06-18).** Terme **chaleur latente** ajouté à la cible thermique dans
`thermique.py` : `cible -= REFROID_EVAP · humidité_norm` (knob `REFROID_EVAP=6.0`
dans `constants.py`). Humidité lue = fin du tick précédent (2b avant `tick_hydrology`,
voulu). Vérif mécanisme : à `lum=1.0` constant, T_sol décroît monotone quand l'humidité
monte (25.83 @hum=1.12 → 25.42 @hum=1.35) = refroidissement évaporatif isolé. Cercle
vicieux sécheresse en place. Golden **RE-FIGÉ** :
`7cfef3312f0f38a983214cef8f49f4a81e59a706e0c9501a35c1933afa9cbc70`. Suites
ciblées (eau/croissance/population/génétique) PASS. `main.py 3` OK (pas de crash).
Dérive = température/hydro → cascade succession (traçable, comme ① — attendu).

**③ CLOS (2026-06-18).** Terme **isolation par le couvert** ajouté à la cible
thermique dans `thermique.py` : `cible -= ISOLATION_COUVERT · litière_norm` avec
`litière_norm = min(1, om_fresh_at(r,c) / LITIERE_REF)` (knobs `ISOLATION_COUVERT=4.0`,
`LITIERE_REF=2.0` dans `constants.py`). Litière lue = fin du tick précédent (2b avant
décompo, voulu). Vérif mécanisme isolé (lum=1, hum=0, convergé) : litière 0 → T_sol
35.0 ; litière 2.0 (saturée) → 31.0 = −4 °C pile = ISOLATION_COUVERT ; sature à
litière ≥ LITIERE_REF. Monotone, borné. Interconnexion : litière de la décompo → thermique.
Golden **RE-FIGÉ** : `aab6c60acc3829c887e3821681a7494d355ca034fd4802ca22bc8a8ef7cf17d4`.
Suites ciblées (eau 20/20, croissance 67/67, population, génétique 20/20) PASS.
`main.py 3` OK. Dérive = température/hydro légère → cascade succession (traçable, comme ①②).

**④ CLOS (2026-06-18).** 4ᵉ et DERNIER terme de la cible thermique DIURNE :
`cible = T_air + GAIN_SOLAIRE · lum · intensité · (1 − K_NEBUL_DIURNE · nébulosité) − …`
(knob `K_NEBUL_DIURNE=0.8` + table `NEBULOSITE` indexée par `event.kind`, données PURES
dans `constants.py`). 1re fois que la MÉTÉO entre dans la carte T_sol : `boucle.py`
calcule `nebul = NEBULOSITE.get(event.kind, 0.10)` une fois/tick (scalaire, pas un champ)
et le passe à `eco.tick_thermique(saison, nebul)` en 2b. Couche respectée (`sim` importe
`fields.ecofields.constants`, table pure côté `fields`). Vérif mécanisme isolé (lum=1,
hum=0, lit=0, convergé) : nébul=0 → 35.0 °C ; nébul=0.5 → 29.0 ; nébul=1 → 23.0 (= 20 +
15·0.2, surchauffe résiduelle 20 %) — monotone, borné. Golden **RE-FIGÉ** :
`c8af9e1184aac258ba48c22a42c5548e55cb735ab51d51fbd5c03aebb0ec93cc`. Suites ciblées
(eau 20/20, croissance 67/67, population, génétique 20/20) PASS. `main.py 3` OK.
Dérive = T_sol modulée par la nébulosité hebdo (même « Beau temps » a 0.10 → toutes les
semaines bougent un peu) → cascade hydro/croissance/succession (traçable, comme ①②③).

**⑤ CLOS (2026-06-18).** Le gate de croissance ne lit plus T_air nu mais une **T
ressentie** = mélange air/sol local : dans `sim/engine/croissance.py::_avancer_stades`,
`temp = T_PLANTE_ALPHA·t_air + (1−T_PLANTE_ALPHA)·temperature_sol[r,c]` (knob
`T_PLANTE_ALPHA=0.5` dans `fields/ecofields/constants.py` ; import direct
`from fields.ecofields.constants import T_PLANTE_ALPHA`, les knobs thermiques ne
sont pas ré-exportés par `fields/__init__.py`). 1re fois que la croissance est
SPATIALISÉE (GDD locaux : coin chaud/sec pousse plus vite, coin frais/ombragé/humide
stagne plus longtemps). Vérif mécanisme (sem. 20, tuile 0) : T_air uniforme 14.11 °C ;
T_sol spatialisé 13.45→24.49 ; T ressentie 13.78→19.30 (mix α=0.5) — ≠ T_air par plot.
Golden **RE-FIGÉ** : `b1173a78a98e32e6705aaa9c573eadc8df2bfe1cb3bfbf46ed4ba18a8831ecc2`.
**`test_croissance` NON re-calibré** (67/67 PASS — aucun seuil T_air codé en dur, il
teste le mécanisme du gate pas des valeurs absolues). Suites eau 20/20, génétique 20/20,
population PASS. `main.py 3` OK. Le **gel lit encore T_air** (c'est ⑥, séparé). Dérive =
croissance spatialisée → dates de stade/floraison/reproduction/succession décalées
(traçable, comme ①②③④).

**⑥ CLOS (2026-06-18).** Le gel n'est plus GLOBAL/uniforme mais **localisé au plot**.
Helper pur `fields/ecofields/thermique.py::t_min_nuit_at(eco, r, c, t_air, nebul)` =
**carte nocturne SÉPARÉE** (la logique s'inverse : la nuit le soleil ne joue plus, on
ne relit PAS `temperature_sol`) : `T_min_nuit = T_air − RAYONNEMENT_NOCTURNE·(1−couvert)·
(1−nébulosité)`, `couvert = min(1, om_fresh_at/LITIERE_REF)` (même normalisation que
l'isolation diurne ③). Knob `RAYONNEMENT_NOCTURNE=5.0` dans `constants.py`. `boucle.py`
calcule la sévérité PAR PLANTE (depuis T_min_nuit à son plot) et la passe via le nouveau
param **`severity_fn`** (option a) de `mortalite.py::_mediated_damage` ; grêle/canicule
gardent le scalaire (chemin inchangé). Log gel devient **par tuile avec plage**
(`❄ gel [id] t_air=… sév min→max`). Le paillage agit désormais à DEUX échelles
(rondelle joueur + litière émergente) — voulu.

**Golden NEUTRE, hash INCHANGÉ `b1173a78…` (PAS re-figé).** ⚠️ Raison : le smoke
(seed 42) ne descend **jamais** sous `TEMP_FROST_DAMAGE=0.0` (semaine la plus froide =
+1.53 °C, « Gelée tardive ») → l'ancien gel global ne se déclenchait DÉJÀ jamais ; le
localiser ne change donc rien à la sortie. Le mécanisme N'EST PAS exercé par le golden.
Vérif mécanisme isolée (t_air=−2 °C, helper réel sur tuile 0 après 25 sem) : plot nu
(litière 0) → T_min_nuit −7.0 (sév 1.17, gèle) ; plot couvert saturé (litière 2.04) →
−2.0 = T_air (épargné) ; nébul 0→0.9 sur plot nu : sév 1.17→0.42. Monotone, borné.
**Aucun test gel à recalibrer** (il n'en existe pas ; test_croissance ne code aucun
seuil gel). Suites croissance 67/67, eau 20/20, génétique 20/20, population PASS.
`main.py 3` exit 0, scores OK.

**⑦ CLOS (2026-06-18).** **Neige** + **Orage** ajoutés au catalogue météo
(`sim/weather.py::_CATALOGUE` : Neige global durée 2 fenêtre 44-52, Orage local
durée 1 fenêtre 16-30) + entrées `SIGN_TABLE` (voix naturaliste). **Neige** thermique :
`TEMP_DELTA_BASE["Neige"]=-6.0` → entre AUTO dans `TEMP_DRIVEN` (pas d'effet
`WEATHER_ALEA` en plus) → déclenche le gel via la température ET dépose le manteau.
**Orage** non thermique = composite **pluie + vent** (option (b) du kickoff) :
`WEATHER_ALEA["Orage"]` = pluie (humidité +0.5), `ORAGE_VENT` (aleas.py) = vent
(paillage −1) appliqué EN SÉQUENCE dans `boucle.py`. **Manteau neigeux** = nouvel
état scalaire `eco.snow ∈ [0,1]` PAR TUILE (pas un GridField) ; helper PUR
`thermique.snow_next` + fine délégation `container.tick_snow` (calcul PUR sorti du
conteneur comme la T_sol au ①). ⚠️ **container.py = 372 ldc code pur** (> seuil ~350 /
max historique 337) : dépassement ANTÉRIEUR à ⑦ (déjà 359 au ⑥) + mon ajout
irréductible (attribut d'état `snow` + délégation 2 lignes ; le gros calcul est bien
en `thermique.py`). **À SIGNALER à Nico** — candidat éclatement du conteneur (sortir
un mixin décompo/litière ?) à un futur sprint refactor, hors scope ⑦. `boucle.py` appelle `eco.tick_snow(temp_now,
is_neige)` AVANT le gel (qui lit `snow`). Knobs `SNOW_ACCUM=0.5`/`SNOW_MELT_BASE=0.05`/
`SNOW_MELT_WARM=0.03` (constants.py). **Effet igloo** branché dans `t_min_nuit_at` :
`couvert = min(1, om_fresh_at/LITIERE_REF + eco.snow)` → sous bon manteau, couvert
sature, `T_min_nuit → T_air`, la neige PROTÈGE du gel. TODO « + neige ⑦ » retiré.

**Golden RE-FIGÉ LARGE** : `b1173a78…` → **`5fddfe5430dd896de497d5ac9424951f0f29f3f38ad7b50cdb588310a5ffe9f6`**.
Cause TRACÉE (pas un bug) : ajouter Neige/Orage à `_CATALOGUE` allonge la liste
`cands` des fenêtres été (16-30) et hiver (44-52) → l'index `int(pick·len(cands))`
se décale → TOUS les événements de ces fenêtres changent, cascade complète
hydro/croissance/succession. Sur le smoke (seed 0x5AB1057E, 4 ans) : Neige tombe
en semaine 96, Orage en 16/23/122/186 → la fenêtre est bien exercée.
**`population_hash.txt` AUSSI re-figé** (`5e6e688f…`) : `compute_hash` fait tourner
l'`Engine` → la météo décalée décale la température → les densités de population.
Ce n'est pas une suite « météo en dur » : c'est la même dérive maîtrisée en aval ;
les 4 sous-tests comportementaux (photopériode/bornes/cap/positions) PASSENT.

Vérif mécanisme manteau (helper réel) : (a) 1 sem Neige → snow 0.5, 2 sem → 1.0
(sature) ; (b) sol nu sans neige t_air=2 → T_min −3.0 (gèle) ; sous manteau snow=1
→ T_min 2.0 = T_air (igloo) ; (c) fonte 1 sem : froid (0 °C) snow 0.95, dégel
(10 °C) snow 0.65 (dégel plus rapide). Suites croissance 67/67, eau 20/20,
génétique 20/20, population PASS. `main.py 3` exit 0.

**Prochain** : implémenter ⑧ (`sprints/sprint_thermique_microclimat/08_snapshot_meteo.md`).
Kickoffs ⑧→⑩ écrits au fil de l'eau (un avant chaque `/clear`).
