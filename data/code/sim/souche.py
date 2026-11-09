"""
SYMBIOSE — sim/souche.py
Rejets de souche à la mort d'un arbre (sprint frein_rejets_figuier ②, D130).
Spec : `docs/vegetal/regeneration/conception_rejets_de_souche.md` §3.2-3.5.

Ce que fait la nature : quand un arbre perd sa partie aérienne, les bourgeons
dormants de sa souche partent, nourris par les réserves des racines. Les rejets
sortent AU PIED, sans avoir besoin de lumière au départ (la réserve les porte) ;
ensuite la compétition pour la lumière trie, comme pour un semis.

Ici, une passe par tick sur la tuile :
  • cible = un arbre MORT (`morte`) dont la souche a été jugée vivante à la mort
    (`souche_vivante`, figé par `sim.effects.deposer_mort` via le critère pur
    `sim.effects.perturbations.souche_vivante`) et pas encore traitée ;
  • en saison de végétation seulement (même test que la dormance clonale ①) : un
    arbre mort en hiver rejette à la 1ʳᵉ semaine de printemps ;
  • N = round(`rejet_souche` × N_REJETS_MAX), borné 0..4 — un taillis réel en fait
    des dizaines qui s'éclaircissent ; on ne simule que ceux qui comptent (cap perf) ;
  • chaque rejet est un CLONE (gènes, expression, form_seed copiés, comme un ramet
    de `sim/clonal.py`) posé dans un disque de RAYON_REJET_CM autour du mort ;
  • une seule vague par mort (`souche_traitee`).

Pourquoi le squelette suffit à porter la souche : un arbre mort reste dans
`tile.plants` tant qu'il lui reste du bois (`engine._tick_skeletons`, fragmentation
géométrique FRAG_RATE 0,04 × vitesse locale → des années avant d'atteindre ~0),
bien plus que l'hiver le plus long. Les mortes « non marquées » retirées par le
filet de `_tick_skeletons` (jamais passées par `deposer_mort`) ne rejettent pas :
acceptable, c'est un chemin de secours.

Philo : #2 aucune prime à la plante — c'est la perte qui déclenche une réponse
biologique ; #3 déterministe, zéro RNG (`_hash_noise`). Canaux utilisés ici :
week·67 (+k) pour l'angle, week·71 (+k) pour la distance — distincts de ceux de
`sim/clonal.py` (week·31 angle, week·37 distance, week·41 cadence).
Couches : `sim` lit `plants` (traits) et `fields` (bruit) ; câblé dans `sim/engine`.
"""
from __future__ import annotations

import math

from calendrier import saison_de, wiy_de
from constants import PLOT_CM
from fields import _hash_noise
from sim.capacite import recrutement_bloque

# Rayon du disque où partent les rejets autour de la souche [ordre de grandeur] :
# les bourgeons dormants sont sur le collet et les grosses racines superficielles.
RAYON_REJET_CM = 60.0
# Plafond de rejets par vague (cap perf, cf. §3.5) ; N = round(rejet_souche × max).
N_REJETS_MAX = 4


def nombre_rejets(cls) -> int:
    """Rejets d'une vague pour l'espèce `cls` : ∝ sa capacité, borné 0..N_REJETS_MAX."""
    n = round(getattr(cls, "rejet_souche", 0.0) * N_REJETS_MAX)
    return max(0, min(N_REJETS_MAX, n))


def _offset(souche, seed: int, week: int, k: int) -> tuple:
    """Offset (dx, dy) du k-ième rejet, déterministe. Distance en sqrt(u) → répartition
    surfacique uniforme dans le disque (miroir de `clonal._offset_hashe`)."""
    r, c = souche.position
    angle = _hash_noise(seed, week * 67 + k, r, c) * 2.0 * math.pi
    dist = RAYON_REJET_CM * math.sqrt(_hash_noise(seed, week * 71 + k, r, c))
    return math.cos(angle) * dist, math.sin(angle) * dist


def emettre_rejets_souche(tile, seed: int, week: int) -> list[str]:
    """Vague de rejets de chaque souche vivante non traitée de la tuile. Renvoie une
    ligne de log par vague (format stable, lu au ④ par le ledger des voix). Emoji 🌳
    et non 🌱 : `sim/evenements` lit toute ligne 🌱 comme une avance de stade
    (`_RE_AVANCE`) → elle produirait une germination fantôme ; 🌳 y est ignoré."""
    log = []
    if saison_de(wiy_de(week)) == "hiver":
        return log
    for souche in list(tile.plants):
        if not (souche.morte and souche.souche_vivante and not souche.souche_traitee):
            continue
        # Cap perf : tuile saturée → on attend (la souche reste « à traiter »).
        if recrutement_bloque(tile):
            return log
        souche.souche_traitee = True
        cls = souche.plant_class
        poses = []
        for k in range(nombre_rejets(cls)):
            dx, dy = _offset(souche, seed, week, k)
            tx, ty = souche.x_cm + dx, souche.y_cm + dy
            tr, tc = int(math.floor(ty / PLOT_CM)), int(math.floor(tx / PLOT_CM))
            # Pas de gate de lumière : la réserve racinaire porte le rejet.
            rejet = tile.add_plant(cls, tr, tc)      # None si plot invalide
            if rejet is None:
                continue
            rejet.genes = dict(souche.genes)
            rejet.expression.update(souche.expression)
            rejet.form_seed = souche.form_seed
            rejet.x_cm, rejet.y_cm = tx, ty
            poses.append((tr, tc))
        if poses:
            log.append(f"    🌳 Rejet de souche : {cls.name} @{poses[0]} ×{len(poses)} "
                       f"[souche de @{souche.position}]")
    return log
