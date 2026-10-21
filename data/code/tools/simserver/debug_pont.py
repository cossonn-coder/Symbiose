"""
SYMBIOSE — tools/simserver/debug_pont.py
Raccourcis DEBUG du pont (retour F5 voix narratives, demande Nico). Permettent de
tester l'AFFICHAGE des voix sans jouer jusqu'à la maîtrise réelle. Étiquetés
« debug » côté vue (touches F8/F9/F10).

GARDE-FOU DE COUCHE : comme tout le pont, ces helpers vivent AU-DESSUS du tick,
opt-in joueur — `engine`/`fields`/`plants` ne les importent JAMAIS. Le golden
tourne le moteur SANS serveur → jamais appelés → golden intact. Ils écrivent
DIRECTEMENT l'état de maîtrise (bypass de la progression monotone § normal) : c'est
assumé, c'est du debug, jamais un chemin de jeu.
"""
from __future__ import annotations

from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE
from sim import maitrise as M
from sim import maitrise_detection as MD
from sim import pages
from sim.actions import observer
from sim.pages_corpus import PAGES
from sim.signes_corpus import SIGNES
from fields.faune_encyclo import FAUNE_ENCYCLO
from sim.champignon_encyclo import CLE_CHAMPIGNON

from .maitrise_pont import _CLE_DE_CLASSE, _CONCEPT_REPRO_BIPARENTAL

PALIER_DEBUG = 3   # « maîtrise » — le seuil qui ouvre magazine + pages + interprétatif

# Concepts transversaux connus : stagnations canoniques ∪ pollinisation ∪ concepts
# portés par le corpus de pages (pour révéler leurs pages au forçage). Dérivé, non
# dupliqué.
_CONCEPTS = (set(MD.CONCEPT_PAR_STAGNATION.values())
             | {_CONCEPT_REPRO_BIPARENTAL}
             | {PAGES[pid]["concept"] for pid in PAGES}
             | {s["concept"] for s in SIGNES.values()})   # PLANTE ASSEMBLÉE ⑥


def forcer_palier_3(game_state: dict, player: str) -> int:
    """DEBUG : crédite le palier 3 sur toutes les espèces du catalogue + les
    concepts transversaux, et révèle une page « récompense » par concept. Débloque
    d'un coup magazine (offres), carnet interprétatif et pages. Renvoie le nombre
    d'objets crédités."""
    st = M.ensure_player_maitrise(game_state, player)
    # + la faune nommée (⑥) : son nom se révèle au même seuil (info-bulle ⑦) ;
    # + le champignon (INFO-BULLE DU VIVANT ③ : même règle de nom, sinon 3 automnes).
    objets = (set(PLANT_CATALOGUE) | set(PERENNIAL_CATALOGUE) | _CONCEPTS
              | set(FAUNE_ENCYCLO) | {CLE_CHAMPIGNON})
    for objet in objets:
        st["objets"][objet] = {"palier": PALIER_DEBUG, "preuves": 0}
    for concept in _CONCEPTS:
        pages.reveler_page(game_state, player, robinet="récompense",
                           contexte={"concept": concept})
    return len(objets)


def reset_maitrise(game_state: dict, player: str) -> None:
    """DEBUG : remet la maîtrise ET les pages du joueur à zéro (état muet des voix
    depuis le début). Annule `forcer_palier_3`."""
    game_state.setdefault("maitrise", {})[player] = {"objets": {}}
    game_state.setdefault("pages", {})[player] = set()


def observer_toutes_presentes(game_state: dict, player: str) -> int:
    """DEBUG : découvre d'un coup toutes les espèces VIVANTES du terrain (l'ancien
    comportement automatique, désormais à la demande) — pour remplir l'encyclopédie
    sans survoler chaque plante. Renvoie le nombre de nouvelles découvertes."""
    n = 0
    for tile in game_state.get("tiles", []):
        for p in tile.plants:
            if not p.is_alive:
                continue
            cle = _CLE_DE_CLASSE.get(p.plant_class)
            if cle and observer(game_state, player, cle):
                n += 1
    return n
