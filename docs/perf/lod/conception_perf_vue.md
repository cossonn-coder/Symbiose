# Conception — PERF VUE : 60 FPS sur le PC de Nico

> Figée le 2026-10-19 (`/conception`, après le F5 de RENDU VISIBLE / D106).
> Sprint : `sprints/perf/lod/sprint_perf_vue/`. Suite prévue : sprint « plante assemblée ».

## 1. Pourquoi

Le F5 de Nico du 2026-10-19 a raté le critère D1 de RENDU VISIBLE : **1 à 3 FPS à ×4**.
Quatre rapports (touche C, ×4, n=1 chacun, jardins de 150 à 400 plantes) :

| vie macro | ombres | temps d'image | draw calls | primitives |
|---|---|---|---|---|
| affichée | ON | 796 ms | 3191 | 134 k |
| affichée | OFF | 948 ms | 3330 | 131 k |
| masquée | ON | 364 ms | 2789 | 76 k |
| masquée | OFF | 57 ms | 2122 | 73 k |

Même à 57 ms par image, le compteur affiche 3 FPS : il y a des à-coups hors dessin.
Le banc VM de D106 (15-16 FPS à ×4) ne reproduisait pas ce jardin : **l'instrument a raté**.

**Machine cible** : Intel i5-4200H (2 cœurs / 4 threads, 2013), iGPU Intel HD Graphics 4600,
12 Go. Godot en `gl_compatibility` (le bon choix pour ce GPU). Le serveur Python partage les
2 cœurs avec Godot. La VM rend en logiciel (llvmpipe) : ses FPS ne se comparent pas à ce GPU,
ses draw calls / primitives / ms CPU par poste, si.

## 2. Diagnostic (vérifié au code le 2026-10-19)

- **Vie macro** (`visuals/MacroLife.cs`) : un `DrawCircle` par bête, tout redessiné à `AnimHz`
  en continu (~60 k primitives). Un puceron = disque de rayon 2 px *canvas*, soit ~16 px d'écran
  à ×4. Contraire à la DA « l'animation est un signal ».
- **Fuite** : une bête disparue (`DyingAt`) n'est purgée que dans `_Draw`. Masquée (touche I)
  ou sous `MinZoom`, rien n'est dessiné donc rien n'est purgé : 9 205 entrées côté client alors
  que le serveur plafonne à `SPRITES_MONDE_MAX = 5000` (`data/code/fields/population/perception.py`).
- **Peintre serveur** : `sample_sprites` (quantum `DENSITE_PAR_SPRITE = 0.06`, ≤ 4 par plot) puis
  `cap_sprites_global` (5000), appelés dans `data/code/tools/simserver/serialize.py`. Perception
  PURE : le golden ne la lit pas.
- **Ombres** (`visuals/PlantShadow.cs`) : un polygone par plante ; à chaque pas de soleil ≥ 2°
  (`world/WorldView.Soleil.cs`), `QueueRedraw` de tous les nœuds d'ombre. ~300 ms par image [n=1]
  sans hausse de primitives → coût CPU ou casse du regroupement, à trancher au banc.
- **Cadence** : `DebugSecondsPerWeek = 1` est le défaut actuel (`world/WorldView.cs`), et le mode
  Turbo (touche M) existe. En accéléré, le serveur (0,8-2,3 s par semaine sur ce CPU) vole un cœur
  au fil principal.

## 3. Décisions (Nico, 2026-10-19)

1. **Banc d'abord** : un jardin reproductible (graine fixe, printemps de l'an 2, 300-400 plantes,
   vie macro pleine), lançable sur la VM ET sur le PC de Nico, qui mesure la distribution du temps
   d'image et le coût par poste.
2. **Étalonnage** : en fin de tronçon ①, Nico lance le banc sur son PC et colle le rapport C.
   Ensuite, Claude valide par mesure ; le F5 final ne sert qu'au ressenti.
3. **Critère nominal** : à 60 s par semaine, **60 FPS à ×4**, vent dans les plantes et animations à
   vitesse normale ; **30 FPS de ×0,5 à ×2**.
4. **Mode test « au plus vite »** : en accéléré, la cadence s'adapte à la machine (semaine suivante
   dès que la précédente est appliquée, serveur à priorité réduite) ; **aucune image > 100 ms**.
5. **Peintre vie macro = « D2 + points chauds + taille réelle »** :
   - base : 1 individu par espèce présente et par tuile (décision D2 du 2026-08-01) ;
   - individus en plus seulement aux points de forte densité ; **grappes** pour les coloniaux
     (puceron, moustique, cloporte) ; total visé : quelques centaines sur tout le jardin ;
   - **taille réelle** : une bête n'apparaît qu'au palier où elle fait ≥ 1 px interne
     (0,39 px/cm × zoom). Une bête minuscule = 1 pixel, jamais un disque ;
   - **lombric jamais affiché** (souterrain) ;
   - **pixels fixes ou quasi immobiles** ; animation seulement sur **signal** (apparition,
     disparition, geste du joueur à proximité, alarme…) — au repos, elle mange ;
   - **toutes les bêtes d'une tuile en un seul lot**, redessiné au snapshot, au changement de
     palier ou sur signal seulement.
   - Le **champ** de population reste continu et intact : les lecteurs écologiques (herbivorie,
     pollinisation, Vigueur macro) lisent la densité, jamais les sprites. Seul le peintre change.
6. **Ombres en lot** : un dessin par tuile (ou un lot), recalculé quand le soleil bouge vraiment.
7. **D109** : (a) ZIndex allélopathie, (b) vie macro absorbée par la décision 5, (c) poses de vent
   si le banc le justifie ; (d) regroupement des plantes cuites **au minimum** — le sprint plante
   assemblée réécrira le rendu des plantes.
8. **Pleine résolution** (SubViewport 960×540 ×2 → 1920×1080) : **mesure seulement**. Attendu hors
   budget sur HD 4600 (4× plus de pixels à remplir) ; la décision revient au sprint plante assemblée.

Taille réelle → palier d'apparition (indicatif, à caler en ②) :

| espèce (taille) | palier |
|---|---|
| puceron (2 mm) | ×16 |
| moustique (6 mm) | ×8 |
| coccinelle (7 mm), doryphore (1 cm) | ×4 |
| chrysope, cloporte (1,5 cm), carabe (2,5 cm) | ×2 |
| limace, libellule, campagnol, couleuvre, merle, hérisson, rapace | ×0,5 |
| lombric | jamais |

## 4. Philosophie de design

Pure vue + perception (philo #5 : indices visuels). Aucun effet sur la simulation : le golden ne
doit bouger à aucun tronçon. Le moins de bêtes à l'écran n'est pas une écologie appauvrie : le
champ garde la densité réelle, l'écran montre la présence et les pullulations.

## 5. Tronçons

① banc + instrument + étalonnage · ② vie macro · ③ ombres en lot · ④ cadence adaptative, à-coups,
D109 · ⑤ vue et bilan (pleine résolution mesurée, F5 ressenti). Kickoffs dans le dossier du sprint.
