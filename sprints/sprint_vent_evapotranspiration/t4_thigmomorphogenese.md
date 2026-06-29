# Tronçon ④ — Thigmomorphogénèse & dégât des tiges

> Kickoff autonome. Design : `CONCEPTION_VENT_EVAPOTRANSPIRATION.md` **§5.1** (thigmo)
> + **§5.2** (dégât étiolées) + **§3** (transpiration). Effets **par-plante**
> (négligeable en perf). Re-figeage golden probable.

## But (le bouclage plasticité, philo #2)
1. **Thigmo** : ajouter la paire `"port_trapu": "wind_memory"` dans `_EXPR_MEMOIRE`
   (`sim/engine/croissance.py`, ~L46). `wind_memory` = mémoire d'exposition mécanique
   intégrée lentement (lerp, comme `drought_memory`/`shade_memory`) depuis
   `vent_local` au plot. `expressed_gene("port_trapu")` glisse vers
   `1 + EXPR_GAIN·wind_memory` (hystérèse) → phénotype **trapu** : entre-nœuds courts
   (réduit l'étiolement) + susceptibilité au vent abaissée.
   - **Semis extérieur renforcé** : exposé tôt → `wind_memory` ↑ → trapu (✅).
   - **Semis intérieur fragile dehors** : élevé à l'abri (semis maison / conteneur
     jamais sorti) → `wind_memory`=0 → choc à la transplantation (= absence
     d'endurcissement/hardening off) (✅).
   - **Priming hérité** : `child_expression` fait déjà voyager l'expression mère →
     lignée éprouvée par le vent naît pré-armée. **Aucun code neuf** (hérité de ④
     plasticité).
2. **Dégât médié** (modèle `_mediated_damage`, comme gel/grêle, `mortalite.py`) :
   `dégât = sévérité_vent(vent_local, risée) · (étiolement / expressed_gene("port_trapu")) · (1 − protection_abri)`.
   `est_etiole(plant)` existe déjà (sprint Q7). Trapu encaisse, étiolé de serre casse
   → la boucle se referme. Sélecteur de stade à trancher au besoin (tissu tendre/élancé).
3. **Transpiration foliaire** (§3) : le vent amplifie la demande évapotranspiratoire
   → renforce le stress hydrique foliaire des grandes feuilles par grand vent (greffe
   dans le calcul de stress hydrique de croissance, lit `vent_local`).

## Critères de succès
- `test_plasticite` étendu : `wind_memory`→`port_trapu` monte sous vent, retombe à
  l'abri (hystérèse) ; semis intérieur transplanté subit le dégât, semis endurci non.
- Golden re-figé (annoncé). Suites : `test_croissance`, `test_stress_chronique`,
  `test_sim_server`.
- Perf par-plante → négligeable (vérifier ms/tick stable).

## Clôture
MAJ `00_etat.md` (④ ✅). Commit. `/clear`. Lancer `t5_pollinisation_dispersion.md`.
