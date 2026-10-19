# ⑤ — Vue et bilan : pleine résolution mesurée, conversion PC, F5 ressenti

> Lire d'abord `CLAUDE.md`, `00_etat.md` (mesures de ①-④ et rapport d'étalonnage de Nico),
> `docs/perf/lod/conception_perf_vue.md` §3.8. Vue C#. Golden intact.

## Objectif
1. **Pleine résolution — mesure seulement** : le monde est rendu dans un `SubViewport` 960×540
   agrandi ×2 (`stretch_shrink = 2` dans `world/WorldView.tscn`). Mesurer au banc ① le coût à
   1920×1080 ×1 (option temporaire de lancement, ex. argument `--capture-*` ; **ne pas** changer
   le réglage par défaut). Attention aux constantes calibrées sur l'échelle interne
   (`world/WorldView.Projection.cs` TileWPx, `WorldView.Etiquettes.cs`). Sortie : un chiffre de
   surcoût par palier, consigné comme donnée d'entrée du sprint « plante assemblée ».
2. **Bilan contre les critères**, converti en chiffres du PC de Nico grâce à l'étalonnage de ① :
   nominal 60 FPS à ×4 (vent + animations vitesse normale), 30 FPS de ×0,5 à ×2 ; accéléré sans
   image > 100 ms. Si le rapport d'étalonnage de Nico manque, le dire et donner les chiffres VM
   bruts — ne pas inventer de conversion.
3. **Vue / F5** : légende F1 à jour (touche du banc, comportement de la vie macro), et une
   procédure F5 courte pour Nico — ressenti seul : « à ×4, c'est fluide ? la vie macro est-elle
   lisible et à la bonne taille ? les pullulations se voient-elles ? le mode accéléré est-il
   agréable ? ».

## Ne pas faire
Ne pas basculer la résolution par défaut. Pas de nouvelle optimisation ici (si un critère n'est
pas tenu, le chiffrer et ouvrir/annoter la dette — en fermer une pour toute dette ouverte).
Pas de `test_epaisseur_500ans`.

## Fin de tronçon (clôture du sprint)
`00_etat.md` bilan final, entrée `journal/` + pointeur `journal.md`, `DETTE.md` (D109, D1 de
D106) et `BACKLOG.md` à jour (prochain : sprint « plante assemblée », avec le chiffre de pleine
résolution), commit.
