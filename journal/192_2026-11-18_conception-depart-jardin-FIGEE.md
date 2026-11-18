# 2026-11-18 — F5 de D139 + conception DÉPART DU JARDIN (D140) FIGÉE

## F5 de `sprint_caracteres_vivants` (Nico)
Caractères vus ; nuancier hors palette accepté (visuel reporté). Retours : toutes les
cultivées mortes au départ, éclaboussures de pluie qui suivent la caméra, Ctrl+molette
pour les graines, pâturin à rendre réaliste, coûts payés par des gènes non exprimés,
trèfle envahissant (73 % du monde à l'an 3 [1 run]). → D139 close, D140 ouverte.

## Diagnostic (VM, seed 42)
Les 68 cultivées du monde `full` sont repiquées en semaine 1 (≈ 20 mars) ; nuits −0,4 /
… / −2,8 °C (gelée tardive s4) ; > 7 °C seulement dès s10 → mortes en 2 semaines.
Scénario faux, moteur réaliste — mais `lim_gel` de la tomate à +2,8 °C (gène de variété).
Le monde `full` ne contient que 15 espèces sur 52.

## Décisions (Nico)
Ouverture `full` juste après les saints de glace (semaine 10) ; au moins une plante MÛRE
de chaque espèce du catalogue, arbres à l'âge de leur première fructification ; toute
espèce ajoutée devra entrer dans le monde `full` ; semis + repiquage différé + semis
d'intérieur ; pâturin réaliste ; un gène non exprimé ne coûte rien. Trèfle : non mesuré
pour l'instant.

## Sprint
`sprints/vegetal/genetique/sprint_depart_jardin/` : ① pâturin + gènes muets (re-figé) ·
② froid des tendres + chronique (re-figé) · ③ monde `full` complet (intact, perf mesurée)
· ④ pot dans la maison + `repiquer` · ⑤ automate repique · ⑥ vue + banc.
