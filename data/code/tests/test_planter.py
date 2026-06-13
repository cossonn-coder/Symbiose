"""
SYMBIOSE — tests/test_planter.py
Tests ciblés du geste `planter` (Session A du sprint planter/arroser) — geste
event-driven AU-DESSUS du tick : il DÉPOSE une `GrainEnAttente` (banque-joueur,
gènes propres), que la succession lève au bon moment (plot libre + niche).

Couvre (critères Session A) :
  1. Dépôt : take banque-joueur, grain posé, coût FAIBLE débité.
  2. Refus lot vide : aucune Vigueur dépensée, aucun grain.
  3. Levée : gènes PROPRES (pas neutres, pas échantillonnés) + tag `replante`.
  4. Empilement (Q4) : plot occupé → la graine PATIENTE, puis lève au dégagement.

Le golden ÉCOLOGIQUE (`tests/test_golden.py`) reste l'autorité du « rien ne
bouge au tick » ; ici on exerce le chemin planté, hors golden.

Usage (depuis data/code/) :
  python3 -m tests.test_planter
"""
import sys

from world import Tile
from plants import Tomato
from fields import init_eco
from sim import actions as ACT
from sim import vigueur as V
from sim import maitrise_detection as MD
from sim.seeds import Seed, PlayerSeedBank
from sim.succession import succession

SEED = 0x5EED
_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK " if cond else "XX "
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _state_avec_graine(species="tomate", genes=None, n=1):
    """Monde minimal + banque-joueur portant `n` graine(s) de `species`. Niche
    rendue FAVORABLE (pleine lumière, sol perturbé, sol jeune) pour que la levée
    soit fiable et déterministe quand on appelle `succession` directement."""
    tile = Tile(tile_id="T0", soil_type="terre")
    eco = init_eco("T0", 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3)
    eco.lumiere.fill(1.0)
    eco.disturbance.fill(1.0)
    eco.soil_memory_deep.fill(0.0)
    bank = PlayerSeedBank()
    for _ in range(n):
        bank.add(Seed(species=species, genes=dict(genes) if genes else {"hauteur": 1.42}))
    gs = {
        "tiles": [tile], "eco": {"T0": eco}, "scores": {},
        "current_player": "joueur_1", "week": 3, "log": [], "seed": SEED,
        "player_seed_bank": bank,
    }
    return gs, tile, eco, bank


# ---------------------------------------------------------------------------
# 1. Dépôt + coût
# ---------------------------------------------------------------------------
def test_depot():
    print("\n[1] dépôt : take banque-joueur, grain posé, coût FAIBLE débité")
    gs, tile, eco, bank = _state_avec_graine()
    V.ensure_player(gs, "joueur_1")
    avant = gs["vigueur"]["joueur_1"]["courante"]

    ok = ACT.planter(gs, "joueur_1", tile, eco, "tomate", 2, 2)
    apres = gs["vigueur"]["joueur_1"]["courante"]

    check("planter renvoie True", ok)
    check("graine retirée de la banque-joueur", bank.count("tomate") == 0,
          f"reste={bank.count('tomate')}")
    check("un grain déposé au plot (2,2)", len(tile.grains_en_attente.get((2, 2), [])) == 1)
    check("coût FAIBLE débité", abs((avant - apres) - ACT.FAIBLE) < 1e-9,
          f"débit={avant - apres:.2f} attendu={ACT.FAIBLE}")
    g = tile.grains_en_attente[(2, 2)][0]
    check("grain tagué cultive=True", g.cultive is True)
    check("grain porte l'avatar planteur", g.player == "joueur_1")
    check("grain garde ses gènes PROPRES", g.genes.get("hauteur") == 1.42)


# ---------------------------------------------------------------------------
# 2. Refus lot vide — aucune dépense
# ---------------------------------------------------------------------------
def test_refus_lot_vide():
    print("\n[2] lot vide : refus EN AMONT, aucune Vigueur dépensée")
    gs, tile, eco, bank = _state_avec_graine(n=0)   # banque vide
    V.ensure_player(gs, "joueur_1")
    avant = gs["vigueur"]["joueur_1"]["courante"]

    ok = ACT.planter(gs, "joueur_1", tile, eco, "tomate", 2, 2)
    apres = gs["vigueur"]["joueur_1"]["courante"]

    check("planter renvoie False (lot vide)", ok is False)
    check("aucun grain déposé", (2, 2) not in tile.grains_en_attente)
    check("aucune Vigueur dépensée", apres == avant, f"avant={avant} après={apres}")


# ---------------------------------------------------------------------------
# 3. Levée : gènes propres + tag replante transmis
# ---------------------------------------------------------------------------
def test_levee():
    print("\n[3] levée sur plot libre : gènes propres + tag replante")
    gs, tile, eco, bank = _state_avec_graine(genes={"hauteur": 1.42})
    V.ensure_player(gs, "joueur_1")
    ACT.planter(gs, "joueur_1", tile, eco, "tomate", 2, 2)

    germ = None
    for w in range(3, 15):
        gs["week"] = w
        succession(gs, tile, eco, w)
        alive = [p for p in tile.plants if p.is_alive and p.position == (2, 2)]
        if alive:
            germ = alive[0]
            break

    check("la graine plantée a levé en quelques semaines", germ is not None)
    if germ is not None:
        check("c'est bien une tomate", germ.plant_class is Tomato)
        check("gènes PROPRES transmis (hauteur=1.42, ni neutre ni échantillonné)",
              germ.genes.get("hauteur") == 1.42, f"hauteur={germ.genes.get('hauteur')}")
        check("plus de grain en attente sur le plot", not tile.grains_en_attente.get((2, 2)))
        replante = MD._detection(gs, "joueur_1")["replante"]
        check("zone marquée replantée (cultivé vs féral, §9.4)",
              ("T0", 2, 2) in replante, f"replante={replante}")


# ---------------------------------------------------------------------------
# 4. Empilement (Q4) : plot occupé → patiente → lève au dégagement
# ---------------------------------------------------------------------------
def test_empilement_patiente():
    print("\n[4] plot occupé : la graine patiente, puis lève une fois libéré")
    gs, tile, eco, bank = _state_avec_graine()
    V.ensure_player(gs, "joueur_1")
    occupant = tile.add_plant(Tomato, 2, 2)        # plot déjà occupé
    ACT.planter(gs, "joueur_1", tile, eco, "tomate", 2, 2)

    for w in range(3, 10):
        gs["week"] = w
        succession(gs, tile, eco, w)
    patiente = len(tile.grains_en_attente.get((2, 2), [])) == 1
    pas_de_doublon = sum(1 for p in tile.plants if p.is_alive and p.position == (2, 2)) == 1
    check("plot occupé → la graine PATIENTE (toujours en attente)", patiente)
    check("aucune levée tant que le plot est pris", pas_de_doublon)

    tile.remove_plant(occupant)                    # on libère le plot
    leve = False
    for w in range(10, 22):
        gs["week"] = w
        succession(gs, tile, eco, w)
        if any(p.is_alive and p.position == (2, 2) for p in tile.plants):
            leve = bool(tile.grains_en_attente.get((2, 2), []) == [])
            break
    check("la graine lève une fois le plot libéré", leve)


def main():
    test_depot()
    test_refus_lot_vide()
    test_levee()
    test_empilement_patiente()
    n_ok = sum(1 for _, ok in _results if ok)
    n = len(_results)
    print(f"\n[test_planter] {n_ok}/{n} OK")
    if n_ok != n:
        echecs = [name for name, ok in _results if not ok]
        print("ÉCHECS : " + ", ".join(echecs))
        sys.exit(1)
    print("[test_planter] PASS")


if __name__ == "__main__":
    main()
