"""
SYMBIOSE — tests/test_perf_sonde.py
La sonde du rapport perf (touche C) distingue bien ce qu'elle promet de distinguer.

Lancement (depuis data/code/) : python3 -m tests.test_perf_sonde
"""
from __future__ import annotations

import gc
import json
import time

from tools.simserver.perf import rss_mo
from tools.simserver.perf_tick import SondeTick
from tools.simserver.server import SimServer


def check(nom, ok, detail=""):
    print(f"  {'OK ' if ok else 'ÉCHEC'} {nom} {detail}")
    assert ok, nom


def _calcule_longtemps():
    fin = time.perf_counter() + 0.4
    while time.perf_counter() < fin:
        sum(range(1000))


def tick_semaine():
    """Même nom que la méthode du moteur : c'est lui que la sonde cherche dans la pile."""
    _calcule_longtemps()


def test_calcul_et_phase():
    sonde = SondeTick()
    sonde.debut()
    tick_semaine()
    m = sonde.fin()
    check("un calcul compte en CPU", m["cpu_ms"] > 300, m["cpu_ms"])
    check("échantillons relevés", m["echantillons"] >= 3, m["echantillons"])
    check("phase = la fonction appelée par tick_semaine",
          m["phases"][0][0].endswith("._calcule_longtemps"), m["phases"])


def test_attente_sans_calcul():
    sonde = SondeTick()
    sonde.debut()
    time.sleep(0.3)
    m = sonde.fin()
    check("dormir ne compte pas en CPU", m["cpu_ms"] < 100, m["cpu_ms"])


def test_ramasse_miettes():
    sonde = SondeTick()
    sonde.debut()
    gc.collect()
    m = sonde.fin()
    check("une collecte complète est comptée", m["gc_gen2"] >= 1 and m["gc_ms"] > 0.0, m)
    gc.collect()   # hors tick : ne doit rien ajouter à la mesure suivante
    sonde.debut()
    m = sonde.fin()
    check("une collecte hors tick n'est pas comptée", m["gc_passes"] == 0, m["gc_passes"])


def test_rapport_serveur():
    srv = SimServer()
    srv.cmd_init({"config": "full", "seed": 42})
    for _ in range(53):
        assert srv.cmd_step_week({}).get("ok")
    rep = srv.cmd_perf_report({})
    check("rapport sérialisable pour le pont", bool(json.dumps(rep)))
    pire = rep["worst"][0]
    check("pire tick avec sonde et contexte",
          pire["sonde"] is not None and "meteo" in pire and "saison" in pire)
    check("état courant sans sonde", rep["current"]["sonde"] is None)
    check("un bilan après une année complète", len(rep["annees"]) == 1, rep["annees"])
    a = rep["annees"][0]
    check("bilan de l'an 1", a["an"] == 1 and a["plantes"] > 0 and a["especes"] > 0, a)
    check("pas de plots neufs la première année", a["plots_neufs_pct"] is None)


def test_rss():
    check("RSS relevé sur la VM", rss_mo() is not None)


if __name__ == "__main__":
    test_calcul_et_phase()
    test_attente_sans_calcul()
    test_ramasse_miettes()
    test_rapport_serveur()
    test_rss()
    print("tout vert")
