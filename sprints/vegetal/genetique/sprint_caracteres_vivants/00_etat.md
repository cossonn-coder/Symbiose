# Sprint CARACTÈRES VIVANTS — état (D139, sprint ③ sur 3)

> Conception figée le 2026-11-16 : `docs/vegetal/genetique/conception_caracteres_vivants.md`
> (à lire en entier). **Prérequis** : `sprint_genetique_infinitesimale` et
> `sprint_niche_thermique` CLOS (registre, unités, F, `cout_defense` et coût thermique).

## But
20 caractères héritables qui relient la plante aux butineurs, aux fruits mangés, aux
herbivores, aux gestes et au sol, chacun lu par une mécanique existante et chacun payé
d'un compromis.

## Décisions clés (Nico, 2026-11-16)
- Q7 Liste validée + `parfum` + `couleur_fleur` en **dégradé visible**. Couleur inspirée du
  réel : axe de couleur par espèce, préférence par type de butineur, **guides à nectar**
  (piste d'atterrissage) → caractère `guide_nectar`.
- Q8 Toxicité **par organe** (`appetence_feuille`, `appetence_fruit`) : manger un organe
  toxique coûte de la Vigueur (D31) ; certaines plantes ont besoin d'être mangées pour se
  disperser.
- Ajouts de Nico retenus après vérification au code : `dominance_apicale`, `vigueur_clonale`,
  `portee_graine`, `fixation_azote`, `allelopathie`, `mycorhization` (`autofecondation` est
  parti au sprint ①). Écartés : voir conception §2.5.
- Règle : un gène n'entre que si une mécanique le lit ; tout ajout **en queue**.

## Golden
Départ = hash de fin du sprint ②. ①-④ **RE-FIGÉ annoncé** chacun (clés neuves + lecteurs)
· ⑤ INTACT · ⑥ INTACT.

## Tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_fleurs.md` — taille, nectar, pollen, couleur, guides, parfum + `cout_genetique` | à faire |
| ② | `02_fruits_comestibilite.md` — taille des fruits, appétence feuille/fruit, Vigueur négative | à faire |
| ③ | `03_feuille_gestes.md` — coriacité, repousse, bouture, dormance, dominance apicale | à faire |
| ④ | `04_sol_expansion.md` — clonalité, portée, fixation, allélopathie, mycorhization | à faire |
| ⑤ | `05_signes_pont.md` — export des signes visibles, voix | à faire |
| ⑥ | `06_vue_banc.md` — rendu, banc `caracteres_vivants`, recette F5, clôture D139 | à faire |

## REPRISE
Lire `CLAUDE.md`, ce fichier, puis le kickoff du premier tronçon « à faire ».
