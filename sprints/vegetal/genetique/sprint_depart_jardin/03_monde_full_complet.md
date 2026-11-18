# ③ Monde `full` complet : ouverture mi-mai, une plante mûre de chaque espèce (D140 C.1-C.3)

Lire d'abord `docs/vegetal/genetique/conception_depart_jardin.md` §2 C.1-C.3.

## Constat (vérifié 2026-11-18)
- Le monde `full` = `main.build_world_full()` (8 tuiles `SECTORS`, `plant_garden`) +
  `cmd_init` config `"full"` dans `tools/simserver/commands.py` (pré-vieillissement des
  ligneux `_pre_vieillir_ligneux` → `sim/precroissance.pre_croitre`, `AGE_ARBRES_DEMO`
  = 11). Il contient **15 espèces sur 52** (`PLANT_CATALOGUE` 40 + `PERENNIAL_CATALOGUE`
  12). Absentes : ail, armoise, bambou, blé, bourrache, bourse à pasteur, carotte,
  chanvre, chêne, consoude, courgette, dactyle, fétuque, figuier, fraisier,
  framboisier, hêtre, jasmin, lavande, lierre, mâche, menthe, minette, molène,
  moutarde, myrtille, noisetier, noyer, ortie, pâturin, pissenlit, plantain, sapin,
  saule, seigle, thym, violette.
- La semaine de départ vient de `start_week = msg.get("week", BANC_WEEK_DEPART.get(config, 1))`.
- `main.py` (démo 500 ans) et le golden smoke ont leurs propres départs : **ne pas les
  changer**.

## Objectif
1. **Départ du monde `full` en semaine 10** (≈ 22 mai, juste après les saints de glace ;
   la fenêtre « Gelée tardive » de `sim/weather.py` couvre s2-s9). Config `"full"`
   seulement (et `"propre"`, qui est le même monde — décider et le dire). Vérifier que
   rien n'assume `week == 1` au premier tick (chronique `_an`, perf, sauvegarde,
   automate, délai de dormance des grains).
2. **Au moins une plante MATURE de chaque espèce du catalogue** dans le jardin à
   l'ouverture, placée dans une tuile dont le sol/la lumière/l'humidité lui
   conviennent (aquatiques et rives près de la mare, ombre pour violette/lierre…).
   - « Mature » = stade reproducteur atteint (fleurit/fructifie à la saison). Herbacées :
     trouver comment amener une plante à son stade adulte HORS tick (voir
     `sim/precroissance.py`, les bancs `data/code/bancs/` qui posent des plantes
     adultes, `advance_stage`) — déterministe, sans dérouler des semaines de sim.
   - **Arbres** : âge = leur `maturity_years` (première fructification), structure
     pré-croissante de cet âge (`pre_croitre`). Remplacer l'âge unique
     `AGE_ARBRES_DEMO` par l'âge propre de chaque espèce (au moins
     `max(AGE_ARBRES_DEMO, maturity_years)` — le pommier doit toujours nouer au 1er été).
   - Une fabrique dédiée, lisible (ex. `catalogue_complet(...)` dans un module neuf
     sous `world/` ou à côté de `build_world_full`), plutôt que d'alourdir `main.py`.
     Respecter la règle de couches et la taille des fichiers.
   - Les fondateurs restent semés par `semer_fondateur` (gènes de variété, déterminisme).
3. **Semis** : quelques graines déjà semées en terre à l'ouverture (`GrainEnAttente`,
   même voie que le geste `planter`), dont au moins une tendre (lève sur sol chaud).
4. **Garde-fou permanent** : un test (dans `tests/simserver/` ou `tests/`) qui échoue si
   une espèce de `PLANT_CATALOGUE ∪ PERENNIAL_CATALOGUE` est absente du monde `full` à
   l'init. Message d'échec explicite : « ajouter <espèce> au monde full ».
5. **Perf — mesure obligatoire** : tick moyen s10-s30 et durée d'init, avant/après
   [n paires alternées, bruit noté], charge VM vérifiée par `uptime` avant de mesurer.
   Signaler au-delà de +30 % (ne pas optimiser dans ce tronçon).
6. Mettre à jour les tests du pont qui lisent le monde `full` (`tests/simserver/base.py`,
   `delta.py`, `conteneurs.py`…) si leurs attentes changent ; jamais affaiblir un test
   pour le faire passer sans le dire.

## Golden
**INTACT** (le smoke n'utilise pas `build_world_full`). Si `main.py` est modifié,
vérifier que le golden reste identique.

## Ne PAS faire
- Changer le départ du smoke ou de `main.py` ; toucher au trèfle ; ajouter des espèces
  au catalogue ; protéger les tendres par règle.

## F5
Monde `full` : ouverture fin mai, toutes les espèces présentes et adultes (fleurs,
fruits selon la saison), grands arbres qui ombragent leur tuile.
