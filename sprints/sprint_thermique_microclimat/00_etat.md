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
| ⑥ | Gel nocturne localisé (couvert + nébulosité + neige protègent) | gel | ⬜ |
| ⑦ | Catalogue : Neige + Orage + effets | météo (tirages) | ⬜ |
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

**Prochain** : implémenter ⑥ (`sprints/sprint_thermique_microclimat/06_gel_nocturne.md`).
Kickoffs ⑦→⑩ écrits au fil de l'eau (un avant chaque `/clear`).
