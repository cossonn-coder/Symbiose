# SYMBIOSE — tools/bancs/jardin_tenu.py
# LE BANC DE MESURE du sprint (tronçon ⑤) : « jardin TENU vs ABANDONNÉ ». Monte
# DEUX copies déterministes du MÊME monde (même config, même seed → mondes
# bit-identiques au départ), en joue une avec un `JardinierAutomate` (tenu) et
# laisse l'autre livrée à elle-même (abandonné), sur N années, puis imprime un
# tableau comparatif : démographie, couverture du sol, et surtout COÛT PERF
# `LightField` (hypothèse Q9 : le régime tenu porte plus de biomasse → plus
# d'ombre → tick_light plus cher). Plus le RAPPORT D'IMPASSES agrégé.
#
# EXTERNE au moteur (invariant H2) : `engine.tick_semaine()` puis, en régime tenu,
# `automate.jouer_tick(engine)`. L'automate n'est JAMAIS dans le tick → golden
# intact. C'est un OUTIL de dev, pas un test golden. On ne simule qu'une poignée
# d'années (JAMAIS 500 ans — perf LightField, §2.7/Q9).
#
# Usage (depuis data/code/) :
#   python3 -m tools.bancs.jardin_tenu [--years N] [--config full|propre] [--seed S]
#         [--desherbage curatif|aucun|systematique] [--part-recoltee F] [--paie-vigueur]

from __future__ import annotations
import argparse
import cProfile
import pstats
import time
from dataclasses import replace

from tools.jardinier_auto import JardinierAutomate, LIBRE, marquer_jardin_cultive
from tools.jardinier_auto.tutelle import zones_cultivees, sous_tutelle
from tools.jardinier_auto.rapport import rapport_impasses


def _build_engine(config: str, seed: int):
    """Monte le monde `config` via `SimServer.cmd_init` (fabrique du F5) — même
    patron que les bancs frères (diag_population, profile_monde)."""
    from tools.simserver.server import SimServer
    srv = SimServer()
    rep = srv.cmd_init({"config": config, "seed": seed})
    if not rep.get("ok"):
        raise RuntimeError(f"cmd_init a échoué : {rep}")
    return srv.engine


def _mesure(engine, player: str) -> dict:
    """Photo démographique + couverture du sol à la semaine courante (lecture seule).
    Classe cultivées/férales via le set `replante` (tutelle) : une plante dont le
    plot-foyer est déclaré cultivé est comptée cultivée, sinon férale."""
    gs = engine.game_state
    cultivees = zones_cultivees(gs, player)
    n_total = n_cult = n_feral = 0
    tuile_max = 0
    paillage_sum = 0.0
    for tile in engine.tiles:
        n_tuile = 0
        for plant in tile.plants:
            if not plant.is_alive:
                continue
            n_total += 1
            n_tuile += 1
            if sous_tutelle(plant, tile.tile_id, cultivees):
                n_cult += 1
            else:
                n_feral += 1
        tuile_max = max(tuile_max, n_tuile)
        paillage_sum += engine._eco(tile).paillage.average()
    return {"n": n_total, "cultivees": n_cult, "ferales": n_feral,
            "tuile_max": tuile_max, "paillage": paillage_sum / len(engine.tiles)}


def _jouer(engine, automate, weeks: int) -> float:
    """Fait avancer `engine` de `weeks` semaines. Si `automate` est fourni, il joue
    ENTRE deux ticks (régime tenu). Renvoie le ms/tick moyen (perf_counter autour
    du SEUL `tick_semaine` — le coût de l'automate, hors moteur, n'est pas compté :
    on mesure le coût MOTEUR du régime, c'est lui que Q9 interroge)."""
    t_tick = 0.0
    for _ in range(weeks):
        t0 = time.perf_counter()
        engine.tick_semaine()
        t_tick += time.perf_counter() - t0
        if automate is not None:
            automate.jouer_tick(engine)
    return t_tick / weeks * 1000.0


def _part_light(engine, ticks: int = 2) -> tuple[float, float]:
    """Décompose le tick courant via cProfile sur `ticks` ticks : renvoie
    `(ms/tick, part_lightfield)` où la part est le cumtime de `tick_light` rapporté
    au temps total profilé. cProfile est EXTERNE au moteur → golden intact. Fait
    AVANCER le monde de `ticks` semaines (mesure au bout du régime, états divergés
    — c'est exactement ce que Q9 compare : l'ombre portée du régime)."""
    prof = cProfile.Profile()
    t0 = time.perf_counter()
    prof.enable()
    for _ in range(ticks):
        engine.tick_semaine()
    prof.disable()
    total = time.perf_counter() - t0
    light_ct = 0.0
    stats = pstats.Stats(prof)
    for (_f, _l, name), (_cc, _nc, _tt, ct, _callers) in stats.stats.items():
        if name == "tick_light":
            light_ct += ct
    part = light_ct / total if total > 0 else 0.0
    return total / ticks * 1000.0, part


def _regime(nom: str, config: str, seed: int, profil, avec_automate: bool,
            weeks: int) -> tuple[dict, float, tuple]:
    """Monte un monde, déclare le jardin cultivé (tutelle, hors tick), le joue
    `weeks` semaines (avec ou sans automate), puis mesure. Renvoie
    `(mesure, ms_tick_moyen, (ms_profil, part_light))` et — pour le tenu — laisse
    le journal d'impasses dans le game_state (récupéré par l'appelant)."""
    engine = _build_engine(config, seed)
    player = engine.game_state["current_player"]
    marquer_jardin_cultive(engine, player)     # même déclaration des deux côtés
    automate = JardinierAutomate(profil) if avec_automate else None
    print(f"  [{nom}] {weeks} semaines…")
    ms_tick = _jouer(engine, automate, weeks)
    mesure = _mesure(engine, player)
    light = _part_light(engine)                # décomposition perf en fin de régime
    return mesure, ms_tick, light, engine.game_state


def _tableau(m_tenu, m_aband, ms_tenu, ms_aband, l_tenu, l_aband) -> None:
    """Imprime le comparatif tenu vs abandonné, ligne par métrique + écart."""
    def ligne(label, a, b, fmt="{:>8}"):
        va, vb = fmt.format(a), fmt.format(b)
        ecart = f"{(a - b):+.2f}" if isinstance(a, float) else f"{a - b:+d}"
        print(f"    {label:<22} tenu={va}  abandonné={vb}  Δ={ecart}")
    print("  ── COMPARATIF (fin de simulation) ──")
    ligne("N plantes vivantes", m_tenu["n"], m_aband["n"])
    ligne("dont cultivées", m_tenu["cultivees"], m_aband["cultivees"])
    ligne("dont férales", m_tenu["ferales"], m_aband["ferales"])
    ligne("N/tuile max", m_tenu["tuile_max"], m_aband["tuile_max"])
    ligne("couverture (paillage)", m_tenu["paillage"], m_aband["paillage"], "{:>8.3f}")
    print("  ── PERF (Q9 : le régime tenu coûte-t-il plus cher ?) ──")
    ligne("ms/tick moyen", ms_tenu, ms_aband, "{:>8.2f}")
    ligne("ms/tick (profilé)", l_tenu[0], l_aband[0], "{:>8.2f}")
    ligne("part LightField", l_tenu[1] * 100, l_aband[1] * 100, "{:>7.1f}%")
    surcout = (ms_tenu / ms_aband - 1.0) * 100 if ms_aband > 0 else 0.0
    verdict = ("le régime tenu est PLUS cher" if surcout > 2 else
               "coût comparable" if surcout > -2 else "le régime tenu est MOINS cher")
    print(f"  ➜ VERDICT Q9 : {verdict} (surcoût moteur {surcout:+.1f} %).")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Banc de mesure « jardin tenu vs abandonné » (tronçon ⑤).")
    ap.add_argument("--years", type=int, default=2,
                    help="années simulées de chaque côté (défaut 2 ; PAS 500 ! "
                         "le tick full grossit vite, cf. perf LightField §2.7/Q9)")
    ap.add_argument("--config", default="full", choices=["full", "propre"])
    ap.add_argument("--seed", type=lambda s: int(s, 0), default=0x5AB1057E)
    ap.add_argument("--desherbage", default="curatif",
                    choices=["curatif", "aucun", "systematique"])
    ap.add_argument("--part-recoltee", type=float, default=1.0)
    ap.add_argument("--paie-vigueur", action="store_true",
                    help="active le budget de Vigueur du régime tenu (preset BRIDE partiel)")
    args = ap.parse_args()

    weeks = args.years * 52
    profil = replace(LIBRE, desherbage=args.desherbage,
                     part_recoltee=args.part_recoltee, paie_vigueur=args.paie_vigueur)
    print(f"=== Banc jardin tenu vs abandonné — config={args.config}, "
          f"seed={args.seed:#x}, years={args.years} ({weeks} sem) ===")
    print(f"  profil (tenu) : desherbage={profil.desherbage}, "
          f"part_recoltee={profil.part_recoltee}, paie_vigueur={profil.paie_vigueur}")

    t_start = time.perf_counter()
    m_tenu, ms_tenu, l_tenu, gs_tenu = _regime(
        "tenu", args.config, args.seed, profil, True, weeks)
    m_aband, ms_aband, l_aband, _gs = _regime(
        "abandonné", args.config, args.seed, profil, False, weeks)
    print(f"  (temps mur total : {time.perf_counter() - t_start:.1f} s)\n")

    _tableau(m_tenu, m_aband, ms_tenu, ms_aband, l_tenu, l_aband)
    print()
    print(rapport_impasses(gs_tenu))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
