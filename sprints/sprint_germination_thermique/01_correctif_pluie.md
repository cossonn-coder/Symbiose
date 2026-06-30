# Tronçon ① — Correctif T_air pluie + banc/oracle `pluie_thermique`

> Kickoff **autosuffisant** (démarrage à froid : lis CLAUDE.md + 00_etat.md + ce
> fichier). Conception : `docs/conception/CONCEPTION_GERMINATION_THERMIQUE.md` §3.
> Lancement depuis `data/code/`. Golden : **RE-FIGÉ maîtrisé** (annoncé).

## Objectif
La pluie ne refroidit **PAS** l'air aujourd'hui (trou vérifié). On corrige cette
coupure amont AVANT de brancher la germination dessus, et on pose un banc qui
prouve le couplage pluie → air → sol.

## Le trou (vérifié)
`weather.py:197` : `t_air = temp_norm(...) + temperature_delta(event)`.
`temperature_delta` (≈ l.155-167) ne rend ≠ 0 que pour les clés de
`TEMP_DELTA_BASE` (`weather.py:65`) = `{"Gelée tardive": -9.0, "Canicule": +7.0,
"Redoux": +5.0, "Neige": -6.0}`. **`Pluie prolongée`, `Orage`, `Grêle` absents**
→ delta 0.0 → une averse laisse l'air aussi chaud qu'avant (faux).

## À faire
1. **`sim/weather.py:65`** — ajouter au dict `TEMP_DELTA_BASE` un **delta froid**
   pour la pluie (placeholder, calibrage post-test au banc) :
   ```python
   "Pluie prolongée": -3.0,
   "Orage":           -2.0,
   ```
   (Garder `Grêle` hors scope pour l'instant — ou +un petit froid si cohérent avec
   le reste ; par défaut on s'en tient à Pluie/Orage comme arbitré.)
2. Vérifier que `temperature_delta(event)` applique bien ce delta (il fait
   `TEMP_DELTA_BASE.get(event.kind, 0.0)` éventuellement pondéré par l'intensité —
   ne pas changer la mécanique, juste alimenter le dict).
3. **Banc `pluie_thermique`** dans `data/code/bancs/climatique.py` (patron des
   bancs existants `secheresse_sable`/`acclimatation`) : un climat forcé sous
   averse répétée, qui expose `humidite`, `temperature_sol`, `temperature_air`
   après N ticks. L'enregistrer dans le registre `BANCS` (`bancs/__init__.py`).
4. **Oracle** dans `data/code/tests/bancs/` (patron des oracles existants) :
   asserte le sens des couplages — sous averse, `T_air` **baisse** (nouveau),
   `humidite` **monte**, `T_sol` **baisse** au tick suivant (lag 1 tick, cf.
   ordre thermique avant hydrologie). Valeurs en **tendance/borne**, pas en
   égalité fragile.

## Golden
**RE-FIGÉ maîtrisé.** Le delta froid pluie déplace `t_air` (donc `t_sol`) du smoke
test. Procédure : lancer `python3 -m tests.test_golden`, constater la dérive,
**re-figer** le hash attendu dans `tests/test_golden.py`, et **annoncer** dans le
message de commit + cocher ① dans `00_etat.md`. La dérive est **attendue et
localisée** au couplage thermique pluie.

## Ce qu'il NE faut PAS faire
- Ne PAS toucher la germination (c'est ②+). Ici, **seulement** le couplage météo.
- Ne PAS monter le banc dans le smoke/full (golden NEUTRE pour le banc lui-même).
- Ne PAS inventer de RNG : `weather_state` reste déterministe.
- Ne PAS calibrer finement le delta maintenant (placeholder assumé, calibrage ⑥).
