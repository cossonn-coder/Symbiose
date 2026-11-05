"""
SYMBIOSE — tests/bancs/test_bancs_grimpe.py
Oracle des bancs de grimpe (`grimpantes`, `accroches_adultes`) : retour F5 du 2026-11-05,
« aucune plante n'est présente » et aucune graine pour tester. Les pieds posés doivent
vivre assez longtemps pour être regardés (0 vivant sur 9 à +5 et +7 semaines avant la
coupe de l'herbivorie, D127) et une graine de la banque doit pouvoir se semer.

Usage (depuis data/code/) : python3 -m tests.bancs.test_bancs_grimpe
"""
from tools.simserver.server import SimServer

SEMAINES = 12
GRAINES = {"haricot", "tomate", "lierre", "jasmin", "tournesol"}


def _vivants(serveur):
    return [p for p in serveur.cmd_snapshot({})["snapshot"]["plants"] if not p.get("dead")]


def test_banc(nom):
    serveur = SimServer()
    assert serveur.cmd_init({"cmd": "init", "seed": 42, "config": nom})["ok"]
    assert set(serveur.cmd_snapshot({})["snapshot"]["player"]["seeds"]) == GRAINES, nom
    for _ in range(SEMAINES):
        serveur.cmd_step_week({"cmd": "step_week"})
    vivants = _vivants(serveur)
    assert len(vivants) == 9, f"{nom} : {len(vivants)} vivants sur 9 à +{SEMAINES} semaines"
    print(f"OK {nom} : 9 vivants sur 9 à +{SEMAINES} semaines, 5 espèces en banque")


def test_semer():
    serveur = SimServer()
    serveur.cmd_init({"cmd": "init", "seed": 42, "config": "accroches_adultes"})
    tuile = serveur.engine.tiles[0].tile_id
    avant = serveur.cmd_snapshot({})["snapshot"]["player"]["seeds"]["haricot"]
    rep = serveur.cmd_action({"cmd": "action", "verb": "planter",
                              "target": {"tile": tuile, "x_cm": 575.0, "y_cm": 75.0},
                              "params": {"species": "haricot"}})
    assert rep["ok"] and rep["result"]["applied"], rep.get("result", rep)
    assert rep["snapshot"]["player"]["seeds"]["haricot"] == avant - 1
    print("OK semis d'un haricot depuis la banque du banc")


if __name__ == "__main__":
    test_banc("accroches_adultes")
    test_banc("grimpantes")
    test_semer()
