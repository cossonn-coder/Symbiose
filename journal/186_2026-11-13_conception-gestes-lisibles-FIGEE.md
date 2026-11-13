# 2026-11-13 — Conception GESTES LISIBLES figée (D136 (a)-(f))

`/conception` après le F5 de la refonte des gestes. Doc :
`docs/joueur/gestes/conception_gestes_lisibles.md`. Sprint :
`sprints/joueur/gestes/sprint_gestes_lisibles/` (6 tronçons, golden intact visé).

## Constats au code
- Les animations du curseur n'étaient que l'icône décalée de 1 à 3 px de grille : invisible
  pour les gestes de coupe.
- `becher` / `grelinette` n'écrivent que des champs invisibles : rien à dessiner sans mémoire.
- Messages du pont chiffrés (contre la philo #5) et quantités minuscules (glaner, épandre, miel).

## Décisions de Nico
- L'outil bouge au curseur (images précuites), la conséquence se voit au sol.
- Le sol est un **canvas** : gestes et événements y laissent des traces ; registre de traces
  côté moteur, « on n'invente pas » côté vue. Ce sprint pose le canvas + pluie + sécheresse ;
  D108 le remplira.
- Rééquilibrer les quantités à l'excès pour tester.
- Outils : tous à trouver, fabriquer ou réparer (mini-jeu visuel, manche de hêtre…) →
  `sprint_outils_atelier`, à concevoir ; on ne touche à rien des outils d'ici là.
- Automate : un « semblant d'âme », qui joue pour la diversité, la récolte, la luxuriance →
  `sprint_automate_intention`, à concevoir. Dans ce sprint : actif fenêtre fermée + mode
  testeur (plan de test déroulé par le chemin du clic joueur).
- Devenir des fruits récoltés → D137.

## Suite
`/sprint-auto sprint_gestes_lisibles`, puis `/conception` outils_atelier, puis
automate_intention.
