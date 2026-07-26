"""
SYMBIOSE — fields/population/spec.py
Schémas data-driven : `TrophicSpec` (une guilde) et `PollinatorSpec` (un type de
pollinisateur). Extrait de `population.py` (scission /refactor 2026-06-30).
"""
from dataclasses import dataclass
from typing import Callable

from fields.foragers import ForagerParams
from fields.lifecycle import LifeCycleBridge
from fields.population.constants import (
    DEF_RESOURCE_W, DEF_HABITAT_W, DEF_PRED_W, DEF_DISTURB_W,
    POP_INERTIA, POP_INERTIA_DECAY, DEF_DAYLEN_MIN, DEF_DAYLEN_FULL,
)


@dataclass(frozen=True)
class TrophicSpec:
    """
    Décrit UNE guilde de façon data-driven (docs/faune/vie_macro/conception_vie_macro.md §2.1) :
      - resource_fn : (eco, tile, plants) → grille [rows][cols] ∈ [0,1]
                      = le `qi_local` trophique (ce dont la guilde se nourrit).
      - habitat_fn  : (eco, tile, plants) → grille [rows][cols] ∈ [0,1]
                      = plancher persistant (nectar, refuge, sol non perturbé…).
      - predators   : noms des champs de population qui PRÉDATENT cette guilde
                      (lus dans eco.populations au tick — puits biotique).
      - salt        : canal _hash_noise DÉDIÉ pour les positions de sprites
                      (décorrélé des autres guildes et des tirages du tick).
      - signal_fn   : (eco, tile, plants) → grille [rows][cols] ≥ 0, terme ADDITIF
                      optionnel à la capacité (attraction par le fruit tombé, ④).
                      None (défaut) = pas de signal → capacité inchangée (golden
                      neutre pour les guildes sans fruit : pollinisateur, vers).
    Les pondérations ont des défauts de module, surchargeables par guilde.

    `category` (modèle B, docs/faune/vie_macro/conception_faune_dediee.md §1) : la GUILDE rétrogradée en
    ÉTIQUETTE. Plusieurs espèces nommées partageront une même catégorie
    (ravageur / auxiliaire / detritivore) ; les consommateurs qui raisonnaient
    « par guilde » (santé des plantes, vigueur macro) lisent désormais l'AGRÉGAT
    de la catégorie (`EcoFields.category_density` / `category_fields`). Tant qu'une
    catégorie n'a qu'un membre (état ④a), l'agrégat == le champ → golden NEUTRE.
    """
    name: str
    category: str
    salt: int
    resource_fn: Callable
    habitat_fn: Callable
    predators: tuple[str, ...] = ()
    signal_fn: Callable | None = None
    resource_w: float = DEF_RESOURCE_W
    habitat_w: float = DEF_HABITAT_W
    pred_w: float = DEF_PRED_W
    disturb_w: float = DEF_DISTURB_W
    # Poids de l'effet de LISIÈRE dans la capacité (sprint PÉRIPHÉRIE ③, D73, §4.2) :
    # ce que CETTE guilde tire du champ du milieu `eco.lisiere`. Le milieu porte
    # l'information, la réponse est déclarée par espèce — un carabe hiverne dans
    # l'ourlet d'une lisière, un puceron s'en moque. DÉFAUT 0.0 : toute guilde qui ne
    # le déclare pas ignore la lisière, terme non calculé → capacité bit-identique
    # (golden INTACT). C'est ce défaut qui empêche le « bonus déguisé » (philo #2).
    lisiere_w: float = 0.0
    inertia: float = POP_INERTIA               # inertie de MONTÉE
    inertia_decay: float = POP_INERTIA_DECAY   # inertie de DÉCRUE (§4)
    # Fenêtre phénologique de la guilde (heures de jour) : porte saisonnière §3.
    daylen_min: float = DEF_DAYLEN_MIN
    daylen_full: float = DEF_DAYLEN_FULL
    # Métadonnée d'ENCYCLOPÉDIE (④e, CONCEPTION_FAUNE_DEDIEE §1.1) — DONNÉE PURE,
    # jamais lue par `tick` → golden NEUTRE. `blurb` = texte naturaliste ; rendu = ⑥.
    # `interconnexions` = graphe relationnel §3 (source : fields/faune_encyclo.py).
    blurb: str = ""
    interconnexions: tuple[str, ...] = ()


@dataclass(frozen=True)
class PollinatorSpec:
    """Type de pollinisateur, déclaré PAR DONNÉE (§E.1). Le `PopulationField`
    générique le ticke comme une guilde ordinaire : on n'expose ici que ce qui
    DIFFÈRE d'une guilde trophique.

      - attractivite        : préférence florale PAR FAMILLE botanique (le nectar
                              perçu par CE type) ; alimente la resource_fn (§C.1).
      - attractivite_defaut : préférence d'une famille non listée (fleur générique).
      - habitat_fn          : terme-source d'habitat (rondelle dédiée).
      - daylen_min/full     : fenêtre d'activité photopériodique (porte des guildes).
      - forager             : paramètres d'agent butineur (§F, tronçon ③).
      - bridge              : pont de cycle de vie larvaire optionnel (§D, tronçon
                              ⑤) — `None` pour l'abeille (nid hors sol, pas de larve
                              au sol). Source UNIQUE des ponts (build_lifecycle_bridges).
      - lisiere_w           : poids d'effet de lisière, comme pour une guilde
                              trophique (périphérie ③). Défaut 0.0 ; seul le syrphe
                              le porte (il hiverne hors des planches).
    """
    name: str
    salt: int
    attractivite: dict
    attractivite_defaut: float
    habitat_fn: Callable
    daylen_min: float
    daylen_full: float
    forager: ForagerParams
    bridge: LifeCycleBridge | None = None
    lisiere_w: float = 0.0
