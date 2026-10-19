# ② — Vie macro : peintre « D2 + points chauds + taille réelle », un lot par tuile

> Lire d'abord `CLAUDE.md`, `00_etat.md`, `docs/perf/lod/conception_perf_vue.md` §3.5, et pour
> le contexte écologique `sprints/perf/faune/sprint_optim_vie_macro/00_etat.md` (§D2, §(b)
> inventaire des lecteurs). Python (perception + pont) + vue C#. **Golden intact.**

## Objectif
Montrer la **présence** et les **pullulations**, pas un point par quantum de densité ; et
dessiner toute la vie macro d'une tuile **en un seul lot**, sans redessin continu.

### Côté moteur (perception pure)
- Nouveau peintre dans `data/code/fields/population/perception.py`, appelé par
  `data/code/tools/simserver/serialize.py` à la place de `sample_sprites` + `cap_sprites_global` :
  1 individu par espèce présente et par tuile ; individus en plus aux points de forte densité ;
  **grappes** (plusieurs individus serrés autour du point chaud) pour puceron, moustique,
  cloporte ; **lombric exclu** du bloc envoyé. Total visé : quelques centaines sur le jardin
  du banc ①. Positions par hash, indépendantes de la semaine (comme aujourd'hui) — **zéro RNG
  vivant**.
- ⚠️ **Ne pas toucher** `DENSITE_PAR_SPRITE` : les gestes (`sim/actions/gestes.py`, écraser /
  bioturbation) retirent ou ajoutent un quantum au CHAMP avec cette constante. Le champ reste
  continu et intact ; seuls les sprites envoyés changent. Garder `sample_sprites` (tests, autres
  usages — conserver le code).
- Format du bloc `sprites` : garder la forme compacte actuelle si possible (`{tuile: {espèce:
  [[r,c,x,y,act], …]}}`) ; bump `ENGINE_VERSION` dans `data/code/tools/simserver/version.py`
  (0.5.44 → 0.5.45) et ajuster les tests du pont qui vérifient l'ancienne forme (cap 4/plot :
  `tests/simserver/macro.py`, `tests/test_sim_server.py`) — modification **voulue**, à dire dans
  le commit.
- Vérifier : `python3 -m tests.test_golden` INCHANGÉ (`22768f33…`) et `python3 -m
  tests.test_population` inchangé — si l'un bouge, le peintre lit/écrit le champ : bug, annuler.

### Côté vue (`visuals/MacroLife.cs`)
- **Taille réelle** par espèce (table de données à côté de `Especes`, en cm) ; une bête n'est
  dessinée qu'à partir du palier où elle fait ≥ 1 px interne (`WorldView.PxPerCmX` × zoom) ;
  à sa taille réelle, minimum 1 pixel. Paliers indicatifs dans la conception §3 — à vérifier
  sur captures VM (`tools/capture_vm.sh`) à ×0,5, ×4, ×16, ×32.
- **Un lot par tuile** (ou un seul pour tout le monde visible) : `MultiMeshInstance2D` ou
  équivalent qui ne repasse pas par `_Draw` à chaque image. Reconstruit seulement au snapshot,
  au changement de palier, à la rotation de vue ou sur signal. Respecter `MargeVue` (D109 b).
- **Fixes au repos** : plus d'errance sin/cos continue. Animation seulement sur signal :
  apparition / disparition (fondus existants), geste du joueur dans le plot, alarme si le
  snapshot l'expose (vérifier ce qui existe : champ `alarme`, `activite`). Une animation de
  signal est brève puis la bête se fige.
- **Corriger la fuite** : la purge des entrées mourantes ne doit pas dépendre du dessin
  (masquée ou dézoomée, `Count` doit rester ≤ ce que le serveur envoie + celles en fondu).
- `ForagerLayer` (butineurs, agents distincts) : hors périmètre, sauf s'il pèse au banc ①.
- `dotnet build Symbiose.csproj` vert.

## Mesure (banc ①)
Primitives et draw calls de la vie macro à ×4 avant/après, ms CPU du poste, `Count` après
5 min masquée. Cible : la vie macro ne pèse plus qu'au snapshot, ~0 entre deux.

## Ne pas faire
Pas de sprites par espèce dessinés (c'est le sprint B / D44 b) : des pixels colorés à la bonne
taille suffisent. Ne pas modifier les champs de population ni leur tick. Pas de
`test_epaisseur_500ans`.

## Fin de tronçon
`00_etat.md` (mesures, total de bêtes au banc, paliers retenus), commit. F5 de ressenti au ⑤.
