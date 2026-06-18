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
| ① | Socle T_sol diurne (surchauffe solaire + inertie lerp) + évaporation branchée | hydrologie | ⬜ |
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

Conception + kickoff ① écrits. Dettes D37/D38 ajoutées à `DETTE.md`.
**Prochain** : implémenter ① (`sprints/sprint_thermique_microclimat/01_socle_tsol_diurne.md`).
Kickoffs ②→⑩ écrits au fil de l'eau (un avant chaque `/clear`).
