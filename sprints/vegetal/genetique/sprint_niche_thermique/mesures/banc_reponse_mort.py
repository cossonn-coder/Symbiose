"""
Banc headless « la plante répond et meurt d'elle-même » (D139 niche thermique ③).
Mesure, pas test : il imprime des chiffres à consigner dans `00_etat.md`. Golden
intact (rien n'est écrit sur disque ; les forçages sont des monkeypatchs en mémoire,
un sous-processus par scénario).

Lancement (depuis data/code/) :
    python3 ../../sprints/vegetal/genetique/sprint_niche_thermique/mesures/banc_reponse_mort.py [nuit|basilic|hiver|canicule|graines|bisannuelle|tout]

  nuit        basilic neutre à nuits forcées 6 / 7 / 8 °C (été) : vitalité semaine par semaine
  (nuit, basilic, canicule : perturbations coupées, cf. `_sans_herbivorie`)
  basilic     basilic semé s12 (mi-juin), sol nu / paillé (litière) / voilé : date et cause
  hiver       mâche et seigle semés s27 (automne) : passent-ils l'hiver ? fin de cycle ?
  canicule    T_air forcée 28 °C ciel clair s16-19 : basilic assoiffé au soleil / arrosé /
              ombragé (lumière reçue forcée à 0,3 : l'ombrière n'atténue que la
              lumière-SOL, pas `light_received` de la plante — constat ③)
  graines     basilic, phacélie, moutarde, bourse-à-pasteur, 3 ans : pic de vivants par
              an AVEC et SANS le dépôt de graines à la fin de cycle (seule la bourse a un
              archétype : la succession férale ne fait lever que les archétypes)
  bisannuelle carotte semée s1 : fleurit-elle l'an 2, s'éteint-elle par fin de cycle ?
"""

import os
import subprocess
import sys

sys.path.insert(0, os.getcwd())

SEED = 42


def _monde(rows=8, cols=8, week=1, humidite=1.5):
    from world import Tile, House
    from fields import init_eco
    from sim.engine import Engine
    tile = Tile(tile_id="B", soil_type="terre", grid_rows=rows, grid_cols=cols,
                origin_x_cm=0.0, origin_y_cm=0.0)
    eco = init_eco("B", rows, cols, humidite=humidite, fertilite=1.0, microbiome=0.3,
                   soil_type="terre", heterogene=False)
    gs = {"tiles": [tile], "eco": {"B": eco}, "scores": {}, "seed": SEED,
          "current_player": "j1", "week": week, "log": [], "house": House()}
    return tile, eco, Engine(gs), gs


def _sans_herbivorie():
    """Isole la réponse thermique : coupe les perturbations (herbivorie, maladie,
    mortalité de fond) qui emportent un semis isolé en 2-4 semaines et masquent la
    cause qu'on mesure. Seulement pour les scénarios nuit / basilic / canicule."""
    import sim.engine.boucle as BO
    BO.apply_disturbances = lambda *a, **k: []


def _cause(log, plant):
    """Ligne de log de la mort d'une plante (cause lisible)."""
    tag = f"@{plant.position}"
    for l in log:
        if tag in l and ("meurt" in l or "→ meurt" in l):
            return l.strip()[:90]
    return "?"


def _suivre(eng, gs, plante, semaines):
    """Tique jusqu'à la mort de `plante` ou `semaines` ; renvoie (semaine abs, cause)."""
    for _ in range(semaines):
        w = gs["week"]
        log = eng.tick_semaine()
        gs["log"].clear()
        if not plante.is_alive:
            return w, _cause(log, plante)
    return None, f"vivante (vit {plante.vitalite:.2f})"


def _wiy(w):
    return f"s{(w - 1) % 52 + 1}/an{(w - 1) // 52 + 1}"


def scenario_nuit():
    _sans_herbivorie()
    import sim.engine.reponse_thermique as RT
    from plants import Basil
    for t in (6.0, 7.0, 8.0):
        RT.t_min_nuit_at = lambda *a, _t=t: _t
        tile, eco, eng, gs = _monde(week=14)
        b = tile.add_plant(Basil, 3, 3)
        traj = []
        for _ in range(12):
            log = eng.tick_semaine()
            gs["log"].clear()
            traj.append(round(b.vitalite, 2))
            if not b.is_alive:
                break
        print(f"  nuits {t:.0f} °C : vitalité par semaine {traj} — "
              f"{_cause(log, b) if not b.is_alive else 'vivant'}")


def scenario_basilic():
    _sans_herbivorie()
    from plants import Basil
    for mode in ("nu", "paillé", "voilé"):
        tile, eco, eng, gs = _monde(week=12)
        b = tile.add_plant(Basil, 3, 3)
        if mode == "voilé":
            eco.poser_couvert(3, 3, 0.85, 1.5)          # = geste poser_voile
        w = None
        for _ in range(60):
            if mode == "paillé":                        # litière maintenue ≈ 1 (½ saturation)
                manque = 1.0 - eco.om_fresh_at(3, 3)
                eco.deposer_litiere(3, 3, "herbace", max(0.0, manque))
            wk = gs["week"]
            log = eng.tick_semaine()
            gs["log"].clear()
            if not b.is_alive:
                w = wk
                break
        print(f"  basilic {mode:6s} : {'mort ' + _wiy(w) if w else 'vivant'} — "
              f"{_cause(log, b) if w else ''}")


def scenario_hiver():
    from plants import CornSalad, Rye
    for cls in (CornSalad, Rye):
        tile, eco, eng, gs = _monde(week=27)
        p = tile.add_plant(cls, 3, 3)
        vmin, w_mort = 1.0, None
        for _ in range(78):
            wk = gs["week"]
            log = eng.tick_semaine()
            gs["log"].clear()
            if p.is_alive:
                vmin = min(vmin, p.vitalite)
            elif w_mort is None:
                w_mort, cause = wk, _cause(log, p)
                break
        fl = _wiy(p.floraison_abs) if p.floraison_abs > 0 else "jamais"
        fin = (f"mort {_wiy(w_mort)} — {cause}" if w_mort else "vivante")
        print(f"  {cls.name:8s} semé s27 : vitalité min {vmin:.2f} ; 1ʳᵉ floraison {fl} ; {fin}")


def scenario_canicule():
    _sans_herbivorie()
    import sim.engine.boucle as BO
    from plants import Basil
    meteo = BO.weather_state

    def canicule(seed, week, *a, **k):
        ev, t, n = meteo(seed, week, *a, **k)
        if 16 <= (week - 1) % 52 + 1 <= 19:
            return ev, 28.0, 0.0
        return ev, t, n
    BO.weather_state = canicule
    for mode in ("assoiffé", "arrosé", "ombragé"):
        tile, eco, eng, gs = _monde(week=14)
        b = tile.add_plant(Basil, 3, 3)
        hum = 2.0 if mode == "arrosé" else 0.05
        eco.humidite.at_plot = lambda r, c, _h=hum: _h
        if mode == "ombragé":
            eco.lumiere.light_received = lambda p: 0.3
        tmax, brul, stag = -99.0, 0, 0
        for _ in range(12):
            log = eng.tick_semaine()
            gs["log"].clear()
            if b.t_feuille is not None:
                tmax = max(tmax, b.t_feuille)
            brul += sum("brûlure" in l and "Basilic" in l for l in log)
            stag += sum("stagne (chaud" in l and "Basilic" in l for l in log)
            if not b.is_alive:
                break
        etat = (f"mort — {_cause(log, b)}" if not b.is_alive
                else f"vivant (vit {b.vitalite:.2f})")
        print(f"  basilic {mode:8s} : T_feuille max {tmax:.1f} °C, lim_brul "
              f"{b.lim_brul():.1f} ; {brul} brûlures, {stag} sem. sans croissance ; {etat}")


def scenario_graines():
    import sim.engine.mortalite as MO
    from plants import Basil, Phacelia, Mustard, BursaPastoris
    avec = os.environ.get("SANS_DEPOT") is None
    if not avec:
        MO.semer_fin_de_cycle = lambda *a: None
    print(f"  dépôt de graines à la fin de cycle : {'AVEC' if avec else 'SANS'}")
    for cls, sem in ((Basil, 12), (Phacelia, 1), (Mustard, 1), (BursaPastoris, 1)):
        tile, eco, eng, gs = _monde(week=sem)
        tile.add_plant(cls, 3, 3)
        par_an = []
        for an in range(3):
            pic = 0
            for _ in range(52):
                eng.tick_semaine()
                gs["log"].clear()
                pic = max(pic, sum(1 for p in tile.plants
                                   if p.is_alive and p.plant_class is cls))
            par_an.append(pic)
        print(f"    {cls.name:10s} (semé s{sem}) : pic de vivants par an {par_an}")


def scenario_bisannuelle():
    from plants import Carrot
    tile, eco, eng, gs = _monde(week=1)
    p = tile.add_plant(Carrot, 3, 3)
    w, cause = _suivre(eng, gs, p, 52 * 3)
    fl = _wiy(p.floraison_abs) if p.floraison_abs > 0 else "jamais"
    print(f"  carotte semée s1 : 1ʳᵉ floraison {fl} ; "
          f"{'mort ' + _wiy(w) + ' — ' + cause if w else cause}")


SCENARIOS = {"nuit": scenario_nuit, "basilic": scenario_basilic, "hiver": scenario_hiver,
             "canicule": scenario_canicule, "graines": scenario_graines,
             "bisannuelle": scenario_bisannuelle}

if __name__ == "__main__":
    choix = sys.argv[1] if len(sys.argv) > 1 else "tout"
    if choix == "tout":
        for nom in SCENARIOS:
            print(f"[{nom}]", flush=True)
            subprocess.run([sys.executable, __file__, nom], check=True)
            if nom == "graines":
                subprocess.run([sys.executable, __file__, nom], check=True,
                               env={**os.environ, "SANS_DEPOT": "1"})
    else:
        SCENARIOS[choix]()
