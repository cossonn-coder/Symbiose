# ③ Vue + banc — litière herbacée visible, consoudes lisibles, info-bulles vérifiées

Lire d'abord `docs/vegetal/sante/conception_lisibilite_bilan.md` (§2.3, §2.4). Tronçon
**vue** final du sprint (règle projet : la vue Godot clôt toujours le sprint).

## A. Litière d'herbacée visible
- Constat : le moteur dépose bien la litière à la mort d'un poivron (+~1,3 par plot, seed
  42, n=1) ; le tissu `herbace` est dessiné en amas abstraits par `visuals/LitterLayer.cs`,
  quasi invisible. Seul `feuille` a un rendu figuratif (`visuals/LeafLitterLayer.cs`,
  format compact `[r, c, tissu_dominant, masse, age_sem, bois × 3, …]`).
- Intention : la litière `herbace` (et les tissus mous voisins si c'est naturel — à
  trancher en lisant les tissus de `TISSU_ORDER` côté moteur) se dessine en **tiges
  couchées couleur paille** qui brunissent vers l'humus avec `age_sem`, semis en lot
  déterministe, même patron et même coût que `LeafLitterLayer`. Un fichier = une
  responsabilité (nouveau calque ou extension propre, ≤ 300 LDC).
- Vérifie que le pont expose ce qu'il faut (tissu dominant ou masse par tissu) ; si une
  clé manque, ajoute-la et bump la version du pont.
- Pas de geste neuf : `composter` ramasse déjà la litière tendre
  (`sim/actions/compost.py`). Vérifie en test que composter sur le plot d'un poivron mort
  retire bien sa litière `herbace`.

## B. Banc `plante_vivante` lisible (`data/code/bancs/plante_vivante.py`)
- Consoudes broutées : partent à 0,35 au lieu de 0,2 au premier tick observé — trouve
  pourquoi (pré-tick, refeuillaison du tick d'init…) et fais qu'on **voie** 0,2.
- Donne-leur aussi des **réserves basses** : la refeuillaison est payée sur les réserves
  (≤ ½ réserve/sem), la repousse s'étale. Cible : écart visible témoin / broutées
  pendant **≥ 10 semaines** simulées (mesure-le).
- La densité de feuilles doit se voir à ×4 : si le port rosette à 1 segment ne montre pas
  la différence, rends la scène lisible (stade plus développé, autre port…) — décision de
  calibrage, à consigner.
- Mets à jour le docstring du banc (chiffres mesurés, [seed 42, n=1]).

## C. Info-bulles vérifiées sur la VM
- Le pont 0.6.21 envoie `feuillage_bilan`/`reserves` ; `PlantRenderer.EtatBilan`
  (`visuals/PlantRenderer.Bilan.cs`) choisit « épuisé » / « refait » / « clairsemé » ;
  `WorldView.InfoBulle.cs` les affiche au survol.
- Utilise le banc de capture VM (`tools/capture_vm.sh`, `tools/lib_vm_godot.sh`) pour
  produire des PNG où l'on voit : la phrase sur un poivron qui ternit, la phrase sur une
  consoude qui refait ses feuilles, la litière herbacée au sol. Si le survol ne peut pas
  être simulé par le banc de capture, dis-le et trouve l'équivalent le plus proche
  (forcer le survol en mode capture), sans code de triche en jeu.
- Range les PNG dans `sprints/vegetal/sante/sprint_lisibilite_bilan/captures/`.

## Golden
**INTACT** (hash courant dans `00_etat.md`, re-figé au ①). Bancs = golden neutre.

## Build / tests
`dotnet build Symbiose.csproj` vert ; tests du pont et du banc verts.

## F5 pour Nico (à écrire dans `00_etat.md`)
Banc `plante_vivante` : consoudes broutées visiblement moins feuillues pendant plusieurs
minutes ; tas de tiges paille au pied du mur nord après la mort des poivrons ; geste
composter sur ce tas ; phrases d'info-bulle au survol.

## Clôture côté doc (l'orchestrateur fait journal, refactor, push)
`00_etat.md` §REPRISE → suite `/sprint-auto sprint_stress_au_bilan` ; DETTE D141 fermée
(si ② l'a fermée) ; backlog `docs/vegetal/sante/backlog_sante.md` à jour.
