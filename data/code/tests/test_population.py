"""
SYMBIOSE — tests/test_population.py
Filet de non-régression pour la vie macroscopique (D31.1).

Deux garanties :
  1. GOLDEN DE CHAMP — les densités des champs de population (puceron/limace/
     doryphore/auxiliaire/pollinisateurs/vers_de_terre) sont DÉTERMINISTES et
     reproductibles sur N semaines (hash sha256 contre `population_hash.txt`).
  2. BORNES & PERCEPTION — densité ∈ [0, POP_MAX] partout ; `sample_sprites`
     respecte le cap par plot ; les positions de sprites sont INDÉPENDANTES de
     la semaine (pure fonction de seed/position/slot).

Lancement (depuis data/code/) :
  python3 -m tests.test_population            # vérifie contre population_hash.txt
  python3 -m tests.test_population --capture  # (re)capture le hash de référence
"""

import sys
import os
import hashlib

from world import Tile
from plants import Tomato, Basil, Sunflower, Bean, Yarrow, Phacelia
from fields import (init_eco, POP_MAX, SPRITES_PAR_PLOT_MAX,
                    sample_sprites, PopulationField, build_population_specs,
                    daylength)
from sim.engine import Engine

N_WEEKS = 60
SEED = 0x5AB1057E
HASH_FILE = os.path.join(os.path.dirname(__file__), "population_hash.txt")
GUILDS = ("puceron", "limace", "doryphore",
          "coccinelle", "chrysope", "carabe", "merle", "herisson",
          "abeille", "syrphe", "papillon", "vers_de_terre")


def build_world():
    """Petit monde déterministe : 2 tuiles, jardin diversifié + attire-auxiliaires."""
    tiles, ecos = [], {}
    for i, soil in enumerate(["terre", "argile"]):
        tid = f"T{i}"
        tile = Tile(tile_id=tid, soil_type=soil)
        eco = init_eco(tid, 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3)
        tile.add_plant(Tomato,    2, 2)
        tile.add_plant(Basil,     2, 4)
        tile.add_plant(Bean,      4, 2)
        tile.add_plant(Sunflower, 0, 1)
        if i % 2 == 0:
            tile.add_plant(Yarrow,   3, 5)
            tile.add_plant(Phacelia, 1, 6)
        tiles.append(tile)
        ecos[tid] = eco
    return tiles, ecos


def _run(tiles, ecos):
    gs = {"tiles": tiles, "eco": ecos, "scores": {},
          "current_player": "joueur_1", "week": 1, "log": [], "seed": SEED}
    engine = Engine(gs)
    for _ in range(N_WEEKS):
        engine.tick_semaine()
        gs["log"].clear()
    return tiles, ecos


def population_digest(tiles, ecos) -> str:
    """Empreinte exacte des densités de tous les champs (round 6 → round-trip)."""
    lines = []
    for tile in tiles:
        eco = ecos[tile.tile_id]
        for g in GUILDS:
            f = eco.populations[g]
            lines.append(f"{tile.tile_id}/{g}")
            for r in range(f.rows):
                lines.append(" ".join(f"{f.at_plot(r, c):.6f}"
                                      for c in range(f.cols)))
    return "\n".join(lines)


def compute_hash() -> str:
    tiles, ecos = _run(*build_world())
    h = hashlib.sha256()
    h.update(population_digest(tiles, ecos).encode("utf-8"))
    return h.hexdigest()


# ---------------------------------------------------------------------------
# 3. SAISONNALITÉ (CONCEPTION_SAISONNALITE_VIE_MACRO.md §6)
# ---------------------------------------------------------------------------
# Ces tests PROUVENT le comportement saisonnier indépendamment du hash golden :
# dormance hivernale franche (plus de « vie qui grouille en hiver »), réveil
# saisonnier, fenêtre par guilde, et robustesse au redoux (la photopériode ne
# lit pas la température).

def _mean_density(ecos, guild) -> float:
    """Densité moyenne d'une guilde sur tous les plots de toutes les tuiles."""
    tot = n = 0
    for eco in ecos.values():
        f = eco.populations[guild]
        for r in range(f.rows):
            for c in range(f.cols):
                tot += f.at_plot(r, c); n += 1
    return tot / n if n else 0.0


def _run_trace(n_weeks=110):
    """Simule n_weeks et renvoie {guilde: (pic_annuel, max_hiver_profond)}.
    Hiver profond = wiy 44-49 (porte photopériodique fermée pour les guildes
    estivales)."""
    tiles, ecos = build_world()
    gs = {"tiles": tiles, "eco": ecos, "scores": {},
          "current_player": "joueur_1", "week": 1, "log": [], "seed": SEED}
    engine = Engine(gs)
    peak = {g: 0.0 for g in GUILDS}
    hiver = {g: [] for g in GUILDS}
    for _ in range(n_weeks):
        engine.tick_semaine()
        gs["log"].clear()
        wiy = ((gs["week"] - 2) % 52) + 1   # semaine qui vient d'être simulée
        for g in GUILDS:
            m = _mean_density(ecos, g)
            peak[g] = max(peak[g], m)
            if 44 <= wiy <= 49:
                hiver[g].append(m)
    return {g: (peak[g], max(hiver[g])) for g in GUILDS}


def test_saisonnalite_dormance_reveil():
    """Les guildes PHOTOSENSIBLES (puceron/coccinelle/abeille) décollent en
    saison et S'ÉTEIGNENT en plein hiver (dormance, plus de traîne). La coccinelle
    (auxiliaire, scindée ④c) suit le puceron, sa proie. L'abeille représente les
    pollinisateurs : sa ressource = nectar (floraison × attractivite, ②) — elle ne
    décolle que si le jardin fleurit pour de vrai."""
    res = _run_trace()
    for g in ("puceron", "coccinelle", "abeille"):
        peak, hiv = res[g]
        assert peak > 0.05, f"{g} ne décolle jamais (pic {peak:.3f})"
        assert hiv < 0.02, f"{g} grouille encore en hiver (max {hiv:.3f})"
    print("[pop] dormance hivernale + réveil saisonnier (3 guildes) : OK")


def test_vers_insensibles_photoperiode():
    """Le ver de terre (fenêtre LARGE) garde une fraction hivernale bien plus
    grande que les guildes estivales → la fenêtre par guilde fonctionne."""
    res = _run_trace()
    peak, hiv = res["vers_de_terre"]
    assert peak > 0.05, f"vers ne décolle jamais (pic {peak:.3f})"
    assert hiv > 0.25 * peak, \
        f"vers trop éteint en hiver ({hiv:.3f} vs pic {peak:.3f}) — devrait rester actif"
    print(f"[pop] vers actifs l'hiver ({hiv:.3f} = {hiv/peak:.0%} du pic) : OK")


def test_photoperiode_verrouille_redoux():
    """Un REDOUX hivernal (température estivale en plein hiver) ne réveille PAS
    le puceron : phenology(wiy=46)=0 annule la cible quelle que soit la chaleur.
    Test signature de la valeur ajoutée (lumière ≠ température)."""
    assert daylength(46) < 9.0 < daylength(30), "photopériode hiver/été incohérente"

    def _tick_warm(wiy):
        eco = init_eco("R", 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3)
        rav = eco.populations["puceron"]
        rav.fill(0.5)
        eco.temperature.fill(20.0)   # redoux : chaud comme en été
        eco.tick_populations(Tile(tile_id="R", soil_type="terre"), [], week_in_year=wiy)
        return rav.at_plot(3, 4)

    hiver = _tick_warm(46)
    ete   = _tick_warm(25)
    assert hiver < 0.5, "le puceron ne devrait pas se maintenir au redoux hivernal"
    assert ete > hiver, "à chaleur égale, l'été doit préserver mieux que l'hiver"
    print(f"[pop] photopériode verrouille le redoux (hiver {hiver:.3f} < été {ete:.3f}) : OK")


# ---------------------------------------------------------------------------
# 2. BORNES & PERCEPTION
# ---------------------------------------------------------------------------

def test_bornes_densite():
    """Toute densité reste dans [0, POP_MAX] après une simulation."""
    tiles, ecos = _run(*build_world())
    for tile in tiles:
        for g in GUILDS:
            f = ecos[tile.tile_id].populations[g]
            for r in range(f.rows):
                for c in range(f.cols):
                    d = f.at_plot(r, c)
                    assert 0.0 <= d <= POP_MAX, f"{g}@{r},{c} densité {d} hors bornes"
    print("[pop] bornes densité ∈ [0, POP_MAX] : OK")


def test_cap_sprites():
    """sample_sprites ne dépasse jamais le cap par plot, même à densité saturée."""
    spec = build_population_specs()[0]
    f = PopulationField(spec, 6, 8)
    f.fill(POP_MAX)   # densité maximale partout → cap doit s'appliquer
    sprites = sample_sprites(f, SEED)
    per_plot = {}
    for s in sprites:
        per_plot[(s.row, s.col)] = per_plot.get((s.row, s.col), 0) + 1
    assert per_plot, "aucun sprite à densité max"
    assert max(per_plot.values()) <= SPRITES_PAR_PLOT_MAX, "cap par plot dépassé"
    # densité nulle → aucun sprite
    f.fill(0.0)
    assert sample_sprites(f, SEED) == [], "densité nulle devrait donner 0 sprite"
    print(f"[pop] cap sprites ≤ {SPRITES_PAR_PLOT_MAX}/plot : OK")


def test_positions_independantes_semaine():
    """
    Les positions de sprites ne dépendent QUE de seed/position/slot — donc deux
    échantillonnages du MÊME état de champ sont identiques, et un slot occupe
    toujours le même point quelle que soit la densité (tant qu'il reste visible).
    """
    spec = build_population_specs()[0]
    f = PopulationField(spec, 6, 8)
    f.fill(POP_MAX)
    a = sample_sprites(f, SEED)
    b = sample_sprites(f, SEED)
    assert [(s.row, s.col, s.slot, s.x_frac, s.y_frac) for s in a] == \
           [(s.row, s.col, s.slot, s.x_frac, s.y_frac) for s in b], \
           "échantillonnage non reproductible"
    # Le slot 0 d'un plot donné occupe le même point à densité faible ou forte.
    pos_haute = {(s.row, s.col, s.slot): (s.x_frac, s.y_frac) for s in a}
    f.fill(0.30)   # densité plus faible → moins de slots, mais positions stables
    for s in sample_sprites(f, SEED):
        assert pos_haute[(s.row, s.col, s.slot)] == (s.x_frac, s.y_frac), \
            "un slot a bougé quand la densité a changé (téléportation interdite)"
    print("[pop] positions indépendantes de la semaine : OK")


def test_determinisme_golden():
    """Le hash des densités doit être stable (deux runs identiques)."""
    h1 = compute_hash()
    h2 = compute_hash()
    assert h1 == h2, "densités non déterministes entre deux runs !"
    capture = "--capture" in sys.argv
    if capture or not os.path.exists(HASH_FILE):
        with open(HASH_FILE, "w") as f:
            f.write(h1 + "\n")
        print(f"[pop] hash de référence capturé : {h1}")
        return
    with open(HASH_FILE) as f:
        ref = f.read().strip()
    assert h1 == ref, f"divergence !\n  attendu : {ref}\n  obtenu  : {h1}"
    print(f"[pop] golden de champ — hash identique : {h1}")


def main():
    test_saisonnalite_dormance_reveil()
    test_vers_insensibles_photoperiode()
    test_photoperiode_verrouille_redoux()
    test_bornes_densite()
    test_cap_sprites()
    test_positions_independantes_semaine()
    test_determinisme_golden()
    print("[pop] TOUS LES TESTS PASSENT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
