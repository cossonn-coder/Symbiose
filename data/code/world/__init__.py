"""
SYMBIOSE — paquet world/
Ré-export de l'API publique (les sites d'appel font `from world import Tile`).
"""

from world.tile import RONDELLE_TYPES, StakeSlot, Tile
from world.building import House
from world.substrat import SUBSTRATS, SubstratRecette, get_substrat
from world.container import Container, make_container, planter_dans
