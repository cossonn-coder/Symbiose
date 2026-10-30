# ① Banc de mesure du calendrier — golden INTACT

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, `docs/champs/climat/conception_calendrier_unique.md`
(§1 le bug, §6 la liste des indicateurs).

## Objectif

Figer, AVANT tout changement, une photographie chiffrée de « quand se passe quoi » dans
l'année simulée, rejouable à l'identique après ② et ③ (décision C3 : mesurer d'abord,
recalibrer après). Aucun changement de mécanique.

## À faire

1. Créer `data/code/bancs/mesure_calendrier.py` — script de diagnostic exécutable
   (`python3 -m bancs.mesure_calendrier [n_ans]`, défaut 3, **jamais plus de 3**), frère de
   `bancs/mesure_floraison.py` (même façon de monter un monde et de lire l'état : reprends
   son `_monde()` / sa lecture `eco.populations`, `plant.floraison`). Il déroule le moteur
   et **lit** l'état réel ; il ne touche à aucune mécanique.
2. Indicateurs (§6 de la conception), **par année et par saison étiquetée**
   (`sim.engine.calendrier.saison_de`) :
   1. semaines de T min / T max de l'air (`sim.weather.weather_state`) et leur saison ;
      nombre de semaines `T_air < 0` par saison ;
   2. semaine du jour le plus long (`fields.population.daylength`) et sa saison ;
   3. semaines de neige (événement « Neige ») et semaines où `eco.glace` > 0 quelque part,
      par saison (prends un banc/monde qui a de l'eau de surface si celui de floraison
      n'en a pas — `tourbiere` ou le monde complet ; documente le choix) ;
   4. pommier : `bloom_week` et sa saison, recouvrement = part des semaines
      `floraison ≥ 0,5` où la densité totale des butineurs ≥ 0,05 (seuil de
      `mesure_floraison`), nombre de fruits noués s'il est lisible ;
   5. tomate : semaine de mort ou « survit » (prends le scénario où elle est plantée —
      cf. `tests/test_golden.py` ou un banc qui la sème ; documente) ;
   6. humidité du sol médiane (`eco.humidite`) par saison ;
   7. carpophores apparus par saison, par espèce (lis où le moteur les échantillonne :
      `fields/population/perception.sample_carpophores` / `fields.fongique.especes_de_saison`) ;
   8. semaine d'abscission effective (premier largage observé) et T de cette semaine.
   Si un indicateur est inaccessible sans toucher au moteur, **note-le « non mesurable »**
   dans la sortie plutôt que de modifier le moteur.
3. Sortie : un tableau markdown sur stdout. Le copier dans
   `sprints/champs/climat/sprint_calendrier_unique/mesures/avant.md`, avec en tête la
   commande exacte, le commit, la durée du run.
4. Mettre à jour `00_etat.md` (① fait + 3-4 lignes des chiffres les plus parlants, avec
   `[n=… ans, VM]` collé aux chiffres).

## Golden

**INTACT** (`python3 -m tests.test_golden` doit passer sans `--capture`).

## NE PAS

- Modifier `sim/`, `fields/`, `plants/`, `world/`.
- Lancer `tests/test_epaisseur_500ans.py`.
- Interpréter ou recalibrer : on photographie seulement.
