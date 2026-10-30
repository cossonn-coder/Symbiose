"""D120 : ressource locale (activite) des bêtes LÀ OÙ elles sont présentes."""
import sys, collections
from tools.simserver.server import SimServer
def q(xs,f):
    xs=sorted(xs); return xs[int(f*(len(xs)-1))] if xs else float('nan')
seed=int(sys.argv[1]); W=int(sys.argv[2])
srv=SimServer(); srv.cmd_init({"config":"full","seed":seed})
for w in range(W): srv.cmd_step_week({})
gs=srv.engine.game_state
res=collections.defaultdict(list)
for t in gs['tiles']:
    eco=gs['eco'][t.tile_id]
    for cle,f in (eco.populations or {}).items():
        for r in range(eco.rows):
            for c in range(eco.cols):
                d=f.at_plot(r,c)
                if d>0.05: res[cle].append((f.activite(r,c),d))
print(f"semaine {W}")
for cle,v in sorted(res.items()):
    a=[x for x,_ in v]
    print(f"  {cle:11s} plots présents {len(v):4d} · ressource q10/méd/q90 {q(a,.1):.2f}/{q(a,.5):.2f}/{q(a,.9):.2f} · part <0,4 (dit faim) {sum(x<0.4 for x in a)/len(a):.0%} · densité méd {q([d for _,d in v],.5):.2f}")
