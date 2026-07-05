# Tronçon ④ — Vue Godot : banc d'observation perf

> Kickoff autosuffisant. Lire `CLAUDE.md` + `00_etat.md` + `CONCEPTION_PERF_RUN_ETERNEL.md`
> §6/§7. C# côté Godot + éventuel champ snapshot côté `tools/simserver/serialize.py`.
> Filet de compilation : `dotnet build Symbiose.csproj` (SDK sur la VM). F5 visuel = Nico.

## Objectif
Donner à Nico **l'œil** pour observer, en jeu, que la stabilisation fonctionne : un
**compteur discret de perf** (mode debug) affichant `ms/tick`, `N plantes`, et si possible
la mémoire, PLUS un usage d'un banc d'observation longue durée (turbo) pour vérifier F5 que
`N(t)` plafonne et que le tick ne dérive plus. Règle projet : **chaque sprint finit par son
tronçon vue Godot** (mémoire `feedback_vue_godot_toujours`).

## Périmètre
1. **Compteur perf debug** (overlay C#, style des overlays existants — s'inspirer de
   `visuals/FieldOverlay.cs` toggle F6). Un toggle clavier dédié (ex. F7 si libre, sinon
   choisir/documenter) affiche un petit texte HUD :
   - `ms/tick` : temps du dernier `step_week` (mesuré côté Godot autour de l'appel pont,
     OU exposé par le serveur dans le snapshot — voir point 2).
   - `N plantes` : nombre total de plantes du snapshot (déjà disponible : compter les
     entrées plantes par tuile).
   - (option) RSS process serveur si le serveur l'expose.
   Étiqueté « affichage technique — debug » comme les autres overlays (philo #5 : pas de
   chiffres en HUD primaire ; ceci est un mode debug opt-in, pas le HUD de jeu).
2. **Exposition serveur (si nécessaire)** : si `ms/tick` est plus fiable mesuré côté Python,
   l'ajouter au SNAPSHOT (lecture seule) dans `tools/simserver/serialize.py` — un champ
   `perf: {ms_tick, n_plants, rss_mo}`. Règle d'or : **on ajoute au snapshot, jamais au
   tick** (le serveur reste un adaptateur, golden intact par construction). Mesurer le temps
   autour de `tick_semaine()` dans `commands.py` (step_week), pas dans le tick lui-même.

## Golden attendu
**INTACT** — hash de référence courant (voir `00_etat.md` : soit `061934db…` si ③ n'a pas
re-figé, soit le hash re-figé par ③). Ce tronçon n'ajoute QUE de l'observation (snapshot
lecture seule + overlay Godot). Vérifier : `python3 -m tests.test_golden`.

## Ce qu'il NE faut PAS faire
- Ne PAS ajouter de règle de simulation côté C# (Godot = vue, Option B). Le compteur
  OBSERVE, il ne décide rien.
- Ne PAS mettre le compteur dans le HUD primaire (philo #5) — mode debug opt-in seulement.
- Ne PAS toucher au tick pour mesurer (mesurer AUTOUR, dans le driver/serveur).
- Ne PAS lancer `test_epaisseur_500ans`.
- GDScript INTERDIT — tout en C#, namespace `Symbiose`.

## Points F5 (pour Nico, hors VM)
- Toggle le compteur, lancer en turbo sur le monde complet 8 tuiles, laisser courir
  ~10-15 ans : vérifier que `N plantes` **plafonne** (ne croît plus indéfiniment) et que
  `ms/tick` **se stabilise** (ne double plus d'année en année). C'est la VALIDATION visuelle
  du sprint entier.
- Si un `⚠ cap perf tuile` apparaît dans les logs debug en jeu normal → le backstop ③ est
  réglé trop bas (le signaler, ajuster la constante).

## Fin de tronçon
`00_etat.md` : compteur livré, champ snapshot `perf` éventuel, golden intact confirmé,
points F5 listés pour Nico. Commit. **Sprint clos** une fois le F5 de Nico validé.
