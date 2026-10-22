"""
SYMBIOSE — sim/champignon_manger.py
MANGER un carpophore (sprint « le sol qui respire » ⑥, D111 §4) + la liste des
carpophores VISIBLES d'une tuile (source unique du snapshot et du geste).

📖 Pédagogie — manger est un PARI tant qu'on ne sait pas (philo #6). L'effet suit
la comestibilité du registre ③ (`fields/fongique.REGISTRE_FONGIQUE`, tags cumulables) :
  - comestible    → Vigueur, ∝ la « maturité » du carpophore (densité du réseau qui
                    le porte), comme un fruit (`HARVEST_GAIN_FULL`) ;
  - vénéneux      → Vigueur effondrée (une fraction de la Vigueur max) ;
  - mortel        → effondrée PLUS fort — mais JAMAIS de mort (pas de game over :
                    la Vigueur a un plancher 0, le jardinier se relève) ;
  - psychédélique → une semaine de vision (`sim/vision.py`) ; un 2ᵉ pendant l'effet
                    = overdose ; l'amanite tue-mouches cumule vision ET perte ;
  - immangeable   → trop coriace : refus, rien n'est consommé.
Le message ne NOMME l'espèce que si le jardinier l'a nommée (sinon : ce qu'il ressent).

Le carpophore mangé DISPARAÎT pour la semaine affichée : mémoire de PERCEPTION
`game_state["carpophores_manges"] = {semaine, cles: [[tuile, r, c, slot], …]}`,
remise à zéro quand la semaine change (bornée), jamais lue par le tick.
Les pertes passent par `vigueur.spend` (seul point de débit) : l'interrupteur de test
« Vigueur infinie » les masque donc, comme toute dépense.

Couche `sim`, hors tick → golden NEUTRE. Zéro RNG.
"""
from __future__ import annotations

from fields.population import sample_carpophores
from fields.population.perception import CARPO_DENS_REF
from fields.fongique import (REGISTRE_FONGIQUE, COMESTIBLE, VENENEUX, MORTEL,
                             PSYCHEDELIQUE, IMMANGEABLE)
from sim.champignon_role import racines_par_plot, pluie_semaine_precedente
from sim.champignon_voix import champignons_nommes
from sim.vigueur import spend, gain, vigueur_max
from sim.actions.gestes import HARVEST_GAIN_FULL   # même échelle qu'un fruit (DRY)
from sim import vision

# Fractions de la Vigueur MAX retirées (calibrage à l'usage) : vénéneux = une bonne
# indigestion, mortel = le jardinier est à terre (mais vivant).
PERTE_VENENEUX = 0.5
PERTE_MORTEL = 0.9

_CLE_MEMOIRE = "carpophores_manges"


def _manges(game_state: dict, tile_id) -> set:
    """Carpophores `(r, c, slot)` mangés cette semaine sur la tuile (lecture pure)."""
    mem = game_state.get(_CLE_MEMOIRE)
    if not mem or mem["semaine"] != game_state["week"]:
        return set()
    return {(r, c, s) for t, r, c, s in mem["cles"] if t == tile_id}


def carpophores_tuile(game_state: dict, tile, pluie_prec: bool | None = None):
    """(carpophores VISIBLES non mangés, racines par plot) d'une tuile — exactement
    l'échantillonnage du snapshot (semaine de l'horloge moteur, pluie de la semaine
    d'avant, niches d'hôtes), moins ce que le jardinier a mangé cette semaine."""
    if pluie_prec is None:
        pluie_prec = pluie_semaine_precedente(game_state)
    eco = game_state["eco"][tile.tile_id]
    racines = racines_par_plot(tile.plants) if pluie_prec else {}
    week_in_year = ((game_state["week"] - 1) % 52) + 1
    carpos = sample_carpophores(eco, game_state["seed"], week_in_year, pluie_prec, racines)
    manges = _manges(game_state, tile.tile_id)
    if manges:
        carpos = [k for k in carpos if (k.row, k.col, k.slot) not in manges]
    return carpos, racines


def _memoriser(game_state: dict, tile_id, k) -> None:
    """Retire le carpophore de la perception jusqu'à la fin de la semaine."""
    mem = game_state.get(_CLE_MEMOIRE)
    if not mem or mem["semaine"] != game_state["week"]:
        mem = {"semaine": game_state["week"], "cles": []}
        game_state[_CLE_MEMOIRE] = mem
    mem["cles"].append([tile_id, k.row, k.col, k.slot])


def manger_carpophore(game_state: dict, player: str, tile, r: int, c: int,
                      slot: int) -> dict:
    """Manger le carpophore `(r, c, slot)` de `tile`. Renvoie
    `{applied, gain, perte, vision, espece_nommee, message}` — `vision` ∈ {None,
    "vision", "overdose"} ; `espece_nommee` = clé si le joueur la connaît, sinon None
    (la vue ne doit pas apprendre le nom par le geste)."""
    carpos, _ = carpophores_tuile(game_state, tile)
    k = next((k for k in carpos if (k.row, k.col, k.slot) == (r, c, slot)), None)
    if k is None:
        return {"applied": False, "gain": 0.0, "perte": 0.0, "vision": None,
                "espece_nommee": None,
                "message": "aucun champignon à cueillir ici"}
    esp = REGISTRE_FONGIQUE[k.espece]
    tags = esp.comestibilite
    nomme = k.espece in champignons_nommes(game_state, player)
    if IMMANGEABLE in tags:
        return {"applied": False, "gain": 0.0, "perte": 0.0, "vision": None,
                "espece_nommee": k.espece if nomme else None,
                "message": "trop coriace : la dent n'y entre pas"}
    _memoriser(game_state, tile.tile_id, k)
    ressentis = []
    g = perte = 0.0
    if COMESTIBLE in tags:
        g = HARVEST_GAIN_FULL * min(1.0, k.densite / CARPO_DENS_REF)
        gain(game_state, player, g)
        ressentis.append(f"une chair ferme au goût de sous-bois (+{g:.1f} Vigueur)")
    frac = PERTE_MORTEL if MORTEL in tags else PERTE_VENENEUX if VENENEUX in tags else 0.0
    if frac:
        perte = frac * vigueur_max(game_state, player)
        spend(game_state, player, perte)
        txt = ("des crampes te jettent à terre, tu mets longtemps à te relever"
               if MORTEL in tags else "le ventre se noue, la tête tourne")
        ressentis.append(f"{txt} (−{perte:.0f} Vigueur)")
    v = vision.commencer(game_state, player) if PSYCHEDELIQUE in tags else None
    if v == "vision":
        ressentis.append("les couleurs se mettent à vibrer, le jardin te parle")
    elif v == "overdose":
        ressentis.append("tout parle en même temps, partout — impossible de se taire")
    tete = f"{esp.nom} mangé" if nomme else "champignon mangé"
    return {"applied": True, "gain": g, "perte": perte, "vision": v,
            "espece_nommee": k.espece if nomme else None,
            "message": f"{tete} : " + " ; ".join(ressentis or ["un goût de terre"])}
