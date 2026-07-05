# SYMBIOSE — tools/profile_monde.py
# Profileur PERF du MONDE COMPLET (livrable ① du sprint « instrumentation perf »).
#
# But : répondre à « où part le temps de tick, sur le VRAI monde de jeu, pour
# savoir quoi optimiser en priorité ». `profile_tick.py` (son frère) ne profile
# que le petit monde golden (2 tuiles) ; ici on grandit le monde `config="full"`
# (8 tuiles + maison, celui du F5) jusqu'à la semaine voulue — typiquement l'an 6
# où le tick se met à coûter ~1,3 s — puis on sort DEUX mesures complémentaires :
#
#   1. le ms/tick ABSOLU (non instrumenté → chiffre vrai, comparable au HUD F4) ;
#   2. la TABLE DE PRIORITÉS via cProfile (temps propre par fonction) → la carte
#      de « qui coûte quoi » (on sait déjà LightField ≈ 53 %, dette D32 ; ceci
#      donne le reste sans deviner).
#
# Régime HORS-LIGNE, sans Godot ni pont : c'est le chemin « pour les tests ça
# aille vite » — quelques minutes headless au lieu de regarder tourner à 2,8 s/sem.
# cProfile est EXTERNE au moteur → aucune instrumentation dans la boucle → golden
# INTACT par construction (ce script est lecture seule, il ne fige jamais rien).
#
# Fidélité au F5 : le monde est monté par le SERVEUR lui-même (`SimServer.cmd_init`
# config="full") — même fabrique, même pré-vieillissement des fruitiers, zéro
# duplication. On profile ensuite `engine.tick_semaine()` EN DIRECT (pas
# `cmd_step_week`, qui ajoute la couche voix/journal du pont — hors moteur).
#
# Usage (depuis data/code/) :
#   python3 -m tools.profile_monde [--week N] [--mesures M] [--profil K] [--top T]
#     --week    N : semaine cible où profiler (défaut 262 ≈ an 6, printemps)
#     --mesures M : ticks non instrumentés pour le ms/tick absolu (défaut 5)
#     --profil  K : ticks passés sous cProfile pour la table (défaut 3)
#     --top     T : lignes de la table de priorités (défaut 30)

from __future__ import annotations
import argparse
import cProfile
import io
import pstats
import time

from sim.engine.calendrier import saison_de, SAISONS


def _saison_nom(week: int) -> str:
    """Nom de saison lisible pour l'en-tête (miroir de la boucle : 1-52 cyclique)."""
    return saison_de(((week - 1) % 52) + 1)


def _build_engine_full(seed: int):
    """Monte le monde `config="full"` VIA LE SERVEUR (même fabrique que le F5) et
    renvoie son `Engine`, prêt à ticker. On passe par `SimServer.cmd_init` pour
    hériter du pré-vieillissement des fruitiers et de la banque de départ sans
    dupliquer la logique — puis on ticke le moteur en direct (hors couche pont)."""
    from tools.simserver.server import SimServer
    srv = SimServer()
    rep = srv.cmd_init({"config": "full", "seed": seed})
    if not rep.get("ok"):
        raise RuntimeError(f"cmd_init a échoué : {rep}")
    return srv.engine


def _compo_monde(engine) -> dict:
    """Composition du monde à la semaine courante : plantes vivantes, segments
    (même comptage que le snapshot Godot — `structure_to_dict()`), par espèce.
    Purement descriptif pour l'en-tête ; dit QUELLE configuration on profile."""
    tiles = engine.game_state["tiles"]
    ecos = engine.game_state["eco"]
    n_plants = n_segments = 0
    par_espece: dict[str, int] = {}
    for t in tiles:
        for p in t.plants:
            if not p.is_alive:
                continue
            n_plants += 1
            n_segments += len(p.structure_to_dict())
            nom = p.plant_class.__name__
            par_espece[nom] = par_espece.get(nom, 0) + 1
    n_plots = sum(e.lumiere.rows * e.lumiere.cols for e in ecos.values())
    return {"tuiles": len(tiles), "plots": n_plots, "plantes": n_plants,
            "segments": n_segments, "par_espece": par_espece}


def _grandir(engine, jusqu_a: int) -> None:
    """Fait avancer le moteur jusqu'à la semaine `jusqu_a` (échauffement non
    mesuré). Trace la progression toutes les 26 semaines : grandir jusqu'à l'an 6
    prend quelques minutes, un signe de vie évite de croire à un blocage."""
    t0 = time.perf_counter()
    while engine.week < jusqu_a:
        engine.tick_semaine()
        if engine.week % 26 == 0:
            dt = time.perf_counter() - t0
            print(f"  … semaine {engine.week} atteinte ({dt:5.1f} s écoulées)")


def _ms_tick_absolu(engine, mesures: int) -> float:
    """ms/tick moyen NON instrumenté : le chiffre vrai (comparable au HUD F4),
    sans le biais ×2 de cProfile. Mesuré juste après l'échauffement."""
    t0 = time.perf_counter()
    for _ in range(mesures):
        engine.tick_semaine()
    return (time.perf_counter() - t0) / mesures * 1000.0


def _table_priorites(engine, ticks: int, top: int) -> str:
    """Table de priorités via cProfile sur `ticks` ticks, triée par TEMPS PROPRE
    (tottime = temps passé DANS la fonction, hors sous-appels — c'est lui qui
    pointe le vrai coûteux). `strip_dirs` raccourcit les chemins. Retourne le
    texte prêt à afficher (et à copier-coller dans un rapport)."""
    prof = cProfile.Profile()
    prof.enable()
    for _ in range(ticks):
        engine.tick_semaine()
    prof.disable()
    flux = io.StringIO()
    stats = pstats.Stats(prof, stream=flux).strip_dirs().sort_stats("tottime")
    stats.print_stats(top)
    return flux.getvalue()


def main() -> int:
    ap = argparse.ArgumentParser(description="Profileur perf du monde complet Symbiose.")
    ap.add_argument("--week", type=int, default=262,
                    help="semaine cible à profiler (défaut 262 ≈ an 6, printemps)")
    ap.add_argument("--mesures", type=int, default=5,
                    help="ticks non instrumentés pour le ms/tick absolu (défaut 5)")
    ap.add_argument("--profil", type=int, default=3,
                    help="ticks sous cProfile pour la table (défaut 3)")
    ap.add_argument("--top", type=int, default=30,
                    help="lignes de la table de priorités (défaut 30)")
    ap.add_argument("--seed", type=lambda s: int(s, 0), default=0x5AB1057E,
                    help="seed global déterministe (défaut = celui du serveur)")
    args = ap.parse_args()

    print(f"=== Profil monde complet — config=full, seed={args.seed:#x} ===")
    print(f"  cible : semaine {args.week} "
          f"(an {(args.week - 1) // 52 + 1}, {_saison_nom(args.week)})")
    engine = _build_engine_full(args.seed)

    print(f"  échauffement jusqu'à la semaine {args.week}…")
    _grandir(engine, args.week)

    compo = _compo_monde(engine)
    print(f"\n  monde à la semaine {engine.week} : {compo['tuiles']} tuiles, "
          f"{compo['plots']} plots, {compo['plantes']} plantes, "
          f"{compo['segments']} segments")
    espece_tri = sorted(compo["par_espece"].items(), key=lambda kv: -kv[1])
    print("  par espèce : "
          + ", ".join(f"{nom}×{n}" for nom, n in espece_tri))

    ms = _ms_tick_absolu(engine, args.mesures)
    print(f"\n  ms/tick ABSOLU (moyen sur {args.mesures} ticks non instrumentés) : "
          f"{ms:7.2f} ms")

    print(f"\n--- Table de priorités (cProfile, {args.profil} ticks, "
          f"tri temps propre) ---")
    print(_table_priorites(engine, args.profil, args.top))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
