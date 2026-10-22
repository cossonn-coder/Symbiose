"""
SYMBIOSE — tests/test_parasite.py
Parasite de faiblesse (sprint « le sol qui respire » ④, D111 §3.3) : un champignon
`parasite` du registre fongique attaque les racines des hôtes DÉJÀ affaiblis de ses
familles/espèces, par le canal racinaire (`root_herbivory_memory`), et l'hôte RESSENT
la perte (eau perçue ↓ → stress hydrique ↑, convalescence ↓).

  A. hôte VIGOUREUX sur mycélium → pression 0 ;
  B. hôte AFFAIBLI sur mycélium → pression > 0, croissante avec la faiblesse et le réseau ;
  C. famille NON listée (figuier, Moraceae) affaiblie sur mycélium → 0 ;
  D. hôtes tirés des DONNÉES (registre) — jamais en dur ;
  E. neutralité : mémoire racinaire nulle → eau perçue == eau du sol (bit-identique) ;
  F. le canal agit : uptake ↓ et eau perçue ↓ à mémoire > 0 ;
  G. intégration (moteur, 104 sem., sol sec plafonné) : pommier affaibli sur réseau →
     mémoire racinaire ↑, stress hydrique ↑, déficit de vitalité cumulé plus fort que le témoin.
⑦bis (le parasite peut tuer — pourridié du collet `pourriture_memory`) :
  H. pourridié : monte sous pression, redescend sans pression ; eau perçue × (1 − m) ;
  I. banc moteur sol HUMIDE (non plafonné), 156 sem. : hôte affaibli + réseau → MEURT
     (squelette de bois) ; même hôte sans réseau → vit ; hôte vigoureux jamais attaqué ;
  J. déterminisme (même semaine de mort).

Déterministe (zéro RNG). Lancement depuis `data/code` : `python3 -m tests.test_parasite`.
"""
from __future__ import annotations

import sys

from fields import init_eco
from fields.ecofields import EcoFields
from fields.fongique import REGISTRE_FONGIQUE
from plants import PlantInstance
from plants.base.instance import SEUIL_SAIN, SEUIL_AFFAIBLI
from plants.perennials import AppleTree, Fig, BirchTree, OakTree
from sim.engine.racines import (HOTES_PARASITES, est_hote, faiblesse,
                                pression_parasite, eau_percue)

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'OK ' if cond else 'XX '} {name}" + (f" — {detail}" if detail else ""))


def _eco(myc: float, hum: float = 1.5) -> EcoFields:
    e = init_eco("t", 6, 6, humidite=hum, fertilite=1.0, microbiome=0.3)
    for r in range(e.rows):
        for c in range(e.cols):
            e.mycelium.set(r, c, myc)
    return e


def _plante(cls, vit: float) -> PlantInstance:
    p = PlantInstance(plant_class=cls, position=(2, 2))
    p.vitalite = vit
    return p


# A. hôte vigoureux
eco = _eco(0.4)
check("A. pommier sain sur réseau 0,4 → pression 0",
      pression_parasite(_plante(AppleTree, 1.0), eco) == 0.0)
check("A. pommier juste au seuil sain → pression 0",
      pression_parasite(_plante(AppleTree, SEUIL_SAIN + 1e-9), eco) == 0.0)

# B. hôte affaibli
p_aff = pression_parasite(_plante(AppleTree, 0.7), eco)
p_mal = pression_parasite(_plante(AppleTree, 0.4), eco)
p_peu = pression_parasite(_plante(AppleTree, 0.4), _eco(0.1))
check("B. pommier affaibli → pression > 0", p_aff > 0.0, f"{p_aff:.3f}")
check("B. plus faible → pression plus forte", p_mal > p_aff, f"{p_aff:.3f} < {p_mal:.3f}")
check("B. moins de réseau → pression plus faible", p_peu < p_mal, f"{p_peu:.3f} < {p_mal:.3f}")
check("B. sans mycélium → pression 0",
      pression_parasite(_plante(AppleTree, 0.4), _eco(0.0)) == 0.0)
check("B. bouleau (polypore) et chêne (armillaire, Fagaceae) attaquables",
      pression_parasite(_plante(BirchTree, 0.4), eco) > 0
      and pression_parasite(_plante(OakTree, 0.4), eco) > 0)
check("B. faiblesse : 0 au seuil sain, 1 au seuil malade",
      faiblesse(_plante(AppleTree, SEUIL_SAIN)) == 0.0
      and abs(faiblesse(_plante(AppleTree, SEUIL_AFFAIBLI)) - 1.0) < 1e-12)

# C. non-hôte
check("C. figuier (Moraceae) affaibli sur réseau → 0",
      not est_hote(_plante(Fig, 0.4)) and pression_parasite(_plante(Fig, 0.4), eco) == 0.0)

# D. données
attendus = {h for e in REGISTRE_FONGIQUE.values() if e.parasite for h in e.hotes}
check("D. hôtes = union des hôtes des espèces `parasite` du registre",
      HOTES_PARASITES == attendus and attendus, sorted(attendus))
check("D. hôtes des mycorhiziens NON attaqués (Pinaceae de la tue-mouches)",
      "Pinaceae" not in HOTES_PARASITES)

# E. neutralité
p0 = _plante(AppleTree, 0.4)
check("E. mémoire 0 → eau perçue == eau du sol", eau_percue(p0, eco, 1.2345) == 1.2345)

# F. le canal agit
p1 = _plante(AppleTree, 0.4)
p1.root_herbivory_memory = 0.8
e_sain, e_ronge = _eco(0.4), _eco(0.4)
u0 = e_sain.plant_uptake(2, 2, 2, root_herbivory_memory=0.0,
                         root_loss_tolerance=AppleTree.root_loss_tolerance_base)
u1 = e_ronge.plant_uptake(2, 2, 2, root_herbivory_memory=0.8,
                          root_loss_tolerance=AppleTree.root_loss_tolerance_base)
check("F. uptake d'eau ↓ à mémoire 0,8", u1["humidite"] < u0["humidite"],
      f"{u0['humidite']} → {u1['humidite']}")
check("F. eau perçue ↓ à mémoire 0,8", eau_percue(p1, eco, 1.0) < 1.0,
      f"{eau_percue(p1, eco, 1.0):.3f}")


# G. intégration moteur
def _run(myc: float, hum_max: float = 0.4, n: int = 104):
    from world import Tile
    from sim.engine import Engine
    from sim.precroissance import pre_croitre
    tile = Tile(tile_id="T0", soil_type="terre", origin_x_cm=0, origin_y_cm=0)
    e = init_eco("T0", 6, 6, humidite=1.5, fertilite=1.0, microbiome=0.3,
                 soil_type="terre", heterogene=True)
    p = tile.add_plant(AppleTree, 2, 2)
    p.age_years = 8
    p.current_stage = len(AppleTree.growth_stages) - 1
    pre_croitre(p, 42, 8)
    p.vitalite = 0.6
    gs = {"tiles": [tile], "eco": {"T0": e}, "scores": {}, "current_player": "j",
          "week": 1, "log": []}
    eng = Engine(gs)
    orig = Engine._apply_uptake

    def force(self, t, ec, *a, **k):        # réseau et sol sec imposés (banc)
        for r in range(ec.rows):
            for c in range(ec.cols):
                ec.mycelium.set(r, c, myc)
                ec.humidite.set(r, c, min(hum_max, ec.humidite.at_plot(r, c)))
        return orig(self, t, ec, *a, **k)
    Engine._apply_uptake = force
    mem = dm = 0.0
    deficit = 0.0
    try:
        for _ in range(n):
            eng.tick_semaine()
            gs["log"].clear()
            mem = max(mem, p.root_herbivory_memory)
            dm = max(dm, p.drought_memory)
            deficit += 1.0 - p.vitalite
    finally:
        Engine._apply_uptake = orig
    return mem, dm, deficit


t_mem, t_dm, t_ns = _run(0.0)
a_mem, a_dm, a_ns = _run(0.4)
check("G. mémoire racinaire ↑ sous le parasite", a_mem > t_mem + 0.3,
      f"{t_mem:.2f} → {a_mem:.2f}")
check("G. stress hydrique ressenti ↑", a_dm > t_dm, f"{t_dm:.2f} → {a_dm:.2f}")
check("G. déclin : déficit de vitalité cumulé ↑ (convalescence freinée)", a_ns > t_ns,
      f"{t_ns:.1f} → {a_ns:.1f}")

# H. pourridié (⑦bis)
from sim.engine.racines import maj_pourriture
ph = _plante(AppleTree, 0.4)
maj_pourriture(ph, 0.5)
m1 = ph.pourriture_memory
maj_pourriture(ph, 0.5)
check("H. pourridié monte sous pression", 0.0 < m1 < ph.pourriture_memory <= 1.0,
      f"{m1:.3f} → {ph.pourriture_memory:.3f}")
m2 = ph.pourriture_memory
maj_pourriture(ph, 0.0)
check("H. pourridié redescend sans pression (racines qui repoussent)",
      ph.pourriture_memory < m2, f"{m2:.3f} → {ph.pourriture_memory:.3f}")
ph.pourriture_memory = 0.75
check("H. eau perçue × (1 − pourridié), sans plafond",
      abs(eau_percue(ph, _eco(0.0), 2.0) - 0.5) < 1e-12, eau_percue(ph, _eco(0.0), 2.0))


# I-J. banc moteur sur sol humide : le parasite TUE un hôte affaibli
def _banc_mort(myc: float, vit: float, n: int = 156):
    from world import Tile
    from sim.engine import Engine
    from sim.precroissance import pre_croitre
    tile = Tile(tile_id="T0", soil_type="terre", origin_x_cm=0, origin_y_cm=0)
    e = init_eco("T0", 6, 6, humidite=1.5, fertilite=1.0, microbiome=0.3,
                 soil_type="terre", heterogene=True)
    p = tile.add_plant(AppleTree, 2, 2)
    p.age_years = 8
    p.current_stage = len(AppleTree.growth_stages) - 1
    pre_croitre(p, 42, 8)
    p.vitalite = vit
    gs = {"tiles": [tile], "eco": {"T0": e}, "scores": {}, "current_player": "j",
          "week": 1, "log": []}
    eng = Engine(gs)
    orig = Engine._apply_uptake

    def force(self, t, ec, *a, **k):        # réseau imposé, sol NON plafonné (humide)
        for r in range(ec.rows):
            for c in range(ec.cols):
                ec.mycelium.set(r, c, myc)
        return orig(self, t, ec, *a, **k)
    Engine._apply_uptake = force
    mort, attaque = None, False
    try:
        for w in range(n):
            if p.vitalite > SEUIL_SAIN and pression_parasite(p, e) > 0.0:
                attaque = True             # garde-fou : un hôte sain n'est jamais attaqué
            eng.tick_semaine()
            gs["log"].clear()
            if not p.is_alive:
                mort = w + 1
                break
    finally:
        Engine._apply_uptake = orig
    return mort, attaque, p


mort_a, att_a, pa = _banc_mort(0.4, 0.6)
mort_t, _, pt = _banc_mort(0.0, 0.6)
check("I. hôte affaibli + réseau 0,4 → MEURT en quelques années", mort_a is not None,
      f"sem. {mort_a}, pourridié {pa.pourriture_memory:.2f}")
check("I. sa mort laisse un squelette de bois (boucle → saprophytes)",
      pa.morte and pa.bois_restant > 0.0 and pa.bois_diam_cm > 1.0,
      f"bois {pa.bois_restant:.2f}, Ø {pa.bois_diam_cm:.1f} cm")
check("I. même hôte SANS réseau → vit", mort_t is None and pt.pourriture_memory == 0.0,
      f"vitalité {pt.vitalite:.2f}")
check("I. un hôte sain n'est jamais attaqué (pression 0 au-dessus de SEUIL_SAIN)", not att_a)
check("J. déterminisme : même semaine de mort", _banc_mort(0.4, 0.6)[0] == mort_a)

n_ok = sum(ok for _, ok in _results)
print(f"\n=== test_parasite : {n_ok}/{len(_results)} OK ===")
sys.exit(0 if n_ok == len(_results) else 1)
