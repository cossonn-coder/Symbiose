## 2026-11-02 — Sprint LISIÈRE NUE (D124) — CLOS côté code (①→③)

Ouvert au F5 d'AUTOMNE VISIBLE (Nico : plus de branches sur les arbres de lisière une fois nus, marguerites en
quadrillage). État, bilans et protocole F5 : `sprints/rendu/ambiance/sprint_lisiere_nue/00_etat.md`.

- ① moteur (`0ae40ab`) : `fields/fleurs_lisiere.py`, colonies déterministes par secteur, floraison par couleur, nourriture
  des butineurs (carte mémoïsée × scalaire hebdomadaire), pont 0.6.4. Tick an 2 +4,7 % [n=2 par côté, VM, une mesure sous
  charge 7,13], plantes an 3 660 → 690 [seed 42, n=1 graine].
- ② vue (`67edf20`) : fleurs seulement dans les colonies, butineurs de bord, damier remplacé par du bruit. Draw calls ×0,5
  78 → 78 et ×1 79 → 80 [n=1 run par côté, VM]. En plus du kickoff : rang du fond, limite de bande, couture de friche.
- ③ vue (`4d5c7b0`) : `DecorLayer.Branches.cs`, enveloppe absente en hiver, bouleau nu, touches rousses. Sommets ×1 +3,3 %
  [seed 42, s12, VM, terrain à 4 forêts non mesuré].
- Passe `/refactor` : rien à scinder, maximum 320 LDC (`container.py`) parmi les fichiers touchés.

Golden intact tout le sprint : `ac48b170…`.

Limites ouvertes :
- **D119 (c) reste ouverte** : pommier × butineurs en an 1 de 0/2 à 1/2 semaines [`full`, seed 42, n=1 graine, marge 0,002
  sur le seuil], pollen toujours 0 pendant la floraison. Le pommier fleurit avant les colonies et par temps froid. À trancher
  par Nico : population de départ (touche le golden) ou fenêtre plus précoce.
- Le miel des ruches profite aussi des colonies.
- Aulne et noyer gardent des feuilles sèches (règle shader « tout sauf le bouleau », hors décision de conception), à juger au F5.
- Sous la neige, l'ombre au pied reste un aplat sombre.
- `tests/test_parasite` plante en `IndexError` dans `deposer_litiere` (`_abscission`), déjà sur `2c79791`, avant ce sprint.
  Cause non isolée.

Attend le **F5 de Nico** (`00_etat.md` §F5, 2 minutes). D124 fermée seulement après.

**F5 de Nico, le 2026-11-02** : taches de fleurs, insectes, lisière des 4 saisons et branches validés. D124 fermée. Retours versés en D125 : points blancs en quadrillage l'été (trame `bayer` de la brume chaude, arrivée avec AUTOMNE VISIBLE ⑥), décor absent au-delà de ×4 (`DecorLayer.MaxZoom`), un peu plus de neige.
