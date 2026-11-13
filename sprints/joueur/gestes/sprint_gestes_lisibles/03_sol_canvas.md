# ③ Le sol-canvas — traces au sol (vue)

> Lire d'abord : `CLAUDE.md`, `00_etat.md` (clés de pont posées au ①),
> `docs/joueur/gestes/conception_gestes_lisibles.md` §3 en entier.
> DA : `docs/rendu/pixelart/etude_brief_da_16bits.md`. Golden : **INTACT** (pure vue C#).
> **Prérequis : ① CLOS** (registre `traces_sol` + plots secs exportés).

## Objectif
Que le jardin se souvienne des gestes et des événements, à l'œil : mottes du bêchage,
raies de grelinette, empreinte de pas, compost épandu, auréole d'arrosage, rebord de la
cuvette, paillis qui couvre tout le plot, cadavre couché, pile qui grossit, éclaboussures
de pluie, sol craquelé. **La vue ne dessine que ce que le snapshot dit.**

## À faire
1. **Couche de traces** (fichier neuf, ex. `visuals/TracesSolLayer.cs`) : lit la clé de
   traces du snapshot (nom exact dans `00_etat.md`), dessine chaque sorte (table §3.1) au
   plot ou au point `x_cm, y_cm`, **estompée avec l'âge**. Rendu **en lot par tuile**
   (patron du sol : `world/SolMaillage.cs`, `visuals/LotTriangles.cs`), reconstruit
   seulement quand la liste de la tuile change. Projection par la fonction unique de la
   vue (`WorldToScreen`). Couleurs par `Palette16` / palette indexée, motifs pixel.
2. **Paillis** (`visuals/MulchLayer.cs`) : couvre **tout le plot**, texture par nature
   (paille dorée en brins, BRF en copeaux bien visibles, aiguilles, feuilles), opacité par
   profondeur. Une courte animation de pose (brins qui tombent) au moment où le paillage
   d'un plot augmente entre deux snapshots — effet de transition sur un fait moteur, pas
   une invention.
3. **Cuvette** de `creuser` : vérifier ce que `world/WorldView.Relief.cs` /
   `visuals/PuddleLayer.cs` montrent d'une baisse d'`altitude` d'un seul plot ; si le trou
   ne se voit pas, le dessiner (fond plus sombre, bord). La mare qui s'étend par
   convergence de l'eau doit se voir sans code spécial.
4. **Cadavre couché** : vérifier que le rendu des morts (`visuals/DeadWoodLayer.cs` et le
   rendu des squelettes) couche bien un `stade_mort = "couchee"` ; corriger sinon.
5. **Pile et bac qui se remplissent** : la pile à bois / le bac montrent leur quantité
   (volume visible qui croît), à partir de ce que le snapshot exporte des structures
   (lire `visuals/CompostStructure.cs` et la sérialisation des structures avant ; si la
   quantité n'est pas exportée, l'ajouter au pont, lecture pure, et le consigner).
6. **Événements** (§3.2) : éclaboussures au sol sous la pluie (nombre borné, densité ∝
   intensité de la météo du snapshot, immobiles hors pluie) ; sol craquelé sur les plots
   secs exportés, avec **hystérésis d'affichage** (apparaît sous un seuil, disparaît au-
   dessus d'un seuil plus haut).
7. **Banc de capture** : vérifier chaque trace à la capture VM (`tools/capture_vm.sh`,
   banc qui contient des traces — en fabriquer un dans le registre `data/code/bancs/` si
   besoin, en appliquant les gestes par le pont au montage) et **regarder les PNG**.
   Images versionnées dans `planche/` du sprint.

## Perf
Couche en lot : ~1 appel de dessin par tuile ; aucune reconstruction sans changement ;
éclaboussures bornées. Mesurer le FPS du banc avant/après (`tools/perf_vm.sh` si
pertinent) et le consigner.

## Ne PAS faire
- Aucune trace sans donnée du snapshot. Pas de chiffre à l'écran.
- Ne pas concevoir les autres états du sol (imbibé, herbacé, litière par paliers) : D108.
- Ne rien ajouter à `WorldView.cs` (300 LDC). > 300 LDC → scinder. GDScript interdit.
- Ne jamais lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.

## Fin de tronçon
`dotnet build` vert, golden intact, captures regardées. `00_etat.md` : rendu par sorte,
mesures perf, traces encore faibles, écarts.
