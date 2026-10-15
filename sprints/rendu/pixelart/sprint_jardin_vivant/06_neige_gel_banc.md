# T5 — Neige, grêle et gel + traces + banc F5 « jardin vivant » (tronçon vue final)

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, `docs/rendu/pixelart/conception_jardin_vivant.md` §5-§6.

## Objectif
Finir la météo animée sur les épisodes froids et violents, puis livrer à Nico
**un banc F5 unique** qui fait défiler les situations du sprint (calme, vent,
canicule, pluie, neige, grêle, gel) pour qu'il juge le ressenti d'un coup.

## Contexte vérifié
- Catalogue `data/code/sim/weather.py` : `Neige` (manteau neigeux, effet
  igloo), `Gelée tardive` (global, sem 8-15), `Grêle` (local, sem 10-26).
- Causes `gel`, `grele` dans `leaf_symptoms` (`sim/semiologie.py:221`) ;
  marques persistantes `plant.symptom_marks` (les dégâts AIGUS restent visibles
  après l'épisode — c'est la trace).
- `visuals/SnowLayer.cs` (manteau au sol, 57 LDC), `WeatherLayer.cs`,
  `CouvertureLayer.cs` (voiles posables D104 ③ — une plante sous voile ne
  doit PAS montrer la charge de neige/grêle).
- Bancs F5 existants : chercher le patron (`DecorLayer.Banc.cs`, bancs
  `WorldView.*`, encart ciel D104 ④) et le réutiliser.

## À faire (intention)
- **Variantes cuites** (infra T2) : neige = charge blanche sur la canopée ∝
  intensité, qui **raidit** la plante (flexion T3 réduite sous la charge) et
  tombe par plaques quand le vent forcit ; gel = givre (contours clairs,
  désaturation bleutée) ; grêle = feuilles trouées/déchiquetées ∝ `grele`.
- **Traces** : les marques `gel`/`grele` restent dessinées tant que le
  snapshot les porte (pas de minuterie inventée côté vue).
- Plante sous couverture/voile : pas de charge de neige ni d'impact de grêle.
- **Banc F5 « jardin vivant »** : enchaîne les épisodes (via le mécanisme de
  banc existant), avec l'encart ciel ; une ligne de doc d'usage dans
  `00_etat.md` (touche, durée). Captures T0 de chaque épisode.
- **Clôture du sprint** : `00_etat.md` (mesures finales, tableau des tronçons),
  entrée `journal/` + pointeur `journal.md`, `BACKLOG.md` (sprint A clos,
  sprint B faune/champignons/fumée/eau à concevoir), `DETTE.md` (D34/D44 :
  noter ce que le sprint a couvert ou non), `/refactor` auto-léger si un
  fichier a franchi 400 LDC.

## Critère de réussite
PNG T0 des 7 situations décrits dans `00_etat.md` ; `dotnet build` vert ;
`test_sim_server` vert ; golden intact. Question F5 unique pour Nico :
« le jardin est-il beau et vivant ? » (+ liste courte de ce qu'il doit regarder).

## NE PAS
- Animer sans épisode ; synchroniser les réponses de toutes les plantes.
- Inventer une durée de trace côté vue (la vérité est dans le snapshot).
- Toucher au moteur Python / golden ; GDScript ; `test_epaisseur_500ans` ;
  fichiers > 400 LDC.
