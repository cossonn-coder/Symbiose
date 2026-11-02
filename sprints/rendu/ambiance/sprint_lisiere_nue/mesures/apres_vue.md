# Mesures du tronçon ② (vue : fleurs, butineurs, damier)

`tools/perf_vm.sh -b full -w 12 -k 3 -n 5`, seed 42, llvmpipe, charge VM 4 à 9. Les FPS ne valent pas ceux du PC.

| Palier | Draw calls avant → après | Sommets du décor avant → après | Primitives avant → après |
|---|---|---|---|
| ×0,5 | 78 → 78 [n=1 run par côté, VM] | 37 182 → 42 126 (+13 %) [seed 42, s12, VM] | 27 861 → 29 335 [n=5 relevés, VM] |
| ×1 | 79 → 80 [n=1 run par côté, VM] | 91 692 → 101 538 (+11 %) [seed 42, s12, VM] | 59 836 → 63 181 [n=5 relevés, VM] |

- Le +1 à ×1 = le lot de `ForagerLayer`, vide à ce palier avant le sprint. À ×4, il existait déjà : même lot.
- ×4 après : 65 draw calls [n=1 run, VM, pas de relevé « avant »].
- Reconstruction : 1 seule « maille construite » à ×1 sur 8 semaines de turbo [n=1 run, seed 42, VM].

## Captures lues (`full` seed 42, banc `smoke -B`, ×0,5 et ×1, s6 s12 s20 s30 ; ×2 s9)

- s6 (semaine 7) : bouton d'or dense au sud, marguerites qui s'ouvrent, grands vides entre les taches.
- s12 (semaine 13) : taches en place, sous la pluie de ce jour-là ; nappes de saison en cours de transition, d'aspect « camouflage » à ×1 sur 2 ou 3 semaines.
- s20 (été) : plus aucune fleur, conforme aux fenêtres du pont. Plus de damier ; la frange claire ondule.
- s30 (automne) : aucune fleur, prairie en paille, nappes souples.
- ×2 s9 : insectes (abeille, papillon, syrphe) sur le secteur sud ; ils changent de place entre deux images.
- ×0,5 : aucun insecte, par choix (point d'un pixel, illisible).

## Alignements trouvés et traités en plus du kickoff

- Rang du fond (cellules de 40 cm × 27 m) : une phase propre à chacune donnait des barres sombres aux transitions. Phase fixe.
- Fin de bande à `DepthCm` : droite iso + saut de ton. Limite sinueuse (`BordFond`), même ton.
- Couture friche / prairie : droite filant jusqu'au bord du cadre. La friche s'arrête à sa bande et s'effiloche à ses deux bouts.

## Restent visibles

- Friche : le contour extérieur de son fond sombre garde des segments droits en été.
- Givre de printemps (×2 s9) : plaques gris-bleu très marquées sur la prairie, par ciel dégagé. Non touché par ce tronçon, à juger au F5.
