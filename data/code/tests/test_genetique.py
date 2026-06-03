"""
SYMBIOSE — test_genetique.py
Tests du moteur de génétique des populations (Sprint génétique, D17 + D22).

Cinq vérifications, toutes DÉTERMINISTES (aucun RNG live) :
  1. genetic_factor branché : la hauteur effective varie avec le gène `hauteur`.
  2. Sélection émergente : sélectionner les plus hauts sur N générations fait
     monter la moyenne `hauteur` de la lignée.
  3. Brassage par pollinisation : la présence d'auxiliaires/pollinisateurs élargit
     le rayon de croisement → outcrossing (gènes du père) au lieu d'autofécondation.
  4. Introgression intra-famille : père d'une autre espèce de la même famille
     décale les gènes ; croisement inter-familles interdit.
  5. Intégration moteur : banque-sol génétique + pont récolte → banque-joueur,
     sur une vraie tuile, sans crash.

Usage (depuis data/code/) : python3 -m tests.test_genetique
"""
import math

from plants import (PlantInstance, Tomato, Pepper, Bean, species_compatible,
                    GENE_NAMES)
from fields import SeedBank, GeneStat, hash_gauss
from sim.reproduction import (find_father, child_genes, is_seed_bearing,
                              pollinator_reach)
from sim.seeds import Seed, PlayerSeedBank

SEED = 0x5AB1057E
_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _tomato(h=1.0, pos=(0, 0)):
    return PlantInstance(Tomato, pos, current_stage=3, genes={"hauteur": h})


# ---------------------------------------------------------------------------
# 1. genetic_factor branché dans la hauteur
# ---------------------------------------------------------------------------

def test_genetic_factor():
    print("\n[1] genetic_factor branché dans current_height")
    neutre = _tomato(1.0)
    grand  = _tomato(1.3)
    petit  = _tomato(0.7)
    neutre.growth_factor = grand.growth_factor = petit.growth_factor = 1.0
    ratio_grand = grand.current_height / neutre.current_height
    ratio_petit = petit.current_height / neutre.current_height
    check("hauteur ∝ gène (×1.3)", abs(ratio_grand - 1.3) < 1e-6,
          f"ratio={ratio_grand:.3f}")
    check("hauteur ∝ gène (×0.7)", abs(ratio_petit - 0.7) < 1e-6,
          f"ratio={ratio_petit:.3f}")
    check("vecteur vide ⇒ neutre 1.0",
          PlantInstance(Tomato, (0, 0)).gene("hauteur") == 1.0)


# ---------------------------------------------------------------------------
# 2. Sélection émergente (lignée qui dérive vers le haut)
# ---------------------------------------------------------------------------

def _next_gen(parents, gen, select_top):
    """Chaque parent s'autoféconde une fois ; on garde les plus hauts."""
    kids = []
    for i, p in enumerate(parents):
        p.position = (gen, i)
        g = child_genes(p, None, SEED, gen + 1)
        kids.append(_tomato(g["hauteur"], pos=(gen, i)))
    kids.sort(key=lambda x: x.gene("hauteur"), reverse=True)
    keep = kids[:select_top] if select_top else kids
    # Repeuple à taille constante par auto-fécondation supplémentaire des gardés.
    extra = []
    for i, p in enumerate(keep):
        p.position = (gen, 100 + i)
        g = child_genes(p, None, SEED, gen + 1)
        extra.append(_tomato(g["hauteur"], pos=(gen, 100 + i)))
    return (keep + extra)[:len(parents)]


def _mean_h(pop):
    return sum(p.gene("hauteur") for p in pop) / len(pop)


def test_selection_emergente():
    print("\n[2] Sélection émergente — récolter les plus hauts → lignée monte")
    N, GENS = 16, 14
    # Lignée SÉLECTIONNÉE (garder le top 1/3)
    sel = [_tomato(1.0) for _ in range(N)]
    start = _mean_h(sel)
    for gen in range(GENS):
        sel = _next_gen(sel, gen, select_top=N // 3)
    end_sel = _mean_h(sel)

    # Lignée NEUTRE (aucune sélection) — dérive faible, reste proche de 1.0
    neu = [_tomato(1.0) for _ in range(N)]
    for gen in range(GENS):
        neu = _next_gen(neu, gen + 500, select_top=0)
    end_neu = _mean_h(neu)

    check("lignée sélectionnée monte nettement", end_sel > start + 0.10,
          f"{start:.3f} → {end_sel:.3f}")
    check("lignée non sélectionnée reste proche de 1.0", abs(end_neu - 1.0) < 0.05,
          f"{end_neu:.3f}")
    check("sélection > dérive neutre", end_sel > end_neu + 0.08,
          f"sel={end_sel:.3f} vs neu={end_neu:.3f}")


# ---------------------------------------------------------------------------
# 3. Brassage par pollinisation (auxiliaires → outcrossing)
# ---------------------------------------------------------------------------

class _FakeTile:
    """Tuile minimale : seules les rondelles comptent pour la pollinisation."""
    def __init__(self, pollinisateur=0, auxiliaire=0):
        self._r = {"pollinisateur": pollinisateur, "auxiliaire": auxiliaire}

    def get_rondelle_count(self, v):
        return self._r.get(v, 0)


def test_brassage_pollinisation():
    print("\n[3] Brassage — auxiliaires élargissent le rayon de croisement")
    mere = _tomato(1.0, pos=(2, 2))
    # Père grand placé à 130 cm (hors rayon réduit ~75 cm, dans rayon nominal 150)
    pere = _tomato(1.3, pos=(2, 2))
    pere.x_cm, pere.y_cm = mere.x_cm + 130.0, mere.y_cm
    plants = [mere, pere]

    sans = _FakeTile(pollinisateur=0, auxiliaire=0)
    avec = _FakeTile(pollinisateur=3, auxiliaire=3)
    reach_sans = pollinator_reach(mere, sans)
    reach_avec = pollinator_reach(mere, avec)
    check("rayon ↑ avec auxiliaires", reach_avec > reach_sans,
          f"{reach_sans:.0f}cm → {reach_avec:.0f}cm")

    pere_sans = find_father(mere, plants, sans, SEED, 7)
    pere_avec = find_father(mere, plants, avec, SEED, 7)
    check("sans pollinisateur → autofécondation", pere_sans is None)
    check("avec pollinisateurs → père trouvé", pere_avec is pere)

    g_self  = child_genes(mere, None,      SEED, 7)["hauteur"]
    g_cross = child_genes(mere, pere_avec, SEED, 7)["hauteur"]
    check("outcrossing déplace l'enfant vers le père",
          g_cross > g_self + 0.05, f"self={g_self:.3f} cross={g_cross:.3f}")


# ---------------------------------------------------------------------------
# 4. Introgression intra-famille
# ---------------------------------------------------------------------------

def test_introgression():
    print("\n[4] Introgression — même famille décale, familles ≠ interdites")
    check("Tomate × Poivron compatibles (Solanaceae)",
          species_compatible(Tomato, Pepper))
    check("Tomate × Haricot incompatibles (familles ≠)",
          not species_compatible(Tomato, Bean))

    mere = _tomato(1.0, pos=(3, 3))
    pere_pepper = PlantInstance(Pepper, (3, 4), current_stage=2,
                                genes={"hauteur": 1.3})
    g = child_genes(mere, pere_pepper, SEED, 11)["hauteur"]
    # L'enfant reste de l'espèce mère (créé par le moteur comme Tomato) mais ses
    # gènes sont décalés vers le père d'une autre espèce.
    check("gènes décalés par le père hétérospécifique", 1.0 < g < 1.3 + 0.2,
          f"hauteur enfant={g:.3f}")


# ---------------------------------------------------------------------------
# 5. Intégration moteur — banque-sol génétique + pont récolte → joueur
# ---------------------------------------------------------------------------

def test_banque_sol_sampling():
    print("\n[5a] Banque-sol génétique — dépôt puis échantillonnage")
    sb = SeedBank(3, 3)
    # Dépose 200 graines « hautes » au plot (1,1)
    for k in range(200):
        sb.add_species(1, 1, Tomato, 0.05,
                       {"hauteur": 1.0 + 0.3 * hash_gauss(SEED, k, 1, 1)})
    stat = sb.species[1][1][Tomato]["genes"]["hauteur"]
    check("moyenne du pool ≈ 1.0", abs(stat.mean - 1.0) < 0.08,
          f"mean={stat.mean:.3f} var={stat.var:.3f}")
    check("variance du pool > 0", stat.var > 0.01, f"var={stat.var:.3f}")
    g = sb.sample_genes(1, 1, Tomato, SEED, 3)
    check("échantillon dans la plage dure", 0.4 <= g["hauteur"] <= 1.6,
          f"h={g['hauteur']:.3f}")
    check("plot vide → gènes neutres (dict vide)",
          sb.sample_genes(2, 2, Tomato, SEED, 3) == {})


def test_integration_engine():
    print("\n[5b] Intégration moteur — run 4 ans + pont récolte → banque-joueur")
    import random
    random.seed(42)
    from world import Tile
    from fields import init_eco
    from sim.engine import Engine
    from plants import AppleTree

    tile = Tile(tile_id="G0", soil_type="terre")
    eco = init_eco("G0", 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3)
    tile.add_plant(Tomato, 2, 2)
    tile.add_plant(Pepper, 2, 4)
    tile.add_plant(Bean, 4, 2)
    tile.add_plant(AppleTree, 0, 7)

    bank = PlayerSeedBank()
    gs = {"tiles": [tile], "eco": {"G0": eco}, "scores": {},
          "current_player": "j1", "week": 1, "log": [],
          "player_seed_bank": bank}
    eng = Engine(gs)
    try:
        eng.run_years(4, verbose=False)
        ran = True
    except Exception as e:  # noqa
        ran = False
        print(f"      EXCEPTION: {e}")
    check("run moteur 4 ans sans crash", ran)
    check("banque-joueur a reçu des graines (récolte)", bank.count() > 0,
          f"{bank!r}")
    # Le pool génétique du sol s'est rempli quelque part (chute des graines)
    has_pool = any(eco.seed_bank.species[r][c]
                   for r in range(6) for c in range(8))
    check("banque-sol génétique alimentée", has_pool)


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Tests génétique / reproduction (D17 + D22)")
    print("=" * 60)
    test_genetic_factor()
    test_selection_emergente()
    test_brassage_pollinisation()
    test_introgression()
    test_banque_sol_sampling()
    test_integration_engine()

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
