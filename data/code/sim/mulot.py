"""
SYMBIOSE — sim/mulot.py
Le MULOT mange les graines tombées, et en cache quelques-unes (zoochorie ⑥, D42).

Chaque semaine, sur chaque tuile, chaque grain SAUVAGE en attente au sol (tombé au
pied, semé par le merle, oublié par le geai ou l'écureuil, apporté de la ceinture)
risque d'être trouvé : `p = PRED_MAX × mulot(r,c) × satiation`.

  - SATIATION (Holling II) : `s = A / (A + O)`, O = nombre de grains sauvages de la
    tuile. Une année de glandée inonde le sol de glands : le mulot n'en mange
    qu'une petite PART, le reste lève. Une année maigre, presque tout est mangé.
    C'est le sens écologique du « masting » (②) : rassasier les prédateurs.
  - Un grain trouvé est CACHÉ avec `P_CACHE_MULOT` (déplacé à ≤ `R_CACHE_CM` sous
    couvert, `origine="mulot"`, sa dormance et sa péremption CONSERVÉES : c'est la
    même graine, enterrée ailleurs, et le mulot ne revient pas toujours) ; sinon il
    est MANGÉ (retiré).
  - Les grains plantés par le joueur (`origine == "joueur"`) ne sont JAMAIS touchés
    (le mulot n'est pas un ravageur de semis ici — dette notée au doc).

Appelé UNE fois par tick, APRÈS `caches_sement` (étape 17a-quater) : tous les dépôts
du jour sont posés (chute au pied 15c, merle 17a-bis, caches et ceinture 17a-ter),
donc une graine semée cette semaine court déjà le risque cette nuit. Les tuiles sont
indépendantes (cache dans la même tuile) → leur ordre ne décide rien. Un grain ne
lève qu'au printemps suivant (dormance ①) : rien ne lève entre dépôt et prédation.

Couche `sim` : lit `fields`, jamais `sim.engine`. Zéro RNG (philo #3) : tous les
tirages passent par `_hash_noise`.
"""
from __future__ import annotations

from bisect import bisect_right

from constants import PLOT_CM
from fields import _hash_noise
from fields.population.mulot import _mulot_habitat_grid
from fields.seedbank import deposer_grain_sauvage

# Probabilité hebdomadaire qu'un grain soit trouvé sous un champ `mulot` SATURÉ
# (densité 1) et un mulot affamé (satiation 1). Placeholder, calibrage au ⑦.
PRED_MAX = 0.5
# Demi-saturation Holling II, en grains sauvages par tuile : à `A` grains offerts,
# la pression par grain est divisée par deux. Placeholder, calibrage au ⑦.
A_SATIATION = 40.0
# Part des grains trouvés qui sont cachés (et oubliés) plutôt que mangés [odg].
P_CACHE_MULOT = 0.15
# Rayon de cache (cm) : le mulot enterre près de son terrier.
R_CACHE_CM = 300.0
# Plots de cache pondérés par le COUVERT = max(couverture du sol, habitat du mulot) ;
# sans aucun couvert dans le rayon, pas de cache : le grain est mangé.
# Canal de hash : `week * 89` (libre dans sim/fields, vérifié par grep au ⑥).
_CANAL = 89


def _poids_cache(tile, eco) -> list:
    """Grille de couvert où le mulot cache : max(couverture du sol, habitat)."""
    hab = _mulot_habitat_grid(eco, tile, tile.plants)
    couv = eco.couverture_sol
    return [[max(hab[r][c], couv.data[r][c] if couv is not None else 0.0)
             for c in range(eco.cols)] for r in range(eco.rows)]


def _cible(poids, r: int, c: int, rows: int, cols: int, u: float):
    """Plot de cache tiré (u ∈ [0,1)) dans le rayon `R_CACHE_CM`, pondéré par le
    couvert ; None si aucun couvert dans le rayon."""
    rad = int(R_CACHE_CM // PLOT_CM)
    plots, cumul, acc = [], [], 0.0
    for rr in range(max(0, r - rad), min(rows, r + rad + 1)):
        for cc in range(max(0, c - rad), min(cols, c + rad + 1)):
            if (rr - r) ** 2 + (cc - c) ** 2 > rad * rad:
                continue
            w = poids[rr][cc]
            if w > 0.0:
                acc += w
                plots.append((rr, cc))
                cumul.append(acc)
    if not plots:
        return None
    return plots[min(bisect_right(cumul, u * acc), len(plots) - 1)]


def mulot_tuile(tile, eco, seed: int, week: int) -> tuple[int, int]:
    """Prédation et caches du mulot sur une tuile : `(mangés, cachés)`. No-op sans
    champ `mulot` ou sans grain sauvage. Ordre déterministe : plots triés, puis
    ordre de la liste du plot."""
    champ = (eco.populations or {}).get("mulot")
    grains = tile.grains_en_attente
    if champ is None or not grains:
        return 0, 0
    offre = sum(1 for lst in grains.values() for g in lst if g.origine != "joueur")
    if offre == 0:
        return 0, 0
    s = A_SATIATION / (A_SATIATION + offre)
    poids, mange, cache = None, 0, []          # cache : [(r, c, grain)] à reposer
    for (r, c) in sorted(grains):
        d = champ.get(r, c)
        if d <= 0.0:
            continue
        p = PRED_MAX * d * s
        garde = []
        for k, g in enumerate(grains[(r, c)]):
            if g.origine == "joueur" or _hash_noise(seed, week * _CANAL, r * 1009 + k, c) >= p:
                garde.append(g)
                continue
            dest = None
            if _hash_noise(seed, week * _CANAL + 1, r * 1009 + k, c) < P_CACHE_MULOT:
                if poids is None:
                    poids = _poids_cache(tile, eco)
                u = _hash_noise(seed, week * _CANAL + 2, r * 1009 + k, c)
                dest = _cible(poids, r, c, eco.rows, eco.cols, u)
            if dest is None:
                mange += 1
            else:
                g.origine = "mulot"
                cache.append((dest, g))
        grains[(r, c)] = garde
    # Reposés APRÈS la passe : un grain caché n'est pas re-tiré la même nuit. Le
    # plafond par plot (①) peut refuser : la graine en trop est mangée.
    caches = 0
    for (rr, cc), g in cache:
        if deposer_grain_sauvage(tile, rr, cc, g):
            caches += 1
        else:
            mange += 1
    return mange, caches


def mulot_mange(game_state: dict, seed: int, week: int) -> list:
    """Passe du mulot sur toutes les tuiles ; une ligne de log par tuile où il y a eu
    prédation. Appelé APRÈS `caches_sement`."""
    log = []
    for tile in game_state["tiles"]:
        eco = game_state["eco"][tile.tile_id]
        n, k = mulot_tuile(tile, eco, seed, week)
        if n or k:
            log.append(f"  🐭 Mulot : {n} graines mangées, {k} cachées "
                       f"({tile.tile_id})")
    return log
