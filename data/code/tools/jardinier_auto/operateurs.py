# SYMBIOSE — tools/jardinier_auto/operateurs.py
# Le CATALOGUE des OPÉRATEURS CRÉATIFS de l'automate (D87 tronçon ②, §2/§4). Là où
# le cœur réactif (diagnostic Liebig → regles → proposition) MAINTIENT le vivant en
# place, les opérateurs le font ADVENIR : ils comblent les trois gestes que Liebig
# ne déclenche jamais (aucun individu n'a un « déficit de graine plantée ») :
#   1. `acheter_magazine(sp)` — se procurer une graine par la voie magazine ;
#   2. `planter(sp)`          — semer une graine de banque à un plot libre ;
#   3. `favoriser_auxiliaire(sp)` — poser l'habitat pollinisateur d'une fruitière.
#
# Chaque opérateur = des fonctions PURES qui SONDENT l'état vivant du moteur (patron
# `est_atteignable`/`proposer` étendu) : une PRÉ-condition (« ce geste est-il
# faisable maintenant ? ») et une POST-condition (« qu'obtient-on ? », lue par
# `but_satisfait` / le placement rendu). AUCUNE écriture : la DÉCISION vit ici,
# l'EXÉCUTION est au tronçon ③. Déterminisme total (philo #3) : tout balayage passe
# par une clé de départage canonique, zéro RNG.
#
# Ce tronçon N'EST PAS branché dans la boucle → aucun effet sur un run → golden
# INTACT par construction (le smoke tourne sans joueur/objectif : no-op strict).

from __future__ import annotations
from typing import NamedTuple

from sim.magazine import magazine_offres, COUT_MAGAZINE
from sim.vigueur import MAX_BASE
from sim.vigueur_plante import maturite
from .diagnostic import MATURITE_MUR
from .objectifs import classe_cible
from .tutelle import sous_tutelle

# Priorité MODÉRÉE BASSE des gestes créatifs — bien SOUS les facteurs de survie de
# regles.py (10-20) → préemption survie (③) : le vivant en péril passe TOUJOURS
# d'abord, l'advenir ralentit sans jamais couper un soin. Constante nommée.
PRIO_CREATIF = 5

# Registre porté par un Plan créatif (champ `facteur` du dataclass `Plan` réutilisé,
# proposition.py). ≠ un facteur limitant de Liebig : c'est « faire ADVENIR la cible »,
# distinct du registre réactif « maintenir le vivant » — le tri de ③ les départage.
FACTEUR_ADVENIR = "advenir"

# Maturité d'un fruit à partir de laquelle il est jugé MÛR (récoltable). Le moteur
# fait mûrir un fruit jusqu'à 1.0, puis le laisse sur-mûrir jusqu'à MATURITE_CHUTE
# (1.3) avant chute (fields/ecofields/constants : FRUIT_DMAT « atteint 1.0 (mûr) »).
# On LIT ce repère du moteur, on n'ajoute AUCUNE donnée aux espèces (kickoff ②).
FRUIT_MUR = 1.0


class CibleCreative(NamedTuple):
    """Charge utile d'un Plan créatif, portée par `Plan.cible_obj` (dataclass réutilisé
    de proposition.py, mêmes champs — kickoff ②). `espece` = espèce à faire advenir ;
    `tile` = tuile-cible (None pour un achat, geste sans lieu) ; `(r, c)` = plot choisi
    pour `planter` (None sinon). Immuable, hashable, déterministe (philo #3)."""

    espece: str
    tile: object          # world.tile.Tile | None
    r: object             # int | None
    c: object             # int | None


# ---------------------------------------------------------------------------------
# POST-condition TERMINALE de l'objectif — « récoltable » TYPÉ ORGANE (C2, §2.1)
# ---------------------------------------------------------------------------------

def but_satisfait(plant, sp) -> bool:
    """La cible `recolter sp` est-elle ADVENUE sur `plant` (une cultivée vivante de
    `sp`) ? Post-condition TYPÉE ORGANE selon le profil reproducteur (C2) :
      - `fruitier=True`  → un FRUIT mûr présent (`fruits` avec `maturite ≥ FRUIT_MUR`) ;
      - `fruitier=False` → maturité VÉGÉTATIVE atteinte (`maturite(plant) ≥
        MATURITE_MUR`, = l'opportunité `organe_mur` que `recolter` sert déjà
        réactivement — diagnostic.py).
    Lecture PURE. `sp` sert de garde-fou : mauvaise espèce ou plante morte → False."""
    cls = classe_cible(sp)
    if cls is None or plant.plant_class is not cls or not plant.is_alive:
        return False
    if getattr(plant.plant_class, "fruitier", False):
        return any(f.maturite >= FRUIT_MUR for f in plant.fruits)
    return maturite(plant) >= MATURITE_MUR


# ---------------------------------------------------------------------------------
# Sondes d'état partagées (culture permanente C1, placement T5)
# ---------------------------------------------------------------------------------

def cultivees_vivantes(engine, sp, cultivees) -> list:
    """Les cultivées VIVANTES de l'espèce `sp` sous tutelle, en couples `(tile,
    plant)`, triées par clé totale `(tile_id, y_cm, x_cm)` (déterminisme, philo #3).
    Une FÉRALE de même espèce (plot hors du set `cultivees`) ne compte PAS : le
    déclencheur « advenir » raisonne en CULTURE permanente, pas en simple présence
    (C1/Q9). `len(...)` donne le compte `n_vivantes`. PURE."""
    cls = classe_cible(sp)
    if cls is None:
        return []
    paires = []
    for tile in engine.tiles:
        for plant in tile.plants:
            if plant.plant_class is cls and sous_tutelle(plant, tile.tile_id, cultivees):
                paires.append((tile, plant))
    paires.sort(key=lambda tp: (tp[0].tile_id, tp[1].y_cm, tp[1].x_cm))
    return paires


def plot_libre(engine):
    """Premier plot LIBRE en balayage déterministe (T5, placement canonique) :
    `engine.tiles` dans l'ordre de la liste, puis `(r, c)` croissant. LIBRE = aucune
    plante vivante dont l'empreinte couvre le plot (`plants_at` vide) ET aucun grain
    en attente (`(r, c) not in grains_en_attente`). Renvoie `(tile, r, c)` ou None si
    le monde est saturé. Aucune écriture — c'est une lecture (philo #3)."""
    for tile in engine.tiles:
        for r in range(tile.grid_rows):
            for c in range(tile.grid_cols):
                if tile.plants_at(r, c):
                    continue
                if (r, c) in tile.grains_en_attente:
                    continue
                return (tile, r, c)
    return None


# ---------------------------------------------------------------------------------
# Les trois OPÉRATEURS — pré-conditions sondées (pas de post-écriture ici)
# ---------------------------------------------------------------------------------

def _vigueur_courante(gs, player) -> float:
    """Solde de Vigueur du joueur — LECTURE défensive qui ne CRÉE aucune clé (pur,
    golden neutre). Absent → MAX_BASE (jamais atteint quand un objectif est actif :
    la couche Vigueur existe déjà)."""
    return gs.get("vigueur", {}).get(player, {}).get("courante", MAX_BASE)


def pre_acheter_magazine(gs, sp, player) -> bool:
    """Pré-condition de `acheter_magazine(sp)` : `sp` figure dans l'offre courante du
    magazine (palier 3 d'un membre de sa famille — `magazine_offres`) ET la Vigueur
    couvre `COUT_MAGAZINE`. Post (à l'exécution ③) : une graine `sp` en banque. PURE."""
    return (sp in magazine_offres(gs, player)
            and _vigueur_courante(gs, player) >= COUT_MAGAZINE)


def pre_planter(engine, sp):
    """Pré-condition de `planter(sp)` : une graine `sp` dort en banque-joueur ET un
    plot libre déterministe existe. Renvoie le PLACEMENT `(tile, r, c)` (= la
    post-condition « où la cultivée adviendra ») quand la pré est vraie, sinon None.
    On renvoie le plot DÉJÀ calculé pour que l'appelant ne le RECALCULE pas (mémo,
    règle « pas de recalcul dans un tick »). PURE."""
    bank = engine.game_state.get("player_seed_bank")
    if bank is None or bank.count(sp) == 0:
        return None
    return plot_libre(engine)


def zone_fruitiere_sans_habitat(engine, sp, cultivees):
    """Cible de `favoriser_auxiliaire(sp)` (C4, timing « au plus tôt ») : la TUILE de
    la première cultivée `fruitier` de `sp` (ordre canonique de `cultivees_vivantes`)
    dont la tuile ne porte PAS encore de rondelle `auxiliaire`. Habitat posé AVANT
    floraison → pollinisateurs établis à temps (one-shot déterministe, pas calé sur
    le pic). None si `sp` n'est pas fruitière, si aucune cultivée, ou si l'habitat
    est déjà là. PURE."""
    cls = classe_cible(sp)
    if cls is None or not getattr(cls, "fruitier", False):
        return None
    for tile, _plant in cultivees_vivantes(engine, sp, cultivees):
        if tile.get_rondelle_count("auxiliaire") == 0:
            return tile
    return None
