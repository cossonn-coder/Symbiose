# ③ Les feuilles au sol dans le moteur + pont — golden RE-FIGÉ (annoncé)

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, conception §3.2 et §3.3.

## Objectif

Les feuilles tombent sous toute la couronne, sur plusieurs semaines, et la vue reçoit de quoi le
montrer.

## À faire

1. **Largage** (`sim/engine/decompo._abscission`, appelé sur la fenêtre `ABSCISSION_MIN/MAX`) :
   aujourd'hui un seul dépôt sur `plant.position`. Répartir sur `plant.foliar_plots` (mémoïsé),
   restreint aux plots de la tuile ; étaler sur `CHUTE_SEMAINES` (~4) à partir de
   `semaine_abscission(plant)`. Vérifier que la fenêtre de l'appelant couvre ces semaines
   (`sim/engine/boucle.py`) : sinon l'élargir. Conserver le total annuel, sans RNG.
2. **Masse** : elle dépend aujourd'hui de la hauteur seule (`current_height × NECROMASS_PER_CM ×
   ABSCISSION_FRAC`). La faire suivre la couronne, pour une masse par plot à peu près stable. Calibrer
   par mesure : tapis présent sur la plupart des plots de la couronne en s36 [`full`, seed 42], et pas
   de dérive aberrante de l'azote ou de la matière organique sous l'arbre (comparer à un plot témoin).
3. **Pont** (`tools/simserver/serialize.py`), ajouts rétro-compatibles, version 0.6.3 consignée dans
   `tools/simserver/version.py` :
   - entrée de `litiere` : 9ᵉ élément = masse de la parcelle `feuille` du plot, même si un autre tissu
     domine (les plots de ~0 restent omis comme aujourd'hui) ;
   - par plante : `feuillage ∈ [0,1]` (1 avant `semaine_abscission`, puis baisse linéaire sur
     `CHUTE_SEMAINES`, 0 ensuite et jusqu'au débourrement ; persistants : 1). Hint PUR, sans écriture.
   Vérifier le passage dans le pont delta (`tools/simserver/pont_delta.py`) et la mémoïsation de
   `_snapshot`.
4. **Taille du snapshot** : plus de plots de litière. Mesurer le gain de taille au pic d'automne
   `[n=…, VM]` et le signaler s'il dépasse +20 %.
5. `mesures/apres_feuilles.md` : plots de litière feuille et masse, s30 → s45, par arbre.
6. Tests ciblés : conservation du total, tuile non dépassée, `feuillage` monotone.

## Golden

**RE-FIGÉ, annoncé** : la matière organique se redistribue sous les caducs. Ancien → nouveau hash et
raison à donner.

## NE PAS

Modifier `foliage_density_at` (limite assumée, conception §3.3). Faire passer des feuilles d'une tuile
à l'autre. Toucher au C#. Lancer `tests/test_epaisseur_500ans.py`.
