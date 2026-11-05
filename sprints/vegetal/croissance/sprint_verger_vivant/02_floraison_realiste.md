# ② Floraison réaliste des arbres — golden INTACT attendu

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, conception §5, `sim/engine/floraison.py`, `plants/perennials/fruitiers.py`, `plants/perennials/*.py` (autres ligneux), `calendrier.py`, `docs/vegetal/croissance/fiches_arbres.md`, `docs/vegetal/floraison/` (conceptions de floraison existantes).

## Objectif

Dans le moteur, les arbres fleurissent à la bonne date, dans le bon ordre, pendant la bonne durée, et atteignent une vraie pleine floraison.

## À faire

1. **Sourcer** (fiches, pépiniéristes, INRAE) les dates et durées de floraison sous climat normand : cerisier, pommier, noyer (chatons et fleurs femelles), figuier, plus les autres ligneux à fleurs du catalogue si un écart flagrant saute aux yeux. Déclarer `[odg]` avec la source. wiy 1 ≈ 20 mars.
2. **Ordre et dates** : aujourd'hui le pommier (`bloom_forcing_gdd` 8) fleurit avant le cerisier (12), ce qui est faux ; le noyer n'a pas de réglage et fleurit de s11 à s17 (juin), sur 7 semaines [`verger_mur`, seed 42, n=1 run]. Corriger les leviers d'espèce.
3. **Pic réel** : la montée exponentielle (`FLORAISON_MONTEE` 0,35) plafonne le cerisier à 0,73. Il faut qu'un arbre en pleine floraison approche 1 pendant sa durée réelle. Levier **par espèce ligneuse** (montée, durée, ou les deux), défaut inchangé : les herbacées ne bougent pas.
4. **Couplages à vérifier par mesure** : recouvrement avec les butineurs (D119 (c), pollen pendant la floraison), nouaison (`SEUIL_FLEURI` 0,5, `SEUIL_NOUAISON` 0,2 dans `sim/engine/decompo.py`), dose anémophile du noyer. Rapporter `floraison` semaine par semaine pour chaque arbre et `pollen_recu` annuel, avant/après [`verger_mur`, 3 ans].
5. Golden, `tests/test_desync_phenologie`, les suites de floraison et pollinisation (`ls tests`), `test_verger_mur`, puis bilan et commit.

## Golden

**INTACT attendu** : les arbres du smoke n'atteignent pas leur maturité, donc leur `floraison` reste à 0. S'il bouge : vérifier qu'aucune herbacée n'a changé ; un re-figeage n'est pas prévu.

## NE PAS

Changer `FLORAISON_MONTEE`/`FLORAISON_DESCENTE` globaux. Changer le dessin (④). Lancer `tests/test_epaisseur_500ans.py`.
