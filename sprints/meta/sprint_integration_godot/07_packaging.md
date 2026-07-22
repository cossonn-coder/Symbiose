# Tranche 7 — packaging : gel du moteur (PyInstaller) + export Godot

> **Kickoff autosuffisant** (démarrage à froid : lire `00_etat.md` d'abord).
> DERNIÈRE tranche du sprint Intégration. But : un dossier que les amis et
> la famille de Nico peuvent lancer **sans rien installer** — ni Python, ni
> Godot. Ampleur : **moyen** (peu de code, mais 2 machines et 2 OS dans la
> boucle — prévoir des allers-retours avec Nico).

## Ce qu'on livre, en une phrase
Le moteur Python (`tools/sim_server.py` + paquets) gelé en **binaire
autonome** par PyInstaller ; `SimBridge` lance ce binaire s'il existe
(repli `python3` + script en dev — le confort actuel ne change pas) ;
export Godot Windows + le binaire à côté = dossier distribuable.

## État de départ (vérifié au kickoff)
- Moteur **100 % stdlib** (vérifié en t0) → gel sans dépendance tierce.
- `core/SimBridge.cs:60` : `FileName = "python3"` codé en dur,
  `ServerScript = "res://data/code/tools/sim_server.py"`, cwd = `data/code`.
- **⚠ Piège n°1 — imports DIFFÉRÉS** dans `sim_server.py` : `tests.
  test_golden` (config smoke, ligne ~139) et `main` (config full, ~145)
  sont importés DANS des fonctions → l'analyse statique de PyInstaller ne
  les voit pas → `--hidden-import=tests.test_golden --hidden-import=main`
  obligatoires (leurs deps transitives sont des imports de tête, ramassées
  ensuite). Symptôme sinon : le binaire démarre puis `init` répond
  `ModuleNotFoundError` — tester les DEUX configs.
- **Plateformes** : PyInstaller gèle pour l'OS **hôte**. Poste Nico =
  **Windows** (cible de distribution), VM Claude = Debian (répétition).
  Le binaire de ship sera donc construit PAR NICO sur son poste, avec une
  recette pas-à-pas fournie (il a déjà Python : le pont tourne en dev).

## Plan (étapes vérifiables)
1. **Répétition sur la VM (Linux)** : `pip install pyinstaller` (venv ou
   --user), geler `sim_server` en `--onefile` depuis `data/code/` :
   `pyinstaller --onefile --name sim_server --hidden-import=tests.test_golden
   --hidden-import=main tools/sim_server.py`. Vérifier : le binaire répond
   au protocole (init smoke ET full, step, action, fields, quit).
   → **test automatisé** : variable d'env `SIM_SERVER_BIN` lue par
   `tests/test_sim_server.py` (si posée → lance le binaire au lieu de
   `python3 tools/sim_server.py`) ; les 87 checks doivent passer sur le
   binaire gelé À L'IDENTIQUE (déterminisme compris — même seed, mêmes
   octets). Spec `.spec` et recette conservées dans `tools/`.
2. **`SimBridge.cs` — résolution du serveur** : chercher dans l'ordre
   (a) `sim_server[.exe]` à côté de l'exécutable Godot
   (`OS.GetExecutablePath()`) — le mode DISTRIBUÉ ; (b) repli dev actuel
   `python3` + script `res://` (inchangé — F5 dans l'éditeur continue de
   marcher sans binaire). Print console du mode choisi (témoin). Sous
   Windows dev, `python3` peut s'appeler `python` : tenter l'un puis
   l'autre au repli (correction du TODO ligne 60).
3. **Gel Windows par Nico (recette fournie, allers-retours prévus)** :
   même commande sur son poste → `sim_server.exe`. Pièges Windows à
   documenter dans la recette : console parasite (le binaire est un
   process caché par Godot, pas besoin de `--noconsole` — c'est un serveur
   stdio, PAS une app fenêtrée) ; SmartScreen/antivirus qui met le .exe en
   quarantaine (faux positif PyInstaller classique — exclusion à prévoir) ;
   UTF-8 des pipes (le protocole impose déjà `encoding`, vérifier côté C#).
4. **Export Godot Windows** + assemblage : preset Desktop, le `.exe`
   Godot + `.pck` + `sim_server.exe` dans UN dossier (le binaire moteur ne
   peut PAS vivre dans le .pck — un exécutable ne se lance pas depuis une
   archive). Test final sur le poste Nico HORS éditeur : double-clic,
   jardin complet, une saison vécue, une action, F6. Idéalement : test sur
   une machine SANS Python (la vraie cible) — à défaut, renommer
   temporairement `python.exe` ne suffit pas, mais `SIM_` print du mode
   choisi au démarrage fait foi (mode binaire = aucun Python sollicité).

## Critères de succès (F5 final = Nico, hors éditeur)
- [ ] `test_sim_server` **87/87 sur le binaire gelé** (VM, `SIM_SERVER_BIN`),
      déterminisme byte-identique au script.
- [ ] Console Godot affiche le **mode de lancement** (binaire vs dev).
- [ ] Dossier exporté : double-clic → monde full, saison, gestes, F6 —
      sans Python installé sollicité.
- [ ] Le F5 ÉDITEUR continue de marcher sans binaire (repli dev intact).
- [ ] Golden intact (`16a1b937…`) — le moteur n'est pas touché (le gel est
      un EMBALLAGE ; seul `test_sim_server.py` gagne la variable d'env,
      additif pur).

## Contraintes & rappels
- Moteur Python JAMAIS modifié pour le packaging (si un chemin gêne, c'est
  le lanceur/SimBridge qu'on adapte, pas le moteur).
- `.spec`, recette Windows et scripts conservés (on ne jette pas de code) ;
  binaires et `build/`/`dist/` de PyInstaller **hors git** (.gitignore).
- Témoin de build à incrémenter (« t7 … ») — piège sync Nextcloud, et la
  boucle passe par 2 machines cette fois.
- Pédagogie à donner en route : ce que PyInstaller met VRAIMENT dans le
  binaire (un CPython + la stdlib + nos .pyc dans une archive auto-
  extraite), pourquoi le déterminisme survit au gel (même interpréteur,
  mêmes sources), et le compromis --onefile (démarrage un peu plus lent :
  décompression) vs --onedir.
- Après t7 : **sprint Intégration CLOS** → retour aux sprints moteur
  (BACKLOG.md) ; le « sprint save global » devient un bon candidat (le
  hook `OnSeasonEnd` attend toujours).
