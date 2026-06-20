"""
SYMBIOSE — fields/ecofields/structure.py
Structure / compaction du sol : calcul PUR de la dérive lente du champ
`structure_sol ∈ [0,1]` (1 = grumeleux/aéré, 0 = compacté/battant).

Isolé de `container.py` (le fichier le plus dense du dépôt) sur le modèle de
`ph.py`/`nutriments.py` : le conteneur n'expose qu'une fine méthode `tick_structure`
qui délègue ici. Fonction pure, zéro RNG, zéro log — déterminisme philo #3.

Modèle (tronçon ⑧, CONCEPTION_SOL_STRUCTURE §2.1) — FORCES CONTINUES seulement :

    d_struct[r,c] = + BIOTURB      · lombric_norm[r,c]            (vers, constructeur lent)
                   + RACINE_PIVOT · presence_pivot[r,c]          (racine pivot décompactante)
                   − BATTANCE     · pluie_norm · (1 − couvert)   (pluie battante sur sol NU)
    structure_sol[r,c] += d_struct · STRUCT_INERTIA              (champ lent ; clampe [0,1])

Les GESTES (becher/grelinette) NE passent PAS par ici : ils mutent `structure_sol`
DIRECTEMENT au moment de l'action, à plein effet (cf. `sim/actions/gestes.py`),
comme becher mute déjà microbiome/lombric. tick_structure ne porte donc QUE les
forces qui agissent à chaque tick.

`lombric_norm` = densité du détritivore lombric DIRECTE (`populations["lombric"]`,
max POP_MAX=1.0 → déjà [0,1] ; PAS de /3, qui ne vaut que pour le microbiome de
`decomp_speed` dont l'échelle est [0,3]). `presence_pivot` = 1 si une plante VIVANTE
à racine pivot décompactante (`plant_class.decompactante`) occupe le plot (foyer ou
plot racinaire), 0 sinon. `couvert` = litière protectrice (`om_fresh_at` normalisée
par LITIERE_REF) qui amortit la battance : un sol paillé ne bat pas. `pluie_norm`
∈[0,1] = violence d'impact de l'événement météo du tick (PRECIP_NORM, calculé dans
la boucle ; 0 hors pluie frappante → terme battance nul).
"""

from __future__ import annotations

from .constants import (BIOTURB, RACINE_PIVOT, BATTANCE, STRUCT_INERTIA, LITIERE_REF)


def tick_structure(eco, plants, pluie_norm: float = 0.0) -> None:
    """Met à jour `eco.structure_sol` (dérive lente) depuis la bioturbation des vers,
    la présence de racines pivots décompactantes et la battance de la pluie sur sol
    nu. Pure : n'écrit QUE `structure_sol`. `pluie_norm` ∈[0,1] = PRECIP_NORM de
    l'événement météo du tick (0 hors pluie battante)."""
    # Plots occupés par une racine pivot décompactante VIVANTE (foyer + plots racinaires).
    pivot_plots = set()
    for p in plants:
        if not p.is_alive:
            continue
        if getattr(p.plant_class, "decompactante", False):
            pivot_plots.add(p.position)
            pivot_plots.update(p.root_plots)

    lombric = eco.populations.get("lombric") if eco.populations else None
    struct = eco.structure_sol
    for r in range(eco.rows):
        for c in range(eco.cols):
            lombric_norm = lombric.at_plot(r, c) if lombric else 0.0
            pivot   = 1.0 if (r, c) in pivot_plots else 0.0
            couvert = min(1.0, eco.om_fresh_at(r, c) / LITIERE_REF)
            d = (BIOTURB * lombric_norm
                 + RACINE_PIVOT * pivot
                 - BATTANCE * pluie_norm * (1.0 - couvert))
            struct.set(r, c, struct.data[r][c] + d * STRUCT_INERTIA)  # clampe [0,1]
