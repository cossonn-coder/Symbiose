"""
Banc headless « fleurs » (D139 caractères vivants ①). Mesure, pas test : il imprime
des chiffres à consigner dans `00_etat.md`. Golden intact (rien n'est écrit sur
disque ; chaque scénario tourne dans son propre monde en mémoire).

Lancement (depuis data/code/) :
    python3 ../../sprints/vegetal/genetique/sprint_caracteres_vivants/mesures/banc_fleurs.py [a|b|tout]

(a) BOURRACHES SAUVAGES, 1 génération, 3 rondelles pollinisateur : pollen reçu
    des butineurs par la moitié la plus bleue contre la plus rose, puis moyenne de
    `couleur_fleur` dans la banque-sol contre celle des fondateurs (différentiel
    de sélection réalisé). Une sélection par l'abeille (qui préfère le bleu) ferait
    descendre la moyenne.
(b) PHACÉLIES (4 pieds, sous la saturation du champ), 2 ans, nectar génétique forcé
    à 0,7 / 1,0 / 1,3 sur TOUS les pieds : nourriture offerte à l'abeille
    (Σ poids_floral), densité moyenne d'abeilles et pollen reçu par pied.
"""

import os
import statistics as st
import sys

sys.path.insert(0, os.getcwd())

SEED = 42


def _monde(cls, n_pieds, genes_forces=None):
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
    k = 0
    for r in range(0, 8, 2):
        for c in range(0, 8, 2):
            if k >= n_pieds:
                break
            p = semer_fondateur(tile, cls, r, c, SEED, sauvage=True)
            if p is not None and genes_forces:
                p.genes.update(genes_forces)
            k += 1
    gs = {"tiles": [tile], "eco": {"B": eco}, "scores": {}, "seed": SEED,
          "current_player": "joueur_1", "week": 1, "log": [], "house": House()}
    return tile, eco, gs, Engine(gs)


def _pool(eco, nom, cls_name):
    tot = acc = 0.0
    bank = eco.seed_bank
    for r in range(bank.rows):
        for c in range(bank.cols):
            for esp, rec in bank.species[r][c].items():
                if getattr(esp, "__name__", str(esp)) != cls_name:
                    continue
                stat = rec["genes"].get(nom)
                d = rec.get("density", 0.0)
                if stat is not None and d > 0:
                    tot += d
                    acc += d * stat.mean
    return acc / tot if tot else float("nan")


def scenario_a():
    """Une génération de bourraches : visites (pollen déposé par les butineurs)
    selon la couleur, puis différentiel RÉALISÉ (banque-sol − fondateurs). La
    bourrache ne relève pas d'elle-même dans ce bac (aucune levée férale) : une
    génération suffit à lire le gradient."""
    from plants import Borage
    tile, eco, gs, eng = _monde(Borage, 16)
    pieds = [p for p in tile.plants if p.plant_class is Borage]
    vu = {id(p): 0.0 for p in pieds}
    fec = {id(p): 0.0 for p in pieds}
    # Densité DÉPOSÉE par pied (①b) : on espionne `add_species` (plot → pied).
    par_plot = {p.position: id(p) for p in pieds}
    depose = {id(p): 0.0 for p in pieds}
    orig_add = eco.seed_bank.add_species

    def _espion(r, c, cls, amount, *a, **k):
        if cls is Borage and (r, c) in par_plot:
            depose[par_plot[(r, c)]] += amount
        return orig_add(r, c, cls, amount, *a, **k)
    eco.seed_bank.add_species = _espion
    print("(a) bourraches — couleur_fleur (−1 bleu … +1 rose), 1 génération")
    for _ in range(52):
        eng.tick_semaine()
        gs["log"].clear()
        for p in pieds:
            vu[id(p)] = max(vu[id(p)], p.pollen_recu)   # dose avant la fanaison (①b : remise à 0)
            fec[id(p)] = max(fec[id(p)], p.fecondation)
    pieds.sort(key=lambda p: p.gene("couleur_fleur"))
    moitie = len(pieds) // 2
    bleues, roses = pieds[:moitie], pieds[moitie:]
    m = lambda xs: st.mean(xs) if xs else float("nan")
    print(f"  fondateurs : couleur moy. {m([p.gene('couleur_fleur') for p in pieds]):+.3f}")
    print(f"  pollen reçu : moitié bleue {m([vu[id(p)] for p in bleues]):.3f} "
          f"(couleur {m([p.gene('couleur_fleur') for p in bleues]):+.2f}) | "
          f"moitié rose {m([vu[id(p)] for p in roses]):.3f} "
          f"(couleur {m([p.gene('couleur_fleur') for p in roses]):+.2f})")
    print(f"  fécondation (①b) : moitié bleue {m([fec[id(p)] for p in bleues]):.3f} | "
          f"moitié rose {m([fec[id(p)] for p in roses]):.3f}")
    print(f"  densité déposée/pied : moitié bleue {m([depose[id(p)] for p in bleues]):.4f} | "
          f"moitié rose {m([depose[id(p)] for p in roses]):.4f}")
    print(f"  banque-sol après 1 an : couleur moy. {_pool(eco, 'couleur_fleur', 'Borage'):+.3f}"
          " (différentiel réalisé = banque − fondateurs)")


def scenario_b():
    from plants import Phacelia
    from fields.population import poids_floral, build_pollinator_registry
    ab = next(ps for ps in build_pollinator_registry() if ps.name == "abeille")
    print("(b) phacélies — nectar génétique forcé, 2 ans")
    for nectar in (0.7, 1.0, 1.3):
        tile, eco, gs, eng = _monde(Phacelia, 4, {"nectar": nectar})
        nourriture, abeilles = [], []
        pieds = [p for p in tile.plants if p.plant_class is Phacelia]
        vu = {id(p): 0.0 for p in pieds}
        for _ in range(104):
            eng.tick_semaine()
            gs["log"].clear()
            for p in pieds:
                vu[id(p)] = max(vu[id(p)], p.pollen_recu)
            w = sum(poids_floral(p, ab.attractivite, ab.attractivite_defaut,
                                 ab.pollen_vibre, ab.pref_couleur) for p in tile.plants)
            if w > 0.0:
                nourriture.append(w)
                f = eco.populations["abeille"]
                abeilles.append(st.mean(f.at_plot(r, c) for r in range(8) for c in range(8)))
        pollen = st.mean(vu.values())
        print(f"  nectar {nectar:.1f} : semaines fleuries {len(nourriture)} | "
              f"nourriture abeille moy. {st.mean(nourriture) if nourriture else 0:.3f} | "
              f"densité abeille moy. {st.mean(abeilles) if abeilles else 0:.4f} | "
              f"pollen reçu/pied {pollen:.2f}")


if __name__ == "__main__":
    quoi = sys.argv[1] if len(sys.argv) > 1 else "tout"
    if quoi in ("a", "tout"):
        scenario_a()
    if quoi in ("b", "tout"):
        scenario_b()
