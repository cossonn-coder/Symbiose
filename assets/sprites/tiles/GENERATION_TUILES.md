# Génération des sprites tuiles — cahier des charges + prompt LLM

> Rédigé le 2026-06-10 (sprint Intégration t2). Les PNG actuels (`tile_terre`,
> `tile_argile`, `tile_sable`) sont **inutilisables pour une grille jointive** :
> fond gris du damier de transparence **cuit dans l'image** (alpha=255 partout)
> et **tailles incohérentes** (terre 78×57, argile/sable 32×23). En attendant le
> ré-export, Godot affiche des **placeholders procéduraux** (`WorldView.cs`).
> Rien n'est supprimé : les PNG actuels restent en place.

## Spécifications exactes (mesurées sur tile_terre.png, la référence)

| Propriété | Valeur |
|---|---|
| Canvas | **78 × 57 px**, PNG **RGBA**, fond **alpha = 0** (vraie transparence) |
| Losange (face sup.) | **78 × 39 px**, iso 2:1 exact — sommet nord à (39, 0), pointe est (77, 19), pointe sud (39, 38), pointe ouest (0, 19) |
| Socle (épaisseur) | **18 px** extrudés vers le bas sous les 2 arêtes inférieures (39 + 18 = 57) |
| Style | Pixel art net, **aucun anti-aliasing** (bords durs), pas d'ombre portée |
| Contour | 1 px très sombre autour de la silhouette (comme l'actuel) |
| Éclairage | Face supérieure claire, faces du socle ≈ −35 % de luminosité |
| Échelle jeu | 1 tuile = 1 plot de 50 × 50 cm, rendu filtre Nearest |

## Palettes (teinte dominante de la face supérieure)

- `tile_terre.png` — brun terre `#967a64`, mouchetures plus sombres/claires
- `tile_argile.png` — ocre orangé `#cd7434`, surface légèrement craquelée
- `tile_sable.png` — beige clair `#f1e9bb`, grain fin
- `tile_roche.png` — gris minéral `#8d8881`, facettes (optionnel, même gabarit)

## Prompt à copier dans le LLM générateur d'images

```
Pixel art isometric floor tile for a 2D garden simulation game.
EXACT format: 78x57 pixel PNG with a FULLY TRANSPARENT background
(real alpha channel — absolutely NO gray checkerboard pattern drawn
into the image, no background color).
Geometry: a 2:1 isometric diamond (rhombus), 78 px wide and 39 px tall,
top vertex centered at the top edge; below it an 18 px thick extruded
soil edge (left and right lower faces), total image height 57 px.
Style: clean pixel art, hard edges, NO anti-aliasing, no drop shadow,
top face brightly lit, side faces about 35% darker, 1 px dark outline
around the silhouette.
Subject: [VARIANTE — voir ci-dessous]
```

Variantes (remplacer `[VARIANTE]`) :
- terre : `rich brown garden soil, dominant color #967a64, subtle darker speckles`
- argile : `orange clay soil, dominant color #cd7434, faint dry cracks`
- sable : `pale sand, dominant color #f1e9bb, fine grain dithering`
- roche : `gray stone, dominant color #8d8881, faceted mineral surface`

## Post-traitement (quasi inévitable)

Les générateurs sortent rarement la taille exacte ni un vrai alpha. Pipeline de
rattrapage (Pillow dans un venv, cf. mémoire « rendu SVG sur la VM ») :

1. **Taille** : générer grand (ex. 624×456 = ×8) puis réduire en **Nearest** :
   `img.resize((78, 57), Image.NEAREST)`
2. **Alpha** : si le fond revient cuit (gris/blanc), le percer par chromakey :
   tout pixel « neutre » (|R−G| ≤ 6, |G−B| ≤ 6, luminosité > 120) **hors du
   gabarit du losange** → alpha 0. Ne jamais chromakeyer à l'intérieur du
   gabarit (la texture contient des pixels neutres légitimes).
3. **Contrôle** : vérifier `im.mode == "RGBA"` et qu'il existe des pixels
   d'alpha 0 aux 4 coins du canvas.

Une fois les 3-4 PNG conformes déposés ici, rebrancher les sprites dans
`world/WorldView.cs` (remplacer `MakeLozenge` par un `Sprite2D` +
`SpriteLoader.GetTile(soil)`, ancrage : centre du losange = centre du sprite
décalé du demi-socle, soit offset y = −9 px).
