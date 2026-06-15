"""
SYMBIOSE — tests/vigueur/contrats.py
A. Contrats de la couche Vigueur (déterministes, sans RNG) : no-op golden sans
joueur, régen plafonnée, refill au passage de saison, interface paliers (D12).
"""
from sim.engine import Engine
from sim import vigueur as V

from .harness import check, _minimal_state


# ---------------------------------------------------------------------------
# A1. No-op golden : pas de joueur ⇒ le tick n'injecte JAMAIS de Vigueur
# ---------------------------------------------------------------------------

def test_noop_sans_joueur():
    print("\n[A1] sans couche joueur, le tick reste un no-op strict")
    gs = _minimal_state()
    eng = Engine(gs)
    for _ in range(20):
        eng.tick_semaine()
    check("aucune clé `vigueur` créée par le tick", "vigueur" not in gs,
          f"clés={sorted(gs.keys())}")


# ---------------------------------------------------------------------------
# A2. Régen plafonnée
# ---------------------------------------------------------------------------

def test_regen_plafonnee():
    print("\n[A2] régen passive +REGEN_BASE/semaine, plafonnée à vigueur_max")
    gs = {}
    st = V.ensure_player(gs, "joueur_1")
    st["courante"] = 0.0
    V.tick_player_vigueur(gs)
    check("première semaine : 0 → REGEN_BASE", st["courante"] == V.REGEN_BASE,
          f"courante={st['courante']}")
    # On régénère jusqu'au plafond et on vérifie qu'on n'overshoote pas.
    for _ in range(50):
        V.tick_player_vigueur(gs)
    cap = V.vigueur_max(gs, "joueur_1")
    check("plafonnée à vigueur_max (pas d'overshoot)", st["courante"] == cap,
          f"courante={st['courante']} cap={cap}")


# ---------------------------------------------------------------------------
# A3. Refill saison
# ---------------------------------------------------------------------------

def test_refill_saison():
    print("\n[A3] passage de saison : courante = vigueur_max")
    gs = {}
    st = V.ensure_player(gs, "joueur_1")
    st["courante"] = 12.5
    V.refill_saison(gs)
    check("refill → vigueur_max", st["courante"] == V.vigueur_max(gs, "joueur_1"),
          f"courante={st['courante']}")


# ---------------------------------------------------------------------------
# A4. Interface paliers stubbée
# ---------------------------------------------------------------------------

def test_interface_paliers():
    print("\n[A4] interface paliers (D12) remplie par la maîtrise, neutre 1.0 sans savoir")
    gs = {}
    V.ensure_player(gs, "joueur_1")
    check("palier_bonus neutre (1.0) sans maîtrise acquise",
          V.palier_bonus(gs, "joueur_1") == 1.0)
    check("vigueur_max == max_base × palier_bonus",
          V.vigueur_max(gs, "joueur_1") == V.MAX_BASE * V.palier_bonus(gs, "joueur_1"))
    check("regen_rate == REGEN_BASE × palier_bonus",
          V.regen_rate(gs, "joueur_1") == V.REGEN_BASE * V.palier_bonus(gs, "joueur_1"))
