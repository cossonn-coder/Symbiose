# T2 — Bouton + panneau Paramètres (launcher)

> Kickoff autosuffisant. Lire d'abord `CLAUDE.md` + `00_etat.md` (décisions
> A1/A7). Conception : `docs/joueur/interface/conception_fenetrage_ui.md` §4-T2.
> **T1 doit être fait** (patron défilable réutilisable + launcher haut-gauche).

## Objectif
Ajouter au launcher un bouton **« Paramètres »** ouvrant un sous-panneau
**défilable** (patron T1) qui regroupe deux familles d'options :
1. **Confort/debug** (leviers réels d'aujourd'hui) appliqués à la vue.
2. **Options d'init** passées au montage du monde (`cmd_init`).

Famille EXCLUE (A1) : params du modèle écologique — ne rien exposer de tel.

## Options à exposer

### Confort (vue)
- **Vitesse de sim** : `SecondsPerWeek` (`world/WorldView.cs:112`, plage 30-180 s,
  défaut 60). Un slider/stepper qui écrit ce champ.
- **Overlays debug** : toggles miroir des touches existantes (F6 heatmaps champs
  via `FieldOverlay`, F7 temp sol, O ombres, I vie macro). Réutiliser les mêmes
  méthodes `Toggle*` que `WorldView.Controls.cs` — ne pas dupliquer la logique.

### Init (passées à cmd_init)
- **Encyclopédie de démarrage** : vierge / amorcée / fournie (défaut : amorcée).
- **Carnet interprétatif anticipé** : OUI / NON (défaut : NON).

Ces deux choix sont **mémorisés** avant le lancement et transmis à
`StartSimulation` → `cmd_init`.

## À faire

### Python
1. `cmd_init` (`data/code/tools/simserver/commands.py`) : accepter deux champs
   **optionnels** dans le message :
   - `carnet_anticipe: bool` → poser
     `game_state["options"][player]["carnet_anticipe"] = True/False` (le backend
     `sim/carnet.py::_reglage_anticipe` le lit déjà ; `SEUIL_ANTICIPE = 1`).
     Créer le sous-dict `options`/`options[player]` s'il n'existe pas.
   - `encyclo_demarrage: "vierge"|"amorcee"|"fournie"` → **amorcer les paliers de
     maîtrise** du joueur courant à l'init :
       - `vierge` → ne rien amorcer (état actuel).
       - `amorcee` → amorcer un petit lot curé de clés à **palier 1** (ex. les
         cultivées de base) → fiches niveau 1 SANS basculer le carnet
         interprétatif (seuil 3).
       - `fournie` → amorcer toutes les clés connues à **palier 1**.
     Réutiliser le **mécanisme existant** d'amorçage de maîtrise (celui derrière
     le debug maîtrise, cf. `sim/maitrise.py` — repérer la fonction qui pose un
     palier ; NE PAS en écrire une nouvelle). Amorçage APRÈS construction du
     moteur et opt-in Vigueur, comme `BANC_POST_INIT`.
2. `tools/simserver/version.py` : bump + changelog (« cmd_init options d'init :
   carnet_anticipe, encyclo_demarrage »).
3. **Défauts = comportement actuel** : champs absents → aucun effet. `smoke`/`full`
   ne les passent jamais.

### C#
4. `SimBridge` : permettre à `Init(...)` (ou l'équivalent qui envoie `cmd_init`)
   de joindre les champs optionnels `carnet_anticipe` / `encyclo_demarrage`.
5. `WorldView.Selecteur.cs` : bouton « Paramètres » → ouvre un sous-panneau
   (nouveau `world/ParametresPanel.cs` si ça dépasse une responsabilité, sinon un
   partial) **défilable** (patron T1). Le panneau lit/écrit les réglages confort
   (SecondsPerWeek, toggles) et mémorise les choix d'init, retransmis à
   `StartSimulation`.
6. `StartSimulation` / le chemin d'init : propager les deux choix d'init au pont.

## Golden
**INCHANGÉ.** Défauts reproduisent l'actuel ; `smoke`/`full` ne passent pas les
options. Lancer `python3 -m tests.test_golden` (data/code/), vérifier le hash,
ne PAS re-figer.

## Filet de compilation
`dotnet build Symbiose.csproj` doit passer.

## Ce qu'il NE faut PAS faire
- Ne PAS exposer de params du modèle écologique (A1).
- Ne PAS écrire un nouveau mécanisme d'amorçage de maîtrise — réutiliser
  l'existant.
- Ne PAS rendre Paramètres accessible in-game (A7 : launcher-only v1).
- Ne PAS créer un onglet Paramètres (c'est un panneau du launcher).
- Ne PAS re-figer le golden.

## F5 (Nico)
Paramètres s'ouvre/défile. Changer la vitesse agit. Monter un banc en « encyclo
fournie » → l'encyclopédie est remplie. « Carnet anticipé » ON → le carnet
bascule en interprétatif dès palier 1.
