# ② Calendrier unique + décalage du climat — golden RE-FIGÉ LARGE (annoncé)

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, `docs/champs/climat/conception_calendrier_unique.md`
(§1-§3), `mesures/avant.md` (produit par ①).

## Objectif

Une seule convention de semaine dans tout le moteur : **wiy 1 = équinoxe de printemps**
(décision C1), définie en **un seul endroit de couche basse** (C2). Changement
MÉCANIQUE : on ne recalibre rien ici (c'est ③).

## À faire

1. **Créer `data/code/calendrier.py`** (racine, à côté de `constants.py`, zéro import du
   projet → importable depuis `plants`, `fields`, `sim` sans cycle ; `constants.py` y est
   déjà importé ainsi : `from constants import PLOT_CM`). Y déplacer le contenu de
   `sim/engine/calendrier.py` (`SAISONS`, `PHASES_ACTIVES`, `FRUIT_NOUAISON_WEEK`,
   `saison_de`, prédicats) + ajouter :
   - `wiy_de(week)` = `((week - 1) % 52) + 1` (remplace les copies inline au fil de l'eau
     là où tu passes, sans chasse systématique) ;
   - les phases climatiques nommées : `W_T_MIN = 45` (froid max, ≈ fin janvier),
     `W_SOLSTICE_ETE = 14` (≈ 21 juin) ; commentaire pédagogique : la convention, la
     table mois → semaine (conception §4).
   `sim/engine/calendrier.py` devient un **ré-export** (les 10+ importeurs, dont
   `tools/`, restent inchangés).
2. **Brancher les copies sur la source unique** (comportement identique à ce stade) :
   `sim/weather._saison_meteo`, `sim/precroissance.SEMAINE_HIVER`,
   `sim/growth/phases._season_factor` (`wiy >= 40`). Si un import direct crée un cycle,
   garde le symbole local mais **dérivé** de `calendrier` (jamais un littéral).
3. **Décaler les 4 courbes** (le cœur du changement) :
   - `sim/weather.temp_norm` : `(week_in_year - 4)` → `(week_in_year - W_T_MIN)` ;
   - `sim/weather.humidite_air` : idem (max d'humidité au cœur de l'hiver) ;
   - `sim/wind.py:~131` : idem ;
   - `fields/population/constants.W_SOLSTICE_ETE` : 25 → importer celle de `calendrier`
     (14). Vérifie les défauts `week_in_year=25` / `= W_SOLSTICE_ETE` dans
     `fields/ecofields/vie_macro.py` et `fields/population/field.py` : ils désignent « le
     jour le plus long » → ils doivent suivre la constante, pas rester à 25.
   Corriger les commentaires qui disent « semaine 4 = fin janvier », « wiy≈25 »,
   « pic thermique wiy≈30 » (→ 45, 14, ≈19).
4. **Ne PAS toucher** aux fenêtres calées sur des semaines (aléas `_CATALOGUE`, fenêtres
   fongiques, `ABSCISSION_*`, `bois_chute_semaine`, `BANC_WEEK_DEPART`) : c'est ③.
5. Doc : `docs/champs/climat/conception_meteo.md` §1.1 (« minimum ~semaine 4 (fin janvier) »)
   → convention équinoxe + renvoi vers `conception_calendrier_unique.md`.
6. **Golden** : `python3 -m tests.test_golden` va casser (attendu). Vérifier que la dérive
   est bien climatique (T_air, gel, croissance), puis `--capture` ; consigner l'ancien et
   le nouveau hash dans `00_etat.md`. Faire tourner les autres suites `tests/test_*.py`
   (SAUF `test_epaisseur_500ans.py`) : un test qui casse uniquement parce qu'il fige une
   semaine climatique (ex. « il gèle en s4 ») se met à jour **en le disant dans le
   commit** ; un test qui casse pour une autre raison = bug à corriger, pas à figer.
   `tests/population_hash.txt` : même règle.
7. **Re-mesurer** : `python3 -m bancs.mesure_calendrier` → `mesures/apres_decalage.md` +
   tableau comparatif avant/après de 6-10 lignes dans `00_etat.md` (indicateurs en rouge
   = contredisent la réalité de la conception §4-§5 → liste d'entrée de ③).

## Golden

**RE-FIGÉ LARGE, annoncé** : tout le climat glisse de 11 semaines (dérive globale,
attendue, expliquée par la conception §3).

## NE PAS

- Recalibrer un seuil, une fenêtre, un banc (③).
- Toucher la déclinaison solaire `fields/light.SOLAR_DECLINATION` (C4, hors périmètre).
- Toucher le C# (④).
- Lancer `tests/test_epaisseur_500ans.py`.
