"""
SYMBIOSE — tests/test_posture_thermique.py
Signes thermiques par paliers (D139, sprint niche thermique ④). Hors golden :
plantes et EcoFields à conditions forcées.

Vérifie :
  - posture < 0 pour un basilic une nuit à 7 °C, ≈ 0 à 20 °C, > 0 pour une plante
    assoiffée au soleil en canicule ;
  - DRY : chaque palier de DÉGÂT s'allume au seuil MÊME du moteur (`lim_froid`,
    `lim_gel`, `lim_chaud`, `lim_brul`), et le palier d'annonce 3 °C avant ;
  - `_tick_nuit_froide` mémorise la nuit (`t_nuit`) que la posture relit ;
  - les marques `froid`/`brulure` passent dans `leaf_symptoms` et prolongent le palier ;
  - la lecture est PURE (aucun attribut de la plante modifié).

Usage (depuis data/code/) :
  python3 -m tests.test_posture_thermique
"""
import sys

from world import Tile
from plants import Basil, CornSalad, BursaPastoris
from fields import init_eco
from sim import semiologie
from sim.engine import Engine
import sim.engine.reponse_thermique as RT
from sim.engine.posture_thermique import etat_thermique, MARGE_ANNONCE

_results = []
EPS = 0.01


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'OK ' if cond else 'XX '} {name}" + (f" — {detail}" if detail else ""))


def lab(*especes, hum=1.2):
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = init_eco("T0", 6, 6, humidite=hum, fertilite=1.2, microbiome=0.3)
    plantes = [tile.add_plant(cls, 1 + 2 * i, 1 + 2 * i) for i, cls in enumerate(especes)]
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {}, "seed": 42,
          "current_player": "j1", "week": 20, "log": []}
    return Engine(gs), tile, eco, plantes


def test_trois_cas():
    print("\n[1] froid, confort, chaud")
    _, _, eco, (b,) = lab(Basil)
    b.t_nuit, b.t_feuille = 7.0, 22.0
    v, pal = etat_thermique(b, eco)
    check("basilic, nuit à 7 °C : posture < 0", v < 0.0, f"{v} {pal}")
    b.t_nuit, b.t_feuille = 20.0, 22.0
    v, pal = etat_thermique(b, eco)
    check("basilic, nuit à 20 °C : posture ≈ 0, feuilles étalées", v == 0.0 and pal is None,
          f"{v} {pal}")
    _, _, eco, (p,) = lab(BursaPastoris, hum=0.0)
    p.t_nuit, p.t_feuille = 22.0, p.lim_chaud() - 1.0
    v, pal = etat_thermique(p, eco)
    check("assoiffée au soleil, feuille près de lim_chaud : flétrie à midi",
          v > 0.25 and pal == "fletri_midi", f"{v} {pal}")
    p.t_feuille = p.lim_brul() + 2.0
    v, pal = etat_thermique(p, eco)
    check("canicule, feuille > lim_brul : brûlée, posture > 0.75", v > 0.75 and pal == "brulure",
          f"{v} {pal}")


def test_dry():
    print("\n[2] DRY : le palier de dégât s'allume au seuil même du moteur")
    _, _, eco, (b, m) = lab(Basil, CornSalad)
    lf = b.lim_froid()
    b.t_nuit = lf + MARGE_ANNONCE + EPS
    check("basilic : rien 3 °C au-dessus de lim_froid", etat_thermique(b, eco)[1] is None)
    b.t_nuit = lf + EPS
    v, pal = etat_thermique(b, eco)
    check("basilic : annonce (pendant) juste au-dessus de lim_froid",
          pal == "pendant" and -0.25 <= v < 0.0, f"{v} {pal}")
    b.t_nuit = lf - EPS
    v, pal = etat_thermique(b, eco)
    check("basilic : translucide (froid) juste sous lim_froid", pal == "froid" and v <= -0.5,
          f"{v} {pal}")
    lg = m.lim_gel()
    m.t_nuit = lg + EPS
    check("mâche (pas de lésion sans gel) : pas noircie au-dessus de lim_gel",
          etat_thermique(m, eco)[1] == "pendant")
    m.t_nuit = lg - EPS
    v, pal = etat_thermique(m, eco)
    check("mâche : noircie (gel) juste sous lim_gel", pal == "gel" and v <= -0.75, f"{v} {pal}")
    m.cold_memory = 1.0
    m.t_nuit = lg + 0.5
    check("mâche endurcie au froid prolongé : violacée",
          etat_thermique(m, eco)[1] == "violace")
    _, _, eco, (p,) = lab(BursaPastoris, hum=1.2)
    p.t_feuille = p.lim_chaud() - EPS
    check("feuille juste sous lim_chaud (arrosée) : repliée",
          etat_thermique(p, eco)[1] == "replie")
    p.t_feuille = p.lim_chaud() + EPS
    check("feuille juste au-dessus de lim_chaud : bords jaunis",
          etat_thermique(p, eco)[1] == "bords_jaunis")
    p.t_feuille = p.lim_brul() + EPS
    check("feuille juste au-dessus de lim_brul : brûlée", etat_thermique(p, eco)[1] == "brulure")


def test_tick_et_marques():
    print("\n[3] nuit mémorisée au tick, marques froid → leaf_symptoms")
    eng, tile, eco, (b,) = lab(Basil)
    vieux = RT.t_min_nuit_at
    RT.t_min_nuit_at = lambda *a: 6.0
    try:
        eng._tick_nuit_froide(tile, eco, 12.0, 0.5)
    finally:
        RT.t_min_nuit_at = vieux
    check("t_nuit mémorisée par le tick", b.t_nuit == 6.0)
    causes = [s["cause"] for s in semiologie.leaf_symptoms(b, eco, "printemps")]
    check("marque `froid` dans leaf_symptoms", "froid" in causes, causes)
    b.t_nuit = 25.0                       # la nuit s'est radoucie, la marque reste
    v, pal = etat_thermique(b, eco)
    check("la marque prolonge le palier translucide", pal == "froid" and v <= -0.5, f"{v} {pal}")
    avant = dict(vars(b))
    etat_thermique(b, eco)
    check("lecture pure (plante inchangée)", dict(vars(b)) == avant)


if __name__ == "__main__":
    test_trois_cas()
    test_dry()
    test_tick_et_marques()
    ok = sum(1 for _, r in _results if r)
    print(f"\n{ok}/{len(_results)} OK")
    sys.exit(0 if ok == len(_results) else 1)
