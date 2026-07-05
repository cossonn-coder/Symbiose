"""
SYMBIOSE — sim/capacite.py
Backstop PUR-PERF de la capacité de charge par tuile (sprint « perf run éternel »,
tronçon ③, arbitrage A « plafond ÉMERGENT + BACKSTOP »).

Ce module NE contient PAS de mécanique de gameplay. La capacité de charge du jeu
est ÉMERGENTE (couverture→germination dans `succession`, self-thinning par
`shade_stress_damage`) — c'est elle qui fait plafonner N à l'équilibre
recrutement=mortalité, propre à chaque tuile (philo #2/#7). Ici on pose seulement
un DISJONCTEUR : un cap dur sur `len(plantes vivantes)` d'une tuile, placé TRÈS
au-dessus du plateau écologique observé, qui ne se déclenche JAMAIS en jeu normal.

S'il fire, c'est le signe d'un déséquilibre pathologique (bug, réglage extrême) :
on bloque tout recrutement (levée, reproduction, ramet) sur cette tuile pour ce
tick et on logge un avertissement debug. Ce n'est PAS une règle visible pour le
joueur — pas un plafond qui « sculpte » la population (cf. §4.3, interdit) : c'est
un filet anti-crash. En régime calibré il ne se lit nulle part → golden neutre.
"""
from __future__ import annotations

# Cap dur par tuile sur le nombre de plantes VIVANTES. PUR-perf, jamais atteint en
# jeu normal : le plateau écologique émergent MESURÉ au tronçon ③ (sweeps 2 tuiles ×
# 14 ans, vis A/B calibrées) s'établit vers ~100-105 plantes pour une tuile 11×11
# (121 plots, quasi-saturée) ; une grande tuile (16 col, jusqu'à 256 plots)
# plafonnerait plus haut, ~150-200. On place le disjoncteur BIEN au-dessus (4-5× le
# plus grand plateau plausible) pour ne mordre QUE sur une divergence pathologique
# (bug, réglage extrême). Vérifié : ne fire JAMAIS dans le smoke golden (2 tuiles ×
# 2 ans, ~42 plantes) — s'il firait, la valeur serait trop basse.
CAP_PERF_TUILE = 800


def recrutement_bloque(tile) -> bool:
    """True si la tuile a atteint le cap dur PUR-perf → on gèle tout recrutement
    (levée férale, grains plantés, reproduction, ramets clonaux) ce tick sur cette
    tuile. Lecture seule (compte les plantes vivantes), déterministe. Renvoie
    False dès qu'une plante meurt et repasse sous le cap → le recrutement reprend
    naturellement au tick suivant (le disjoncteur ne se ré-arme pas, il suit N)."""
    return sum(1 for p in tile.plants if p.is_alive) >= CAP_PERF_TUILE
