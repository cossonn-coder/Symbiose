"""
SYMBIOSE — tests/bancs/test_verger_mur.py
Oracle du sprint HOUPPIER ③ : pommier, cerisier, figuier et noyer portent leurs fruits, mûrs
dans la fenêtre de leur fiche, et ceux qu'on ne cueille pas tombent en litière `fruit`.
Tomate, fraise, framboise et courgette gardent la durée commune `FRUIT_DMAT`.

Fenêtres : table du `calendrier.py`, 1ᵉʳ juin s11, 1ᵉʳ août s20, 1ᵉʳ sept. s24, 1ᵉʳ nov. s33.
Le banc tourne 3 ans, seed 42 ; les chiffres d'autres seeds sont consignés dans `00_etat.md`.

Usage (depuis data/code/) : python3 -m tests.bancs.test_verger_mur
"""
from calendrier import wiy_de
from fields import FRUIT_DMAT
from plants import Fig
from plants.catalogue import PLANT_CATALOGUE
from sim.engine import decompo
from tools.simserver.server import SimServer

SEMAINES = 156
FENETRES = {"Cerisier": (11, 20), "Pommier": (24, 33), "Figuier": (20, 33), "Noyer": (24, 33)}


def _monter():
    serveur = SimServer()
    assert serveur.cmd_init({"cmd": "init", "seed": 42, "config": "verger_mur"})["ok"]
    return serveur


def _relever(semaines=SEMAINES):
    """Par espèce : semaines de fruit mûr, de fruit sur l'arbre, et masse tombée au sol."""
    serveur = _monter()
    tuile = serveur.engine.tiles[0]
    eco = serveur.engine.game_state["eco"][tuile.tile_id]
    mur, porte, tombe = {}, {}, {}
    depot_vrai = eco.deposer_litiere
    plots = {p.position: p.name for p in tuile.plants}

    def depot(r, c, tissu, masse, *a, **k):
        if tissu == "fruit" and (r, c) in plots:
            tombe[plots[(r, c)]] = tombe.get(plots[(r, c)], 0.0) + masse
        depot_vrai(r, c, tissu, masse, *a, **k)

    eco.deposer_litiere = depot
    for semaine in range(1, semaines + 1):
        serveur.cmd_step_week({"cmd": "step_week"})
        for p in tuile.plants:
            if p.fruits:
                porte.setdefault(p.name, []).append(wiy_de(semaine))
                if any(f.maturite >= 1.0 for f in p.fruits):
                    mur.setdefault(p.name, []).append(wiy_de(semaine))
    return mur, porte, tombe


def test_fruits_dans_leur_fenetre():
    mur, porte, tombe = _relever()
    for nom, (debut, fin) in FENETRES.items():
        assert mur.get(nom), f"{nom} : aucun fruit mûr en 3 ans"
        assert min(mur[nom]) >= debut, f"{nom} : mûr dès s{min(mur[nom])}, avant s{debut}"
        assert max(porte[nom]) <= fin, f"{nom} : encore sur l'arbre en s{max(porte[nom])}, après s{fin}"
        assert tombe.get(nom, 0.0) > 0.0, f"{nom} : rien de tombé en litière `fruit`"
    print({nom: (min(mur[nom]), max(porte[nom]), round(tombe[nom], 2)) for nom in FENETRES})


def test_figuier_sans_autogamie():
    """Constat du kickoff : sans `self`, le figuier (`nectar` 0) ne nouerait jamais."""
    Fig.pollination_mode = "insect"
    try:
        _mur, porte, _tombe = _relever(52)
    finally:
        Fig.pollination_mode = "self"
    assert "Figuier" not in porte


def test_duree_par_defaut():
    for nom in ("tomate", "fraisier", "framboisier", "courgette"):
        assert PLANT_CATALOGUE[nom].fruit_semaines_maturation is None, nom
    assert decompo.FRUIT_DMAT == FRUIT_DMAT == 0.08


def test_determinisme():
    assert _relever(52) == _relever(52)


if __name__ == "__main__":
    test_fruits_dans_leur_fenetre()
    test_figuier_sans_autogamie()
    test_duree_par_defaut()
    test_determinisme()
    print("[test_verger_mur] PASS")
