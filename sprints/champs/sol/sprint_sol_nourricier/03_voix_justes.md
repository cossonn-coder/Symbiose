# ③ Voix justes : la faim dit ce que l'être subit

**Python, lecture seule (voix sous vision). Golden INCHANGÉ obligatoire.**
Conception : `docs/champs/sol/conception_sol_nourricier.md` §3.3.

## Faits vérifiés au code (2026-10-30)
- Voix plante : `sim/voix_etres.py` `besoins_plante` ~l.95-100 — faim =
  `_ramp(SEUIL_FAIM − min(npk)/FIELD_NORM, 0, SEUIL_FAIM)`, seuil 0,4×3 = 1,2 au-dessus
  des valeurs initiales → faim dite dès s0.
- Voix bête : `besoins_bete` ~l.134 — faim = `_ramp(1 − field.activite(r,c), 0.6, 1.0)`,
  où `activite_grid` = ressource locale brute (`fields/population/field.py:63`).
  La population suit `cible = capacite × survie` avec inertie asymétrique
  (field.py ~l.105-121).
- Seuil de parole `SEUIL_DIRE` = 0,25.

## Modèle (intention)
1. **Plante** : intensité de « faim » = `1 − facteur_nutrition` (helper du ②) mis à
   l'échelle pour que « dit » ⇔ croissance réellement escomptée de façon visible ;
   nutriment cité = le limitant de ce même calcul. UNE source de vérité.
2. **Bête** : « faim » = déficit de la population face à ce que sa NOURRITURE locale
   porte : mémoriser dans `PopulationField.tick` une grille de rendu (comme
   `activite_grid`) du déficit `max(0, pop − cible_nourriture)/pop` (définition exacte
   à poser : part de la capacité venant de la ressource × survie). **Bit-identique** :
   aucune expression du calcul de `row[c]` ne change.
3. `faim_fleurs` / `faim_proies` suivent la même grandeur.

## Critères mesurés (dans 00_etat.md)
`mesure_faim.py` + `sonde_betes.py` (seed 42 ; 156 sem.) :
- part des plantes dont la voix dominante est « faim » : avant / après (attendu :
  minoritaire sur sol à l'équilibre ; toujours dite sur un sol carencé — le prouver
  par une sonde) ;
- part des bêtes présentes « affamées » à la semaine 26 : avant 75-100 % / après
  (attendu : seulement là où la population décline).
Adapter `sonde_betes.py` à la nouvelle grandeur.

## Golden
INCHANGÉ. S'il bouge : c'est un bug (la grille de rendu a touché le calcul) → corriger.

## Ne PAS faire
Changer les seuils de population, les densités (D119), le corpus de phrases.
