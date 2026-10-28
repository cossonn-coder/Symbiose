# ② Régulateur de cadence + banc de partage (vue C#)

Lire d'abord : `CLAUDE.md`, `00_etat.md`, `docs/perf/fluidite/conception_fluidite_pc_partage.md`
§2 et §4 ②. **Golden intact** (aucun Python moteur). Filet : `dotnet build Symbiose.csproj`.
Pas d'appel DeepSeek.

## Contexte
Run PC 2026-10-27 [n=1 run] : A 2,78 s/sem (tick 1 819 ms), B rendu suspendu 1,19 s/sem
(tick 842 ms). Hypothèse NON mesurée : la vue rend sans plafond (≈17 FPS en A, la
synchro verticale ne bride jamais), l'iGPU HD 4600 et les cœurs partagent TDP et L3 →
le moteur ralentit. Plancher accepté par Nico : **15 FPS**.

## (a) Régulateur
- Nouveau partial (ex. `world/WorldView.Regulateur.cs`, un concept = un fichier).
- Règle : en `Phase.Saison`, si une semaine est **due** (`_timeAccum >= spw`, cf.
  `world/WorldView.cs` ~l.620-645) **et** un step est en vol (`_pendingStep != null`) →
  `Engine.MaxFps = 15`. Sinon plafond d'origine (mémorisé au démarrage). Plein régime
  aussi pendant ~1 s après toute interaction caméra (molette `StepZoom`, glisser,
  touches de caméra — `world/WorldView.Camera.cs` / `Controls.cs` : trouve les points
  d'entrée au code) et en Planification / pause.
- **Cohabitation** : `WorldView.Banc3Phases.cs` force `Engine.MaxFps = 60` pendant la
  phase B et restaure ensuite → le régulateur ne doit pas écraser ce réglage pendant B
  (un seul propriétaire de `Engine.MaxFps` à la fois : vérifie l'ordre au code). Phase C
  (moteur en pause) : aucune semaine due → jamais régulée, normal.
- Rendre l'état visible dans l'overlay F4 (« régulé 15 FPS » / « libre ») et le compter
  au rapport du banc (part du temps régulé).

## (b) Priorité moteur pilotable
`core/SimBridge.cs:166` `BaisserPriorite()` pose `BelowNormal` au lancement. Ajoute une
méthode pour basculer à chaud BelowNormal ↔ Normal (Windows `PriorityClass` ; Linux : le
`nice` ne remonte pas sans droits → sur VM, rapporter « non applicable » plutôt
qu'échouer). Défaut de jeu inchangé (BelowNormal) tant que le banc PC n'a pas parlé.

## (c) Banc de partage
- Nouvel argument (ex. `--capture-banc-partage=SEC`) : la phase **A** du banc 3 phases
  (`WorldView.Banc3Phases.cs`) est remplacée par **4 sous-phases** de SEC secondes,
  enchaînées : A1 régulateur OFF + BelowNormal (= A d'aujourd'hui) · A2 OFF + Normal ·
  A3 régulateur 15 + BelowNormal · A4 15 + Normal. Ordre C → A1..A4 → B conservé.
- Rapport : un tableau côte à côte (s/sem, tick moy., step vu, images moy., p99,
  > 100 ms, FPS, % du temps régulé) + rappel C et B. Biais à écrire dans le rapport :
  chaque sous-phase joue des semaines différentes.
- `tools/perf_vm.sh` : option correspondante (ex. `-P SEC`), documentée dans son en-tête.
- Respecte la taille de fichier (`tools/compte_ldc.py`) : `Banc3Phases.cs` risque de
  dépasser → scinde (partial dédié au partage).

## Mesure VM
`tools/perf_vm.sh -3 25,25,20 -P 20 -A 1 -W 90 -S 1521550718` [n=1 run] : rapporte le
tableau. Sur llvmpipe le rendu reste CPU : le chiffre VM ne prouve pas l'hypothèse iGPU,
il vérifie seulement que le régulateur s'engage/dégage et que le banc tourne.

## Ne PAS faire
Changer la cadence demandée, la logique d'étalement, le protocole du pont ; ajouter une
option au menu ; toucher `data/code/`.

## Fin de tronçon
`00_etat.md` §② (fichiers, mesure VM, argument exact du banc pour le run PC), commit.
F5 Nico (au ④) : en Saison accélérée, le vent/butineurs à 15 FPS quand la semaine est en
retard — gênant ? la caméra reste-t-elle fluide quand on la bouge ?
