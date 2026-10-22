# ② Bois mort qui tombe

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, conception §2.
**Golden** : RE-FIGÉ probable (un ligneux du smoke qui s'élague dépose désormais du bois →
litière, décomposition, mycélium). Si inchangé, le constater. Re-figeage annoncé, une fois.

## Objectif
Une branche qui meurt tombe au sol en litière `bois` visible, au lieu de disparaître.

- `sim/growth/phases.py::_elaguer` (appelé par `grow_plant`, lui-même par
  `sim/engine/boucle.py` ~l.435 et `sim/quetes.py`) supprime les sous-arbres morts
  (`kill`) « sans couplage écologique ». Le faire RENVOYER (ou exposer) les segments
  retirés, et faire déposer par la couche `sim/engine` (qui a l'`eco`) leur masse en
  litière `bois` via `eco.deposer_litiere(r, c, "bois", masse)`.
- Masse ∝ longueur × épaisseur² (`Segment.length_cm`, `thickness_cm`), constante de
  conversion dans les constantes (ordre de grandeur cohérent avec `bois_restant` des
  squelettes, `sim/engine/decompo.py`). Plot = projection au sol du milieu du segment ;
  **vérifier le repère** de `Segment.base` (relatif au collet ou monde ?
  `plants/base/instance.py::update_footprint` lit `segs[0].base`) avant de convertir en
  plot (`floor(pos / PLOT_CM)`), borné à la tuile.
- Seuls les ligneux déposent du `bois` (le reste existe déjà via la litière de feuilles) ;
  le décider par la donnée d'espèce existante (`tissu_mort` / famille ligneuse).
- **Pont** : le bloc `litiere` du snapshot (`tools/simserver/serialize.py` ~l.418-440)
  n'expose que le tissu DOMINANT par plot. Ajouter la masse de `bois` du plot et son âge
  moyen (pour que la vue ⑧ dessine une branche et ses stades de décomposition même sous
  des feuilles). Bump version du pont + note dans `version.py`.
- Mesure : nombre de plots avec bois > 0 et mycélium max/médian sur `full`, graine
  1521550718, 104 sem. (avant : 0 plot sur 1 188, mycélium max 0,24 [n=1 run]).

## Ne PAS faire
Pas de dessin C# (⑧). Pas de nouvelle mécanique de chute aléatoire. Pas de 500 ans.
