# ① — Banc du jardin réel + instrument + étalonnage VM ↔ PC

> Lire d'abord `CLAUDE.md`, `00_etat.md` (même dossier) et
> `docs/perf/lod/conception_perf_vue.md`. Vue C# + scripts. Golden intact
> (vérifier en tête : `cd data/code && python3 -m tests.test_golden`).

## Objectif
Reproduire **le jardin réel de Nico** (an 1-2, 300-400 plantes, vie macro pleine, ombres ON) de
façon déterministe, sur la VM ET sur son PC, et mesurer **où part le temps** — sans rien optimiser.

1. **Scénario de banc** : graine fixe, avance automatique jusqu'au **printemps de l'an 2**
   (~55 semaines). Partir de l'existant : `tools/perf_vm.sh` (options `-b -S -w -T -z -x`) et
   `world/WorldView.Capture.cs` (`--capture-banc/semaines/seed/turbo`). Vérifier par mesure que
   le scénario atteint bien 300-400 plantes et plusieurs milliers d'entrées de vie macro ; sinon
   ajuster graine/semaines. Rester sur le monde `full` (celui de Nico).
2. **Lancement sur le PC de Nico SANS ligne de commande** (il lance par F5 dans l'éditeur Windows) :
   une touche libre (lire `world/WorldView.Controls.cs` + la légende F1 de `WorldView.Hud.cs` avant
   de choisir) qui déroule le même scénario : avance au plus vite jusqu'au point de banc, pose zoom
   ×4 au centre défini, cadence nominale, mesure N secondes, puis copie le rapport dans le
   presse-papier (comme C). La légende F1 la mentionne.
3. **Instrument** (étendre `world/WorldView.PerfMesure.cs` / `WorldView.PerfReport.cs`) :
   - distribution du temps d'image sur la fenêtre de mesure : médiane, p95, p99, max, nombre
     d'images > 33 ms et > 100 ms (horloge murale, pas `delta`) ;
   - coût CPU par poste, chronométré autour des points d'entrée existants : `_Process` /
     `_Draw` vie macro, ombres (redessins par seconde + ms), plantes (vent, cuisson `BakeQueue`),
     application de semaine (`WorldView.Etalement.cs`), sol ;
   - état des bascules dans le rapport : vie macro visible O/N (la touche I ne change pas
     `Count` — le rapport actuel ne permet pas de savoir si elle était masquée), ombres, cadence ;
   - le rapport doit dire VM ou PC (OS / nom du GPU via `RenderingServer.GetVideoAdapterName()`).
4. **Matrice VM** : sur le scénario, 4 cas (vie macro × ombres) à ×4, et tout affiché à ×0,5,
   ×1, ×2, ×8 — n ≥ 2 runs par cas, charge VM vérifiée (`perf_vm.sh` le fait).

## Ne pas faire
Aucune optimisation, aucun changement de rendu. Ne pas toucher `data/code/` ni le pont. Ne pas
corriger la fuite `MacroLife` ici (c'est ②) — la **mesurer** seulement (entrées vivantes vs
mourantes). Ne jamais lancer `test_epaisseur_500ans`.

## Fin de tronçon
- `00_etat.md` : tableau de référence VM (cas × palier, n runs), touche choisie, mode d'emploi.
- Commit ; l'orchestrateur pousse (Nico doit pouvoir tirer le banc sur Windows).
- **Étalonnage Nico (seul point F5 de mesure du sprint)** : « `git pull`, F5, touche X, attendre
  la fin, coller le rapport ». Le sous-agent ne l'attend pas : il consigne la demande dans
  `00_etat.md` ; l'orchestrateur la transmet à Nico. Les tronçons ②-④ avancent sur les mesures VM
  (draw calls, primitives, ms CPU par poste) ; la conversion PC se fait en ⑤ avec le rapport de Nico.
