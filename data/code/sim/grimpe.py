"""
SYMBIOSE — sim/grimpe.py
Recherche d'accroche des plantes grimpantes (D49 volet A, CONCEPTION_GRIMPANTES
§4). Couche `sim` (importe `world` : Support/mur + compatibilité). Appelée par
l'engine JUSTE AVANT la croissance : une grimpante LIBRE, plus haute que sa
`hauteur_autoportante`, cherche dans un rayon BORNÉ un support compatible et s'y
accroche. L'accroche est un ÉTAT PERSISTANT (`plant.support`) → une accrochée
n'est plus jamais scannée (réflexe perf D32 : on élague, on ne balaie pas).

Supports possibles : structures posées (tuteur/treillis/pergola, ②), mur maison
(②) et — tronçon ③ — une PLANTE-HÔTE VIVANTE voisine plus haute. L'hôte vivant
est le SEUL support mouvant : sa hauteur d'appui est RELUE chaque tick (l'hôte
grandit → la grimpante suit) et l'accroche se DÉTACHE quand l'hôte meurt ou quitte
la tuile. L'ÉTRANGLEMENT (la grimpante finit par ombrager l'hôte quand elle le
dépasse) n'est PAS codé ici : il ÉMERGE du `LightField` (canopée haute → ombre
projetée sur l'hôte plus bas), philo #2 (flux → contrainte → réponse), zéro malus.

Déterministe, ZÉRO RNG (philo #3) : départage distance PUIS identité stable.
Le biais de grimpe lui-même (relèvement du plancher d'apex quand accroché) vit
dans `sim/growth/geometrie.py` (`_apex_z_floor`), déjà en place depuis ①.
"""

from __future__ import annotations
import math

from constants import PLOT_CM
from world import support_compatible, MUR, HOTE

# Rayon de recherche d'accroche : plot-foyer + son voisinage immédiat (§4, ~50 cm).
# 1.5 plot couvre le foyer et déborde sur les plots adjacents où un support proche
# peut être posé. Placeholder de calibrage (maquette ⑥).
RAYON_ACCROCHE_CM = 1.5 * PLOT_CM


def _mur_appui(plant, house, tile_origin) -> tuple | None:
    """Point d'appui du MUR maison le plus proche de la plante, s'il tombe dans le
    rayon d'accroche. Renvoie `(dist_cm, height_cm, x_world, y_world)` ou None.
    La plante est en repère TUILE-local ; on la projette en repère MONDE (offset
    `tile_origin`) pour la comparer à `house.footprint_bounds` (repère monde). Le
    point d'appui = le point du RECTANGLE-empreinte le plus proche (clamp)."""
    if house is None:
        return None
    ox, oy = tile_origin
    px, py = plant.x_cm + ox, plant.y_cm + oy
    x0, y0, x1, y1 = house.footprint_bounds
    cx = min(max(px, x0), x1)                        # point du rectangle le plus proche
    cy = min(max(py, y0), y1)
    d = math.hypot(px - cx, py - cy)
    if d > RAYON_ACCROCHE_CM:
        return None
    return (d, house.height_cm, cx, cy)


def _est_hote(ref) -> bool:
    """Vrai si la référence d'accroche est une PLANTE-HÔTE vivante (③) plutôt qu'un
    `Support` inerte ou une sentinelle `MUR`/`HOTE`. Duck-typing : seule une
    `PlantInstance` porte `is_alive`/`current_height` (les supports posés n'en ont
    pas). Aucun import de `PlantInstance` ici (couche `sim` n'importe pas `plants`
    pour ça — on reste sur l'attribut)."""
    return hasattr(ref, "is_alive") and hasattr(ref, "current_height")


def _maj_ou_detache_hote(plant, tile) -> bool:
    """Entretien de l'accroche à un hôte VIVANT, appelé AVANT le filtre perf. Si
    `plant.support` référence une plante :
      • hôte mort ou disparu de la tuile → DÉTACHE (`support = None`) : la grimpante
        redevient libre et retombe (①) ou re-cherche au tick suivant ;
      • hôte encore vivant → RELIT sa hauteur (`height_appui = hote.current_height`)
        pour que la grimpante suive sa croissance.
    Renvoie True si l'accroche a été détachée (l'appelant doit alors laisser le scan
    reprendre). No-op (False) pour tout support non-hôte (structure/mur, figé)."""
    sup = plant.support
    if sup is None or not _est_hote(sup[0]):
        return False
    hote = sup[0]
    if (not hote.is_alive) or (hote not in tile.plants):
        plant.support = None
        return True
    plant.support = (hote, hote.current_height)     # suit la croissance de l'hôte
    return False


def _hote_candidats(plant, tile, mode) -> list:
    """Voisines VIVANTES plus hautes que la hauteur autoportante de `plant`, dans le
    rayon d'accroche, compatibles comme hôtes. Renvoie des tuples de candidats au
    même format que `chercher_support` : (distance, clé_stable, ref, height_appui).
    Clé stable = `id(other)` (déterministe intra-tick, départage sans RNG à distance
    strictement égale). L'hôte lui-même est exclu (`other is not plant`)."""
    out: list[tuple] = []
    if not support_compatible(mode, HOTE):
        return out
    hp = plant.plant_class.hauteur_autoportante
    for other in tile.plants:
        if other is plant or not other.is_alive:
            continue
        h = other.current_height
        if h <= hp:                                 # pas assez haute pour porter
            continue
        d = math.hypot(plant.x_cm - other.x_cm, plant.y_cm - other.y_cm)
        if d <= RAYON_ACCROCHE_CM:
            out.append((d, id(other), other, h))
    return out


def chercher_support(plant, tile, house=None) -> None:
    """Tente d'accrocher `plant` à un support proche (structures de la tuile + mur
    maison). No-op sauf pour une grimpante LIBRE au-dessus de sa hauteur
    autoportante — le seul cas qui coûte un scan (borné). Pose
    `plant.support = (ref, height_appui)` sur le compatible le PLUS PROCHE
    (départage déterministe : distance, puis identité stable — zéro RNG).

    `ref` = l'objet `Support` accroché, ou la sentinelle `MUR` pour le mur maison.
    `height_appui` = hauteur d'appui offerte (cm) : le plancher d'apex renforcé
    (`_apex_z_floor`) fera monter la structure jusque-là."""
    cls = plant.plant_class
    mode = cls.mode_grimpe
    hp = cls.hauteur_autoportante
    # Entretien de l'accroche à un hôte VIVANT (③) AVANT le filtre perf : relit sa
    # hauteur (l'hôte grandit) ou détache si l'hôte est mort/parti (→ scan repris).
    # No-op pour un support inerte (structure/mur) et pour toute non-grimpante.
    if mode is not None and hp is not None:
        _maj_ou_detache_hote(plant, tile)
    # Filtre perf : seules les grimpantes LIBRES et déjà trop hautes pour se tenir
    # seules cherchent un appui. Tout le reste (non-grimpantes, accrochées, encore
    # courtes) sort immédiatement → aucun scan.
    if mode is None or hp is None or plant.support is not None:
        return
    max_z = max((s.base[2] + s.dir[2] * s.length_cm for s in plant.segments),
                default=0.0)
    if max_z <= hp:
        return

    # Candidats compatibles dans le rayon : (distance, clé_stable, ref, height).
    # La clé_stable départage à distance égale sans RNG (index de pose du support ;
    # -1 pour le mur, prioritaire à distance strictement égale — cas de bord).
    candidats: list[tuple] = []
    for i, sup in enumerate(tile.supports):
        if not support_compatible(mode, sup.support_type):
            continue
        d = math.hypot(plant.x_cm - sup.x_cm, plant.y_cm - sup.y_cm)
        if d <= RAYON_ACCROCHE_CM:
            candidats.append((d, i, sup, sup.height_cm))

    # Plantes-hôtes VIVANTES voisines (③) : mêmes tuples (distance, id, ref, height).
    # La hauteur d'appui = la hauteur COURANTE de l'hôte, relue ensuite chaque tick
    # par `_maj_ou_detache_hote` tant que l'accroche tient.
    candidats.extend(_hote_candidats(plant, tile, mode))

    # Mur maison : comparé en repère MONDE (on passe l'offset de la tuile). Ajouté
    # aux candidats avec la clé stable -1 (prioritaire au départage strictement
    # égal, cas de bord).
    if support_compatible(mode, MUR):
        mur = _mur_appui(plant, house, (tile.origin_x_cm, tile.origin_y_cm))
        if mur is not None:
            d, h, _, _ = mur
            candidats.append((d, -1, MUR, h))

    if not candidats:
        return
    # Le plus proche ; départage déterministe par la clé stable (distance, clé).
    d, _, ref, height_appui = min(candidats, key=lambda t: (t[0], t[1]))
    plant.support = (ref, height_appui)
