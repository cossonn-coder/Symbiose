  ▎ Tâche : tranche 04 « packaging » du projet Symbiose (dernière tranche, sur poste 
  ▎ Windows). Tu démarres à froid ; tout est dans le repo.
  ▎
  ▎ Contexte minimal : Symbiose = moteur Python (data/code/, source de vérité) + vue 
  ▎ Godot 4.6 .NET / C#. Architecture Option B : Python tourne en sous-process, Godot 
  ▎ est une vue. But du packaging : un dossier que des amis/famille lancent par 
  ▎ double-clic, sans Python ni Godot installés.
  ▎
  ▎ Recette autoritaire à SUIVRE : data/code/tools/RECETTE_PACKAGING.md (deux étages : 
  ▎ geler sim_server.exe via PyInstaller, puis export Godot + poser le binaire à côté de
  ▎ l'exe). Lis-la en entier avant de commencer.
  ▎
  ▎ ⚠️  Mises à jour à appliquer sur la recette (elle a vieilli) :
  ▎ - La recette dit « 87/87 checks » → c'est maintenant 158 checks (suite 
  ▎ tests/test_sim_server).
  ▎ - Protocole moteur = ENGINE_VERSION 0.3.8.
  ▎ - Golden de référence (ne doit pas bouger, mais tu n'y touches pas) : 908f591bee….
  ▎
  ▎ Étape 0 — vérifier la synchro AVANT de geler (piège récurrent : Nextcloud en retard)
  ▎ :
  ▎ - py --version doit répondre (Python requis pour geler).
  ▎ - La ligne public const string Build dans world/WorldView.cs doit contenir « 
  ▎ vue·rattrapage 03 correctif F5 ». Sinon, la synchro Nextcloud n'est pas finie → 
  ▎ stoppe et signale-le, ne gèle pas du vieux code.
  ▎
  ▎ Étape 1 — geler + valider (recette étage 1) : installer PyInstaller, geler depuis 
  ▎ data\code (les options --paths=. + les 2 --hidden-import sont OBLIGATOIRES), fumée 
  ▎ rapide, puis validation $env:SIM_SERVER_BIN → attendu PASS — 158/158 (et non 87). 
  ▎ Déterminisme : sortie byte-identique script vs binaire.
  ▎
  ▎ Étape 2 — export Godot + assemblage (recette étage 2) : compiler le C# (valide 
  ▎ SimBridge.cs bimode + tout le code 01–03), export preset Windows Desktop vers un 
  ▎ dossier vide, copier sim_server.exe à côté de Symbiose.exe. Vérifier le témoin via 
  ▎ Symbiose.console.exe : il doit afficher « Mode BINAIRE — moteur gelé » (= aucun 
  ▎ Python sollicité).
  ▎
  ▎ Critères de succès (cf. sprints/meta/sprint_vue_rattrapage/04_packaging.md) :
  ▎ - [ ] 158/158 sur le binaire gelé ;
  ▎ - [ ] console affiche « Mode BINAIRE » ;
  ▎ - [ ] double-clic Symbiose.exe hors éditeur → jardin complet + une saison + un geste
  ▎ de chaque famille (planter, arroser, tailler, manger-fruit, composter) + F6, sans 
  ▎ Python ;
  ▎ - [ ] F5 éditeur marche toujours sans binaire (repli dev intact).
  ▎
  ▎ NE FAIS PAS : pas de commit, pas de modif de docs/source, pas de re-figeage golden. 
  ▎ Tu exécutes et vérifies seulement. À la fin, produis un rapport : commandes lancées,
  ▎ résultat de la validation (le nombre de checks exact), témoin observé, et toute 
  ▎ anomalie (SmartScreen/antivirus sur le .exe PyInstaller est un faux positif 
  ▎ classique — le signaler si ça arrive). Le test visuel hors éditeur (double-clic)
  ▎ revient à Nico ; toi tu confirmes le « Mode BINAIRE » et les 158 checks.