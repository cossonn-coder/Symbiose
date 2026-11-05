"""
SYMBIOSE — tests/bancs/test_liane_relais.py
Oracle du sprint HOUPPIER ② : au sommet de son appui, une liane en trouve un autre, ou elle
plie et sa partie pendante tombe en litière `bois`, puis repart. Levier inerte sans
`rigidite_tige`. Le banc tourne 3 ans, jamais plus (déterminisme vérifié sur 1 an).

Usage (depuis data/code/) : python3 -m tests.bancs.test_liane_relais
"""
import hashlib

from fields import init_eco
from plants import Bean, Ivy
from plants.base import Segment
from sim.engine import branches
from sim.grimpe import relais_appui
from sim.growth import grow_plant
from sim.growth.geometrie import _tip
from sim.growth.tige_libre import apex_plies, effondrer, longueurs_libres
from tools.simserver.server import SimServer
from world import Support, Tile, MUR

SEMAINES = 156
# Un apex passé L_crit finit son segment, et le premier segment courbé monte encore un peu.
ARC_CM = 2 * 20.0        # 2 × `emit_length_cm`


def _monter(semaines=SEMAINES, a_chaque_semaine=None):
    serveur = SimServer()
    assert serveur.cmd_init({"cmd": "init", "seed": 42, "config": "liane_relais"})["ok"]
    for semaine in range(1, semaines + 1):
        serveur.cmd_step_week({"cmd": "step_week"})
        if a_chaque_semaine is not None:
            a_chaque_semaine(semaine, serveur.engine.tiles[0])
    return serveur.engine.tiles[0]


def _liane(tuile, nom, x, y):
    return next(p for p in tuile.plants
                if p.name == nom and round(p.x_cm) == x and round(p.y_cm) == y)


def _zmax(plante):
    return max(_tip(s)[2] for s in plante.segments)


def test_banc():
    plis = {}
    coupes = {}
    depassements = []
    effondrer_vrai = branches.effondrer

    def compter(plante):
        tombes = effondrer_vrai(plante)
        if tombes:
            coupes[(plante.name, plante.y_cm)] = coupes.get((plante.name, plante.y_cm), 0) + 1
        return tombes

    def relever(semaine, tuile):
        for nom, x, y in (("Lierre", 525, 825), ("Jasmin", 225, 825),
                          ("Lierre", 225, 1175), ("Jasmin", 525, 1175)):
            plante = _liane(tuile, nom, x, y)
            h = plante.support[1] if plante.support else plante.plant_class.hauteur_autoportante
            libre, crit = longueurs_libres(plante)
            tenue = max((c for c in crit if c != float("inf")), default=0.0)
            if _zmax(plante) > h + tenue + ARC_CM:
                depassements.append((semaine, nom, y, _zmax(plante), h, tenue))
            if apex_plies(plante):
                plis[(nom, y)] = plis.get((nom, y), 0) + 1

    branches.effondrer = compter
    try:
        tuile = _monter(a_chaque_semaine=relever)
    finally:
        branches.effondrer = effondrer_vrai

    # Le mur : le lierre y passe, le jasmin jamais (il reste au geste `palisser`).
    assert _liane(tuile, "Lierre", 25, 325).support[0] is MUR
    jasmin_mur = _liane(tuile, "Jasmin", 25, 625)
    assert isinstance(jasmin_mur.support[0], Support), jasmin_mur.support
    # L'arbre haut : les deux y passent.
    assert _liane(tuile, "Lierre", 275, 125).support[0].name == "Pommier"
    assert _liane(tuile, "Jasmin", 275, 475).support[0].name == "Pommier"
    # Appui ou non, la hauteur reste celle que permet L_crit.
    assert not depassements, depassements[:5]
    assert _zmax(_liane(tuile, "Lierre", 225, 1175)) < 200.0      # 320 cm au tronçon ①
    assert _zmax(_liane(tuile, "Jasmin", 525, 1175)) < 170.0      # 412 cm au tronçon ①
    # Elle plie, tombe et repart, sans retomber à chaque tick.
    assert plis.get(("Jasmin", 1175), 0) > 0, plis
    assert 0 < coupes.get(("Jasmin", 1175), 0) <= SEMAINES / 4, coupes
    assert any(s.is_apex for s in _liane(tuile, "Jasmin", 525, 1175).segments)
    print(f"OK banc sur {SEMAINES} semaines : relais mur et arbre, zmax bornée, "
          f"{coupes.get(('Jasmin', 1175))} effondrements du jasmin sans appui")


def _bois(eco, r, c):
    return sum(p.masse for p in eco.litiere[r][c] if p.tissu == "bois")


def _tige_dressee(cls, n_segments=30):
    """Pied posé à la main : une tige droite, seule, de `n_segments` × 20 cm, âgée."""
    tuile = Tile(tile_id="T", soil_type="terre", grid_rows=8, grid_cols=8)
    eco = init_eco("T", 8, 8, humidite=0.5, microbiome=0.3, soil_type="terre")
    plante = tuile.add_plant(cls, 2, 2)
    plante.segments = [
        Segment(parent=(i - 1) if i else None, base=(125.0, 125.0, 20.0 * i), dir=(0.0, 0.0, 1.0),
                length_cm=20.0, thickness_cm=1.0, age_weeks=200, auxin=0.0,
                is_apex=(i == n_segments - 1), has_bud=False)
        for i in range(n_segments)]
    return tuile, eco, plante


def test_effondrement_litiere_repousse():
    tuile, eco, plante = _tige_dressee(Ivy)
    plante.support = (Support("treillis", 125.0, 125.0, 180.0, "surface"), 180.0)
    log = branches.mort_des_branches(tuile, eco, "ete", 1, 1, 42, 0.0, False)
    assert any("effondrement" in ligne for ligne in log), log
    libre, crit = longueurs_libres(plante)
    assert max(libre) <= max(c for c in crit if c != float("inf"))
    assert any(s.has_bud for s in plante.segments), "un bourgeon sur le porteur"
    assert _zmax(plante) >= 180.0, "ce qui reste sous l'appui n'est pas touché"
    assert _bois(eco, 2, 2) > 0.0, "la tige tombe en litière `bois` à sa verticale"
    for semaine in range(1, 30):
        grow_plant(plante, 42, semaine)
    assert any(s.is_apex for s in plante.segments), "la tige repart"
    print("OK effondrement : litière, bourgeon, repousse")


def test_inerte_sans_rigidite():
    tuile, _, plante = _tige_dressee(Bean)
    haut = Support("tuteur", plante.x_cm, plante.y_cm, 900.0, "fin")
    tuile.supports.append(haut)
    plante.support = (Support("tuteur", 0.0, 0.0, 180.0, "fin"), 180.0)
    n = len(plante.segments)
    assert effondrer(plante) == [] and not apex_plies(plante) and len(plante.segments) == n
    relais_appui(plante, tuile, None, 4)
    assert plante.support[0] is not haut, "pas de relais pour une grimpante sans `rigidite_tige`"
    print("OK levier inerte sans `rigidite_tige`")


def test_relais_sans_id():
    """Deux appuis à égale distance : le départage ne doit pas dépendre de la mémoire."""
    tuile, _, plante = _tige_dressee(Ivy)
    bas = Support("treillis", 125.0, 125.0, 180.0, "surface")
    plante.support = (bas, 180.0)
    un = Support("treillis", 75.0, 125.0, 900.0, "surface")
    deux = Support("treillis", 175.0, 125.0, 900.0, "surface")
    tuile.supports.extend([bas, un, deux])
    relais_appui(plante, tuile, None, 4)
    assert plante.support[0] is un and plante.relais == (un, 75.0, 125.0)
    print("OK départage du relais par rang de pose")


def test_determinisme():
    def empreinte():
        tuile = _monter(semaines=52)
        lianes = [p for p in tuile.plants if p.name in ("Lierre", "Jasmin")]
        return hashlib.sha256(repr([[(s.parent, s.base, s.dir, s.length_cm) for s in p.segments]
                                    for p in lianes]).encode()).hexdigest()
    assert empreinte() == empreinte()
    print("OK rejeu identique sur 52 semaines")


if __name__ == "__main__":
    test_inerte_sans_rigidite()
    test_relais_sans_id()
    test_effondrement_litiere_repousse()
    test_banc()
    test_determinisme()
