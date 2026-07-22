"""
SYMBIOSE — tests/test_competition.py
Tests ciblés du sprint COMPÉTITION INTRA-PLOT (conception FIGÉE Q1-Q11,
docs/vegetal/catalogue/conception_competition_intraplot.md). Lancé à la demande (hors smoke
test). Couvre les MÉCANISMES, par assertion de comportement déterministe — pas
de hash global.

Mécanismes exercés :
  1. Tolérance à l'ombre par strate (`shade_tolerance_base`) + override explicite.
  2. Étiolement (`est_etiole`) : héliophile ombragé file, sciaphile/plein soleil non.
  3. Étiolement OBSERVABLE : un héliophile à l'ombre s'allonge plus vite (vitesse ×1.3).
  4. Escompte de niche à la germination (Q6) : sous faible lumière, un héliophile
     lève sur MOINS de plots qu'un sciaphile — « ne lève pas sous canopée ».
  5. Co-occupation intra-plot (verrou levé, §2.4) : une germination spontanée
     s'installe sur un plot DÉJÀ occupé (deux plantes partagent le plot).

Le verrou d'occupation a été LEVÉ (tronçon 1) : la cohabitation est arbitrée par
les champs réels (lumière, eau, racines), pas par un verrou artificiel.

Lancement (depuis data/code/) :
  python3 -m tests.test_competition
"""
import sys

from world import Tile
from plants import Tomato, BursaPastoris, AppleTree, GrowthStage, PlantBase, PlantInstance
from fields import init_eco, LightField, SeedBank, SEED_ARCHETYPES
from sim.growth import est_etiole, grow_plant, ETIOLEMENT_LIGHT_SEUIL
from sim.succession import succession

SEED = 0x5EED
_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK " if cond else "XX "
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _apex_height(plant) -> float:
    """Flèche la plus haute = max des z d'extrémité de segment (cm)."""
    h = 0.0
    for s in plant.segments:
        bx, by, bz = s.base
        ex = bx + s.dir[0] * s.length_cm
        ey = by + s.dir[1] * s.length_cm
        ez = bz + s.dir[2] * s.length_cm
        h = max(h, ez)
    return h


# ---------------------------------------------------------------------------
# 1. Tolérance à l'ombre par strate + override explicite
# ---------------------------------------------------------------------------
def test_shade_tolerance_base():
    print("\n[1] tolérance à l'ombre : dérivée de la strate + override explicite")

    def cls_strate(strate, override=None):
        class _T(PlantBase):
            shade_tolerance = override
            growth_stages = [GrowthStage(name="s", duration_weeks=1, strate=strate)]
        return _T

    check("strate sol → sciaphile 1.25", cls_strate("sol").shade_tolerance_base() == 1.25)
    check("strate basse → sciaphile 1.25", cls_strate("basse").shade_tolerance_base() == 1.25)
    check("strate moyenne → neutre 1.0", cls_strate("moyenne").shade_tolerance_base() == 1.0)
    check("strate haute → héliophile 0.90", cls_strate("haute").shade_tolerance_base() == 0.90)
    check("override explicite l'emporte sur la strate",
          cls_strate("sol", override=0.5).shade_tolerance_base() == 0.5)
    # Espèces réelles : le pommier (strate haute) est héliophile, < 1.
    check("pommier (haute) héliophile < 1", AppleTree.shade_tolerance_base() < 1.0,
          f"={AppleTree.shade_tolerance_base()}")


# ---------------------------------------------------------------------------
# 2. est_etiole : héliophile ombragé file, sciaphile / plein soleil non
# ---------------------------------------------------------------------------
def test_est_etiole():
    print("\n[2] est_etiole : héliophile ombragé OUI, sciaphile / plein soleil NON")
    lf = LightField(4, 4)   # grille uniforme 1.0 → pas de gradient (pas de phototropisme)

    helio_sun = PlantInstance(plant_class=AppleTree, position=(1, 1))     # haute → tol 0.9
    helio_shade = PlantInstance(plant_class=AppleTree, position=(2, 2))
    scia_shade = PlantInstance(plant_class=BursaPastoris, position=(3, 3))  # basse → tol 1.25

    lf.received[id(helio_sun)] = 1.0
    lf.received[id(helio_shade)] = 0.15    # 0.15 × 0.9 = 0.135 < seuil 0.40
    lf.received[id(scia_shade)] = 0.05     # sciaphile : ne file jamais

    check("héliophile en plein soleil ne file pas", est_etiole(helio_sun, lf) is False)
    check("héliophile à l'ombre file", est_etiole(helio_shade, lf) is True)
    check("sciaphile à l'ombre profonde ne file pas (tol ≥ 1)",
          est_etiole(scia_shade, lf) is False)
    check("light_field None → jamais d'étiolement",
          est_etiole(helio_shade, None) is False)


# ---------------------------------------------------------------------------
# 3. Étiolement OBSERVABLE : l'ombragé s'allonge plus vite
# ---------------------------------------------------------------------------
def test_etiolement_observable():
    print("\n[3] étiolement observable : l'héliophile ombragé pousse plus haut")
    lf = LightField(4, 4)   # uniforme → phototropisme neutre, seul l'étiolement joue

    sun = PlantInstance(plant_class=AppleTree, position=(1, 1))
    shade = PlantInstance(plant_class=AppleTree, position=(1, 1))
    lf.received[id(sun)] = 1.0
    lf.received[id(shade)] = 0.15

    # Mêmes ticks pour les deux : seule la lumière reçue (donc l'étiolement) diffère.
    for w in range(18, 34):     # quelques semaines d'été, hors plafond de gabarit
        grow_plant(sun, SEED, w, lf)
        grow_plant(shade, SEED, w, lf)

    hs, hh = _apex_height(sun), _apex_height(shade)
    check("l'ombragé (étiolé) est plus haut que le plein-soleil", hh > hs,
          f"ombre={hh:.2f}cm soleil={hs:.2f}cm")


# ---------------------------------------------------------------------------
# 4. Escompte de niche à la germination — héliophile lève sur MOINS de plots
# ---------------------------------------------------------------------------
def test_germination_discount_canopee():
    print("\n[4] germination sous canopée : héliophile lève sur MOINS de plots qu'un sciaphile")
    rows = cols = 8
    light = 0.30                # faible lumière = sous canopée
    niche = 0.9

    def compte(tol):
        sb = SeedBank(rows, cols)
        for r in range(rows):
            for c in range(cols):
                sb.add(r, c, "pioneer", 1.0)    # densité de graines saturée
        n = 0
        for r in range(rows):
            for c in range(cols):
                cands = sb.germination_candidates(
                    r, c, SEED, 5, niche, light=light,
                    arch_tolerance={"pioneer": tol})
                if "pioneer" in cands:
                    n += 1
        return n

    n_helio = compte(0.5)       # héliophile : voit moins de lumière qu'il n'y en a
    n_scia = compte(1.25)       # sciaphile : voit plus de lumière qu'il n'y en a
    check("le sciaphile lève sur plus de plots que l'héliophile", n_scia > n_helio,
          f"sciaphile={n_scia} héliophile={n_helio} / {rows*cols}")
    check("l'héliophile est franchement freiné sous canopée", n_helio < n_scia,
          f"héliophile={n_helio}")


# ---------------------------------------------------------------------------
# 5. Co-occupation intra-plot : germination spontanée sur plot occupé
# ---------------------------------------------------------------------------
def test_co_occupation_succession():
    print("\n[5] co-occupation : une germination spontanée s'installe sur un plot occupé")
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = init_eco("T0", 6, 6, humidite=1.5, fertilite=0.5, microbiome=0.3)
    eco.lumiere.fill(1.0)
    eco.disturbance.fill(1.0)
    eco.soil_memory_deep.fill(0.0)
    # Banque-sol VIDE partout SAUF au plot occupé : toute germination spontanée
    # ne PEUT survenir que là → si elle survient, elle se co-localise (verrou levé).
    # (Les voisins restent libres → root_density nulle → niche élevée au plot ciblé.)
    for r in range(6):
        for c in range(6):
            for a in SEED_ARCHETYPES:
                eco.seed_bank.data[r][c][a] = 0.0
    for a in SEED_ARCHETYPES:
        eco.seed_bank.add(3, 3, a, 1.0)

    tile.add_plant(BursaPastoris, 3, 3)        # occupant unique, racines menues

    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {},
          "current_player": "joueur_1", "week": 5, "log": [], "seed": SEED}

    co_occupe = False
    for w in range(5, 60):
        gs["week"] = w
        succession(gs, tile, eco, w)
        n_33 = sum(1 for p in tile.plants if p.is_alive and p.position == (3, 3))
        if n_33 >= 2:
            co_occupe = True
            break
    check("une germination s'est installée sur un plot déjà occupé (verrou levé)",
          co_occupe)


def main():
    test_shade_tolerance_base()
    test_est_etiole()
    test_etiolement_observable()
    test_germination_discount_canopee()
    test_co_occupation_succession()
    n_ok = sum(1 for _, ok in _results if ok)
    n = len(_results)
    print(f"\n[test_competition] {n_ok}/{n} OK")
    if n_ok != n:
        echecs = [name for name, ok in _results if not ok]
        print("ÉCHECS : " + ", ".join(echecs))
        sys.exit(1)
    print("[test_competition] PASS")


if __name__ == "__main__":
    main()
