# SYMBIOSE — tools/jardinier_auto/repiquage.py
# Le REPIQUAGE DIFFÉRÉ de l'automate (départ du jardin ⑤, D140 C.5). Un plant élevé
# en pot (dans la maison ou dehors) attend que la saison le permette pour SON
# espèce ; l'automate le sort alors en pleine terre par le geste du joueur
# `repiquer` (sim/actions/conteneurs.py) — aucune voie privilégiée (philo #2).
#
# Intégration = une RÈGLE RÉACTIVE de plus, pas un opérateur de plan : aucun objectif
# n'est requis (le plant existe déjà, il ne s'agit pas de le faire advenir) et la
# décision se relit chaque semaine sur l'état du monde. La boucle ajoute ces plans aux
# plans réactifs AVANT le tri : ils passent donc par le même gating (`repiquer` est
# gated), le même budget de Vigueur et la même trace (`facteur` = la raison).
#
# QUAND (lecture du moteur, rien de recalculé autrement que lui) :
#   - hors de la fenêtre des « Gelée tardive » du catalogue météo
#     (`sim.weather.fenetre_evenement`) — on ne se fie pas à la prévision avant
#     les saints de glace ;
#   - la nuit la plus froide de la semaine écoulée ET des semaines prévues, au plot
#     visé, au-dessus de la limite de la plante + `MARGE_NUIT`. Même formule que le
#     tick (`t_min_nuit_at` sur `weather_state`, fonction PURE : prévoir = évaluer
#     la semaine à venir) ; le couvert du plot est celui d'aujourd'hui.
#   La limite est `max(lim_froid, lim_gel)` : la tomate s'abîme sous 10 °C sans
#   geler, une espèce non sensible au froid (lim_froid = −∞) ne craint que le gel.
#
# OÙ : le plot libre le PLUS LUMINEUX (`plots_libres`, le placement de `planter`) —
# les plants qu'on élève au chaud sont des cultures de soleil. Égalité → premier
# dans l'ordre canonique. Déterminisme total, zéro RNG (philo #3) ; aucune écriture.

from __future__ import annotations
from typing import NamedTuple

from sim.weather import weather_state, fenetre_evenement
from sim.engine.calendrier import wiy_de
from fields.ecofields.thermique import t_min_nuit_at
from .operateurs import plots_libres
from .proposition import Plan

# Degrés exigés AU-DESSUS de la limite de la plante, la nuit la plus froide : un
# jardinier ne sort pas ses tomates la semaine où la nuit frôle tout juste 10 °C.
MARGE_NUIT = 0.5

# Nuits lues : la semaine qui vient de s'écouler (NUITS_RECENTES) et les semaines à
# venir (HORIZON_NUITS, l'horizon par défaut de `sim.weather.forecast`).
NUITS_RECENTES = 1
HORIZON_NUITS = 2

# Événement dont la fenêtre bloque le repiquage, quelle que soit la prévision.
GELEE_TARDIVE = "Gelée tardive"

# Priorité : SOUS les facteurs de survie (10-20, regles.py), AU-DESSUS des gestes
# créatifs (5) — un plant qui attend en pot file et serre ses racines.
PRIO_REPIQUAGE = 7

# Raison tracée (`facteur_limitant` du journal) : les nuits sont devenues douces.
FACTEUR_REPIQUAGE = "nuits_douces"


class CibleRepiquage(NamedTuple):
    """Charge utile d'un Plan `repiquer` : le pot source et le plot de destination."""

    container: object     # world.container.Container
    tile: object          # world.tile.Tile
    r: int
    c: int


def limite_nuit(plant) -> float:
    """Nuit la plus froide supportée sans lésion : froid sans gel OU gel, la plus
    haute des deux (lim_froid vaut −∞ chez une espèce non sensible)."""
    return max(plant.lim_froid(), plant.lim_gel())


def hors_gelees_tardives(week: int) -> bool:
    """Vrai si aucune semaine lue (récente comme prévue) ne tombe dans la fenêtre des
    gelées tardives du catalogue météo."""
    lo, hi = fenetre_evenement(GELEE_TARDIVE)
    return not any(lo <= wiy_de(w) <= hi
                   for w in range(week - NUITS_RECENTES, week + HORIZON_NUITS))


def nuit_min(gs: dict, week: int, eco, r: int, c: int) -> float:
    """Nuit la plus froide, au plot `(r, c)`, sur les semaines lues. `week` = la
    semaine que le prochain tick simulera (l'automate joue APRÈS le tick)."""
    seed, forcee = gs.get("seed", 42), gs.get("pluie_forcee", False)
    nuits = []
    for w in range(week - NUITS_RECENTES, week + HORIZON_NUITS):
        _ev, t_air, nebul = weather_state(seed, w, forcee)
        nuits.append(t_min_nuit_at(eco, r, c, t_air, nebul))
    return min(nuits)


def _plots_par_lumiere(engine) -> list:
    """Plots libres `(tile, eco, r, c)` du plus lumineux au moins lumineux ; le tri est
    stable → à lumière égale, l'ordre canonique de `plots_libres`. Un balayage par
    tick, partagé par tous les pots (pas de recalcul)."""
    plots = [(tile, engine._eco(tile), r, c) for tile, r, c in plots_libres(engine)]
    return sorted(plots, key=lambda p: -p[1].lumiere.at_plot(p[2], p[3]))


def proposer_repiquages(engine) -> list:
    """Plans `repiquer` de la semaine, au format des plans réactifs `(cle, tile, eco,
    plant, Plan)`. Un pot par plante vivante (la première, comme le geste), dans
    l'ordre de `game_state["containers"]` ; chaque plot retenu est promis (le pot
    suivant prend le suivant), un plot refusé reste offert au pot suivant. Liste
    vide hors saison ou sans pot planté."""
    gs = engine.game_state
    week = engine.week
    pots = [(ctn, p) for ctn in gs.get("containers", ())
            for p in [next((q for q in ctn.plants if q.is_alive), None)] if p is not None]
    if not pots or not hors_gelees_tardives(week):
        return []
    plots = _plots_par_lumiere(engine)
    plans = []
    for ctn, plant in pots:
        if len(plans) >= len(plots):
            break                                     # monde saturé
        tile, eco, r, c = plots[len(plans)]           # le meilleur plot pas encore promis
        if nuit_min(gs, week, eco, r, c) < limite_nuit(plant) + MARGE_NUIT:
            continue                                  # trop tôt pour CE plant ; plot gardé
        plan = Plan(verbe="repiquer", cible="vivant",
                    cible_obj=CibleRepiquage(ctn, tile, r, c), nature=None,
                    facteur=FACTEUR_REPIQUAGE, priorite=PRIO_REPIQUAGE)
        plans.append(((tile.tile_id, r, c), tile, eco, plant, plan))
    return plans
