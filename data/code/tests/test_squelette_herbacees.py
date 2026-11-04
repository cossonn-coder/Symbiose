"""
SYMBIOSE — tests/test_squelette_herbacees.py
FORMES DES PLANTES ⑤ : les herbacées à port ne font plus pousser de segments.

Garde ce que le golden et le monde `full` ne voient pas, faute de fraisier, de courgette
et de geste :
  1. chaque espèce sans squelette a un port dessiné, et les exclues sont les bonnes ;
  2. le collet seul demeure, et il vieillit (âge du pied, lignification de l'écrasement) ;
  3. fraisier et courgette gardent leurs apex, donc leur nombre de fruits ;
  4. tailler et arracher déposent la hauteur rabattue, jamais plus que la plante n'a ;
  5. pincer reste payé et noté, sans rien déposer ;
  6. écraser et bouturer marchent sur un pied réduit au collet.

Lancement (depuis data/code/) : python3 -m tests.test_squelette_herbacees
"""
import os
import re

from plants import AppleTree, PLANT_CATALOGUE, PERENNIAL_CATALOGUE, organ_sites
from plants.catalogue import ESPECES_SPONTANEES
from plants.species import (Basil, Bean, Clover, Sunflower, Tomato, Thyme, Raspberry, Ivy,
                            Strawberry, Zucchini, Mint)
from fields.ecofields import BOIS_PAR_CM, VITALITE_STEP
from sim import actions as ACT, vigueur as V
from sim.actions import bouture as B
from sim.actions.taille_herbacee import RABATTU_PART
from sim.growth import f_lignification, grow_plant
from tests.vigueur.harness import check, _gs_with, _results

RACINE = os.path.join(os.path.dirname(__file__), "..", "..", "..")
SEED = 42


def _pousser(plant, semaines):
    for w in range(1, semaines + 1):
        grow_plant(plant, SEED, w)
    return plant


def _especes():
    """Toutes les espèces jouables, y compris celles de la flore spontanée."""
    vus = set(ESPECES_SPONTANEES)
    for cat in (PLANT_CATALOGUE, PERENNIAL_CATALOGUE):
        vus.update(cat.values())
    return vus


def _depots(eco):
    """Enregistre chaque dépôt de litière de `eco`, sans l'empêcher."""
    depots = []
    vrai = eco.deposer_litiere

    def sonde(r, c, tissu, masse, *a, **k):
        if masse > 0.0:          # le dépôt nul est un no-op de `deposer_litiere`
            depots.append((tissu, masse))
        return vrai(r, c, tissu, masse, *a, **k)

    eco.deposer_litiere = sonde
    return depots


def test_predicat():
    print("\n[1] prédicat : une espèce sans squelette a toujours un port")
    fiches = ""
    for f in ("PlantRenderer.PortsFiches.cs", "PlantRenderer.Prairie.cs"):
        with open(os.path.join(RACINE, "visuals", f), encoding="utf-8") as src:
            fiches += src.read()
    ports = set(re.findall(r'\["(\w+)"\]\s*=\s*(?:new\(FormePort|PortPrairie)', fiches))
    sans = {c for c in _especes() if c.sans_squelette()}
    manquent = sorted(c.__name__ for c in sans if c.__name__ not in ports)
    check("toutes dans la table des ports", not manquent, f"sans port : {manquent}")
    check("au moins 30 espèces concernées", len(sans) >= 30, f"{len(sans)}")
    for c in (Tomato, Bean, Ivy, Thyme, Raspberry, AppleTree, Strawberry, Zucchini):
        check(f"{c.__name__} garde ses segments", not c.sans_squelette())


def test_collet():
    print("\n[2] le collet seul demeure, et vieillit")
    _, tile, _ = _gs_with((Basil, 2, 2))
    p = tile.plants[0]
    tombes = [grow_plant(p, SEED, w) for w in range(1, 61)]
    check("un seul segment après 60 semaines", len(p.segments) == 1, f"{len(p.segments)}")
    check("le collet a 60 semaines", p.segments[0].age_weeks == 60, f"{p.segments[0].age_weeks}")
    check("rien ne tombe", not any(tombes))
    check("le collet reste au point sol", p.segments[0].base == (p.x_cm, p.y_cm, 0.0))


def test_fruits():
    print("\n[3] fraisier et courgette : le nombre de fruits suit toujours les apex")
    for cls in (Strawberry, Zucchini):
        _, tile, _ = _gs_with((cls, 2, 2))
        p = tile.plants[0]
        p.growth_factor = 1.0
        n1 = len(organ_sites(_pousser(p, 26)))
        p2 = _gs_with((cls, 2, 2))[1].plants[0]
        p2.growth_factor = 1.0
        n2 = len(organ_sites(_pousser(p2, 104)))
        check(f"{cls.__name__} : 1 site à 26 semaines", n1 == 1, f"{n1}")
        check(f"{cls.__name__} : plusieurs à 2 ans, comme avant le retrait", n2 == 10, f"{n2}")


def _taillable(cls=Sunflower, stade=None):
    gs, tile, eco = _gs_with((cls, 2, 2))
    st = V.ensure_player(gs, "joueur_1")
    st["max_base"] = st["courante"] = 10_000.0
    p = tile.plants[0]
    p.current_stage = len(cls.growth_stages) - 1 if stade is None else stade
    _pousser(p, 40)
    return gs, eco, p, st


def test_taille():
    print("\n[4] tailler, arracher : la hauteur rabattue, jamais deux fois")
    for geste in (ACT.tailler, ACT.arracher):
        gs, eco, p, _ = _taillable()
        depots = _depots(eco)
        attendu = p.current_height * RABATTU_PART * BOIS_PAR_CM
        check(f"{geste.__name__} : payé", geste(gs, "joueur_1", p, eco))
        check(f"{geste.__name__} : masse = hauteur rabattue, en `bois`",
              len(depots) == 1 and depots[0][0] == "bois" and abs(depots[0][1] - attendu) < 1e-9,
              f"{depots} pour {attendu:.3f}")
        check(f"{geste.__name__} : semaine notée", p.semaine_coupe == gs["week"])
        depots.clear()
        geste(gs, "joueur_1", p, eco)
        check(f"{geste.__name__} : second clic la même semaine, rien", not depots, f"{depots}")
        gs["week"] += 4
        geste(gs, "joueur_1", p, eco)
        check(f"{geste.__name__} : 4 semaines après, la moitié",
              len(depots) == 1 and abs(depots[0][1] - attendu * 0.5) < 1e-9,
              f"{depots} pour {attendu * 0.5:.3f}")
        check(f"{geste.__name__} : le collet reste", len(p.segments) == 1)

    gs, eco, p, st = _taillable()
    vit = p.vitalite
    ACT.arracher(gs, "joueur_1", p, eco)
    check("arracher érode toujours", abs(p.vitalite - (vit - VITALITE_STEP / p.plant_class.resilience_base)) < 1e-9,
          f"{vit:.3f} → {p.vitalite:.3f}")
    gs, eco, p, st = _taillable()
    st["courante"] = 0.0
    depots = _depots(eco)
    check("Vigueur insuffisante : refus", not ACT.tailler(gs, "joueur_1", p, eco))
    check("refus : rien déposé, rien noté", not depots and p.semaine_coupe < 0)
    gs, eco, p, _ = _taillable(Zucchini)
    n = len(p.segments)
    depots = _depots(eco)
    ACT.tailler(gs, "joueur_1", p, eco)
    check("fraisier, courgette : la coupe reste au segment", len(p.segments) <= n and all(
        m <= 8 * BOIS_PAR_CM + 1e-9 for _, m in depots), f"{depots}")


def test_pincer():
    print("\n[5] pincer : payé, noté, rien au sol")
    gs, eco, p, st = _taillable(Basil)
    av = st["courante"]
    depots = _depots(eco)
    check("payé", ACT.pincer(gs, "joueur_1", p, eco))
    check("coût FAIBLE débité", st["courante"] == av - ACT.FAIBLE, f"{st['courante']}")
    check("semaine notée, pour `pince`", p.semaine_pince == gs["week"])
    check("rien au sol", not depots)


def test_ecraser_bouturer():
    print("\n[6] écraser et bouturer sur un pied réduit au collet")
    gs, eco, p, _ = _taillable(Clover)
    age = p.segments[0].age_weeks
    check("l'âge du pied est lu sur le collet", f_lignification(age) == f_lignification(40), f"{age}")
    check("écraser payé, sans erreur", ACT.ecraser_plante(gs, "joueur_1", p, eco))
    check("le collet reste", len(p.segments) == 1)
    gs, eco, p, _ = _taillable(Mint)
    check("une menthe mûre au collet reste bouturable", B.peut_bouturer(p, eco))


def main():
    for t in (test_predicat, test_collet, test_fruits, test_taille, test_pincer,
              test_ecraser_bouturer):
        t()
    ko = [n for n, ok in _results if not ok]
    print(f"\n{len(_results) - len(ko)}/{len(_results)} verts")
    return 1 if ko else 0


if __name__ == "__main__":
    raise SystemExit(main())
