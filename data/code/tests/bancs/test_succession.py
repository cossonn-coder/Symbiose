"""
SYMBIOSE — tests/bancs/test_succession.py
Oracle du banc de SUCCESSION (tronçon ② du sprint « bugs d'émergence »).

Contrairement aux bancs foliaires (un signe lu sur quelques semaines), celui-ci
observe une TRAJECTOIRE sur ~15 ans : la composition du peuplement an par an. Il
prouve que le verrou S3 est levé — sans hash figé, uniquement des tendances et
des bornes (un banc décrit un monde, l'oracle décide quoi observer).

Ce qu'on asserte, dans le SENS du déverrouillage :
  1. le pioneer culmine PUIS décroît (ne reste pas ~95 % → plus de monoculture) ;
  2. la part cumulée fixatrice+graminée+competitor CROÎT et dépasse un seuil
     (> 40 %) avant ~15 ans ;
  3. la banque-sol des tardifs (sbFix/sbGra/sbCmp) se garnit (non nulle).

Usage (depuis data/code/) : python3 -m tests.bancs.test_succession
"""
from __future__ import annotations

from bancs import BANCS
from sim.engine import Engine
from .oracle import SEED

_results = []

ARCHETYPES = ("pioneer", "nitrogen_fixer", "grass", "competitor")
ANS = 15            # horizon d'observation : la bascule doit survenir AVANT ~15 ans


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK  " if cond else "FAIL"
    print(f"  [{flag}] {name}" + (f" — {detail}" if detail else ""))


def _composition(tiles) -> dict:
    """Compte les plantes vivantes par archétype sur toutes les tuiles du banc."""
    comp = {a: 0 for a in ARCHETYPES}
    for tile in tiles:
        for p in tile.plants:
            if not p.is_alive:
                continue
            a = getattr(p.plant_class, "archetype", None)
            if a in comp:
                comp[a] += 1
    return comp


def _seedbank_tardifs(tiles, ecos) -> dict:
    """Somme de la densité en banque-sol des archétypes tardifs (moyennée plot)."""
    tot = {a: 0.0 for a in ("nitrogen_fixer", "grass", "competitor")}
    n = 0
    for tile in tiles:
        eco = ecos[tile.tile_id]
        for r in range(tile.grid_rows):
            for c in range(tile.grid_cols):
                for a in tot:
                    tot[a] += eco.seed_bank.get(r, c, a)
                n += 1
    return {a: (v / n if n else 0.0) for a, v in tot.items()}


def _trajectoire():
    """Monte `succession_bascule` et simule ANS années, en relevant la composition
    à la fin de chaque année. Renvoie (compos_par_an, seedbank_final)."""
    tiles, ecos, house, banque = BANCS["succession_bascule"]()
    game_state = {
        "tiles": tiles, "eco": ecos, "scores": {},
        "current_player": "joueur_1", "week": 1, "log": [],
        "house": house, "seed": SEED, "player_seed_bank": banque,
    }
    engine = Engine(game_state)
    compos = []
    for _ in range(ANS):
        for _ in range(52):
            engine.tick_semaine()
            game_state["log"].clear()
        compos.append(_composition(tiles))
    return compos, _seedbank_tardifs(tiles, ecos)


def test_succession_bascule():
    """La friche pionnière bascule vers la prairie : le pioneer culmine puis
    reflue, les tardifs prennent le relais et garnissent la banque-sol."""
    compos, sb = _trajectoire()

    pion = [c["pioneer"] for c in compos]
    tardifs = [c["nitrogen_fixer"] + c["grass"] + c["competitor"] for c in compos]
    totaux = [p + t for p, t in zip(pion, tardifs)]

    # 1. pioneer culmine PUIS décroît (n'est pas monotone jusqu'à saturer).
    pic = max(pion)
    idx_pic = pion.index(pic)
    apres = pion[-1]
    check("pioneer culmine puis DÉCROÎT (plus de saturation)",
          idx_pic < len(pion) - 1 and apres < pic,
          f"pic={pic} à l'an {idx_pic + 1}, fin={apres}")

    # 1bis. le pioneer NE domine PLUS en fin d'horizon (part < 40 %).
    part_pion_fin = pion[-1] / totaux[-1] if totaux[-1] else 0.0
    check("pioneer ne domine plus en fin d'horizon (part < 40 %)",
          part_pion_fin < 0.40, f"part_pioneer_fin={part_pion_fin:.2%}")

    # 2. la part cumulée des tardifs dépasse 40 % avant ANS ans.
    parts_tardifs = [(t / tot if tot else 0.0) for t, tot in zip(tardifs, totaux)]
    an_bascule = next((i + 1 for i, p in enumerate(parts_tardifs) if p > 0.40), None)
    check("tardifs > 40 % du couvert avant 15 ans",
          an_bascule is not None and an_bascule <= 15,
          f"bascule à l'an {an_bascule}, part finale={parts_tardifs[-1]:.2%}")

    # 3. la banque-sol des tardifs est GARNIE (verrou levé : plus au plancher).
    check("banque-sol fixatrice non nulle", sb["nitrogen_fixer"] > 0.05,
          f"sbFix={sb['nitrogen_fixer']:.3f}")
    check("banque-sol graminée non nulle", sb["grass"] > 0.05,
          f"sbGra={sb['grass']:.3f}")
    check("banque-sol competitor non nulle", sb["competitor"] > 0.05,
          f"sbCmp={sb['competitor']:.3f}")


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Oracle banc succession (tronçon ②)")
    print("=" * 60)
    test_succession_bascule()
    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
