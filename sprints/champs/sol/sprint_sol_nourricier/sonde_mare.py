"""D120 ④ : la mare NE du monde full — lame, marais, faune, plantes de mare. Lecture seule.
Usage (depuis data/code/) : PYTHONPATH=. python3 <ce fichier> <seed> <semaines>"""
import sys
from tools.simserver.server import SimServer
from sim.mare_initiale import MARE_FOND
MARE_CENTRE=(8,5)
from fields.ecofields.constants import SEUIL_FLAQUE

seed=int(sys.argv[1]); W=int(sys.argv[2])
srv=SimServer(); srv.cmd_init({"config":"full","seed":seed})
gs=srv.engine.game_state; eco=gs['eco']['NE']; tile=[t for t in gs['tiles'] if t.tile_id=='NE'][0]
r0,c0=MARE_CENTRE
ok=0; lame_ok=0; maj=0; mous={}; lib={}
def mare_plants():
    return [(p.plant_class.name, int(p.y_cm//50), int((p.x_cm-1450)//50), round(getattr(p,'vitalite',0) or 0,2)) for p in tile.plants if p.is_alive and p.plant_class.name in ('Aulne','Sphaigne','Rossolis')]
vus={}
for w in range(W):
    srv.cmd_step_week({})
    presents={id(p) for p in tile.plants}
    for k in list(vus):
        if k not in presents and vus[k] is not None: print('DISPARU',w,vus[k]); vus[k]=None
    for p in tile.plants:
        if p.plant_class.name in ('Aulne','Sphaigne','Rossolis'):
            k=id(p)
            if p.is_alive: vus[k]={'nom':p.plant_class.name,'pos':(round(p.x_cm),round(p.y_cm)),'stage':str(getattr(p,'stage',''))} | {kk:round(v,2) for kk,v in vars(p).items() if isinstance(v,float) and ('memory' in kk or 'vital' in kk)}
            elif vus.get(k) is not None: print('MORT',w,p.plant_class.name,round(p.x_cm),round(p.y_cm),vus[k], getattr(p,'stage',None)); vus[k]=None
    m=eco.est_marais(r0,c0); l=eco.eau_surface.data[r0][c0]>SEUIL_FLAQUE
    nm=sum(eco.est_marais(*p) for p in MARE_FOND); nl=sum(eco.eau_surface.data[r][c]>SEUIL_FLAQUE for r,c in MARE_FOND)
    ok+= (m and l); lame_ok+=l
    maj+= sum(eco.est_marais(r,c) and eco.eau_surface.data[r][c]>SEUIL_FLAQUE for r,c in MARE_FOND)>=5
    mo=max(eco.populations['moustique'].data[r][c] for r,c in MARE_FOND); li=max(eco.populations['libellule'].data[r][c] for r,c in MARE_FOND)
    if w==26: print('S fond', [round(eco.altitude.data[r][c]+eco.epaisseur_sol.data[r][c],1) for r,c in MARE_FOND], 'lame', [round(eco.eau_surface.data[r][c],2) for r,c in MARE_FOND])
    if w%8==0 or w==W-1:
        print(w,'lame',round(eco.eau_surface.data[r0][c0],2),'lame>flaque',nl,'/9 marais',nm,'/9 hum berge',round(eco.humidite.data[6][5],2),'ph',round(eco.ph.data[r0][c0],2),'mous',round(mo,3),'lib',round(li,3), 'plantes',mare_plants() if w%13==0 else '')
print(f"semaines >=5/9 plots lame+marais {maj}/{W}"); print(f"centre lame+marais {ok}/{W} = {ok/W:.0%}; lame {lame_ok}/{W}")
print('fin', mare_plants())
for p in tile.plants:
    if p.plant_class.name in ('Aulne','Sphaigne','Rossolis'):
        print(p.plant_class.name, p.is_alive, round(p.x_cm),round(p.y_cm), {k:round(v,2) for k,v in vars(p).items() if isinstance(v,float) and ('memory' in k or 'vital' in k or 'stress' in k or 'health' in k)}, getattr(p,'cause_mort',None) or getattr(p,'death_cause',None))
