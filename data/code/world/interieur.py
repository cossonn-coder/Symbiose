"""
SYMBIOSE — world/interieur.py
Le POT DANS LA MAISON — semis d'intérieur (D140 C.4, sprint DÉPART DU JARDIN ④,
docs/vegetal/genetique/conception_depart_jardin.md §2 C.4).

📖 Pédagogie (Nico) — la maison n'est pas une serre, c'est un MILIEU :
  un pot posé dans l'emprise de la maison est À L'INTÉRIEUR. Il y fait doux jour et
  nuit (pas de gel), il n'y pleut pas (seul le jardinier arrose), et la lumière n'y
  entre que par la fenêtre — une fraction de celle du dehors. Rien n'est un bonus
  (philo #1/#2) : un plant élevé là est à l'abri du froid mais pousse moins vite, et
  une plante de plein soleil y file (étiolement, `sim/growth.est_etiole`, si son
  espèce est héliophile). Choix le plus simple : TOUTE l'emprise de la maison est
  l'intérieur (pas d'emplacement « rebord de fenêtre » dédié).

Appelé par `Container.tick_chimie` à la place de la lumière dehors + T_air.
Zéro RNG (philo #3). Golden NEUTRE : le smoke ne pose aucun conteneur.
"""
from __future__ import annotations

# Température d'une pièce habitée normande au printemps (°C). Le jour on chauffe un
# peu ou le soleil des vitres réchauffe ; la nuit la pièce redescend sans geler.
T_INTERIEUR_JOUR = 20.0
T_INTERIEUR_NUIT = 15.0
# T_air de la SEMAINE (le champ `temperature` d'un mini-sol est une moyenne
# hebdomadaire, comme celui des tuiles) : moyenne du jour et de la nuit.
T_INTERIEUR = (T_INTERIEUR_JOUR + T_INTERIEUR_NUIT) / 2.0
# Part de la lumière du dehors qui atteint un plant derrière une fenêtre : vitre
# (≈ 0,8) × ciel vu seulement d'un côté, à travers l'embrasure (≈ 0,4).
FENETRE = 0.3


def est_interieur(x_cm: float, y_cm: float, house) -> bool:
    """La position monde `(x_cm, y_cm)` est-elle dans l'emprise de la maison ?
    Pas de maison (bancs, tests) → toujours dehors."""
    if house is None:
        return False
    x0, y0, x1, y1 = house.footprint_bounds
    return x0 <= x_cm <= x1 and y0 <= y_cm <= y1


def climat_interieur(eco, plants: list, saison: str, tile_origin: tuple) -> None:
    """Lumière et T_air d'un mini-sol À L'INTÉRIEUR, pour ce tick : la lumière du
    ciel ouvert (la maison ne fait pas d'ombre sur ce qui est dedans) filtrée par la
    fenêtre, puis la température de la pièce. Le microclimat de surface
    (`tick_thermique`) est ensuite calculé par l'appelant comme pour un pot dehors."""
    eco.tick_light(plants, saison, house=None, tile_origin=tile_origin)
    eco.lumiere.filtrer(FENETRE)
    eco.temperature.fill(T_INTERIEUR)
