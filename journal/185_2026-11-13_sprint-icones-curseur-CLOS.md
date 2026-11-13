# 2026-11-13 — Sprint ICÔNES & CURSEUR — CLOS côté code (①→④)

Troisième et dernier sprint de la refonte de l'accès aux gestes
(`docs/joueur/gestes/conception_refonte_palette.md` §5). Quatre tronçons, pure vue
C#, golden `b4a921f8…` intact du début à la fin. Pont inchangé (0.6.13). F5 attendu.
La refonte (acces_gestes → palette_tiroir → icones_curseur) est close côté code.

## Ce qui change
- **① Moteur d'icônes** : grilles de caractères 16×16, alphabet de 16 lettres pris
  dans `Palette16.Maitre`, cuisson en cache (`visuals/IconeGeste.cs`), planche de
  contrôle (`capture_vm.sh -I`), `GesteIcon` branché (ancien dessin gardé en repli).
- **② Les icônes** : 46 grilles (45 gestes + `planter_conteneur`), 8 familles dans
  `visuals/icones/`, points chauds (`IconesPointsChauds.cs`), vérification de démarrage.
- **③ Curseur** : l'icône du geste armé sur la forme système `Cross`, point chaud au
  pixel actif ; la main gantée revient seule sur l'interface. Témoin de capture.
- **④ Animations** : table verbe → mouvement (`icones/IconesMouvements.cs`), sept
  mouvements (verser, couper, frapper, poser, ramasser, remuer, écraser) fabriqués en
  transformant l'icône (`visuals/AnimationGeste.cs`), joués une fois à la réponse
  `applied` ; secousse de 2 images au refus ; une image « tap » au clic. Lecture dans
  `world/WorldView.CurseurAnim.cs`. Planche `capture_vm.sh -W`.

## Décisions et écarts (④)
- Images d'animation données à l'OS sous forme d'`Image` CPU, pas de texture : une
  texture serait relue depuis la carte graphique à chaque image.
- Une recette par mouvement, avec une « avance » dirigée du centre vers le point
  chaud : une seule recette sert aux 12 outils de « frapper ». Effets peints derrière
  le dessin (une miette ne troue pas une lame).
- Au clic, une image « tap » de l'icône (réponse immédiate, et seul signe du premier
  clic d'un geste à deux temps).
- La secousse ne joue qu'au refus du pont, pas aux refus de désignation côté vue
  (« aucune tuile ici ») : ceux-ci gardent le seul clignotement du message.

## Reste
- F5 de Nico : recette dans `sprints/joueur/gestes/sprint_icones_curseur/00_etat.md`.
- Hors DA, relevés en couleurs brutes et non traités : `WorldView.Hud`, `SkyPanel`,
  `SupportRenderer`, `CompostStructure`, `MulchLayer`, `CoverLayer`,
  `ContainerStructure` (reste dans D118).
