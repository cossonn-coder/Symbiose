# Sprint NICHE THERMIQUE — état (D139, sprint ② sur 3)

> Conception figée le 2026-11-16 : `docs/vegetal/genetique/conception_niche_thermique.md`
> (à lire en entier). **Prérequis** : `sprint_genetique_infinitesimale` CLOS (registre des
> caractères, unités en °C, F). Suite : `sprint_caracteres_vivants`.

## But
Le basilic meurt du froid d'automne, la mâche passe l'hiver, la canicule grille la plante
assoiffée au soleil, et chaque lignée porte sa plage vivable en °C, qui dérive de
génération en génération.

## Diagnostic d'origine (vérifié au code le 2026-11-16, détail §1 de la conception)
Mort calendaire aux semaines 49-52 (mi-février) · gel limité au stade `semis` · aucun dégât
de froid sans gel · nuit type au lieu de la plus froide (≈ 7 semaines de gel/an [seed 42,
sol nu]) et T_air hebdo ≤ 24,9 °C [8 ans, seed 42].

## Décisions clés (Nico, 2026-11-16)
- T1 **Le moteur ne tue pas, la plante meurt** : plus de mort calendaire ; sénescence de fin
  de cycle propre à la plante ; pas de filet de vieillesse arbitraire.
- T2 Nuit la plus froide + jour le plus chaud ; T_feuille = soleil × soif.
- T3 Plage d'espèce + 3 caractères en °C (`rusticite_froid` refondu, `limite_froid`,
  `limite_chaud`) + endurcissement et acclimatation en °C.
- T4 Signes par paliers (froid → confort → chaud), sans chiffre. T5 Gel sur tous les stades.

## Golden
Départ = hash de fin du sprint ①. ① **RE-FIGÉ annoncé** (nuit la plus froide) · ②
**RE-FIGÉ annoncé** (clés neuves + `rusticite_froid` en °C) · ③ **RE-FIGÉ annoncé, dérive
large** (dates de mort des annuelles) · ④ INTACT · ⑤ INTACT.

## Tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_temperatures_extremes.md` — nuit la plus froide, jour le plus chaud, T_feuille | **FAIT** 2026-11-18 (non commité) |
| ② | `02_niche_caracteres.md` — niches des 52 espèces, 3 caractères, plasticité, coût | à faire |
| ③ | `03_reponse_mort.md` — dégâts gradués, fin de la mort calendaire, fin de cycle | à faire |
| ④ | `04_signes.md` — posture thermique et marques, voix | à faire |
| ⑤ | `05_vue.md` — postures et teintes, banc `niche_thermique`, recette F5 | à faire |

## ① FAIT (2026-11-18)
- `fields/ecofields/thermique.py` : `t_min_nuit_at` = **nuit la plus froide** (nuit type −
  `ECART_NUIT_FROIDE`·(1−couvert)·(1−nébul)) ; ancienne formule gardée en
  `t_min_nuit_type_at` ; `t_max_jour(t_air, nebul)` = T_air + (`AMPLITUDE_DIURNE` +
  `ECART_JOUR_CHAUD`)·(1−nébul). Constantes 3,0 / 7,0 / 5,0 dans `constants.py`.
- Lecteurs : gel (`boucle.py`) et glace (`glace.py`) → nuit la plus froide ; **rosée/givre →
  nuit type** (bilan de toutes les nuits, calibrage D111 conservé).
- `sim/engine/feuille.py` : `t_feuille(plant, eco, t_air, nebul)` + `soif` = stress hydrique
  instantané sur `eau_percue` (pas `drought_memory`, trop lente). Aucun lecteur (③).
- **Écart au kickoff** : `t_max_jour` sans `eco, r, c` (l'air est uniforme ; soleil et soif
  sont dans `t_feuille`). **Garde du gel levé** : `boucle.py` ne gelait que si T_air < 0
  (8 sem./8 ans [seed 42]) → la nuit la plus froide n'aurait rien changé ; chaque plot
  décide maintenant par sa nuit, log seulement si sév > 0.
- Mesures (`mesures/mesure_extremes.py`, seed 42, 8 ans, sol nu sans vent) : nuits < 0 °C
  54 → 113 semaines (6,8 → 14,1/an [n=1 seed]), min −7,8 → −10,6 °C ; jour le plus chaud
  max 35,9 °C (T_air 24,9). Smoke 5,99 → 5,58 s [1 run chacun] ; voie gel ≈ 0,01 s [cProfile].
- Golden **RE-FIGÉ** `3927690e…` → `72896cbd4fa9e596d23cf1c8ccc6101e744d694a0c7983e5c18bfea2fdd2c575` :
  1ʳᵉ divergence = gel des semis en W1 (T_air 7,2 °C, nuit claire) ; 2 → 26 lignes de gel,
  le reste en découle. Suites vertes : temperatures_extremes (neuve, 28/28), meteo_heterogene,
  rosee, mare_vivante, couvertures, senescence, stress_chronique, evergreen, evenements,
  microbiome_clim, signes_legende, humectation, caracteres, genetique, heredite, population.
- F5 : la glace des mares prend plus souvent (lit la nuit la plus froide) — à regarder.

## REPRISE
Lire `CLAUDE.md`, ce fichier, puis le kickoff du premier tronçon « à faire » (②).

## Report du sprint ① (génétique infinitésimale, décision Nico 2026-11-16)
La réponse à la sélection sur `germination_thermique` (banc
`sprint_genetique_infinitesimale/mesures/banc_reponse_selection.py`, cas (a), parcelle
froide 10 ans) est NULLE : +0,02 °C [n=80] vs témoin +0,11 °C [n=96], cible ≥ +1 °C.
Le tri thermique à la levée (`_levee_triee`, `sim/succession.py`) existe déjà ; ce qui manque
est la **pression** : tolérances de levée (7-10 °C) ≫ σ_A 1,5 ; levées près de l'optimum ;
~9 levées/an ; aucun avantage à lever tôt. Ce sprint doit la créer et **re-mesurer avec ce
banc** avant clôture (un tronçon inerte n'est pas un succès).
