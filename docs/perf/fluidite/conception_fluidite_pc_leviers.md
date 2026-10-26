# Conception — FLUIDITÉ PC : leviers (2ᵉ `/conception D116`, figée le 2026-10-26)

> Suite de `conception_fluidite_pc.md` (diagnostic). Sprint :
> `sprints/perf/fluidite/sprint_fluidite_pc_leviers/`. Golden `fecccded…` intact partout.

## 1. Cible (inchangée)
PC de Nico (i5-4200H, 2 cœurs / 4 threads, HD 4600, ANGLE D3D11), an 2, 1 s/sem demandée →
**≤ 2 s/sem effectives** et **aucune image > 100 ms**.

## 2. Ce que le run PC 3 phases a établi [n=1 run, PC, s90 an 2, ×4, graine 1521550718]
| Phase | s/sem | tick moteur | step vu par la vue | images moy. | > 100 ms | rendu CPU | draw calls |
|---|---|---|---|---|---|---|---|
| C moteur en pause | — | — | — | 244,8 ms (4,1 FPS) | 70/83 | 116,8 ms | 861 |
| A normal | 6,26 | 3 179 ms | 5 221 ms | 108,4 ms (9,2 FPS) | 63/231 | 44,4 ms | 449 |
| B rendu suspendu | 2,27 | 1 572 ms | 2 454 ms | — | — | — | — |

Lectures :
1. **Moteur seul** : 2,27 s/sem → la cible est manquée même sans rendu. Surcoût du pont
   ≈ 880 ms/step (step vu − tick) : sérialisation d'une réponse de 2,2 Mo, parse JSON
   192 ms, lecture plantes 173 ms.
2. **Le rendu double le tick** (A 3 179 / B 1 572 ms) : contention CPU côté moteur malgré la
   priorité BelowNormal. Tout CPU rendu par la vue profite au moteur.
3. **Images lentes = rendu seul trop lourd** : moteur en pause, les images sont PIRES
   (contention réfutée pour les images). Biais : C passe en premier sur la scène la plus
   chargée (285 fleurs pollinisées, 53 butineurs ; A finit à 116 fleurs, 20 butineurs).
4. **Butineurs _Draw** 29 ms/image, pics 108 ms (C). Vérifié au code : un `DrawCircle` par
   grain de pollen (`visuals/PollenLot.cs:131-138`, ≤ 8 par fleur) et par butineur
   (`ForagerLayer.cs`) → ~2 300 cercles [estimation code] dont les commandes repartent au
   rendu à chaque image (rendu CPU 117 ms en C).
5. **Plantes _Draw** 21 ms/image (C) : chaque plante dessine son image cuite — ou, sans
   image, son dessin VECTORIEL complet en direct (`PlantRenderer.Bake.cs` `DessinerPlante`).
6. Au changement de palier : redessin complet du décor (×4 ~165 ms [n=2 runs, VM]) +
   invalidation des plantes → à-coup ressenti par Nico.

## 3. Arbitrages (Nico, 2026-10-26)
- **Vue d'abord, re-mesure PC, puis le reste.** Le moteur Python (tick) n'est PAS optimisé
  dans ce sprint ; il se décide sur le run PC suivant (3ᵉ temps de D116).
- **Le pont** (delta des segments) EST dans ce sprint : la phase B montre que la cible est
  manquée même sans rendu, et le surcoût du pont est mesuré (≈ 880 ms/step).
- **Outil à-coup de zoom** : demandé par Nico (« un outil qui extrait cette information quand
  je zoome et dézoome »).
- **Lisière côté caméra** : les tuiles du jardin passent au-dessus des arbres de la lisière
  au SE → l'illusion casse. Corrigé ici (petit, vue).
- **Hors périmètre, inscrit en dette D112** : décor animé au vent et à la lumière ; soleil
  visible sur les plantes (face éclairée) ; cohérence de DA inter-paliers (modèle = ×1 avec
  contour noir, `PlantRenderer.Kit.cs:37-38` ; chaque palier plus fin = même idée + plus de
  détails, assets prêts par palier ; deux méthodes : agrandir ×0,5 et ajouter, ou partir de
  ×32 et retirer) ; maison en verre (D112 b). Le décor absent au-delà de ×4 est VOULU
  (`DecorLayer.MaxZoom = 4`, la lisière sort du cadre).

## 4. Leviers retenus
- **L1 Outil zoom** — journal par changement de palier (avant → après, redessin décor, plantes
  invalidées / file de cuisson, pire image et somme sur ~1 s après), rapport copiable sur une
  touche libre ; balayage scripté en capture VM.
- **L2 Butineurs + pollen en lot** — une géométrie unique (`LotTriangles`, déjà utilisé par le
  décor et la litière), points pixel-art (petits carrés / losanges) au lieu de cercles
  polygonaux. Même rendu perçu, même cadence d'animation.
- **L3 Plantes et décor prêts par palier** — le décor garde une maille par palier
  (×0,5/×1/×2/×4), construite une fois (étalée au démarrage) : changer de zoom = permuter.
  Plantes : plus de dessin vectoriel en direct en attendant la cuisson si L1 montre que
  c'est lui qui coûte (garder l'image précédente, ou rien une image).
- **L4 Pont en delta** — mode **opt-in** par requête (la vue le demande ; le mode complet reste
  le défaut → tests et outils intacts) : segments avec **semaine de naissance** au lieu de
  `age_weeks`, envoi des seuls segments changés par plante, gènes au premier envoi, plantes
  disparues listées ; resynchronisation complète sur demande. Pont 0.6.0. Test d'équivalence :
  l'état reconstruit par application des deltas = le snapshot complet.
- **L5 Lisière devant** — les pièces HAUTES des bords côté caméra (arbres, houppiers,
  roseaux, falaise) passent dans une couche au-dessus du sol (et devant ce qu'elles masquent
  réellement), selon la rotation de vue.

## 5. Coût / gains attendus [estimations, non mesurées]
L2 : l'essentiel des 29 ms butineurs et une grosse part du rendu CPU en scène fleurie.
L3 : supprime le pic de redessin au zoom. L4 : −200 à −300 ms/step. Le moteur seul restant à
~1,57 s de tick, **2 s/sem exigera probablement un levier moteur** au 3ᵉ temps.

## 6. Tronçons
① outil zoom · ② butineurs/pollen en lot · ③ décor et plantes prêts par palier · ④ pont delta ·
⑤ lisière devant + bilan VM + protocole PC + dette.
