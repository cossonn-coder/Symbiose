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
| ① | `01_temperatures_extremes.md` — nuit la plus froide, jour le plus chaud, T_feuille | à faire |
| ② | `02_niche_caracteres.md` — niches des 52 espèces, 3 caractères, plasticité, coût | à faire |
| ③ | `03_reponse_mort.md` — dégâts gradués, fin de la mort calendaire, fin de cycle | à faire |
| ④ | `04_signes.md` — posture thermique et marques, voix | à faire |
| ⑤ | `05_vue.md` — postures et teintes, banc `niche_thermique`, recette F5 | à faire |

## REPRISE
Lire `CLAUDE.md`, ce fichier, puis le kickoff du premier tronçon « à faire ».
