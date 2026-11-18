"""
Banc headless « levée des graines » (D139 caractères vivants ①d) — POPULATION.
Mesure, pas test : il imprime des chiffres à consigner dans `00_etat.md`. Golden
intact (monde en mémoire, aucun espion sur le moteur : on lit le log et les tuiles).

Monde « full » du jeu (`main.build_world_full`, fruitiers pré-vieillis comme
`banc_fecondation`), N ans (10 par défaut, ne pas dépasser sans raison). Pour chaque
année : nombre de pieds vivants par espèce au cœur de l'été (semaine 26 de l'année)
et au maximum de l'année, levées férales (« 🌿 Germination ») par espèce et par voie
(archétype S3 / ressemis S2), temps de tick moyen, tuiles au cap perf.

À lancer AVANT et APRÈS le tronçon (même seed, même monde) et à comparer.

Lancement (depuis data/code/) :
    python3 ../../sprints/vegetal/genetique/sprint_caracteres_vivants/mesures/banc_levee.py [ans] [sortie.json]
"""

import json
import os
import re
import sys
import time
from collections import Counter, defaultdict

sys.path.insert(0, os.getcwd())

_GERM = re.compile(r"🌿 Germination : (.+?) @\(\d+,\d+\) \[niche=[0-9.]+ (\S+?)\]")


def main(n_ans: int = 10, sortie: str | None = None):
    from main import build_world_full
    from sim.engine import Engine
    from sim import vigueur as VIG
    from sim.seeds import PlayerSeedBank
    from sim.capacite import CAP_PERF_TUILE

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

    ans = []
    for an in range(n_ans):
        ete, maxi = Counter(), Counter()
        levees = defaultdict(Counter)       # voie → espèce → nombre
        cap, t_tot = 0, 0.0
        for s in range(52):
            t0 = time.perf_counter()
            eng.tick_semaine()
            t_tot += time.perf_counter() - t0
            for ligne in gs["log"]:
                m = _GERM.search(ligne)
                if m:
                    voie = "S2" if m.group(2) == "ressemis" else "S3"
                    levees[voie][m.group(1)] += 1
                if "cap perf" in ligne:
                    cap += 1
            gs["log"].clear()
            compte = Counter(p.plant_class.name for t in tiles for p in t.plants
                             if p.is_alive)
            for nom, n in compte.items():
                maxi[nom] = max(maxi[nom], n)
            if s == 25:
                ete = compte
        n_tuile = max(sum(1 for p in t.plants if p.is_alive) for t in tiles)
        ans.append({"an": an + 1, "ete": dict(ete), "max": dict(maxi),
                    "levees": {v: dict(c) for v, c in levees.items()},
                    "tick_s": t_tot / 52, "cap_hits": cap,
                    "max_par_tuile": n_tuile})
        print(f"an {an + 1:>2} : {sum(ete.values()):>5} pieds en été, tick "
              f"{t_tot / 52:.2f} s, max/tuile {n_tuile} (cap {CAP_PERF_TUILE}), "
              f"cap atteint {cap}×, levées S3 {sum(levees['S3'].values())} "
              f"S2 {sum(levees['S2'].values())}", flush=True)

    especes = sorted({n for a in ans for n in a["ete"]})
    print(f"\n{'espèce (été)':<26}" + "".join(f"{a['an']:>6}" for a in ans))
    for nom in especes:
        print(f"{nom:<26}" + "".join(f"{a['ete'].get(nom, 0):>6}" for a in ans))
    s2 = Counter()
    for a in ans:
        s2.update(a["levees"].get("S2", {}))
    print(f"\nRessemis S2 cumulés : {dict(s2.most_common()) or 'aucun'}")
    if sortie:
        with open(sortie, "w") as f:
            json.dump(ans, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 10,
         sys.argv[2] if len(sys.argv) > 2 else None)
