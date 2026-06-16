# 01 — Gestes joueur manquants (planter · arroser · écraser-plante)

> Lire `00_etat.md`. **Pur câblage C#** : le pont route déjà ces verbes (0.3.5),
> on ajoute la sélection/désignation côté vue. **Aucun moteur touché → golden
> neutre** (on ne fait que `SimBridge.Action`). Ampleur : **petit/moyen**.

## But
Rendre déclenchables dans Godot trois gestes que le moteur sait déjà appliquer
mais que la palette C# (8 gestes, touches 1..8) n'expose pas : **planter**
(avec choix de graine), **arroser**, **écraser une PLANTE** (≠ écraser un
nuisible, déjà présent en geste plot/guilde).

## Rappel du protocole (déjà en place, `tools/simserver/actions.py` + routeur)
- `planter` : `target = {tile, r, c}` (plot), `params.species` = clé catalogue.
  Le serveur refuse **en amont, sans coût** : espèce inconnue, **lot vide**, hors
  tuile. Coût `FAIBLE`. Les graines disponibles sont dans le snapshot
  `player.seeds {clé: nombre}` (se remplit aux récoltes d'automne).
- `arroser` : `target = {tile, r, c}`, `params.urgence` (bool) **ou**
  `params.phase == "saison"` → ×1.5. Coût `MODÉRÉ`. Monte l'humidité (cap 3.0).
- `ecraser` une plante : `target = {tile, x_cm, y_cm}` **sans `guilde`** →
  le routeur vise la PLANTE (modèle écrasement ②, seam croissance). `params.urgence`
  comme les autres. (Le geste `ecraser` plot/guilde actuel envoie une guilde →
  on le garde tel quel ; le serveur désambiguïse par présence de `x_cm/y_cm`.)

## Travail C# (`world/WorldView.Actions.cs` + `.Controls.cs` + `.Hud.cs`)
1. **Étendre la palette `Gestes`** au-delà de 8. On passe à ~14 verbes (avec 03)
   → la sélection par touches 1..8 ne suffit plus. **Défaut sobre proposé** :
   garder 1..8 pour les gestes courants, ajouter une **sélection cyclique**
   (ex. touches `[`/`]` ou molette sur un bandeau HUD) qui parcourt TOUTE la
   palette, le HUD affichant le geste courant + sa cible attendue. HUD riche =
   hors scope ; viser lisible, pas joli. *(À ajuster au F5 selon le ressenti.)*
2. **`planter` (kind `q`)** : sélection de l'espèce courante parmi
   `player.seeds` (snapshot). Une touche cycle l'espèce sélectionnée ; le HUD
   montre « planter : <espèce> (×N) ». Clic sur un plot → `target {tile,r,c}` +
   `params.species`. Lot vide / pas de graine → message du serveur relayé (déjà
   instructif), pas de pré-filtre côté vue (le serveur est juge).
3. **`arroser` (kind `q`)** : clic plot → `target {tile,r,c}` ; `params.urgence
   = _phase == Phase.Saison` (même couture préparation/réaction que `ecraser`).
4. **`ecraser` plante (kind `p`, NOUVELLE entrée distincte)** : libellé
   « écraser (plante) » ; réutilise le picking `FindPlant`/`FindSegmentGlobal` ;
   `target {tile, x_cm, y_cm}` (PAS de `guilde`) + `params.urgence`. Garder
   l'entrée « écraser (nuisible) » existante (plot/guilde) — deux gestes nommés.

## Vérification
- `export PATH="$HOME/.dotnet:$PATH" && dotnet build Symbiose.csproj` → vert.
- Golden inchangé `908f591bee…` (rien touché côté moteur — à re-lancer par
  principe ; aucune raison qu'il bouge).
- **F5 Nico** : (a) sélectionner planter, cycler une graine disponible, cliquer
  un plot → une plante apparaît au snapshot suivant (ou message « lot vide » si
  banque vide — avancer des saisons pour récolter d'abord) ; (b) arroser un plot
  en Pause vs en Saison (coût différent, message d'humidité) ; (c) écraser une
  plante → réponse (déformation/écimage/mort selon l'espèce, ②).

## Définition de fait
- [ ] planter / arroser / écraser-plante déclenchables et routés (logs console
      `→ action …`), réponses serveur relayées au HUD.
- [ ] Palette lisible au-delà de 8 gestes (sélection + libellé + cible).
- [ ] Build vert, golden inchangé, témoin de build incrémenté.
- [ ] `00_etat.md` : ligne 01 close + note F5. Commit.

## Commit suggéré
`feat(vue·rattrapage) : 01 — gestes planter/arroser/écraser-plante câblés (pont 0.3.5, moteur intact)`
