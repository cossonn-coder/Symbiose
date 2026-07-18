# SYMBIOSE — tools/jardinier_auto/tutelle.py
# QUI l'automate prend-il en charge ? (§3, Q3 tranché). La tutelle vise les plantes
# CULTIVÉES (semées par le joueur/scénario). Le moteur ne porte AUCUN attribut
# `cultive` sur `PlantInstance` : la distinction cultivé/féral vit dans la détection
# de maîtrise comme un ENSEMBLE DE ZONES `(tile_id, r, c)` (`replante`), alimenté par
# `planter`/succession (`sim.maitrise_detection.marquer_replante`). On s'y RABAT
# plutôt que d'inventer un champ (le kickoff ② l'interdit).
#
# Lecture du set `replante` : le moteur n'expose qu'un accesseur privé
# `_detection`. On le lit ICI (couche tools AU-DESSUS de sim → import légitime),
# derrière une façade — si le moteur publie un jour un getter public, un seul point
# à changer. AUCUNE écriture moteur : `zones_cultivees` est pure lecture.

from __future__ import annotations

from sim import maitrise_detection as MD


def zones_cultivees(game_state: dict, player: str) -> set:
    """L'ensemble des zones `(tile_id, r, c)` déclarées CULTIVÉES par le joueur.
    Copie défensive (le set moteur ne doit pas fuiter/être muté par l'automate)."""
    return set(MD._detection(game_state, player)["replante"])


def sous_tutelle(plant, tile_id: str, cultivees: set) -> bool:
    """La plante est-elle une CULTIVÉE vivante prise en charge ? Vraie ssi elle est
    vivante ET son plot-foyer est dans le set `cultivees`. Une férale (zone hors
    set) n'est JAMAIS soignée — elle peut seulement être la CIBLE d'un désherbage
    (§4). Si `cultivees` est vide (aucune zone déclarée), personne n'est sous
    tutelle : c'est au banc/serveur de déclarer le jardin (`marquer_jardin_cultive`)."""
    if not plant.is_alive:
        return False
    r, c = plant.position
    return (tile_id, r, c) in cultivees


def est_ferale(plant, tile_id: str, cultivees: set) -> bool:
    """Symétrique : une plante vivante dont le plot-foyer n'est PAS cultivé. Sert au
    diagnostic de concurrence férale et au désherbage (§4)."""
    if not plant.is_alive:
        return False
    r, c = plant.position
    return (tile_id, r, c) not in cultivees


def marquer_jardin_cultive(engine, player: str) -> int:
    """DÉCLARE toutes les plantes vivantes courantes comme cultivées (setup de banc
    /serveur, HORS TICK). Au montage d'un monde `full`, les plantes initiales sont
    les SECTORS plantées — le jardin du joueur ; les férales n'arrivent qu'ensuite
    par succession et resteront hors du set. Déterministe (itération sur listes).
    Renvoie le nombre de zones marquées. Réservé aux appelants (banc, sim_server) —
    l'automate lui-même ne marque jamais."""
    gs = engine.game_state
    n = 0
    for tile in engine.tiles:
        for plant in tile.plants:
            if plant.is_alive:
                r, c = plant.position
                MD.marquer_replante(gs, player, tile.tile_id, r, c)
                n += 1
    return n
