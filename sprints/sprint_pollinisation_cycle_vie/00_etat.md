# État partagé — Sprint POLLINISATION & CYCLE DE VIE (implémentation)

> Conception FIGÉE : `docs/conception/CONCEPTION_POLLINISATION_CYCLE_VIE.md`
> (§A–§J figés, synthèse §K, découpe §L). Kickoff conception :
> `00_conception_kickoff.md`. Mémoire : [[design_pollinisation_cycle_vie]].
> Découpe = **7 tronçons** : ①→⑤ MOTEUR (re-fige le golden isolé), ⑥⑦ COUCHE
> JOUEUR (golden neutre, sprint distinct APRÈS le moteur).

## Avancement

- **① Floraison réelle + phénologie (A) — CLOS, golden NEUTRE.** ✅
  - `PlantInstance.floraison: float` + `gdd_accum: float` (instance.py).
  - `PlantBase.gdd_floraison / bloom_daylen_min / bloom_daylen_max` (familles.py,
    défauts estivaux placeholders).
  - `sim/engine/floraison.py` = `FloraisonMixin._tick_floraison` : double porte
    GDD (`T_BASE_FLORAISON=6 °C`, reset annuel) + photopériode (`daylength`) +
    maturité (`is_seed_bearing`) → relaxation de `floraison` (montée 0.35 /
    descente 0.50). N'émet AUCUN log, n'écrit que floraison/gdd_accum.
  - Câblé boucle.py (étape 9d, après croissance/sénescence ; la « phase floraison »
    proxy étape 10 reste en place jusqu'à ②/③).
  - **Golden INCHANGÉ** : `af3bfa8f…972f` (hors `_PLANT_ATTRS`, pas de log).
  - Sanity (non-régression du mécanisme) : annuelles estivales matures fleurissent
    (~0.58 pic sur 2 ans) ; tomate/poivron (morts précoces) & pommier (5 ans) à 0.

## Reste (ordre conseillé ②→③→④→⑤)

- **② Registre + champs par type + nectar (C/E)** — `PollinatorSpec` data-driven,
  N `PopulationField` (abeille/syrphe/papillon), ressource = `floraison ×
  attractivite` (remplace `_flower_grid`). **Golden re-figé MAÎTRISÉ.**
  Reprise : conception §C, §E.
- **③ Butineurs déterministes (F)** — agents, constance florale, dépôt
  `pollen_recu` + snapshot. Golden probablement neutre. §F.
- **④ Nouaison pollinisée (B)** — `_tick_fruits` lit `pollen_recu`, modes, fin de
  floraison par plante (remplace `FRUIT_NOUAISON_WEEK`). §B.
- **⑤ Ponts de cycle de vie (D)** — chenille→papillon, syrphe_larve→syrphe ;
  `HERBIVORY_GAIN` lit `ravageur + chenille`. **Golden re-figé MAÎTRISÉ.** §D.
- **⑥⑦ COUCHE JOUEUR** (ruche/miel H/I, piqûre J) — sprint distinct, golden neutre.

## Garde-fous

- Golden re-figé uniquement aux tronçons ② et ⑤ — **maîtrisé + annoncé**, isolé.
- Déterminisme : `seed`/`_hash_noise`/`daylength`, jamais de RNG vivant.
- Couches `plants ← fields ← sim` ; ~350 l code pur ; doc d'abord (FAIT).
- **Reprise à froid** : « lis `sprints/sprint_pollinisation_cycle_vie/00_etat.md`
  puis lance le tronçon ② (conception §C/§E) ».
