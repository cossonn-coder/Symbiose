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
| ② | branchement `expressed_gene` chez tous les consommateurs | re-figeage annoncé | à faire |
| ③ | coût croissance/défense (vigueur) | re-figeage annoncé | à faire |
| ④ | priming transgénérationnel (`child_genes`) | re-figeage annoncé | à faire |
| ⑤ | signe d'acclimatation (sémiologie + vue C#) + dette | NEUTRE (lecture) | à faire |

## Golden
- Départ : `3f86bf5310712c6b73e3f74840aa1367d53ea8ad3ca86d21af4bb7fcdafbd29c`
  (post « mort par stress chronique » voie ombre).
- Après ① : `f503dc15f07800869edb3132a301f8fb0f5a8515e966efe85a7d4401929dcd82`.
- Pont actuel : **0.5.2** (inchangé au ①).

## REPRISE
① CLOS. Reprendre par `02_branchement.md` (brancher `expressed_gene` chez les
consommateurs → acclimatation ACTIVE, re-figeage comportemental cette fois).

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
