# 2026-11-06 — Sprint VERGER VIVANT (D129) — CLOS côté code (①→④)

Golden `a10b7225…` intact sur les 4 tronçons, aucun re-figeage. Pont 0.6.9. F5 de Nico attendu. Tous les chiffres et leurs limites : `sprints/vegetal/croissance/sprint_verger_vivant/00_etat.md`, bilans ① à ④.

## ① Bourgeons dormants
- Un ligneux sous 85 % de son plafond, vivant, réveille au plus un bourgeon toutes les 4 semaines hors hiver, sur un point éclairé (1,5 × seuil de cladoptose), collet exclu (`sim/growth/dormance.py`).
- Aucune boucle casse-repousse : mêmes cladoptoses avec ou sans réveil [seed 42, n=1 run par côté].
- Appliqué aussi en pré-croissance (choix laissé ouvert par le kickoff) : les arbres de départ sont plus fournis.
- Banc `verger_mur` espacé sur le monde entier : le pommier n'est plus à l'ombre et ne meurt plus.

## ② Floraison réaliste
- Levier d'espèce `floraison_montee`. Cerisier mi-avril avant le pommier, pic 0,94 ; noyer en mai sur 2 semaines.
- Maturations recalées (pommier 15, noyer 15 semaines) pour tenir les fenêtres de fiche.

## ③ Fruits par cohortes
- `Fruit.nombre` ; leviers `fruits_par_site`, `fruit_masse`, `anemo_dose` (noyer 12). Cerisier ~2 000 fruits/an, pommier 158-296, noyers 281-747 [seed 42, n=1 run].
- Écart au kickoff : la litière fruit d'un arbre tombe sous toute la couronne (garde-fou de masse), pas au pied.
- Sol et faune sans dérive, seule la MO fraîche monte (+38 % sur `verger_mur` [n=1 run]).

## ④ Vue
- Densité de fleurs continue, boutons à la montée, pétales au sol au déclin (`PetalLayer.cs`).
- Gerbes de fleurs ×0,5-×4, pièces d'atlas par fleur dès ×8 : écart au kickoff, `KitFleuron` enrichi ne blanchissait pas la couronne.
- Fruits à leur taille de fiche, jusqu'à 500 dessinés par arbre ; `manger` vise ce qui est dessiné.

## Reliquats (versés dans D129)
- Les autres ligneux anémophiles (chêne, hêtre, bouleau, charme, sapin, aulne) fleurissent encore en juin sur 6 semaines.
- Les noyers du banc perdent leurs branches au vent (102 segments en 3 ans [n=1 run]).
- Une partie chargée en pleine défloraison ne montre ses pétales qu'à la semaine suivante.
