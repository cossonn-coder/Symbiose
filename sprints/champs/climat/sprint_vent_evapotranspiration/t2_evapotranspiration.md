# Tronçon ② — Évapotranspiration enrichie (débloque D39)

> Kickoff autonome. Design : `docs/champs/climat/conception_vent_evapotranspiration.md` **§3** + **§0**
> (déséquilibre chiffré). **Re-figeage golden LARGE annoncé.** C'est le cœur : il
> fait repasser `test_senescence` au **vert**.

## But
Donner à l'évaporation les deux pilotes qui manquent (rayonnement + vent masse
d'air), greffés **dans la boucle hydro EXISTANTE** (`fields/ecofields/container.py`
`tick_hydrology`, étape 1) — **zéro nouvelle traversée** :

```
evap = EVAPORATION
       − EVAP_TEMP_COEF · max(0, T_sol − EVAP_TEMP_REF)   # existant
       − EVAP_RAD_COEF  · (1 − nebulosite)                # NOUVEAU rayonnement
       − EVAP_WIND_COEF · vent_masse_air                  # NOUVEAU vent (uniforme, ①)
evap = max(EVAP_MIN, evap)
```

À ce stade on lit la **force de masse d'air** uniforme (① `wind_at`), pas encore le
champ d'abri spatial (③) — suffisant pour rééquilibrer la rosée. Brancher aussi la
**nébulosité dynamique** (① §2.3) en amont (lumière + rosée + thermique).

## Calibrage (knobs post-test)
`EVAP_RAD_COEF`, `EVAP_WIND_COEF` dans `fields/ecofields/constants.py`. Cible
**chiffrée** : sous climat clair calme à 15 °C (le climat labo de `test_senescence`),
l'équilibre hydrique **redescend sous le seuil d'asphyxie** → le pommier isolé meurt
de **sénescence** ∈ [49, 112] ans. SANS assécher tout le jardin (garde-fou
`EVAP_MIN` conservé). Itérer les coefs en relançant `test_senescence` + le golden.

## Critères de succès
- `python3 -m tests.test_senescence` → **VERT** (mort sénescente, pas asphyxie). Le
  test n'est **PAS** ré-isolé : il valide le bilan hydrique réel (rosée vs
  évaporation ventée/radiative).
- **Golden re-figé (annoncé)** : `python3 -m tests.test_golden --capture` (+
  population/vigueur si elles bougent), consigner **nouveau hash + raison**
  (rayonnement+vent dans l'évaporation).
- Suites : `test_rosee`, `test_eau`, `test_croissance`, `test_stress_chronique`,
  `test_sim_server`. Vérifier qu'on n'a pas créé une **sécheresse** généralisée.
- Budget perf : +2 lectures/plot dans une boucle existante → marginal (vérifier).

## Clôture
MAJ `00_etat.md` (② ✅ + nouveau hash golden + coefs retenus). **Rouvrir D39** dans
`DETTE.md` (récidive via rosée, re-résolue par le fond — pas par ré-isolation).
Commit. `/clear`. Lancer `t3_abri_spatial.md`.
