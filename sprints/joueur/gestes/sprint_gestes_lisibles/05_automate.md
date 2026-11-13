# ⑤ Automate — actif fenêtre fermée, gestes visibles, mode testeur

> Lire d'abord : `CLAUDE.md`, `00_etat.md`, `docs/joueur/gestes/conception_gestes_lisibles.md`
> §7. Code : `world/WorldView.Automate.cs`, `world/AutomateContent.cs`,
> `data/code/tools/jardinier_auto/` (boucle, trace = journal), registre des bancs
> `data/code/bancs/`. Golden : **INTACT**.

## Objectif
L'automate tourne sans occuper l'écran, on voit ce qu'il fait, et un banc peut lui faire
jouer un plan de test geste par geste. **Pas** d'automate à intentions ici
(`sprint_automate_intention`, conception à part).

## À faire
1. **Actif fenêtre fermée** : aujourd'hui fermer l'onglet le débranche, et la sim ne
   tourne que onglet actif (« pause par onglet »). Découpler : la touche A branche /
   débranche ; fermer l'onglet ne fait que le fermer. Un indicateur discret (petite
   icône, pas de chiffre) dit que l'automate tourne. Vérifier que la règle de pause
   générale reste cohérente (le jeu suit ses propres règles de pause, onglet fermé).
2. **Gestes de l'automate visibles** : la vue lit les gestes du dernier tick (journal de
   l'automate dans le bloc `automate` du snapshot — vérifier qu'il porte verbe, tuile et
   point ; compléter au pont en lecture pure sinon) et joue, au point visé, un **sprite
   du monde** avec les images animées du geste (API posée au ②), à l'échelle du zoom,
   étalés dans le temps s'il y en a plusieurs. Nombre simultané borné.
3. **Mode testeur** : un banc du registre peut déclarer un **plan de test** = liste
   ordonnée `(verbe, cible)` (cible résolue au montage : plante d'une espèce, plot, bac,
   ruche…). Le pont expose le plan (commande de lecture). La vue le déroule **par le
   même chemin qu'un clic du joueur** (dispatch d'action normal → animation curseur +
   réponse + traces), un geste toutes les N secondes (constante, ~3 s), et écrit un
   rapport : verbe, cible, appliqué / refusé, message. Rapport affiché dans l'onglet
   Automate et écrit au journal Godot (`[Testeur]`) pour la capture VM. Lancement : une
   touche (documentée dans l'aide F1) et une option de `tools/capture_vm.sh`.

## Vérification
Capture VM d'un banc avec un plan court (3-4 gestes) : le journal `[Testeur]` liste les
résultats, les images montrent animation et trace. Regarder les PNG.

## Ne PAS faire
- Ne pas changer la logique de décision de l'automate (règles, priorités, objectifs).
- Ne pas toucher aux outils. Pas de chiffre à l'écran.
- Ne rien ajouter à `WorldView.cs` (300 LDC). > 300 LDC → scinder. GDScript interdit.
- Ne jamais lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.

## Fin de tronçon
`dotnet build` vert, golden intact, tests de l'automate verts (`data/code/tests/`, ceux
du jardinier automate). `00_etat.md` : format du plan de test, touche, option de capture,
points F5.
