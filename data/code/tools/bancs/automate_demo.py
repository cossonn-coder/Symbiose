# SYMBIOSE — tools/bancs/automate_demo.py
# Banc de démonstration HEADLESS du jardinier automate (tronçons ①→②). Monte un
# petit monde via le SERVEUR (même fabrique que le F5, cf. diag_population), DÉCLARE
# le jardin initial comme cultivé (tutelle = cultivées, §3/Q3), branche un
# JardinierAutomate ENTRE deux ticks, et imprime le journal (gestes + impasses).
#
# EXTERNE au moteur : `engine.tick_semaine()` puis `automate.jouer_tick(engine)` —
# l'automate n'est jamais dans le tick (invariant H2) → golden intact. On ne simule
# QU'UNE poignée d'années (jamais 500 ans).
#
# Usage (depuis data/code/) :
#   python3 -m tools.bancs.automate_demo [--weeks N] [--config full|propre]
#                                        [--seed S] [--desherbage curatif|aucun|systematique]
#                                        [--part-recoltee F] [--paie-vigueur]
#                                        [--credite-maitrise] [--amorce-maitrise OBJET]
#
# Le couple `--paie-vigueur --credite-maitrise` reproduit le preset BRIDE (§4,
# tronçon ③) : respect de `gestes_debloques`, conséquences tracées. `--amorce-
# maitrise OBJET` accorde le palier 1 d'un concept (dev only, comme
# `marquer_jardin_cultive`) pour DÉMONTRER un déverrouillage dans la trace.

from __future__ import annotations
import argparse
from dataclasses import replace

from tools.jardinier_auto import JardinierAutomate, LIBRE, marquer_jardin_cultive
from tools.jardinier_auto.trace import journal


def _build_engine(config: str, seed: int):
    """Monte le monde `config` via `SimServer.cmd_init` (fabrique du F5) et renvoie
    son Engine, prêt à ticker (patron repris de diag_population.py)."""
    from tools.simserver.server import SimServer
    srv = SimServer()
    rep = srv.cmd_init({"config": config, "seed": seed})
    if not rep.get("ok"):
        raise RuntimeError(f"cmd_init a échoué : {rep}")
    return srv.engine


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Démo headless du jardinier automate (tronçons ①→②).")
    ap.add_argument("--weeks", type=int, default=104,
                    help="nombre de semaines simulées (défaut 104 ≈ 2 ans)")
    ap.add_argument("--config", default="full", choices=["full", "propre"],
                    help="preset de monde (défaut 'full')")
    ap.add_argument("--seed", type=lambda s: int(s, 0), default=0x5AB1057E,
                    help="seed global déterministe")
    ap.add_argument("--desherbage", default="curatif",
                    choices=["curatif", "aucun", "systematique"],
                    help="mode de désherbage du profil (défaut 'curatif')")
    ap.add_argument("--part-recoltee", type=float, default=1.0,
                    help="fraction récoltée ∈ [0,1] (défaut 1.0)")
    ap.add_argument("--paie-vigueur", action="store_true",
                    help="active le budget de Vigueur (coupe les gestes trop chers)")
    ap.add_argument("--credite-maitrise", action="store_true",
                    help="crédite la maîtrise (déverrouillages/paliers tracés) — preset BRIDE")
    ap.add_argument("--amorce-maitrise", metavar="OBJET", default=None,
                    help="accorde le palier 1 d'un concept (dev only) pour démontrer un "
                         "déverrouillage — ex. 'paillage' ouvre pailler/broyer")
    args = ap.parse_args()

    profil = replace(LIBRE, desherbage=args.desherbage,
                     part_recoltee=args.part_recoltee,
                     paie_vigueur=args.paie_vigueur,
                     credite_maitrise=args.credite_maitrise)
    print(f"=== Démo jardinier automate — config={args.config}, seed={args.seed:#x}, "
          f"weeks={args.weeks} ===")
    print(f"  profil : desherbage={profil.desherbage}, part_recoltee={profil.part_recoltee}, "
          f"paie_vigueur={profil.paie_vigueur}, credite_maitrise={profil.credite_maitrise}")
    engine = _build_engine(args.config, args.seed)
    player = engine.game_state["current_player"]
    n_cult = marquer_jardin_cultive(engine, player)
    print(f"  {n_cult} zones déclarées cultivées (tutelle).")
    if args.amorce_maitrise:
        # Dev only (comme marquer_jardin_cultive) : pose le palier 1 d'un concept
        # AVANT la boucle → au 1ᵉ tick, evaluer_deblocages ouvre les gestes gated et
        # les consigne en conséquence `deblocage` (démonstration de la trace ③).
        from sim import maitrise as M
        M.decouvrir(engine.game_state, player, args.amorce_maitrise)
        print(f"  maîtrise amorcée : {args.amorce_maitrise} (palier 1) — dev only.")
    automate = JardinierAutomate(profil)

    for _ in range(args.weeks):
        engine.tick_semaine()
        automate.jouer_tick(engine)

    jr = journal(engine.game_state)
    gestes = [e for e in jr if e["categorie"] == "geste"]
    impasses = [e for e in jr if e["categorie"] == "impasse"]
    print(f"  {len(gestes)} gestes + {len(impasses)} impasses sur {args.weeks} semaines.")
    # Répartition des GESTES par (geste, résultat) — vue synthétique déterministe.
    compo: dict[tuple, int] = {}
    for e in gestes:
        cle = (e["geste"], e["resultat"])
        compo[cle] = compo.get(cle, 0) + 1
    for (geste, res), n in sorted(compo.items()):
        print(f"    {geste:<15} {res:<8} ×{n}")
    # Répartition des IMPASSES par (facteur, cause) — le livrable « trous de gameplay ».
    if impasses:
        print("  impasses (facteur → cause) :")
        icompo: dict[tuple, int] = {}
        for e in impasses:
            icompo[(e["facteur_limitant"], e["cause"])] = \
                icompo.get((e["facteur_limitant"], e["cause"]), 0) + 1
        for (facteur, cause), n in sorted(icompo.items()):
            print(f"    {facteur:<18} → {cause:<24} ×{n}")
    # Répartition des CONSÉQUENCES (③) — déblocages / paliers / morts consignés.
    conseq = [e for e in jr if e["categorie"] == "consequence"]
    if conseq:
        print(f"  {len(conseq)} conséquences (type → detail) :")
        ccompo: dict[tuple, int] = {}
        for e in conseq:
            ccompo[(e["type"], e["detail"])] = ccompo.get((e["type"], e["detail"]), 0) + 1
        for (type_, detail), n in sorted(ccompo.items()):
            print(f"    {type_:<10} {detail:<28} ×{n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
