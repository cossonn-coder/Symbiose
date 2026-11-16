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
| ① | `01_registre.md` — registre des caractères, neutre par caractère, bornes | à faire |
| ② | `02_heredite.md` — brassage, F, autofécondation, fondateurs, variétés, banque | à faire |
| ③ | `03_unites_compromis.md` — °C et semaines, compromis, banc « réponse à la sélection » | à faire |
| ④ | `04_vue.md` — pont (unités + F), survol G, voix « lignée », banc F5 `lignees` | à faire |

## REPRISE
Lire `CLAUDE.md`, ce fichier, puis le kickoff du premier tronçon « à faire ».
