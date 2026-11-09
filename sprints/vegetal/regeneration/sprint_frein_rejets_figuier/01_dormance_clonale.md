# ① Dormance clonale — pas de stolon, rhizome ni drageon en hiver

À lire d'abord : `CLAUDE.md`, `00_etat.md`,
`docs/vegetal/regeneration/conception_rejets_de_souche.md` §1 et §3.1.

## Objectif
Aujourd'hui `sim/clonal.py::emettre_ramets` émet toute l'année. En hiver ses deux
portes (lumière au sol ≥ `CLONAL_LIGHT_SEUIL` 0,30, couverture <
`COUVERTURE_SATURATION` 0,85) sont grandes ouvertes (caduc nu, herbe rase) : les
164 rejets du figuier mesurés sur 25 ans sont TOUS nés en hiver. Rien ne
s'enracine en dormance : couper l'émission clonale hors saison de végétation,
pour **toutes** les clonales.

## Modèle
- Dans `emettre_ramets(tile, eco, seed, week)` : si la semaine de l'année
  (`((week - 1) % 52) + 1`, même formule que `sim/engine/boucle.py:83`) tombe
  en `"hiver"` (`calendrier.SAISONS` ; `saison_de` est ré-exporté par
  `sim/engine/calendrier.py`), retour immédiat (log vide). Vérifier que l'import
  ne crée pas de cycle (`sim.clonal` est importé par `sim/engine/boucle.py` ;
  préférer le module racine `calendrier` si `sim.engine` importe `sim.clonal`).
- Placer le test AVANT tout appel à `_hash_noise` ou `vigueur_plante` (aucun état
  consommé, le tirage est sans état mais restons lisibles).
- Commentaire pédagogique : pourquoi (dormance ; portes calibrées pour la saison
  feuillée ; mesure du 2026-11-09).
- Le figuier garde son `drageon` à ce tronçon (il le perd au ②) : après ①, il
  n'émet plus RIEN (mesuré : 0 rejet en 25 ans quand l'hiver est coupé). C'est
  attendu et transitoire.

## Golden
**INCHANGÉ** attendu : espion sur le golden (2026-11-09) = 36 ramets de trèfle,
6 au printemps, 21 en été, 9 en automne, **0 en hiver** [smoke, n=1 run, VM]. S'il
bouge : STOP, consigner dans `00_etat.md`, ne pas re-figer.

## Mesure (à consigner)
Sur `full` (ou la config de démo par défaut du serveur), 5 ans, seed 42 : ramets
émis par saison et par espèce AVANT/APRÈS (espion qui enveloppe
`sim.engine.boucle.emettre_ramets`, script hors dépôt). Dire quelles espèces
s'enracinaient en hiver et combien [n=1 run].

## Tests
- `tests/test_figuier_realiste.py` (c) attend des rejets d'un figuier mûr sur 200
  semaines : il en aura encore (saisons actives) ou plus du tout selon la lumière
  imposée — l'ajuster si besoin, en le disant (il sera réécrit au ②).
- Test neuf (dans un fichier clonal existant si l'un s'y prête, sinon
  `tests/test_dormance_clonale.py`) : même plante clonale mature, mêmes champs
  ouverts ; semaine d'hiver → 0 ramet ; semaine d'été → l'émission reste possible.
- `tests.test_golden`, `test_evenements`, suites clonales
  (`grep -l "clonal\|ramet" data/code/tests/test_*.py`). **Jamais
  `test_epaisseur_500ans`.**

## Ne PAS faire
- Toucher aux portes lumière/couverture ou à `clonal_interval`.
- Toucher au figuier (c'est le ②).
