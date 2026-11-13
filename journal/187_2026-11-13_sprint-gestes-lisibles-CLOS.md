# 2026-11-13 — Sprint GESTES LISIBLES — CLOS côté code (①→⑥)

Reprend D136 (a)-(f), retour F5 de la refonte des gestes. Conception
`docs/joueur/gestes/conception_gestes_lisibles.md`. Six tronçons en `/sprint-auto`,
golden `b4a921f8…` intact du début à la fin, pont 0.6.14 → 0.6.16. F5 attendu.

## Ce qui change
- **① Moteur + pont** : registre `sim/traces_sol.py` (la vue ne dessine que ce que le
  moteur note), `sol_sec`, `volants` (`ecraser` refuse ce qui vole), déraciné couché,
  pot hors du jardin refusé, phrases en mots (`tools/simserver/mots.py`), quantités
  rééquilibrées à l'excès (glanage ×2, miel ×100 au tick — aucune ruche au golden).
- **② Curseur** : 46 gestes en 4 à 6 images précuites (rotation au pivot, vote 4×4),
  sécateur = tailler, scie = couper, `pincer` et `glaner` redessinés.
- **③ Sol-canvas** : traces (mottes, raies, botte, voile, auréole, cuvette), paillis par
  matière, tas qui grossissent, pluie, craquelé ; le gisant se couche vraiment.
- **④ Objet en main** : bouture, greffon, pelletée, pot qui suit la souris ; habitat
  d'auxiliaires dessiné ; catalogue trié ; récolte au fruit mûr.
- **⑤ Automate** : actif fenêtre fermée (touche A), gestes joués en sprite monde, mode
  testeur (touche B) qui déroule le plan de test d'un banc par le chemin du clic.
- **⑥ Banc et recette** : banc `gestes_lisibles` (une cible valide par geste, 25 gestes
  au plan), oracle `tests/bancs/test_gestes_lisibles.py` (26/26), capture VM en mode
  testeur, recette F5 dans `00_etat.md`. Perf du banc ×2 : 21,2 FPS [VM logicielle, n=8 relevés
  de 1 s], 84 draw calls, aucun gel.

## Défauts trouvés et corrigés au ⑥
- **Grelinette cassée depuis la vue** : Maj+clic partait sans cible, le pont la refusait
  (« tuile introuvable »). La vue envoie maintenant le plot cliqué.
- **Écraser un volant** : la vue ne désignait jamais un volant, le défaut « puceron » du
  pont écrasait alors un puceron invisible. Un volant seul sous le pied est désigné et
  le pont répond « ça s'envole ». Les butineurs (abeille…) restent hors d'atteinte : ce
  sont des agents des fleurs, pas des sprites de plot.
- **Testeur et récolte** : le plan donne le pied ; le testeur vise un fruit mûr dessiné.

## Reste
- F5 de Nico (recette dans `sprints/joueur/gestes/sprint_gestes_lisibles/00_etat.md`).
- D136 (g) structures en volume, (h) paysage après la rivière ; D137 fruits récoltés ;
  `serialize.py` à 409 LDC à scinder (`/refactor`).
