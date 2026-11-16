"""
Banc headless « réponse à la sélection » (D139 ③). Mesure, pas test : il imprime des
chiffres à consigner dans `00_etat.md`. Golden intact (rien n'est écrit sur disque,
les surcharges de climat sont en mémoire, dans un sous-processus par scénario).

Lancement (depuis data/code/) :
    python3 ../../sprints/vegetal/genetique/sprint_genetique_infinitesimale/mesures/banc_reponse_selection.py [a|b|tout]

(a) PARCELLE FROIDE, 10 ans de succession férale seule (seed 42) : climat normal
    (T_MOY 11 °C) contre site froid (T_MOY abaissée). On suit la moyenne, pondérée
    par la densité, de `germination_thermique` (°C) dans la banque-sol. Une réponse
    à la sélection = la moyenne du site froid dérive vers le haut (lève-tôt) plus
    que celle du témoin. Cible : ≥ +1 °C.
(b) LIGNÉES, 6 générations : tomate (autogame) contre courgette (allogame). Chaque
    génération = 8 frères issus d'une même mère (`heredite`, père = un autre
    individu de la génération). On suit le F moyen et la variance entre frères
    de `hauteur` (facteur) et `phenologie_florale` (semaines).
"""

import os
import statistics as st
import subprocess
import sys

sys.path.insert(0, os.getcwd())

SEED = 42
ANS = 10
# Témoin = climat normal (T_MOY 11 °C, gain solaire 15 °C). Parcelle froide = site
# frais (T_MOY 7 °C) ET à l'ombre (aucun gain solaire au sol) : sans l'ombre, le
# soleil d'été réchauffe le sol au-delà des optimums de levée, et le froid ne trie
# rien (mesuré : un T_MOY abaissé seul laisse les levées à T_sol ≈ optimum).
TEMOIN = (11.0, 15.0)
FROID = (7.0, 0.0)


def _moyenne_pool(eco, nom="germination_thermique"):
    """Moyenne (pondérée par la densité) d'un caractère dans toute la banque-sol."""
    tot = acc = 0.0
    bank = eco.seed_bank
    for r in range(bank.rows):
        for c in range(bank.cols):
            for rec in bank.species[r][c].values():
                stat = rec["genes"].get(nom)
                d = rec.get("density", 0.0)
                if stat is not None and d > 0:
                    tot += d
                    acc += d * stat.mean
    return acc / tot if tot else float("nan")


def scenario_a(t_moy, gain):
    import importlib
    import sim.weather as W
    import fields.ecofields.thermique as TH
    W.T_MOY, TH.GAIN_SOLAIRE = t_moy, gain
    succ = importlib.import_module("sim.succession")   # `sim.succession` = la fonction
    levees = []                                          # gène des semis féraux, par an
    tri = succ._levee_triee

    def espion(genes, *a):
        tri(genes, *a)
        levees[-1].append(genes.get("germination_thermique", 0.0))
    succ._levee_triee = espion
    from world import Tile, House
    from fields import init_eco
    from sim.engine import Engine
    tile = Tile(tile_id="F", soil_type="terre", grid_rows=8, grid_cols=8,
                origin_x_cm=0.0, origin_y_cm=0.0)
    eco = init_eco("F", 8, 8, humidite=1.5, fertilite=1.0, microbiome=0.3,
                   soil_type="terre", heterogene=True)
    gs = {"tiles": [tile], "eco": {"F": eco}, "scores": {}, "seed": SEED,
          "current_player": "joueur_1", "week": 1, "log": [], "house": House()}
    eng = Engine(gs)
    print(f"T_MOY={t_moy:4.1f} GAIN_SOLAIRE={gain:4.1f} — par an : "
          "pool | vivants (n) | semis féraux (n)")
    for an in range(1, ANS + 1):
        levees.append([])
        for _ in range(52):
            eng.tick_semaine()
            gs["log"].clear()
        viv = [p.gene("germination_thermique") for p in tile.plants if p.is_alive]
        lv = levees[-1]
        print(f"  an {an:2d} : {_moyenne_pool(eco):+.3f} | "
              f"{(st.mean(viv) if viv else float('nan')):+.2f} ({len(viv)}) | "
              f"{(st.mean(lv) if lv else float('nan')):+.2f} ({len(lv)})")
    tous = [x for lv in levees for x in lv]
    print(f"  semis féraux sur {ANS} ans : moyenne {st.mean(tous):+.2f} °C (n={len(tous)})")


def scenario_b():
    from plants import PlantInstance, Tomato, Zucchini
    from fields import founder_genes
    from sim.reproduction import heredite
    for cls in (Tomato, Zucchini):
        mere = PlantInstance(plant_class=cls, position=(2, 2))
        mere.genes = founder_genes(cls, SEED, 1, 2, 2, 125.0, 125.0)
        pere = PlantInstance(plant_class=cls, position=(2, 4))
        pere.genes = founder_genes(cls, SEED, 1, 2, 4, 225.0, 125.0)
        print(f"{cls.__name__} (autofecondation neutre {mere.gene('autofecondation'):.2f})")
        for gen in range(1, 7):
            freres = []
            for k in range(8):
                p = PlantInstance(plant_class=cls, position=(2 + k % 3, 2 + k // 3))
                p.genes, p.F = heredite(mere, pere, SEED, 100 * gen + k)
                freres.append(p)
            F = st.mean(p.F for p in freres)
            v_h = st.pvariance([p.gene("hauteur") for p in freres])
            v_p = st.pvariance([p.gene("phenologie_florale") for p in freres])
            print(f"  gén {gen} : F moyen {F:.3f}  var hauteur {v_h:.5f}  "
                  f"var phéno {v_p:.3f} sem²")
            mere, pere = freres[0], freres[1]


if __name__ == "__main__":
    quoi = sys.argv[1] if len(sys.argv) > 1 else "tout"
    if quoi == "_a":
        scenario_a(float(sys.argv[2]), float(sys.argv[3]))
    elif quoi in ("a", "tout"):
        for t, g in (TEMOIN, FROID):      # un sous-processus par climat (caches propres)
            subprocess.run([sys.executable, __file__, "_a", str(t), str(g)], check=True)
    if quoi in ("b", "tout"):
        scenario_b()
