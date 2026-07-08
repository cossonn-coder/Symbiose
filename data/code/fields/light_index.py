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


class ReceiverIndex:
    """Buckets de plots (pas = PLOT_CM) indexant les ÉCHANTILLONS de lumière
    reçue par leur cellule. Miroir de `ObstacleIndex` mais côté RÉCEPTEUR : c'est
    le SCATTER de la boucle reçue (chaque émetteur ne visite que la bbox de sa
    capsule au lieu que chaque échantillon parcoure tous les émetteurs).

    Chaque échantillon stocké = `(ph, ref, sx, sy)` :
      • `ph`  = hauteur du récepteur (pour le test d'auto-ombrage `qh > ph`) ;
      • `ref` = clé du récepteur (identité de la plante réceptrice) ;
      • `(sx, sy)` = position continue de l'échantillon dans le repère tuile.

    BIT-IDENTITÉ : l'index ne fait qu'ÉLAGUER des couples (émetteur, échantillon)
    dont l'échantillon est hors de la bbox de la capsule → `_point_in_capsule`
    renvoyait déjà False (facteur neutre). En itérant les émetteurs dans l'ORDRE
    EXACT de `order` (hauteur décroissante) et en n'appliquant `att *= (1-qd)`
    qu'aux échantillons réellement couverts, le produit flottant accumule les
    mêmes facteurs dans le même ordre par échantillon → résultat inchangé.
    """

    def __init__(self, samples: list, cell_cm: float = PLOT_CM):
        self.cell = cell_cm
        self._buckets: dict[tuple[int, int], list[tuple]] = {}
        for s in samples:
            _ph, _ref, sx, sy = s
            cx = int(sx // cell_cm)
            cy = int(sy // cell_cm)
            self._buckets.setdefault((cx, cy), []).append(s)

    def in_bbox(self, xmin: float, xmax: float,
                ymin: float, ymax: float) -> list[tuple]:
        """Échantillons dont la cellule tombe dans la bbox [xmin,xmax]×[ymin,ymax].

        Sur-ensemble strict : on scanne les cellules de la bbox et on renvoie tous
        les échantillons qui y logent. Un échantillon dont la cellule est hors bbox
        est forcément hors de la capsule → l'élaguer est neutre (il renvoyait
        `_point_in_capsule == False`)."""
        c_lo = int(xmin // self.cell)
        c_hi = int(xmax // self.cell)
        r_lo = int(ymin // self.cell)
        r_hi = int(ymax // self.cell)
        out: list[tuple] = []
        buckets = self._buckets
        for cx in range(c_lo, c_hi + 1):
            for cy in range(r_lo, r_hi + 1):
                b = buckets.get((cx, cy))
                if b is not None:
                    out.extend(b)
        return out
