"""
Banc headless « paternité » (D139 caractères vivants ①c). Mesure, pas test : il
imprime des chiffres à consigner dans `00_etat.md`. Rien n'est écrit sur disque.

Lancement (depuis data/code/) :
    python3 ../../sprints/vegetal/genetique/sprint_caracteres_vivants/mesures/banc_paternite.py [n_seeds]

Une mère neutre au centre, deux pères à égale distance (100 cm, même rangée) :
l'un ATTIRANT (`nectar` et `taille_fleur` à 1,3), l'autre TERNE (0,7). Sur une
saison, on lit (1) le `pollen_donne` de chaque père à la mise en graine de la mère,
(2) la part de paternité ATTENDUE du père attirant = son poids / Σ poids, et (3) les
pères réellement tirés par `find_father` pour CETTE mère (tous chemins confondus).
Les côtés gauche/droite sont alternés d'une graine de monde à l'autre (biais de
position neutralisé).
"""

import os
import sys

sys.path.insert(0, os.getcwd())

ATTIRANT = {"nectar": 1.3, "taille_fleur": 1.3}
TERNE = {"nectar": 0.7, "taille_fleur": 0.7}


def _monde(cls, seed, attirant_a_gauche):
    from world import Tile, House
    from fields import init_eco
    from sim.engine import Engine
    from sim.seeds import semer_fondateur
    tile = Tile(tile_id="B", soil_type="terre", grid_rows=8, grid_cols=8)
    for _ in range(3):
        tile.stakes[0].add("pollinisateur")
        tile.stakes[1].add("auxiliaire")
    eco = init_eco("B", 8, 8, humidite=1.5, fertilite=1.0, microbiome=0.3,
                   soil_type="terre", heterogene=True)
    mere = semer_fondateur(tile, cls, 4, 4, seed, sauvage=True)
    g = semer_fondateur(tile, cls, 4, 2, seed, sauvage=True)
    d = semer_fondateur(tile, cls, 4, 6, seed, sauvage=True)
    att, ter = (g, d) if attirant_a_gauche else (d, g)
    att.genes.update(ATTIRANT)
    ter.genes.update(TERNE)
    gs = {"tiles": [tile], "eco": {"B": eco}, "scores": {}, "seed": seed,
          "current_player": "joueur_1", "week": 1, "log": [], "house": House()}
    return gs, Engine(gs), mere, att, ter


def _espionner(tirages):
    """Remplace `find_father` chez tous ses appelants ; consigne (mère, père)."""
    import sim.reproduction as R
    import sim.engine.mortalite as M, sim.engine.fin_de_cycle as F
    import sim.engine.decompo as D, sim.engine.boucle as B
    import sim.zoochorie as Z, sim.caches as C
    orig = R.find_father

    def espion(mother, plants, tile, eco, seed, week):
        pere = orig(mother, plants, tile, eco, seed, week)
        tirages.append((mother, pere))
        return pere
    for m in (M, F, D, B, Z, C):
        m.find_father = espion


def main():
    from plants import Borage
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    tirages = []
    _espionner(tirages)
    parts, n_att, n_ter, n_self = [], 0, 0, 0
    print(f"(①c) bourraches — mère neutre, père attirant (1,3) contre terne (0,7), "
          f"{n_seeds} mondes")
    for k in range(n_seeds):
        gs, eng, mere, att, ter = _monde(Borage, 42 + k, k % 2 == 0)
        tirages.clear()
        donne = (0.0, 0.0)
        for _ in range(52):
            eng.tick_semaine()
            gs["log"].clear()
            if any(m is mere for m, _ in tirages) and donne == (0.0, 0.0):
                donne = (att.pollen_donne, ter.pollen_donne)
        if donne == (0.0, 0.0):
            donne = (att.pollen_donne, ter.pollen_donne)
        part = donne[0] / sum(donne) if sum(donne) > 0 else float("nan")
        parts.append(part)
        peres = [p for m, p in tirages if m is mere]
        a = sum(p is att for p in peres)
        t = sum(p is ter for p in peres)
        s = sum(p is None for p in peres)
        n_att, n_ter, n_self = n_att + a, n_ter + t, n_self + s
        print(f"  seed {42 + k} : donné attirant {donne[0]:.2f} / terne {donne[1]:.2f}"
              f" → part attendue {part:.2f} | tirés : attirant {a}, terne {t}, aucun {s}")
    ok = [p for p in parts if p == p]
    print(f"  part attendue moyenne : {sum(ok) / len(ok):.3f} [n={len(ok)} mondes]"
          if ok else "  aucun pollen exporté")
    print(f"  tirages réels : attirant {n_att}, terne {n_ter}, autofécondé/sans père {n_self}")


if __name__ == "__main__":
    main()
