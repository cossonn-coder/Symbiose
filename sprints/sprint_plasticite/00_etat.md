# Sprint « plasticité & expression de gènes adaptogènes » — état partagé

> Le stress VÉCU module l'EXPRESSION effective des gènes adaptogènes (plasticité
> phénotypique / épigénétique), distincte de la sélection darwinienne sur le
> génotype figé. Conception FIGÉE : `docs/conception/CONCEPTION_PLASTICITE_EXPRESSION.md`.
> **Lire la conception AVANT tout tronçon.**

## Modèle (3 échelles d'adaptation coexistantes)
- **génotype** `genes[g]` — darwinien, figé, irréversible (existe déjà) ;
- **expression** `expression[g]` — lamarckien, plastique, réversible (NOUVEAU)
  via `expressed_gene(g) = clamp_gene(genes[g] × expression[g])` ;
- `stress_memory` — recentré sur la seule mortalité de fond.

## Décisions figées (Nico, 2026-06-21)
- **5 gènes adaptogènes** : `tolerance_secheresse`, `tolerance_ombre`,
  `rusticite_froid`, `resistance_pathogene`, `tolerance_asphyxie`. Créer
  `cold_memory` + `infection_memory` ; ajouter le gène `tolerance_asphyxie`
  (`asphyxie_memory` existe déjà).
- **Coût** = compromis croissance/défense (la sur-expression ronge la vigueur,
  pas de bonus direct — philo #2).
- **Priming transgénérationnel** : mère seule, **oubli ÉMERGENT** (pas de compteur).
- **Hystérèse** : `TAU_UP` ≠ `TAU_DOWN` (désacclimatation plus lente).
- **Signe diégétique visible** (mécanique apprenable, pas magique).
- **Lien Maîtrise → carnet interprétatif** = dette (hors sprint).
- **Calibrage itératif** assumé ; double registre darwinien+lamarckien assumé.

## Tronçons
| # | Titre | Golden | Statut |
|---|---|---|---|
| ① | substrat (gène asphyxie + 2 mémoires + `expression` + `expressed_gene` + dynamique) | re-figé `f503dc15…` (artefact digest, voir note) | **CLOS** |
| ② | branchement `expressed_gene` chez tous les consommateurs | re-figé `0549fc35…` (acclimatation active) | **CLOS** |
| ③ | coût croissance/défense (vigueur) | re-figé `f3635a1d…` (+ `population_hash` `6056713d…`) | **CLOS** |
| ④ | priming transgénérationnel (`child_expression` + banque-sol) | re-figé `2ab026ad…` (lignées pré-armées) | **CLOS** |
| ⑤ | signe d'acclimatation (sémiologie + vue C#) + dette | NEUTRE (lecture) | à faire |

## Golden
- Départ : `3f86bf5310712c6b73e3f74840aa1367d53ea8ad3ca86d21af4bb7fcdafbd29c`
  (post « mort par stress chronique » voie ombre).
- Après ① : `f503dc15f07800869edb3132a301f8fb0f5a8515e966efe85a7d4401929dcd82`.
- Après ② : `0549fc35728753d85ba5a0d523e697b9e5757ec02d87a82aca376bb0de1333ca`.
- Après ③ : `f3635a1d05e74eb788196de0ab1a0d304336985c4f4fa8f19ba716dbc2aa703d`
  (+ `tests/population_hash.txt` re-figé `cd21704b…`→`6056713d…`, même cause).
- Après ④ : `2ab026ad2b3f484777a2a29f804e1a4785ecffd6976fc0058fe0a33dd1498646`
  (`population_hash` `6056713d…` INCHANGÉ — le macro ne dérive pas dans la fenêtre).
- Pont actuel : **0.5.2** (inchangé aux ①②③④ — aucun schéma de pont touché).

## REPRISE
④ CLOS. Reprendre par `05_signe.md` (signe d'acclimatation : sémiologie d'un
durcissement visible + mapping/texture côté `PlantRenderer` C#, lecture seule
→ golden NEUTRE ; clore aussi la dette « Maîtrise → carnet interprétatif »).

## Journal de bord (MAJ en fin de chaque tronçon)
- **① substrat — CLOS (golden re-figé `f503dc15…`).** Posé : gène
  `tolerance_asphyxie` (fin de `GENE_NAMES`), `ADAPTOGENIC_GENES` + knobs
  (`EXPR_GAIN=0.30`, `EXPR_MIN=1.0`, `EXPR_MAX=1.30`, `TAU_UP=0.08`,
  `TAU_DOWN=0.04`) dans `genetics.py` ; mémoires `cold_memory` + `infection_memory`
  + état `expression` + méthode `expressed_gene()` sur `PlantInstance` ; signaux
  (froid sub-létal < 10 °C ; pression pathogène = manque de protection sol ×
  humidité) + dynamique d'expression lerp à hystérèse dans `_update_physiology`.
  Test `tests/test_plasticite.py` (math + montée TAU_UP + hystérèse).
  **DÉRIVE GOLDEN = pur artefact de sérialisation** : le digest fige `genes[...]`,
  donc la clé `tolerance_asphyxie` y apparaît sur les plantes reproduites/semées.
  PROUVÉ comportementalement neutre : `LOG-only` (`0da50a36…`) ET `DIGEST` privé
  des gènes (`41d68a4a…`) **identiques bit-à-bit** avant/après. Aucun consommateur
  ne lit `expressed_gene` (acclimatation INERTE, branchée au ②). Re-figeage validé
  par Nico (option « re-figer », recommandée). Tous tests ciblés verts
  (genetique, vigueur, population-hash, stress_chronique, eau, croissance…).
- **② branchement — CLOS (golden re-figé `f503dc15…`→`0549fc35…`).** 9 sites
  passent `gene(…)`→`expressed_gene(…)`, uniquement les gènes adaptogènes :
  `perturbations.py` ×4 (damping_off + fungal_disease `resistance_pathogene`,
  drought_stress_damage `tolerance_secheresse`, shade_stress_damage
  `tolerance_ombre`) ; `croissance.py` ×2 (gate `ok_hum` sécheresse, growth_factor
  ombre) ; `phases.py` `shade_tolerance_effective` (étiolement) ; `mortalite.py`
  `_mediated_damage` (gel `rusticite_froid`) + **asphyxie** (premier consommateur
  du gène `tolerance_asphyxie`, jusqu'ici non médié). `gene("vigueur"/"hauteur")`
  laissés intacts (non adaptogènes). **DÉRIVE GOLDEN attendue & plausible** :
  `EXPR_MIN=1.0` → `expressed_gene ≥ gene` partout → l'acclimatation ne fait
  qu'ADOUCIR (le coût n'arrive qu'au ③) ; sur 4 ans le monde golden accumule
  ombre/sécheresse → expression > 1 → dégâts/gates plus doux, monotone et borné
  (`EXPR_MAX=1.30` + `clamp_gene`). Test `test_branchement_acclimatation` :
  neutre = génotype exact (non-régression) ; endurci 21 dégâts < neutre 34 +
  gate ombre relevée. `dotnet build` vert (aucun schéma de pont changé).
- **③ coût croissance/défense — CLOS (golden re-figé `0549fc35…`→`f3635a1d…`).**
  Knobs `DEFENSE_COST=0.15` + `DEFENSE_PLANCHER=0.5` (départ, calibrage itératif P6)
  dans `genetics.py`. `cout_defense()` = méthode sur `PlantInstance` (à côté
  d'`expressed_gene`, même nature : lecture dérivée de `expression`) :
  `max(PLANCHER, 1 − DEFENSE_COST × Σ_g max(0, expr[g]−1))` — seule la part > 1
  ronge, désexprimer est gratuit, jamais sous le plancher.
  **DÉVIATION DE SPEC ASSUMÉE (validée Nico) :** la conception §2.4 / le kickoff
  pointaient `vigueur_plante.py:91`, MAIS cette façade est read-only et **le tick
  ne l'appelle JAMAIS** (seul `gestes.py:89` « manger » la lit) → y appliquer le
  coût laissait le golden NEUTRE et ne touchait NI croissance NI graines, en
  contradiction avec l'intention §2.4 (« croît moins, moins de graines ») et la
  vérif kickoff (« hash change »). Nico a tranché **« croissance réelle (tick) »** :
  coût multiplié sur les lectures de `gene("vigueur")` DANS le tick —
  `croissance.py:109` (vitesse d'avancement de stade) + `mortalite.py:89`
  (convalescence). La façade `vigueur_plante` reste INCHANGÉE.
  **DÉRIVE GOLDEN attendue & saine** : `cout_defense < 1` partout où une plante a
  accumulé ombre/sécheresse (expression > 1) → croissance/cicatrisation plus lentes,
  localisé, monotone, borné (plancher 0.5). `population_hash` re-figé pour la même
  cause (le monde macro dépend des plantes). **Garde-fou P6 (anti-sélection) OK** :
  1 gène saturé = −4,5 % croissance, 5 saturés = −22,5 % (> plancher), pendant que
  l'acclimatation divise les dégâts par ~1.3 → le gain de survie domine le coût,
  pas d'anti-sélection. Test `test_cout_defense` (neutre=1.0, sur-expression ronge
  monotone, désexpression gratuite, plancher tenu). Suites ciblées vertes
  (genetique, vigueur, stress_chronique, eau, croissance, population re-figé) ;
  `dotnet build` vert.
- **④ priming transgénérationnel — CLOS (golden re-figé `f3635a1d…`→`2ab026ad…`).**
  Knob `PRIMING_FRAC=0.4` (genetics.py). Helper `child_expression(mother)` =
  `{g: 1 + PRIMING_FRAC×(mother.expression[g]−1)}` sur les seuls `ADAPTOGENIC_GENES`
  (reproduction.py, à côté de `child_genes` mais ORTHOGONAL : génotype ≠ expression).
  **DÉCISION ACTÉE (Nico : « l'expression voyage avec la graine ») :** porté par la
  banque-sol, PAS recalculé à la germination. `add_species(…, expression=None)`
  agrège l'expression héritée en MOYENNE pondérée densité (réutilise `GeneStat`,
  variance ignorée — un état d'alerte n'est pas un tirage) ; `sample_expression()`
  la relit DÉTERMINISTE (la moyenne, sans bruit gaussien) à la germination →
  `new_plant.expression.update(…)` aux 2 sites féraux (`succession`/`spring_flush`).
  Recrutement DIRECT des pérennes (mère vivante, `mortalite.py`) : priming posé
  directement depuis `parent`. Vieillissement de l'expression aligné sur celui des
  gènes (`tick_species_aging`).
  **DÉRIVE GOLDEN attendue & vérifiée** : sonde du scénario → 11 records de banque-sol
  portent une expression primée >1 (BursaPastoris/Yarrow… `tolerance_ombre`/
  `resistance_pathogene` ~1.03-1.06), transmise aux semis féraux → `expressed_gene`
  adoucit dégâts + `cout_defense` ralentit → attrs digérés (health/stade) dérivent.
  L'expression elle-même reste HORS `_PLANT_ATTRS` (comme ②③). **Oubli émergent
  PROUVÉ** (pas de compteur) : `PRIMING_FRAC<1` atténue à chaque transmission +
  l'enfant sans stress désacclimate (TAU_DOWN). `population_hash` INCHANGÉ. Test
  `test_priming_transgenerationnel` (math mère→enfant, round-trip banque, oubli
  émergent). Suites ciblées vertes ; `dotnet build` vert (aucun schéma de pont).
- **④bis canal JOUEUR (tous les canaux de graine) — CLOS, golden NEUTRE `2ab026ad…`.**
  Décision Nico : « on le câble — valide pour TOUS les cas de reproduction (récolte,
  autonome, mangé par un oiseau…) ». Invariant posé : *toute graine = un descendant
  portant `child_expression(mère)`*. Câblé sur les canaux CONCRETS : `Seed` gagne un
  champ `expression` (sérialisé save, OMIS si neutre → save lisible) ; pont récolte
  auto `boucle.py` dépose `child_expression(plant)` filtré non-neutre dans la
  banque-joueur ; `planter` copie `seed.expression` → `GrainEnAttente.expression` ;
  `_lever_grains_en_attente` l'applique à la levée (`new_plant.expression.update`).
  Une attaque atténue UNE fois (au pont récolte) ; `planter`/germination ne font que
  RECOPIER (pas de double atténuation). Pas de zoochorie concrète codée aujourd'hui
  (la « dispersion oiseaux » de `seedbank.py` est un trickle abstrait d'archétypes,
  sans mère) → tout canal FUTUR héritera de l'invariant. **Golden NEUTRE** (pas de
  `player_seed_bank` ni de grains au golden → canal inerte). Test
  `test_priming_canal_joueur` (récolte→Seed→sérialisation→planter→germination
  pré-armée). `test_planter` 18/18, genetique/competition/vigueur/stress verts.
