## 2026-11-05 — Sprint FORMES DES PLANTES (reste de D118 (A)) — CLOS côté code (①→⑥)

Bilans : `sprints/rendu/pixelart/sprint_formes_plantes/00_etat.md`. Mesures : `mesures/avant.md`, `mesures/apres.md`. Golden intact `a10b7225…` sur les 6 tronçons. Pont 0.6.8. F5 attendu.

**Fait** : banc et 36 fiches, 7 ports dessinés (33 espèces), taille au pied, plus de squelette pour 30 herbacées, haricot autour de son appui, tomate, lierre et jasmin habillés sur leurs segments, fleurs d'arbre et limbes de près en grammaire SNES.

**Effet mesuré** : paires confondues ×4 28 → 0, ×1 14 → 1 ; hauteur hors tolérance ×4 30 → 9 sur 40 [seed 42, n=1 capture, VM]. 16 espèces sur 21 passent par un port en fin d'an 2 [`full`, seed 42, sans automate, n=1 run, VM].

**Non tenu ou à arbitrer** : garde-fou de cuisson, environ +60 % contre +10 % visés [n=3 runs par côté en alternance, charge de départ 1,8 à 4,9], seuil non modifié ; gain CPU du ⑤ −8 % au tick et −12 % à la semaine en an 3 [`full`, seed 42, n=2 runs par côté, charge 5 à 10], pas −41 % ; fraisier et courgette restés à squelette ; masse de coupe sous automate ×8 sur 3 ans [n=1 run par côté] ; 38 pieds sur 40 morts en s26 si la saison tourne sur la planche [départ s20, n=1 run, VM], non diagnostiqué.

**Faible à l'œil** : arbres en pompons à ×4 et ×8, disques verts au sol, haricot accroché jamais vu dans `full`.

**Écart** : le ⑥ devait être vue pure, le pont gagne l'écart du pied à l'appui (lecture pure).
