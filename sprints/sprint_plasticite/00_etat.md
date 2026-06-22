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
| ③ | coût croissance/défense (vigueur) | re-figeage annoncé | à faire |
| ④ | priming transgénérationnel (`child_genes`) | re-figeage annoncé | à faire |
| ⑤ | signe d'acclimatation (sémiologie + vue C#) + dette | NEUTRE (lecture) | à faire |

## Golden
- Départ : `3f86bf5310712c6b73e3f74840aa1367d53ea8ad3ca86d21af4bb7fcdafbd29c`
  (post « mort par stress chronique » voie ombre).
- Après ① : `f503dc15f07800869edb3132a301f8fb0f5a8515e966efe85a7d4401929dcd82`.
- Après ② : `0549fc35728753d85ba5a0d523e697b9e5757ec02d87a82aca376bb0de1333ca`.
- Pont actuel : **0.5.2** (inchangé au ① et au ② — aucun schéma de pont touché).

## REPRISE
② CLOS. Reprendre par `03_cout.md` (coût croissance/défense : la sur-expression
re-route la vigueur dans `vigueur_plante.py` → le compromis émerge, re-figeage).

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
