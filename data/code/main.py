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
"""

import sys
from collections import Counter
from world import Tile, House
from plants import (Tomato, Basil, Sunflower, Bean, Clover, Pepper,
                    Yarrow, Phacelia, AppleTree)
from fields import init_eco
from sim.engine import Engine

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

HOUSE = House()   # défauts : centrée (1000,1000), 8×8×6 m, calcaire 0.35


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


tiles = []
ecos = {}
aux_tiles = set()
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

game_state = {
    "tiles": tiles,
    "eco":   ecos,
    "house": HOUSE,        # posée dans le monde, INERTE (le moteur ne la lit pas encore)
    "scores": {},
    "current_player": "joueur_1",
    "week": 1,
    "log":  [],
}

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


# Nombre d'années : 1er argument CLI, sinon 30. Pour la sénescence du pommier
# (~70 ans), lancer « python3 main.py 100 ».
N_YEARS    = int(sys.argv[1]) if len(sys.argv) > 1 else 30
SNAP_EVERY = 10
SNAP_WEEK  = 26    # plein été — couvert maximal

control_tiles = {t.tile_id for t in tiles} - aux_tiles

print("\nTRAJECTOIRE — couvert vivant agrégé (S26) + rondelles auxiliaire moyennes")
print(f"{'année':>6} {'pion':>5} {'fixe':>5} {'gram':>5} {'comp':>5} {'cult':>5} "
      f"{'%viv':>5} {'aux+':>5} {'aux0':>5}")
for y in range(1, N_YEARS + 1):
    for _ in range(52):
        wiy = ((engine.week - 1) % 52) + 1
        engine.tick_semaine()
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

scores = game_state.get("scores", {})
if scores:
    print("\nScores finaux :")
    for pid, sc in scores.items():
        total = sum(sc.values())
        print(f"  {pid} — récolte:{sc.get('recolte',0)} "
              f"luxuriance:{sc.get('luxuriance',0)} "
              f"biodiversité:{sc.get('biodiversite',0)} TOTAL:{total}")
