# ③ Herbivorie par atteinte (golden RE-FIGÉ, annoncé)

Lire d'abord : `CLAUDE.md`, `00_etat.md`, `docs/vegetal/sante/conception_plante_vivante.md`
§0 et §4.

## Objectif
Chaque ravageur ne mange que ce qu'il atteint ; ce qu'il mange se partage entre les
feuillages présents ; la plante perd une **part de feuillage** (ou de sucres pour le
puceron), pas un tiers de vie. Un chêne encaisse, un semis peut mourir.

## Existant (vérifié au code le 2026-11-18)
`herbivory_pressure` (`sim/effects/perturbations.py` ~l. 477-555) : lit
`eco.category_density("ravageur", r, c)` au plot-foyer + `eco.larvae["chenille"]`,
× `HERBIVORY_GAIN` 0,2, × parfum / appétence / coriacité ; porte
`pressure > stress_memory·0,5` ; `ReduceHealth(1 ou 2)` capé par `_cap_chronique`.
Guildes ravageurs (`fields/population/registry.py`) : `puceron`, `limace`,
`doryphore` (catégorie `ravageur`). Feuillage par plot : `plant.foliar_plots`
(en cache) ; somme des feuillages d'un plot : patron `_foliage_grid`
(`fields/population/resources.py`).

## À faire
1. Remplacer la lecture « catégorie ravageur au plot-foyer » par une lecture **par
   espèce de ravageur** sur les **plots foliaires** de la plante, avec une table
   d'atteinte data-driven (une ligne par ravageur, à côté des constantes
   d'herbivorie) :
   - `limace` : part du feuillage sous `LIMACE_HAUTEUR_CM` (≈ 40 cm) — dérivée de
     la hauteur de la plante (plante basse = tout atteint ; arbre = presque rien) ;
   - `puceron` : toute plante, en saison de croissance ; effet = **sucres volés**
     (retrait direct au bilan, `reserves`) + faible perte de feuillage ;
   - `doryphore` : famille Solanaceae seulement ;
   - `chenille` : feuillage (comme aujourd'hui).
2. Part de la plante sur un plot = son poids / somme des poids du plot (patron
   `_foliage_grid`). Perte hebdo = `K_HERB × moyenne sur ses plots foliaires de
   (densité atteignante × part)` × parfum × appétence / coriacité (facteurs
   existants conservés tels quels). Bascule létale (peu d'auxiliaires + sol mort)
   → consommation × 2.
3. Appliquer la perte sur `feuillage` (et `reserves` pour le puceron) via une
   mutation de tissus — garder la `cause`/`reason` « herbivorie » (sémiologie,
   chronique). Retirer la porte `stress_memory` de l'herbivorie (le champ
   `stress_memory` reste, il a d'autres lecteurs).
4. Si une grille par plot de la somme des feuillages est nécessaire, la calculer
   **une fois par tuile et par tick** (pas par plante) ; vérifier qu'elle n'existe
   pas déjà côté population avant d'en créer une.
5. Calibrer `K_HERB` par banc (`tests/test_herbivorie_atteinte.py`) :
   - semis seul sur un plot à limace 0,10 : perd 10-25 % de feuillage/sem, peut
     mourir s'il ne refait pas ses feuilles ;
   - laitue/basilic mûrs à ravageurs 0,10 : vivent, feuillage entamé ;
   - chêne de 25 ans, ravageurs 0,15 partout : perte < 2 %/sem, ne meurt pas ;
   - limace n'entame jamais un feuillage au-dessus de 40 cm.

## Golden
**RE-FIGÉ, annoncé** : dérive due à la seule herbivorie. Preuve : neutraliser la
nouvelle herbivorie (monkeypatch en mémoire) retombe sur le hash du ②. Consigner.

## Ne PAS faire
- Toucher les dynamiques de population (registre, `field.py`) : la population est
  juste ; c'est le dégât qui était faux.
- Lancer `test_epaisseur_500ans`.

## Contrôle
Reprendre la mesure du `00_etat.md` (ouverture s10, morts des 136 posées à s21) et
consigner le nouveau chiffre. Perf ≤ +5 %.
