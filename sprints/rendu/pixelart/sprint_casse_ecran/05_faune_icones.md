# ⑤ Faune en icônes pixel-art

Lire d'abord : `CLAUDE.md`, `00_etat.md` (§Notes ① et ③), `docs/rendu/pixelart/etude_brief_da_16bits.md`
(règle 7 : contour sélectif ; dialecte 3), `docs/rendu/pixelart/conception_casse_ecran.md` §2.
**Golden intact.** Filet : `dotnet build Symbiose.csproj`. Pas d'appel DeepSeek.
Ne JAMAIS lancer `test_epaisseur_500ans`.

## Constat (D112 a, D44 b)
Les bêtes sont dessinées en **rectangles** de taille réelle, une couleur par espèce
(`visuals/MacroLife.cs:61+`, table `Especes`, 14 espèces) ; butineurs dans
`visuals/ForagerLayer.cs`. Les « grands traits noirs » vus par Nico ≈ merle (25×8 cm,
`1e1e22`), « petits traits verts » ≈ chrysope / puceron.

## Objectif
Chaque espèce devient une **petite icône** lisible : silhouette caractéristique vue de
dessus/oblique (oiseau = corps + tête + queue ; hérisson = dôme de piquants ; limace =
ovale allongé + cornes ; coccinelle = dôme rouge + points ; carabe = élytres sombres
irisés ; cloporte = segments ; butineurs = corps + ailes claires), **3-4 tons** de sa propre
rampe (table ①, avec dérive de teinte), **contour 1 px de sa teinte la plus sombre**
(jamais noir — le merle : noir bleuté/brun, pas `#000`), éclat côté soleil (même encodage
indexé que ③). **Taille réelle conservée** : l'icône naît quand la bête atteint quelques px
au palier courant (sous ~2 px elle reste un point de sa couleur moyenne, comme aujourd'hui).
Portraits **précuits par espèce et par taille**, dessinés **en lot** (modèle :
`CarpophoreLayer` / `CarpophoreStyles`) → draw calls inchangés. Animation = SIGNAL
seulement (fondus + sursaut existants, DA « l'animation est un signal ») ; orientation de
l'icône au hash (pas de rotation de sprite : variantes précuites).

## Validation
Planche de la faune à ×2/×4/×8/×16 (ajouter un mode à la planche L si besoin) ; banc ① :
tons, 0 noir, contour non noir ; reconnaissance : une capture par espèce lue avec Read.
Perf : draw calls `MacroLife` avant/après.

## Ne PAS faire
Changer la perception moteur (`fields/population/perception.py`) ; nommer les bêtes à
l'écran (philo naturaliste débutant) ; ajouter de l'errance continue.

## Fin de tronçon
`00_etat.md` §Notes ⑤ ; commit. F5 Nico : trouver un merle, un hérisson, une coccinelle.
