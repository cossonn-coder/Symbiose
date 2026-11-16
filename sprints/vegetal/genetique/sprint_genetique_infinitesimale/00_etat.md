# Sprint GÉNÉTIQUE INFINITÉSIMALE — état (D139, sprint ① sur 3)

> Conception figée le 2026-11-16 : `docs/vegetal/genetique/conception_genetique_infinitesimale.md`
> (à lire en entier). Étude : `docs/vegetal/genetique/etude_genetique_realiste.md`.
> Suite : `sprint_niche_thermique` (②), puis `sprint_caracteres_vivants` (③), même dossier parent.

## But
Des gènes en vraies unités, une diversité qui vient du brassage, des lignées qui se fixent
(autogames) ou se mélangent (allogames), et des gènes qui coûtent.

## Décisions clés (Nico, 2026-11-16)
- G1 Modèle infinitésimal (option B de l'étude). G2 Brassage = ½σ_A²(1−F̄), mutation = filet.
- G3 Consanguinité F par plante. G4 `autofecondation` = gène (taux par plante).
- G5 Compromis : dépression de consanguinité (allogames) + précocité ↔ taille.
- G6 Multiplier les gènes autant qu'il faut (≈ 0,1 % de tick par gène [smoke, cProfile]).
- Ajout de gènes **en queue** seulement (canaux de hash positionnels).

## Golden
Départ `b4a921f8…` (`data/code/tests/golden_hash.txt`). ① INTACT · ② **RE-FIGÉ LARGE
annoncé** (toutes les valeurs de gènes changent) · ③ **RE-FIGÉ annoncé** (unités +
compromis) · ④ INTACT. Chaque re-figeage : dérive expliquée et consignée ici avec le hash.

## Tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_registre.md` — registre des caractères, neutre par caractère, bornes | **FAIT** 2026-11-16, golden INTACT `b4a921f8…` |
| ② | `02_heredite.md` — brassage, F, autofécondation, fondateurs, variétés, banque | à faire |
| ③ | `03_unites_compromis.md` — °C et semaines, compromis, banc « réponse à la sélection » | à faire |
| ④ | `04_vue.md` — pont (unités + F), survol G, voix « lignée », banc F5 `lignees` | à faire |

## Notes ①
- Registre = `plants/caracteres.py` (pur, sans import interne) : `Caractere` (unite, neutre,
  sigma_a, bornes, adaptogene), table `CARACTERES` ordonnée, helpers `parametres_espece`
  (helper UNIQUE neutre/σ_A effectifs), `neutre`, `sigma_a`, `borne`. Ré-exportés par
  `plants.genetics` et `plants`. `GENE_NAMES = tuple(CARACTERES)` ; `GENE_INIT_SIGMA` et
  `GENE_HARD_MIN/MAX` dérivés du registre.
- `PlantBase.genetique = {}` (familles.py). `PlantInstance.gene()` : absent → `neutre(nom,
  plant_class)`. ⚠ un nom hors registre lève désormais `KeyError` (avant : 1.0) — tous les
  appelants actuels lisent des noms de `GENE_NAMES` (vérifié au grep).
- `borne(nom, x)` remplace `clamp_gene` dans `child_genes`, `founder_genes`,
  `sample_genes`, `expressed_gene`. `clamp_gene` reste exporté (bancs, tests).
- `GeneStat` des gènes (banque-sol + `seed_founder_pool`) part de `neutre(g, espèce)`.
  Non fait au ① (laissé au ②) : `founder_genes`/`seed_founder_pool` tirent encore autour
  de 1.0 avec `GENE_INIT_SIGMA` global (pas encore le σ_A d'espèce).
- Test neuf `tests/test_caracteres.py` (30/30). Suites génétique/plasticité/diversité/greffe vertes.

## REPRISE
Lire `CLAUDE.md`, ce fichier, puis le kickoff du premier tronçon « à faire » (②).
