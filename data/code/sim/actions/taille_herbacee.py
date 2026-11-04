"""
SYMBIOSE — sim/actions/taille_herbacee.py
Ce que `tailler` et `arracher` rendent au sol pour une espèce SANS SQUELETTE (FORMES DES
PLANTES ⑤, `PlantBase.sans_squelette`). Elle n'a plus de sous-arbre à retirer : la coupe se
compte en hauteur rabattue, celle que la vue dessine (conception §4.4).

Le hint `rabattu` vit ici et le pont le relit, car `sim` ne peut pas importer `tools`.

Ordre de grandeur mesuré avant le retrait (`Σ longueur × BOIS_PAR_CM`, gf 0,7, 26 à 104
semaines) : clic sur un segment, médiane 0,48 à 0,78 et maximum 0,85 à 5,1, identique pour
toutes ces espèces puisque leur squelette ignorait `height_cm` [banc isolé, n=1 pied par
âge]. Après, 0,6 × hauteur : trèfle 0,19, basilic 0,50, tournesol 3,15, chanvre 3,78 [mêmes
pieds]. La masse suit enfin la plante coupée.
"""
from __future__ import annotations

from fields.ecofields import BOIS_PAR_CM
from sim.growth.constantes import THICKNESS_INIT

# Semaines pour que le pied dessiné retrouve sa forme [choix, conception §4.4].
RABATTU_SEMAINES = 8
# Part de la hauteur retirée par une coupe : la vue dessine hauteur × (1 − 0,6 × rabattu).
RABATTU_PART = 0.6


def decroissant(semaine_geste: int, semaine: int, duree: int) -> float:
    """1 la semaine du geste, 0 après `duree` semaines ; 0 si le geste n'a jamais eu lieu."""
    if semaine_geste < 0:
        return 0.0
    return round(max(0.0, 1.0 - (semaine - semaine_geste) / duree), 3)


def deposer_rabattu(game_state: dict, plant, eco) -> float:
    """Dépose en litière `bois` la hauteur qu'une coupe retire ENCORE, et la renvoie.
    À appeler AVANT de noter la nouvelle coupe : on part de la hauteur déjà rabattue. Un
    second clic la même semaine ne dépose donc rien, et un clic 4 semaines plus tard ne rend
    que ce qui a repoussé. Une plante ne redépose jamais plus qu'elle n'a."""
    deja = decroissant(plant.semaine_coupe, game_state.get("week", 0), RABATTU_SEMAINES)
    masse = plant.current_height * RABATTU_PART * (1.0 - deja) * BOIS_PAR_CM
    eco.deposer_litiere(*plant.position, "bois", masse, THICKNESS_INIT)   # no-op si masse ≤ 0
    return masse
