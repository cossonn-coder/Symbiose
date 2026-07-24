# T4 — Vue Godot + banc F5 (les 10 ports)

**Sprint :** migration des 9 arbres en croissance procédurale (D91).
**Doc de conception :** `docs/vegetal/croissance/conception_migration_arbres.md` (§4, §6, §7).
**Prérequis :** T1 + T2 + T3 clos (les 9 arbres sont `procedural_growth=True`).
**Golden attendu : INCHANGÉ** (`57c166d8…`). Tronçon PUR-VUE (+ éventuel pont) —
zéro moteur écologique. `dotnet build Symbiose.csproj` doit rester VERT.

## Objectif
Rendre les 9 nouveaux arbres **en branches** (ils sortent tous du snapshot avec
une structure de segments comme le pommier), et offrir un **banc F5** pour valider
chaque port à l'œil. C'est le tronçon vue obligatoire de tout sprint (règle projet).

## Contexte technique
- Le rendu des branches est **déjà générique** : `visuals/PlantRenderer*.cs`
  rastérise les segments du snapshot (pas de code par espèce pour l'ossature). Les 9
  arbres migrés exposeront leur structure via `update_footprint`/le pont exactement
  comme le pommier → **ils devraient se dessiner en branches sans code neuf**. À
  vérifier au F5 d'abord ; ne coder que ce qui manque réellement.
- **Feuilles par espèce** : tables `LeafProfiles` (Leaf.cs) + `LeafOutlines`
  (PlantRenderer.LeafOutline.cs), **clé = nom d'espèce**. Les 9 arbres n'y sont
  peut-être pas → repli par défaut. Ajouter une entrée par arbre **si** le repli lit
  mal (feuillage crédible).
- **Sapin = aiguilles** : `deciduous=False`, feuillage persistant. Le générateur de
  feuilles doit savoir dessiner des **aiguilles** (touffes fines) et non des limbes.
  C'est le seul cas de rendu spécifique. Mode « needle » à ajouter au dispatch
  feuille (Leaf.cs), déclenché pour le sapin.
- **Bancs F5** : `data/code/bancs/croissance.py` (config `vieux_pommier`, montée
  côté Godot par `init config="…"`). Patron à répliquer pour un banc multi-arbres.
- **Pont** : `tools/sim_server.py` + `core/SimBridge.cs`. Si un champ de structure
  manque au snapshot pour ces espèces, l'ajouter (bump de version de protocole).
  A priori rien à ajouter (même structure que le pommier).

## Fichiers à toucher (selon ce que le F5 révèle)
- `data/code/bancs/croissance.py` — **nouveau banc** `foret_ports` (les 10 arbres).
- `visuals/Leaf.cs` — mode aiguilles pour le sapin (dispatch feuille).
- `visuals/PlantRenderer.LeafOutline.cs` — entrées `LeafOutlines` des arbres si repli
  insuffisant.
- (éventuel) `tools/sim_server.py` + `core/SimBridge.cs` si un champ manque.
- Doc encyclopédie (optionnel, §6) : enrichir la fiche descriptive des 9 espèces
  avec leur architecture — **non bloquant**.

## Étapes
1. **Banc `foret_ports`** dans `bancs/croissance.py` : instancier les 10 arbres
   (pommier + les 9 migrés) espacés sur une tuile, warmup Engine ~10-15 ans
   (`growth_factor` favorable, nappe forcée si besoin comme `vieux_pommier`), pour
   observer chaque port à maturité. Config montée F5 par `init config="foret_ports"`.
2. **F5 d'observation** (Nico) : vérifier que chaque arbre se dessine en branches et
   que son **port lit correctement** — flèche du sapin, étalé du chêne/hêtre/noyer,
   bas-ramifié du figuier, pleureur du bouleau, élancé de l'aulne, ovoïde du
   cerisier/charme. Noter les écarts.
3. **Aiguilles du sapin** : ajouter le mode « needle » au dispatch de `Leaf.cs`
   (touffes de traits fins, teinte conifère sombre) déclenché pour `FirTree`.
   Golden intact (pur rendu). `dotnet build` vert.
4. **Feuilles des arbres** (si repli insuffisant) : entrées `LeafProfiles` /
   `LeafOutlines` par espèce (feuille de chêne lobée, de hêtre ovale, de bouleau
   losangée dentée…). Optionnel/itératif.
5. **Enrichissement encyclopédie** (optionnel, §6) : phrase d'architecture au niveau
   descriptif de chaque fiche. Non bloquant — peut être différé si le temps manque.

## Ce qu'il NE faut PAS faire
- Ne PAS toucher `data/code/` moteur (sim/fields/plants logique écolo) — pur vue.
  Seuls `bancs/` (outil de test) et éventuellement le pont sont permis côté Python.
- Ne PAS re-figer le golden. Lancer `python3 -m tests.test_golden` pour confirmer
  qu'il est **INCHANGÉ** (le banc ne doit rien changer au scénario golden).
- Ne PAS implémenter la **phyllotaxie verticillée** du sapin (polish différé — une
  flèche dense lit déjà « conifère »).
- Ne PAS implémenter le multi-tronc du figuier (option F5 différée, cf. T2).
- Ne PAS coder de rendu par espèce **avant** d'avoir constaté au F5 que le rendu
  générique ne suffit pas (les branches sortent déjà du renderer commun).

## Tests / vérification
- **Golden** : `python3 -m tests.test_golden` → **INCHANGÉ**.
- `cd <racine> && dotnet build Symbiose.csproj` → **VERT** (filet de compilation).
- Le banc `foret_ports` tourne sans crash (warmup complet).
- **Ne PAS** lancer `test_epaisseur_500ans`.

## Mise à jour en fin de tronçon (clôture du sprint)
- `00_etat.md` : cocher T4, marquer le sprint CLOS, hash golden inchangé, pont si
  bumpé, **reste = F5 Nico** (validation visuelle des ports + calibrage à l'œil).
- Commit : `feat(arbres ④) : rendu branches 9 arbres + aiguilles sapin + banc foret_ports (D91)`.
- Passer **D91 → CLOS** dans `DETTE.md` et écrire l'entrée de clôture `journal.md`.
