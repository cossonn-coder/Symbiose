# 2026-06-19 — Sprint CATALOGUE ENRICHI · tronçon ⑥b (vue Godot, C#) — SPRINT TERMINÉ

**Vue Godot de la faune nommée : table sprite par espèce + butineurs B + heatmaps
par espèce + bascule client `target.espece`.** Seconde moitié de ⑥, clôt le sprint
CATALOGUE ENRICHI. 100 % vue (0 ligne Python), golden **NEUTRE**, F5 validé par Nico.

## Contexte

Depuis la scission faune ④b–④d le snapshot émet des **clés d'espèce** (puceron…
cloporte) + 5 pollinisateurs, mais le client mappait encore les **3 anciennes
guildes** (`ravageur`/`auxiliaire`/`vers_de_terre`) → les 10 espèces tombaient en
point gris `GuildeInconnue`. ⑥a (Python) avait posé le protocole `target.espece`
(serveur l'accepte, `guilde` en repli). ⑥b câble la vue.

## Ce qui est fait (4 fichiers C#)

1. **`visuals/MacroLife.cs`** : dict `Guilds` (4 guildes) → `Especes` (10
   consommateurs : 3 ravageurs puceron/limace/doryphore, 5 auxiliaires coccinelle/
   chrysope/carabe/merle/hérisson, 2 détritivores lombric/cloporte). Couleur/rayon/
   amplitude d'errance/vitesse par espèce — **placeholders procéduraux** (pas de PNG,
   décision Nico) : oiseaux/hérisson errent large, limace/cloporte traînent,
   `lombric` garde le **tiret** du ver (rayon 0). `GuildeInconnue`→`EspeceInconnue`
   (filet gris conservé). `NonDessine` += `bourdon, osmie` (les 5 pollinisateurs sont
   des AGENTS butineurs dessinés par ForagerLayer, pas un nuage de densité ; le
   snapshot émet pourtant leur densité dans `sprites` → on les saute). NOUVEAU
   `SpeciesNear(w, r)` = espèce du sprite vivant dont l'ancre est la plus proche.
2. **`visuals/ForagerLayer.cs`** : `Guilds` += `bourdon` (gros, lent, ambré) /
   `osmie` (menue, vive, cuivrée). Le bloc `foragers` les expose déjà (registre ⑤).
3. **`visuals/FieldOverlay.cs`** : `Palettes` += **15 espèces** (10 consommateurs +
   5 pollinisateurs). Pôle haut = la couleur du point MacroLife/ForagerLayer de
   l'espèce → **un seul langage visuel** (la heatmap double les points). Bornes fixes
   0..1 (densités bornées côté moteur). Les 4 palettes de guildes legacy sont retirées
   (le registre `fields` ne les émet plus).
4. **`world/WorldView.Actions.cs`** : `ecraser` au plot émet `target["espece"]` =
   `_macroLife.SpeciesNear(w, MacroPickRadiusCm=50)` quand un sprite est sous le
   curseur (on écrase ce qu'on VOIT) ; sans sprite à portée → plot seul, le serveur
   applique son défaut (`puceron`). Commentaires `guilde`→`espèce` (Actions +
   `WorldView.cs:361`, mode instrument FocusGuild).

## Décision tranchée par Claude (le HANDOFF la laissait ouverte)

**Heatmaps par ESPÈCE, pas par catégorie.** Le registre `fields` du serveur expose
déjà une grille **par espèce** (`eco.populations`, 15 clés) ; une heatmap par
catégorie aurait exigé d'exposer `category_density` côté Python — hors du périmètre
« ⑥b = 100 % vue ». Le mode instrument (resserrement d'errance sur l'ancre quand la
heatmap d'une espèce est affichée) fonctionne tel quel : `FocusGuild` = nom de champ
= nom d'espèce = `entry.Guild`.

## Vérifs

- `dotnet build Symbiose.csproj` : **0 erreur, 0 avertissement**.
- Golden Python re-vérifié par sécurité (⑥b ne touche pas Python) : **`f7e1a9b4…`
  INCHANGÉ** — golden NEUTRE.
- **F5 validé par Nico** : bestioles colorées par espèce, butineurs bourdon/osmie,
  écrasement ciblé d'un sprite nommé.

## Sprint CATALOGUE ENRICHI — bilan

①→⑥ TOUS CLOS. Plantes : 17 → **27** (②③, 5 familles botaniques neuves). Faune : 3
guildes abstraites → **15 espèces nommées data-driven** (10 consommateurs modèle B
④ + 5 pollinisateurs ⑤), encyclopédie complète (④e/⑥a), pont par espèce (⑥a),
vue Godot par espèce (⑥b). 3 re-figeages golden localisés et maîtrisés (④b/④c/④d),
puis ⑤ (pollen→nouaison) → golden final **`f7e1a9b4…`** ; vigueur-traj `e63b9d7f…`
inchangée tout du long.

## Dette signalée (hors périmètre catalogue, à arbitrer)

- `fields/population.py` > garde-fou ~350 LDC pur (alourdi par les triades) →
  éclatement en paquet `fields/population/` dans un sprint refactor dédié.
- 2 échecs PRÉ-EXISTANTS : `test_senescence` (~2.7 ans, modèle eau) ; `test_sim_server`
  pommier nouaison (0 fruit @ S52). → dette, hors catalogue.
- Repli serveur `guilde` sur `ecraser` (actions.py:240) : le client est basculé sur
  `espece` (⑥b), le repli peut être retiré quand on veut (optionnel, compat).
