# 2026-11-18 — Sprint GÉNÉTIQUE INFINITÉSIMALE (D139, sprint ① sur 3) — CLOS côté code

Tronçons ①→④ faits (`sprints/vegetal/genetique/sprint_genetique_infinitesimale/`).

## Ce qui change
- ① Registre des caractères (`plants/caracteres.py`) : unité, neutre par espèce, σ_A, bornes.
- ② Hérédité infinitésimale : brassage ½σ_A²(1−F̄), consanguinité F par plante, gène
  `autofecondation`, variétés, F qui voyage avec la graine. Golden re-figé `07122393…`.
- ③ Gènes en °C et semaines (`sim/tempo.py`), compromis précocité ↔ taille, tri thermique
  à la levée férale. Golden re-figé `3927690e…`.
- ④ Vue : pont 0.6.17 (`F` par plante, table `caracteres` des unités), survol G en unités
  avec la lignée (fixée / en voie / mélangée), voix « lignée » (encyclopédie, carnet au
  ressemis d'une graine récoltée, palier du concept), banc F5 `lignees`. Golden INTACT.

## Constats
- Banc (b) du ③ : la tomate se fixe (F 0,98 en 6 générations, variance de hauteur ÷30),
  la courgette reste mêlée. Cible (a) ≥ +1 °C de réponse à la sélection NON tenue :
  reportée à `sprint_niche_thermique`.
- Banc `lignees` : l'herbivorie tuait les 24 pieds avant la fin du warmup → garde
  `sans_herbivorie` (D127).

## Suite
F5 de Nico (recette dans `00_etat.md`), puis `sprint_niche_thermique`.
