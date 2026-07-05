"""
SYMBIOSE — fields/light_index.py
Index spatial de la boucle « lumière reçue par plante » (LightField, tronçon ②
du sprint perf run éternel). Coupe le O(N²) : au lieu de faire parcourir à CHAQUE
échantillon TOUS les obstacles plus hauts, on n'itère que ceux dont la capsule
d'ombre PEUT couvrir l'échantillon.

BIT-IDENTITÉ (invariant critique, cf. D32) : l'index ne fait qu'ÉLAGUER des
obstacles qui renvoyaient déjà `_point_in_capsule == False` (facteur (1-qd)=1.0,
neutre). Les candidats retenus sont ré-triés dans l'ORDRE EXACT de `order`
(hauteur décroissante, départages identiques) avant d'appliquer les facteurs →
le produit flottant `att` accumule les mêmes (1-qd) dans le même ordre. Le
résultat est donc strictement inchangé (golden intact).
"""

from __future__ import annotations

from constants import PLOT_CM


class ObstacleIndex:
    """Buckets de plots (pas = PLOT_CM) indexant les obstacles par CENTRE de
    canopée. Chaque obstacle est stocké avec son RANG dans `order` (trié hauteur
    décroissante) pour permettre un ré-tri stable identique après collecte.

    `order` : liste de tuples (plante, x, y, hauteur, rayon, densité) TRIÉE
    hauteur décroissante — exactement la séquence de la boucle d'origine.
    """

    def __init__(self, order: list, cell_cm: float = PLOT_CM):
        self.cell = cell_cm
        self._buckets: dict[tuple[int, int], list[tuple[int, tuple]]] = {}
        # Portée max d'un obstacle = rayon de canopée (marge latérale de la
        # capsule). La longueur d'ombre (hauteur×inv_tan) s'ajoute par tranche.
        self.max_radius = 0.0
        self.max_height = 0.0
        for rank, info in enumerate(order):
            _, x, y, h, radius, _ = info
            cx = int(x // cell_cm)
            cy = int(y // cell_cm)
            self._buckets.setdefault((cx, cy), []).append((rank, info))
            if radius > self.max_radius:
                self.max_radius = radius
            if h > self.max_height:
                self.max_height = h

    def covering(self, sx: float, sy: float, max_length: float) -> list[tuple[int, tuple]]:
        """Candidats (rank, info) dont la capsule POURRAIT couvrir l'échantillon
        (sx, sy) pour une tranche dont la longueur d'ombre max vaut `max_length`.

        Sur-ensemble strict : on prend tous les obstacles dont le CENTRE est dans
        un carré de demi-côté `reach` = max_length + max_radius autour de
        l'échantillon. Un obstacle hors de ce carré a son centre trop loin pour
        que sa capsule (longueur ≤ max_length, rayon ≤ max_radius) atteigne
        l'échantillon → il renvoyait False de toute façon (élagage neutre).

        Retour NON TRIÉ (l'appelant re-trie par rank pour l'ordre bit-identique)."""
        reach = max_length + self.max_radius
        c_lo = int((sx - reach) // self.cell)
        c_hi = int((sx + reach) // self.cell)
        r_lo = int((sy - reach) // self.cell)
        r_hi = int((sy + reach) // self.cell)
        out: list[tuple[int, tuple]] = []
        buckets = self._buckets
        for cx in range(c_lo, c_hi + 1):
            for cy in range(r_lo, r_hi + 1):
                b = buckets.get((cx, cy))
                if b is not None:
                    out.extend(b)
        return out
