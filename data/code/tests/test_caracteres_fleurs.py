"""
SYMBIOSE — tests/test_caracteres_fleurs.py
Test ciblé du D139 caractères vivants ① — LA FLEUR et le COÛT GÉNÉTIQUE.

Ce que le golden re-figé ne prouve pas (il constate seulement une dérive), ce test
le garde :
  1. `poids_floral` (nourriture d'une plante pour un butineur) croît avec `nectar`,
     `taille_fleur`, `guide_nectar`, `parfum` ; `pollen` sert la voie vibrée ;
  2. la préférence de couleur est maximale sur la teinte préférée du butineur, et
     vaut 1 pour une espèce sans axe ou un butineur aveugle ;
  3. `cout_genetique` baisse avec un excès coûteux, ne paie rien sous le neutre,
     ne passe jamais sous le plancher, et inclut le coût thermique rapatrié ;
  4. le parfum réduit la pression des ravageurs (facteur borné) ;
  5. le pollen multiplie la dose anémophile.

Lancement (depuis data/code/) : python3 -m tests.test_caracteres_fleurs
"""

import sys

from plants import PlantInstance, Borage, Phacelia, Tomato, Clover, Nettle
from plants.genetics import DEFENSE_PLANCHER, K_THERMO
from plants.couleurs import (preferences, preference_couleur, couleur_sur_axe,
                             PREF_MAX, PREF_MIN, BLEU, ROSE)
from world import Tile
from fields import init_eco
from fields.population import poids_floral, build_pollinator_registry
from sim.effects.herbivorie import facteur_gout   # D140 G ③ : herbivorie par atteinte

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'✅' if cond else '❌'} {name}" + (f" — {detail}" if detail else ""))


def _fleur(cls, **genes):
    p = PlantInstance(plant_class=cls, position=(0, 0))
    p.genes = dict(genes)
    p.floraison = 1.0
    return p


_REG = {ps.name: ps for ps in build_pollinator_registry()}


def _w(p, type_):
    ps = _REG[type_]
    return poids_floral(p, ps.attractivite, ps.attractivite_defaut,
                        ps.pollen_vibre, ps.pref_couleur)


def test_poids_floral_croit():
    print("\n[1] poids_floral croît avec chaque caractère floral")
    base = _w(_fleur(Phacelia), "abeille")
    check("phacélie neutre nourrit l'abeille", base > 0.0, f"{base:.3f}")
    for g in ("nectar", "taille_fleur", "guide_nectar", "parfum"):
        haut = _w(_fleur(Phacelia, **{g: 1.3}), "abeille")
        bas = _w(_fleur(Phacelia, **{g: 0.7}), "abeille")
        check(f"{g} : 0,7 < neutre < 1,3", bas < base < haut,
              f"{bas:.3f} < {base:.3f} < {haut:.3f}")
    t0 = _w(_fleur(Tomato), "bourdon")
    t1 = _w(_fleur(Tomato, pollen=1.3), "bourdon")
    check("pollen : la tomate nourrit plus le bourdon (voie vibrée)", t1 > t0 > 0.0,
          f"{t0:.3f} → {t1:.3f}")
    check("pollen n'ouvre pas la tomate à l'abeille",
          _w(_fleur(Tomato, pollen=1.6), "abeille") == 0.0)


def test_preference_couleur():
    print("\n[2] préférence de couleur")
    pref = preferences((BLEU,), 0.35)
    axe = (BLEU, ROSE)
    bleue = preference_couleur(axe, -1.0, pref)
    rose = preference_couleur(axe, 1.0, pref)
    check("maximale sur la teinte préférée", abs(bleue - PREF_MAX) < 1e-12, f"{bleue:.3f}")
    check("plus faible loin d'elle", PREF_MIN <= rose < bleue, f"{rose:.3f}")
    check("espèce sans axe → 1", preference_couleur(None, 0.5, pref) == 1.0)
    check("butineur aveugle → 1", preference_couleur(axe, 0.5, None) == 1.0)
    h, s = couleur_sur_axe(axe, -1.0)
    check("couleur_sur_axe(−1) = première teinte", abs(h - 225.0) < 1e-9 and abs(s - 1.0) < 1e-9)
    # La bourrache (bleu → rose) : l'abeille préfère la bleue, le papillon la rose.
    ab = (_w(_fleur(Borage, couleur_fleur=-0.8), "abeille"),
          _w(_fleur(Borage, couleur_fleur=0.8), "abeille"))
    pa = (_w(_fleur(Borage, couleur_fleur=-0.8), "papillon"),
          _w(_fleur(Borage, couleur_fleur=0.8), "papillon"))
    check("bourrache bleue : l'abeille la préfère", ab[0] > ab[1], f"{ab[0]:.3f} > {ab[1]:.3f}")
    check("bourrache rose : le papillon la préfère", pa[1] > pa[0], f"{pa[1]:.3f} > {pa[0]:.3f}")


def test_cout_genetique():
    print("\n[3] cout_genetique")
    p = _fleur(Phacelia)
    check("neutre → 1", p.cout_genetique() == 1.0)
    p.genes = {"nectar": 1.15}
    un = p.cout_genetique()
    check("+1 σ de nectar coûte ≈ 3 %", abs(un - 0.97) < 1e-9, f"{un:.4f}")
    p.genes = {"nectar": 1.3, "parfum": 1.3}
    check("deux excès coûtent plus qu'un", p.cout_genetique() < un)
    p.genes = {"nectar": 0.7, "taille_fleur": 0.6}
    check("sous le neutre : rien gagné, rien payé", p.cout_genetique() == 1.0)
    p.genes = {"couleur_fleur": 1.0}
    check("la couleur est gratuite", p.cout_genetique() == 1.0)
    p.genes = {g: 1.6 for g in ("taille_fleur", "nectar", "pollen", "guide_nectar", "parfum")}
    p.genes.update(rusticite_froid=6.0, limite_froid=4.0, limite_chaud=6.0)
    check("jamais sous le plancher", p.cout_genetique() >= DEFENSE_PLANCHER,
          f"{p.cout_genetique():.3f}")
    p.genes = {"limite_chaud": 1.0}
    check("coût thermique rapatrié : 1 °C = K_THERMO",
          abs(p.cout_genetique() - (1.0 - K_THERMO)) < 1e-12)


def test_parfum_ravageurs():
    print("\n[4] le parfum repousse une part des ravageurs")
    tile = Tile(tile_id="PF", soil_type="terre", grid_rows=4, grid_cols=4)
    eco = init_eco("PF", 4, 4, humidite=1.5, fertilite=1.0, microbiome=0.3,
                   soil_type="terre")
    eco.category_density = lambda cat, r, c: 0.5 if cat == "ravageur" else 0.0

    def pression(parfum):
        p = tile.add_plant(Clover, 1, 1)
        p.genes = {"parfum": parfum}
        return facteur_gout(p)   # facteur plante de la perte (D140 G ③)
    neutre, fort, faible = pression(1.0), pression(1.6), pression(0.4)
    check("parfum fort : moins de pression", fort < neutre, f"{fort:.3f} < {neutre:.3f}")
    check("parfum faible : plus de pression", faible > neutre, f"{faible:.3f}")
    check("facteur borné à ±30 %", abs(fort / neutre - 0.7) < 0.02, f"{fort / neutre:.3f}")


def test_pollen_anemophile():
    print("\n[5] le pollen multiplie la dose anémophile")
    from sim.engine.anemophilie import AnemophilieMixin

    class _Vent:
        def at_plot(self, r, c):
            return 0.8

    def dose(pollen_src):
        tile = Tile(tile_id="AN", soil_type="terre", grid_rows=4, grid_cols=4)
        src, cible = tile.add_plant(Nettle, 1, 1), tile.add_plant(Nettle, 1, 2)
        src.genes, cible.genes = {"pollen": pollen_src}, {}
        src.floraison = cible.floraison = 1.0
        eco = type("E", (), {"vent": _Vent()})()
        # Vent soufflant de la source vers la cible : quelle que soit la convention
        # d'angle, l'une des quatre directions la place au vent → dose maximale.
        doses = []
        for d in (0.0, 90.0, 180.0, 270.0):
            cible.pollen_recu = 0.0
            AnemophilieMixin._tick_anemophilie(None, tile, eco, d, 1.0)
            doses.append(cible.pollen_recu)
        return max(doses)
    check("ortie riche en pollen : la voisine en reçoit plus", dose(1.4) > dose(1.0) > 0.0,
          f"{dose(1.0):.3f} → {dose(1.4):.3f}")


def main():
    test_poids_floral_croit()
    test_preference_couleur()
    test_cout_genetique()
    test_parfum_ravageurs()
    test_pollen_anemophile()
    print("\n" + "=" * 60)
    ok = sum(1 for _, c in _results if c)
    print(f"caractères vivants ① — fleurs : {ok}/{len(_results)} OK")
    return 0 if ok == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
