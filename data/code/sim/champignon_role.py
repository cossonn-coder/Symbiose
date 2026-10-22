"""
SYMBIOSE — sim/champignon_role.py
RÔLE LOCAL d'un carpophore (INFO-BULLE DU VIVANT ①, D110 b).
Spec : `docs/narration/semiologie/conception_infobulle_vivant.md` §2 décision 4.

Le réseau mycélien a 3 rôles au moteur (sprint mycélium) : saprophyte du bois mort,
mycorhize des racines (boost P de `fields/ecofields/uptake.py`, lu sur les
`root_plots` des plantes vivantes), liant de l'humus stable. Un carpophore ne dit
QUE ce qui se passe SOUS LUI, dans cet ordre de priorité :
  1. bois frais au plot (`eco.bois_fresh_at > 0`)        → `b` « décompose le bois mort » ;
  2. sinon racines vivantes exploitant le plot          → `r` « relie les racines » ;
  3. sinon                                              → `h` « lie l'humus ».
Codes courts = clés de `signes_corpus.CHAMPIGNON_ROLE` (texte côté corpus).

LECTURE PURE, hors tick (appelé par le snapshot) → golden NEUTRE. Les plots racinés
se construisent UNE fois par tuile et par snapshot (`plots_racines`), jamais par
carpophore. `eco` et les plantes sont lus par duck-typing ; la météo (pure) sert
au gate « après la pluie » de la fructification (D111 ③).
"""
from __future__ import annotations

from fields.ecofields.constants import PLUIE_APPORT
from sim.weather import weather_state

ROLE_BOIS = "b"
ROLE_RACINES = "r"
ROLE_HUMUS = "h"


def plots_racines(plants) -> set:
    """Ensemble des plots `(r, c)` exploités par les racines d'au moins une plante
    VIVANTE — la même empreinte (`root_plots`) que l'uptake mycorhizien."""
    plots: set = set()
    for p in plants:
        if p.is_alive:
            plots.update(p.root_plots)
    return plots


def racines_par_plot(plants) -> dict:
    """Plot `(r, c)` → labels des racines VIVANTES qui l'exploitent (D111 ③) : la
    FAMILLE et le NOM d'espèce de chaque plante (les hôtes du registre fongique
    s'écrivent dans l'un ou l'autre) ; une plante affaiblie ajoute aussi ces labels
    préfixés `"!"` (niche des parasites, `fields/fongique.py`). Une fois par tuile."""
    out: dict = {}
    for p in plants:
        if not p.is_alive:
            continue
        cls = p.plant_class
        labels = [lab for lab in (getattr(cls, "family", None), cls.name) if lab]
        if p.etat != "sain":
            labels += ["!" + lab for lab in labels]
        for plot in p.root_plots:
            out.setdefault(plot, set()).update(labels)
    return out


def role_carpophore(eco, racines: set, r: int, c: int) -> str:
    """Code du rôle local du réseau au plot `(r, c)` (priorité bois > racines >
    humus). `racines` = `plots_racines(…)` ou `racines_par_plot(…)` (lu par `in`)."""
    if eco.bois_fresh_at(r, c) > 0:
        return ROLE_BOIS
    if (r, c) in racines:
        return ROLE_RACINES
    return ROLE_HUMUS


# Pluie qui fait sortir les carpophores (SOL QUI RESPIRE ③, D111) : un épisode dont
# l'apport d'eau du moteur (`PLUIE_APPORT`, même table que l'hydrologie) est une
# VRAIE pluie (Pluie prolongée 0,14, Orage 0,10) — pas la bruine d'une tempête.
PLUIE_FRUCTIFIANTE = 0.05


def pluie_semaine_precedente(gs) -> bool:
    """La semaine AVANT la dernière simulée a-t-elle été pluvieuse ? Le snapshot
    montre l'état après la semaine `week − 1` ; un carpophore perce ~3 jours après
    la pluie → visible la semaine qui SUIT l'épisode (`week − 2`). Météo PURE
    recalculée (rien de stocké) → golden NEUTRE. Banc `pluie_forcee` : toujours."""
    prec = gs["week"] - 2
    if prec < 1:
        return False
    ev = weather_state(gs["seed"], prec, gs.get("pluie_forcee", False))[0]
    return PLUIE_APPORT.get(ev.kind, 0.0) >= PLUIE_FRUCTIFIANTE
