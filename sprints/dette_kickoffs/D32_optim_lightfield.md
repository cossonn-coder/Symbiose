# Dette D32 — Optimisation du LightField (dette de perf)

> **Kickoff autosuffisant.** Lis ce fichier en entier, puis les sources, puis
> exécute. Français + pédagogie (tu es expert simulation/perf — ici on parle ton
> langage). Ampleur **moyenne**. **Pas de choix de design pour toi** : l'approche est
> claire ; le seul arbitrage est *quand* (« si la perf serre »). **Optimisation à
> golden STRICTEMENT intact** (c'est une dette de perf, pas de comportement).

## Ce que c'est, en une phrase
Réduire le coût CPU du `LightField` : le profilage du 2026-06-04 (monde cible, 432
plots) montre que `fields/light.py` pèse **~53 % du CPU**, **recalculé entièrement
chaque tick**, et que son coût **croît avec la taille des canopées** (74 → 325 ms/tick
quand la végétation mûrit). C'est le **premier centre de coût** du moteur.

## L'état du moteur aujourd'hui (vérifié)
- `fields/light.py` : `LightField(GridField)` ; `compute(plants, saison) -> list[str]`
  rastérise des **ombres-capsules astronomiques** à **2 cm/px** ; le test
  `_point_in_capsule(px, py, …)` est appelé pour chaque pixel d'ombre × chaque plante
  projetante. `_sun_slices(saison)` est **déjà caché** (`_sun_cache` par saison) — donc
  le soleil n'est pas le problème, c'est la **rastérisation des canopées**.
- **Appelé chaque tick** par l'engine (l'éclairement pilote `growth_factor`). Le
  résultat (`light_received` par plante) **est lu** par le tick → toute optimisation
  doit rendre **exactement les mêmes valeurs** (golden intact, bit à bit).
- **Profil mémoire** : 27 Mo, **non-sujet**. C'est purement du CPU.
- **Marge actuelle** : gameplay à **×339** (1 semaine = 60 s réel, 177 ms/tick moyen
  Python). → **Aucune urgence en jeu.** Devient pertinent pour : (a) la **sim
  accélérée/offline** (génération de terrain, rejeu 500 ans ≈ 1-2 h Python), (b) le
  **portage C#** (D24, ×10-30 attendu, mais le hotspot reste le hotspot).
- Réf mémoire : `perf_profile_simulation.md` (177 ms/tick, LightField 53 %, coût ∝
  canopée).

## Ce qui est déjà tranché (ne pas re-débattre)
- **Pas d'urgence** : « À optimiser **seulement si la perf serre** » (DETTE.md D32).
  Ce kickoff est un **plan prêt**, à dégainer le jour où la sim offline ou le portage
  rendent les ms importantes — pas avant (ne pas optimiser prématurément, CLAUDE.md §2).
- **Golden sacré** : l'optimisation doit être **iso-résultat** (mêmes
  `light_received`, donc même golden `6369c30b…`). Une approximation qui change une
  décimale **re-figerait le golden** = elle n'est **pas** acceptable ici (ce serait un
  changement de comportement déguisé, pas une optim).

## Les 3 leviers (du moins au plus invasif) — à appliquer dans cet ordre
DETTE.md liste 3 pistes ; voici l'ordre de risque/rendement, **chacune golden-neutre
si faite proprement** :

### Levier 1 — Bounding-box par capsule (gain élevé, risque nul) — ⭐ commencer ici
Aujourd'hui (à vérifier dans `compute`) la boucle teste `_point_in_capsule` sur une
zone large. Restreindre l'itération à la **boîte englobante** de chaque ombre-capsule
(la capsule est bornée : on connaît son extension max depuis hauteur×inv_tan + rayon).
- **Iso-résultat** : on ne teste pas moins de pixels *vrais*, on **saute** ceux qui
  sont mathématiquement hors capsule. Mêmes valeurs, exactement.
- **Gain** : ∝ rapport (aire boîte / aire grille) — souvent grand pour les petites
  plantes.

### Levier 2 — Cache d'ombres tant que la plante n'a pas grandi (gain élevé)
La projection d'ombre d'une plante ne change que si **sa géométrie change**
(hauteur/rayon/position) **ou la saison** (angle solaire). Mémoriser l'empreinte
d'ombre par plante, **invalidée** quand `(height_at, canopy_radius_at, saison)` bouge.
- **Iso-résultat** : recalcul déclenché exactement quand un input change → mêmes
  valeurs. Avec la croissance procédurale (D29) les plantes changent **chaque tick**
  tant qu'elles poussent, mais **se stabilisent** à maturité → le cache paie surtout
  sur un jardin mûr (justement quand le coût explose : 325 ms).
- **Attention** : l'invalidation doit être **exacte** (clé = tous les inputs de la
  projection), sinon golden faussé. C'est le levier le plus subtil → bien tester.

### Levier 3 — Résolution adaptative (gain moyen, à manier avec prudence)
Rastériser les grandes ombres à une résolution plus grossière que 2 cm/px.
- **⚠️ Risque golden** : changer la résolution **change les valeurs** → **re-fige le
  golden**. Donc ce levier n'est **iso-résultat que** si on garde 2 cm/px pour le
  calcul des `light_received` et qu'on n'allège que le **rendu** (Godot), pas la sim.
  → **Pour la sim, NE PAS toucher la résolution.** Réservé au rendu Godot (tronçon 4),
  hors de cette dette. Mentionné pour mémoire.

## Périmètre
1. **Re-profiler** d'abord (confirmer que LightField est toujours le hotspot, mesurer
   l'état actuel post-croissance-procédurale). Un micro-bench reproductible
   (`tests/` ou script jetable) sur un jardin mûr.
2. **Levier 1** (bounding-box), puis **Levier 2** (cache invalidé), **chacun suivi
   d'une vérification golden bit-à-bit** (`test_golden` doit redonner le **même**
   hash).
3. Re-mesurer le gain (objectif : casser la croissance ∝ canopée).

## Hors périmètre
Toute **approximation** qui changerait `light_received` (= re-figeage = changement de
comportement déguisé). La **résolution de rendu** Godot (Levier 3, tronçon rendu). Le
portage C# du LightField (D24 — mais ce plan d'optim s'y transpose). L'optim des
**autres** centres de coût (LightField d'abord, c'est 53 %).

## Vérification (success criteria)
```
cd data/code
python3 -m tests.test_golden   # MÊME hash 6369c30b… — iso-résultat OBLIGATOIRE
python3 -m tests.test_croissance && python3 -m tests.test_population
python3 main.py                # plus rapide, comportement identique
```
Critère dur : **golden bit-à-bit intact** (sinon ce n'est pas une optim, c'est un
bug), et coût LightField **mesurablement réduit** sur un jardin mûr. MAJ
`DETTE.md` D32 (leviers appliqués + gain mesuré) + `perf_profile_simulation.md`.
