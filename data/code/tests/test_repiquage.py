"""
SYMBIOSE — tests/test_repiquage.py
Départ du jardin ④ (D140 C.4-C.5) : le POT DANS LA MAISON (`world/interieur.py`) et
le geste `repiquer` + son choc par le bilan (`sim/repiquage.py`).

  [1] pot dans la maison : pièce tempérée même si l'air du mini-sol était à −3 °C ;
  [2] lumière de fenêtre : ≈ 0,3 × celle d'un pot en plein soleil ;
  [3] `repiquer` : même plante (id, gènes, âge, structure translatée), pot vidé,
      chevelu entamé, Vigueur débitée ;
  [4] refus propres, sans Vigueur : plot hors tuile, pot vide ;
  [5] le choc passe par le BILAN : absorption plafonnée, repousse payée, rien en
      dormance, refait en quelques semaines ;
  [6] voix : ligne de log → événement → note du carnet (une fois par cause).

Lancement : depuis `data/code/`, `python3 -m tests.test_repiquage`.
"""
from __future__ import annotations

from constants import PLOT_CM
from plants import PLANT_CATALOGUE
from sim import actions as A
from sim import vigueur as V
from sim import bilan as B
from sim.evenements import evenements
from sim.repiquage import (COUPE_MOTTE, COUPE_CHIGNON, REPRISE_RACINES,
                           couper_racines, reprendre_racines)
from world import House, make_container, planter_dans
from world.interieur import T_INTERIEUR, FENETRE, est_interieur

J = "joueur_1"
_res = []


def check(nom, cond, detail=""):
    _res.append(bool(cond))
    print(f"  {'✅' if cond else '❌'} {nom}" + (f" — {detail}" if detail else ""))


def _gs():
    from tests.test_golden import build_world
    tiles, ecos = build_world()
    gs = {"current_player": J, "house": House(), "tiles": tiles, "eco": ecos,
          "log": [], "week": 10}
    V.ensure_player(gs, J)["courante"] = 1e6
    return gs


def _pot(x, y, cle="tomate", semaines=6):
    ctn = make_container("pot", "terreau", 2.0, x, y)
    plant = planter_dans(ctn, PLANT_CATALOGUE[cle])
    for w in range(2, 2 + semaines):
        ctn.tick("printemps", 42, w, house=House())
    return ctn, plant


def test_interieur():
    print("\n[1-2] pot dans la maison")
    dedans, p_in = _pot(1000.0, 1375.0)
    dehors, p_out = _pot(1000.0, 1900.0)          # au sud de la maison, plein soleil
    check("emprise de la maison = intérieur",
          est_interieur(1000.0, 1375.0, House()) and not est_interieur(1000.0, 1900.0, House()))
    dedans.eco.temperature.fill(-3.0)             # comme si une nuit de gel l'avait écrit
    dedans.tick("printemps", 42, 8, house=House())
    t_air, t_sol = dedans.eco.temperature.at_plot(0, 0), dedans.eco.temperature_sol.at_plot(0, 0)
    check("[1] la pièce reste tempérée malgré −3 °C dehors (pas de gel)",
          t_air == T_INTERIEUR and t_sol > 10.0, f"T_air {t_air}, T_sol {t_sol:.1f}")
    l_in = dedans.eco.lumiere.light_received(p_in)
    l_out = dehors.eco.lumiere.light_received(p_out)
    check("[2] lumière de fenêtre ≈ FENETRE × plein soleil",
          abs(l_in - FENETRE * l_out) < 0.02 and l_in < l_out,
          f"dedans {l_in:.3f}, dehors {l_out:.3f}")
    # Re-tick à géométrie inchangée : le filtre ne s'applique pas deux fois (cache).
    dedans.tick("printemps", 42, 9, house=House())
    check("[2] pas de double filtrage d'un tick à l'autre",
          abs(dedans.eco.lumiere.light_received(p_in) - l_in) < 0.02,
          f"{dedans.eco.lumiere.light_received(p_in):.3f}")


def test_repiquer():
    print("\n[3-4] geste repiquer")
    gs = _gs()
    tile = gs["tiles"][0]
    ctn, plant = _pot(1000.0, 1375.0)
    gs["containers"] = [ctn]
    plant.genes["hauteur"] = 1.1
    ident, age, nseg = id(plant), plant.age_weeks, len(plant.segments)
    v0 = V.ensure_player(gs, J)["courante"]
    check("[4] plot hors tuile → refus, aucune Vigueur",
          A.repiquer(gs, J, ctn, tile, 99, 0) is None
          and V.ensure_player(gs, J)["courante"] == v0 and plant in ctn.plants)
    cause = A.repiquer(gs, J, ctn, tile, 3, 4)
    x, y = 4 * PLOT_CM + PLOT_CM / 2, 3 * PLOT_CM + PLOT_CM / 2
    sur_tuile = [p for p in tile.plants if id(p) == ident]
    check("[3] même plante en pleine terre (id, gènes, âge, segments)",
          len(sur_tuile) == 1 and plant.genes["hauteur"] == 1.1
          and plant.age_weeks == age and len(plant.segments) == nseg)
    check("[3] collet au centre du plot visé, structure translatée",
          plant.position == (3, 4) and (plant.x_cm, plant.y_cm) == (x, y)
          and plant.segments[0].base[:2] == (x, y), plant.segments[0].base)
    check("[3] pot resté, vidé", ctn in gs["containers"] and ctn.plants == [])
    check("[3] choc : chevelu entamé selon le serrage du godet",
          cause in ("motte", "chignon") and plant.racines_coupees >= COUPE_MOTTE,
          f"{cause}, coupées {plant.racines_coupees:.2f}")
    check("[3] Vigueur débitée", V.ensure_player(gs, J)["courante"] < v0)
    v1 = V.ensure_player(gs, J)["courante"]
    check("[4] pot vide → refus, aucune Vigueur",
          A.repiquer(gs, J, ctn, tile, 3, 5) is None
          and V.ensure_player(gs, J)["courante"] == v1)


def test_choc_bilan():
    print("\n[5] le choc passe par le bilan")
    eco = _gs()["eco"]
    eco = next(iter(eco.values()))
    plant = planter_dans(make_container("pot", "terreau", 2.0, 0, 0), PLANT_CATALOGUE["tomate"])
    plant.position = (2, 2)
    hum = eco.humidite.at_plot(2, 2)
    serre = couper_racines(plant, 1.0)
    check("racines à l'étroit → chignon, plus fort qu'une motte",
          serre == "chignon"
          and abs(plant.racines_coupees - (COUPE_MOTTE + COUPE_CHIGNON)) < 1e-9)
    check("absorption plafonnée au chevelu restant, même en sol frais",
          abs(B.f_eau(plant, hum) - (1 - plant.racines_coupees)) < 1e-9
          and B.f_eau(plant, hum) < 1.0, f"hum {hum:.2f}, f_eau {B.f_eau(plant, hum):.2f}")
    avant = plant.racines_coupees
    check("dormante : ni repousse ni coût", reprendre_racines(plant, active=False) == 0.0
          and plant.racines_coupees == avant)
    kw = dict(saison="printemps", presence=1.0, light_eff=1.0, hum_percue=1.0, temp=20.0,
              t_feuille=22.0, t_air=18.0, f_nut=1.0, f_allelo=1.0)
    temoin = planter_dans(make_container("pot", "terreau", 2.0, 0, 0), PLANT_CATALOGUE["tomate"])
    temoin.reserves = plant.reserves = 0.5        # réserves à remplir : le net se lit
    B.semaine_bilan(temoin, **kw)
    B.semaine_bilan(plant, **kw)
    cout = 2.0 * REPRISE_RACINES                  # cout_feuillage herbacée × repousse
    check("le repiqué produit moins ET paie sa repousse (net plus bas que témoin − coût)",
          temoin.bilan_net - plant.bilan_net > cout,
          f"témoin {temoin.bilan_net:.2f}, repiqué {plant.bilan_net:.2f}")
    n = 1
    while plant.racines_coupees > 0.0 and n < 20:
        B.semaine_bilan(plant, **kw)
        n += 1
    check("chevelu refait en quelques semaines", 3 <= n <= 6, f"{n} semaines")


def test_voix():
    print("\n[6] voix du carnet")
    gs = _gs()
    tile = gs["tiles"][0]
    for c in (1, 2):
        ctn, _ = _pot(1000.0, 1375.0)
        A.repiquer(gs, J, ctn, tile, 1, c)
    lignes = [l for l in gs["log"] if "Repiquage" in l]
    check("une note la première fois par cause", len(lignes) == 1, lignes)
    ev = [e for e in evenements(gs["log"]) if e.kind == "repiquage"]
    check("relue par evenements (espèce, tuile, cause)",
          len(ev) == 1 and ev[0].espece == "tomate" and ev[0].cause in ("motte", "chignon"),
          ev)
    from sim.carnet import _texte, _D
    txt = _texte("repiquage", ev[0].cause, _D, "tomate", (tile.tile_id, 1, 1), 10)
    check("texte de carnet dédié", "tomate" in txt and "Quelque chose" not in txt, txt)


if __name__ == "__main__":
    test_interieur()
    test_repiquer()
    test_choc_bilan()
    test_voix()
    ok = sum(_res)
    print(f"\n{ok}/{len(_res)} OK")
    raise SystemExit(0 if ok == len(_res) else 1)
