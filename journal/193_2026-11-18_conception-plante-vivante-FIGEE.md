# 2026-11-18 — Conception PLANTE VIVANTE (D140 G) FIGÉE : un bilan, pas des PV

## Constat
`sprint_depart_jardin` ③ puis F5 de Nico : à l'ouverture du monde `full` (s10), presque
toutes les plantes posées meurent « d'herbivorie » en 6 semaines, chênes de 25 ans
compris ; des centaines de semis de chêne au pied des arbres morts.

## Diagnostic (VM, monde `full`, seed 42, n=1 par cas)
Morts des 136 posées à s21 : tel quel 121 ; faune pré-roulée s1→s9 130 (pire) ;
prédateurs seuls pré-roulés 97 ; `stress_memory` amorcée 49. Les prédateurs existent et
régulent ; la règle de dégât retire 1/3 de vitalité/sem dès un seuil inférieur à
l'équilibre normal des ravageurs, même coup pour semis et chêne ; seul rempart une porte
sur `stress_memory`. Semis de chêne = cascade de rejets de souche (un rejet mort devient
une souche neuve) : 9 → 27 → 75 → 153 par vague.

## Décisions (Nico)
La règle est aberrante. Les plantes n'ont pas de PV : elles vivent d'un bilan
(photosynthèse, entretien, échange avec les champignons, plage d'eau/lumière/chaleur par
espèce). Tout le vivant végétal passe au bilan ; `vitalite` = lecture ; plus de mort au
sort. Critère d'ouverture : 0 arbre posé mort, ≤ 25 % d'herbacées, ≤ 4 rejets par arbre.

## Sprints
`docs/vegetal/sante/conception_plante_vivante.md` →
`sprints/vegetal/sante/sprint_plante_vivante/` (A : socle en ombre, bascule, herbivorie
par atteinte, souches, ouverture, vue) puis `sprint_stress_au_bilan/` (B : sécheresse et
embolie, froid/gel/brûlure, maladies et racines, vieillesse/cycle/mycorhize, vue). Puis
reprise de `sprint_depart_jardin` ④.
