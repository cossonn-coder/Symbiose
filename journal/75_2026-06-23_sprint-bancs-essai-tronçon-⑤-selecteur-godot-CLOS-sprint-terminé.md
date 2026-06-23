# 2026-06-23 — Sprint « bancs d'essai » · tronçon ⑤ (sélecteur Godot + bilan D47) — SPRINT TERMINÉ

> Sprint dédié né du verdict F5 du 2026-06-22 (post-plasticité) : la carte `full`
> est un jardin de démo, pas un instrument d'observation — un signe muet à l'écran
> ne dit pas si c'est un bug ou un artefact de carte (dette D47). Réponse : une
> bibliothèque de **mondes paramétrés** (paquet `bancs/`) qui FORCENT chaque
> condition observable, **chacun avec un oracle** Python qui asserte le signe au
> même endroit que la vue le lit (`sim/semiologie.py`). Tronçons ①→④ : infra +
> 9 fabriques (édaphique/climatique/biotique) + oracles, golden NEUTRE tout du long.
> Ce tronçon ⑤ = rendre les bancs choisissables à l'écran + consolider le bilan D47.

## Ce qui est livré (code, côté VM)

### 1. Commande pont `list_bancs` (pont 0.5.4)
- `tools/simserver/commands.py:cmd_list_bancs` → `{"ok": True, "bancs": sorted(BANCS)}`.
  Lecture du **registre Python** `BANCS`, **sans moteur** → appelable AVANT `init`
  (pour peupler le menu). Enregistrée au dispatch (`server.py`).
- **Décision tranchée** (le kickoff me la déléguait : « choisir le plus simple et
  le NOTER ») : la liste vient du SERVEUR, pas d'une copie codée en dur en C#.
  Raison qui l'emporte sur la simplicité brute → **principe #1 du projet : Python
  source de vérité**. Une liste codée en dur en C# serait une 2ᵉ source qui se
  périme en silence à l'ajout d'un banc ; or ce sprint existe précisément parce
  que des signaux ambigus ont égaré le diagnostic (D47). Un **menu qui ment** est
  le faux signal même qu'on cherche à éliminer. Coût marginal (~6 lignes Python +
  ~10 C#), bump de pont 0.5.4 explicitement anticipé par le kickoff, golden
  *écologique* NEUTRE (la version de pont est indépendante du hash).
- Repli : un vieux binaire gelé pré-0.5.4 répond « commande inconnue » →
  `SimBridge.ListBancs()` renvoie `[]` → le sélecteur retombe sur `full`/`smoke`.

### 2. `SimBridge.ListBancs()` (C#)
Demande `list_bancs` au serveur, renvoie `string[]`. Appelable après `Start()`
sans `Init` (lecture du registre).

### 3. Sélecteur Godot — `world/WorldView.Selecteur.cs` (nouveau partial, 41 LDC pur)
- `_Ready` ne lance plus la `config` de l'Export directement : il démarre le pont
  (`_bridge.Start()`) puis appelle `BuildSelecteur()`.
- `BuildSelecteur` : `CanvasLayer` + `PanelContainer` centré → `Label` « Choisir un
  monde » + `OptionButton` (peuplé `full`, `smoke`, puis `_bridge.ListBancs()`,
  présélection = la `config` de l'Export) + `Button` « Lancer ». Au clic : lit la
  config choisie, libère le menu (`QueueFree`), appelle `StartSimulation(config)`.
- `StartSimulation(string config)` = l'ancienne séquence de `_Ready` extraite
  TELLE QUELLE (init → warmup → construction des couches → 1er snapshot → caméra),
  paramétrée par la config choisie. Pose `_started = true` à la fin.
- **Garde `_started`** (nouveau champ bool) en tête de `_Process` ET de
  `_UnhandledInput` : tant que le monde n'est pas construit, la boucle et les
  entrées court-circuitent (pas de déréférencement de `_objects`/`_origins` nuls).
- `dotnet build Symbiose.csproj` : **vert** (0 erreur, 0 avertissement). F5 visuel
  = Nico (Godot pas sur la VM).

## Bilan D47 (consolidé, cf. DETTE.md)
Verdicts MOTEUR (oracles verts aux ②③④) :
- **C4 CLOS = artefact de carte** : la chaîne floraison→pollen→butineurs→nouaison→
  fruits FONCTIONNE (`verger_floraison` : 7 butineurs, 3 fruits). « 0 fruit/0
  butineur » sur `full` = conditions de carte (photopériode ~sem 15, nouaison à la
  fanaison ~sem 35, pollinisateurs requis), pas une régression.
- **C5 CLOS = design, pas bug** : tomate ET poivron lèvent/survivent dans
  `semis_tempere` (porte de `planter` saine). Symptôme `full` = fragilité Solanaceae
  (mildiou familial + froid de démarrage) → protection des semis.
- **C6 CLOS = symptôme de D41** : sol uniformément pauvre = épuisement NORMAL
  (uptake > minéralisation), croissance bridée Liebig sans mort.
- **C2 / C3 / `ombre` = SUSPECTS RENDU C#, à confirmer au F5 du ⑤** (instrument =
  oracle vert + écran muet ⇒ bug rendu) : `ombre` (`ombre_dense`) = dette 0.5.2
  déjà ouverte (mapping couleur/texture manquant dans `PlantRenderer`) ; `asphyxie`
  (C2) émis dès `asphyxie_memory > 0.10` (intégration lente 0.05/sem) → mapping à
  vérifier ; `ravageurs` (C3) émis dès densité > ~0.025 (floor sous-perceptif) →
  au F5, témoin criblé ⇒ bug rendu, sinon criblage sincère.

## Vérifs
- Golden NEUTRE : `2ab026ad2b3f484777a2a29f804e1a4785ecffd6976fc0058fe0a33dd1498646`
  (inchangé depuis le ② — les bancs ne sont jamais montés pour smoke/full).
- `list_bancs` bout-en-bout : renvoie les 9 bancs triés.
- `dotnet build` vert. `WorldView.Selecteur.cs` = 41 LDC pur (≪ 350).

## Reste (hors périmètre du sprint)
- **F5 visuel = Nico** : exhiber chaque banc, confronter écran ↔ oracle, verser les
  bugs RENDU confirmés (C2 `asphyxie`, C3 `ravageurs` si témoin criblé) en dette
  ciblée mapping `PlantRenderer`.
- **Lever la dette 0.5.2** (mapping `ombre` dans `PlantRenderer`) — `ombre_dense` en
  est l'instrument de validation.
