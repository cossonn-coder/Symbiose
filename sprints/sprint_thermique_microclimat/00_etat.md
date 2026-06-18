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
| ② | Refroidissement évaporatif (chaleur latente) | température/hydro | ⬜ |
| ③ | Isolation par le couvert (litière) | température légère | ⬜ |
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

**Prochain** : implémenter ② (`sprints/sprint_thermique_microclimat/02_refroidissement_evaporatif.md`).
Kickoffs ③→⑩ écrits au fil de l'eau (un avant chaque `/clear`).
