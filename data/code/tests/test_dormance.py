"""
SYMBIOSE — tests/test_dormance.py
Bourgeons DORMANTS (D129 ①, `sim/growth/dormance.py`) : un ligneux amputé réveille des
bourgeons latents et reconstruit sa couronne, tant qu'il est vivant et éclairé.

Contrats :
  1. reconstruction — un cerisier amputé de moitié regagne plus de segments en un an
                      avec les bourgeons dormants que sans ;
  2. gate lumière   — sous une ombre profonde, aucun réveil (pas de boucle avec la
                      cladoptose : la branche tombée à l'ombre ne repousse pas dessous) ;
  3. gardes         — collet jamais réveillé ; aucun réveil au-dessus du plafond, ni
                      sur un arbre mort ;
  4. déterminisme   — mêmes entrées → même structure.

Usage (depuis data/code/) : python3 -m tests.test_dormance
"""
from plants import PlantInstance
from plants.perennials import CherryTree
import sim.growth as G
import sim.growth.dormance as D
import sim.growth.phases as P
from sim.growth.cladoptose import axe_porteur
from sim.growth.geometrie import _children
from sim.precroissance import pre_croitre

SEED = 42
_res = []


def check(nom, cond, detail=""):
    _res.append(bool(cond))
    print(f"  {'✅' if cond else '❌'} {nom}" + (f" — {detail}" if detail else ""))


class _Ombre:
    """Champ de lumière minimal et UNIFORME : la plante reçoit `l`, gradient nul."""
    def __init__(self, l):
        self.l, self.rows, self.cols, self.data = l, 1, 1, [[l]]

    def light_received(self, _plant):
        return self.l


def _ampute(ans=10):
    """Cerisier pré-crû `ans` ans puis amputé de TOUTES ses latérales (tempête extrême) :
    il ne reste que l'axe porteur (tronc + flèche)."""
    p = PlantInstance(plant_class=CherryTree, position=(4, 4))
    pre_croitre(p, SEED, ans)
    segs = p.segments
    ch = _children(segs)
    axe = axe_porteur(segs, ch)
    G.couper_branches(p, [i for i in range(1, len(segs))
                          if i not in axe and segs[i].parent in axe])
    return p


def _pousser(p, semaines, lf=None, w0=1):
    for w in range(w0, w0 + semaines):
        G.grow_plant(p, SEED, w, lf)


def _sans_dormance(fn):
    vrai = P.peut_reveiller
    P.peut_reveiller = lambda *a, **k: False
    try:
        return fn()
    finally:
        P.peut_reveiller = vrai


def main():
    print("=" * 60 + "\nSYMBIOSE — Bourgeons dormants (D129 ①)\n" + "=" * 60)

    # 1. Reconstruction
    a = _ampute(); n0 = len(a.segments)
    _pousser(a, 52)
    b = _sans_dormance(lambda: (lambda q: (_pousser(q, 52), q)[1])(_ampute()))
    check("amputé + dormants : repousse plus que sans", len(a.segments) > len(b.segments),
          f"départ {n0}, avec {len(a.segments)}, sans {len(b.segments)}")

    # 2. Gate lumière : ombre profonde → aucun réveil
    c = _ampute(); reveils = []
    vrai = P.reveiller_bourgeon
    P.reveiller_bourgeon = lambda *x, **k: reveils.append(vrai(*x, **k))
    try:
        _pousser(c, 52, _Ombre(0.15))
    finally:
        P.reveiller_bourgeon = vrai
    check("ombre 0,15 : aucun bourgeon réveillé",
          reveils and all(r is None for r in reveils), f"{len(reveils)} fenêtres examinées")
    plein, h = [], _ampute()
    P.reveiller_bourgeon = lambda *x, **k: plein.append(vrai(*x, **k))
    try:
        _pousser(h, 52, _Ombre(1.0))
    finally:
        P.reveiller_bourgeon = vrai
    check("plein soleil : des bourgeons réveillés", any(r is not None for r in plein),
          f"{sum(r is not None for r in plein)} réveils")

    # 3. Gardes
    check("collet jamais réveillé", all(r != 0 for r in plein))
    d = _ampute(); d.vitalite = 0.0
    check("arbre mort : pas de réveil", not any(D.peut_reveiller(d, w) for w in range(1, 9)))
    e = PlantInstance(plant_class=CherryTree, position=(4, 4))
    pre_croitre(e, SEED, 10)
    plafond = len(e.segments) >= D.DORMANCE_PLAFOND * CherryTree.max_segments
    check("couronne au plafond : pas de réveil",
          plafond and not any(D.peut_reveiller(e, w) for w in range(1, 9)),
          f"{len(e.segments)} segments")

    # 4. Déterminisme
    f, g = _ampute(), _ampute()
    _pousser(f, 52); _pousser(g, 52)
    check("déterministe", [(s.parent, s.base, s.dir) for s in f.segments]
          == [(s.parent, s.base, s.dir) for s in g.segments])

    print(f"\nRÉSULTAT : {sum(_res)}/{len(_res)} vérifications passées")
    assert all(_res)


if __name__ == "__main__":
    main()
