"""
SYMBIOSE — plants/catalogue.py
Catalogues d'espèces : cultivées + adventices (succession) + pérennes ligneuses.
"""

from __future__ import annotations
from plants.species import (Tomato, Pepper, Bean, Clover, Sunflower, Basil,
                            Yarrow, Phacelia, Borage, Comfrey, Mustard,
                            Thyme, Lavender,
                            Carrot, Zucchini, CornSalad, Nettle, Garlic,
                            BursaPastoris, MedicagoLupulina, PoaAnnua, Taraxacum)
from plants.perennials import Fig, AppleTree, CherryTree, WalnutTree, OakTree


PLANT_CATALOGUE: dict[str, type] = {
    # Plantes cultivées
    "tomate":    Tomato,
    "poivron":   Pepper,
    "haricot":   Bean,
    "trefle":    Clover,
    "tournesol": Sunflower,
    "basilic":   Basil,
    "achillee":  Yarrow,
    "phacelie":  Phacelia,
    # Aromatiques persistantes (Lamiacées evergreen)
    "thym":      Thyme,
    "lavande":   Lavender,
    # Mellifères / engrais verts compagnons
    "bourrache": Borage,
    "consoude":  Comfrey,
    "moutarde":  Mustard,
    # Potagères lot 2 — familles botaniques neuves (Apiaceae, Cucurbitaceae, Caprifoliaceae)
    "carotte":   Carrot,
    "courgette": Zucchini,
    "mache":     CornSalad,
    # Spontanée non-archétype (Urticaceae) + compagne répulsive bisannuelle (Amaryllidaceae)
    "ortie":     Nettle,
    "ail":       Garlic,
    # Adventices / succession écologique
    "bourse_pasteur": BursaPastoris,
    "minette":        MedicagoLupulina,
    "paturin":        PoaAnnua,
    "pissenlit":      Taraxacum,
}

# Catalogue des adventices uniquement (pour la succession)
WEED_CATALOGUE: dict[str, type] = {
    "pioneer":        BursaPastoris,
    "nitrogen_fixer": MedicagoLupulina,
    "grass":          PoaAnnua,
    "competitor":     Taraxacum,
}

PERENNIAL_CATALOGUE: dict[str, type] = {
    "figuier":  Fig,
    "pommier":  AppleTree,
    "cerisier": CherryTree,
    "noyer":    WalnutTree,
    "chene":    OakTree,
}
