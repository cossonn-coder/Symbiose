# ⑤ Lisière côté caméra devant le jardin + bilan + protocole PC + clôture

**Golden** : intact. **Build** vert. Tronçon VUE final du sprint.

## 1. Lisière devant (bug F5 Nico 2026-10-26)
Au SE (bas-droite de l'écran, rotation par défaut), les tuiles du jardin sont dessinées
PAR-DESSUS les arbres de la lisière : le décor entier est en `ZIndex = -5`
(`world/WorldView.cs:311`), derrière le sol (0) et les objets (10). Or un arbre planté
devant le jardin (côté caméra) doit le masquer.
- Les pièces HAUTES (arbres / houppiers, roseaux, falaise si elle dépasse) des bords côté
  caméra passent dans une couche au-dessus du sol, à un ordre cohérent avec les plantes
  qu'elles masquent réellement. Le reste du décor (assise, tapis, bords du fond) reste
  derrière.
- « Côté caméra » dépend de la ROTATION de vue (`RotateView`, D35) : vérifier au code comment
  le décor la gère et changer de couche au changement de rotation.
- Un seul lot de plus au maximum (coût de rendu à mesurer). Captures avant/après des
  4 rotations dans `captures_05/`.

## 2. Bilan VM
Banc 3 phases + balayage de zoom (outil ①) avant (chiffres de ①) / après tous les tronçons,
même graine 1521550718, même semaine. Tableau dans `00_etat.md`.

## 3. Protocole PC (un seul run)
Rédiger dans `00_etat.md` §F5 les Main Run Args exacts (banc 3 phases, comme au sprint
précédent : `--capture-banc=full --capture-seed=1521550718 --capture-etalonnage=25
--capture-banc-3phases=25,25,20 --capture-banc-cadence=1 --capture-banc-semaine=90`, adapté
si ① a ajouté le balayage de zoom au banc) + les questions F5 de ②③④⑤.

## 4. Clôture
- `DETTE.md` **D116** : leviers vue + pont faits, chiffres VM, **attend le run PC** → 3ᵉ temps
  (levier moteur si 2 s/sem n'est pas tenu).
- `DETTE.md` **D112** — (k)(l)(m) ont été INSCRITS à la conception (2026-10-26) : vérifier qu'ils y sont, y ajouter seulement ce que le sprint découvre ; pour mémoire :
  (k) décor animé au vent et à la lumière comme le jardin ; (l) le soleil ne se voit sur
  aucune plante (face éclairée) ; (m) **cohérence de DA inter-paliers** : modèle = ×1 avec
  contour noir (`PlantRenderer.Kit.cs`, contour 1 px si touffe ≥ 7 px), absent des paliers
  hauts ×4+ ; chaque palier plus fin = même idée + plus de détails, assets prêts par palier ;
  deux méthodes proposées par Nico (agrandir ×0,5 et ajouter les détails / partir de ×32 et
  retirer) — lier à (i) « ×2 plus beau que ×4 » ; noter que le décor absent > ×4 est VOULU
  (`DecorLayer.MaxZoom`). (b) maison en verre reste ouverte. (c) confirmée fermée au F5.
- `BACKLOG.md`, entrée `journal/` + index `journal.md`.

## Ne PAS faire
Animer le décor, éclairer les plantes, toucher aux paliers de style (tout ça = dette D112).
