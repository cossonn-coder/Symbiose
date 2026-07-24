"""
SYMBIOSE — plants/species (paquet)
Espèces concrètes (niveau 3) : 4 adventices archétypes de succession + plantes
cultivées + compagnes attire-auxiliaires.

Éclaté en paquet au Sprint refactor global (SS④, 2026-06-15) ; l'ancien
`plants/species.py` (654 l) devient ce paquet. L'API publique est ré-exportée
ici → tous les imports existants (`from plants.species import Tomato, …` et le
ré-export en bloc de `plants/__init__.py`) marchent sans changement.

Orientation :
  - `adventices.py`   — 4 archétypes de succession (pioneer/N₂/grass/competitor)
  - `cultivees.py`    — légumes du potager (Solanacées, Légumineuses, Astéracées…)
  - `compagnes.py`    — attire-auxiliaires + mellifères + engrais verts (Achillée,
                        Phacélie, Bourrache, Consoude, Moutarde)
  - `aromatiques.py`  — Lamiacées aromatiques persistantes/evergreen (Thym, Lavande)
                        + Menthe (rhizome envahissant, luxuriance ④)
  - `potageres.py`    — potagères lot 2 à familles NEUVES (Carotte/Apiaceae,
                        Courgette/Cucurbitaceae, Mâche/Caprifoliaceae) + Fraisier
                        (Rosaceae, couvre-sol stolonifère, luxuriance ④)
  - `sauvages.py`     — spontanées non-archétypes (Ortie/Urticaceae,
                        Myrtille/Ericaceae acidophile) + trio clonal luxuriance ⑤
                        (Framboisier/Rosaceae drageon, Bambou traçant/Poaceae
                        rhizome, Violette odorante/Violaceae stolon d'ombre)
  - `grimpantes.py`   — grimpantes à familles NEUVES (Lierre/Araliaceae crampon,
                        Jasmin/Oleaceae sarmenteux — sprint Grimpantes ⑤)
  - `mulch_sources.py`— sources de mulch annuelles (Blé/Poaceae, Chanvre/Cannabaceae
                        NEUVE) → paille (sprint équilibre invasion ⑤)
"""

from .adventices import BursaPastoris, MedicagoLupulina, PoaAnnua, Taraxacum, Molene
from .cultivees import Tomato, Pepper, Bean, Clover, Sunflower, Basil
from .compagnes import Yarrow, Phacelia, Borage, Comfrey, Mustard, Garlic
from .aromatiques import Thyme, Lavender, Mint
from .potageres import Carrot, Zucchini, CornSalad, Strawberry
from .sauvages import (Nettle, Vaccinium, Raspberry, RunningBamboo, SweetViolet,
                       Mugwort, Sphagnum, Drosera)
from .grimpantes import Ivy, Jasmine
from .mulch_sources import Wheat, Hemp, Rye

__all__ = [
    "BursaPastoris", "MedicagoLupulina", "PoaAnnua", "Taraxacum", "Molene",
    "Tomato", "Pepper", "Bean", "Clover", "Sunflower", "Basil",
    "Yarrow", "Phacelia", "Borage", "Comfrey", "Mustard", "Garlic",
    "Thyme", "Lavender", "Mint",
    "Carrot", "Zucchini", "CornSalad", "Strawberry", "Nettle", "Vaccinium",
    "Raspberry", "RunningBamboo", "SweetViolet", "Mugwort", "Sphagnum", "Drosera",
    "Ivy", "Jasmine",
    "Wheat", "Hemp", "Rye",
]
