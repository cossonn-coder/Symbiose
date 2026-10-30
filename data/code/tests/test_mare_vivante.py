"""
SYMBIOSE — tests/test_mare_vivante.py
MARE VIVANTE ① (D121) — glace sur l'eau libre et « ce qui est dit = ce qui est peint ».

  A. `glace_next` (pur) : pas de lame → 0 ; nuit gelée → la glace prend ; semaine
     douce → elle fond ; bornée [0,1].
  B. `tick_glace` : plusieurs semaines de gel prennent la lame ; une lame disparue
     emporte sa glace ; un plot sec ne gèle jamais.
  C. Dit = peint : hors saison (densité < SEUIL_PRESENCE), la voix d'une bête de mare
     ne nomme ni moustique ni libellule ; en saison, elle les nomme, l'article en
     minuscule en milieu de phrase (« J'ai senti la libellule »).

Golden non concerné (glace sans effet en retour ; voix = lecture pure).
Usage (depuis data/code/) : python3 -m tests.test_mare_vivante
"""
from fields.ecofields import EcoFields
from fields.ecofields.constants import SEUIL_FLAQUE
from fields.ecofields.glace import glace_next
from fields.population.perception import SEUIL_PRESENCE, est_peinte
from sim import voix_etres as VE
from tools.simserver.server import SimServer

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'✅' if cond else '❌'} {name}" + (f" — {detail}" if detail else ""))


def test_glace_pure():
    print("\n[A] glace_next pur")
    check("pas de lame → pas de glace", glace_next(0.8, SEUIL_FLAQUE, -5.0, -2.0) == 0.0)
    g = glace_next(0.0, 1.0, -2.0, 2.0)
    check("nuit gelée → la glace prend", g > 0.0, g)
    check("semaine douce → la glace fond", glace_next(0.6, 1.0, 3.0, 12.0) < 0.6)
    check("bornée à 1", glace_next(0.95, 1.0, -10.0, -5.0) == 1.0)
    check("bornée à 0", glace_next(0.05, 1.0, 5.0, 20.0) == 0.0)


def test_tick_glace():
    print("\n[B] tick_glace")
    eco = EcoFields(tile_id=0, rows=4, cols=4)
    eco.eau_surface.set(1, 1, 1.0)                  # une lame ; le reste est sec
    for _ in range(3):
        eco.tick_glace(-3.0, 0.0)                   # 3 semaines de gel, ciel clair
    check("la lame est prise après 3 semaines de gel", eco.glace.at_plot(1, 1) >= 0.5,
          eco.glace.at_plot(1, 1))
    check("un plot sec ne gèle jamais", eco.glace.at_plot(2, 2) == 0.0)
    eco.eau_surface.set(1, 1, 0.0)
    eco.tick_glace(-3.0, 0.0)
    check("la lame disparue emporte sa glace", eco.glace.at_plot(1, 1) == 0.0)


def _phrases(cle, tile, eco, r, c, gs):
    """Toutes les phrases possibles sur 30 semaines (variantes par hash)."""
    return [p for w in range(30) for p in VE.phrases_bete(cle, tile, eco, r, c, gs["seed"], w)]


def test_dit_peint():
    print("\n[C] dit = peint (mare NE du monde full)")
    s = SimServer()
    s.cmd_init({"config": "full", "seed": 42})
    gs = s.engine.game_state
    tile = next(t for t in gs["tiles"] if t.tile_id == "NE")
    eco = gs["eco"]["NE"]
    mous, lib = eco.populations["moustique"], eco.populations["libellule"]
    r, c = 8, 5
    # Hors saison : les deux espèces sous le seuil de présence partout.
    for f in (mous, lib):
        for rr in range(f.rows):
            for cc in range(f.cols):
                f.set(rr, cc, SEUIL_PRESENCE * 0.5)
    check("hors saison : ni l'une ni l'autre n'est peinte",
          not est_peinte(mous) and not est_peinte(lib))
    mous.set(r, c, 0.5)                            # le moustique seul est visible
    textes = _phrases("moustique", tile, eco, r, c, gs)
    check("hors saison : le moustique ne nomme pas la libellule invisible",
          not any("libellule" in p for p in textes), sorted(set(textes))[:3])
    mous.set(r, c, SEUIL_PRESENCE * 0.5)
    lib.set(r, c, 0.5)
    lib.faim = lambda rr, cc: 1.0                  # faim forte → elle parle de proies
    textes = _phrases("libellule", tile, eco, r, c, gs)
    check("hors saison : la libellule ne nomme pas le moustique invisible",
          not any("moustique" in p for p in textes), sorted(set(textes))[:3])
    # En saison : le prédateur est peint → il est nommé, article en minuscule.
    mous.set(r, c, 0.5)
    lib.set(r, c, 0.6)
    del lib.faim
    textes = _phrases("moustique", tile, eco, r, c, gs)
    check("en saison : le moustique nomme la libellule",
          any("libellule" in p for p in textes), sorted(set(textes))[:3])
    check("article en minuscule en milieu de phrase",
          not any("senti La" in p or "chasse Le" in p for p in textes))
    check("tête de phrase en capitale", all(p[:1].isupper() for p in textes))


def main() -> int:
    test_glace_pure()
    test_tick_glace()
    test_dit_peint()
    ko = [n for n, ok in _results if not ok]
    print(f"\n{len(_results) - len(ko)}/{len(_results)} OK")
    return 1 if ko else 0


if __name__ == "__main__":
    raise SystemExit(main())
