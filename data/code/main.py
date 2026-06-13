"""
SYMBIOSE — main.py
DÉMO / banc d'essai (sprint maison, tronçon 1). N'est PLUS le golden (décision
Q4 : le golden est devenu un smoke test rapide, cf. tests/test_golden.py).

Monde 20×20 m (40×40 = 1600 plots) selon le layout 3×3 de
CONCEPTION_MAISON_OMBRE.md §2 : la MAISON occupe le centre 8×8 m, entourée de
8 tuiles jardin (les 8 orientations N/NE/E/SE/S/SO/O/NO), séparées par des
chemins en pierre de 50 cm (largeur tranchée ici = 1 plot). Les chemins ne sont
PAS des plots simulés : ce sont les espaces monde entre les tuiles (modèle le
plus sobre, kickoff §"Chemins"). La maison est posée mais INERTE : elle ne
projette encore aucune ombre (l'ombre arrive au tronçon 2).

Arithmétique du layout (2000 cm de côté, chemin P=50 cm) :
  bandes colonnes : [0,550) 11 plots | chemin | [600,1400) 16 | chemin | [1450,2000) 11
  bandes lignes   : idem → tuiles 11×11 (coins), 11×16 / 16×11 (arêtes), maison 16×16.
  origin_x_cm ↔ col (x, est-ouest) ; origin_y_cm ↔ row (y, nord-sud).

Comme avant : la moitié des tuiles reçoit des plantes compagnes ATTIRE-
AUXILIAIRES (achillée, phacélie, trèfle) → on observe le contraste de régulation
des ravageurs vs les tuiles témoins.

Depuis le sprint Intégration tranche 2 : la FABRIQUE du monde (SECTORS,
build_tile, plant_garden, build_world_full) est importable sans lancer la démo
(scénario sous `if __name__ == "__main__"`) — tools/sim_server.py la réutilise
pour `init(config="full")`, exactement comme la tranche 1 réutilisait
build_world du golden. Import, pas de copie : zéro duplication de layout.
"""

import sys
from collections import Counter
from world import Tile, House
from plants import (Tomato, Basil, Sunflower, Bean, Clover, Pepper,
                    Yarrow, Phacelia, AppleTree, PLANT_CATALOGUE)
from fields import init_eco
from sim.engine import Engine
from sim import actions as ACT, vigueur as VIG
from sim.seeds import PlayerSeedBank, Seed

# Layout 3×3 : (nom, soil, rows, cols, origin_x_cm, origin_y_cm, attire_aux).
# rows = hauteur en plots (y), cols = largeur en plots (x). Le centre (600,600,
# 16×16) est la MAISON → pas de tuile. 4 tuiles attire-aux, 4 témoins.
SECTORS = [
    ("NO", "argile", 11, 11,    0,    0, True),
    ("N",  "terre",  11, 16,  600,    0, False),
    ("NE", "sable",  11, 11, 1450,    0, True),
    ("O",  "terre",  16, 11,    0,  600, False),
    ("E",  "argile", 16, 11, 1450,  600, True),
    ("SO", "sable",  11, 11,    0, 1450, False),
    ("S",  "terre",  11, 16,  600, 1450, True),
    ("SE", "argile", 11, 11, 1450, 1450, False),
]

def build_tile(name, soil, rows, cols, ox, oy):
    tile = Tile(tile_id=name, soil_type=soil, grid_rows=rows, grid_cols=cols,
                origin_x_cm=float(ox), origin_y_cm=float(oy))
    if soil == "sable":
        eco = init_eco(name, rows, cols, humidite=1.0, fertilite=0.6, microbiome=0.2)
    elif soil == "argile":
        eco = init_eco(name, rows, cols, humidite=2.0, fertilite=1.2, microbiome=0.3)
    else:
        eco = init_eco(name, rows, cols, humidite=1.5, fertilite=1.0, microbiome=0.3)
    return tile, eco


def plant_garden(tile, with_auxiliaries: bool):
    """Jardin diversifié de base (positions valides dans 11×11) ; +attire-aux."""
    tile.add_plant(Tomato,    2, 2)
    tile.add_plant(Basil,     2, 4)
    tile.add_plant(Bean,      4, 2)
    tile.add_plant(Sunflower, 0, 1)
    tile.add_plant(Pepper,    4, 6)
    if with_auxiliaries:
        tile.add_plant(Yarrow,   3, 5)   # achillée (vivace attire-auxiliaires)
        tile.add_plant(Phacelia, 1, 6)   # phacélie (annuelle attire-auxiliaires)
        tile.add_plant(Clover,   5, 4)


def build_world_full():
    """Fabrique du monde COMPLET 20×20 m : 8 tuiles SECTORS plantées + maison.
    Retourne (tiles, ecos, aux_tiles, house) — consommée par le scénario démo
    ci-dessous ET par tools/sim_server.py (init config="full")."""
    tiles, ecos, aux_tiles = [], {}, set()
    for name, soil, rows, cols, ox, oy, with_aux in SECTORS:
        tile, eco = build_tile(name, soil, rows, cols, ox, oy)
        plant_garden(tile, with_aux)
        if with_aux:
            aux_tiles.add(tile.tile_id)
        tiles.append(tile)
        ecos[tile.tile_id] = eco

    # Pommier sur la tuile S (plein soleil — futur verger), en coin. Observer la
    # sénescence (~70 ans) demande « python3 main.py 100 » (cf. tests/test_senescence).
    tiles_by_id = {t.tile_id: t for t in tiles}
    tiles_by_id["S"].add_plant(AppleTree, 0, 7)

    house = House()   # défauts : centrée (1000,1000), 8×8×6 m, calcaire 0.35
    return tiles, ecos, aux_tiles, house


def composition(tiles) -> Counter:
    """Couvert vivant agrégé sur toutes les tuiles, par archétype."""
    c = Counter()
    for tile in tiles:
        for p in tile.plants:
            if p.is_alive:
                c[getattr(p.plant_class, "archetype", None) or "cultivée"] += 1
    return c


def aux_rondelles(tiles, group) -> float:
    """Moyenne de rondelles `auxiliaire` sur un groupe de tuiles."""
    sel = [t for t in tiles if t.tile_id in group]
    if not sel:
        return 0.0
    return sum(t.get_rondelle_count("auxiliaire") for t in sel) / len(sel)


# --- Potager dédié (scénario démo) -----------------------------------------
# La tuile "N" (terre, plein nord, 11×16) devient un POTAGER : on y sème chaque
# printemps un carré dense de cultures via le GESTE planter() FIDÈLE — graine
# prise dans la banque-joueur, coût FAIBLE de Vigueur, germination différée par
# la succession (le tick lève les grains quand la niche est favorable). Aucune
# plante n'est spawnée directement (philo #2). Le verrou d'occupation étant levé
# (sprint compétition intra-plot), les grains lèvent même sur un plot déjà pris.
POTAGER_TILE_ID  = "N"
POTAGER_CROPS    = ["tomate", "basilic", "poivron", "tournesol"]
POTAGER_PER_CROP = 7                       # ~6-8 plots/espèce → potager dense


def potager_plan():
    """Grille dense du potager : une bande de POTAGER_PER_CROP plots par culture
    (lignes 1,3,5,7 ; colonnes 1..7). Positions valides dans la tuile 11×16."""
    plan = []
    for i, sp in enumerate(POTAGER_CROPS):
        r = 1 + 2 * i
        for c in range(1, 1 + POTAGER_PER_CROP):
            plan.append((sp, r, c))
    return plan


def sow_potager(game_state, tile, eco, player, plan, done):
    """Sème (geste planter() fidèle) les plots du plan pas encore semés cette
    année, tant que la Vigueur du joueur le permet. La banque-joueur est
    réapprovisionnée à la volée (les sachets de graines du joueur). On lit le coût
    AVANT de planter pour ne pas drainer la Vigueur d'un semis impossible.
    Renvoie le nombre de graines déposées cet appel."""
    bank = game_state["player_seed_bank"]
    st = VIG.ensure_player(game_state, player)
    objs = ACT._objets_action("planter")
    n = 0
    for key in plan:
        if key in done:
            continue
        sp, r, c = key
        cost = ACT.cout_action(game_state, player, "planter", objs)
        if st["courante"] < cost:          # plus assez de Vigueur cette semaine
            break
        if bank.count(sp) == 0:
            bank.add(Seed(species=sp))     # sachet de graines du joueur
        if ACT.planter(game_state, player, tile, eco, sp, r, c):
            done.add(key)
            n += 1
    return n


if __name__ == "__main__":
    tiles, ecos, aux_tiles, HOUSE = build_world_full()

    game_state = {
        "tiles": tiles,
        "eco":   ecos,
        "house": HOUSE,        # posée dans le monde, INERTE (le moteur ne la lit pas encore)
        "scores": {},
        "current_player": "joueur_1",
        "week": 1,
        "log":  [],
    }

    # Potager : banque-joueur + opt-in Vigueur (le moteur recharge alors la
    # Vigueur au passage de saison et la régénère chaque semaine).
    game_state["player_seed_bank"] = PlayerSeedBank()
    VIG.ensure_player(game_state, "joueur_1")
    POTAGER     = next((t for t in tiles if t.tile_id == POTAGER_TILE_ID), None)
    POTAGER_ECO = ecos.get(POTAGER_TILE_ID)
    POTAGER_PLAN = potager_plan()

    print("╔══════════════════════════════════════════════════════╗")
    print("║   SYMBIOSE — Démo monde 20×20 m (maison centrale)    ║")
    print("║   8 tuiles jardin + maison INERTE + chemins pierre   ║")
    print("╚══════════════════════════════════════════════════════╝")
    x0, y0, x1, y1 = HOUSE.footprint_bounds
    print(f"Maison : centre ({HOUSE.center_x_cm:.0f},{HOUSE.center_y_cm:.0f}) cm "
          f"empreinte [{x0:.0f},{y0:.0f}]→[{x1:.0f},{y1:.0f}] h={HOUSE.height_cm:.0f} "
          f"albédo={HOUSE.wall_albedo} (INERTE)")
    print(f"Tuiles attire-auxiliaires : {sorted(aux_tiles)}")
    print(f"Tuiles témoins            : {sorted(t.tile_id for t in tiles if t.tile_id not in aux_tiles)}")

    engine = Engine(game_state)

    # Nombre d'années : 1er argument CLI, sinon 30. Pour la sénescence du pommier
    # (~70 ans), lancer « python3 main.py 100 ».
    N_YEARS    = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    SNAP_EVERY = 10
    SNAP_WEEK  = 26    # plein été — couvert maximal

    # Le potager (tuile dense semée à la main) est exclu du contraste attire-aux
    # vs témoins : ses chiffres n'ont rien à voir avec la régulation passive.
    control_tiles = {t.tile_id for t in tiles} - aux_tiles - {POTAGER_TILE_ID}

    # Suivi du potager : les cultures sont des ANNUELLES (mortes en hiver) → un
    # recensement de fin de run (sem. 52) lirait toujours 0. On suit donc le PIC
    # de cultures vivantes par espèce sur toute la durée (le couvert estival réel).
    crop_of = {PLANT_CATALOGUE[k]: k for k in POTAGER_CROPS}
    potager_peak = Counter()

    print("\nTRAJECTOIRE — couvert vivant agrégé (S26) + rondelles auxiliaire moyennes")
    print(f"{'année':>6} {'pion':>5} {'fixe':>5} {'gram':>5} {'comp':>5} {'cult':>5} "
          f"{'%viv':>5} {'aux+':>5} {'aux0':>5}")
    for y in range(1, N_YEARS + 1):
        sown = set()                          # potager re-semé chaque printemps
        for _ in range(52):
            wiy = ((engine.week - 1) % 52) + 1
            # Semis du potager au printemps (sem. 1-13), étalé : la Vigueur (100
            # au passage de saison, +10/sem) borne le nombre de plots par semaine.
            if POTAGER is not None and 1 <= wiy <= 13:
                sow_potager(game_state, POTAGER, POTAGER_ECO, "joueur_1",
                            POTAGER_PLAN, sown)
            engine.tick_semaine()
            if POTAGER is not None:
                cur = Counter()
                for p in POTAGER.plants:
                    if p.is_alive and p.plant_class in crop_of:
                        cur[crop_of[p.plant_class]] += 1
                for sp in POTAGER_CROPS:
                    potager_peak[sp] = max(potager_peak[sp], cur[sp])
            if wiy == SNAP_WEEK and (y == 1 or y == N_YEARS or y % SNAP_EVERY == 0):
                c = composition(tiles)
                pion = c["pioneer"]; fix = c["nitrogen_fixer"]
                gra  = c["grass"];   comp = c["competitor"]; cult = c["cultivée"]
                viv  = fix + gra + comp
                spont = pion + viv
                pct  = 100.0 * viv / spont if spont else 0.0
                a_plus = aux_rondelles(tiles, aux_tiles)
                a_zero = aux_rondelles(tiles, control_tiles)
                print(f"{y:>6} {pion:>5} {fix:>5} {gra:>5} {comp:>5} {cult:>5} "
                      f"{pct:>4.0f}% {a_plus:>5.1f} {a_zero:>5.1f}")
        engine.game_state["log"].clear()

    # --- Résumé final ---
    print("\n" + "═"*60)
    print("RÉSUMÉ FINAL — par tuile (orientation)")
    print("═"*60)
    print(f"{'tuile':>6} {'sol':>7} {'aux?':>5} {'vivantes':>9} "
          f"{'aux●':>5} {'pollin●':>8} {'vitalité':>9}")
    for tile in tiles:
        eco = ecos[tile.tile_id]
        alive = sum(1 for p in tile.plants if p.is_alive)
        is_aux = "oui" if tile.tile_id in aux_tiles else "—"
        auxr = tile.get_rondelle_count("auxiliaire")
        polr = tile.get_rondelle_count("pollinisateur")
        print(f"{tile.tile_id:>6} {tile.soil_type:>7} {is_aux:>5} {alive:>9} "
              f"{auxr:>5} {polr:>8} {eco.vitalite_average():>9.3f}")

    # Moyennes par groupe (montre l'effet attire-auxiliaires)
    def group_avg(group, fn):
        sel = [t for t in tiles if t.tile_id in group]
        return sum(fn(t) for t in sel) / len(sel) if sel else 0.0

    print("\nContraste attire-auxiliaires vs témoins (moyennes par tuile) :")
    for label, group in [("attire-aux", aux_tiles), ("témoins   ", control_tiles)]:
        auxr = group_avg(group, lambda t: t.get_rondelle_count("auxiliaire"))
        vit  = group_avg(group, lambda t: ecos[t.tile_id].vitalite_average())
        alive = group_avg(group, lambda t: sum(1 for p in t.plants if p.is_alive))
        print(f"  {label} : auxiliaire●={auxr:.1f}  vitalité={vit:.3f}  vivantes={alive:.1f}")

    # --- Potager : bilan des cultures semées chaque printemps via planter() ---
    if POTAGER is not None:
        grains = sum(len(g) for g in POTAGER.grains_en_attente.values())
        vst = game_state["vigueur"]["joueur_1"]
        vmax = vst["max_base"] * VIG.palier_bonus(game_state, "joueur_1")
        print(f"\nPotager (tuile {POTAGER_TILE_ID}) — semé via planter() chaque "
              f"printemps, {POTAGER_PER_CROP} plots/espèce :")
        print("  (pic de cultures vivantes sur la durée — annuelles, mortes en hiver)")
        for sp in POTAGER_CROPS:
            print(f"  {sp:>10} : pic {potager_peak.get(sp, 0)} vivante(s)")
        print(f"  grains encore en attente de levée : {grains}")
        print(f"  Vigueur joueur_1 (fin de run) : {vst['courante']:.0f}/{vmax:.0f}")

    scores = game_state.get("scores", {})
    if scores:
        print("\nScores finaux :")
        for pid, sc in scores.items():
            total = sum(sc.values())
            print(f"  {pid} — récolte:{sc.get('recolte',0)} "
                  f"luxuriance:{sc.get('luxuriance',0)} "
                  f"biodiversité:{sc.get('biodiversite',0)} TOTAL:{total}")
