# SYMBIOSE — tools/diag_lod_ombre.py
# Bras FIDÉLITÉ du sprint « LOD des émetteurs d'ombre » (D67, tronçon ①).
#
# Frère du bras PERF `profile_monde.py` : là où celui-ci répond « où part le
# temps », celui-ci répond « qu'est-ce que le LOD CHANGE, écologiquement, et le
# gain vaut-il la dérive ». Il compare DEUX régimes du MÊME monde (même seed,
# config=full, an 0→6) :
#   • LOD OFF  = `light.SHADING_POWER_MIN = 0.0` (dormant, bit-identique au golden) ;
#   • LOD ON   = `--seuil S` (les plantes sous S REÇOIVENT la lumière mais n'ÉMETTENT
#                plus d'ombre → coupées des deux boucles géométriques de `compute`).
#
# Cinq critères (D6) :
#   1. TRAJECTOIRE N — N vivant par saison off vs on, + onset (bascule férale) +
#      plateau an 6. Garde-fou : N doit tenir la bande ±15 % (~613/an6, D5/D69).
#   2. DÉRIVE `light_received` — mesurée à MONDE FIGÉ (le monde OFF an 6) : recompute
#      la lumière à seuil 0 puis à S sur le MÊME monde, écart relatif reçu par plante
#      (moyen + max). ⚠ on NE compare PAS deux runs divergents (ils divergent en 6 ans).
#   3. SELF-THINNING vis B — coups de `shade_stress_damage` (carence lumineuse) par
#      run : le LOD relâche l'ombre → moins de coups ? (frein MINEUR, cf. D67).
#   4. GAIN ms/tick — an 6, off vs on (le gain géométrique brut).
#   5. COÛT GERMINATION SURNUMÉRAIRE — nouvelles plantes/saison off vs on (le LOD
#      ↑ lumière-sol ↑ germination → recoût) + gain NET = ms(off) − ms(on) mesuré à
#      l'équilibre PROPRE de chaque run (le gain déjà amputé du recoût germination).
#
# Régime HORS-LIGNE, LECTURE SEULE (ne fige jamais rien, comme profile_monde) :
# monte deux moteurs frais via le SERVEUR (même fabrique que le F5), quelques
# minutes headless. À `--seuil 0`, off ≡ on → dérive nulle, gain nul = sanity check
# du banc lui-même.
#
# Usage (depuis data/code/) :
#   python3 -m tools.diag_lod_ombre [--seuil S] [--week N] [--mesures M] [--seed H]
#     --seuil   S : seuil de pouvoir ombrageant du régime ON (défaut 0.0 = sanity)
#     --week    N : semaine cible (défaut 262 ≈ an 6, printemps)
#     --mesures M : ticks non instrumentés pour le ms/tick d'équilibre (défaut 5)

from __future__ import annotations
import argparse
import time

from fields import light
from world.tile import Tile
from sim.effects import perturbations
from sim.engine import saison_de

PLATEAU_CIBLE = 613          # ~N/an6 fixé par D69 (banc équilibre invasion)
BANDE = 0.15                 # tolérance ±15 % (D5) → [521, 705]


def _build_engine_full(seed):
    """Monte le monde config=full VIA LE SERVEUR (même fabrique que le F5) et
    renvoie son Engine, prêt à ticker (pré-vieillissement fruitiers inclus)."""
    from tools.simserver.server import SimServer
    srv = SimServer()
    rep = srv.cmd_init({"config": "full", "seed": seed})
    if not rep.get("ok"):
        raise RuntimeError(f"cmd_init a échoué : {rep}")
    return srv.engine


def _n_vivant(engine) -> int:
    return sum(1 for t in engine.game_state["tiles"] for p in t.plants if p.is_alive)


def _run_regime(seed, seuil, jusqu_a, trace):
    """Grandit un moteur config=full au régime LOD (seuil donné) jusqu'à `jusqu_a`,
    en instrumentant : trajectoire (semaine, N) par saison, coups vis B (carence
    lumineuse), nouvelles plantes par saison (germination férale + clonal — tout ce
    qui passe par `Tile.add_plant` PENDANT le ticking). Les cultivées plantées au
    MONTAGE sont hors comptage (wrappers installés APRÈS `_build_engine_full`).
    Renvoie (engine, traj, visB_total, germ_par_saison)."""
    light.SHADING_POWER_MIN = seuil
    engine = _build_engine_full(seed)

    stats = {"visB": 0, "germ": 0}
    orig_ssd = perturbations.shade_stress_damage
    orig_add = Tile.add_plant

    def ssd(*a, **k):
        r = orig_ssd(*a, **k)
        if r:                       # liste non vide = un ReduceHealth « carence lumineuse »
            stats["visB"] += 1
        return r

    def add(self, *a, **k):
        p = orig_add(self, *a, **k)
        if p is not None:           # None = échec de pose (plot pris) → pas une levée
            stats["germ"] += 1
        return p

    perturbations.shade_stress_damage = ssd
    Tile.add_plant = add
    traj, germ_par_saison, germ_ref = [], [], 0
    try:
        while engine.week < jusqu_a:
            engine.tick_semaine()
            if engine.week % 13 == 0:            # frontière de saison
                n = _n_vivant(engine)
                traj.append((engine.week, n))
                germ_par_saison.append(stats["germ"] - germ_ref)
                germ_ref = stats["germ"]
                if trace:
                    print(f"    … s{engine.week} N={n} "
                          f"(nouvelles+{germ_par_saison[-1]}, visB_cumul={stats['visB']})")
    finally:
        perturbations.shade_stress_damage = orig_ssd
        Tile.add_plant = orig_add
    return engine, traj, stats["visB"], germ_par_saison


def _ms_tick(engine, mesures) -> float:
    """ms/tick moyen NON instrumenté à l'équilibre propre du run (comparable HUD F4)."""
    t0 = time.perf_counter()
    for _ in range(mesures):
        engine.tick_semaine()
    return (time.perf_counter() - t0) / mesures * 1000.0


def _derive_received(engine_off, seuil):
    """Dérive du MODÈLE à MONDE FIGÉ (le monde OFF an 6, critère b) : recompute la
    lumière à seuil 0 puis à `seuil` sur le MÊME monde, écart relatif |on−off|/off
    de la lumière reçue, plante par plante. Renvoie (moy, max, n_plantes)."""
    tiles = engine_off.game_state["tiles"]
    ecos = engine_off.game_state["eco"]
    house = engine_off.game_state.get("house")
    saison = saison_de(engine_off.week)
    ecarts = []
    for tile in tiles:
        lf = ecos[tile.tile_id].lumiere
        origin = (tile.origin_x_cm, tile.origin_y_cm)
        plants = tile.plants
        lf._geom_key = None
        light.SHADING_POWER_MIN = 0.0
        lf.compute(plants, saison, house=house, tile_origin=origin)
        base = dict(lf.received)
        lf._geom_key = None
        light.SHADING_POWER_MIN = seuil
        lf.compute(plants, saison, house=house, tile_origin=origin)
        on = dict(lf.received)
        for k, b in base.items():
            if b > 1e-9:
                ecarts.append(abs(on[k] - b) / b)
    n = len(ecarts)
    return (sum(ecarts) / n if n else 0.0), (max(ecarts) if ecarts else 0.0), n


def _onset(traj) -> int:
    """Semaine où N franchit la moitié de son plateau an 6 (proxy de la bascule
    férale). Renvoie 0 si jamais franchi."""
    if not traj:
        return 0
    plateau = traj[-1][1]
    for wk, n in traj:
        if n >= 0.5 * plateau:
            return wk
    return 0


def _bloc_trajectoire(traj_off, traj_on):
    print("\n[1] TRAJECTOIRE N (N vivant par saison, off vs on)")
    print(f"    {'semaine':>8} {'N off':>7} {'N on':>7} {'Δ':>6}")
    for (wk, noff), (_, non) in zip(traj_off, traj_on):
        print(f"    {wk:>8} {noff:>7} {non:>7} {non - noff:>+6}")
    p_off, p_on = traj_off[-1][1], traj_on[-1][1]
    lo, hi = int(PLATEAU_CIBLE * (1 - BANDE)), int(PLATEAU_CIBLE * (1 + BANDE))
    dans = lo <= p_on <= hi
    print(f"    onset (½ plateau) : off s{_onset(traj_off)} | on s{_onset(traj_on)}")
    print(f"    plateau an 6 : off {p_off} | on {p_on} "
          f"(bande D5 [{lo}, {hi}] → {'DANS' if dans else '⚠ HORS'})")


def main() -> int:
    ap = argparse.ArgumentParser(description="Banc fidélité LOD des émetteurs d'ombre (D67).")
    ap.add_argument("--seuil", type=float, default=0.0,
                    help="seuil de pouvoir ombrageant du régime ON (défaut 0.0 = sanity)")
    ap.add_argument("--week", type=int, default=262,
                    help="semaine cible (défaut 262 ≈ an 6, printemps)")
    ap.add_argument("--mesures", type=int, default=5,
                    help="ticks non instrumentés pour le ms/tick d'équilibre (défaut 5)")
    ap.add_argument("--seed", type=lambda s: int(s, 0), default=0x5AB1057E,
                    help="seed global déterministe (défaut = celui du serveur)")
    args = ap.parse_args()

    print(f"=== Diag LOD ombre (D67) — config=full, seed={args.seed:#x}, "
          f"seuil ON={args.seuil} ===")
    print(f"  cible : semaine {args.week} (an {(args.week - 1) // 52 + 1})")

    print("\n  régime OFF (seuil 0.0)…")
    eng_off, traj_off, visB_off, germ_off = _run_regime(args.seed, 0.0, args.week, True)
    print("  régime ON (seuil "
          f"{args.seuil})…")
    eng_on, traj_on, visB_on, germ_on = _run_regime(args.seed, args.seuil, args.week, True)

    ms_off = _ms_tick(eng_off, args.mesures)
    ms_on = _ms_tick(eng_on, args.mesures)
    der_moy, der_max, der_n = _derive_received(eng_off, args.seuil)

    _bloc_trajectoire(traj_off, traj_on)

    print("\n[2] DÉRIVE light_received (monde OFF an 6 figé, écart relatif |on−off|/off)")
    print(f"    sur {der_n} plantes : moyenne {der_moy * 100:6.3f} % | "
          f"max {der_max * 100:6.3f} %")

    print("\n[3] SELF-THINNING vis B (coups « carence lumineuse » cumulés an 0→6)")
    print(f"    off {visB_off} | on {visB_on} (Δ {visB_on - visB_off:+d})")

    print("\n[4] GAIN ms/tick (équilibre an 6, non instrumenté)")
    gain = ms_off - ms_on
    pct = (gain / ms_off * 100) if ms_off else 0.0
    print(f"    off {ms_off:7.2f} ms | on {ms_on:7.2f} ms | "
          f"gain NET {gain:+7.2f} ms ({pct:+5.1f} %)")

    print("\n[5] COÛT GERMINATION SURNUMÉRAIRE (nouvelles plantes/saison, moyenne)")
    m_off = sum(germ_off) / len(germ_off) if germ_off else 0.0
    m_on = sum(germ_on) / len(germ_on) if germ_on else 0.0
    print(f"    off {m_off:6.1f}/saison | on {m_on:6.1f}/saison "
          f"(Δ {m_on - m_off:+.1f} → recoût déjà inclus dans le gain NET [4])")

    light.SHADING_POWER_MIN = 0.0          # restaure le défaut module (propreté)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
