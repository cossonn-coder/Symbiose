"""
SYMBIOSE — tools/simserver/vent_pont.py
Le VENT au pont (sprint JARDIN VIVANT T3, protocole 0.5.44) : deux lectures PURES
qui permettent à la vue de faire passer une ONDE de vent sur les plantes.

  1. `wind_block(seed, last)` → `weather.wind = {force, direction, gusts}` : la
     MASSE D'AIR de la dernière semaine simulée (`sim.wind.wind_at` +
     `gust_profile`, fonctions pures O(1)). Même repère temporel que le reste du
     bloc `weather` (`last = week − 1`) ; à l'init (rien simulé) = calme.
  2. `abri_facteur(eco, plant)` → facteur d'ABRI local de la plante (1.0 = pleine
     exposition, < 1 abritée derrière la maison/une haie, > 1 venturi). Lu dans le
     cache géométrique du champ d'abri (`fields/abri.py`, `eco._abri_cache`) — c'est
     exactement `eco.vent[r,c] / force`, mais défini même par vent nul. Si le champ
     n'a JAMAIS été calculé (cache froid, monde neuf) → None : l'appelant OMET la
     clé et la vue prend 1.0. On ne FORCE jamais ce calcul (D99 : champ paresseux).

Lecture seule, zéro RNG, aucune écriture moteur → golden NEUTRE (le golden hache
le log moteur, pas le snapshot).
"""
from __future__ import annotations

from sim.wind import wind_at, gust_profile, SUBTICKS


def wind_block(seed: int, last: int) -> dict:
    """Masse d'air de la semaine `last` (dernière simulée). `direction` (rad) =
    D'OÙ VIENT le vent (convention `WindState`) ; `gusts` = les SUBTICKS facteurs
    intra-journaliers (risées) — la vue s'en sert pour moduler les fronts d'onde."""
    if last < 1:
        # Rien simulé : calme (cohérent avec `weather` = CALME à l'init). La
        # direction reste celle de la semaine 1 (le terrain a déjà son secteur).
        return {"force": 0.0, "direction": wind_at(seed, 1).direction,
                "gusts": [1.0] * SUBTICKS}
    w = wind_at(seed, last)
    return {"force": w.force, "direction": w.direction,
            "gusts": list(gust_profile(seed, last))}


def abri_facteur(eco, plant) -> float | None:
    """Facteur d'abri au plot-foyer de `plant`, ou None si le champ d'abri n'a pas
    encore été calculé (cache froid) ou si le plot sort de la grille."""
    cache = getattr(eco, "_abri_cache", None)
    if cache is None:
        return None
    facteur = cache[1]          # (signature, facteur, turbulence) — cf. compute_abri
    r, c = plant.position
    if not (0 <= r < len(facteur) and 0 <= c < len(facteur[r])):
        return None
    return round(facteur[r][c], 3)
