"""
SYMBIOSE — tests/bancs/test_hydrologie.py
Oracle du banc HYDROLOGIQUE (tronçon ③) : tourbière (marécage installé).

Monte le banc via sa fabrique, simule quelques semaines, puis LIT l'état du sol
(mémoire de marais, `decomp_speed`, pH) sur la cuvette gorgée et le compare au
témoin sec. Prouve le MÉCANISME du marécage (émergent, pas scripté) :
  - la mémoire de marais PERSISTE (hystérèse, `est_marais` vrai) ;
  - la décompo est RALENTIE (anaérobie → tourbe) vs le témoin ;
  - le pH BAISSE (acidification tourbeuse) vs le témoin.
Déterministe (seed fixe du serveur). Lecture pure.

Usage (depuis data/code/) : python3 -m tests.bancs.test_hydrologie
"""
from .oracle import run_banc

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK  " if cond else "FAIL"
    print(f"  [{flag}] {name}" + (f" — {detail}" if detail else ""))


def test_tourbiere():
    """Cuvette gorgée (marais installé) vs témoin sec : le marécage persiste,
    ralentit la décompo et acidifie le pH. Le plot central (4,4) est représentatif
    (tuiles remplies uniformément)."""
    game_state, _ = run_banc("tourbiere", semaines=8)
    tiles = game_state["tiles"]
    marais, temoin = tiles[0], tiles[1]
    eco_m = game_state["eco"][marais.tile_id]
    eco_t = game_state["eco"][temoin.tile_id]
    r, c = 4, 4

    # (1) L'état de marais PERSISTE (hystérèse). La flaque + le sol saturé entretiennent
    #     la mémoire ; elle reste au-dessus de MARAIS_ON → `est_marais` vrai.
    mem = eco_m.marais_memory.at_plot(r, c)
    check("tourbiere — marais installé (mémoire > 0.6)", mem > 0.6,
          f"marais_memory={mem:.3f}")
    check("tourbiere — est_marais vrai (hystérèse)", eco_m.est_marais(r, c),
          f"est_marais={eco_m.est_marais(r, c)}")
    check("tourbiere — témoin sec PAS en marais", not eco_t.est_marais(r, c),
          f"est_marais_temoin={eco_t.est_marais(r, c)}")

    # (2) DÉCOMPO ralentie (anaérobie) : même microbiome, mais le marais rabote la
    #     vitesse → decomp_speed du marais < témoin.
    sp_m = eco_m.decomp_speed(r, c)
    sp_t = eco_t.decomp_speed(r, c)
    check("tourbiere — décompo RALENTIE vs témoin (anaérobie)", sp_m < sp_t,
          f"speed_marais={sp_m:.3f} < speed_temoin={sp_t:.3f}")

    # (3) pH ACIDIFIÉ : la cible du pH est tirée vers PH_TOURBE (acide) → le pH du
    #     marais descend sous le pH du témoin (parti du même 6.8).
    ph_m = eco_m.ph.at_plot(r, c)
    ph_t = eco_t.ph.at_plot(r, c)
    check("tourbiere — pH ACIDIFIÉ vs témoin (tourbière)", ph_m < ph_t,
          f"ph_marais={ph_m:.3f} < ph_temoin={ph_t:.3f}")


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Oracle banc hydrologique (tronçon ③)")
    print("=" * 60)
    test_tourbiere()
    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
