"""
SYMBIOSE — tests/test_paillage.py
Tronçon ③ du sprint équilibre invasion (D69) : le champ `paillage` + le geste
`pailler` + ses quatre effets écologiques. On prouve le LEVIER PERMACOLE contre
l'invasion (philo #1/#2 : le mulch change le MILIEU, la réponse émerge) :

  1. Geste `pailler` : dépose le champ `paillage` (cumulatif, cap 1.0), coût MODÉRÉ
     débité ; refus si Vigueur insuffisante (binaire).
  2. Germination férale : un plot MULCHÉ (≥ seuil) ne laisse PAS lever d'adventice,
     alors qu'un plot NU (banque-sol identique) en laisse lever.
  3. `tick_paillage` : le champ DÉCROÎT et reverse la part décomposée à `om_stable`.
  4. Évaporation : sous mulch l'humidité descend MOINS vite (rétention).
  5. Vieillissement de banque : sous mulch les graines enfouies s'épuisent plus vite.
  6. INVARIANT golden : champ nul au repos → tous les lecteurs neutres (paillage=0
     → germination/évaporation/aging strictement inchangés).

Le golden ÉCOLOGIQUE (`tests/test_golden.py`) reste l'autorité du « rien ne bouge
au tick » ; ici on exerce le chemin PAILLÉ, hors golden.

Usage (depuis data/code/) :
  python3 -m tests.test_paillage
"""
from __future__ import annotations

import sys

from world import Tile
from fields import init_eco
from fields.seedbank import SEED_ARCHETYPES, SeedBank, SEED_VIABILITY_LOSS
from fields.ecofields import EcoFields, PAILLAGE_GERM_SEUIL, PAILLAGE_DOSE
from sim import actions as ACT
from sim import vigueur as V
from sim.succession import succession

SEED = 0x5EED
_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK " if cond else "XX "
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


# ---------------------------------------------------------------------------
# 1. Geste `pailler`
# ---------------------------------------------------------------------------
def test_geste_pailler():
    print("\n[1] geste pailler : dépose le champ, coût débité, cumulatif, refus si à sec")
    eco = init_eco("T0", 4, 4, humidite=1.0)
    gs = {"scores": {}, "current_player": "joueur_1", "week": 3, "seed": SEED}
    V.ensure_player(gs, "joueur_1")
    avant = gs["vigueur"]["joueur_1"]["courante"]

    ok = ACT.pailler(gs, "joueur_1", eco, 2, 2)
    check("pailler renvoie True (payé)", ok)
    check("champ paillage déposé au plot ciblé",
          abs(eco.paillage.at_plot(2, 2) - PAILLAGE_DOSE) < 1e-9,
          f"paillage={eco.paillage.at_plot(2, 2):.3f}")
    check("Vigueur débitée", gs["vigueur"]["joueur_1"]["courante"] < avant)
    check("plot voisin intact (geste local)", eco.paillage.at_plot(0, 0) == 0.0)

    ACT.pailler(gs, "joueur_1", eco, 2, 2)     # ré-paille : cumule, cap 1.0
    check("ré-pailler cumule (cap 1.0)",
          eco.paillage.at_plot(2, 2) == min(1.0, 2 * PAILLAGE_DOSE),
          f"paillage={eco.paillage.at_plot(2, 2):.3f}")

    gs["vigueur"]["joueur_1"]["courante"] = 0.0
    ok2 = ACT.pailler(gs, "joueur_1", eco, 0, 3)
    check("Vigueur nulle → refus (binaire), plot intact",
          (ok2 is False) and eco.paillage.at_plot(0, 3) == 0.0)


# ---------------------------------------------------------------------------
# 2. Germination férale étouffée sous mulch
# ---------------------------------------------------------------------------
def _tuile_germinable():
    """Tuile 6×6, niche FAVORABLE partout, banque férale saturée au seul plot (3,3)."""
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = init_eco("T0", 6, 6, humidite=1.5, fertilite=0.5, microbiome=0.3)
    eco.lumiere.fill(1.0)
    eco.disturbance.fill(1.0)
    eco.soil_memory_deep.fill(0.0)
    for r in range(6):
        for c in range(6):
            for a in SEED_ARCHETYPES:
                eco.seed_bank.data[r][c][a] = 0.0
    for a in SEED_ARCHETYPES:
        eco.seed_bank.add(3, 3, a, 1.0)
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {},
          "current_player": "joueur_1", "week": 5, "log": [], "seed": SEED}
    return gs, tile, eco


def _leve_une_adventice(paille: bool) -> bool:
    gs, tile, eco = _tuile_germinable()
    if paille:
        eco.paillage.set(3, 3, 1.0)            # mulch plein sur le plot germinable
    for w in range(5, 80):
        gs["week"] = w
        succession(gs, tile, eco, w)
        if any(p.is_alive and p.position == (3, 3) for p in tile.plants):
            return True
    return False


def test_germination_etouffee():
    print("\n[2] germination férale : nu → lève ; mulché → ne lève pas")
    leve_nu = _leve_une_adventice(paille=False)
    leve_paille = _leve_une_adventice(paille=True)
    check("plot NU : une adventice férale lève (témoin)", leve_nu)
    check("plot MULCHÉ (≥ seuil) : aucune levée férale", not leve_paille)
    check("le seuil de cutoff est bien franchi par le mulch plein",
          1.0 >= PAILLAGE_GERM_SEUIL)


# ---------------------------------------------------------------------------
# 3. tick_paillage : décroissance + reversement à om_stable
# ---------------------------------------------------------------------------
def test_tick_decroissance_om():
    print("\n[3] tick_paillage : le mulch décroît et nourrit om_stable")
    eco = init_eco("T0", 3, 3, humidite=1.0)
    eco.paillage.set(1, 1, 0.8)
    om_avant = eco.om_stable.at_plot(1, 1)
    p_avant = eco.paillage.at_plot(1, 1)
    eco.tick_paillage()
    check("paillage a décru", eco.paillage.at_plot(1, 1) < p_avant,
          f"{p_avant:.3f} → {eco.paillage.at_plot(1, 1):.3f}")
    check("om_stable a monté (part décomposée reversée)",
          eco.om_stable.at_plot(1, 1) > om_avant,
          f"{om_avant:.4f} → {eco.om_stable.at_plot(1, 1):.4f}")


# ---------------------------------------------------------------------------
# 4. Évaporation freinée sous mulch
# ---------------------------------------------------------------------------
def test_evaporation_freinee():
    print("\n[4] évaporation : sous mulch l'humidité descend moins vite")
    eco_nu = init_eco("A", 2, 2, humidite=2.0)
    eco_mu = init_eco("A", 2, 2, humidite=2.0)   # même tile_id → sol identique
    eco_mu.paillage.fill(1.0)
    eco_nu.tick_hydrology("terre")
    eco_mu.tick_hydrology("terre")
    h_nu = eco_nu.humidite.at_plot(0, 0)
    h_mu = eco_mu.humidite.at_plot(0, 0)
    check("le sol mulché retient plus d'humidité que le sol nu", h_mu > h_nu,
          f"nu={h_nu:.4f} mulché={h_mu:.4f}")


# ---------------------------------------------------------------------------
# 5. Vieillissement de banque accéléré sous mulch
# ---------------------------------------------------------------------------
def test_aging_accelere():
    print("\n[5] vieillissement de banque : plus rapide sous mulch")
    from fields.grids import GridField
    sb = SeedBank(2, 2)
    sb.add(0, 0, "pioneer", 1.0)   # plot nu
    sb.add(1, 1, "pioneer", 1.0)   # plot mulché
    paille = GridField(2, 2, max_val=1.0)
    paille.set(1, 1, 1.0)
    sb.tick_aging(paille)
    dens_nu = sb.get(0, 0, "pioneer")
    dens_mu = sb.get(1, 1, "pioneer")
    check("plot nu : vieillissement nominal", abs(dens_nu - SEED_VIABILITY_LOSS) < 1e-9,
          f"{dens_nu:.5f}")
    check("plot mulché : banque plus épuisée (vieillissement accéléré)",
          dens_mu < dens_nu, f"nu={dens_nu:.5f} mulché={dens_mu:.5f}")


# ---------------------------------------------------------------------------
# 6. Invariant golden : champ nul → tous les lecteurs neutres
# ---------------------------------------------------------------------------
def test_invariant_repos():
    print("\n[6] invariant : paillage=0 → lecteurs strictement neutres")
    from fields.grids import GridField
    # aging : sans champ (legacy) ET avec champ nul → identiques
    sb1, sb2 = SeedBank(2, 2), SeedBank(2, 2)
    for sb in (sb1, sb2):
        sb.add(0, 0, "pioneer", 1.0)
    sb1.tick_aging()
    sb2.tick_aging(GridField(2, 2, max_val=1.0))
    check("aging sans champ == aging champ nul", sb1.get(0, 0, "pioneer") == sb2.get(0, 0, "pioneer"))
    # évaporation : deux tuiles identiques, paillage nul → humidité identique
    a = init_eco("Z", 2, 2, humidite=2.0)
    b = init_eco("Z", 2, 2, humidite=2.0)
    a.tick_hydrology("terre")
    b.tick_hydrology("terre")
    check("évaporation à paillage nul == bit-identique",
          a.humidite.at_plot(0, 0) == b.humidite.at_plot(0, 0))
    # tick_paillage sur champ nul → om_stable inchangé
    c = init_eco("Z", 2, 2, humidite=1.0)
    om = c.om_stable.at_plot(0, 0)
    c.tick_paillage()
    check("tick_paillage à champ nul → om_stable inchangé (no-op)",
          c.om_stable.at_plot(0, 0) == om)


def main():
    test_geste_pailler()
    test_germination_etouffee()
    test_tick_decroissance_om()
    test_evaporation_freinee()
    test_aging_accelere()
    test_invariant_repos()
    n_ok = sum(1 for _, ok in _results if ok)
    print(f"\n=== {n_ok}/{len(_results)} OK ===")
    if n_ok != len(_results):
        sys.exit(1)


if __name__ == "__main__":
    main()
