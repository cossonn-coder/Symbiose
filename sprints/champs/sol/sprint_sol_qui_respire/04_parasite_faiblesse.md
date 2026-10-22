# ④ Parasite de faiblesse

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, conception §3.3.
**Golden** : re-figé SEULEMENT si le smoke (2 tuiles × 4 ans) contient un hôte affaibli sur
mycélium ; sinon intact. Constater et consigner lequel.

## Objectif
Les espèces `parasite` du registre (③ : armillaire, polypore du bouleau) attaquent les
racines des hôtes de leurs familles **déjà affaiblis** ; l'hôte boit moins, décline, meurt,
son bois tombe (②) et nourrit les saprophytes. Mécanique GÉNÉRIQUE (données), jamais
« cerisier » ou « armillaire » en dur.

- Canal existant (vérifié) : `plant.root_herbivory_memory` est lerpé vers une pression
  `rong` du campagnol dans `sim/engine/croissance.py` (~l.383, `ROOT_HERBIVORY_MEMORY_LERP`)
  puis lu par `fields/ecofields/uptake.py::plant_uptake` (`root_factor`). Le parasite
  AJOUTE sa pression à cette cible (intention ; placement exact à décider au code).
- Pression ∝ densité de mycélium sur les `root_plots` de l'hôte × faiblesse de l'hôte
  (vitalité sous un seuil — `vitalite` du sprint santé & résilience), × appartenance de la
  famille aux hôtes d'une espèce parasite présente sur la niche. Hôte vigoureux = 0.
- Déterministe, tick hebdo. Coût : seulement les ligneux affaiblis (peu nombreux).
- Test ciblé `tests/` : hôte vigoureux intact ; hôte affaibli sur mycélium → uptake ↓,
  déclin ; hôte d'une famille non listée → 0.

## Ne PAS faire
Pas de bonus/malus direct sur la vitalité (passer par le canal racinaire). Pas de 500 ans.
