# ④ Recettes manquantes : trèfle, thym, lavande, fétuque, blé, fleurons

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (comptes rendus ② tailles et ③ couches), la
conception, et dans `../sprint_precuisson_splats/00_etat.md` la liste « Reste DESSINÉ » du
④bis et la lecture des captures du ⑤ (fleuron sans cœur).

## Objectif
Faire passer en pièces splat ce qui est encore dessiné **sur les herbacées**, faute de
recette. Les brins et rubans des graminées et les masses ×4 des arbres sont **hors
périmètre** : ils vont en S2.

## À faire (recette + crochet d'une ligne, ancien dessin intact derrière)
1. **Trèfle** : feuille de ~3 cm à 3 folioles. Une **variante rare à 4 folioles**, tirée
   au hash du pied et de la feuille (zéro hasard vivant, philo #3), environ 1 feuille sur
   quelques centaines (à régler). Crochet dans le chemin des feuilles du trèfle
   (`PlantRenderer.Prairie.cs` / `PortTapis.cs`, à localiser).
2. **Thym** : les « grains » de la masse du buisson (1,9 cm) deviennent un petit rameau
   ligneux couvert de feuilles minuscules.
3. **Lavande** : les « lames » (8 cm), étroites et gris-vert, en touffe.
   Pour 2 et 3, crochet dans `PlantRenderer.PortBuisson.cs`. Le portrait raté du thym
   (« feuilles qui flottent détachées, pas de coussinet ») indique que la masse doit former
   un coussin.
4. **Fétuque** : panicule fine d'épillets roux de 0,5 cm.
5. **Blé** : anthères pendantes. Couche ou pièce, visible aux paliers hauts seulement (même
   logique de seuil que ③).
6. **Fleurons** du kit (`fleuron`, plantes sans fiche, ×0,5-×2) : la couche cœur est vide
   aux petites tailles, donc le cœur jaune disparaît. Le cuire pour qu'il survive à 1-3 px
   (cœur agrandi ou pixel forcé à la réduction).

Toutes ces recettes sont cuites aux 3 tailles du ② et portent leurs couches de détail
(③). Elles s'ajoutent à la bibliothèque et au contrôle (`controle_feuilles.js` /
`controle_organes.js`).

## Mesures attendues
Captures avant/après (Maj+F11) de la prairie (`planche_especes` : trèfle 3 cm, fétuque),
du thym, de la lavande et du blé, de ×0,5 à ×32 (`capture_vm.sh -l`), plus la planche du
kit (`-k`) pour les fleurons. Poids et temps de cuisson.

## Ne pas faire
- Toucher les brins de graminées, le bois ou les arbres (S2).
- Toucher `data/code/`.
- Lancer `test_epaisseur_500ans`, appeler DeepSeek.

## Fin
Build vert, golden intact, LDC. Compte rendu ④ avec ce qui reste dessiné sur les herbacées
(doit tendre vers rien, hors brins).
