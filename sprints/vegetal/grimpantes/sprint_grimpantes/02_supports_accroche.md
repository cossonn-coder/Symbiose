# ② — Structures-support posables + mur + recherche d'accroche + grimpe

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + CE fichier. Conception :
> `docs/vegetal/grimpantes/conception_grimpantes.md` §4. **Golden NEUTRE vs ①.** Repose
> sur ① (traits + loi d'apex). Lancement depuis `data/code/`.

## Objectif
Créer les supports (structure posable NEUVE + mur maison), la **recherche
d'accroche bornée** (perf), et le **biais de grimpe** : une grimpante libre
au-dessus de sa `hauteur_autoportante` qui trouve un support compatible s'y
accroche et **monte** le long de son axe.

## Fichiers
- `world/support.py` (NEUF) : dataclass `Support` — `type` ∈
  {`"tuteur"`,`"treillis"`,`"pergola"`}, `x_cm`, `y_cm`, `height_cm`, `finesse`
  (`"fin"`/`"surface"`). Rattachée à la tuile (`Tile.supports: list[Support]`,
  champ neuf dans `world/tile.py`, défaut `[]`). Patron des bac/pile posables.
- `world/support.py` : table de **compatibilité** `mode_grimpe × support` (helper
  pur `support_compatible(mode, support_type_ou_mur) -> bool`) :
  - `crampon` → tout (mur, tuteur, treillis, pergola) ;
  - `vrille_volubile` → tout SAUF **mur nu** ;
  - `sarmenteux` → RIEN automatiquement (accroche seulement via `palisser`, ④).
- `world/__init__.py` : ré-exporter `Support`.
- `sim/growth/phases.py` (ou un `sim/grimpe.py` NEUF si plus propre, couche `sim`) :
  `chercher_support(plant, tile, house)` — appelé dans le tick de croissance,
  **uniquement** pour grimpante libre (`support is None`) au-dessus de
  `hauteur_autoportante`. Cherche dans un **rayon borné** (plot-foyer + 8 voisins,
  ~50 cm) : les `Support` de la tuile + le **mur maison** (si un bord de la maison
  passe dans le rayon, cf. `house.footprint_bounds`). Retient le compatible **le
  plus proche**, départage **déterministe** (distance puis `id` — ZÉRO RNG).
  Pose `plant.support = (ref, height_appui)`.
- `sim/growth/geometrie.py` : compléter la loi d'apex ① pour le cas **accroché** :
  `support is not None` → plancher de verticalité **renforcé** (biais fort vers le
  haut, l'axe du support) tant que `max_z < min(height_appui, capacité_propre)`.
  → la structure monte, `max_z` grimpe jusqu'au sommet du support.

## Perf (réflexe D32)
- `chercher_support` NE tourne que pour les grimpantes libres au-dessus du seuil
  (état `support` persistant → une accrochée n'est plus scannée). Rayon borné,
  déterministe. ~quelques centaines de tests/tick max vs ~160 k ops du LightField.
- Élaguer, ne pas balayer toute la tuile.

## Golden
**NEUTRE vs ①** (même hash que celui re-figé au ①). Raison : le golden ne pose
AUCUN `Support`, et son unique grimpante (`Bean` = `vrille_volubile`) **ne peut
pas s'accrocher au mur nu** (compatibilité refuse). Donc aucune accroche ne se
déclenche → croissance identique à ①.
1. `python3 -m tests.test_golden` → **inchangé** vs hash ①.
2. S'il bouge : soit `chercher_support` accroche le haricot au mur (compatibilité
   `vrille_volubile`×mur mal codée), soit il tourne pour une non-grimpante →
   corriger, ne PAS re-figer.

## Ce qu'il NE faut PAS faire
- Pas de plante-hôte vivante ici (c'est ③) : `chercher_support` ne regarde que
  structures + mur.
- Pas de gestes joueur ici (pose = ④) : le banc/tests posent les `Support`
  directement.
- Pas de rendu (⑥).

## F5
- (au ⑥) un haricot près d'un tuteur doit grimper droit ; loin de tout, s'affaler.
