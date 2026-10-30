"""D120 : NPK du monde full, voix dominante des plantes/bêtes, vitalité. Lecture seule."""
import sys, collections
from tools.simserver.server import SimServer
from sim.voix_etres import besoins_plante, contexte_tuile, besoins_bete
from sim.vigueur_plante import qi_local, FIELD_NORM
from tools.simserver.vision_cmds import _semaine
from sim.voix_etres import SEUIL_DIRE

def med(xs):
    xs=sorted(xs); return xs[len(xs)//2] if xs else float('nan')

seed=int(sys.argv[1]); W=int(sys.argv[2])
srv=SimServer(); srv.cmd_init({"config":"full","seed":seed})
eng=srv.engine
for w in range(W+1):
    if w % 13 == 0:
        npk={'n':[],'p':[],'k':[]}; top=collections.Counter(); nut=collections.Counter()
        vit=[]; qi=[]; faim_int=[]; btop=collections.Counter()
        gs=eng.game_state; _,saison=_semaine(gs)
        for t in gs['tiles']:
            eco=gs['eco'][t.tile_id]
            for e in npk: npk[e].append(getattr(eco,e).average())
            ctx=contexte_tuile(t)
            for p in t.plants:
                if not p.is_alive: continue
                try:
                    b=besoins_plante(p,t,eco,saison,ctx)
                except Exception as ex:
                    print('err',ex); b=[]
                if b:
                    i,th,ch=max(b,key=lambda x:x[0])
                    top[th if i>=SEUIL_DIRE else 'bien']+=1
                    for i2,th2,ch2 in b:
                        if th2=='faim' and i2>=SEUIL_DIRE: nut[ch2['nutriment']]+=1
                        if th2=='faim': faim_int.append(i2)
                qi.append(qi_local(p,eco))
                v=getattr(p,'vitalite',None)
                if v is not None: vit.append(v)
            for cle,f in (eco.populations or {}).items():
                for r in range(0,eco.rows,4):
                    for c in range(0,eco.cols,4):
                        try:
                            bb=besoins_bete(cle,t,eco,r,c)
                        except Exception as ex:
                            bb=[]
                        if bb:
                            i,th,_=max(bb,key=lambda x:x[0]); btop[th if i>=SEUIL_DIRE else 'bien']+=1
        n=lambda e: f"{med(npk[e]):.2f}"
        print(f"s{w} an{w//52} NPK méd tuiles {n('n')}/{n('p')}/{n('k')} (FIELD_NORM {FIELD_NORM}) · plantes {sum(top.values())} · qi méd {med(qi):.2f} · vitalité méd {med(vit):.2f} · faim int méd {med(faim_int):.2f} · nutriment cité {dict(nut)} · voix dominante {top.most_common(5)} · bêtes {btop.most_common(4)}", flush=True)
    if w<W: srv.cmd_step_week({})
