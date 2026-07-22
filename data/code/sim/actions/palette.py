"""
SYMBIOSE — sim/actions/palette.py
LAYOUT de la PALETTE de gestes, PAR AVATAR (sprint PALETTE DE GESTES, tronçon ⑤).
Spec : `docs/joueur/gestes/conception_palette_gestes.md` §3.1/§3.7 (D1/D5/D10) +
kickoff `sprints/joueur/gestes/sprint_palette_gestes/05_macros_banc.md`.

Ce module porte l'ÉTAT et les DONNÉES du layout de palette — les slots CURÉS par
le joueur (l'ordre/la sélection des gestes à portée, esprit « paint ») et ses
MACROS. Persisté PAR AVATAR dans la save JSON (comme `gestes_debloques`/maîtrise/
encyclopédie). Une macro (D1/D5) = une SÉQUENCE ordonnée de gestes rejouée par la
VUE sur la MÊME cible cliquée (planter→pailler→arroser ICI) : le MOTEUR ne
« connaît » pas les macros, il reçoit N gestes normaux séquencés (chacun paie sa
Vigueur, philo #1). Ici on ne stocke QUE la définition (donnée) + on la valide.

GARDE-FOU DE COUCHE (miroir de `deblocage.py`/`maitrise.py`) : ce module vit
AU-DESSUS du tick écologique. Le golden (`tests/test_golden.py`) est une
succession spontanée SANS joueur → aucune clé `palette` n'est jamais créée →
no-op strict. Aucun RNG (philo #3). On n'importe AUCUN geste (respect des couches :
ce module est data/état pur — la seule VALIDATION de cohérence de cible s'appuie
sur une petite table `FAMILLE_CIBLE` locale, source de vérité Python).
"""
from __future__ import annotations


# --- Famille de CIBLE par geste (validation de cohérence des macros, §Modèle) --
# Une macro n'a de sens que si TOUS ses sous-gestes acceptent la MÊME famille de
# cible : le clic unique doit désigner une cible que chaque sous-geste sait
# consommer. On regroupe donc les verbes par famille de désignation :
#   "plot"      — un plot de milieu {tile, r/c ou x/y} (planter/arroser/pailler…) ;
#   "plante"    — une plante par position (recolter/tailler/manger/bouturer…) ;
#   "tuile"     — la tuile entière (favoriser_auxiliaire) ;
#   "structure" — une structure existante (composter/retourner/epandre…) ;
#   "conteneur" — un pot/bac existant (deplacer_pot/planter_conteneur) ;
#   "global"    — sans cible (grelinette).
# La table est PROPOSÉE (calibrage F5, alignée sur les Kinds de WorldView.Actions.cs :
# m/q/U→plot, p/x/D/b→plante, t→tuile, s/E→structure, C→conteneur, '-'→global). Un
# verbe absent de la table est traité comme sa PROPRE famille (macro à un seul type
# de geste toujours cohérente) → dégradation gracieuse, jamais de rejet abusif.
FAMILLE_CIBLE: dict[str, str] = {
    # plot de milieu
    "planter": "plot", "arroser": "plot", "pailler": "plot", "becher": "plot",
    "poser_bac": "plot", "poser_pile": "plot", "poser_ruche": "plot",
    "glaner": "plot",   # ramasse la litière tendre d'un plot → stock (moyens d'agir ③)
    # plante par position
    "recolter": "plante", "deraciner": "plante", "tailler": "plante",
    "pincer": "plante", "arracher": "plante",
    "couper": "plante", "manger": "plante", "ecraser": "plante",
    "broyer": "plante", "bouturer": "plante", "greffer": "plante",
    "favoriser_auxiliaire": "tuile",
    # structures posées
    "composter": "structure", "empiler_bois": "structure",
    "retourner": "structure", "epandre": "structure", "recolter_miel": "structure",
    # conteneurs
    "deplacer_pot": "conteneur", "planter_conteneur": "conteneur",
    # sans cible
    "grelinette": "global",
}


def famille_cible(verbe: str) -> str:
    """Famille de désignation d'un geste (défaut = le verbe lui-même si absent de
    la table → une macro mono-verbe reste toujours cohérente)."""
    return FAMILLE_CIBLE.get(verbe, verbe)


def macro_coherente(sequence: list[str]) -> bool:
    """Vrai ssi tous les sous-gestes d'une macro partagent la MÊME famille de
    cible — condition pour qu'un clic unique les alimente tous (§Modèle). Une
    séquence vide ou à un seul geste est trivialement cohérente."""
    if len(sequence) <= 1:
        return True
    familles = {famille_cible(v) for v in sequence}
    return len(familles) == 1


# --- État joueur (miroir de deblocage.init_gestes_debloques) -----------------
def _defaut() -> dict:
    """Layout par défaut d'un nouvel avatar : aucune curation de slots (la palette
    Godot montre alors tous les gestes ouverts), aucune macro."""
    return {"slots": [], "macros": []}


def init_palette(game_state: dict, player: str) -> dict:
    """Crée (si besoin) et renvoie le layout de palette d'un avatar. Geste d'OPT-IN :
    tant qu'aucun joueur n'a de palette, `game_state` n'a pas la clé `palette` → le
    tick reste un no-op strict (golden intact). Tout nouvel avatar part du défaut."""
    pal = game_state.setdefault("palette", {})
    return pal.setdefault(player, _defaut())


def palette_layout(game_state: dict, player: str) -> dict:
    """Lecture pure du layout d'un avatar (pour l'expo au snapshot). Un joueur sans
    couche palette retombe sur le défaut, SANS écrire (déterminisme, no-op golden)."""
    pal = game_state.get("palette")
    layout = (pal or {}).get(player)
    return layout if layout else _defaut()


def _macro_valide(m) -> tuple[bool, str]:
    """Valide UNE macro reçue de la vue : `{nom, sequence}` avec une `sequence` de
    verbes (liste de str non vide) COHÉRENTE en famille de cible. Renvoie
    (ok, message)."""
    if not isinstance(m, dict):
        return False, "macro non-objet"
    seq = m.get("sequence")
    if not isinstance(seq, list) or not seq:
        return False, "macro sans séquence"
    if not all(isinstance(v, str) for v in seq):
        return False, "séquence de gestes non textuelle"
    if not macro_coherente(seq):
        return False, ("macro incohérente : gestes de familles de cible "
                       f"différentes ({', '.join(sorted(set(map(famille_cible, seq))))})")
    return True, ""


def definir_palette(game_state: dict, player: str,
                    slots=None, macros=None) -> tuple[bool, str]:
    """Persiste un changement de LAYOUT envoyé par la vue (le joueur cure sa palette
    ou enregistre une macro). Écriture bornée à l'état JOUEUR (opt-in) → golden
    intact. Chaque argument non-None REMPLACE la clé correspondante (curation
    complète, pas un patch incrémental — la vue possède le layout affiché et le
    renvoie entier). Valide les macros AVANT d'écrire (une macro incohérente est
    refusée en bloc, rien n'est modifié). Renvoie (ok, message)."""
    layout = init_palette(game_state, player)
    if slots is not None:
        if not isinstance(slots, list) or not all(isinstance(s, str) for s in slots):
            return False, "slots doivent être une liste de verbes (str)"
    if macros is not None:
        if not isinstance(macros, list):
            return False, "macros doivent être une liste"
        for m in macros:
            ok, msg = _macro_valide(m)
            if not ok:
                return False, msg
    # Tout est validé → on écrit (transaction : aucune modif si un refus plus haut).
    if slots is not None:
        layout["slots"] = list(slots)
    if macros is not None:
        layout["macros"] = [{"nom": m.get("nom", ""),
                             "sequence": list(m["sequence"])} for m in macros]
    return True, "layout de palette enregistré"
