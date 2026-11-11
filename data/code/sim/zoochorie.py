"""
SYMBIOSE — sim/zoochorie.py
Dispersion des graines par les bêtes (zoochorie ④, D42) : le MERLE.

Le merle prend les fruits MÛRS sur la plante (cerisier, framboisier, fraisier :
trait d'espèce `mange_par`), et les graines qui survivent au transit tombent là où
il se POSE — sous un arbre, un mort debout, un support (tuteur, perchoir posé…),
en lisière. Il ne se pose pas au milieu du gazon : sans perchoir, la graine est
perdue. C'est la nucléation : un perchoir au milieu d'une friche devient, en
quelques années, un îlot de ronces et d'arbustes à baies.

Deux temps par semaine (appelés par `sim/engine/boucle.py`) :
  1. `merle_prend` — PAR TUILE, étape 15c, juste APRÈS `_tick_fruits` : les fruits
     de la semaine sont à jour (nouaison, maturation, chute des sur-mûrs). Le fruit
     pris est RETIRÉ de sa cohorte (il ne tombera plus en litière `fruit`) ; les
     graines survivantes partent dans un TAMPON monde (`game_state`).
  2. `merle_seme` — UNE fois, APRÈS la boucle des tuiles : la grille « perchoir »
     du monde entier est calculée sur l'état de fin de tick, puis chaque graine
     tombe sur un plot tiré par hash, pondéré par cette grille. Calculer la grille
     ici (et pas au fil des tuiles) fait que l'ORDRE des tuiles ne décide rien : un
     merle nourri sur la tuile O peut semer sur la tuile E. Le grain est un grain
     SAUVAGE (`origine="merle"`) : dormance → il lève au plus tôt au printemps
     suivant (`fields.seedbank.grain_sauvage`), jamais la semaine même.

Réponse saturante (Holling II) : la prise de la tuile est bornée par l'appétit
(∝ population de merles de la tuile). Une grosse récolte rassasie : le reste tombe.

Effet induit VOULU, non compensé : moins de cerises au sol → moins de litière
`fruit` → la ressource du merle (`_merle_food_grid`, fruit tombé) et le signal des
ravageurs attirés par le fruit pourri baissent. C'est la boucle réelle.

Couche `sim` : lit `fields`, `plants` et `sim.reproduction`, jamais `sim.engine`.
Zéro RNG (philo #3) : tous les tirages passent par `_hash_noise`.
"""
from __future__ import annotations

from constants import PLOT_CM
from fields import _hash_noise
from fields.seedbank import grain_sauvage, deposer_grain_sauvage
from sim.reproduction import (find_father, child_genes, child_expression,
                              recrue_par_fruits)

# Part d'une cohorte mûre prise en une semaine par un champ `merle` SATURÉ (densité
# 1) au-dessus de la plante. Placeholder, calibrage au ⑦.
TAUX_PRISE = 0.15
# Appétit : fruits qu'une unité de densité de merle peut avaler par semaine (borne
# Holling II, sommée sur la tuile). Placeholder, calibrage au ⑦ : une année
# ordinaire doit laisser tomber une part des cerises.
APPETIT = 25.0
# Part des graines avalées qui ressortent viables (transit intestinal, noyaux
# régurgités). Une cerise = un noyau. Placeholder, calibrage au ⑦.
P_TRANSIT = 0.05
# Seuil « mûr » d'une cohorte (maturité 1,0 ; la chute vient à MATURITE_CHUTE). La
# tolérance absorbe l'arrondi d'une maturation en 1/7 par semaine (7 × 1/7 < 1).
MUR = 1.0 - 1e-9
# Hauteur minimale d'un ligneux vivant pour servir de perchoir (cm).
HAUTEUR_PERCHOIR_CM = 150.0
# Clé du tampon monde dans `game_state` (créée au besoin, retirée par `merle_seme`
# → aucune trace persistante, ni au save ni au golden).
TAMPON = "zoochorie_tampon"
# Canal de hash : `week * 83` (aucun autre canal `week * 83` dans sim/fields).
_CANAL = 83


def _entier(x: float, seed: int, week: int, a: int, b: int) -> int:
    """Arrondi entier déterministe : partie entière + 1 avec la probabilité de la
    partie fractionnaire, tranchée par hash. Espérance exacte, zéro RNG."""
    n = int(x)
    if _hash_noise(seed, week * _CANAL, a, b) < x - n:
        n += 1
    return n


def _plots_plante(plant, tile) -> list:
    """Plots où le merle cueille : la couronne (arbre à cohortes) ou le pied
    (herbacée) — même règle que la chute (`decompo.deposer_fruits`)."""
    if plant.plant_class.fruits_par_site is None:
        return [plant.position]
    plots = [rc for rc in plant.foliar_plots if tile.is_valid_plot(*rc)]
    return plots or [plant.position]


def merle_prend(game_state: dict, tile, eco, seed: int, week: int) -> list:
    """Le merle cueille les fruits mûrs de la tuile ; les graines vont au tampon.

    Par cohorte mûre : `demande = nombre × TAUX_PRISE × d̄`, d̄ = densité moyenne du
    champ `merle` sur les plots de la plante. Si la demande totale de la tuile
    dépasse `APPETIT × Σ densité`, toutes les prises sont réduites au prorata.
    Graines : `prise × P_TRANSIT`, gènes `child_genes(mère, père)`. Renvoie le log
    (une ligne par plante et par semaine de prise). No-op sans champ `merle`."""
    champ = (eco.populations or {}).get("merle")
    if champ is None:
        return []
    demandes = []                 # (plante, cohorte, demande)
    for plant in tile.plants:
        cls = plant.plant_class
        if (not plant.is_alive or not plant.fruits
                or "merle" not in cls.mange_par or not recrue_par_fruits(cls)):
            continue
        mures = [f for f in plant.fruits if f.maturite >= MUR]
        if not mures:
            continue
        plots = _plots_plante(plant, tile)
        d = sum(champ.get(r, c) for r, c in plots) / len(plots)
        for f in mures:
            demandes.append((plant, f, f.nombre * TAUX_PRISE * d))
    total = sum(dem for _p, _f, dem in demandes)
    if total <= 0.0:
        return []
    appetit = APPETIT * champ.total()
    facteur = min(1.0, appetit / total)

    log, prises = [], {}          # id(plante) → (plante, fruits pris)
    for plant, f, dem in demandes:
        pr, pc = plant.position
        prise = min(f.nombre, _entier(dem * facteur, seed, week,
                                      pr * 1009 + f.segment_id, pc))
        if prise <= 0:
            continue
        f.nombre -= prise
        p, n = prises.get(id(plant), (plant, 0))
        prises[id(plant)] = (p, n + prise)
    tampon = None
    for plant, n_pris in prises.values():
        plant.fruits = [f for f in plant.fruits if f.nombre > 0]
        log.append(f"    🐦 Merle : {n_pris} fruits pris sur "
                   f"{plant.name}@{plant.position}")
        pr, pc = plant.position
        n_graines = _entier(n_pris * P_TRANSIT, seed, week, pr * 1009 + 7, pc + 1)
        if n_graines == 0:
            continue
        father = find_father(plant, tile.plants, tile, eco, seed, week)
        if tampon is None:
            tampon = game_state.setdefault(TAMPON, [])
        tampon.append((plant.plant_class, child_genes(plant, father, seed, week),
                       child_expression(plant), n_graines, pr * 1009 + pc))
    return log


def grille_perchoirs(game_state: dict) -> list:
    """Plots du MONDE où un merle se pose : `[(tuile, r, c, poids), …]`, poids > 0.

    Poids d'un plot = 1 sous la couronne d'un ligneux vivant haut (≥ 150 cm) + 1 sous
    un mort debout (`stade_mort == "seche"` : son ancienne couronne, à défaut son
    pied) + 1 au pied d'un `Support` posé (tout type : tuteur, treillis, pergola,
    perchoir) + `eco.lisiere` si la ceinture est posée. Ordre stable (tuiles du
    monde, puis lignes, colonnes) → tirage reproductible."""
    grille = []
    for tile in game_state["tiles"]:
        eco = game_state["eco"][tile.tile_id]
        poids = {}

        def ajouter(plots, w=1.0):
            for rc in plots:
                poids[rc] = poids.get(rc, 0.0) + w

        couronnes, morts = set(), set()
        for p in tile.plants:
            if not getattr(p.plant_class, "ligneux", False):
                continue
            if p.is_alive and p.current_height >= HAUTEUR_PERCHOIR_CM:
                couronnes.update(rc for rc in p.foliar_plots if tile.is_valid_plot(*rc))
            elif not p.is_alive and p.stade_mort == "seche":
                plots = [rc for rc in p.foliar_plots if tile.is_valid_plot(*rc)]
                morts.update(plots or [p.position])
        ajouter(couronnes)
        ajouter(morts)
        ajouter({(min(tile.grid_rows - 1, max(0, int(s.y_cm // PLOT_CM))),
                  min(tile.grid_cols - 1, max(0, int(s.x_cm // PLOT_CM))))
                 for s in tile.supports})
        if eco.lisiere is not None:
            for r in range(tile.grid_rows):
                for c in range(tile.grid_cols):
                    ajouter([(r, c)], eco.lisiere.get(r, c))
        grille += [(tile, r, c, w) for (r, c), w in sorted(poids.items()) if w > 0.0]
    return grille


def merle_seme(game_state: dict, seed: int, week: int) -> list:
    """Vide le tampon : chaque graine tombe sur un perchoir du monde (tirage par
    hash pondéré par `grille_perchoirs`), en grain sauvage `origine="merle"`. Le
    plafond par plot (①) peut refuser un grain : il est perdu. Sans perchoir nulle
    part, toutes les graines sont perdues. Appelé APRÈS la boucle des tuiles."""
    tampon = game_state.pop(TAMPON, None)
    if not tampon:
        return []
    grille = grille_perchoirs(game_state)
    if not grille:
        return []
    cumul, acc = [], 0.0
    for _t, _r, _c, w in grille:
        acc += w
        cumul.append(acc)
    poses = 0
    for cls, genes, expr, n, sel in tampon:
        for k in range(n):
            cible = _hash_noise(seed, week * _CANAL + 1, sel, k) * acc
            i = next((j for j, v in enumerate(cumul) if v > cible), len(cumul) - 1)
            tile, r, c, _w = grille[i]
            grain = grain_sauvage(cls, genes, expr, "merle", week, None, None)
            poses += deposer_grain_sauvage(tile, r, c, grain)
    return [f"  🐦 Merle : {poses} graine(s) semée(s) sous les perchoirs"] if poses else []
