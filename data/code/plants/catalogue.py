"""
SYMBIOSE — plants/catalogue.py
Catalogues d'espèces : cultivées + adventices (succession) + pérennes ligneuses.
"""

from __future__ import annotations
from plants.species import (Tomato, Pepper, Bean, Clover, Sunflower, Basil,
                            Yarrow, Phacelia, Borage, Comfrey, Mustard,
                            Thyme, Lavender, Mint,
                            Carrot, Zucchini, CornSalad, Strawberry, Nettle,
                            Vaccinium, Raspberry, RunningBamboo, SweetViolet, Garlic,
                            Ivy, Jasmine, Wheat, Hemp, Rye, Mugwort, Sphagnum, Drosera,
                            BursaPastoris, MedicagoLupulina, PoaAnnua, Taraxacum,
                            Molene)
from plants.perennials import (Fig, AppleTree, CherryTree, WalnutTree, OakTree,
                               FirTree, BeechTree, BirchTree, HornbeamTree, Alder)


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
    # Trio clonal luxuriance ⑤ (absorbe D62) : Framboisier (Rosaceae, drageon →
    # fourré resserré) + Bambou traçant (Poaceae, rhizome envahissant, borné par
    # le gate couverture ①) + Violette odorante (Violaceae NEUVE, stolon d'ombre)
    "framboisier": Raspberry,
    "bambou":      RunningBamboo,
    "violette":    SweetViolet,
    # Grimpantes à familles neuves (sprint Grimpantes ⑤) — Lierre (Araliaceae,
    # crampon, monte au mur nu) + Jasmin (Oleaceae, sarmenteux, se palisse)
    "lierre":    Ivy,
    "jasmin":    Jasmine,
    # Sources de mulch annuelles (sprint équilibre invasion ⑤) — Blé (Poaceae) +
    # Chanvre (Cannabaceae NEUVE), toutes deux → paille à la récolte (④/⑤)
    "ble":       Wheat,
    "chanvre":   Hemp,
    # Émetteurs allélopathiques NEUFS (sprint ALLÉLOPATHIE ⑤) — Armoise (Asteraceae,
    # vivace toxique qui « fait le vide ») + Seigle (Poaceae, engrais vert /
    # couvert nettoyant qui étouffe chimiquement les adventices puis se fauche)
    "armoise":   Mugwort,
    "seigle":    Rye,
    # Ingénieur de tourbière (sprint HYDROLOGIE & MARÉCAGES ⑤) — Sphaigne
    # (Sphagnaceae, mousse) : acidifie + retient l'eau + nécromasse-tourbe.
    "sphaigne":  Sphagnum,
    # Végétal-prédateur de tourbière (sprint HYDROLOGIE & MARÉCAGES ⑥) — Rossolis
    # (Droseraceae, drosera) : puits sur le moustique + azote des proies (échappe
    # à la faim d'azote → prospère sur tourbe acide pauvre).
    "drosera":   Drosera,
    # Adventices / succession écologique
    "bourse_pasteur": BursaPastoris,
    "minette":        MedicagoLupulina,
    "paturin":        PoaAnnua,
    "pissenlit":      Taraxacum,
    # Indicatrice de terre malade (sprint MÉMOIRE D'INOCULUM ③) — Molène / bouillon-
    # blanc (Scrophulariaceae NEUVE) : bisannuelle qui lève sur inoculum élevé (porte
    # `arch_inoculum`), pas par le gradient de succession. Aussi dans WEED_CATALOGUE
    # (archétype `disease_indicator`) ; ici pour ses voix (encyclopédie, magazine, maîtrise).
    "molene":         Molene,
}

# Catalogue des adventices uniquement (pour la succession)
WEED_CATALOGUE: dict[str, type] = {
    "pioneer":        BursaPastoris,
    "nitrogen_fixer": MedicagoLupulina,
    "grass":          PoaAnnua,
    "competitor":     Taraxacum,
    # Archétype HORS gradient de maturité (sprint MÉMOIRE D'INOCULUM ③) : ne germe
    # que via la porte de relâche `arch_inoculum` (inoculum du plot élevé), jamais
    # sur sol sain → golden NEUTRE. Cf. `choisir_archetype` (priorité indicatrice).
    "disease_indicator": Molene,
}

PERENNIAL_CATALOGUE: dict[str, type] = {
    "figuier":  Fig,
    "pommier":  AppleTree,
    "cerisier": CherryTree,
    "noyer":    WalnutTree,
    "chene":    OakTree,
    # Conifère persistant (sprint équilibre invasion ⑤) — aiguilles acidifiantes
    # (récolte) + BRF (broyage) ; ombre projetée toute l'année (non caduc)
    "sapin":    FirTree,
    # Essences forestières normandes (sprint RENDU AMBIANCE T1, D58) — silhouettes
    # du décor (T5) + acquisition future canal #3 (friche). Hors scénario smoke.
    "hetre":    BeechTree,     # Fagaceae, hêtraie cathédrale (ombre dense)
    "bouleau":  BirchTree,     # Betulaceae (famille neuve), pionnier de lisière
    "charme":   HornbeamTree,  # Betulaceae, bocage (tronc cannelé)
    # Hélophyte fixateur d'azote (sprint HYDROLOGIE & MARÉCAGES ⑤) — Aulne
    # (Betulaceae) : arbre des berges, N₂ actinorhizien (Frankia), survit au sol gorgé.
    "aulne":    Alder,
}
