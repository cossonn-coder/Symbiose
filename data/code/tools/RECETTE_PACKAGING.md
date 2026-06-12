# Recette packaging — gel du moteur + export Godot (tranche 7)

> But : un dossier que les amis/famille lancent par **double-clic**, sans
> Python ni Godot installés. Deux étages : (1) geler le moteur Python en
> `sim_server.exe` (PyInstaller), (2) exporter le jeu Godot et poser le
> binaire À CÔTÉ de l'exe du jeu.
>
> 📖 Ce que PyInstaller met VRAIMENT dans le binaire : un interpréteur
> CPython complet + la stdlib + nos `.pyc`, dans une archive auto-extraite
> (`--onefile`). Ce n'est PAS une compilation : même interpréteur + mêmes
> sources + même seed ⇒ mêmes octets en sortie. Le déterminisme survit au
> gel par construction (prouvé byte-à-byte sur la VM, 87/87 checks).
> Compromis `--onefile` : démarrage un peu plus lent (décompression dans un
> dossier temporaire au premier lancement) — négligeable pour un serveur
> lancé une fois par partie. `--onedir` démarre plus vite mais ship un
> dossier de ~200 fichiers ; on préfère UN fichier propre.

## Étage 1 — geler `sim_server.exe` (sur le poste Windows)

PyInstaller gèle pour l'OS **hôte** : le binaire Windows DOIT être produit
sous Windows (la VM Linux a servi de répétition).

1. Installer PyInstaller (une fois) :
   ```
   py -m pip install pyinstaller
   ```
2. Depuis `data\code` (IMPORTANT — pas depuis `tools\`) :
   ```
   py -m PyInstaller --onefile --name sim_server --paths=. --hidden-import=tests.test_golden --hidden-import=main --specpath tools --noconfirm tools\sim_server.py
   ```
   → produit `data\code\dist\sim_server.exe` (~8 Mo). `build\` et `dist\`
   sont ignorés par git (et peuvent être supprimés après copie).

   ⚠ Les trois options non évidentes sont OBLIGATOIRES :
   - `--paths=.` : PyInstaller analyse depuis le dossier DU SCRIPT
     (`tools\`) ; sans ça il ne trouve pas les paquets `plants/ world/
     fields/ sim/` → binaire qui crashe au démarrage (`ModuleNotFoundError:
     world`). Vécu sur la VM.
   - `--hidden-import=tests.test_golden` et `=main` : ces deux modules sont
     importés DANS des fonctions (configs `smoke` et `full`) — l'analyse
     statique ne les voit pas. Symptôme sinon : le binaire démarre puis
     `init` répond `ModuleNotFoundError`.
   - Surtout PAS `--noconsole` : le serveur est une app **stdio**, pas une
     app fenêtrée — `--noconsole` le priverait de ses flux. La fenêtre cmd
     parasite est évitée côté Godot (`CreateNoWindow` dans `SimBridge.cs`).
3. Fumée rapide (PowerShell, depuis `data\code`) :
   ```powershell
   '{"cmd":"init","seed":42,"config":"smoke"}','{"cmd":"quit"}' | .\dist\sim_server.exe
   ```
   Attendu : une ligne `{"engine_version":"...","ok":true,...}` puis
   `{"ok":true}`.
4. Validation complète — les 87 checks de la suite CONTRE le binaire
   (PowerShell, depuis `data\code`) :
   ```powershell
   $env:SIM_SERVER_BIN = "$PWD\dist\sim_server.exe"
   py -m tests.test_sim_server
   Remove-Item Env:SIM_SERVER_BIN
   ```
   Attendu : `PASS — 87/87 checks verts`.

### Pièges Windows connus
- **SmartScreen / antivirus** : les binaires PyInstaller `--onefile` sont
  un faux positif CLASSIQUE (auto-extraction = comportement de packer).
  Si `sim_server.exe` disparaît ou refuse de se lancer → restaurer de
  quarantaine + ajouter une exclusion sur le dossier du jeu. À prévenir
  aussi chez les amis/famille (le mentionner dans le mot d'accompagnement).
- **Encodage des pipes** : déjà verrouillé — protocole ASCII par
  construction (`json.dumps` échappe les accents, verbes sans accents) +
  UTF-8 sans BOM forcé côté C#. Rien à faire.

## Étage 2 — export Godot + assemblage

1. Godot → Projet → Exporter… → preset **Windows Desktop** (le télécharger
   via « Gérer les modèles d'export » si absent). Exporter vers un dossier
   vide, p. ex. `C:\tmp\symbiose_ship\Symbiose.exe`.
2. Copier `sim_server.exe` DANS CE DOSSIER, à côté de `Symbiose.exe`.
   ⚠ Le binaire moteur ne peut PAS vivre dans le `.pck` : un exécutable ne
   se lance pas depuis une archive. `SimBridge.Start()` le cherche à côté
   de l'exe du jeu (`OS.GetExecutablePath()`).
3. Le dossier distribuable = `Symbiose.exe` + `.pck` (si séparé) +
   `sim_server.exe` + les DLL .NET exportées par Godot. Zipper tel quel.

### Vérifier le mode de lancement (témoin)
`SimBridge` imprime le mode choisi en console :
- `[SimBridge] Mode BINAIRE — moteur gelé …` → mode distribué, AUCUN
  Python sollicité (la vraie cible : machine sans Python).
- `[SimBridge] Mode DEV — python3 + sim_server.py …` → repli dev (F5
  éditeur, inchangé).

Hors éditeur, les prints ne sont visibles qu'en lançant
`Symbiose.console.exe` (exporté automatiquement à côté de l'exe par le
preset Windows) — c'est lui qu'on lance pour LIRE le témoin ; les
joueurs, eux, double-cliquent `Symbiose.exe`.

### Test final (critères F5 de la tranche)
Sur le poste Windows, HORS éditeur : double-clic → monde full, vivre une
saison, un geste joueur, F6 (heatmaps). Idéalement répéter sur une machine
SANS Python — à défaut, le témoin « Mode BINAIRE » fait foi.

## Répétition Linux (déjà faite sur la VM, pour mémoire)
Mêmes commandes avec `python3 -m venv` + `pip install pyinstaller`, binaire
`dist/sim_server` (sans `.exe`). Résultats du 2026-06-12 : protocole OK
(smoke + full), 87/87 via `SIM_SERVER_BIN`, sorties **byte-identiques**
script vs binaire (seed 1234, 4 semaines, 27 396 octets comparés).
Le `.spec` versionné dans `tools/` est rejouable :
`pyinstaller tools/sim_server.spec` depuis `data/code` (mais la commande
CLI complète ci-dessus reste la référence — elle régénère le spec).
