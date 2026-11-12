# ③ Le curseur prend l'icône du geste

**Lire avant** : `CLAUDE.md`, `00_etat.md`, doc de conception §5.
**Nature** : C#. **Golden : INTACT**. Reprend D118 (d).

## État du code (vérifié le 2026-11-12)
- `world/WorldView.Curseur.cs` : `Input.SetCustomMouseCursor(texture,
  CursorShape.Arrow, hotspot)` ; main gantée repos/tap ; `TapCurseur()` au clic
  gauche (150 ms) ; `UpdateCurseur()` chaque image ; le losange `PlotHover`
  « respire » quand un geste est armé.
- Le geste actif vit dans `_gesteIndex` (ou son successeur depuis le sprint
  palette : relire `WorldView.Actions.cs` / `WorldView.Tiroir.cs`).
- Le curseur système est dessiné par l'OS, hors SubViewport : non quantifié par le
  post-traitement, d'où l'obligation de peindre avec la palette maître.

## À faire
1. À chaque changement de geste actif : curseur = icône du geste (cuite à
   l'échelle du curseur actuel, ×2), point chaud = pixel actif noté au ②.
   Aucun geste actif → main gantée, inchangée.
2. Sur les panneaux et la barre (zone d'interface), le curseur redevient la main :
   on ne clique pas un bouton avec une bêche. Utiliser le mécanisme le plus simple
   (forme de curseur par `Control`, ou test de survol d'interface déjà présent).
3. Le tap de 150 ms de la main reste pour les clics sans geste ; avec un geste,
   il sera remplacé au ④ par l'animation (laisser ici une image fixe).
4. Limite Godot à respecter : texture de curseur ≤ 256×256, et changer de curseur
   seulement au changement d'état (pas à chaque image).
5. Libérer les textures à la sortie (`LibererCurseur`).
6. Capture VM : le curseur système n'apparaît pas forcément dans les PNG du Movie
   Maker. Le vérifier ; s'il manque, ajouter au mode capture un sprite témoin qui
   dessine la texture du curseur à la position de la souris (`-s X,Y`), actif en
   capture seulement.

## Vérification
`dotnet build` vert ; captures avec 3 gestes différents armés (`-g`), main sur la
barre.

## À ne pas faire
- Pas d'animation (tronçon ④).
- Ne pas remplacer le curseur système par un sprite en jeu normal (latence d'une
  image).
