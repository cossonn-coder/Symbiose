"""
SYMBIOSE — sim/monde_complet.py
OUVERTURE du monde de jeu `full`/`propre` (D140 C.1-C.3, sprint DÉPART DU JARDIN ③,
docs/vegetal/genetique/conception_depart_jardin.md §2 C).

Responsabilité : à l'INIT, amener le jardin de `main.build_world_full` à l'état d'un
jardin qui VIT déjà quand le joueur arrive, fin mai :
  1. au moins UNE plante MATURE de chaque espèce du catalogue (52), chacune posée
     dans une tuile à sa niche (`PLACEMENTS`) ;
  2. tous les arbres pré-vieillis à l'âge de LEUR première fructification
     (`maturity_years`, au moins `AGE_ARBRES_DEMO`) — structure comprise ;
  3. quelques graines déjà semées en terre (`SEMIS_OUVERTURE`) ;
  4. quelques pots de tendres DANS la maison (`POTS_INTERIEUR`, départ du jardin ④) :
     semés à l'abri en mars, ils attendent d'être repiqués (`repiquer`).

📖 Pédagogie (Nico) — pourquoi « pré-croître » plutôt que dérouler la simulation ?
  Dérouler 30 ans de ticks pour avoir un hêtre adulte coûterait des heures. Ici on
  appelle la même morphogénèse que le tick (`grow_plant`, via `pre_croitre`) en
  boucle, HORS tick, sans champs écologiques : l'arbre a la charpente de son âge,
  mais le sol, la faune et la concurrence démarrent à l'ouverture. C'est le patron
  des bancs (`bancs/planche_especes._poser_adulte`) appliqué au monde de jeu.

📖 Continuité du calendrier : la pré-croissance déroule les semaines 1..N·52 + les
  semaines du printemps déjà écoulées (1..SEMAINE_OUVERTURE−1) — la partie démarre à
  la semaine suivante, sans trou dans le cycle saisonnier des structures.

Aucun bonus (philo #2) : on compose l'état initial du monde, les plantes ne sont
protégées de rien. Déterministe (philo #3) : table fixe + semis fondateurs seedés.
Hors tick, hors golden : le smoke (`tests/test_golden.build_world`) et la démo
`main.py` n'appellent jamais ce module (seul `cmd_init` des configs `full`/`propre`).
"""

from __future__ import annotations

from plants import PLANT_CATALOGUE, PERENNIAL_CATALOGUE
from plants.perennials import PerennialWoody
from fields.seedbank import GrainEnAttente
from sim.seeds import semer_fondateur
from sim.precroissance import pre_croitre
from sim.growth import grow_plant
from sim.reproduction import is_seed_bearing
from world import make_container, planter_dans

# Ouverture juste APRÈS les saints de glace (≈ 22 mai) : la fenêtre « Gelée
# tardive » de `sim/weather.py` couvre s2-s9 (D140 C.1). Le smoke garde s1.
SEMAINE_OUVERTURE = 10

# Âge plancher des arbres (AUTOMNE VISIBLE §3.1 : une couronne). Chaque espèce prend
# max(plancher, maturity_years) → le pommier (5 ans) reste à 11 et noue au 1er été ;
# le chêne a 25 ans, le hêtre 30 — ils occupent leur tuile, c'est le réel.
AGE_ARBRES_DEMO = 11.0

# Herbacées : un an de pousse donne le squelette d'adulte (patron `planche_especes`,
# validé aux silhouettes) ; les lianes vivaces ligneuses (lierre, jasmin) ont besoin de
# trois ans. Vivaces et bisannuelles sont dans leur 2ᵉ printemps (la bisannuelle a
# passé son an 1 en rosette : sa hampe est permise, `_bolt_bloque`).
ANS_HERBACEE = 1.0
ANS_LIANE = 3.0

# Une plante MATURE par espèce absente à maturité du monde de `build_world_full` :
# (clé catalogue, tuile, ligne, colonne). Plots LIBRES (vérifié par le test du monde
# full) : `plant_garden` n'occupe que 8 plots des lignes 0..5 / colonnes 0..6 ; la
# tuile S a son pommier (0,7) et sa planche paillée (lignes 2..8, colonnes 9..12) ;
# NE a sa mare (lignes 6..10, colonnes 3..7) ; SO/O/SE ont leur caduc de démo.
# Les arbres sont gardés hors des angles de tuile (un arbre d'angle a moins de plots
# où puiser, cf. sim/mare_initiale.py) et hors de portée de la nappe de ceinture.
PLACEMENTS = [
    # --- Arbres : grands au NORD (leur ombre, portée vers le nord, sort du jardin) ---
    ("chene",      "NO",  8, 5),    # argile profonde, coin nord-ouest
    ("hetre",      "N",   8, 8),    # tolère l'ombre de la maison (sciaphile 1,3)
    ("noyer",      "E",  11, 5),    # isolé dans sa tuile (juglone : il tient ses voisins à distance)
    ("noisetier",  "O",   7, 8),    # sous-bois de lisière, mi-ombre
    ("sapin",      "SO",  4, 9),    # sable acide (pH 5,8, sa fenêtre 5,5 ± 1,3)
    ("saule",      "NE",  8, 2),    # rive ouest de la mare, sol gorgé (asphyxie 3)
    ("figuier",    "SE",  4, 8),    # coin sud-est, plein soleil et chaleur
    # --- Ombre et mi-ombre : au nord de la maison et sous le hêtre ---
    ("violette",   "N",   6, 8),    # sous le hêtre, côté nord (sciaphile 1,6)
    ("lierre",     "N",   8, 9),    # au pied du hêtre (sciaphile 1,4)
    ("framboisier", "N",  9, 13),   # lisière
    ("menthe",     "N",   9, 3),    # fraîcheur
    ("consoude",   "N",  10, 6),
    ("ortie",      "N",   7, 14),   # nitrophile, coin de jardin
    # --- Acidophile : sable, à côté du sapin ---
    ("myrtille",   "SO",  5, 8),
    # --- Potager mûr, plein sud (tuile S, colonnes 13..15) ---
    ("tomate",     "S",   0, 13), ("poivron",   "S",  0, 15),
    ("basilic",    "S",   1, 14), ("haricot",   "S",  2, 13),
    ("courgette",  "S",   2, 15), ("tournesol", "S",  3, 14),
    ("carotte",    "S",   4, 13), ("mache",     "S",  4, 15),
    ("fraisier",   "S",   5, 14), ("ail",       "S",  6, 13),
    ("bourrache",  "S",   6, 15), ("phacelie",  "S",  7, 14),
    ("moutarde",   "S",   8, 13), ("achillee",  "S",  8, 15),
    ("trefle",     "S",   9, 14),
    ("jasmin",     "S",  10, 7),    # grimpante de plein soleil
    # --- Aromatiques calcicoles : argile (pH 7,0), sud-est ensoleillé ---
    ("thym",       "SE",  9, 8), ("lavande",   "SE", 10, 9),
    # --- Céréales à paille et chanvre : SE, lignes du bas ---
    ("ble",        "SE",  7, 8), ("seigle",    "SE",  8, 10),
    ("chanvre",    "SE", 10, 7),
    # --- Prairie, adventices et rudérales : tuile O (terre), sous le noisetier ---
    ("paturin",    "O",   9, 2), ("dactyle",   "O",  9, 4),
    ("fetuque",    "O",  10, 3), ("plantain",  "O", 10, 5),
    ("pissenlit",  "O",  11, 2), ("minette",   "O", 11, 4),
    ("bourse_pasteur", "O", 7, 3), ("molene",  "O",  14, 3),
    ("armoise",    "O",  14, 8),
    # --- Bambou traçant : isolé dans le coin libre de NO ---
    ("bambou",     "NO",  2, 9),
]

# Graines DÉJÀ semées en terre à l'ouverture (C.3) : au sud de la planche paillée de
# la tuile S. Même structure que le geste `planter` (`GrainEnAttente`), semées la
# semaine d'avant ; la levée suit `bell(T_sol)`. Haricot et courgette = tendres (lèvent
# sur sol chaud), carotte et phacélie = semis de pleine terre ordinaires.
SEMIS_OUVERTURE = [("haricot", 9, 9), ("haricot", 9, 10), ("courgette", 10, 9),
                   ("carotte", 9, 11), ("carotte", 9, 12), ("phacelie", 10, 11)]


# Pots de semis d'intérieur à l'ouverture (C.4) : les trois tendres qu'on sème au chaud
# en mars, sur le rebord de la façade SUD de la maison (emprise 600..1400 cm, mur sud
# à y = 1400). Godet de terreau de 2 L. (clé catalogue, x_cm, y_cm) monde.
POTS_INTERIEUR = [("tomate", 900.0, 1375.0), ("basilic", 1000.0, 1375.0),
                  ("poivron", 1100.0, 1375.0)]
VOLUME_GODET = 2.0
# Semaines passées en pot avant l'ouverture : semés début mars (≈ s2). La pousse en pot
# est TICKÉE (même `Container.tick` que pendant la partie) : lumière de fenêtre, pièce
# tempérée. Le tick de pot n'avance pas les stades → plant posé au 2ᵉ stade (jeune).
SEMAINES_EN_POT = 8
STADE_PLANT = 0


def pots_interieur(house, seed: int, semaine: int = SEMAINE_OUVERTURE) -> list:
    """Les pots de tendres dans la maison à l'ouverture (liste `game_state["containers"]`).
    Chaque plant a poussé `SEMAINES_EN_POT` semaines dans son pot, à l'intérieur."""
    pots = []
    for cle, x, y in POTS_INTERIEUR:
        ctn = make_container("pot", "terreau", VOLUME_GODET, x, y,
                             container_id=f"semis_{cle}")
        plant = planter_dans(ctn, PLANT_CATALOGUE[cle])
        plant.current_stage = STADE_PLANT
        for w in range(semaine - SEMAINES_EN_POT, semaine):
            ctn.tick("printemps", seed, w, house=house)
        pots.append(ctn)
    return pots


def _classe(cle: str) -> type:
    return PLANT_CATALOGUE.get(cle) or PERENNIAL_CATALOGUE[cle]


def _ans_arbre(cls) -> float:
    return max(AGE_ARBRES_DEMO, float(cls.maturity_years))


def _pre_vieillir_arbre(plant, seed: int, semaine: int) -> None:
    """Arbre fondateur → âge de première fructification, structure de cet âge."""
    ans = _ans_arbre(plant.plant_class)
    pre_croitre(plant, seed, ans + (semaine - 1) / 52.0)
    plant.age_years = ans


def _mettre_adulte(plant, seed: int, semaine: int) -> None:
    """Herbacée posée → dernier stade (reproductrice) + squelette d'adulte.
    `age_weeks` reste 0 (semaines DANS le stade, comme `advance_stage`)."""
    cls = plant.plant_class
    plant.current_stage = len(cls.growth_stages) - 1
    ans = ANS_LIANE if cls.procedural_growth and cls.ligneux else ANS_HERBACEE
    n = int(round(ans * 52)) + semaine - 1
    if cls.procedural_growth:
        pre_croitre(plant, seed, n / 52.0)
    else:                                  # `pre_croitre` ne fait rien pour elles :
        for w in range(1, n + 1):          # leur structure sert aux fruits/grimpe
            grow_plant(plant, seed, w)
    plant.age_years = ans


def ouvrir_monde_complet(tiles: list, seed: int,
                         semaine: int = SEMAINE_OUVERTURE) -> None:
    """Pose les espèces manquantes adultes, pré-vieillit TOUS les arbres et sème les
    graines d'ouverture. Mute `tiles` (le monde de `build_world_full`)."""
    par_id = {t.tile_id: t for t in tiles}
    poses = set()
    for cle, tuile, r, c in PLACEMENTS:
        p = semer_fondateur(par_id[tuile], _classe(cle), r, c, seed)
        if p is not None:
            poses.add(id(p))
    for t in tiles:
        for p in t.plants:
            if issubclass(p.plant_class, PerennialWoody):
                _pre_vieillir_arbre(p, seed, semaine)
            elif id(p) in poses:
                _mettre_adulte(p, seed, semaine)
    s_tile = par_id["S"]
    for cle, r, c in SEMIS_OUVERTURE:
        s_tile.grains_en_attente.setdefault((r, c), []).append(
            GrainEnAttente(species=cle, cultive=True, player="joueur_1",
                           semaine_depot=semaine - 1))


def especes_matures(tiles: list) -> set[str]:
    """Clés catalogue des espèces qui ont au moins un pied VIVANT en âge/stade de
    porter graine (`is_seed_bearing`) — lu par le garde-fou du monde full."""
    cle_de = {v: k for k, v in {**PLANT_CATALOGUE, **PERENNIAL_CATALOGUE}.items()}
    return {cle_de[p.plant_class] for t in tiles for p in t.plants
            if p.is_alive and p.plant_class in cle_de and is_seed_bearing(p)}
