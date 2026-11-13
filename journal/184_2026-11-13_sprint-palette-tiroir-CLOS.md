# 2026-11-13 — Sprint PALETTE & TIROIR — CLOS côté code (①→③)

Deuxième des trois sprints de la refonte de l'accès aux gestes
(`docs/joueur/gestes/conception_refonte_palette.md` §4). Trois tronçons, golden
`b4a921f8…` intact du début à la fin. Pont **0.6.13**. F5 attendu.

## Ce qui change
- **① Tiroir par familles** : bouton en bas de la barre et touche `Q`. Tous les gestes
  ouverts, une rangée par famille (ordre du pont). Clic gauche = geste en main, même
  sans case (le bouton porte alors son pictogramme) ; clic droit = « case 1…0 ».
  `world/TiroirPanel.cs`, `world/TiroirBouton.cs`, `world/WorldView.Tiroir.cs`.
- **② Réglages contextuels** : graines, substrats, paillis en pastilles cliquables à
  hauteur du geste actif ; fin des touches S, B, N. `world/WorldView.Reglages.cs`,
  `world/ReglagePastille.cs`.
- **③ Pressentis et finitions** : silhouettes inertes dans le tiroir, la phrase du
  pont pour seule info-bulle ; le bouton bat quand un geste s'ouvre ou qu'un pressenti
  apparaît ; Ctrl+molette fait défiler le geste actif ; D118 (b) et (c) ; macros K/J
  débranchées (code conservé).

## Décisions et écarts
- **Écart au cadre « pure vue C# »** (prémisse fausse du kickoff ② : le stock de mulch
  n'était pas au snapshot) : deux clés de lecture pure ajoutées au bloc `player` du
  pont, `paillis_dispo` (noms, aucune quantité) et `graines_espece`. Aucun fichier du
  moteur touché, golden identique. Décision prise en exécution, à valider par Nico.
- **D118 (c)** : cause isolée par un banc avant correction (`capture_vm.sh -M`) — le
  tronc d'un arbre est dessiné hors de l'ellipse de couronne qui servait au clic.
  13/15 → 15/15 milieux de segments vus [×2, n=1 banc, 2 espèces].
- Un clic hors du tiroir le ferme sans agir sur le jardin.

## Reste
- F5 de Nico : recette dans `sprints/joueur/gestes/sprint_palette_tiroir/00_etat.md`.
- Pictogrammes en double dans le tiroir et pastilles de graines peu distinctes :
  sujet du sprint `icones_curseur`.
