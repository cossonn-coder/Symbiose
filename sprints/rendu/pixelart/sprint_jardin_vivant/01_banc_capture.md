# T0 — Banc de capture sur la VM (les « yeux » de l'agent)

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, `docs/rendu/pixelart/conception_jardin_vivant.md` §6.

## Objectif
Pouvoir lancer le jeu Godot **sur la VM sans écran** et en sortir des **PNG**
qu'un agent regarde avec l'outil Read. Tous les tronçons suivants s'en servent
pour vérifier leur rendu AVANT le F5 de Nico. Ce n'est PAS un livrable joueur.

## Contexte vérifié
- Projet Godot 4.6 .NET, `gl_compatibility` (`project.godot:15,48`), scène
  principale `world/WorldView.tscn`, moteur Python lancé en sous-process par
  `core/SimBridge.cs`.
- VM Debian, pas de sudo, réseau OK vers github ; `dotnet` 8 dans `~/.dotnet` ;
  Mesa EGL + `dri/*swrast*` présents ; **Xvfb absent** → `apt-get download xvfb`
  (+ dépendances manquantes) puis `dpkg-deb -x` dans un dossier utilisateur.

## À faire (intention — placer et ajuster librement)
1. Télécharger **Godot 4.6 stable .NET Linux x86_64** (même version mineure que
   le projet) dans `~/opt/godot/` (hors dépôt). Vérifier la version exacte
   attendue dans `project.godot` / `Symbiose.csproj` (SDK `Godot.NET.Sdk/…`).
2. Obtenir Xvfb sans sudo ; lancer Godot sous Xvfb en rendu logiciel
   (`LIBGL_ALWAYS_SOFTWARE=1`, llvmpipe), `--rendering-driver opengl3`.
3. Capture : Movie Maker (`--write-movie <dossier>/frame.png --fixed-fps 60
   --quit-after N`) **ou** un mode capture C# déclenché par argument
   (`OS.GetCmdlineUserArgs()`, ex. `-- --capture=<dossier> --frames=N
   --zoom=8 --banc=<nom>`) qui fait `GetViewport().GetTexture().GetImage().SavePng()`.
   Choisir le plus fiable ; si du code C# est ajouté, un fichier dédié
   `tools/`-like côté C# (ex. `core/CaptureMode.cs`), inactif sans l'argument.
4. Script `tools/capture_vm.sh` (dépôt) : build + lancement + N PNG dans un
   dossier passé en argument (défaut : scratchpad / `/tmp/capture_symbiose`).
   Doit pouvoir cibler un **banc** existant (les bancs F5 existent déjà, cf.
   `world/WorldView.*` / `DecorLayer.Banc.cs`) et un palier de zoom.
5. Doc d'usage courte en tête du script + ligne dans `00_etat.md` (« Faits
   vérifiés ») : commande exacte, durée d'une capture, limites (FPS logiciel).

## Critère de réussite
Une commande unique produit ≥ 3 PNG non noirs du jardin de démo à un zoom
donné ; l'agent les ouvre avec Read et décrit ce qu'il voit. Si impossible
(Godot ne démarre pas en logiciel), **échec bloquant documenté** dans
`00_etat.md` avec l'erreur exacte — ne pas contourner en inventant.

## NE PAS
- Committer le binaire Godot ou Xvfb (hors dépôt, `~/opt/`).
- Modifier le moteur Python ; toucher au golden ; lancer `test_epaisseur_500ans`.
- Laisser un mode capture actif par défaut (F5 de Nico inchangé).
- Committer de `.uid` générés (politique D63, `.gitignore`).

## Golden
Non concerné (aucun code moteur). Vérifier quand même `python3 -m tests.test_golden` vert depuis `data/code/`.
