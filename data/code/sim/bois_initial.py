"""
SYMBIOSE — sim/bois_initial.py
Bois mort de l'ÉTAT INITIAL (D111 ②bis, §D) : un jardin réel n'a jamais un sol
nu de bois. Dès la semaine 0 des mondes de JEU (`full`/`propre`, jamais `smoke`),
on pose de la litière `bois` :
  1. sous la couronne de chaque ligneux déjà en place (branches tombées les années
     passées) ;
  2. quelques PIÈCES isolées par tuile — une souche (grosse) ou une branche —
     placées par hachage de la graine du terrain.
Âges VARIÉS (0 à AGE_MAX semaines) pour que tous les stades de décomposition se
voient à la vue (⑧) ; une pièce plus vieille a déjà perdu une part de sa masse.
Pure fabrique d'init (hors tick) : déterministe, zéro RNG (`_hash_noise`).
"""

from __future__ import annotations

from fields import _hash_noise
from constants import PLOT_CM

# Masses de litière `bois` (même unité que BOIS_MORT_PAR_CM3 ; MYCEL_SUBSTRAT_REF
# = 2,0 sature le substrat d'un plot). Knobs, calibrage F5/③.
SOUS_COURONNE   = (0.15, 0.45)   # par plot sous un ligneux en place (min, max)
PIECES_PAR_TUILE = (2, 4)        # nombre de pièces isolées par tuile (min, max)
SOUCHE          = (1.5, 3.0)     # masse d'une souche
BRANCHE         = (0.4, 1.0)     # masse d'une branche tombée
P_SOUCHE        = 0.35           # part des pièces qui sont des souches
AGE_MAX         = 150            # semaines : la plus vieille pièce (~3 ans au sol)
PERTE_AGE       = 0.5            # part de masse déjà perdue à AGE_MAX


def _entre(bornes: tuple, h: float) -> float:
    return bornes[0] + (bornes[1] - bornes[0]) * h


def _poser(eco, r: int, c: int, masse: float, age: float) -> float:
    """Dépose `masse` de bois d'âge `age` (fusion pondérée par la masse, comme
    `_fusion_parcelle`, mais avec un âge non nul)."""
    masse *= 1.0 - PERTE_AGE * age / AGE_MAX
    if masse <= 0.0:
        return 0.0
    eco.deposer_litiere(r, c, "bois", masse)
    for p in eco.litiere[r][c]:
        if p.tissu == "bois":
            # le dépôt vient d'être fusionné à l'âge 0 : on lui rend son âge
            p.age_sem += age * masse / p.masse
    return masse


def poser_bois_initial(tiles, ecos: dict, seed: int) -> float:
    """Pose le bois mort initial sur toutes les tuiles. Renvoie la masse totale."""
    total = 0.0
    for ti, tile in enumerate(tiles):
        eco = ecos[tile.tile_id]
        # 1. Sous la couronne des ligneux en place.
        for plant in tile.plants:
            cls = plant.plant_class
            if not plant.is_alive or not getattr(cls, "ligneux", False):
                continue
            rayon = max(PLOT_CM, cls.canopy_radius_at(plant))
            r0, r1 = int((plant.y_cm - rayon) // PLOT_CM), int((plant.y_cm + rayon) // PLOT_CM)
            c0, c1 = int((plant.x_cm - rayon) // PLOT_CM), int((plant.x_cm + rayon) // PLOT_CM)
            for r in range(max(0, r0), min(eco.rows - 1, r1) + 1):
                for c in range(max(0, c0), min(eco.cols - 1, c1) + 1):
                    dx = (c + 0.5) * PLOT_CM - plant.x_cm
                    dy = (r + 0.5) * PLOT_CM - plant.y_cm
                    if dx * dx + dy * dy > rayon * rayon:
                        continue
                    m = _entre(SOUS_COURONNE, _hash_noise(seed, ti, r, c))
                    age = AGE_MAX * _hash_noise(seed, ti + 101, r, c)
                    total += _poser(eco, r, c, m, age)
        # 2. Pièces isolées (souche ou branche).
        n = PIECES_PAR_TUILE[0] + int(_hash_noise(seed, ti, 977, 1)
                                      * (PIECES_PAR_TUILE[1] - PIECES_PAR_TUILE[0] + 1))
        for k in range(n):
            r = int(_hash_noise(seed, ti, k, 11) * eco.rows) % eco.rows
            c = int(_hash_noise(seed, ti, k, 12) * eco.cols) % eco.cols
            souche = _hash_noise(seed, ti, k, 13) < P_SOUCHE
            m = _entre(SOUCHE if souche else BRANCHE, _hash_noise(seed, ti, k, 14))
            age = AGE_MAX * _hash_noise(seed, ti, k, 15)
            total += _poser(eco, r, c, m, age)
    return total
