# ⑤ Automate : repiquage différé (D140 C.5)

Lire d'abord `docs/vegetal/genetique/conception_depart_jardin.md` §2 C.5, puis le
bilan du ④ dans `00_etat.md` (nom exact du geste et de la commande).

## Existant
Le jardinier automate vit dans `data/code/tools/jardinier_auto/` (planification
moyens-fins déterministe : `operateurs.py`, `planification.py`, `execution.py`,
`regles.py`, `boucle.py`, trace `trace.py`). Il est opt-in (automate OFF = golden
bit-identique).

## Objectif
1. L'automate **repique** un plant en pot (intérieur ou extérieur) vers la pleine terre
   quand la saison le permet pour SON espèce : nuits récentes et prévues au-dessus de
   `lim_froid()` (ou `lim_gel()` pour une espèce non sensible) avec une marge nommée,
   ET hors de la fenêtre des gelées tardives. Lire ce que le moteur expose déjà
   (préavis météo `sim/ciel.py`, nuit la plus froide) plutôt que recalculer.
2. Où repiquer : un plot libre et à la niche de l'espèce (réutiliser le placement
   existant de l'opérateur `planter`).
3. Choix d'intégration (opérateur de plan OU règle réactive) : celui qui colle à
   l'architecture existante ; tracer le geste (`trace.py`) avec sa raison.
4. Tests : sur un monde à pots intérieurs, l'automate ne repique PAS en s4 (gelée
   tardive) et repique après la fenêtre ; aucun repiquage si automate OFF.

## Golden
**INTACT** (automate opt-in).

## Ne PAS faire
- Faire semer en intérieur par l'automate (non demandé) ; toucher à la vue.

## F5
Au ⑥ (automate branché : les pots de tendres sortent fin mai / début juin).
