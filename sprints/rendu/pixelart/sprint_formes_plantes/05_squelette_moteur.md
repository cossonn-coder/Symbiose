# ⑤ Plus de squelette pour les herbacées à port — golden INTACT

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (bilans ①→④), conception §4.4, §4.6 ; `sim/growth/phases.py` (`grow_plant`), `sim/growth/seam.py`, `sim/actions/gestes.py`.

## Objectif

Les herbacées à port ne font plus pousser de segments qui ne se dessinent plus. La cadence y gagne, l'écologie ne bouge pas, les gestes gardent leur sens.

## Concernées

`not procedural_growth and not ligneux and mode_grimpe is None`, vérifié espèce par espèce contre la table des ports. Si une espèce concernée n'a pas de port, elle reste hors du retrait et le bilan le dit.

## À faire

1. **Référence** avant toute modification : `full`, seed 42, 3 ans, sans automate, puis avec `cmd_automate` curatif. Par semaine : digest de `tests/test_golden.final_digest`, plantes, espèces, CPU (`process_time`). Sauver sous `mesures/`. Vérifier la charge (`uptime`).
2. **Inventaire des lecteurs**, avant de placer le retrait. Lecteurs déjà repérés, à relire et compléter au `grep` :
   - `sim/actions/gestes.py` : `tailler`, `pincer`, `arracher`, et `age_weeks` du coup de pied (l. ~475) ;
   - `tools/simserver/actions.py` (~284-297, message selon `len(segments)`) ;
   - `tools/simserver/plante_route.py` (~125-156, gestes qui exigent un segment non collet) : **bouture et multiplication d'une herbacée doivent rester possibles** ;
   - `plant.fruits` et son `segment_id`, et `tools/maquette/organes.py` : **où naît un fruit sans apex ?** Poivron, courgette, fraisier sont fruitiers ;
   - `world/container.py` (`grow_plant` en pot) et `sim/quetes.py` ;
   - `sim/effects/perturbations.py` (`diam_pondere`), `sim/engine/branches.py` ;
   - `visuals/PlantRenderer.Prairie.cs` (`CroissancePrairie` compte les segments du trèfle : à remplacer par l'âge ou le stade) ; `world/WorldView.Conteneurs.cs:171` ; `PlantRenderer.Bake.cs` (`BakeCost`) ;
   - tests qui lisent la structure d'une espèce concernée.

   Noter la réponse à chacun dans le bilan.
3. **Retrait** : pour ces espèces, le collet reste et son `age_weeks` continue d'avancer ; plus d'élongation, de débourrement, d'élagage. **Intention, pas de placement imposé** : passage dans `grow_plant` ou autre, selon l'inventaire. Un seul prédicat, sur la classe, nommé et commenté.
4. **Taille** : la masse déposée par `tailler` et `arracher` sur ces espèces se déduit de la hauteur rabattue, même ordre de grandeur qu'avant (le mesurer avant de choisir). `rabattu` et `pince` restent la lecture visible. Un second clic rapproché ne doit pas redéposer plus que la plante n'a.
5. **Vérifier que rien d'écologique ne bouge** : rejouer le point 1. Digests hebdomadaires identiques sans automate et avec. Tout écart se diagnostique ; s'il vient d'un geste de l'automate, l'expliquer et le borner, sinon anomalie.
6. **Gain** : CPU année et tick médian an 1, 2, 3, avant/après, à charge comparable (`[n=…, VM, charge …]`). Le rapporter tel quel, même très inférieur à −41 % (conception §4.6). Dire d'où il vient si le profil le permet.
7. **Vue** : captures `full` et `planche_especes` inchangées à l'œil ; `dotnet build Symbiose.csproj` vert ; `tools/perf_vm.sh`.
8. Golden, `tests/simserver`, suites de croissance et de gestes (`test_succession`, `test_edaphique`, `test_parasite` déjà rouges avant ce sprint).

## Golden

**INTACT**. S'il bouge : anomalie à diagnostiquer, pas de re-figeage.

## NE PAS

Toucher aux ligneux, au haricot, à la tomate, au lierre, au jasmin. Modifier `height_at` ou l'empreinte. Changer le format du snapshot. Lancer `tests/test_epaisseur_500ans.py`.
