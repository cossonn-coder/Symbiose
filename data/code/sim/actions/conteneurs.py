"""
SYMBIOSE — sim/actions/conteneurs.py
Gestes JOUEUR sur les CONTENEURS (pots mobiles / bacs immobiles) — couche joueur
du sprint pots/bacs (CONCEPTION_POTS_BACS_SUBSTRATS §4, tronçon ④).

Trois gestes, modelés sur la famille décompo ⑤ (`poser_bac`/`poser_pile`) et sur
la pose de structures :
  - `poser_pot`  : pose un conteneur MOBILE 1×1 rempli d'un substrat (planification,
    coût MODÉRÉ, binaire). `kind="pot"`, `mobile=True`, `fond_ouvert=False`.
  - `poser_bac`  : pose un conteneur IMMOBILE N×M rempli (planification, coût MODÉRÉ,
    binaire). `kind="bac"`, `mobile=False`, `fond_ouvert=True` par défaut (couplé à
    la tuile dessous — son EFFET est branché au ⑤ ; ici on ne fait que le STOCKER).
  - `deplacer_pot` : déplace un pot à une nouvelle position monde. Coût Vigueur AU
    JOUEUR SEUL (effort), MODÉRÉ. **Aucun choc, aucun malus sur la plante** (philo
    #2) : le mini-sol et sa/ses plante(s) voyagent INTACTS. La seule conséquence
    écologique est ÉMERGENTE : à la nouvelle position, l'ombre maison change → la
    lumière reçue est recalculée au prochain `Container.tick_chimie` (`tile_origin`
    suit `x_cm, y_cm`). Refus EN AMONT si la cible n'est pas mobile (un bac ne se
    déplace pas) → aucune Vigueur dépensée (modèle `epandre` jauge vide).

  - `repiquer` (départ du jardin ④, D140 C.5) : sort la plante d'un conteneur et la
    met en pleine terre avec sa motte ; choc de repiquage par le bilan, pas de malus
    (`sim/repiquage.py`). Un pot posé DANS la maison est un semis d'intérieur
    (`world/interieur.py`).

Les conteneurs vivent dans une LISTE au niveau monde `game_state["containers"]`
(défaut `[]` → tick no-op → golden NEUTRE). Ces gestes la PEUPLENT (event-driven,
hors tick) : le smoke n'en pose aucun → golden NEUTRE par construction.

Concept de maîtrise associé = `"jardinage_hors_sol"` (sans état moteur aujourd'hui
→ `M.palier(...) == 0` → atténuation neutre 1.0, comme `"compostage"`). La table le
NOMME pour quand son sprint le câblera.
"""
from __future__ import annotations

from constants import PLOT_CM
from sim.vigueur import spend
from sim.repiquage import couper_racines, ligne_repiquage
from world import Container, make_container
from .couts import cout_action, OBJETS_TOUCHES, _objets_action, _cle_espece


def _containers(game_state: dict) -> list:
    """La liste monde des conteneurs (créée à la volée au 1er usage). Tant
    qu'aucun geste ne la peuple, elle n'existe pas → la boucle 17b lit `[]` →
    no-op strict → golden NEUTRE."""
    return game_state.setdefault("containers", [])


def poser_pot(game_state: dict, player: str, substrat: str, volume_litres: float,
              x_cm: float, y_cm: float, *,
              tile_eco=None, tile_rc=None) -> Container | None:
    """Poser un POT mobile (§4) à la position monde `(x_cm, y_cm)` — phase
    PLANIFICATION, coût MODÉRÉ. Crée un conteneur 1×1 rempli du `substrat` choisi
    (`make_container`) et l'ajoute à la liste monde. Binaire (modèle `poser_bac`
    compost) : posé QUE si le coût est intégralement payé — un geste à vide draine
    la Vigueur sans rien poser.

    `tile_eco`/`tile_rc` ne sont requis que pour le substrat `terre_jardin`
    (hérite_tuile) — ils sont passés tels quels à `make_container` (ValueError franc
    en amont si manquants). Renvoie le `Container` posé, ou None si Vigueur
    insuffisante."""
    cost = cout_action(game_state, player, "poser_pot", OBJETS_TOUCHES["poser_pot"])
    if spend(game_state, player, cost) < 1.0:
        return None
    ctn = make_container("pot", substrat, volume_litres, x_cm, y_cm,
                         tile_eco=tile_eco, tile_rc=tile_rc)
    _containers(game_state).append(ctn)
    return ctn


def poser_bac(game_state: dict, player: str, substrat: str, volume_litres: float,
              x_cm: float, y_cm: float, rows: int = 2, cols: int = 2, *,
              fond_ouvert: bool = True,
              tile_eco=None, tile_rc=None) -> Container | None:
    """Poser un BAC immobile N×M (§4) à `(x_cm, y_cm)` — phase PLANIFICATION, coût
    MODÉRÉ. Symétrique de `poser_pot` (kind=`bac`), mais : grille `rows×cols > 1`
    (volume grand → confinement faible/nul, ③ s'applique tel quel via `volume_norm`),
    `mobile=False` (pas de geste déplacer), `fond_ouvert` STOCKÉ ici (défaut True =
    couplé à la tuile dessous — son EFFET drainage/racines/microbiome est branché au
    ⑤, en ④ il est juste mémorisé). Binaire : posé QUE si le coût est payé.
    Renvoie le `Container` posé, ou None si Vigueur insuffisante."""
    cost = cout_action(game_state, player, "poser_bac_culture",
                       OBJETS_TOUCHES["poser_bac_culture"])
    if spend(game_state, player, cost) < 1.0:
        return None
    ctn = make_container("bac", substrat, volume_litres, x_cm, y_cm,
                         rows=rows, cols=cols, tile_eco=tile_eco, tile_rc=tile_rc)
    ctn.fond_ouvert = fond_ouvert
    _containers(game_state).append(ctn)
    return ctn


def deplacer_pot(game_state: dict, player: str, container: Container,
                 x_cm: float, y_cm: float) -> bool:
    """Déplacer un POT à la position monde `(x_cm, y_cm)` (§4, décision tranchée
    2/6 : Vigueur JOUEUR seule, pas de choc plante). Coût MODÉRÉ.

    Refus EN AMONT si `not container.mobile` (un bac est immobile) — aucune Vigueur
    dépensée (modèle `epandre` jauge vide : on ne paie pas un geste qu'on ne peut pas
    faire). Sinon, geste binaire : la position n'est mise à jour QUE si le coût est
    intégralement payé. **Le mini-sol et la/les plante(s) voyagent INTACTS** : on ne
    touche qu'à `x_cm, y_cm` du conteneur (zéro écriture sur la plante → philo #2). La
    lumière reçue à la nouvelle position (ombre maison) est recalculée au prochain
    `Container.tick_chimie` (`tile_origin=(x_cm, y_cm)`), pas ici — la conséquence
    écologique reste ÉMERGENTE. Renvoie True si déplacé, False sinon."""
    if not container.mobile:
        return False                      # bac immobile → refus, aucune Vigueur
    cost = cout_action(game_state, player, "deplacer_pot",
                       OBJETS_TOUCHES["deplacer_pot"])
    if spend(game_state, player, cost) < 1.0:
        return False                      # Vigueur insuffisante → position intacte
    container.x_cm = x_cm
    container.y_cm = y_cm
    return True


def repiquer(game_state: dict, player: str, container: Container, tile,
             r: int, c: int) -> str | None:
    """Repiquer (D140 C.5, départ du jardin ④) : sortir la plante d'un conteneur et
    la mettre en pleine terre AVEC SA MOTTE, au centre du plot `(r, c)` de `tile`.

    La plante GARDE son identité : même objet (gènes, âge, stade, structure,
    réserves, feuillage, mémoires) ; seule sa position change (collet et segments
    translatés d'un bloc). Le conteneur reste, vidé de cette plante. Le CHOC n'est
    pas un malus : la motte laisse une part du chevelu, plus grande si les racines
    étaient à l'étroit (`Container.serrage`) → la plante ressent un sol plus sec et
    paie la repousse de ses racines sur son bilan (`sim/repiquage.py`).

    Refus EN AMONT, sans Vigueur dépensée : aucune plante vivante dans le conteneur
    ou plot hors de la tuile. Binaire : rien ne bouge si le coût n'est pas payé.
    Renvoie la cause du choc (`motte`/`chignon`), ou None si refusé."""
    plant = next((p for p in container.plants if p.is_alive), None)
    if plant is None or not tile.is_valid_plot(r, c):
        return None
    cost = cout_action(game_state, player, "repiquer", _objets_action("repiquer", plant))
    if spend(game_state, player, cost) < 1.0:
        return None
    serrage = container.serrage(plant)          # lu AVANT de sortir la plante du pot
    x, y = c * PLOT_CM + PLOT_CM / 2, r * PLOT_CM + PLOT_CM / 2
    dx, dy = x - plant.x_cm, y - plant.y_cm
    for seg in plant.segments:                  # la structure suit le collet, d'un bloc
        bx, by, bz = seg.base
        seg.base = (bx + dx, by + dy, bz)
    plant.x_cm, plant.y_cm, plant.position = x, y, (r, c)
    container.plants.remove(plant)
    tile.plants.append(plant)
    cause = couper_racines(plant, serrage)
    # Plant mis en terre par le joueur = CULTIVÉ (comme un semis qui lève,
    # succession.py) — import local, même patron que la succession.
    from sim.maitrise_detection import marquer_replante
    marquer_replante(game_state, player, tile.tile_id, r, c)
    _noter_repiquage(game_state, player, tile.tile_id, r, c, plant, cause)
    return cause


def _noter_repiquage(game_state: dict, player: str, tile_id: str, r: int, c: int,
                     plant, cause: str) -> None:
    """Note du carnet : une ligne dans le canal `log` du serveur (absent hors
    serveur → rien), relue par `sim/evenements`. PREMIÈRE FOIS seulement par joueur
    et par cause (patron `_noter_gout`) : le premier repiquage (`motte`), puis le
    premier choc fort d'une plante à l'étroit (`chignon`)."""
    log = game_state.get("log")
    if log is None:
        return
    deja = game_state.setdefault("repiquages_notes", {}).setdefault(player, [])
    if cause in deja:
        return
    deja.append(cause)
    log.append(ligne_repiquage(tile_id, r, c, _cle_espece(plant) or "plante", cause))
