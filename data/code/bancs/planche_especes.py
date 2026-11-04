"""
SYMBIOSE — bancs/planche_especes.py
Banc « planche des espèces » (sprint FORMES DES PLANTES ①) : les 40 espèces de
`PLANT_CATALOGUE`, UN pied adulte par emplacement, séparés, pour capturer et comparer
leurs silhouettes (`tools/mesure_silhouettes.py`) et les regarder au F5.

Pure COMPOSITION de l'état moteur, aucune mécanique → golden NEUTRE (jamais monté
pour smoke/full).

📖 Pédagogie — où poser 40 pieds sans que rien ne masque rien ?
  La vue iso dessine du nord (haut de l'écran) vers le sud (bas) : ce qui est au sud
  passe devant. La maison ne peut donc cacher que ce qui est DERRIÈRE elle : la bande
  x ≥ 1400 ou y ≥ 1400 (les deux bras d'un L, tournés vers la caméra) ne l'est jamais.
  Dans ce L, on trie : les plus grandes au nord, les plus petites au sud, pour qu'une
  haute plante ne recouvre jamais sa voisine de derrière. Pas de 2 m entre pieds
  → à l'écran, un voisin d'axe est à (78, 39) px internes et un voisin de diagonale
  à (0, 78). `tests/bancs/test_planche_especes.py` vérifie les boîtes à l'adulte.

📖 Fleurs et fruits : sans forçage, peu d'espèces fleurissent à une semaine donnée
  (chacune a son seuil thermique) et un fruit ne se noue qu'après la floraison. Comme
  `verger_floraison`, on POSE donc `floraison` à 1 et des fruits mûrs sur les fruitières,
  sans aucun tick : c'est l'état « tout est visible » d'une planche d'herbier, pas
  une scène phénologique. Procédé et bilan du banc court : `00_etat.md` du sprint.

Capture : `--capture-semaines=0`, pour rester à cet état posé (un tick relâcherait
`floraison` vers sa cible). Morphogénèse pure (`grow_plant`, patron `foret_ports`) sur
un an : le squelette réel d'une espèce non migrée, sans mort hydrique ni concurrence.
"""
from __future__ import annotations

from plants import Fruit, organ_sites
from plants.catalogue import PLANT_CATALOGUE
from fields import FRUIT_MASSE
from sim.growth import grow_plant
from .base import build_banc_tile, monde, vieillir

# Du plus haut au plus bas [`height_cm` au dernier stade] : l'ordre des emplacements,
# du nord au sud. Toute espèce ajoutée au catalogue doit entrer ici (test).
ESPECES_PAR_TAILLE = (
    "chanvre", "bambou", "tournesol", "haricot", "seigle", "molene", "framboisier",
    "armoise", "ble", "ortie", "dactyle", "lierre", "jasmin", "tomate", "poivron",
    "phacelie", "bourrache", "moutarde", "carotte", "lavande", "consoude", "ail",
    "courgette", "basilic", "achillee", "myrtille", "bourse_pasteur", "menthe",
    "minette", "paturin", "pissenlit", "thym", "fetuque", "plantain", "mache",
    "trefle", "fraisier", "violette", "drosera", "sphaigne",
)

PAS_CM = 200                  # 2 m entre pieds, cf. en-tête
BRAS_CM = 1400                # début des deux bras du L (bord de la maison)
COTE_MONDE_CM = 2000
MARGE_CM = 25                 # centre du premier plot du bras
ANS_ADULTE = 1.0              # un an de pousse : `grow_plant` a son squelette d'adulte
ANS_LIANE = 3.0               # lierre, jasmin : vivaces procédurales, un an est un semis
MATURITE_FRUIT_POSE = 1.0     # fruit mûr, sous `MATURITE_CHUTE`
GRAINE_FORME = 0              # graine de forme fixe (philo #3)


def _emplacements() -> list[tuple[int, int]]:
    """Plots-centres du L, triés du nord au sud (x + y croissant = haut de l'écran
    vers le bas), puis d'ouest en est pour un ordre total."""
    lignes = range(BRAS_CM + MARGE_CM + PAS_CM // 2, COTE_MONDE_CM, PAS_CM)
    longs = range(MARGE_CM + PAS_CM // 2, COTE_MONDE_CM, PAS_CM)
    points = {(x, y) for x in lignes for y in longs} | {(x, y) for y in lignes for x in longs}
    return sorted(points, key=lambda p: (p[0] + p[1], p[0]))


# Table espèce → (x_cm, y_cm) monde : pied exact de chaque espèce, pour cadrer ses
# captures (`capture_vm.sh -c x,y`).
POSITIONS: dict[str, tuple[int, int]] = dict(zip(ESPECES_PAR_TAILLE, _emplacements()))


def _poser_adulte(tuile, cls, x: int, y: int):
    """Pose `cls` au pied (x, y) monde, dernier stade, squelette d'un an ou plus."""
    plante = tuile.add_plant(cls, int((y - tuile.origin_y_cm) // 50),
                             int((x - tuile.origin_x_cm) // 50))
    plante.current_stage = len(cls.growth_stages) - 1
    ans = ANS_LIANE if cls.procedural_growth and cls.ligneux else ANS_ADULTE
    vieillir(plante, ans)                       # âge + pré-croissance des procédurales
    if not cls.procedural_growth:               # `pre_croitre` ne fait rien pour elles
        for semaine in range(1, int(ans * 52) + 1):
            grow_plant(plante, GRAINE_FORME, semaine)
    return plante


def _forcer_fleurs_fruits(plante) -> None:
    """État « tout est visible » : pleine fleur, et fruits mûrs sur les fruitières."""
    plante.floraison = 1.0
    if plante.plant_class.fruitier:
        plante.fruits = [Fruit(seg_id, MATURITE_FRUIT_POSE, FRUIT_MASSE)
                         for seg_id, _pos in organ_sites(plante)]


def composer(forcer: bool = True):
    """Monde de la planche. `forcer=False` : sans fleurs ni fruits posés, pour le banc
    court qui vérifie ce qui s'allume tout seul (cf. `00_etat.md`)."""
    sud, eco_sud = build_banc_tile("PLANCHE_SUD", "terre", 12, 40, 0.0, float(BRAS_CM),
                                   humidite=1.2, fertilite=1.2, microbiome=0.6)
    est, eco_est = build_banc_tile("PLANCHE_EST", "terre", 28, 12, float(BRAS_CM), 0.0,
                                   humidite=1.2, fertilite=1.2, microbiome=0.6)
    for nom, (x, y) in POSITIONS.items():
        tuile = sud if y >= BRAS_CM else est
        plante = _poser_adulte(tuile, PLANT_CATALOGUE[nom], x, y)
        if forcer:
            _forcer_fleurs_fruits(plante)
    # Banc ISOLÉ (patron `floraison_saisons`) : aucune levée spontanée sur la planche.
    for eco in (eco_sud, eco_est):
        eco.seed_bank.germination_candidates = lambda *a, **k: []
    return monde([sud, est], {sud.tile_id: eco_sud, est.tile_id: eco_est})


def planche_especes():
    """Banc « planche des espèces » : les 40 adultes séparés, fleurs et fruits posés.
    Instrument de mesure et d'observation F5 ; pas d'oracle à seuil."""
    return composer()
