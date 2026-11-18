"""
Mesure headless du banc F5 `niche_thermique` (D139 ⑤) : déroule le banc comme la vue
(seed 42, départ BANC_WEEK_DEPART, warmup compris) et imprime, semaine par semaine,
le palier thermique de chaque pied — ce que Nico doit voir au F5. Mesure, pas test ;
golden intact (rien n'est écrit sur disque).

Lancement (depuis data/code/) :
    python3 ../../sprints/vegetal/genetique/sprint_niche_thermique/mesures/mesure_banc_vue.py [semaines]
"""
import os
import sys

sys.path.insert(0, os.getcwd())

from bancs import BANCS, BANC_WEEK_DEPART, BANC_POST_INIT, BANC_WARMUP
from sim.engine import Engine
from sim.engine.posture_thermique import etat_thermique

SEED = 42          # = WorldView.Seed (la vue envoie toujours son seed)
WARMUP = BANC_WARMUP["niche_thermique"]   # warmup F5 du banc (défaut vue : 12)

ABREV = {"pendant": "pend", "violace": "viol", "froid": "DETR", "gel": "GEL",
         "effondre": "EFF", "replie": "repl", "fletri_midi": "flet",
         "bords_jaunis": "JAUN", "brulure": "BRUL", None: " ok "}


def main(semaines: int) -> None:
    tiles, ecos, house, banque = BANCS["niche_thermique"]()
    week = BANC_WEEK_DEPART["niche_thermique"]
    gs = {"tiles": tiles, "eco": ecos, "scores": {}, "current_player": "j1",
          "week": week, "log": [], "house": house, "seed": SEED,
          "player_seed_bank": banque}
    BANC_POST_INIT["niche_thermique"](gs, "j1")
    eng = Engine(gs)
    suivis = [(t.tile_id, p) for t in tiles for p in list(t.plants)]
    print("semaine | " + " ".join(f"{tid[:6]}{p.position}" for tid, p in suivis))
    for _ in range(semaines):
        eng.tick_semaine()
        gs["log"].clear()
        w = gs["week"] - 1
        cells = []
        for tid, p in suivis:
            if not p.is_alive:
                cells.append("mort")
                continue
            eco = ecos[tid]
            _post, pal = etat_thermique(p, eco)
            cells.append(ABREV[pal] if pal in ABREV else pal[:4])
        marque = "  <- ouverture F5" if gs["week"] - week == WARMUP else ""
        nuit = min((p.t_nuit for _, p in suivis if p.is_alive and p.t_nuit is not None),
                   default=float("nan"))
        tf = max((p.t_feuille for _, p in suivis if p.is_alive and p.t_feuille is not None),
                 default=float("nan"))
        print(f"s{(w - 1) % 52 + 1:2d} n{nuit:5.1f} f{tf:5.1f} | " + " ".join(cells) + marque)
    for tid, p in suivis:
        if p.is_alive:
            print(f"  {tid:13s} {p.plant_class.name:8s} {p.position} vivant vit {p.vitalite:.2f} "
                  f"gel {p.lim_gel():.1f} froid {p.lim_froid():.1f} chaud {p.lim_chaud():.1f} "
                  f"brul {p.lim_brul():.1f}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 40)
