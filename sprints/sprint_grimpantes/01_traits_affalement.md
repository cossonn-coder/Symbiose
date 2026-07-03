# ① — Traits grimpante + affalement géométrique SANS support

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + CE fichier. Conception :
> `docs/conception/CONCEPTION_GRIMPANTES.md` §2/§3. **Golden RE-FIGÉ maîtrisé
> ANNONCÉ** (le haricot s'affale). Lancement depuis `data/code/`.

## Objectif
Poser les traits de grimpe et la **loi d'apex** qui fait qu'une grimpante trop
longue pour se tenir seule **retombe** (port affalé émergent). À ce tronçon,
AUCUN support n'existe encore → toute grimpante libre au-dessus de sa
`hauteur_autoportante` s'affale. La hauteur reste `max(z)` honnête (JAMAIS de
clamp — cf. §1.3, consommateurs de `current_height`).

## Fichiers
- `plants/base/familles.py` (`PlantBase`) : 2 nouveaux traits, défauts **inertes** :
  - `hauteur_autoportante: float | None = None` (cm tenus sans appui ; `None` =
    non-grimpante → mécanique inerte).
  - `mode_grimpe: str | None = None` (`None`/`"crampon"`/`"vrille_volubile"`/
    `"sarmenteux"`).
- `plants/base/instance.py` (`PlantInstance`) : état persistant `support = None`
  (l'accroche viendra en ②/③ ; ici toujours `None`). Sérialisé plus tard (⑥ pont).
- `plants/species/cultivees.py` (`Bean`) : `hauteur_autoportante = 35`,
  `mode_grimpe = "vrille_volubile"` (démonstrateur, déjà `procedural_growth`).
- `sim/growth/phases.py` + `sim/growth/geometrie.py` : la **loi d'apex**. Réutilise
  `_phototropic_bias`/`MIN_APEX_Z`. Ajouter un helper pur (ex. `_apex_z_floor(plant,
  height_courante)`) qui remplace le plancher constant `MIN_APEX_Z` par un plancher
  **contextuel** :
  - non-grimpante (`mode_grimpe is None`) → `MIN_APEX_Z` (inchangé) ;
  - grimpante libre (`support is None`) et `max_z ≤ hauteur_autoportante` →
    `MIN_APEX_Z` (elle se tient droite tant qu'elle est courte) ;
  - grimpante libre et `max_z > hauteur_autoportante` → plancher **effondré**
    (z → ~0, biais gravitaire léger vers le bas) → l'apex retombe, les segments
    suivants s'étalent → `max_z` plafonne ~`hauteur_autoportante`, `max_horiz`
    grossit (affalement). Le cas « accroché » viendra en ②.
- `sim/growth/constantes.py` : constante du biais gravitaire d'affalement
  (placeholder calibrage, ex. `DROOP_Z = -0.1`).

## Modèle (formule d'apex)
```
def _apex_z_floor(plant, max_z_courant):
    hp = plant.plant_class.hauteur_autoportante
    if plant.plant_class.mode_grimpe is None or hp is None:
        return MIN_APEX_Z                      # non-grimpante : inchangé
    if plant.support is not None:
        return MIN_APEX_Z                      # accroché (②) : monte — géré en ②
    if max_z_courant <= hp:
        return MIN_APEX_Z                      # courte : se tient droite
    return DROOP_Z                             # trop longue, libre : RETOMBE
```
Injecter ce plancher LÀ où `_phototropic_bias` applique aujourd'hui `MIN_APEX_Z`
(geometrie.py:111-115), en passant la plante + son `max_z` courant. Rester
déterministe (zéro RNG). Ne PAS toucher `height_at` (reste `max(z)`).

## Golden
**RE-FIGÉ MAÎTRISÉ, dérive LOCALISÉE au haricot** : `Bean(4,2)` dépasse 35 cm →
s'affale → canopée basse → `growth_factor`/`shade_memory` changent (et ripple
léger sur ses voisins via `LightField`). C'est ATTENDU et ANNONCÉ.
1. Lancer `python3 -m tests.test_golden` → il ÉCHOUE (hash bouge depuis
   `a6c2f651d4289295474918ad25d060c9c7b27f5e2389f9c7806015ad92118209`).
2. **Vérifier que la dérive est cohérente** : le haricot doit être plus bas/étalé,
   les non-grimpantes strictement INCHANGÉES (comparer un diff du digest — seules
   les lignes du haricot + éventuels voisins immédiats bougent). Si une plante
   non-grimpante bouge → BUG (le plancher fuit), annuler.
3. Re-figer le hash dans `tests/test_golden.py`, noter l'ancien→nouveau dans
   `00_etat.md` §Découpage et le commit.

## Ce qu'il NE faut PAS faire
- Pas de clamp/plafond sur `height_at`/`current_height` (§1.3) — on façonne la
  VRAIE géométrie, la hauteur reste honnête.
- Pas d'accroche ni de support ici (c'est ②/③) : `support` reste toujours `None`.
- Ne pas toucher les non-grimpantes (défauts `None` → zéro effet).

## F5
- (au ⑥) le haricot sans tuteur doit visiblement ramper/s'affaler au sol.
