# ③ Maladies et racines (golden RE-FIGÉ annoncé)

Lire : `CLAUDE.md`, `00_etat.md` (ce sprint + sprint A), conception §4-§5.

## Biologie
- **Mildiou** : détruit des feuilles. **Oïdium** : couvre les feuilles, baisse leur
  rendement sans les tuer. **Fonte des semis** : pourrit le collet d'une plantule →
  destruction.
- **Racines perdues** (eau stagnante = asphyxie, pourriture, campagnol) : la plante
  n'absorbe plus → eau et nutriments perçus baissent → famine ou dessèchement.
  L'**annélation** (écorce rongée tout autour) coupe la sève descendante → les
  racines s'affament → mort (destruction différée, déjà gérée en direct aujourd'hui).

## Existant
`sim/effects/perturbations.py` : `fungal_disease`, `oidium_disease`,
`damping_off`, `root_herbivory` (annélation) ; `sim/engine/mortalite.py`
asphyxie (`asphyxie_memory`, `ASPHYXIE_HEALTH_SEUIL`) ; `sim/engine/racines.py`
`pression_parasite`, `maj_pourriture` ; `root_herbivory_memory` lue par
`plant_uptake` (déjà un flux).

## À faire
1. Mildiou → perte de feuillage ; oïdium → facteur de rendement sur `P` (lu dans
   le bilan), pas de perte de feuillage ; fonte → destruction (inchangée dans
   l'esprit).
2. Asphyxie, pourriture : remplacer le décrément de vitalité par une **perte de
   racines** qui baisse l'eau/nutriments perçus (patron `root_herbivory_memory` →
   `plant_uptake`, et `eau_percue`) ; la mort vient du bilan ou de l'embolie.
3. Annélation : conserver la mort mécanique, la consigner comme destruction.
4. Tests adaptés (`test_sante*`, `test_biotique`, `test_asphyxie` s'ils existent —
   vérifier au `ls tests/`) ; aucun test supprimé.

## Golden
RE-FIGÉ annoncé, dérive prouvée par neutralisation des chemins du tronçon.
