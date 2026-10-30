# ① Recharge du sol vers l'équilibre de la roche + lessivage lié à l'eau

**Moteur Python. Golden RE-FIGÉ annoncé** (les champs n/p/k du smoke changent : c'est
l'objet du tronçon). Conception : `docs/champs/sol/conception_sol_nourricier.md` §3.1.

## Objectif
Le sol ne se vide plus jusqu'à zéro : chaque plot remonte lentement vers l'équilibre
hérité de son `soil_type`, et le lessivage passif ne s'applique que là où l'eau draine.

## Faits vérifiés au code (2026-10-30)
- Équilibre = `NUTRIENT_INIT_PAR_SOL` (`fields/ecofields/constants.py:727`, échelle [0,3]).
  ATTENTION : le monde `full` (`main.py build_tile`) passe un `fertilite=` qui pose
  n=p=k uniformes (cf. `container.py` ~l.652) → l'équilibre doit venir du `soil_type`
  (roche), PAS de la valeur initiale du plot. Vérifier ce que `heterogene=True`
  (`_init_catena`, container.py ~l.717) fait de ces valeurs.
- Lessivage : `fields/ecofields/matiere_organique.py:226-246` dans `tick_decomposition`
  (`leach_factor` × `facteur_pluie` lu dans `drainage_last`, écrit AVANT par
  `tick_hydrology`). `leach_factor` = `nutriments.py:86`.

## Modèle (intention — le placement exact est à toi)
1. **Recharge** par plot, par nutriment `e` : si `stock < eq_e(soil)` →
   `stock += RECHARGE[e] · (eq_e − stock)` ; sinon rien. Constantes nommées dans
   `constants.py`, commentées (pédagogie) : demi-vies de remontée visées N ≈ 1 an,
   K ≈ 2-3 ans, P ≈ 5 ans (RECHARGE ≈ ln2 / (52·demi-vie)). Helper PUR dans
   `nutriments.py` si possible. Zéro RNG.
2. **Lessivage lié à l'eau** : la fraction passive `LEACHING[e]·(1−cec)` est
   pondérée par l'eau drainée (`drainage_norm`, déjà calculé) ; sans drainage → 0.
   Garder `facteur_pluie` et `FACTEUR_PLUIE_CAP`. Vérifie que l'ordre recharge /
   lessivage / uptake dans le tick ne fait pas « annuler » la recharge avant lecture.

## Critères mesurés (OBLIGATOIRES, consignés dans 00_etat.md)
Script : `sprints/champs/sol/sprint_sol_nourricier/mesure_faim.py` (depuis
`data/code/` : `PYTHONPATH=. python3 ../../sprints/champs/sol/sprint_sol_nourricier/mesure_faim.py <seed> <semaines>`).
Avant (référence `faim42.log`) / après, seeds 42, 1, 2, 156 semaines :
- NPK médian des tuiles en an 2 **≥ 40 % de l'équilibre** pour chaque nutriment
  (aujourd'hui N 0,03, K 0,01) ;
- un plot nu en jachère (banc ou sonde, sans plantes) remonte d'au moins la moitié
  de l'écart à l'équilibre en 1 an pour N.
Calibre les constantes pour tenir ces cibles ; note les valeurs retenues.

## Golden
Re-figé : lance `python3 -m tests.test_golden`, constate la dérive, re-fige selon la
procédure du test, note l'ancien (`fecccded…`) et le nouveau hash + la raison dans
`00_etat.md`. Les autres suites (`tests/`) doivent passer ; si une suite casse parce
qu'elle supposait le vidage, analyse et signale (ne l'affaiblis pas sans justification).

## Ne PAS faire
Toucher la croissance des plantes (②), les voix (③), le monde `full` (④). Lancer
`test_epaisseur_500ans`.
