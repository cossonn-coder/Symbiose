"""
SYMBIOSE — tests/test_caracteres_feuille.py
Test ciblé du D139 caractères vivants ③ — FEUILLE ET GESTES.

Ce que le golden re-figé ne prouve pas (il constate seulement une dérive), ce test
le garde, un caractère après l'autre :
  1. `coriacite_feuille` : la grêle et les ravageurs mordent moins une feuille
     coriace, et sa litière (morte ou d'abscission) se décompose plus lentement ;
  2. `repousse` : la plante repart plus vite après une coupe (squelette ET rabattu
     des herbacées) et fleurit moins (plafond de floraison) ;
  3. `aptitude_bouture` : la bouture prend selon le gène, de façon déterministe ;
  4. `dormance_graine` : un pool dormant persiste plus longtemps et lève moins ;
  5. `dominance_apicale` : forte → tige plus haute et moins de latérales.

Lancement (depuis data/code/) : python3 -m tests.test_caracteres_feuille
"""

import sys

from world import Tile
from plants import PlantInstance, Clover, Tomato
from plants.species.aromatiques import Mint
from plants.caracteres import CARACTERES
from fields import init_eco
from fields.seedbank import SeedBank
from sim import vigueur as V
from sim import actions as A
from sim.actions.bouture import bouture_prend
from sim.actions.taille_herbacee import semaines_rabattu, RABATTU_SEMAINES
from sim.effects.perturbations import herbivory_pressure
from sim.engine.mortalite import MortaliteMixin
from sim.growth import grow_plant

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'✅' if cond else '❌'} {name}" + (f" — {detail}" if detail else ""))


def _eco(tid="TF", n=6):
    return init_eco(tid, n, n, humidite=1.5, fertilite=1.0, microbiome=0.3,
                    soil_type="terre")


def test_registre():
    print("\n[0] cinq caractères en queue du registre")
    noms = list(CARACTERES)[-5:]
    check("ordre en queue", noms == ["coriacite_feuille", "repousse", "aptitude_bouture",
                                     "dormance_graine", "dominance_apicale"], str(noms))
    p = PlantInstance(plant_class=Mint, position=(0, 0))
    p.genes = {}
    check("neutres : facteurs 1,0, bouture certaine",
          all(p.gene(g) == 1.0 for g in noms), str([p.gene(g) for g in noms]))


class _Moteur(MortaliteMixin):
    def __init__(self, gs):
        self.game_state = gs


def test_coriacite():
    print("\n[1] coriacite_feuille : grêle, ravageurs, litière")
    tile = Tile(tile_id="TF", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = _eco()
    gs = {"tiles": [tile], "eco": {"TF": eco}, "log": [], "seed": 7, "week": 1}
    tendre = tile.add_plant(Clover, 1, 1)
    dure = tile.add_plant(Clover, 4, 4)
    for p, g in ((tendre, 0.7), (dure, 1.5)):
        p.genes = {"coriacite_feuille": g}
        p.current_stage = 0                         # « semis » : seul stade grêlé
    _Moteur(gs)._mediated_damage(tile, eco, 1.0, "grêle (feuillage)", cause="grele",
                                 species_base="hail_resistance_base")
    check("grêle : la feuille coriace perd moins de vitalité",
          dure.vitalite > tendre.vitalite, f"{dure.vitalite:.3f} > {tendre.vitalite:.3f}")

    eco.category_density = lambda cat, r, c: 0.5 if cat == "ravageur" else 0.0

    def pression(g):
        p = tile.add_plant(Clover, 2, 2)
        p.genes = {"coriacite_feuille": g}
        muts = herbivory_pressure(p, tile, {}, eco)
        return float(muts[0].reason.split("p=")[1]) if muts else 0.0
    v = {g: pression(g) for g in (0.6, 1.0, 1.5)}
    check("ravageurs : pression ÷ coriacité", v[1.5] < v[1.0] < v[0.6], str(v))

    eco2 = _eco("TL")
    eco2.deposer_litiere(0, 0, "feuille", 1.0)
    eco2.deposer_litiere(5, 5, "feuille", 1.0, lenteur=1.5)
    for _ in range(4):
        eco2.tick_decomposition()
    def masse(r, c):
        return sum(p.masse for p in eco2.litiere[r][c] if p.tissu == "feuille")
    check("litière coriace : décompo plus lente", masse(5, 5) > masse(0, 0),
          f"{masse(5, 5):.3f} > {masse(0, 0):.3f}")
    eco2.deposer_litiere(5, 5, "feuille", masse(5, 5), lenteur=1.0)
    lent = [p.lenteur for p in eco2.litiere[5][5] if p.tissu == "feuille"][0]
    check("fusion : lenteur moyennée par la masse", 1.0 < lent < 1.5, f"{lent:.3f}")


def test_repousse():
    print("\n[2] repousse : reprise plus vite, floraison plus basse")
    lent = PlantInstance(plant_class=Clover, position=(0, 0))
    vite = PlantInstance(plant_class=Clover, position=(0, 0))
    lent.genes, vite.genes = {"repousse": 0.8}, {"repousse": 1.4}
    check("rabattu : pied à forte repousse retrouve sa forme plus tôt",
          semaines_rabattu(vite) < RABATTU_SEMAINES < semaines_rabattu(lent),
          f"{semaines_rabattu(vite):.1f} < {RABATTU_SEMAINES} < {semaines_rabattu(lent):.1f}")

    def hauteur(g, coupe):
        p = PlantInstance(plant_class=Tomato, position=(2, 2))
        p.genes = {"repousse": g}
        if coupe:
            p.semaine_reprise = 20
        for w in range(20, 26):
            grow_plant(p, 7, w)
        return max(s.base[2] + s.dir[2] * s.length_cm for s in p.segments)
    h = {g: hauteur(g, True) for g in (0.8, 1.4)}
    check("après une coupe : la lignée à forte repousse allonge plus",
          h[1.4] > h[0.8], str({k: round(v, 1) for k, v in h.items()}))
    check("sans coupe : la repousse ne change rien",
          hauteur(0.8, False) == hauteur(1.4, False))

    from sim.engine.floraison import FloraisonMixin

    class _F(FloraisonMixin):
        week = 100
    tile = Tile(tile_id="FL", soil_type="terre", grid_rows=4, grid_cols=4)
    eco = _eco("FL", 4)
    flo = {}
    for g in (0.8, 1.0, 1.5):
        tile.plants = []
        p = tile.add_plant(Clover, 1, 1)
        p.genes = {"repousse": g}
        p.current_stage = len(Clover.growth_stages) - 1
        p.bloom_week, p.gdd_accum = 10, 1e6
        for _ in range(12):
            _F()._tick_floraison(tile, eco, 12)
        flo[g] = p.floraison
    check("floraison plafonnée à 1 ÷ repousse", abs(flo[1.5] - 1 / 1.5) < 0.01
          and flo[1.0] > 0.99 and flo[0.8] == flo[1.0],
          str({k: round(v, 3) for k, v in flo.items()}))


def _monde_bouture():
    tile = Tile(tile_id="T0", soil_type="terre")
    eco = init_eco("T0", 8, 8, humidite=1.5, fertilite=1.0, microbiome=0.5)
    mother = tile.add_plant(Mint, 2, 2)
    mother.current_stage = len(Mint.growth_stages) - 1
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {},
          "current_player": "j1", "week": 1, "log": [], "seed": 0x5AB1057E}
    V.ensure_player(gs, "j1")
    return gs, tile, eco, mother


def test_bouture():
    print("\n[3] aptitude_bouture : reprise au hash")
    gs, tile, eco, mother = _monde_bouture()
    plots = [(r, c) for r in range(8) for c in range(8)]
    taux = {}
    for g in (0.0, 0.5, 1.0):
        mother.genes = {"aptitude_bouture": g}
        taux[g] = sum(bouture_prend(mother, 42, 3, r, c) for r, c in plots) / len(plots)
    check("prend selon le gène", taux[0.0] == 0.0 and taux[1.0] == 1.0
          and 0.3 < taux[0.5] < 0.7, str(taux))
    mother.genes = {"aptitude_bouture": 0.5}
    check("déterministe", [bouture_prend(mother, 42, 3, r, c) for r, c in plots]
          == [bouture_prend(mother, 42, 3, r, c) for r, c in plots])

    mother.genes = {"aptitude_bouture": 0.0}
    n, stress = len(tile.plants), mother.stress_memory
    ok = A.bouturer(gs, "j1", mother, tile, eco, 5, 5)
    check("échec : aucun clone, mère fatiguée quand même",
          not ok and len(tile.plants) == n and mother.stress_memory > stress)
    mother.genes = {"aptitude_bouture": 1.0}
    check("aptitude 1 : le clone est posé",
          A.bouturer(gs, "j1", mother, tile, eco, 4, 4) and len(tile.plants) == n + 1)


def test_dormance():
    print("\n[4] dormance_graine : le pool dure plus, lève moins")
    sb = SeedBank(1, 2)
    for c, g in ((0, 1.0), (1, 1.5)):
        sb.add_species(0, c, Clover, 0.5, {"dormance_graine": g})
    check("levable ÷ dormance", sb.densite_levable(0, 1, Clover)
          < sb.densite_levable(0, 0, Clover) == sb.species_density(0, 0, Clover),
          f"{sb.densite_levable(0, 1, Clover):.3f} < {sb.densite_levable(0, 0, Clover):.3f}")
    for _ in range(300):
        sb.tick_species_aging()
    d0, d1 = sb.species_density(0, 0, Clover), sb.species_density(0, 1, Clover)
    check("le pool dormant persiste plus longtemps", d1 > d0, f"{d1:.3f} > {d0:.3f}")


def test_dominance():
    print("\n[5] dominance_apicale : flèche ou buisson")
    def pousser(g):
        # Tomate isolée, sans lumière : ~70 semaines de pleine saison pour que les
        # bourgeons latéraux débourrent (avant, les trois ports sont identiques).
        p = PlantInstance(plant_class=Tomato, position=(2, 2))
        p.genes = {"dominance_apicale": g}
        for w in range(1, 70):
            grow_plant(p, 7, 20 + (w % 20))
        h = max(s.base[2] + s.dir[2] * s.length_cm for s in p.segments)
        return h, p.branch_count
    (h_fort, b_fort), (h_faible, b_faible) = pousser(1.5), pousser(0.6)
    check("forte dominance → tige plus haute", h_fort > h_faible,
          f"{h_fort:.0f} > {h_faible:.0f} cm")
    check("forte dominance → moins de latérales", b_fort < b_faible,
          f"{b_fort} < {b_faible}")


def main():
    test_registre()
    test_coriacite()
    test_repousse()
    test_bouture()
    test_dormance()
    test_dominance()
    print("\n" + "=" * 60)
    ok = sum(1 for _, c in _results if c)
    print(f"caractères vivants ③ — feuille et gestes : {ok}/{len(_results)} OK")
    return 0 if ok == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
