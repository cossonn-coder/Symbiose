"""
SYMBIOSE — tests/test_population.py
Filet de non-régression pour la vie macroscopique (D31.1).

Deux garanties :
  1. GOLDEN DE CHAMP — les densités des champs de population (puceron/limace/
     doryphore/auxiliaire/pollinisateurs/lombric/cloporte) sont DÉTERMINISTES et
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
from calendrier import W_SOLSTICE_ETE   # convention équinoxe (D122)

N_WEEKS = 60
SEED = 0x5AB1057E
HASH_FILE = os.path.join(os.path.dirname(__file__), "population_hash.txt")
GUILDS = ("puceron", "limace", "doryphore",
          "coccinelle", "chrysope", "carabe", "merle", "herisson",
          "abeille", "syrphe", "papillon", "bourdon", "osmie",
          "lombric", "cloporte", "campagnol", "rapace", "couleuvre",
          "moustique", "libellule")


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
# 3. SAISONNALITÉ (docs/faune/vie_macro/conception_saisonnalite_vie_macro.md §6)
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


def _mean_density_hote(ecos, tiles, guild) -> float:
    """Densité moyenne d'une guilde sur les seuls plots portant une plante VIVANTE.
    D122 ③ (C5bis) : le puceron n'a plus d'habitat sur sol nu (« les ravageurs
    viennent quand il y a des plantes pour les nourrir ») → sa moyenne sur TOUTE la
    tuile se dilue dans le sol nu ; son décollage se juge là où il peut vivre."""
    tot = n = 0
    for t in tiles:
        f = ecos[t.tile_id].populations[guild]
        for (r, c) in {p.position for p in t.plants if p.is_alive}:
            tot += f.at_plot(r, c); n += 1
    return tot / n if n else 0.0


def _run_trace(n_weeks=110):
    """Simule n_weeks et renvoie {guilde: (pic_annuel, max_hiver_profond,
    pic_annuel_sur_plots_plantés)}.
    Hiver profond = wiy 33-38 (jours les plus courts, porte photopériodique
    fermée pour les guildes estivales). Convention ÉQUINOXE (D122) : l'ancienne
    fenêtre 44-49 (calendrier au 1ᵉʳ janvier) décalée de −11 → même climat vu."""
    tiles, ecos = build_world()
    gs = {"tiles": tiles, "eco": ecos, "scores": {},
          "current_player": "joueur_1", "week": 1, "log": [], "seed": SEED}
    engine = Engine(gs)
    peak = {g: 0.0 for g in GUILDS}
    peak_hote = {g: 0.0 for g in GUILDS}
    hiver = {g: [] for g in GUILDS}
    for _ in range(n_weeks):
        engine.tick_semaine()
        gs["log"].clear()
        wiy = ((gs["week"] - 2) % 52) + 1   # semaine qui vient d'être simulée
        for g in GUILDS:
            m = _mean_density(ecos, g)
            peak[g] = max(peak[g], m)
            peak_hote[g] = max(peak_hote[g], _mean_density_hote(ecos, tiles, g))
            if 33 <= wiy <= 38:
                hiver[g].append(m)
    return {g: (peak[g], max(hiver[g]), peak_hote[g]) for g in GUILDS}


def test_saisonnalite_dormance_reveil():
    """Les guildes PHOTOSENSIBLES (puceron/coccinelle/abeille) décollent en
    saison et S'ÉTEIGNENT en plein hiver (dormance, plus de traîne). La coccinelle
    (auxiliaire, scindée ④c) suit le puceron, sa proie. L'abeille représente les
    pollinisateurs : sa ressource = nectar (floraison × attractivite, ②) — elle ne
    décolle que si le jardin fleurit pour de vrai."""
    res = _run_trace()
    for g in ("puceron", "coccinelle", "abeille"):
        _peak, hiv, peak = res[g]   # décollage jugé sur les plots plantés (D122 ③)
        assert peak > 0.05, f"{g} ne décolle jamais (pic {peak:.3f})"
        assert hiv < 0.02, f"{g} grouille encore en hiver (max {hiv:.3f})"
    print("[pop] dormance hivernale + réveil saisonnier (3 guildes) : OK")


def test_vers_insensibles_photoperiode():
    """Le lombric (fenêtre LARGE 8.5/10) garde une fraction hivernale bien plus
    grande que les espèces estivales → la fenêtre par espèce fonctionne."""
    res = _run_trace()
    peak, hiv, _ = res["lombric"]
    assert peak > 0.05, f"vers ne décolle jamais (pic {peak:.3f})"
    assert hiv > 0.25 * peak, \
        f"vers trop éteint en hiver ({hiv:.3f} vs pic {peak:.3f}) — devrait rester actif"
    print(f"[pop] vers actifs l'hiver ({hiv:.3f} = {hiv/peak:.0%} du pic) : OK")


def test_photoperiode_verrouille_redoux():
    """Un REDOUX hivernal (température estivale en plein hiver) ne réveille PAS
    le puceron : phenology(wiy=35)=0 annule la cible quelle que soit la chaleur.
    Test signature de la valeur ajoutée (lumière ≠ température). Semaines en
    convention ÉQUINOXE (D122 : ancien 46/30/25 − 11 → 35/19/14)."""
    assert daylength(35) < 9.0 < daylength(19), "photopériode hiver/été incohérente"

    def _tick_warm(wiy):
        eco = init_eco("R", 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3)
        rav = eco.populations["puceron"]
        rav.fill(0.5)
        eco.temperature.fill(20.0)   # redoux : chaud comme en été
        # Un HÔTE sur le plot lu (D122 ③, C5bis) : sans plante, le puceron n'a plus
        # d'habitat (sol nu → 0) et les deux saisons s'éteindraient À ÉGALITÉ — le
        # test ne distinguerait plus la photopériode. Même hôte été comme hiver.
        tile = Tile(tile_id="R", soil_type="terre")
        hote = tile.add_plant(Basil, 3, 4)
        eco.tick_populations(tile, [hote], week_in_year=wiy)
        return rav.at_plot(3, 4)

    hiver = _tick_warm(35)
    ete   = _tick_warm(W_SOLSTICE_ETE)
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


# ---------------------------------------------------------------------------
# 4. CAMPAGNOL — herbivore vertébré racinaire (sommet trophique ①)
# ---------------------------------------------------------------------------

def test_campagnol_present_et_categorie():
    """Le campagnol est un champ de population de catégorie NEUVE
    `herbivore_vertebre`, agrégée par `category_density`."""
    tiles, ecos = _run(*build_world())
    eco = ecos["T0"]
    assert "campagnol" in eco.populations, "champ campagnol absent"
    assert eco.populations["campagnol"].spec.category == "herbivore_vertebre"
    # L'agrégat de catégorie == le champ tant qu'il n'a qu'un membre.
    f = eco.populations["campagnol"]
    for r in range(f.rows):
        for c in range(f.cols):
            assert abs(eco.category_density("herbivore_vertebre", r, c)
                       - f.at_plot(r, c)) < 1e-9
    print("[pop] campagnol présent, catégorie herbivore_vertebre agrégée : OK")


def _campagnol_peak(plants_at, weeks=30):
    """Simule un petit monde peuplé de `plants_at` = [(cls, r, c), ...] et rend le pic
    de densité campagnol atteint. Sol non remué → habitat de galeries présent, mais
    c'est la RESSOURCE racinaire (bulbes/racines) qui concentre le rongeur."""
    eco = init_eco("R", 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3)
    tile = Tile(tile_id="R", soil_type="terre")
    for (cls, r, c) in plants_at:
        tile.add_plant(cls, r, c)
    gs = {"tiles": [tile], "eco": {"R": eco}, "scores": {},
          "current_player": "j", "week": 1, "log": [], "seed": SEED}
    eng = Engine(gs)
    peak = 0.0
    f = eco.populations["campagnol"]
    for _ in range(weeks):
        eng.tick_semaine(); gs["log"].clear()
        peak = max(peak, max(f.at_plot(r, c)
                             for r in range(f.rows) for c in range(f.cols)))
    return peak


def test_campagnol_ressource_racinaire():
    """La RESSOURCE du campagnol est racinaire (§2.1) : un plot RICHE en bulbes appétés
    (ail = Amaryllidaceae, préférence 1.0) porte une densité NETTEMENT plus haute qu'un
    sol nu (où seul le plancher d'habitat = galeries en sol non remué subsiste). Prouve
    que la ressource lit `root_plots`, pas le feuillage."""
    from plants import Garlic
    nu = _campagnol_peak([])
    ail = _campagnol_peak([(Garlic, r, c) for (r, c) in
                           ((2, 2), (2, 3), (3, 2), (3, 3))])
    assert ail > nu + 0.05, \
        f"les bulbes n'attirent pas le campagnol (nu {nu:.3f} vs ail {ail:.3f})"
    print(f"[pop] campagnol concentré par les racines appétées "
          f"(nu {nu:.3f} < ail {ail:.3f}) : OK")


# ---------------------------------------------------------------------------
# 5. SUPER-PRÉDATEURS — rapace + couleuvre, sommet trophique (②)
# ---------------------------------------------------------------------------

def test_super_predateurs_presents():
    """Rapace et couleuvre sont des champs de catégorie NEUVE `super_predateur`."""
    tiles, ecos = _run(*build_world())
    eco = ecos["T0"]
    for nom in ("rapace", "couleuvre"):
        assert nom in eco.populations, f"champ {nom} absent"
        assert eco.populations[nom].spec.category == "super_predateur"
    print("[pop] rapace + couleuvre présents (catégorie super_predateur) : OK")


def test_super_predateur_nul_sans_proie():
    """Sans proie, le rapace ne décolle pas : sa capacité vient ENTIÈREMENT de la
    densité de proies (`habitat_w=0`). On ticke le SEUL champ rapace (proies à ZÉRO,
    jamais reconstruites) → il reste nul, quel que soit le terrain. Prouve que le
    sommet est piloté par le bas (philo #2), pas par un habitat vide."""
    eco = init_eco("R", 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3)
    tile = Tile(tile_id="R", soil_type="terre")
    eco.temperature.fill(20.0)
    rap = eco.populations["rapace"]
    eco.populations["campagnol"].fill(0.0)
    eco.populations["merle"].fill(0.0)
    for _ in range(20):                          # on ne ticke QUE le rapace : proies figées à 0
        rap.tick(eco, tile, [], [], week_in_year=W_SOLSTICE_ETE)   # plein été (D122 : ex-25)
    m = max(rap.at_plot(r, c) for r in range(rap.rows) for c in range(rap.cols))
    assert m < 1e-6, f"rapace décolle sans proie (max {m:.4f})"
    print("[pop] rapace nul sans proie (piloté par le bas, habitat_w=0) : OK")


def test_super_predateur_monte_avec_proie():
    """Le rapace MONTE là où sa proie (campagnol) abonde. On injecte du campagnol
    frais à chaque tick (source constante) et on vérifie que le rapace s'installe."""
    eco = init_eco("R", 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3)
    tile = Tile(tile_id="R", soil_type="terre")
    eco.temperature.fill(20.0)
    camp, rap = eco.populations["campagnol"], eco.populations["rapace"]
    for _ in range(30):
        camp.fill(0.8)                       # proie maintenue abondante (source externe)
        eco.tick_populations(tile, [], week_in_year=W_SOLSTICE_ETE)   # plein été (D122 : ex-25)
    m = max(rap.at_plot(r, c) for r in range(rap.rows) for c in range(rap.cols))
    assert m > 0.05, f"rapace ne s'installe pas malgré une proie abondante (max {m:.3f})"
    print(f"[pop] rapace s'installe sur une proie abondante (max {m:.3f}) : OK")


def test_super_predateur_puits_top_down():
    """Puits TOP-DOWN (boom-bust) : à campagnol/rapace ÉGAUX, la survie du campagnol
    est RABOTÉE par la prédation → sa cible est plus basse AVEC rapace que sans. On
    compare un tick de campagnol avec et sans champ prédateur présent."""
    def _campagnol_cible(avec_rapace: bool) -> float:
        eco = init_eco("R", 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3)
        tile = Tile(tile_id="R", soil_type="terre")
        eco.temperature.fill(20.0)
        from plants import Garlic
        tile.add_plant(Garlic, 3, 3)         # ressource racinaire → cible non nulle
        eco.populations["campagnol"].fill(0.3)
        if avec_rapace:
            eco.populations["rapace"].fill(0.5)
        eco.tick_populations(tile, tile.plants, week_in_year=W_SOLSTICE_ETE)   # plein été (D122 : ex-25)
        f = eco.populations["campagnol"]
        return max(f.at_plot(r, c) for r in range(f.rows) for c in range(f.cols))

    sans = _campagnol_cible(False)
    avec = _campagnol_cible(True)
    assert avec < sans, \
        f"le rapace ne régule pas le campagnol (avec {avec:.3f} ≥ sans {sans:.3f})"
    print(f"[pop] puits top-down : campagnol raboté par le rapace "
          f"(avec {avec:.3f} < sans {sans:.3f}) : OK")


# ---------------------------------------------------------------------------
# 6. FAUNE DE MARE — moustique + libellule (hydrologie ④)
# ---------------------------------------------------------------------------

def test_faune_mare_presente_et_categorie():
    """Moustique et libellule sont des champs de population de catégorie NEUVE
    `aquatique`, greffés sur l'eau stagnante."""
    tiles, ecos = _run(*build_world())
    eco = ecos["T0"]
    for nom in ("moustique", "libellule"):
        assert nom in eco.populations, f"champ {nom} absent"
        assert eco.populations[nom].spec.category == "aquatique"
    print("[pop] moustique + libellule présents (catégorie aquatique) : OK")


_PLUVIEUX = {"Pluie prolongée", "Orage", "Grêle", "Neige"}   # apports d'eau du ciel


def test_moustique_nul_sans_flaque():
    """Sans eau de surface ni marais (repos du smoke), le moustique ne décolle
    jamais : sa ressource (`_eau_stagnante_grid`) ET son habitat (`_mare_habitat_grid`)
    sont nuls → densité nulle. Prouve que la faune de mare est bien gatée par l'eau
    stagnante (golden de population NEUTRE hors flaque).

    D122 (calendrier équinoxe) : le monde du smoke forme désormais une petite
    flaque de fin d'hiver (sol gorgé après les semaines froides 40-52) → on ne
    s'appuie plus sur « le smoke n'a jamais de flaque » : on COUPE LA PLUIE
    (événements pluvieux → temps calme, température inchangée) le temps du test,
    pour garantir l'absence d'eau stagnante."""
    import sim.engine.boucle as _boucle
    from sim.weather import CALME
    orig = _boucle.weather_state
    def _sans_pluie(seed, week, pluie_forcee=False):
        ev, t, neb = orig(seed, week, pluie_forcee)
        return (CALME if ev.kind in _PLUVIEUX else ev), t, neb
    _boucle.weather_state = _sans_pluie
    try:
        tiles, ecos = _run(*build_world())
    finally:
        _boucle.weather_state = orig
    for tile in tiles:
        f = ecos[tile.tile_id].populations["moustique"]
        m = max(f.at_plot(r, c) for r in range(f.rows) for c in range(f.cols))
        assert m < 1e-9, f"moustique décolle sans flaque (max {m:.4f})"
    print("[pop] moustique nul sans eau stagnante : OK")


def test_moustique_monte_avec_eau_surface():
    """Le moustique MONTE là où l'eau de surface stagne. On maintient une lame
    d'eau au-dessus de SEUIL_FLAQUE et on vérifie qu'il s'installe."""
    from fields.ecofields.constants import SEUIL_FLAQUE
    eco = init_eco("R", 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3)
    tile = Tile(tile_id="R", soil_type="terre")
    eco.temperature.fill(20.0)
    mous = eco.populations["moustique"]
    for _ in range(30):
        eco.eau_surface.fill(SEUIL_FLAQUE + 0.5)   # flaque maintenue (source externe)
        eco.tick_populations(tile, [], week_in_year=W_SOLSTICE_ETE)   # plein été (D122 : ex-25)
    m = max(mous.at_plot(r, c) for r in range(mous.rows) for c in range(mous.cols))
    assert m > 0.05, f"moustique ne s'installe pas malgré une flaque (max {m:.3f})"
    print(f"[pop] moustique s'installe sur l'eau stagnante (max {m:.3f}) : OK")


def test_libellule_suit_le_moustique():
    """La libellule est un PRÉDATEUR piloté par sa proie : elle ne s'installe (sur
    l'eau, son habitat) que si le moustique abonde. On injecte du moustique frais à
    chaque tick au-dessus d'une flaque et on vérifie que la libellule décolle."""
    from fields.ecofields.constants import SEUIL_FLAQUE
    eco = init_eco("R", 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3)
    tile = Tile(tile_id="R", soil_type="terre")
    eco.temperature.fill(20.0)
    mous, lib = eco.populations["moustique"], eco.populations["libellule"]
    for _ in range(30):
        eco.eau_surface.fill(SEUIL_FLAQUE + 0.5)   # flaque (habitat de la libellule)
        mous.fill(0.8)                             # proie maintenue abondante
        eco.tick_populations(tile, [], week_in_year=W_SOLSTICE_ETE)   # plein été (D122 : ex-25)
    m = max(lib.at_plot(r, c) for r in range(lib.rows) for c in range(lib.cols))
    assert m > 0.05, f"la libellule ne suit pas le moustique (max {m:.3f})"
    print(f"[pop] libellule suit le moustique (max {m:.3f}) : OK")


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
    test_campagnol_present_et_categorie()
    test_campagnol_ressource_racinaire()
    test_super_predateurs_presents()
    test_super_predateur_nul_sans_proie()
    test_super_predateur_monte_avec_proie()
    test_super_predateur_puits_top_down()
    test_faune_mare_presente_et_categorie()
    test_moustique_nul_sans_flaque()
    test_moustique_monte_avec_eau_surface()
    test_libellule_suit_le_moustique()
    test_determinisme_golden()
    print("[pop] TOUS LES TESTS PASSENT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
