# Tronçon ③ — Banc d'observation + vue Godot

> Kickoff autosuffisant. Lis `CLAUDE.md` (racine) + `00_etat.md` (ce dossier) +
> `docs/conception/CONCEPTION_MODELE_SPATIAL.md` (§0, §3), puis exécute.
> Tests depuis `data/code/`. **Tronçons ① et ② faits** (placement sous-plot/pixel
> + `form_seed` héritable).

## Objectif
Rendre les deux acquis OBSERVABLES en F5, sans toucher au moteur. Le pont
sérialise DÉJÀ `x_cm,y_cm` + `segments` par plante (`tools/simserver/serialize.py:101-105`)
et le rendu place par `WorldView.WorldToScreen` → les changements remontent tout
seuls. Ce tronçon = un **banc d'observation** déterministe + une **checklist F5**.

## Principe (NE PAS dévier)
- **Aucune mécanique nouvelle**, aucun changement `data/code/` moteur. Un banc ne
  fait que COMPOSER l'état existant (cf. `bancs/base.py`). → **golden NEUTRE**.
- Couche : `bancs/` est au niveau `main.py` (peut tout importer) ; les couches
  basses ne l'importent jamais.
- Déterministe (philo #3) : positions/espèces fixées en dur, seed fixe.

## A. Le banc
Fichier `bancs/modele_spatial.py` (nouveau), sur le patron des bancs existants
(`bancs/luxuriance.py` est le plus proche : plantes posées, ramets). Composer une
tuile où l'on VOIT les deux phénomènes :
1. **Air de famille clonal** : une mère clonale mature (ex. trèfle/fraisier —
   `clonal_mode != "none"`, cf. catalogue) + laisser tourner quelques saisons pour
   qu'elle émette des ramets (`sim.clonal.emettre_ramets` via la boucle) ; les
   ramets doivent afficher un patron de branches proche de la mère.
2. **Pas de superposition** : poser 2-3 plantes au MÊME plot mais à des positions
   sous-plot distinctes (écrire `x_cm,y_cm` explicites à quelques cm d'écart) →
   elles se chevauchent sans se confondre.
3. **Pixel cliqué** : optionnel — un `planter` scripté à un pixel précis pour
   montrer la levée pile à l'endroit.
Enregistrer le banc dans le registre des bancs (regarde comment `cmd_init` /
`bancs/__init__.py` expose les bancs et ajoute `modele_spatial` de la même façon).

## B. Vérifs automatiques (dans le banc ou un test léger)
- deux ramets d'une même mère ont le MÊME `form_seed` (assert) ;
- deux plantes au même plot ont des `(x_cm,y_cm)` distincts (assert) ;
- `python3 -m tests.test_golden` : **INCHANGÉ** (le banc n'est pas branché sur le
  smoke). Si le golden bouge, tu as touché un chemin partagé → corrige.

## C. Checklist F5 pour Nico (à écrire dans `00_etat.md`)
Lister les commandes exactes pour lancer le banc et ce qu'il doit observer :
- les plantes ne sont plus alignées au centre de la grille ;
- les ramets ressemblent à leur mère (même port), plus jeunes ;
- deux plantes au même plot ne se superposent plus ;
- (si fait) la plante plantée apparaît au pixel cliqué.

## NE PAS faire
- Ne pas modifier le pont ni le moteur (tout est déjà porté).
- Ne pas re-figer le golden (il doit rester INTACT).
- Ne pas créer d'assets Godot (placeholders procéduraux existants suffisent).

## Fin de tronçon (clôture du sprint)
Mets à jour `00_etat.md` (checklist F5 + golden final = celui du tronçon ②) et
`journal.md` (entrée de clôture), commit. Sprint clos, F5 côté Nico.
