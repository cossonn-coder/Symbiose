# Tronçon ④ — Récompenses matérielles rares

> Sprint QUÊTES (D79). Lire d'abord : `CLAUDE.md`, `00_etat.md`,
> `docs/joueur/automate/conception_quetes.md`, tronçons ①②③ (faits).
> Golden : **INCHANGÉ**.

## Objectif
Ajouter les récompenses **matérielles rares** de V3, réservées à quelques belles
quêtes : une **plante vivace déjà enracinée de plusieurs années**, une
**structure permanente** posée. (« Outil » : voir §Outil ci-dessous.)

## Point de philo (à ne pas rater)
Ces récompenses **ne violent PAS #2** : on ne dope aucune plante existante. On
**fait apparaître** un acteur neuf (une pérenne instanciée à un âge avancé, une
structure posée) — un **cadeau matériel**, comme le voisin qui offre son vieux
pommier. Interdiction ferme du bonus/malus sur une plante déjà en terre.

## À implémenter
1. **Récompense `vivace_enracinee`** : instancier une pérenne du catalogue
   (`plants/perennials.py`) à un **âge/nombre d'années donné**, plantée dans une
   tuile désignée (ou une règle de placement déterministe). Repérer comment une
   `PlantInstance` pérenne porte son âge/nb d'années et comment `planter`
   l'insère ; réutiliser ces chemins, NE PAS forger un état incohérent (le moteur
   doit voir une plante valide, comme si elle avait poussé). Déterministe.
2. **Récompense `structure`** : poser une structure permanente existante
   (bac/pile/… — cf. sprint décomposition/compost, structures posables). Réutiliser
   l'API de pose existante, ne pas en créer une.
3. **§Outil** : il **n'existe pas d'inventaire d'outils** aujourd'hui. Si aucun
   support n'apparaît trivialement → **différer la récompense `outil` en dette**
   (créer/mettre à jour une entrée dette dédiée) et NE PAS l'implémenter ici. Les
   deux récompenses ci-dessus suffisent à démontrer la récompense matérielle rare.
4. Brancher ces types dans l'aiguillage `recompense` de `sim/quetes.py` (posé ③).
5. Ajouter 1-2 lettres du corpus (`quetes_corpus.py`) portant ces récompenses.

## Tests
- Étendre `tests/test_quetes.py` : accomplir une quête `vivace_enracinee` insère
  une pérenne vivante d'âge attendu dans la tuile ; une quête `structure` pose la
  structure ; déterminisme.
- `python3 -m tests.test_golden` → **hash INCHANGÉ** (opt-in ; aucune quête dans
  le golden).

## Ne PAS faire
- Aucun buff sur une plante existante (#2). Pas de vue Godot (⑤).
- Ne pas forger une `PlantInstance` incohérente (âge sans structure de segments
  correspondante, etc.) — passer par les chemins d'instanciation réels.

## Fin de tronçon
Golden inchangé → maj `00_etat.md` → commit.
