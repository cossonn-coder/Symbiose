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
| ④ | Nébulosité (effet thermique pluie/nuages, diurne) | température/météo | ⬜ |
| ⑤ | T ressentie (mix air/sol) → croissance | croissance | ⬜ |
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

**Prochain** : implémenter ④ (`sprints/sprint_thermique_microclimat/04_nebulosite.md`).
Kickoffs ⑤→⑩ écrits au fil de l'eau (un avant chaque `/clear`).
