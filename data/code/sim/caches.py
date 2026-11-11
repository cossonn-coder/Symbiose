"""
SYMBIOSE — sim/caches.py
Les bêtes qui CACHENT (zoochorie ⑤, D42) : le GEAI et l'ÉCUREUIL.

Ils cueillent glands, faînes, noix et noisettes MÛRS sur l'arbre (trait d'espèce
`mange_par`, même prise saturante que le merle : `sim.zoochorie.prendre`), les
enterrent pour l'hiver, et en OUBLIENT une part. Le fruit oublié est une graine
semée — c'est ainsi que la chênaie avance, à la vitesse des geais.

  - GEAI : enterre au loin, en terrain DÉCOUVERT (sol clair, peu couvert), de
    préférence au pied d'un repère vertical (arbre, tuteur, mort debout) qui l'aide
    à retrouver sa cache. Jamais sous une couronne dense. Peut changer de tuile.
    L'automne, il apporte aussi les glands de la FORÊT de la ceinture.
  - ÉCUREUIL : enterre près des arbres, à ≤ `R_ECUREUIL_CM` de l'arbre source,
    dans l'ANNEAU DE LISIÈRE des couronnes (sol à un ou deux plots d'une cime).

Deux temps par semaine, comme le merle (appelés par `sim/engine/boucle.py`) :
  1. `caches_prennent` — PAR TUILE, juste après `merle_prend` (15c-ter).
  2. `caches_sement` — UNE fois, après `merle_seme` : grilles calculées sur l'état
     de fin de tick du MONDE ENTIER → l'ordre des tuiles ne décide rien.

Satiation : une glandée dépasse l'appétit, le surplus tombe au pied (chemin ②).
Rien n'est ajouté pour ça : c'est la borne Holling II de la prise.

Couche `sim` : lit `fields`, `plants`, `sim.reproduction`, `sim.zoochorie`, jamais
`sim.engine`. Zéro RNG (philo #3) : tous les tirages passent par `_hash_noise`.
"""
from __future__ import annotations

from bisect import bisect_right
from math import hypot

from calendrier import SAISONS, wiy_de
from constants import PLOT_CM
from fields import _hash_noise
from fields.peripherie import plots_de_bord
from fields.population.disperseurs import couronnes
from fields.seedbank import (grain_sauvage, deposer_grain_sauvage, founder_genes)
from plants import PERENNIAL_CATALOGUE
from sim.reproduction import (find_father, child_genes, child_expression,
                              facteur_glandee)
from sim.zoochorie import prendre, _entier, HAUTEUR_PERCHOIR_CM

# (nom, part d'une cohorte mûre prise / sem. par un champ saturé, appétit en fruits
# par unité de densité / sem., part des fruits cachés OUBLIÉE, décalage de canal).
# Placeholders, calibrage au ⑦. Un geai cache des milliers de glands par automne et
# en oublie une part notable ; l'écureuil retrouve mieux les siennes (odorat) [odg].
DISPERSEURS = (
    ("geai",     0.15, 40.0, 0.10, 2),
    ("ecureuil", 0.15, 30.0, 0.10, 3),
)
# Rayon de cache de l'écureuil autour de l'arbre source (cm).
R_ECUREUIL_CM = 1500.0
# Grille « découvert » du geai : la lumière-sol doit dépasser `LUM_DECOUVERT` (sous
# une couronne dense elle tombe bien en dessous) ; bonus près d'un repère vertical
# à ≤ `REPERE_PLOTS` plots (Chebyshev). Placeholders.
LUM_DECOUVERT = 0.5
BONUS_REPERE = 2.0
REPERE_PLOTS = 2
# Anneau de lisière des couronnes (écureuil) : plots hors cime à ≤ 2 plots d'une cime.
ANNEAU_PLOTS = 2
# Apport de la ceinture : grains / semaine d'automne / tuile, × densité ligneuse du
# secteur × densité moyenne de geai de la tuile × glandée. Bande prioritaire : poids
# × (1 + BANDE_W × proximité du bord) sur `BANDE_CM`. Placeholders, calibrage ⑦.
APPORT_CEINTURE = 15.0
BANDE_W = 2.0
BANDE_CM = 500.0
# Tampon monde (créé au besoin, retiré par `caches_sement` → rien au save).
TAMPON_CACHES = "zoochorie_caches"
_LOG = {"geai": "🐦 Geai", "ecureuil": "🐿 Écureuil"}


def caches_prennent(game_state: dict, tile, eco, seed: int, week: int) -> list:
    """Geai puis écureuil cueillent les fruits à coque mûrs de la tuile ; les fruits
    OUBLIÉS (`prise × P_OUBLI`) partent au tampon monde avec la position MONDE de
    l'arbre source (l'écureuil cache autour). Le geai passe le premier : l'écureuil
    prend sur ce qu'il reste. Renvoie le log (une ligne par plante et par bête)."""
    log = []
    ox, oy = tile.origin_x_cm, tile.origin_y_cm
    for nom, taux, appetit, p_oubli, decal in DISPERSEURS:
        for plant, n_pris in prendre(tile, eco, nom, taux, appetit, seed, week, decal):
            log.append(f"    {_LOG[nom]} : {n_pris} fruits cachés depuis "
                       f"{plant.name}@{plant.position}")
            pr, pc = plant.position
            n = _entier(n_pris * p_oubli, seed, week, pr * 1009 + 7, pc + 1, decal)
            if n == 0:
                continue
            father = find_father(plant, tile.plants, tile, eco, seed, week)
            source = (ox + (pc + 0.5) * PLOT_CM, oy + (pr + 0.5) * PLOT_CM)
            game_state.setdefault(TAMPON_CACHES, []).append(
                (nom, plant.plant_class, child_genes(plant, father, seed, week),
                 child_expression(plant), n, pr * 1009 + pc, source))
    return log


def _centre(tile, r: int, c: int) -> tuple:
    return (tile.origin_x_cm + (c + 0.5) * PLOT_CM,
            tile.origin_y_cm + (r + 0.5) * PLOT_CM)


def _decouvert_tuile(tile, eco) -> dict:
    """`{(r, c): poids}` du geai sur une tuile : lumière-sol au-dessus du seuil ×
    (1 − couverture du sol) × (1 + bonus si un repère vertical est proche)."""
    reperes = [p.position for p in tile.plants
               if getattr(p.plant_class, "ligneux", False)
               and ((p.is_alive and p.current_height >= HAUTEUR_PERCHOIR_CM)
                    or (not p.is_alive and p.stade_mort == "seche"))]
    reperes += [(int(s.y_cm // PLOT_CM), int(s.x_cm // PLOT_CM)) for s in tile.supports]
    poids = {}
    for r in range(tile.grid_rows):
        for c in range(tile.grid_cols):
            lum = eco.lumiere.data[r][c]
            ouvert = max(0.0, (lum - LUM_DECOUVERT) / (1.0 - LUM_DECOUVERT))
            w = ouvert * (1.0 - eco.couverture_sol.data[r][c])
            if w <= 0.0:
                continue
            if any(max(abs(r - rr), abs(c - rc)) <= REPERE_PLOTS for rr, rc in reperes):
                w *= 1.0 + BONUS_REPERE
            poids[(r, c)] = w
    return poids


def grille_decouvert(game_state: dict) -> list:
    """Plots du MONDE où le geai enterre : `[(tuile, r, c, poids)]`, ordre stable."""
    grille = []
    for tile in game_state["tiles"]:
        poids = _decouvert_tuile(tile, game_state["eco"][tile.tile_id])
        grille += [(tile, r, c, w) for (r, c), w in sorted(poids.items())]
    return grille


def grille_lisiere_couronnes(game_state: dict) -> list:
    """Plots du MONDE dans l'anneau de lisière des couronnes : hors cime, à ≤
    `ANNEAU_PLOTS` plots d'une cime (ligneux vivant ≥ 3 m) — là où l'écureuil
    descend enterrer. `[(tuile, r, c, 1.0)]`, ordre stable."""
    grille = []
    for tile in game_state["tiles"]:
        cimes = couronnes(tile.plants, tile.grid_rows, tile.grid_cols)
        anneau = set()
        for (r, c) in cimes:
            for dr in range(-ANNEAU_PLOTS, ANNEAU_PLOTS + 1):
                for dc in range(-ANNEAU_PLOTS, ANNEAU_PLOTS + 1):
                    rc = (r + dr, c + dc)
                    if rc not in cimes and tile.is_valid_plot(*rc):
                        anneau.add(rc)
        grille += [(tile, r, c, 1.0) for r, c in sorted(anneau)]
    return grille


def _semer(grille: list, n: int, cls, genes, expr, origine: str,
           seed: int, canal: int, sel: int, week: int) -> int:
    """`n` graines tirées par hash sur `grille` pondérée ; renvoie le nombre posé.
    `genes` None → gènes FONDATEURS au plot de dépôt (graine venue du dehors)."""
    if not grille or n <= 0:
        return 0
    cumul, acc = [], 0.0
    for g in grille:
        acc += g[3]
        cumul.append(acc)
    poses = 0
    for k in range(n):
        i = min(bisect_right(cumul, _hash_noise(seed, canal, sel, k) * acc),
                len(cumul) - 1)
        tile, r, c = grille[i][:3]
        gk = genes if genes is not None else founder_genes(
            cls, seed, week, r, c, (c + 0.5) * PLOT_CM, (r + 0.5) * PLOT_CM)
        poses += deposer_grain_sauvage(
            tile, r, c, grain_sauvage(cls, gk, expr, origine, week, None, None))
    return poses


def _apport_ceinture(game_state: dict, seed: int, week: int) -> int:
    """L'automne, le geai rapporte les glands (et faînes d'une hêtraie) des secteurs
    `foret` de la ceinture. Par tuile : `APPORT_CEINTURE × densité ligneuse × geai
    moyen de la tuile × glandée`, déposés sur le découvert de la tuile, la bande
    côté secteur en priorité. Gènes fondateurs (lignée sauvage, hors jardin). Sans
    ceinture ni geai : rien."""
    ceinture = game_state.get("ceinture")
    if not ceinture or wiy_de(week) not in SAISONS["automne"]:
        return 0
    annee, poses = (week - 1) // 52, 0
    for s in ceinture:
        if s["type"] != "foret" or s["densite_ligneuse"] <= 0.0:
            continue
        cles = ["chene"] + (["hetre"] if s.get("essence") == "hetre" else [])
        for ti, tile in enumerate(game_state["tiles"]):
            eco = game_state["eco"][tile.tile_id]
            champ = (eco.populations or {}).get("geai")
            if champ is None:
                continue
            geai = champ.total() / (eco.rows * eco.cols)
            poids = _decouvert_tuile(tile, eco)
            for r, c, b in plots_de_bord(s["cote"], eco.rows, eco.cols,
                                         (tile.origin_x_cm, tile.origin_y_cm), BANDE_CM):
                if (r, c) in poids:
                    poids[(r, c)] *= 1.0 + BANDE_W * b
            grille = [(tile, r, c, w) for (r, c), w in sorted(poids.items())]
            for k, cle in enumerate(cles):
                cls = PERENNIAL_CATALOGUE[cle]
                x = APPORT_CEINTURE * s["densite_ligneuse"] * geai * facteur_glandee(
                    cls, annee, seed)
                sel = (s["cote"] * 64 + ti) * 8 + k
                n = _entier(x, seed, week, sel, 11, 6)
                poses += _semer(grille, n, cls, None, {}, "ceinture",
                                seed, week * 83 + 7, sel, week)
    return poses


def caches_sement(game_state: dict, seed: int, week: int) -> list:
    """Vide le tampon des caches oubliées (geai → découvert du monde ; écureuil →
    anneau de lisière dans son rayon) puis ajoute l'apport de la ceinture. Le
    plafond par plot (①) peut refuser un grain : il est perdu. Appelé APRÈS
    `merle_seme`. Grilles calculées seulement s'il y a quelque chose à semer."""
    tampon = game_state.pop(TAMPON_CACHES, None) or []
    poses = {"geai": 0, "ecureuil": 0}
    decouvert = lisiere = None
    for nom, cls, genes, expr, n, sel, (sx, sy) in tampon:
        if nom == "geai":
            if decouvert is None:
                decouvert = grille_decouvert(game_state)
            grille, canal = decouvert, week * 83 + 4
        else:
            if lisiere is None:
                lisiere = grille_lisiere_couronnes(game_state)
            grille = [g for g in lisiere
                      if hypot(*(a - b for a, b in zip(_centre(*g[:3]), (sx, sy))))
                      <= R_ECUREUIL_CM]
            canal = week * 83 + 5
        poses[nom] += _semer(grille, n, cls, genes, expr, nom, seed, canal, sel, week)
    ceinture = _apport_ceinture(game_state, seed, week)
    log = [f"  {_LOG[nom]} : {n} cache(s) oubliée(s)" for nom, n in poses.items() if n]
    if ceinture:
        log.append(f"  🐦 Geai : {ceinture} gland(s) de la forêt enterré(s) au jardin")
    return log
