# Tronçon ⑥ — Paillage ↔ vie macro : ABRI pour la faune

**Prérequis** : `CLAUDE.md`, `00_etat.md`, `docs/faune/trophique/conception_equilibre_invasion.md` §5.
Patrons : `fields/population/` (`PopulationField`, `TrophicSpec`, ressources
d'habitat), `fields/ecofields/vie_macro.py`, `sim/vigueur_macro.py`.

## Objectif
Le mulch devient un **habitat/abri** : les guildes ombrophiles (qui n'aiment pas
le plein soleil sans couvert) colonisent les zones paillées. Émergence visible au
F5 (la faune auxiliaire s'abrite sous le mulch).

## Fichiers à toucher
- `fields/population/…` (là où l'habitat/ressource d'une guilde est calculé, cf.
  `resources.py`/`registry.py`) — ajouter au **terme d'habitat** des guildes
  concernées une contribution `+= PAILLAGE_ABRI_W * eco.paillage.at_plot(r,c)`
  (le mulch offre un refuge, surtout là où l'ensoleillement est fort et le couvert
  végétal faible → l'abri COMPENSE l'absence d'ombre). Identifier les guildes
  « ombrophiles » (carabes, vers, détritivores…) via leur `TrophicSpec`.
- Optionnel : `sim/vigueur_macro.py` — la façade de description peut mentionner
  l'abri (lecture seule, philo #5).

## Modèle
Habitat_guilde(r,c) += `PAILLAGE_ABRI_W * paillage(r,c)` (pour les guildes
ombrophiles). Nature du mulch : le BRF (volume) abrite mieux que la paille
(`abri_w` du dict `NATURES_MULCH`, tronçon ④). Déterministe, dans le tick, lit le
paillage de la semaine précédente (décalage uniforme, pas de RNG neuf).

## Golden
**INTACT**. `paillage=0` au repos → habitat inchangé → `test_golden` et surtout
`test_population` (`population_hash`) INCHANGÉS vs post-②. Vérifier explicitement
(c'est un couplage vers les populations : bien confirmer que sans mulch le champ
est bit-identique).

## NE PAS
- Ne pas re-figer `population_hash` (le couplage doit être neutre au repos). Si le
  hash bouge sans mulch → bug, corriger, NE PAS figer. Pas de RNG.

## Vérif / F5
Test : un plot paillé augmente la densité d'habitat des guildes ombrophiles ;
sans mulch, densités inchangées. F5 (⑧) : voir la faune s'agréger sous le mulch
en plein soleil.
