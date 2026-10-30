"""D120 : faim des bêtes LÀ OÙ elles sont présentes (lecture seule).
③ : la voix dit « faim » d'après `PopulationField.faim` (excès de population sur ce
que le lieu porte). Colonnes : ressource brute (ancienne grandeur, `activite`),
part « dit faim » AVANT ③ (ressource < 0,4) et APRÈS ③ (intensité ≥ SEUIL_DIRE),
part qui a DÉCLINÉ au dernier tick (densité < 97 % de la semaine précédente — c'est
ce tick qui a écrit la grille de faim), et part des affamés qui déclinent vraiment."""
import sys, collections
from tools.simserver.server import SimServer
from sim.voix_etres import SEUIL_DIRE, FAIM_BETE_APPARITION, FAIM_BETE_PLEINE, _ramp
def q(xs,f):
    xs=sorted(xs); return xs[int(f*(len(xs)-1))] if xs else float('nan')
seed=int(sys.argv[1]); W=int(sys.argv[2])
srv=SimServer(); srv.cmd_init({"config":"full","seed":seed})
for w in range(W-1): srv.cmd_step_week({})
gs=srv.engine.game_state
avant={(t.tile_id,cle,r,c):f.at_plot(r,c) for t in gs['tiles']
       for cle,f in (gs['eco'][t.tile_id].populations or {}).items()
       for r in range(f.rows) for c in range(f.cols)}
srv.cmd_step_week({})
gs=srv.engine.game_state
res=collections.defaultdict(list)
for t in gs['tiles']:
    eco=gs['eco'][t.tile_id]
    for cle,f in (eco.populations or {}).items():
        for r in range(eco.rows):
            for c in range(eco.cols):
                d=f.at_plot(r,c)
                if d>0.05:
                    dit=_ramp(f.faim(r,c),FAIM_BETE_APPARITION,FAIM_BETE_PLEINE)>=SEUIL_DIRE
                    res[cle].append((f.activite(r,c),d,dit,(t.tile_id,r,c)))
print(f"semaine {W} (seed {seed})")
tot=collections.Counter()
for cle,v in sorted(res.items()):
    a=[x for x,_,_,_ in v]
    decl=[d<avant.get((tid,cle,r,c),0.0)*0.97 for _,d,_,(tid,r,c) in v]
    dits=[x[2] for x in v]
    nd=sum(dits); nd_decl=sum(1 for di,de in zip(dits,decl) if di and de)
    tot.update(n=len(v), avant=sum(x<0.4 for x in a), apres=nd, decl=sum(decl), dd=nd_decl)
    print(f"  {cle:11s} plots {len(v):4d} · ressource méd {q(a,.5):.2f} · dit faim avant③ {sum(x<0.4 for x in a)/len(v):4.0%} → après③ {nd/len(v):4.0%} · déclin {sum(decl)/len(v):4.0%} · affamés qui déclinent {(nd_decl/nd if nd else float('nan')):.0%} · densité méd {q([d for _,d,_,_ in v],.5):.2f}")
n=tot['n']
print(f"  TOTAL plots {n} · dit faim avant③ {tot['avant']/n:.0%} → après③ {tot['apres']/n:.0%} · déclin {tot['decl']/n:.0%} · affamés qui déclinent {(tot['dd']/tot['apres'] if tot['apres'] else float('nan')):.0%}")
