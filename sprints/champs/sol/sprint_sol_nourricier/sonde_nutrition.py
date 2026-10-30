"""D120 ② — sonde : même espèce sur sol à l'équilibre vs sol carencé, 26 semaines.
Deux tuiles terre JUMELLES (mêmes humidité/microbiome), 3 plantes chacune. Mode
`maintenu` : le stock N/P/K de la tuile carencée est remis à 0,05 chaque semaine
(sol épuisé chronique, la recharge ① ne le comble pas). Mode `libre` : la recharge
joue. Lecture seule hors forçage du banc. Lancer depuis data/code (PYTHONPATH=.) :
    python3 ../../sprints/champs/sol/sprint_sol_nourricier/sonde_nutrition.py [maintenu|libre]
"""
import sys
from plants import Sunflower, Basil, Bean
from bancs.base import build_banc_tile, monde
from sim.engine import Engine

mode = sys.argv[1] if len(sys.argv) > 1 else "maintenu"
CAR, SEM, DEPART = 0.05, 26, 14          # semaine 14 = printemps
especes = [(Sunflower, 2, 2), (Basil, 2, 5), (Bean, 5, 3)]
riche, eco_r = build_banc_tile("RICHE", "terre", 8, 8, humidite=1.2,
                               fertilite=1.0, microbiome=0.3)
carence, eco_c = build_banc_tile("CARENCE", "terre", 8, 8, 500.0, 0.0, humidite=1.2,
                                 fertilite=CAR, microbiome=0.3)
suivies = {}                               # (tuile, espèce) → plante (suivie même retirée)
for t in (riche, carence):
    for e, r, c in especes:
        suivies[(t.tile_id, e.__name__)] = t.add_plant(e, r, c)
pic = {k: (0.0, 0) for k in suivies}       # (hauteur max, segments max) sur la run
tiles, ecos, house, banque = monde([riche, carence],
                                   {riche.tile_id: eco_r, carence.tile_id: eco_c})
gs = {"tiles": tiles, "eco": ecos, "scores": {}, "current_player": "j",
      "week": DEPART, "log": [], "house": house, "seed": 0x5AB1057E,
      "player_seed_bank": banque}
eng = Engine(gs)
for w in range(SEM):
    if mode == "maintenu":
        for f in (eco_c.n, eco_c.p, eco_c.k):
            f.fill(CAR)
    eng.tick_semaine(); gs["log"].clear()
    if w + 1 == SEM // 2:
        mi = {k: p.current_height for k, p in suivies.items()}
    for k, p in suivies.items():
        h, n = pic[k]
        pic[k] = (max(h, p.current_height), max(n, len(p.segments)))

print(f"mode={mode} · {SEM} sem dès s{DEPART} · (h à mi-course / h max / segments max)")
for t, eco in ((riche, eco_r), (carence, eco_c)):
    print(f" {t.tile_id} n/p/k fin={eco.n.average():.2f}/{eco.p.average():.2f}/{eco.k.average():.2f}")
    for e, _, _ in especes:
        k = (t.tile_id, e.__name__)
        p = suivies[k]
        print(f"    {e.__name__}: h_mi={mi[k]:.1f} h_max={pic[k][0]:.1f} seg_max={pic[k][1]} "
              f"gf={p.growth_factor:.2f} vivant={p.is_alive}")
