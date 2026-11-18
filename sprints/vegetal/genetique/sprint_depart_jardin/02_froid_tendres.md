# ② Froid des plantes tendres + mort par froid consignée (D140 C.6-C.7)

Lire d'abord `docs/vegetal/genetique/conception_depart_jardin.md` §2 C.6-C.7.

## Constat (vérifié 2026-11-18, monde `full`, seed 42, fondateurs de la tuile NO)
`lim_gel()` = tomate **+2,8 °C**, basilic **+1,2 °C**, poivron **−4,4 °C**, alors que les
données d'espèce disent `t_gel_tendre` = −1 °C (tuple `t_froid_lesion, t_gel_tendre,
endurcissement_max, t_chaud_stress, t_brulure` dans `plants/species/*.py`). C'est le gène
`rusticite_froid` (σ_A 1,5 °C, tiré pour la VARIÉTÉ par `fields.variete_genes`) qui
emporte la limite au-dessus de 0 °C ou bien trop bas. Le tournesol a
`t_froid_lesion` = 5,0 °C : il souffrirait du froid sans gel, ce qui est faux.

## Objectif
1. **Borne physique du gel** : aucune plante ne gèle au-dessus de ≈ −0,5 °C (point de
   congélation de la sève). L'appliquer là où la limite est calculée
   (`PlantInstance.lim_gel`, `plants/base/instance.py`) **ou** sur les bornes du gène
   — choisir le point unique et le justifier ; vérifier aussi `posture_thermique.py`
   (signes par paliers, mêmes limites) pour qu'ils restent cohérents.
2. **Dérive des tendres trop large** : regarder si la variété fondatrice d'une espèce
   tendre peut tirer `rusticite_froid` à ±2,5 σ (poivron −4,4 °C). Si oui, borner de
   façon réaliste (un poivron ne tient pas −4 °C) — sans toucher aux rustiques.
3. **Audit des tendres** : tomate, basilic, poivron, haricot, courgette, tournesol
   (+ toute espèce à `t_froid_lesion` non None). Tournesol → `t_froid_lesion = None`
   (il germe à 5-8 °C et tient une petite gelée au stade plantule). Noter chaque
   changement de donnée avec sa justification bio en commentaire.
4. **Chronique** : la mort par froid/gel sort en `non_consignee` dans
   `tools/simserver/chronique.py` (appariement au log par `sim/evenements.py`, lignes
   « ✗ … → meurt » et cause via `cause_de_raison`). Diagnostiquer pourquoi la ligne
   de `ReduceHealth(..., cause="froid")` / gel n'est pas appariée et corriger pour
   que la cause soit `froid` ou `gel`. Test : un fondateur tendre exposé à une nuit
   froide meurt avec la bonne cause dans la chronique.
5. **Garder** `FROID_LESION_K` (rythme du froid sans gel) : à 0-2 °C une semaine tue
   vraiment un jeune plant tendre (décision de conception).

## Golden
**RE-FIGÉ annoncé** si le smoke contient des tendres dont la limite change (tomate,
basilic…). Expliquer la 1ʳᵉ divergence. Le point 4 (chronique) seul doit être neutre.

## Ne PAS faire
- Protéger les tendres par une règle (pas de béquille) ; changer la météo ; changer
  la semaine de départ (c'est le ③).
- Lancer `test_epaisseur_500ans`.

## F5
Aucun propre au tronçon (la chronique du rapport perf affichera `froid`/`gel`).
