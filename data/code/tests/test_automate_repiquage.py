"""
SYMBIOSE — tests/test_automate_repiquage.py
Départ du jardin ⑤ (D140 C.5) : le REPIQUAGE DIFFÉRÉ du jardinier automate
(`tools/jardinier_auto/repiquage.py`).

  [1] fenêtre des gelées tardives : lue au catalogue météo, bloque s2-s10 ;
  [2] limite de nuit = max(lim_froid, lim_gel) (tomate 10 °C ; espèce non sensible
      → son gel) ;
  [3] monde `full` ouvert en s4, godets dans la maison : `repiquer` ouvert dès
      l'init (les godets de la fabrique franchissent la porte `poser_pot`) ;
  [4] automate ON : AUCUN repiquage pendant la fenêtre ni tant que les nuits sont
      sous la limite, puis les trois godets sortent ; plants cultivés (tutelle) ;
  [5] automate OFF : les godets restent pleins ;
  [6] déterminisme : deux runs → même journal de repiquage.

On tourne ~16 semaines — JAMAIS 500 ans. Golden non concerné (automate opt-in).
Lancement : depuis `data/code/`, `python3 -m tests.test_automate_repiquage`.
"""
from __future__ import annotations

from plants import PLANT_CATALOGUE
from constants import PLOT_CM
from world import make_container, planter_dans
from sim.actions.deblocage import est_debloque
from sim.weather import fenetre_evenement
from tools.simserver.server import SimServer
from tools.jardinier_auto import JardinierAutomate, LIBRE, marquer_jardin_cultive
from tools.jardinier_auto.tutelle import zones_cultivees
from tools.jardinier_auto.trace import journal
from tools.jardinier_auto.repiquage import (
    hors_gelees_tardives, limite_nuit, nuit_min, MARGE_NUIT, GELEE_TARDIVE)

J = "joueur_1"
SEMAINE_INIT = 4
SEMAINE_FIN = 20
_res = []


def check(nom, cond, detail=""):
    _res.append(bool(cond))
    print(f"  {'✅' if cond else '❌'} {nom}" + (f" — {detail}" if detail else ""))


def _plant(cle):
    return planter_dans(make_container("pot", "terreau", 2.0, 0.0, 0.0), PLANT_CATALOGUE[cle])


def _monde():
    srv = SimServer()
    srv.cmd_init({"config": "full", "seed": 42, "week": SEMAINE_INIT})
    return srv.engine


def _jouer(automate_on: bool):
    """Tourne s4 → s20 ; renvoie (engine, entrées `repiquer` du journal)."""
    e = _monde()
    a = None
    if automate_on:
        marquer_jardin_cultive(e, J)
        a = JardinierAutomate(LIBRE)
    while e.week < SEMAINE_FIN:
        e.tick_semaine()
        if a is not None:
            a.jouer_tick(e)
    rep = [x for x in journal(e.game_state) if x.get("geste") == "repiquer"]
    return e, rep


def test_regles():
    print("\n[1-2] fenêtre et limite")
    lo, hi = fenetre_evenement(GELEE_TARDIVE)
    check("[1] fenêtre « Gelée tardive » = s2-s9", (lo, hi) == (2, 9), f"{(lo, hi)}")
    check("[1] bloqué en s4 et en s10 (la nuit écoulée de s9)",
          not hors_gelees_tardives(4) and not hors_gelees_tardives(10))
    check("[1] ouvert dès s11", hors_gelees_tardives(11))
    tomate = _plant("tomate")
    check("[2] tomate : limite = lim_froid (froid sans gel)",
          limite_nuit(tomate) == tomate.lim_froid() and limite_nuit(tomate) > 5.0,
          f"{limite_nuit(tomate):.1f} °C")
    carotte = _plant("carotte")
    check("[2] espèce non sensible : limite = lim_gel",
          limite_nuit(carotte) == carotte.lim_gel(), f"{limite_nuit(carotte):.1f} °C")


def test_automate():
    print("\n[3-6] monde full ouvert en s4, godets dans la maison")
    e0 = _monde()
    check("[3] `repiquer` ouvert dès l'init (godets de la fabrique)",
          est_debloque(e0.game_state, J, "repiquer"))

    e, rep = _jouer(True)
    gs = e.game_state
    semaines = sorted({x["semaine"] for x in rep})
    ok = [x for x in rep if x["resultat"] == "ok"]
    check("[4] aucun repiquage tenté pendant la fenêtre des gelées (≤ s10)",
          all(s > 10 for s in semaines), f"semaines {semaines}")
    premier = min(semaines) if semaines else None
    check("[4] des repiquages après la fenêtre", len(ok) == 3,
          f"{len(ok)} réussis, 1ʳᵉ tentative s{premier}")
    # Fenêtre ouverte dès s11 : un 1ᵉʳ essai plus tard prouve que ce sont les NUITS
    # (sous la limite + marge) qui ont retenu les godets, pas la fenêtre seule.
    check("[4] les nuits froides retiennent les godets après la fenêtre",
          premier is not None and premier > 11, f"1ʳᵉ tentative s{premier}")
    check("[4] tous les godets sont vides", all(not c.plants for c in gs["containers"]))
    cult = zones_cultivees(gs, J)
    zones = [(x["tile_id"], int(x["point"][1] // PLOT_CM), int(x["point"][0] // PLOT_CM))
             for x in ok]
    check("[4] plots repiqués = cultivés (sous tutelle de l'automate)",
          zones and all(z in cult for z in zones), f"{zones}")
    check("[4] raison tracée « nuits_douces »",
          all(x["facteur_limitant"] == "nuits_douces" for x in rep))

    e_off, rep_off = _jouer(False)
    check("[5] automate OFF : aucun repiquage, godets pleins",
          not rep_off and all(c.plants for c in e_off.game_state["containers"]))

    _e2, rep2 = _jouer(True)
    check("[6] déterminisme : même journal de repiquage", rep == rep2)


def test_nuit_au_plot():
    print("\n[7] la nuit lue est celle du moteur")
    e = _monde()
    tile = e.tiles[0]
    eco = e._eco(tile)
    n = nuit_min(e.game_state, 14, eco, 0, 0)
    check("[7] nuit la plus froide lue au plot (s13-s15)", -10.0 < n < 25.0, f"{n:.1f} °C")
    check("[7] marge nommée positive", MARGE_NUIT > 0.0)


if __name__ == "__main__":
    test_regles()
    test_automate()
    test_nuit_au_plot()
    n_ok = sum(_res)
    print(f"\n{n_ok}/{len(_res)} vérifications")
    raise SystemExit(0 if n_ok == len(_res) else 1)
