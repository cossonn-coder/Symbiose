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
  - `potageres.py`    — potagères lot 2 à familles NEUVES (Carotte/Apiaceae,
                        Courgette/Cucurbitaceae, Mâche/Caprifoliaceae)
  - `sauvages.py`     — spontanées non-archétypes (Ortie/Urticaceae,
                        Myrtille/Ericaceae acidophile)
"""

from .adventices import BursaPastoris, MedicagoLupulina, PoaAnnua, Taraxacum
from .cultivees import Tomato, Pepper, Bean, Clover, Sunflower, Basil
from .compagnes import Yarrow, Phacelia, Borage, Comfrey, Mustard, Garlic
from .aromatiques import Thyme, Lavender
from .potageres import Carrot, Zucchini, CornSalad
from .sauvages import Nettle, Vaccinium

__all__ = [
    "BursaPastoris", "MedicagoLupulina", "PoaAnnua", "Taraxacum",
    "Tomato", "Pepper", "Bean", "Clover", "Sunflower", "Basil",
    "Yarrow", "Phacelia", "Borage", "Comfrey", "Mustard", "Garlic",
    "Thyme", "Lavender",
    "Carrot", "Zucchini", "CornSalad", "Nettle", "Vaccinium",
]
