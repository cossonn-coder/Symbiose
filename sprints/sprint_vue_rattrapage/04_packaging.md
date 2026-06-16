# 04 — Packaging (tranche 7) : gel PyInstaller + export Godot — clôture

> Lire `00_etat.md`. **Dernier sous-sprint.** Recette détaillée déjà écrite :
> **`sprints/sprint_integration_godot/07_packaging.md`** (kickoff complet) +
> `tools/RECETTE_PACKAGING.md` (étapes Windows pas-à-pas) + `tools/sim_server.spec`.
> Ce fichier ne duplique pas : il **pointe** et **met à jour** ce qui a changé
> depuis. Ampleur : **petit** côté VM (déjà fait), **bloqué sur le poste Windows
> de Nico** (allers-retours).

## Pourquoi en dernier
Le dossier distribuable doit embarquer la **vue complète** (gestes + fruits +
squelettes + litière + compost des sous-sprints 01–03). On gèle/exporte **après**
le rattrapage, pas avant.

## Déjà fait sur la VM (cf. 07_packaging.md §Avancement + integration/00_etat)
- Répétition PyInstaller `--onefile` validée (piège `--paths=.` + 2
  `--hidden-import` documentés), sorties **byte-identiques** script vs binaire.
- `tests/test_sim_server.py` lit `SIM_SERVER_BIN` (additif pur).
- `SimBridge.cs` bimode (binaire à côté de l'exe Godot / repli dev `python3`→
  `python`), `CreateNoWindow`, UTF-8 sans BOM, print du mode.
- `.spec` versionné, `tools/RECETTE_PACKAGING.md`, `.gitignore` build/dist.

## ⚠️ Mises à jour à reporter (le sprint a vieilli depuis l'écriture de 07)
- **Golden** : la référence n'est plus `16a1b937…` mais **`908f591bee…`**
  (décompo·compost l'a re-figé). Toute mention « golden intact » vise ce hash.
- **`test_sim_server`** : n'est plus 87 checks mais **158** (02/03 + correctif F5
  du 03). Le critère devient : **tous les checks** passent sur le **binaire gelé**
  (`SIM_SERVER_BIN`), déterminisme byte-identique.
- **Protocole** : `ENGINE_VERSION` a atteint **0.3.8** (02/03 + correctif F5 :
  snapshot expose les morts, la litière, le `contenu` des structures). Le gel
  ré-emballe ce moteur-là.
- **Build C# vérifiable sur la VM** désormais (`dotnet build`) — mais l'**export
  Godot et le F5 restent à Nico** (Godot pas sur la VM).

## Reste à faire (Nico, poste Windows — recette = 07 §Plan étapes 3-4)
1. Geler `sim_server.exe` (RECETTE étage 1) ; valider **tous les checks** avec
   `$env:SIM_SERVER_BIN`, déterminisme byte-identique au script.
2. Compiler le C# (le build VALIDE le `SimBridge.cs` bimode + tout le code 01–03) ;
   F5 éditeur doit marcher en mode DEV.
3. Export Godot Windows + poser `sim_server.exe` à côté de l'exe (étage 2) ;
   test HORS éditeur : double-clic → monde, une saison, **un geste de chaque
   famille** (planter, arroser, tailler, manger-fruit, composter…), F6 ; vérifier
   « Mode BINAIRE » via `Symbiose.console.exe` (aucun Python sollicité).

## Critères de succès (F5 final = Nico, hors éditeur)
- [ ] Tous les checks `test_sim_server` passent sur le binaire gelé (VM).
- [ ] Console affiche le mode de lancement (binaire vs dev).
- [ ] Dossier exporté : double-clic → jardin complet + vue 01–03 + saison +
      gestes + F6, sans Python installé.
- [ ] F5 éditeur marche toujours sans binaire (repli dev intact).
- [ ] Golden `908f591bee…` intact (le gel est un EMBALLAGE ; le moteur n'est pas
      touché — seule la variable d'env de test existe).

## Clôture
Quand ces cases sont vertes : **tranche 7 CLOSE = sprint Intégration Godot CLOS
+ ce sprint VUE CLOS**. Graver dans `00_etat.md` (ici et integration/00_etat),
`journal/`, mémoires. Après : retour BACKLOG moteur/contenu (save global — hook
`OnSeasonEnd` posé —, saisonnalité vie macro, physico-chimie sol, encyclopédie/
carnet/HUD riche en sprints dédiés).

## Commit suggéré
`chore(vue·rattrapage) : 04 — packaging PyInstaller + export Godot — SPRINT CLOS (golden 908f591bee, protocole 0.3.7)`
