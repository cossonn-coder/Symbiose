"""
Banc headless « fécondation » (D139 caractères vivants ①b) — INVENTAIRE DE RISQUE.
Mesure, pas test : il imprime des chiffres à consigner dans `00_etat.md`. Golden
intact (monde en mémoire, espions posés sur des fonctions du moteur le temps du run).

Monde « full » du jeu (`main.build_world_full`, fruitiers pré-vieillis comme
`bancs/mesure_nouaison._monde_full`), 3 ans. Pour chaque espèce :
  - à la FANAISON (`decompo.feconder`) : dose `pollen_recu` (min/médiane/max) et
    `fecondation` obtenue, nombre de fanaisons ;
  - à la MISE EN GRAINE (reproduction d'automne + fin de cycle) : nombre de pieds
    qui auraient grené AVANT ①b (rate > 0) contre ceux qui grènent maintenant
    (rate × fecondation > 0). Une espèce « avant > 0, maintenant 0 » a PERDU ses
    graines (jamais fleurie, mode `wind` sans vent…) : à consigner, pas à corriger.

Lancement (depuis data/code/) :
    python3 ../../sprints/vegetal/genetique/sprint_caracteres_vivants/mesures/banc_fecondation.py [ans]
"""

import os
import statistics as st
import sys
from collections import defaultdict

sys.path.insert(0, os.getcwd())


def main(n_ans: int = 3):
    from main import build_world_full
    from sim.engine import Engine
    from sim.engine import decompo, mortalite
    from sim.reproduction import is_seed_bearing, graine_fertile, recrue_par_fruits
    from sim import vigueur as VIG
    from sim.seeds import PlayerSeedBank

    tiles, ecos, _aux, house = build_world_full()
    for t in tiles:
        for p in t.plants:
            if getattr(p.plant_class, "fruitier", False):
                p.age_years = float(p.plant_class.maturity_years)
    gs = {"tiles": tiles, "eco": ecos, "house": house, "scores": {},
          "current_player": "joueur_1", "week": 1, "log": [],
          "player_seed_bank": PlayerSeedBank()}
    VIG.ensure_player(gs, "joueur_1")
    eng = Engine(gs)

    doses = defaultdict(list)      # espèce → [pollen_recu à la fanaison]
    fecs = defaultdict(list)       # espèce → [fecondation]
    modes = {}
    avant = defaultdict(int)       # pieds qui grenaient avant ①b
    maintenant = defaultdict(int)  # pieds qui grènent avec ①b
    vivants = defaultdict(int)     # pieds vus vivants et mûrs (au moins une fois)

    orig_fec = decompo.feconder

    def _fec(plant):
        nom = plant.plant_class.__name__
        doses[nom].append(plant.pollen_recu)
        modes[nom] = plant.plant_class.pollination_mode
        f = orig_fec(plant)
        fecs[nom].append(f)
        return f
    decompo.feconder = _fec

    def _compte(plant):
        cls = plant.plant_class
        if not graine_fertile(cls) or recrue_par_fruits(cls):
            return
        if getattr(cls, "reproduction_rate", 0.0) > 0.0:
            avant[cls.__name__] += 1
            if plant.fecondation > 0.0:
                maintenant[cls.__name__] += 1

    orig_repro = type(eng)._reproduction

    def _repro(self, tile, eco, week, *a, **k):
        for p in tile.plants:
            if p.is_alive and is_seed_bearing(p):
                _compte(p)
        return orig_repro(self, tile, eco, week, *a, **k)
    type(eng)._reproduction = _repro

    orig_sfc = mortalite.semer_fin_de_cycle

    def _sfc(plant, *a, **k):
        _compte(plant)
        return orig_sfc(plant, *a, **k)
    mortalite.semer_fin_de_cycle = _sfc

    vus = set()
    try:
        for _ in range(52 * n_ans):
            eng.tick_semaine()
            gs["log"].clear()
            for t in tiles:
                for p in t.plants:
                    if p.is_alive and is_seed_bearing(p) and id(p) not in vus:
                        vus.add(id(p))
                        vivants[p.plant_class.__name__] += 1
    finally:
        decompo.feconder = orig_fec
        type(eng)._reproduction = orig_repro
        mortalite.semer_fin_de_cycle = orig_sfc

    print(f"Monde full, {n_ans} ans — fanaisons et mise en graine par espèce")
    print(f"{'espèce':<22}{'mode':<7}{'mûrs':>5}{'fan.':>5} "
          f"{'pollen min/méd/max':>22} {'fec méd':>8} {'grène av→ap':>12}")
    noms = sorted(set(vivants) | set(doses) | set(avant))
    perdus = []
    for nom in noms:
        d = doses.get(nom, [])
        f = fecs.get(nom, [])
        pol = (f"{min(d):.2f}/{st.median(d):.2f}/{max(d):.2f}" if d else "—")
        fm = f"{st.median(f):.3f}" if f else "—"
        print(f"{nom:<22}{modes.get(nom, '?'):<7}{vivants.get(nom, 0):>5}{len(d):>5} "
              f"{pol:>22} {fm:>8} {avant.get(nom, 0):>5}→{maintenant.get(nom, 0):<5}")
        if avant.get(nom, 0) > 0 and maintenant.get(nom, 0) == 0:
            perdus.append(nom)
    print(f"\nEspèces qui grenaient avant et ne grènent plus : {perdus or 'aucune'}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
