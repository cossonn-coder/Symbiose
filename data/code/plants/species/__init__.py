"""
SYMBIOSE — plants/species (paquet)
Espèces concrètes (niveau 3) : 4 adventices archétypes de succession + plantes
cultivées + compagnes attire-auxiliaires.

Éclaté en paquet au Sprint refactor global (SS④, 2026-06-15) ; l'ancien
`plants/species.py` (654 l) devient ce paquet. L'API publique est ré-exportée
ici → tous les imports existants (`from plants.species import Tomato, …` et le
ré-export en bloc de `plants/__init__.py`) marchent sans changement.

Orientation :
  - `adventices.py` — 4 archétypes de succession (pioneer/N₂/grass/competitor)
  - `cultivees.py`  — légumes du potager (Solanacées, Légumineuses, Astéracées…)
  - `compagnes.py`  — attire-auxiliaires (Achillée, Phacélie)
"""

from .adventices import BursaPastoris, MedicagoLupulina, PoaAnnua, Taraxacum
from .cultivees import Tomato, Pepper, Bean, Clover, Sunflower, Basil
from .compagnes import Yarrow, Phacelia

__all__ = [
    "BursaPastoris", "MedicagoLupulina", "PoaAnnua", "Taraxacum",
    "Tomato", "Pepper", "Bean", "Clover", "Sunflower", "Basil",
    "Yarrow", "Phacelia",
]
