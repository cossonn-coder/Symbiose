"""
SYMBIOSE — sim/effects/mutations.py
Vocabulaire des MUTATIONS — les ordres élémentaires produits par la résolution
d'effets et consommés par `apply_mutations`.

Aucune mutation ne touche directement « en bonus/malus » une plante : ce sont
des intentions typées (poser/retirer une rondelle, réduire une santé via une
voie écologique, injecter dans un champ, propager une maladie, notifier). Types
PURS (dataclasses), sans logique — isolés ici pour que `resolution.py` et
`perturbations.py` partagent le même vocabulaire. Identique à l'ancien effects.py.
"""

from __future__ import annotations
from dataclasses import dataclass

from plants import PlantInstance


@dataclass
class AddRondelle:
    tile_id: str; variable: str; amount: int; source: str = ""
    def __repr__(self): return f"+{self.amount} {self.variable} [{self.source}]"

@dataclass
class RemoveRondelle:
    tile_id: str; variable: str; amount: int; source: str = ""
    def __repr__(self): return f"-{self.amount} {self.variable} [{self.source}]"

@dataclass
class ReduceHealth:
    # `reason` = chaîne de LOG humaine, jamais stockée. `cause` = enum CANONIQUE
    # de symptôme foliaire ("maladie"/"gel"/"grele", "" = aucune marque) consommé
    # par la sémiologie ② : à la résolution, une cause non vide laisse sur la plante
    # une `symptom_mark` décroissante (cf. resolution.py / sim.semiologie). Les deux
    # champs sont DISTINCTS : reason pour l'humain, cause pour la machine.
    plant: PlantInstance; amount: int; reason: str = ""; cause: str = ""
    def __repr__(self): return f"Santé {self.plant.name}@{self.plant.position} -{self.amount} [{self.reason}]"

@dataclass
class AddScore:
    player_id: str; axis: str; amount: int; source: str = ""
    def __repr__(self): return f"+{self.amount} {self.axis} [{self.source}]"

@dataclass
class InjectField:
    """Injection directe dans un champ continu."""
    tile_id: str; variable: str; amount: float
    row: int | None = None; col: int | None = None
    source: str = ""
    def __repr__(self):
        loc = f"@({self.row},{self.col})" if self.row is not None else "global"
        return f"~{self.amount:+.3f} {self.variable} {loc} [{self.source}]"

@dataclass
class PropagateDisease:
    source_plant: PlantInstance; target_plant: PlantInstance
    disease_name: str = "pathogène"
    probability: float = 1.0
    def __repr__(self):
        return (f"Propagation {self.disease_name} "
                f"{self.source_plant.name}→{self.target_plant.name} "
                f"p={self.probability:.2f}")

@dataclass
class Notification:
    message: str; severity: str = "info"; plant: PlantInstance | None = None
    def __repr__(self): return f"[{self.severity.upper()}] {self.message}"

Mutation = (AddRondelle | RemoveRondelle | ReduceHealth |
            AddScore | InjectField | PropagateDisease | Notification)
