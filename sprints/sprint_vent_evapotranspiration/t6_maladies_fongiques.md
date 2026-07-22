# Tronçon ⑥ — Vent × maladies fongiques

> Kickoff autonome. Design : `docs/champs/climat/conception_vent_evapotranspiration.md` **§5.4**.
> Effets **par-plante/plot** (négligeable en perf). Re-figeage golden probable.
> Cohérent avec le diagnostic D39 (le pommier isolé chopait « maladie fongique »).

## But (double tranchant)
Greffe sur `sim/effects/perturbations.py` (`fungal_disease`, `_local_density`) :
1. **Assèchement protecteur** : le vent assèche le feuillage → **réduit la pression
   fongique locale** (le champignon a besoin d'eau ; lit `infection_memory`/humidité
   foliaire ventée). → **la ventilation est un remède** : enseigne l'aération
   (espacement, taille) — pédagogie permaculture (✅).
2. **Dispersion des spores** : le vent **propage l'inoculum sous le vent**
   (direction !) entre plots/plantes. Net = arbitrage local entre assèchement
   protecteur et transport contaminant.

## Garde-fou perf
`fungal_disease`/`_local_density`/`plots_within_radius` sont **déjà ~25 % du tick**
(D32 voisin, mesuré). **Ne pas alourdir** : lire `vent_local`/humidité déjà calculés,
réutiliser les voisinages existants (`plots_within_radius`), pas de nouvelle passe
spatiale dédiée. Mesurer ms/tick avant/après.

## Critères de succès
- Test maladies étendu : un plot bien venté voit sa pression fongique baisser ; un
  plot sous le vent d'un foyer infecté reçoit l'inoculum.
- Golden re-figé (annoncé). Suites : `test_sim_server`, suite maladies/perturbations
  existante.
- Perf : pas d'alourdissement notable du poste perturbations (vérifier).

## Clôture
MAJ `00_etat.md` (⑥ ✅). Commit. `/clear`. Lancer `t7_transport_voix.md`.
