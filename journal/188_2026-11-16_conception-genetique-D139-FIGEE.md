# 2026-11-16 — Conception D139 FIGÉE : génétique réaliste, niche thermique, caractères vivants

`/conception` lancée sur D139 (F5 du 2026-11-16 : basilic vert en plein hiver, « la
génétique a trop peu d'impact »).

## Diagnostic du basilic (lecture du code)
- `_winter_transition` tue les annuelles aux semaines 49-52 : depuis le calendrier unique,
  c'est mi-février – mi-mars.
- Le gel (`_mediated_damage`) ne frappe que le stade `semis`.
- Aucun dégât de froid sans gel (seulement la stagnation sous `temp_min_growth`).
- `t_min_nuit_at` est la nuit type : 54 semaines de gel en 8 ans [seed 42, sol nu], T_air
  hebdo ≤ 24,9 °C [8 ans, seed 42].

## Décisions de Nico
- **Le moteur ne tue pas, la plante meurt** quand ses conditions de mort sont atteintes : fin
  de la mort calendaire, sénescence de fin de cycle propre à la plante, pas de filet arbitraire.
- Nuit la plus froide + jour le plus chaud (40 °C cet été en Normandie), signes visibles par
  paliers de température.
- Génétique repensée sur le réel : **modèle infinitésimal** (option B de l'étude
  `docs/vegetal/genetique/etude_genetique_realiste.md`).
- Multiplier les gènes autant qu'il faut (≈ 0,1 % de tick par gène [smoke, cProfile]).
- 20 caractères vivants (fleurs avec couleurs inspirées du réel et guides à nectar,
  toxicité par organe, gestes, sol) ; 15 propositions d'ajout de Nico passées au code :
  7 retenues, 8 écartées (doublons ou mécanique absente).

## Livrables
- Docs : `etude_genetique_realiste.md`, `conception_genetique_infinitesimale.md`,
  `conception_niche_thermique.md` (tableau des niches des 52 espèces),
  `conception_caracteres_vivants.md` (tous sous `docs/vegetal/genetique/`).
- Sprints (sous `sprints/vegetal/genetique/`) : `sprint_genetique_infinitesimale` (4
  tronçons) → `sprint_niche_thermique` (5) → `sprint_caracteres_vivants` (6).
