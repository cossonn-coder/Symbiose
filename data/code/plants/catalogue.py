"""
SYMBIOSE — plants/catalogue.py
Catalogues d'espèces : cultivées + adventices (succession) + pérennes ligneuses.
"""

from __future__ import annotations
from plants.species import (Tomato, Pepper, Bean, Clover, Sunflower, Basil,
                            Yarrow, Phacelia, Borage, Comfrey, Mustard,
                            Thyme, Lavender, Mint,
                            Carrot, Zucchini, CornSalad, Strawberry, Nettle,
                            Vaccinium, Garlic,
                            Ivy, Jasmine,
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
    # Menthe (Lamiacée) — rhizome envahissant (sprint LUXURIANCE ④, absorbe D62)
    "menthe":    Mint,
    # Mellifères / engrais verts compagnons
    "bourrache": Borage,
    "consoude":  Comfrey,
    "moutarde":  Mustard,
    # Potagères lot 2 — familles botaniques neuves (Apiaceae, Cucurbitaceae, Caprifoliaceae)
    "carotte":   Carrot,
    "courgette": Zucchini,
    "mache":     CornSalad,
    # Fraisier (Rosaceae) — couvre-sol stolonifère (sprint LUXURIANCE ④, absorbe D62)
    "fraisier":  Strawberry,
    # Spontanée non-archétype (Urticaceae) + compagne répulsive bisannuelle (Amaryllidaceae)
    "ortie":     Nettle,
    "ail":       Garlic,
    # Sous-arbrisseau acidophile (Ericaceae) — démonstrateur fenêtre pH ⑤
    "myrtille":  Vaccinium,
    # Grimpantes à familles neuves (sprint Grimpantes ⑤) — Lierre (Araliaceae,
    # crampon, monte au mur nu) + Jasmin (Oleaceae, sarmenteux, se palisse)
    "lierre":    Ivy,
    "jasmin":    Jasmine,
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
