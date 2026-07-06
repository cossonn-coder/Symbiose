# SYMBIOSE — tools/diag_population.py
# Diag TRAJECTOIRE de population (livrable ① du sprint « équilibre invasion », D69).
#
# But : mesurer l'ONSET de l'invasion férale et le PLATEAU de population N sur le
# VRAI monde de jeu (8 tuiles + maison), pour calibrer les freins férals (②) et
# vérifier le banc « monde propre ». Promotion du script ad-hoc du diagnostic D69.
#
# Deux configs comparables (montées par le SERVEUR, même fabrique que le F5) :
#   --config full   : monde de jeu réel → reproduit la montée de N (~1043 à l'an 5) ;
#   --config propre : MÊME monde, pression férale coupée → N reste ≈ constant
#                     (seulement les cultivées de build_world_full).
#
# Régime HORS-LIGNE, lecture seule, sans Godot ni pont. cProfile ABSENT : ce n'est
# pas un profileur (voir profile_monde.py pour ça) mais un MÈTRE de population. On
# ticke `engine.tick_semaine()` en direct (hors couche voix/journal du pont) et on
# logge tous les 26 ticks : N total, composition par espèce (top 6), N/tuile max.
# EXTERNE au moteur → aucune instrumentation dans la boucle → golden INTACT.
#
# Usage (depuis data/code/) :
#   python3 -m tools.diag_population [--config full|propre] [--week N] [--seed S]
#     --config C : preset de monde monté par le serveur (défaut "full")
#     --week   N : semaine finale (défaut 262 ≈ an 6) — trajectoire jusque-là
#     --seed   S : seed global déterministe (défaut = celui du serveur)

from __future__ import annotations
import argparse

from sim.engine.calendrier import saison_de


def _saison_nom(week: int) -> str:
    """Nom de saison lisible (miroir de la boucle : semaine 1-52 cyclique)."""
    return saison_de(((week - 1) % 52) + 1)


def _build_engine(config: str, seed: int):
    """Monte le monde `config` VIA LE SERVEUR (même fabrique que le F5) et renvoie
    son `Engine`, prêt à ticker. On passe par `SimServer.cmd_init` pour hériter du
    banc « monde propre » (seedbank férale vidée + flag `feral_off`) sans dupliquer
    la logique — puis on ticke le moteur en direct (hors couche pont)."""
    from tools.simserver.server import SimServer
    srv = SimServer()
    rep = srv.cmd_init({"config": config, "seed": seed})
    if not rep.get("ok"):
        raise RuntimeError(f"cmd_init a échoué : {rep}")
    return srv.engine


def _mesure(engine) -> dict:
    """État de population à la semaine courante : N total de plantes VIVANTES,
    composition par espèce, et N max par tuile (indicateur de saturation locale).
    Purement descriptif — aucune écriture moteur."""
    tiles = engine.game_state["tiles"]
    n_total = 0
    par_espece: dict[str, int] = {}
    n_par_tuile_max = 0
    for t in tiles:
        n_tuile = 0
        for p in t.plants:
            if not p.is_alive:
                continue
            n_total += 1
            n_tuile += 1
            nom = p.plant_class.__name__
            par_espece[nom] = par_espece.get(nom, 0) + 1
        n_par_tuile_max = max(n_par_tuile_max, n_tuile)
    return {"n": n_total, "par_espece": par_espece, "tuile_max": n_par_tuile_max}


def _ligne_compo(par_espece: dict[str, int], top: int = 6) -> str:
    """Composition condensée : les `top` espèces les plus nombreuses."""
    tri = sorted(par_espece.items(), key=lambda kv: -kv[1])
    return ", ".join(f"{nom}×{n}" for nom, n in tri[:top])


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Diag trajectoire de population du monde Symbiose (onset/plateau).")
    ap.add_argument("--config", default="full", choices=["full", "propre"],
                    help="preset de monde (défaut 'full')")
    ap.add_argument("--week", type=int, default=262,
                    help="semaine finale (défaut 262 ≈ an 6)")
    ap.add_argument("--seed", type=lambda s: int(s, 0), default=0x5AB1057E,
                    help="seed global déterministe (défaut = celui du serveur)")
    args = ap.parse_args()

    print(f"=== Diag population — config={args.config}, seed={args.seed:#x} ===")
    engine = _build_engine(args.config, args.seed)

    m0 = _mesure(engine)
    print(f"  départ (semaine {engine.week}) : N={m0['n']} "
          f"| {_ligne_compo(m0['par_espece'])}")

    print("  trajectoire (tous les 26 ticks) :")
    while engine.week < args.week:
        engine.tick_semaine()
        if engine.week % 26 == 0 or engine.week >= args.week:
            m = _mesure(engine)
            an = (engine.week - 1) // 52 + 1
            print(f"    s{engine.week:>4} (an {an}, {_saison_nom(engine.week):<9}) : "
                  f"N={m['n']:>4} | tuile_max={m['tuile_max']:>3} "
                  f"| {_ligne_compo(m['par_espece'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
