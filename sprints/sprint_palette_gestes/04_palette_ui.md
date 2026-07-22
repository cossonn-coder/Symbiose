# ④ PALETTE UI (C#) — kickoff autosuffisant

> Sprint PALETTE DE GESTES. Lire d'abord : `CLAUDE.md` + `00_etat.md` +
> `docs/joueur/gestes/conception_palette_gestes.md` §3.7 (D10/D11). Démarre à FROID.
> Prérequis : ①②③ faits (snapshot expose `gestes_debloques` ; bouturer/greffer
> câblés au pont). Ce tronçon est côté **Godot / C#** (`dotnet build` = filet ;
> F5 visuel = Nico).

## Objectif
Remplacer l'accès actuel aux gestes (touches `1..9` + `Tab` + modificateurs) par
une **palette cliquable en colonne sur le bord GAUCHE de l'écran**, **une icône
par geste** (D11). La palette **lit `gestes_debloques`** du snapshot : seuls les
gestes ouverts apparaissent (verrouillés masqués/grisés — calibrage F5). Golden
intact (aucun changement moteur).

## Existant à connaître (relève avant de coder)
- `world/WorldView.Actions.cs` : `Gestes[]` = tableau `(string Verb, string Nom,
  char Kind)` (24 gestes), `_gesteIndex` (sélection), sélection par `Key.Key1..9`
  + cycle `Tab` (`CycleGeste`), modificateurs `S` (graine), `B` (substrat), `N`
  (nature mulch). Kinds de cible : `p/q/t/m/x/a/s/E/P/C/U/D` (dont 2-temps
  `epandre`/`deplacer_pot`).
- `world/WorldView.Hud.cs` : HUD debug provisoire qui listait les gestes (la
  légende reconnaît que « la liste débordait » → c'est ce qu'on remplace).
- Snapshot : le bloc `player` porte désormais `gestes_debloques` (list de
  verbes ouverts, tronçon ①). Tolérance : un binaire pré-0.5.23 n'émet pas la clé
  → si absente, **retombe sur « tout dispo »** (tous les Verbs de `Gestes[]`).

## À implémenter
1. **Panneau palette gauche** : un `Control`/`VBoxContainer` ancré au bord
   gauche, une entrée par geste DÉBLOQUÉ, dans l'ordre de `Gestes[]`. Chaque
   entrée = un bouton icône cliquable qui sélectionne le geste (`_gesteIndex`).
   L'entrée active est mise en évidence. Le clic remplace la frappe `1..9`/`Tab`
   (garde éventuellement `Tab` en accélérateur, mais la SOURCE DE VÉRITÉ devient
   la palette). Pas de texte en HUD primaire (philo #5) — icône muette ;
   éventuel libellé au survol (tooltip) toléré.
2. **Icônes** : une icône par geste. Deux options (choisis la plus simple qui
   RENDE, tranche et signale) :
   - (a) **procédurales** — dessine un pictogramme simple par `Kind`/verbe (le
     projet a déjà des placeholders procéduraux : cf. tuiles/maison dans
     `WorldView`), zéro asset à produire ;
   - (b) **atlas d'icônes** — si un dossier d'icônes existe (`grep -rn "icon\|
     picto" *.cs project.godot`), charge-les via `SpriteLoader`.
   Recommandation : **(a) procédural** pour ne pas bloquer sur des assets ; une
   icône reconnaissable par famille de geste (goutte = arroser, sécateur =
   tailler/récolter, main = planter, tas = compost…). Signale ton choix à Nico.
3. **Filtre par déblocage** : ne construis les entrées QUE pour les verbes
   présents dans `gestes_debloques` du snapshot (ou tous si clé absente). Quand le
   snapshot change (déblocage en cours de partie), la palette se reconstruit.
   Un geste fraîchement débloqué peut clignoter/notifier (optionnel, calibrage F5).
4. **Câblage de TOUS les gestes** existants + `bouturer`/`greffer` : ajoute les
   deux nouvelles entrées à `Gestes[]` (Verb `bouturer`/`greffer`, Kind à 2 temps
   — même mécanisme que `epandre`/`deplacer_pot` : 1er clic source, 2e clic
   cible). Route-les vers le pont comme les autres gestes 2-temps.
5. **Modificateurs** (`S`/`B`/`N`) : conserve-les pour l'instant (graine/substrat/
   nature) — ils affinent des params, pas la sélection de geste. Peuvent devenir
   des sous-menus de la palette plus tard (hors périmètre ici, note en dette).

## Golden
**INTACT** — aucun fichier `data/code/` touché. Vérifie tout de même `cd
data/code && python3 -m tests.test_golden` (doit rester `452b5256…`). Filet C# :
`dotnet build Symbiose.csproj` doit compiler.

## Ne PAS faire
- Pas de logique de simulation en C# (Godot = VUE, Option B).
- Pas de macros ici (⑤). Juste la sélection unitaire de geste par clic.
- Pas de persistance du layout ici (⑤).
- Ne casse pas les gestes 2-temps existants (`epandre`/`deplacer_pot`).

## Vérifs de fin
1. `dotnet build` OK.
2. Golden inchangé (aucun fichier moteur touché).
3. Relève F5 pour Nico : « palette gauche cliquable, icônes, gestes filtrés par
   déblocage, bouturer/greffer sélectionnables ». (F5 = Nico, tu ne lances pas Godot.)
4. MAJ `00_etat.md` (§REPRISE → reste ⑤).
