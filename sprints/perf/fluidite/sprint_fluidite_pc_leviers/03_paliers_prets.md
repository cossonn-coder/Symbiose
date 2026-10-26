# ③ Décor et plantes prêts par palier (plus d'à-coup au zoom)

**Golden** : intact (vue C# seule). **Build** vert.

## Constat
Changer de palier redessine tout le décor (`visuals/DecorLayer.cs` reconstruit son lot au
changement de palier, `_lastZoom`) : ×4 ~165 ms, ×2 66-106 ms [VM, sprint FLUIDITÉ PC ④] ;
et invalide les plantes (`PlantRenderer.Invalidate` → file de cuisson ; sans image cuite,
`DessinerPlante` trace le dessin VECTORIEL complet en direct, `PlantRenderer.Bake.cs`).
`plantes _Draw` = 21 ms/image en phase C au PC [n=1 run, PC]. Les chiffres « avant »
détaillés sont ceux du tronçon ① (`00_etat.md`).

## À faire
1. **Décor** : garder une maille (ou un lot prêt) **par palier** visible (×0,5, ×1, ×2, ×4 ;
   `MaxZoom = 4`). Construite une fois ; changer de palier = permuter, pas reconstruire.
   Les mailles des autres paliers se construisent **étalées** (budget ~8 ms par image, au
   démarrage ou au premier besoin) ; elles s'invalident sur les mêmes signaux qu'aujourd'hui
   (rotation, ceinture qui change). Le scintillement de l'eau reste sur son nœud.
   Si la construction peut se faire hors du fil principal (calcul pur des sommets, maille
   Godot créée sur le fil principal), c'est permis — vérifier la sûreté au code.
2. **Plantes** : avec l'outil ①, établir ce qui coûte au changement de palier (dessin
   vectoriel direct des plantes sans image ? flot de cuisson ?). Levier attendu : pendant
   l'attente de re-cuisson, NE PAS retracer le vectoriel complet — garder l'image du palier
   précédent mise à l'échelle, ou n'afficher que le tapis — si l'outil ① le confirme.
   Si ce n'est pas le poste, ne rien forcer : consigner ce qui coûte réellement.
3. Mesurer avec le balayage ① (avant/après, pire image par paire de paliers) + banc 3 phases
   VM (phase C : `plantes _Draw`). Captures avant/après dans `captures_03/` (aucune
   différence visuelle attendue une fois la cuisson finie).

## Ne PAS faire
Changer le style des paliers (la cohérence DA inter-paliers est en dette D112). Supprimer du
code (l'ancien chemin peut rester, non appelé, commenté). Toucher au moteur.

## F5 Nico
Zoomer / dézoomer : l'à-coup a-t-il disparu ? Rapport de l'outil ① à coller.
