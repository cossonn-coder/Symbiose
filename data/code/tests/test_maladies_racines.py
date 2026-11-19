"""
SYMBIOSE — tests/test_maladies_racines.py
Maladies et racines au BILAN (D140 G, sprint stress au bilan ③).

  [mildiou]    une contamination NÉCROSE des feuilles (perte de feuillage) mais ne
               détruit jamais la plante, même affaiblie (avant : un cran de santé qui
               dépassait la vitalité restante la tuait) ;
  [oïdium]     une contamination COUVRE les feuilles : aucun tissu retiré, production
               du bilan baissée, couverture qui s'efface en quelques semaines ;
  [fonte]      la fonte des semis pourrit le collet : DESTRUCTION, même d'une plantule
               de constitution robuste (trèfle, `resilience_base` 1,25) ; lue `maladie` ;
  [asphyxie]   un sol gorgé fait mourir des RACINES (`pourriture_memory`) — plus chez
               le pommier que chez l'aulne (hélophyte) — sans aucun cran de vitalité
               au sort ; sol ressuyé : la plante a soif (eau ressentie < eau du sol) ;
               des racines pourries ne font pas « sortir » la plante de l'excès d'eau ;
  [annélation] un jeune ligneux annelé par le campagnol meurt (destruction) et la mort
               est CONSIGNÉE (« meurt annelé » → cause `herbivorie`), une seule fois.

Tirages forcés par `_hash_noise` remplacé en mémoire (on teste ce que la contamination
FAIT, pas sa probabilité). Lancement (depuis data/code/) :
    python3 -m tests.test_maladies_racines
"""

import sys

from plants import PlantInstance
from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE
from world import Tile
from fields import init_eco, VITALITE_STEP
from sim.engine import Engine
from sim.bilan import semaine_bilan, bilan, f_eau
from sim.effects import apply_mutations
from sim.effects import perturbations as P
from sim.effects.mutations import PerteTissus, Oidium
from sim.engine.racines import eau_percue
from sim.evenements import evenements

ETE = dict(saison="ete", presence=1.0, light_eff=1.0, temp=20.0, t_feuille=24.0,
           t_air=20.0, f_nut=1.0, f_allelo=1.0)


def _labo(hum=1.2, t=20.0):
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = init_eco("T0", 6, 6, humidite=hum, fertilite=1.2, microbiome=0.3)
    eco.temperature.at_plot = lambda r, c: t
    eco.temperature_sol.at_plot = lambda r, c: t - 2.0
    return tile, eco


def _adulte(tile, cle, r=3, c=3, cat=PLANT_CATALOGUE):
    p = tile.add_plant(cat[cle], r, c)
    p.current_stage = len(p.plant_class.growth_stages) - 1
    if cat is PERENNIAL_CATALOGUE:
        p.age_years = float(p.plant_class.maturity_years) + 5.0
    return p


class _Tirage:
    """Remplace le tirage déterministe de `perturbations` par 0 (contamination sûre)."""
    def __enter__(self):
        self.orig = P._hash_noise
        P._hash_noise = lambda *a, **k: 0.0
    def __exit__(self, *exc):
        P._hash_noise = self.orig


def test_mildiou():
    tile, eco = _labo()
    tom = _adulte(tile, "tomate")
    tom.wetness_memory = 1.0
    tom.reserves, tom.feuillage = 0.3, 0.2      # affaiblie : vitalité 0,36
    v0 = tom.vitalite
    with _Tirage():
        muts = P.fungal_disease(tom, tile, eco, 42, 26)
    assert muts and isinstance(muts[0], PerteTissus), muts
    perte = muts[0].feuillage
    assert perte > v0                           # l'ancien `erode` l'aurait détruite
    apply_mutations(muts, {"tiles": [tile], "eco": {"T0": eco}})
    assert tom.is_alive and tom.feuillage == 0.0 and tom.reserves == 0.3, tom
    assert tom.symptom_marks.get("maladie", 0.0) > 0.0
    print(f"[mildiou] PASS — coup {perte:.2f} de feuillage sur vitalité {v0:.2f} : "
          f"feuilles perdues, plante vivante (réserves {tom.reserves:.2f})")


def test_oidium():
    tile, eco = _labo(t=28.0)
    cou = _adulte(tile, "courgette")
    cou.wetness_memory = 0.0                    # feuillage sec : climat de l'oïdium
    with _Tirage():
        muts = P.oidium_disease(cou, tile, eco, 42, 30)
    assert muts and isinstance(muts[0], Oidium), muts
    apply_mutations(muts, {"tiles": [tile], "eco": {"T0": eco}})
    assert cou.feuillage == 1.0 and abs(cou.oidium - VITALITE_STEP) < 1e-9, cou.oidium
    temoin = PlantInstance(cou.plant_class, (1, 1))
    args = (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 20.0, False)
    p_sale, p_saine = bilan(cou, *args), bilan(temoin, *args)
    assert p_sale < p_saine, (p_sale, p_saine)
    for _ in range(12):
        semaine_bilan(cou, hum_percue=1.2, **ETE)
    assert 0.0 < cou.oidium < 0.1, cou.oidium
    print(f"[oïdium] PASS — feuillage intact, bilan {p_saine:+.2f} → {p_sale:+.2f} ; "
          f"couverture 0,33 → {cou.oidium:.2f} en 12 sem")


def test_fonte():
    tile, eco = _labo(hum=2.5)
    tre = tile.add_plant(PLANT_CATALOGUE["trefle"], 3, 3)
    assert tre.stage.name == "semis" and tre.plant_class.resilience_base > 1.0
    with _Tirage():
        muts = P.damping_off(tre, tile, eco, 42, 14, "printemps")
    assert muts, "fonte attendue (sol détrempé, tirage forcé)"
    log = ["[T0]"] + apply_mutations(muts, {"tiles": [tile], "eco": {"T0": eco}})
    assert not tre.is_alive
    morts = [e for e in evenements(log) if e.kind == "mort"]
    assert morts and morts[0].cause == "maladie", morts
    print(f"[fonte] PASS — semis de trèfle (constitution 1,25) détruit, lu « maladie »")


def _semaines(eng, tile, eco, n, hum):
    eco.humidite.at_plot = lambda r, c: hum
    for _ in range(n):
        eng._update_physiology(tile, eco)


def test_asphyxie():
    tile, eco = _labo()
    pom = _adulte(tile, "pommier", 1, 1, PERENNIAL_CATALOGUE)
    aul = _adulte(tile, "aulne", 4, 4, PERENNIAL_CATALOGUE)
    eng = Engine({"tiles": [tile], "eco": {"T0": eco}, "scores": {},
                  "current_player": "j1", "week": 26, "log": []})
    _semaines(eng, tile, eco, 16, 2.95)               # sol gorgé un été
    assert pom.is_alive and aul.is_alive
    assert pom.pourriture_memory > aul.pourriture_memory > 0.0, \
        (pom.pourriture_memory, aul.pourriture_memory)
    assert pom.limitant == "noyé", pom.limitant
    # Des racines pourries ne rendent pas l'air au sol : le bord « noyé » tient. Sur la
    # moitié du chevelu perdue, l'eau ressentie (1,48) passe sous HUM_NOYE ; lue seule,
    # elle « sortait » la plante de l'excès d'eau (production remontée à tort).
    hp = 2.95 * (1.0 - 0.5)
    assert f_eau(pom, hp, 2.95) < f_eau(pom, hp), (f_eau(pom, hp, 2.95), f_eau(pom, hp))
    m_pic = pom.pourriture_memory
    soif = eau_percue(pom, eco, 0.6)
    assert soif < 0.6 * 0.8, soif                     # ressuyé : la plante a soif
    _semaines(eng, tile, eco, 12, 0.6)                # le chevelu repousse
    assert pom.pourriture_memory < m_pic, (pom.pourriture_memory, m_pic)
    print(f"[asphyxie] PASS — 16 sem gorgées : racines perdues pommier "
          f"{m_pic:.2f} / aulne {aul.pourriture_memory:.2f} ; ressuyé, eau ressentie "
          f"{soif:.2f}/0,60 ; 12 sem plus tard {pom.pourriture_memory:.2f}")


def test_annelation():
    tile, eco = _labo()
    jeune = tile.add_plant(PERENNIAL_CATALOGUE["pommier"], 3, 3)
    assert jeune.current_height <= P.LIGNEUX_ANNELE_CM
    eco.category_density = lambda cat, r, c: (0.6 if cat == "herbivore_vertebre" else 0.3)
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {}, "current_player": "j1",
          "week": 30, "log": []}
    log = ["[T0]"] + P.apply_disturbances(tile, eco, gs, 42, 30, 0.55, "ete")
    assert not jeune.is_alive
    morts = [e for e in evenements(log) if e.kind == "mort"]
    assert len(morts) == 1 and morts[0].cause == "herbivorie", morts
    print(f"[annélation] PASS — {[l.strip() for l in log if 'annelé' in l][0]}")


if __name__ == "__main__":
    for t in (test_mildiou, test_oidium, test_fonte, test_asphyxie, test_annelation):
        t()
    sys.exit(0)
