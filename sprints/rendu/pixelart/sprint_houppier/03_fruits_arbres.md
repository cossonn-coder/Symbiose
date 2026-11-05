# ③ Fruits des arbres — golden INTACT attendu

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, conception §4, `sim/engine/decompo.py` (`_tick_fruits`), `plants/perennials/fruitiers.py`, `fields/ecofields/constants.py` (`FRUIT_DMAT`, `MATURITE_CHUTE`), `calendrier.py`, `docs/vegetal/croissance/fiches_arbres.md`, `tools/jardinier_auto/operateurs.py`.

## Objectif

Pommier, cerisier, figuier, noyer portent leurs fruits, à la bonne saison, et cela se mesure en jeu.

## À faire

1. **Levier** `fruit_semaines_maturation`, défaut `None` → `FRUIT_DMAT`. Maturation = 1 / durée. Chute à `MATURITE_CHUTE` inchangée. Vérifier au `grep` tous les lecteurs de `FRUIT_DMAT` et de la maturité.
2. **Espèces** : `fruitier = True` sur `CherryTree`, `Fig`, `WalnutTree` ; `Fig.pollination_mode = "self"` (figue commune, et `nectar = 0` : sans cela, 0 fruit attendu d'après le code, à constater). Durées à caler sur `calendrier.saison_de` et les fiches : pommes en sept.-oct., cerises en début d'été. Déclarer `[choix]` ou `[odg]`.
3. **Banc** `verger_mur` : les 4 arbres mûrs (noyer `maturity_years` 15 : pré-vieillir), butineurs présents, sans la maison dans le cadre. Oracle : chaque espèce a des fruits, mûrs dans sa fenêtre, chutes en litière `fruit`. Noyer isolé : dose anémophile, rapporter le résultat. S'il ne noue jamais, le dire et poser deux noyers au banc ; ne pas forcer de plancher (`frac_nouaison` n'en a pas, §B.2).
4. **Effet en jeu** sur `full`, seed 42, 3 ans : fruits par espèce et par semaine, litière `fruit`, faune attirée, tick, population par an, avant/après. Automate : `tools/jardinier_auto` traite désormais ces arbres comme fruitiers (`fruitier=True` → exige un fruit mûr), à vérifier. Un tronçon sans effet mesuré n'est pas un succès.
5. **Voix** : l'encyclopédie (`sim/encyclopedie_corpus/ligneux.py`) parle-t-elle des fruits de ces 4 arbres, pages et magazine cohérents ? Compléter seulement ce qui manque.
6. Golden, `tests/simserver`, suites fruits et pollinisation, puis bilan et commit.

## Golden

**INTACT** : identique avec les trois fruitiers et `self` [smoke, patch mémoire], sous réserve du levier. S'il bouge : anomalie, pas de re-figeage.

## NE PAS

Changer la durée de tomate, fraise, framboise, courgette. Toucher à `FRUIT_MASSE` ni à `frac_nouaison`. Dessiner : la vue est au ⑤. Lancer `tests/test_epaisseur_500ans.py`.
