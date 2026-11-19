"""
SYMBIOSE — tests/test_vieillesse_cycle.py
Vieillesse, fin de cycle et paiement racinaire au BILAN (D140 G, stress au bilan ④).

  [bilan]       passé l'onset, le vieux sujet produit moins et coûte plus : même
                semaine, même plante, le solde baisse avec `vieillesse` ;
  [longévité]   arbres et vivaces isolés (labo sans pluie ni gel, comme
                `test_senescence`), posés adultes un an avant l'onset : ils meurent
                « de sénescence » PAR LE BILAN (plus aucun tirage), à ±20 % de l'âge où
                l'ancien tirage `SEN_RATE` les tuait (onset + ½·(1 − onset)·L ≈ 0,85 L) ;
  [fin de cycle] une annuelle qui a fini de mûrir ses graines remobilise ses réserves
                vers elles puis meurt ; une mère affamée remplit moins de graines ;
  [exsudats]    le dépôt d'exsudats suit la vraie part carbone X du bilan : ∝ à la
                production, et au gène `mycorhization` (la plante paie ses champignons).

Lancement (depuis data/code/) :  python3 -m tests.test_vieillesse_cycle   (~30 s)
"""

import sys

from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE
from world import Tile
from fields import init_eco
from sim.engine import Engine
from sim.bilan import semaine_bilan
from sim.tempo import onset_senescence
from sim.evenements import evenements
from sim.weather import CALME
import sim.engine.boucle as _boucle
import sim.wind as _wind
import sim.champignon_role as _champ_role
import tests.test_senescence as _labo_sen

ETE = dict(saison="ete", presence=1.0, light_eff=1.0, hum_percue=0.8, temp=20.0,
           t_feuille=24.0, t_air=20.0, f_nut=1.0, f_allelo=1.0)
_fails = []


def check(nom, ok, detail=""):
    print(f"  {'OK ' if ok else 'KO '} {nom} {detail}")
    if not ok:
        _fails.append(nom)


def _monde(rows=6, cols=6):
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=rows, grid_cols=cols)
    eco = init_eco("T0", rows, cols, humidite=1.5, fertilite=1.2, microbiome=0.3)
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {}, "seed": 42,
          "current_player": "j", "week": 1, "log": []}
    return tile, eco, Engine(gs), gs


def _adulte(tile, cle, r=3, c=3):
    cls = PLANT_CATALOGUE.get(cle) or PERENNIAL_CATALOGUE[cle]
    p = tile.add_plant(cls, r, c)
    p.current_stage = len(cls.growth_stages) - 1
    p.age_years = float(getattr(cls, "maturity_years", 0.0) or 0.0)
    return p


def test_bilan_vieillesse():
    print("\n[bilan] le vieux sujet produit moins et coûte plus")
    tile, _, _, _ = _monde()
    nets = []
    for v in (0.0, 0.25, 0.5):
        p = _adulte(tile, "pommier")
        p.reserves = 0.5
        semaine_bilan(p, vieillesse=v, **ETE)
        nets.append(p.bilan_net)
    check("solde décroissant avec l'âge", nets[0] > nets[1] > nets[2],
          " ".join(f"{n:+.2f}" for n in nets))
    check("sans âge, le même été est positif", nets[0] > 0.0, f"{nets[0]:+.2f}")


def _longevite(cle):
    """Âge et ligne de mort d'un sujet isolé posé adulte un an avant son onset."""
    tile, eco, eng, gs = _monde()
    eco.seed_bank.germination_candidates = lambda *a, **k: []
    p = _adulte(tile, cle)
    L = p.plant_class.longevity()
    p.age_years = max(p.age_years, onset_senescence(p) * L - 1.0)
    tag = f"{p.name}@{p.position}"
    for _ in range(int(L * 52) + 104):
        log = eng.tick_semaine()
        if not p.is_alive:
            causes = [e.cause for e in evenements(log) if e.kind == "mort"]
            return p.age_years, L, onset_senescence(p) * L, causes, \
                next((l for l in log if tag in l and "🪦" in l), "")
        gs["log"].clear()
    return p.age_years, L, onset_senescence(p) * L, [], "vivant"


def test_longevites():
    print("\n[longévité] mort de vieillesse par le bilan, ±20 % de l'ancien âge")
    sauve = (_boucle.weather_state, _wind.weather_at, _champ_role.weather_state)
    _boucle.weather_state = _labo_sen._meteo_labo
    _wind.weather_at = lambda seed, week: CALME
    _champ_role.weather_state = _labo_sen._meteo_labo
    try:
        for cle in ("cerisier", "pommier", "lierre", "lavande", "consoude", "ortie"):
            age, L, onset, causes, ligne = _longevite(cle)
            ref = onset + 0.5 * (L - onset)
            check(f"{cle} meurt de sénescence", "sénescence" in causes
                  and "épuisé par l'âge" in ligne, ligne.strip()[:70])
            check(f"{cle} longévité ±20 %", abs(age / ref - 1.0) <= 0.20,
                  f"âge {age:.1f} / réf {ref:.1f} (L {L:.0f})")
    finally:
        _boucle.weather_state, _wind.weather_at, _champ_role.weather_state = sauve


def _fin_de_cycle(reserves):
    """Annuelle (phacélie) fécondée dont les graines sont mûres : semaines de
    remobilisation jusqu'à la mort, graines transférées, densité de la banque."""
    tile, eco, eng, _ = _monde()
    p = _adulte(tile, "phacelie")
    p.fecondation, p.reserves = 1.0, reserves
    eng.game_state["week"] = 100
    p.floraison_abs = 50                       # floraison + maturation largement passées
    avant = eco.seed_bank.species_density(3, 3, p.plant_class)
    for n in range(1, 10):
        log = eng._tick_senescence_health(tile, eco)
        if not p.is_alive:
            break
    return (n, p.graines_reserves, any("fin de cycle" in l for l in log),
            eco.seed_bank.species_density(3, 3, p.plant_class) - avant)


def test_fin_de_cycle():
    print("\n[fin de cycle] remobilisation vers les graines, puis mort")
    n, g, ligne, graines = _fin_de_cycle(1.0)
    check("mère nourrie : morte en 3 semaines, fin de cycle consignée",
          n == 3 and ligne, f"{n} sem")
    check("toutes ses réserves passées aux graines", abs(g - 1.0) < 1e-6, f"{g:.2f}")
    n2, g2, _, graines2 = _fin_de_cycle(0.3)
    check("mère affamée : morte en 1 semaine, 0,3 transféré",
          n2 == 1 and abs(g2 - 0.3) < 1e-6, f"{n2} sem, {g2:.2f}")
    check("graines semées ∝ réserves transférées", graines > 0 and
          abs(graines2 / graines - 0.3) < 0.02, f"{graines:.4f} vs {graines2:.4f}")


def _depot(part, myco=None):
    tile, eco, eng, _ = _monde()
    p = _adulte(tile, "pommier")
    if myco is not None:
        p.genes["mycorhization"] = myco
        semaine_bilan(p, **ETE)
    else:
        p.part_racinaire = part
    avant = sum(map(sum, eco.microbiome.data))
    eng._apply_exudates(tile, eco)
    return sum(map(sum, eco.microbiome.data)) - avant, p.part_racinaire


def test_exsudats():
    print("\n[exsudats] le dépôt suit la part carbone du bilan")
    d0, _ = _depot(0.0)
    d1, _ = _depot(0.1)
    d2, _ = _depot(0.2)
    check("rien payé, rien déposé", d0 == 0.0, f"{d0:.4f}")
    check("dépôt ∝ part racinaire", d1 > 0 and abs(d2 / d1 - 2.0) < 1e-6,
          f"{d1:.4f} → {d2:.4f}")
    m1, x1 = _depot(None, myco=1.0)
    m2, x2 = _depot(None, myco=1.5)
    check("plus mycorhizée → paie et dépose plus", x2 > x1 and m2 > m1,
          f"X {x1:.3f} → {x2:.3f}")


if __name__ == "__main__":
    test_bilan_vieillesse()
    test_fin_de_cycle()
    test_exsudats()
    test_longevites()
    print(f"\n{'TOUT OK' if not _fails else 'ÉCHECS : ' + ', '.join(_fails)}")
    sys.exit(1 if _fails else 0)
