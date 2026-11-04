## 2026-11-04 — Conception FORMES DES PLANTES (reste de D118 (A)) — FIGÉE

Doc : `docs/rendu/pixelart/conception_formes_plantes.md`. Kickoffs : `sprints/rendu/pixelart/sprint_formes_plantes/`, 6 tronçons, golden intact visé.

**Cause de l'effet générique** : 39 espèces sur 40 ont le même squelette moteur après un an, 17 segments et 84,5 cm [`grow_plant` seul, sans lumière, seed 42]. La vue le dessine : sphaigne 89 cm de bois pour 4 cm de hauteur moteur [`full` an 2, n=1 run, VM].

**Décisions de Nico** : port dessiné par la vue pour 33 espèces (7 ports réglés par fiche), tomate, lierre et jasmin gardent leurs segments ; taille d'un clic sur la plante, coupe visible par hints du pont ; formes seules, le reste demeure dans D118 réduite.

**Limites assumées** : la forme ne naît pas de la croissance ; la coupe est visible mais `height_at` ne bouge pas. 

**Ajout après le rapport C de l'an 8** : tronçon ⑤, plus de squelette pour les herbacées à port. CPU an 3 120 → 71 s, segments 15 468 → 1 299, population et espèces de fin d'année identiques [`full`, seed 42, n=1 run par côté, VM, patch mémoire]. Même rapport, D127 : les pires ticks sont de l'attente, pas de la simulation (s122 : 30,7 s pour 2,5 s de CPU [n=1 run, PC]).
