"""
SYMBIOSE — tests/test_quatre_feuilles.py
Sprint TRÈFLE DOMINANT ③ : le trèfle à quatre feuilles.
  1. déterministe ; adulte vivant non cueilli seulement ; autre espèce jamais ;
  2. rare ; un ramet n'hérite pas du statut de sa mère ;
  3. récolte : Vigueur au plafond, page due, note au carnet, bonus unique, plante intacte ;
  4. rien hors récolte (tick, autres gestes), rien à Vigueur nulle ;
  5. l'automate ne le cueille pas ;
  6. voix ;
  7. pont : hint seulement quand il est vrai, retour du geste, version.
Lancement depuis data/code/ : python3 -m tests.test_quatre_feuilles
"""
from __future__ import annotations

import sys
from types import SimpleNamespace

from fields import init_eco
from plants import Clover, PoaAnnua
from sim import actions as ACT
from sim import pages, vigueur as V
from sim.carnet import carnet_lire
from sim.encyclopedie_corpus import FICHES
from sim.pages_corpus import PAGES
from sim.quatre_feuilles import PROBA_QUATRE_FEUILLES, cueillir, est_quatre_feuilles
from tools.jardinier_auto.boucle import JardinierAutomate
from tools.simserver.server import SimServer
from tools.simserver.version import ENGINE_VERSION
from world import Tile

ECHECS: list[str] = []
SEED = 42
J = "joueur_1"


def check(libelle: str, ok: bool, detail: str = "") -> None:
    print(f"  {'OK ' if ok else 'KO '} {libelle}" + (f" ({detail})" if detail and not ok else ""))
    if not ok:
        ECHECS.append(libelle)


def _monde():
    tile = Tile(tile_id="T0", soil_type="terre", origin_x_cm=0.0, origin_y_cm=0.0)
    eco = init_eco("T0", 6, 8, humidite=2.0, fertilite=1.2, microbiome=0.3, soil_type="terre")
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {}, "current_player": J,
          "week": 10, "log": [], "seed": SEED}
    return gs, tile, eco


def _adulte(tile, cls=Clover, form_seed=77):
    p = tile.add_plant(cls, 2, 3)
    p.current_stage = len(cls.growth_stages) - 1
    p.form_seed = form_seed
    return p


def _placer_a_quatre_feuilles(p) -> None:
    """Déplace le pied sur le premier point qui lui donne quatre feuilles."""
    for x in range(100, 400):
        for y in range(100, 300):
            p.x_cm, p.y_cm = float(x), float(y)
            if est_quatre_feuilles(p, SEED):
                return
    raise AssertionError("aucun point à quatre feuilles")


def test_pure() -> None:
    print("[1] fonction pure")
    gs, tile, _ = _monde()
    p = _adulte(tile)
    _placer_a_quatre_feuilles(p)
    check("déterministe", all(est_quatre_feuilles(p, SEED) for _ in range(5)))
    check("une autre seed change le tirage", not all(
        est_quatre_feuilles(p, s) for s in range(SEED, SEED + 50)))
    p.current_stage = 0
    check("semis : non", not est_quatre_feuilles(p, SEED))
    p.current_stage = 1
    p.vitalite = 0.0
    check("mort : non", not est_quatre_feuilles(p, SEED))
    p.vitalite = 1.0
    p.quatre_feuilles_cueilli = True
    check("déjà cueilli : non", not est_quatre_feuilles(p, SEED))
    autre = _adulte(tile, PoaAnnua)
    autre.x_cm, autre.y_cm = p.x_cm, p.y_cm
    check("autre espèce : jamais", not est_quatre_feuilles(autre, SEED))


def test_rarete() -> None:
    print("[2] rareté et ramets")
    gs, tile, _ = _monde()
    p = _adulte(tile)
    # Colonie : un même form_seed, des positions différentes. 40 000 points.
    n, total = 0, 0
    for x in range(200):
        for y in range(200):
            p.x_cm, p.y_cm = x * 1.37, y * 2.11
            total += 1
            n += est_quatre_feuilles(p, SEED)
    part = n / total
    check("fréquence proche de la probabilité",
          0.5 * PROBA_QUATRE_FEUILLES < part < 1.5 * PROBA_QUATRE_FEUILLES, f"{part:.4f}")
    # Graines différentes (form_seed variés) au même point.
    n = 0
    for fs in range(1, 20001):
        p.form_seed = fs
        n += est_quatre_feuilles(p, SEED)
    check("fréquence proche aussi à form_seed variable",
          0.5 * PROBA_QUATRE_FEUILLES < n / 20000 < 1.5 * PROBA_QUATRE_FEUILLES, f"{n / 20000:.4f}")
    p.form_seed = 77
    _placer_a_quatre_feuilles(p)
    ramets = 0
    x0, y0 = p.x_cm, p.y_cm
    for dx in (-20, -10, 10, 20):
        for dy in (-20, -10, 10, 20):
            p.x_cm, p.y_cm = x0 + dx, y0 + dy
            ramets += est_quatre_feuilles(p, SEED)
    check("les ramets voisins, même form_seed, n'héritent pas", ramets <= 1, f"{ramets}/16")


def test_recolte() -> None:
    print("[3] récolte")
    gs, tile, eco = _monde()
    p = _adulte(tile)
    _placer_a_quatre_feuilles(p)
    st = V.ensure_player(gs, J)
    st["courante"] = 20.0
    genes, vit, stade = dict(p.genes), p.vitalite, p.current_stage
    ratio = ACT.recolter(gs, J, p, eco)
    check("effort plein", ratio == 1.0)
    check("Vigueur au plafond", st["courante"] == V.vigueur_max(gs, J), f"{st['courante']}")
    check("une page ouverte", len(pages.pages_trouvees(gs, J)) == 1)
    notes = [e for e in carnet_lire(gs, J) if "quatre feuilles" in e["texte"]]
    check("une note au carnet", len(notes) == 1, f"{len(notes)}")
    check("zone du ledger", gs["journal"][J]["entries"][-1]["zone"] == ("T0", *p.position))
    check("rien versé à la plante", p.genes == genes and p.vitalite == vit
          and p.current_stage == stade and p.is_alive)
    check("pied marqué", p.quatre_feuilles_cueilli and not est_quatre_feuilles(p, SEED))
    st["courante"] = 20.0
    ACT.recolter(gs, J, p, eco)
    check("bonus unique : seconde récolte ordinaire", st["courante"] < V.vigueur_max(gs, J)
          and len(pages.pages_trouvees(gs, J)) == 1, f"{st['courante']}")
    # Corpus épuisé : la Vigueur reste versée, la page se tait.
    gs, tile, eco = _monde()
    p = _adulte(tile)
    _placer_a_quatre_feuilles(p)
    gs["pages"] = {J: set(PAGES)}
    V.ensure_player(gs, J)["courante"] = 5.0
    check("corpus épuisé : pas de crash", cueillir(gs, J, p, eco)
          and gs["vigueur"][J]["courante"] == V.vigueur_max(gs, J))


def test_hors_recolte() -> None:
    print("[4] rien hors récolte")
    gs, tile, eco = _monde()
    p = _adulte(tile)
    _placer_a_quatre_feuilles(p)
    st = V.ensure_player(gs, J)
    st["courante"] = 0.0
    check("à Vigueur nulle : rien de cueilli", ACT.recolter(gs, J, p, eco) == 0.0
          and not p.quatre_feuilles_cueilli and "pages" not in gs)
    st["courante"] = 50.0
    ACT.deraciner(gs, J, p, eco)
    check("déraciner : aucun bonus", "pages" not in gs and not p.quatre_feuilles_cueilli)
    gs, tile, eco = _monde()
    p = _adulte(tile)
    _placer_a_quatre_feuilles(p)
    avant = dict(gs)
    check("lire le statut n'écrit rien", est_quatre_feuilles(p, SEED) and gs == avant
          and not p.quatre_feuilles_cueilli)
    gs2, tile2, eco2 = _monde()
    p2 = _adulte(tile2, Clover, form_seed=78)
    p2.x_cm = p2.y_cm = 100.0
    check("trèfle ordinaire : cueillir ne fait rien",
          not est_quatre_feuilles(p2, SEED) and not cueillir(gs2, J, p2, eco2)
          and "pages" not in gs2)


def test_automate() -> None:
    print("[5] automate")
    gs, tile, eco = _monde()
    p = _adulte(tile)
    o = _adulte(tile, Clover, form_seed=78)
    _placer_a_quatre_feuilles(p)
    o.x_cm = o.y_cm = 100.0
    check("pied ordinaire bien ordinaire", not est_quatre_feuilles(o, SEED))
    profil = SimpleNamespace(n_a_recolter=lambda n: n)
    plan = SimpleNamespace(verbe="recolter")
    garde = JardinierAutomate(profil)._appliquer_part_recoltee(
        [(("T0", 0, 0), tile, eco, p, plan), (("T0", 0, 1), tile, eco, o, plan)], SEED)
    check("le plan du pied à quatre feuilles tombe, l'autre reste",
          [x[3] for x in garde] == [o])


def test_voix() -> None:
    print("[6] voix")
    check("fiche niveau 3", "quatre folioles" in FICHES["trefle"][3])
    page = [q for q in PAGES.values() if q["titre"] == "Celui qu'on ne cherche pas"]
    check("page de folklore, voix paysanne", len(page) == 1 and page[0]["voix"] == "C")


def test_pont() -> None:
    print("[7] pont")
    srv = SimServer()
    rep = srv.cmd_init({"config": "full", "seed": SEED})
    check("version courante", rep.get("engine_version") == ENGINE_VERSION)
    gs = srv.engine.game_state
    tile = gs["tiles"][0]
    p = tile.add_plant(Clover, 0, 0)
    assert p is not None
    p.current_stage = 1
    p.form_seed = 77
    p.x_cm, p.y_cm = 10.0, 10.0
    for x in range(1, 400):
        for y in range(1, 400):
            p.x_cm, p.y_cm = x / 8, y / 8
            if est_quatre_feuilles(p, SEED):
                break
        else:
            continue
        break

    def _vues():
        return srv._snapshot()["plants"]

    vues = _vues()
    marques = [v for v in vues if v.get("quatre_feuilles")]
    check("hint présent sur le pied", any(v["x_cm"] == p.x_cm and v["y_cm"] == p.y_cm
                                          for v in marques))
    check("clé absente, jamais à false", all(v.get("quatre_feuilles", True) is True for v in vues))
    check("rien au bloc joueur", "quatre_feuilles" not in str(srv._snapshot()["player"]))
    rep = srv.cmd_action({"verb": "recolter", "target": {
        "tile": tile.tile_id, "x_cm": p.x_cm, "y_cm": p.y_cm}})
    check("le geste le dit", "quatre feuilles" in str(rep), str(rep)[:200])
    check("cueilli", p.quatre_feuilles_cueilli)
    check("hint retiré après cueillette", not any(
        v.get("quatre_feuilles") and v["x_cm"] == p.x_cm and v["y_cm"] == p.y_cm
        for v in _vues()))


def main() -> int:
    for t in (test_pure, test_rarete, test_recolte, test_hors_recolte, test_automate,
              test_voix, test_pont):
        t()
    print(f"\n{'KO : ' + ', '.join(ECHECS) if ECHECS else 'tout vert'}")
    return 1 if ECHECS else 0


if __name__ == "__main__":
    sys.exit(main())
