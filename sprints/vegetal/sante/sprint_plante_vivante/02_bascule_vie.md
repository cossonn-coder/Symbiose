# ② Bascule : la plante vit du bilan (golden RE-FIGÉ, annoncé)

Lire d'abord : `CLAUDE.md`, `00_etat.md` (acquis du ①), `docs/vegetal/sante/conception_plante_vivante.md`
§1, §3, §4 (adaptateur), §5.

## Objectif
Le bilan du ① devient la vie de la plante : `vitalite` devient une **lecture**, la
famine tue, la mort au sort et la guérison au sort disparaissent, la croissance
suit le surplus. Les stress existants passent par l'**adaptateur** `erode` = perte
de tissus.

## À faire
1. **Vitalité dérivée** (§3) : `vitalite = min(1, reserves/R_CONFORT) × (0,5 + 0,5 ×
   feuillage)`. `vitalite` est aujourd'hui un champ de dataclass
   (`plants/base/instance.py`) lu par ~40 sites et écrit directement à quelques
   endroits (`= 0.0` : `sim/actions/gestes.py`, `sim/actions/greffe.py`,
   `PlantInstance.regress`, `root_herbivory` annélation dans
   `sim/effects/perturbations.py`). Intention : toute lecture renvoie la valeur
   dérivée ; toute écriture `0` = destruction (`reserves = 0`, `feuillage = 0`).
   Le placement (propriété + champ privé, ou autre) est à choisir **après avoir
   recensé au `grep`** les constructions `PlantInstance(..., vitalite=…)` et les
   écritures non nulles (tests compris) — elles doivent continuer de marcher.
2. **`erode(a)` = perte de tissus** (§4) : `feuillage −= a / resilience_base` ; un coup
   ≥ la vitalité restante = destruction. Tous les `ReduceHealth` passent déjà par
   `erode` (`sim/effects/resolution.py`) → aucune voie à toucher une par une ici.
   Les décréments DIRECTS de vitalité (sénescence et fin de cycle, `mortalite.py`
   `_tick_senescence_health`) : les convertir en retrait de réserves équivalent,
   sans changer leur logique (le sprint B les refond).
3. **Famine** : `reserves ≤ 0` → mort, cause consignée `famine` (log moteur au
   format des autres morts + `CAUSE_DE_RAISON` de la chronique
   `tools/simserver/chronique.py`).
4. **Supprimer (commenter, conserver pour mémoire)** : `background_mortality`,
   `shade_stress_damage` (l'ombre tue désormais par famine) dans
   `sim/effects/perturbations.py` ; la convalescence au sort (`heal`,
   `mortalite.py` ~l. 140-170) — remplacée par la refeuillaison du ①.
5. **Croissance** : la cible du `growth_factor` (`_update_physiology`) dérive du
   surplus (`net` après remplissage des réserves) au lieu de `0,6 + 0,4·light_eff`
   × escomptes (déjà dans P — ne pas compter deux fois). `can_grow`
   (`_avancer_stades`) devient `net > 0` ; garder les lignes de log « stagne (froid
   / ombre / sec / noyé / chaud) » en nommant le facteur limitant le plus bas.
6. Adapter les suites qui encodent l'ancienne arithmétique de PV (paliers 1/3,
   guérison au sort) à la nouvelle physique — **ne supprimer aucun test** ;
   un test qui vérifiait « l'ombre tue en N semaines » vérifie « l'ombre affame ».

## Golden
**RE-FIGÉ, annoncé** : la vie et la mort changent de modèle. Avant de re-figer :
(a) le smoke tourne 4 ans sans crash ; (b) la dérive s'explique (morts au sort
disparues, vitalité dérivée) — consigner dans `00_etat.md` les 3 premières
divergences du log et le nouveau hash. Suites `tests/` vertes.

## Ne PAS faire
- Toucher la règle d'herbivorie (③) ni les souches (④).
- Raffiner chaque stress (sprint B) : l'adaptateur suffit ici.
- Lancer `test_epaisseur_500ans`.

## Contrôle
Monde `full` seed 42, 52 semaines depuis s10 : nombre de plantes vivantes par
semaine, causes de mort ; consigner dans `00_etat.md`. Perf ≤ +10 %.
