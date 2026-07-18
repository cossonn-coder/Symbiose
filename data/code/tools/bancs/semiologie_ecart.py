# SYMBIOSE — tools/bancs/semiologie_ecart.py
# BANC DE MESURE de la SÉMIOLOGIE (tronçon ⑦, optionnel). L'automate a deux profils
# de perception : `omniscient` (lit l'état écologique continu — la RÉFÉRENCE HAUTE) et
# `semiologique` (ne lit QUE les signes visibles, comme un joueur humain). Rejouer le
# MÊME monde sous les deux regards et comparer leurs DÉCISIONS chiffre la qualité de la
# sémiologie du jeu : chaque facteur limitant que l'omniscient voit mais que le
# semiologique manque est un DÉFAUT DE SÉMIOLOGIE #5 (un signe absent, tardif, ou
# ambigu). C'est un INSTRUMENT DE MESURE, pas une correction : on NE bouche AUCUN trou
# (kickoff) — on le remonte.
#
# EXTERNE au moteur (invariant H2) : on fait avancer un SEUL monde abandonné (pour que
# les plantes SOUFFRENT → que les signes apparaissent), et à chaque tick on calcule les
# DEUX perceptions + diagnostics sur le MÊME état, sans jouer aucun geste. Zéro écriture
# moteur → golden intact. Outil de dev : quelques années, JAMAIS 500 ans.
#
# Usage (depuis data/code/) :
#   python3 -m tools.bancs.semiologie_ecart [--years N] [--config full|propre] [--seed S]

from __future__ import annotations
import argparse

from sim.engine.calendrier import saison_de
from tools.jardinier_auto import LIBRE, marquer_jardin_cultive
from tools.jardinier_auto.profil import ProfilAutomate
from tools.jardinier_auto.perception import percevoir
from tools.jardinier_auto.diagnostic import facteur_limitant
from tools.jardinier_auto.tutelle import zones_cultivees, sous_tutelle
from tools.jardinier_auto.impasses import FACTEURS_INVISIBLES

# Profils : deux perceptions, tout le reste identique (mesure PURE de la perception).
OMNI = LIBRE                                       # perception="omniscient" (défaut)
SEMIO = ProfilAutomate(perception="semiologique")  # tout le reste au défaut

# Table de RECENSEMENT des signes (§ préalable du kickoff) : pour chaque facteur
# limitant, le signe diégétique qui le trahit — ou « — » si AUCUN (invisible).
_RECENSEMENT = [
    ("hydrique",           "secheresse (feuille flétrie, désaturée)"),
    ("exces_eau",          "asphyxie (feuillage terne, brunâtre)"),
    ("ombrage",            "ombre (étiolement) + voisin dominant visible"),
    ("concurrence_ferale", "adventices visibles dans le rang"),
    ("organe_mur",         "fruit mûr visible sur la plante"),
    ("sol_compacte",       "—  AUCUN signe foliaire (INVISIBLE)"),
    ("sol_nu",             "—  sol nu : pas de signe SUR LA PLANTE (INVISIBLE)"),
]


def _build_engine(config: str, seed: int):
    """Monte le monde via `SimServer.cmd_init` (même fabrique que les bancs frères)."""
    from tools.simserver.server import SimServer
    srv = SimServer()
    rep = srv.cmd_init({"config": config, "seed": seed})
    if not rep.get("ok"):
        raise RuntimeError(f"cmd_init a échoué : {rep}")
    return srv.engine


def _confusion(engine, player, weeks):
    """Fait avancer le monde `weeks` semaines (abandonné = les plantes souffrent) et
    tally, par tick et par cultivée, le couple `(facteur omniscient, facteur semio)`.
    Renvoie `{(f_omni, f_semio): compte}` — la matrice de confusion des décisions."""
    conf: dict[tuple, int] = {}
    for _ in range(weeks):
        engine.tick_semaine()
        saison = saison_de(engine.week)
        cultivees = zones_cultivees(engine.game_state, player)
        for tile in engine.tiles:
            eco = engine._eco(tile)
            voisins = tile.plants
            for plant in tile.plants:
                if not sous_tutelle(plant, tile.tile_id, cultivees):
                    continue
                p_omni = percevoir(plant, eco, OMNI, voisins, tile.tile_id, cultivees)
                p_semio = percevoir(plant, eco, SEMIO, voisins, tile.tile_id,
                                    cultivees, saison)
                cle = (facteur_limitant(p_omni), facteur_limitant(p_semio))
                conf[cle] = conf.get(cle, 0) + 1
    return conf


def _rapport(conf: dict) -> None:
    """Imprime la table de recensement, la matrice de confusion et les métriques
    dérivées : accord, cécité par facteur invisible, et le CHIFFRE de qualité
    sémiologique (part des décisions où les deux profils s'accordent)."""
    print("  ── RECENSEMENT DES SIGNES (facteur → signe visible) ──")
    for facteur, signe in _RECENSEMENT:
        print(f"    {facteur:<18} {signe}")

    total = sum(conf.values())
    accord = sum(n for (fo, fs), n in conf.items() if fo == fs)
    # Cécité : l'omniscient voit un facteur, le semiologique ne voit RIEN.
    cecite: dict[str, int] = {}
    for (fo, fs), n in conf.items():
        if fo is not None and fs is None:
            cecite[fo] = cecite.get(fo, 0) + n

    print(f"\n  ── MATRICE DE CONFUSION ({total} observations plante×tick) ──")
    print(f"    {'omniscient':<20}{'semiologique':<20}compte")
    for (fo, fs), n in sorted(conf.items(), key=lambda kv: (-kv[1], str(kv[0]))):
        print(f"    {str(fo):<20}{str(fs):<20}{n:>6}")

    print("\n  ── CÉCITÉ SÉMIOLOGIQUE (omniscient voit, joueur ne voit RIEN) ──")
    if not cecite:
        print("    (aucune : tout facteur diagnostiqué a un signe)")
    for facteur, n in sorted(cecite.items(), key=lambda kv: (-kv[1], kv[0])):
        tag = " [INVISIBLE structurel]" if facteur in FACTEURS_INVISIBLES else " [signe tardif]"
        print(f"    {facteur:<18} × {n:>6}{tag}")

    qualite = accord / total * 100 if total else 0.0
    print(f"\n  ➜ QUALITÉ SÉMIOLOGIQUE = {qualite:.1f} %  "
          f"(accord de décision omniscient↔semio sur {total} observations)")
    print("    (100 % = tout facteur limitant a un signe fidèle et à temps ;"
          " chaque point perdu = un signe absent, tardif ou ambigu à concevoir.)")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Banc de mesure de la sémiologie : écart de décision "
                    "omniscient↔semiologique (tronçon ⑦, optionnel).")
    ap.add_argument("--years", type=int, default=2,
                    help="années simulées (défaut 2 ; PAS 500 ! cf. perf LightField)")
    ap.add_argument("--config", default="full", choices=["full", "propre"])
    ap.add_argument("--seed", type=lambda s: int(s, 0), default=0x5AB1057E)
    args = ap.parse_args()

    weeks = args.years * 52
    print(f"=== Banc SÉMIOLOGIE — écart omniscient↔semiologique — config={args.config}, "
          f"seed={args.seed:#x}, years={args.years} ({weeks} sem) ===")
    engine = _build_engine(args.config, args.seed)
    player = engine.game_state["current_player"]
    marquer_jardin_cultive(engine, player)     # déclare le jardin initial (hors tick)
    conf = _confusion(engine, player, weeks)
    _rapport(conf)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
