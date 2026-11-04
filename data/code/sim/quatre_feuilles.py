"""
SYMBIOSE — sim/quatre_feuilles.py
Le trèfle à quatre feuilles (sprint TRÈFLE DOMINANT ③) : quelques pieds rares le
portent, et le récolter récompense le JOUEUR, une fois par pied.

📖 Pourquoi une fonction pure et pas un champ posé à la naissance : le statut se déduit
de l'identité du pied, comme un `form_seed`. Rien n'est écrit dans le tick, aucun RNG
vivant (philo #3), et les plantes déjà vivantes n'ont rien à migrer. Le seul état neuf
est `plant.quatre_feuilles_cueilli`, posé par le geste de récolte.

Le hash mêle `form_seed` ET position : les ramets héritent du `form_seed` de leur mère
(`sim/clonal.py`). Sur le `form_seed` seul, toute la colonie aurait quatre feuilles.

Le bonus va au joueur, jamais à la plante (philo #2). Le pied reste un trèfle ordinaire
pour le moteur. Le golden tourne sans geste : ce module n'y est jamais appelé.

COUCHE : au niveau `sim`, hors tick (comme `journal`, `pages`, `vigueur`). `engine` ne
l'importe pas ; seuls le geste `recolter`, l'automate et le pont l'appellent.
"""
from __future__ import annotations

from fields.noise import _hash_noise
from plants import Clover
from sim import journal, pages
from sim.vigueur import gain, vigueur_max
from sim.vigueur_plante import maturite

# Probabilité qu'un pied adulte porte quatre feuilles. Calibrée par la mesure pour 1 à 3
# pieds à la fois sur le jardin `full` en an 3, cf. mesures/apres_quatre_feuilles.md du
# sprint. Bien plus fréquent que dans un vrai pré : un joueur doit pouvoir en trouver un.
PROBA_QUATRE_FEUILLES = 0.005

# Canal de hash réservé, pour ne pas corréler le statut avec les autres tirages du pied.
_SALT_QUATRE_FEUILLES = 0x4F011

KIND_QUATRE_FEUILLES = "quatre_feuilles"   # marqueur du ledger, lu par `sim/carnet.py`


def est_quatre_feuilles(plant, seed: int) -> bool:
    """Ce pied porte-t-il quatre feuilles, cueillables ? Vrai seulement pour un trèfle
    adulte, vivant, pas encore cueilli. PURE : ne dépend que de l'identité du pied.
    Position au centième de cm : deux ramets d'une même colonie ne se confondent pas."""
    if (plant.plant_class is not Clover or not plant.is_alive
            or plant.quatre_feuilles_cueilli or maturite(plant) < 1.0):
        return False
    u = _hash_noise(seed ^ plant.form_seed, _SALT_QUATRE_FEUILLES,
                    round(plant.x_cm * 100), round(plant.y_cm * 100))
    return u < PROBA_QUATRE_FEUILLES


def cueillir(game_state: dict, player: str, plant, eco) -> bool:
    """Si `plant` porte quatre feuilles : Vigueur pleine, prochaine page secrète due,
    note au carnet, pied marqué. Renvoie True ssi la récompense a été versée, donc une
    seule fois par pied. Appelé par `recolter`, hors tick."""
    if not est_quatre_feuilles(plant, game_state.get("seed", 0)):
        return False
    plant.quatre_feuilles_cueilli = True
    gain(game_state, player, vigueur_max(game_state, player))   # `gain` plafonne au max
    pages.reveler_page(game_state, player, robinet="récompense")   # sans concept : la 1ʳᵉ due
    r, c = plant.position
    journal._appender(journal.ensure_player(game_state, player), {
        "semaine": game_state["week"], "zone": (eco.tile_id, r, c),
        "kind": KIND_QUATRE_FEUILLES, "cause": None, "espece": "trefle"})
    return True
