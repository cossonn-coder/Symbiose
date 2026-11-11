"""
SYMBIOSE — tests/bancs/test_nucleation.py
Oracle du banc `nucleation` (zoochorie ⑦, D42) : les bêtes sèment LOIN de la mère.

Le banc tourne `ANS` ans, seed 42. On espionne chaque dépôt de grain sauvage
(`deposer_grain_sauvage`, vu par le merle et par les caches) et chaque levée du log.
Assertions QUALITATIVES (les chiffres d'un run sont consignés dans `00_etat.md`) :
  (a) le merle sème des noyaux de cerisier autour du PIQUET (8 m au nord) ;
  (b) … et sous le MORT DEBOUT (8 m à l'est) tant qu'il tient debout ;
  (c) la plupart de ses noyaux tombent à plus de 5 m du cerisier ;
  (d) le geai rapporte glands et faînes de la hêtraie du nord, en terrain découvert
      (jamais sous la couronne du cerisier). NB : PAS « surtout côté nord » — la
      maison ombre la moitié nord à l'automne (lumière-sol ~0,5 contre ~0,8 au sud
      [seed 42, sem. 30]) et le geai cherche le découvert ensoleillé : la bande nord
      reçoit 1 dépôt sur 9 en 4 ans [n=1 run]. À 20 m, toute la parcelle est à
      portée de geai ;
  (e) des cerisiers semés par le merle et des chênes/hêtres semés par la ceinture
      LÈVENT.

Usage (depuis data/code/) : python3 -m tests.bancs.test_nucleation
"""
import math
import sys

import sim.caches as caches
import sim.zoochorie as zoochorie
from bancs.nucleation import CERISIER, PERCHOIR, MORT_DEBOUT, SURSIS_DEBOUT
from tools.simserver.server import SimServer

ANS = 4
_res = []


def check(nom, ok, info=""):
    _res.append((nom, ok))
    print(f"  [{'OK' if ok else 'ÉCHEC'}] {nom}" + (f" — {info}" if info else ""))


def _derouler():
    depots, levees = [], []
    semaine = {"w": 0}
    originaux = {m: m.deposer_grain_sauvage for m in (zoochorie, caches)}
    for module in (zoochorie, caches):
        vrai = module.deposer_grain_sauvage

        def espion(tile, r, c, grain, _vrai=vrai):
            ok = _vrai(tile, r, c, grain)
            if ok:
                depots.append((semaine["w"], grain.species, grain.origine, r, c))
            return ok
        module.deposer_grain_sauvage = espion
    srv = SimServer()
    assert srv.cmd_init({"cmd": "init", "seed": 42, "config": "nucleation"})["ok"]
    chro = srv._chronique.apres_tick

    def greffe(engine, log):
        chro(engine, log)
        levees.extend(l for l in log if "semé par" in l)
    srv._chronique.apres_tick = greffe
    try:
        for w in range(1, ANS * 52 + 1):
            semaine["w"] = w
            assert srv.cmd_step_week({"cmd": "step_week"})["ok"]
    finally:
        for module, vrai in originaux.items():
            module.deposer_grain_sauvage = vrai
    return depots, levees


def main():
    print(f"=== Banc nucleation, {ANS} ans, seed 42 ===")
    depots, levees = _derouler()
    merle = [d for d in depots if d[2] == "merle"]
    pr, pc = PERCHOIR
    mr, mc, _ = MORT_DEBOUT
    cr, cc, _ = CERISIER
    piquet = [d for d in merle if max(abs(d[3] - pr), abs(d[4] - pc)) <= 1]
    sous_mort = [d for d in merle if d[0] <= SURSIS_DEBOUT
                 and max(abs(d[3] - mr), abs(d[4] - mc)) <= 4]
    loin = [d for d in merle if math.hypot(d[3] - cr, d[4] - cc) * 50 > 500]
    check("(a) noyaux du merle autour du piquet", len(piquet) >= 1,
          f"{len(piquet)}/{len(merle)}")
    check("(b) noyaux sous le mort debout", len(sous_mort) >= 1, f"{len(sous_mort)}")
    check("(c) la plupart à plus de 5 m du cerisier", len(loin) > len(merle) / 2,
          f"{len(loin)}/{len(merle)}")
    foret = [d for d in depots if d[2] in ("ceinture", "geai") and d[1] in ("chene", "hetre")]
    check("(d) glands et faînes de la hêtraie déposés", len(foret) >= 3, f"{len(foret)}")
    sous_cerisier = [d for d in foret if math.hypot(d[3] - cr, d[4] - cc) * 50 < 300]
    check("(d) en terrain découvert, pas sous la couronne du cerisier",
          not sous_cerisier, f"{len(sous_cerisier)}")
    lev_merle = [l for l in levees if "semé par merle" in l and "Cerisier" in l]
    lev_foret = [l for l in levees if "semé par ceinture" in l or "semé par geai" in l]
    check("(e) des cerisiers semés par le merle lèvent", len(lev_merle) >= 1, f"{len(lev_merle)}")
    check("(e) des chênes/hêtres de la forêt lèvent", len(lev_foret) >= 1, f"{len(lev_foret)}")
    ok = sum(1 for _n, v in _res if v)
    print(f"RÉSULTAT : {ok}/{len(_res)} vérifications passées")
    return 0 if ok == len(_res) else 1


if __name__ == "__main__":
    sys.exit(main())
