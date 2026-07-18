# SYMBIOSE — tools/jardinier_auto/onglet.py
# L'ONGLET d'un objectif (§8) : une PROJECTION en lecture pure du journal (③) et du
# log moteur, filtrée sur un objectif. AUCUNE machinerie neuve — on ne fait que
# relire deux structures déjà écrites :
#   - `game_state["automate_journal"]` : les gestes de l'automate portent `objectif_id`
#     (renseigné par la boucle quand le geste sert un objectif) → filtre direct ;
#   - `game_state["log"]` : les événements du monde, une liste PLATE de lignes ; chaque
#     tick y ouvre un bloc dont la 2ᵉ ligne est un en-tête `S{wiy}/Y{annee}`. On
#     reconstruit la semaine absolue de chaque bloc et on ne garde que ceux de la
#     FENÊTRE active de l'objectif.
#
# DÉCALAGE D'INDICE (assumé, documenté) : le moteur écrit l'en-tête d'un tick avec la
# semaine AVANT incrément (`boucle.py`), puis incrémente `week`. L'automate joue juste
# après → il consigne ses gestes à `engine.week` (APRÈS incrément). Donc un bloc de log
# d'en-tête `header_week` correspond au tick où l'automate a agi à la semaine
# `header_week + 1`. La fenêtre de l'objectif est donc exprimée en en-têtes :
#   borne basse = `semaine_debut` (1ᵉ tick après l'injection porte cet en-tête) ;
#   borne haute = `semaine_fin - 1` si accompli, sinon `week_courante - 1` (dernier
#   tick joué). Lecture PURE, déterministe (aucun tri : ordre du log conservé).

from __future__ import annotations
import re

from .objectifs import CLE_OBJECTIFS
from .trace import CLE_JOURNAL

# En-tête de bloc de tick, ex. "S07/Y2 — ÉTÉ" → (week_in_year, annee).
_ENTETE = re.compile(r"^S(\d+)/Y(\d+)")


def _blocs_log(log: list):
    """Itère `(semaine_absolue, ligne)` sur le log plat. La semaine absolue d'un bloc
    est dérivée de son en-tête `S{wiy}/Y{annee}` : `(annee-1)*52 + wiy`. Les lignes
    avant tout en-tête (aucune, en pratique) sortent avec semaine 0."""
    semaine = 0
    for ligne in log:
        m = _ENTETE.match(ligne)
        if m:
            wiy, annee = int(m.group(1)), int(m.group(2))
            semaine = (annee - 1) * 52 + wiy
        yield semaine, ligne


def onglet(game_state: dict, obj_id: str) -> dict:
    """Vue scopée d'un objectif : ses gestes (journal filtré) + les événements du monde
    de sa fenêtre active. Renvoie un dict JSON-sérialisable (les `Objectif` sont
    aplatis en champs simples). `obj_id` inconnu → dict avec `objectif=None`."""
    rec = game_state.get(CLE_OBJECTIFS, {}).get(obj_id)
    if rec is None:
        return {"objectif": None, "obj_id": obj_id, "gestes": [], "evenements": []}
    obj = rec["objectif"]

    gestes = [e for e in game_state.get(CLE_JOURNAL, [])
              if e.get("objectif_id") == obj_id]

    debut = rec["semaine_debut"]
    if rec["semaine_fin"] is not None:
        haut = rec["semaine_fin"] - 1
    else:
        haut = game_state.get("week", 0) - 1
    evenements = [ligne for sem, ligne in _blocs_log(game_state.get("log", []))
                  if debut <= sem <= haut]

    return {
        "obj_id": obj_id,
        "objectif": {"geste": obj.geste, "quantite": obj.quantite,
                     "cible": obj.cible, "id": obj.id},
        "progression": rec["progression"],
        "accompli": rec["semaine_fin"] is not None,
        "semaine_debut": debut,
        "semaine_fin": rec["semaine_fin"],
        "gestes": gestes,
        "evenements": evenements,
    }
