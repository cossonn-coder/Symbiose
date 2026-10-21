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
carpophore. Aucun import : `eco` et les plantes sont lus par duck-typing.
"""
from __future__ import annotations

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


def role_carpophore(eco, racines: set, r: int, c: int) -> str:
    """Code du rôle local du réseau au plot `(r, c)` (priorité bois > racines >
    humus). `racines` = `plots_racines(tile.plants)` précalculé."""
    if eco.bois_fresh_at(r, c) > 0:
        return ROLE_BOIS
    if (r, c) in racines:
        return ROLE_RACINES
    return ROLE_HUMUS
