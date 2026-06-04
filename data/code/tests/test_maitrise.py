"""
SYMBIOSE — tests/test_maitrise.py
Golden JOUEUR de la couche Maîtrise (D12, tronçon i1) — distinct du golden
ÉCOLOGIQUE (`tests/test_golden.py`) et du golden POPULATION
(`tests/test_population.py`).

La couche maîtrise vit dans `game_state["maitrise"]`, AU-DESSUS du tick, et ne
doit JAMAIS faire avancer la simulation écologique (CONCEPTION_MAITRISE.md §6).
Déterministe SANS RNG : les preuves sont *injectées* par appel d'API, comme le
sous-sprint 1 de la Vigueur posait l'état avant de brancher les actions.

Vérifications :
  1. No-op golden : un `game_state` SANS joueur ne se voit JAMAIS injecter de
     clé `maitrise` par le tick (le contrat qui garde le golden écolo intact —
     s'il casse, le golden bouge).
  2. Découverte (§2.1) : palier 0 → 1, gratuite, idempotente ; inconnu = 0.
  3. Progression par preuves (§2.2/§2.3) : franchissement sur la courbe log,
     courbe croissante.
  4. Plafond (§1) : jamais au-delà de PALIER_MAX.
  5. Monotonie (§2.4) : aucune séquence d'appels ne fait baisser un palier.
  6. Déterminisme : même séquence d'injections → même état.

Usage (depuis data/code/) :
  python3 -m tests.test_maitrise
"""
from world import Tile
from plants import Tomato, Basil, Bean
from fields import init_eco
from sim.engine import Engine
from sim import maitrise as M

SEED = 0x5AB1057E
_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _minimal_state(week=1):
    """Monde minimal (1 tuile, 3 plantes) — assez pour tourner le tick à coût
    négligeable. Copie locale du support de `test_vigueur.py` (indépendance)."""
    tile = Tile(tile_id="T0", soil_type="terre")
    eco = init_eco("T0", 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3)
    tile.add_plant(Tomato, 2, 2)
    tile.add_plant(Basil, 2, 4)
    tile.add_plant(Bean, 4, 2)
    return {
        "tiles": [tile], "eco": {"T0": eco}, "scores": {},
        "current_player": "joueur_1", "week": week, "log": [], "seed": SEED,
    }


# ---------------------------------------------------------------------------
# 1. No-op golden : pas de joueur ⇒ le tick n'injecte JAMAIS de maîtrise
# ---------------------------------------------------------------------------

def test_noop_sans_joueur():
    print("\n[1] sans couche joueur, le tick reste un no-op strict (golden écolo intact)")
    gs = _minimal_state()
    eng = Engine(gs)
    for _ in range(20):
        eng.tick_semaine()
    check("aucune clé `maitrise` créée par le tick", "maitrise" not in gs,
          f"clés={sorted(gs.keys())}")


# ---------------------------------------------------------------------------
# 2. Découverte (§2.1) : 0 → 1, gratuite, idempotente
# ---------------------------------------------------------------------------

def test_decouverte():
    print("\n[2] découverte : palier 0 avant, decouvrir → 1, idempotente, inconnu = 0")
    gs = {}
    check("objet inconnu (jamais découvert) → palier 0",
          M.palier(gs, "j", "tomate") == 0)
    check("lecture d'un inconnu n'a PAS créé de clé `maitrise`", "maitrise" not in gs)
    neuf = M.decouvrir(gs, "j", "tomate")
    check("découverte → True (nouvelle)", neuf is True)
    check("palier passe à 1", M.palier(gs, "j", "tomate") == 1)
    redite = M.decouvrir(gs, "j", "tomate")
    check("re-découvrir → False (idempotent)", redite is False)
    check("palier reste 1 (jamais 2 par découverte)", M.palier(gs, "j", "tomate") == 1)
    # Découverte d'un autre objet : strictement indépendante.
    M.decouvrir(gs, "j", "basilic")
    check("objets indépendants (basilic=1, tomate=1)",
          M.palier(gs, "j", "basilic") == 1 and M.palier(gs, "j", "tomate") == 1)


# ---------------------------------------------------------------------------
# 3. Progression par preuves (§2.2/§2.3) + courbe croissante
# ---------------------------------------------------------------------------

def test_courbe_croissante():
    print("\n[3a] courbe de difficulté géométrique strictement croissante (§2.3)")
    req = [M.preuves_requises(k) for k in (1, 2, 3, 4)]
    check("preuves_requises croît avec k (1<2<3<4)",
          req[0] < req[1] < req[2] < req[3], f"requises(1..4)={req}")
    check("requises(1) == PREUVES_BASE", req[0] == M.PREUVES_BASE, f"={req[0]}")


def test_progression():
    print("\n[3b] progression : injecter requires(1) preuves → palier 1 → 2")
    gs = {}
    M.decouvrir(gs, "j", "tomate")
    besoin = M.preuves_requises(1)
    for i in range(besoin - 1):
        p = M.enregistrer_preuve(gs, "j", "tomate")
        check(f"avant le quota (preuve {i+1}/{besoin}) : reste au palier 1", p == 1)
    p = M.enregistrer_preuve(gs, "j", "tomate")
    check("quota atteint → franchit au palier 2", p == 2, f"palier={p}")

    # Reliquat : une grosse fournée peut franchir plusieurs paliers d'un coup,
    # le reliquat reste au crédit du palier suivant (consommation cumulative).
    gs2 = {}
    total = M.preuves_requises(1) + M.preuves_requises(2)   # franchit 1→2→3 pile
    for _ in range(total):
        M.enregistrer_preuve(gs2, "j", "tomate")
    check("requires(1)+requires(2) preuves → palier 3 (cumulatif)",
          M.palier(gs2, "j", "tomate") == 3, f"palier={M.palier(gs2,'j','tomate')}")

    # Auto-découverte : une preuve sur un inconnu le découvre d'abord (§ défaut).
    gs3 = {}
    p3 = M.enregistrer_preuve(gs3, "j", "haricot")
    check("preuve sur inconnu → auto-découverte (palier ≥ 1)", p3 >= 1, f"palier={p3}")


# ---------------------------------------------------------------------------
# 4. Plafond (§1) : jamais au-delà de PALIER_MAX
# ---------------------------------------------------------------------------

def test_plafond():
    print("\n[4] plafond : sur-injection massive ne dépasse jamais PALIER_MAX")
    gs = {}
    M.decouvrir(gs, "j", "tomate")
    for _ in range(10_000):
        M.enregistrer_preuve(gs, "j", "tomate")
    check(f"palier plafonné à {M.PALIER_MAX} (transcendant)",
          M.palier(gs, "j", "tomate") == M.PALIER_MAX,
          f"palier={M.palier(gs, 'j', 'tomate')}")


# ---------------------------------------------------------------------------
# 5. Monotonie (§2.4) : aucune séquence ne fait baisser un palier
# ---------------------------------------------------------------------------

def test_monotonie():
    print("\n[5] monotonie : le palier ne redescend jamais le long d'une séquence")
    gs = {}
    M.decouvrir(gs, "j", "tomate")
    precedent = M.palier(gs, "j", "tomate")
    monotone = True
    for _ in range(200):
        courant = M.enregistrer_preuve(gs, "j", "tomate")
        if courant < precedent:
            monotone = False
        precedent = courant
    check("palier non décroissant sur 200 preuves", monotone)
    check("aucune API de décrément exposée",
          not hasattr(M, "oublier") and not hasattr(M, "decrementer"))


# ---------------------------------------------------------------------------
# 6. Déterminisme : même séquence d'injections → même état
# ---------------------------------------------------------------------------

def test_determinisme():
    print("\n[6] déterminisme : même séquence d'injections → même état exact")
    def run():
        gs = {}
        M.decouvrir(gs, "j", "tomate")
        M.decouvrir(gs, "j", "basilic")
        for _ in range(7):
            M.enregistrer_preuve(gs, "j", "tomate")
        for _ in range(3):
            M.enregistrer_preuve(gs, "j", "basilic")
        return gs["maitrise"]
    a, b = run(), run()
    check("deux exécutions identiques → état identique", a == b, f"{a} == {b}")


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Golden JOUEUR Maîtrise (D12, tronçon i1)")
    print("=" * 60)
    test_noop_sans_joueur()
    test_decouverte()
    test_courbe_croissante()
    test_progression()
    test_plafond()
    test_monotonie()
    test_determinisme()

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
