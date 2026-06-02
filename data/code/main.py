"""
SYMBIOSE — main.py
Scénario de test : 1 tuile terre, 5 plantes, 1 an complet.
Champs continus initialisés : humidité 1.5/3, fertilité 1.0/3, microbiome 0.3/3
"""

import sys
import random
from collections import Counter
from models import Tile, Tomato, Basil, Sunflower, Bean, Clover
from fields import init_eco, inject_patch
from engine import Engine

random.seed(42)

# Tuile
tile = Tile(tile_id="A1", soil_type="terre")

# Champs continus initiaux (valeurs continues, pas rondelles)
eco = init_eco("A1", rows=6, cols=8,
               humidite=1.5, fertilite=1.0, microbiome=0.3)

# Rondelles discrètes (variables de gameplay)
tile.stakes[0].add("pollinisateur")   # déjà un pollinisateur présent

# Plantation — espacées pour éviter conflits root immédiats
tile.add_plant(Tomato,    2, 2)   # séparé du basilic
tile.add_plant(Basil,     2, 5)   # compagnon mais distant
tile.add_plant(Sunflower, 0, 1)
tile.add_plant(Bean,      4, 2)
tile.add_plant(Clover,    4, 6)

# Injecter un patch humide sous la tomate (arrosage initial joueur)
inject_patch(eco, "humidite", center_row=2, center_col=2, value=0.5, radius=1)

game_state = {
    "tiles": [tile],
    "eco":   {"A1": eco},
    "scores": {},
    "current_player": "joueur_1",
    "week": 1,
    "log":  [],
}

print("╔══════════════════════════════════════════════════════╗")
print("║         SYMBIOSE — Simulation 10 ans v2             ║")
print("║   Diffusion écologique continue + uptake racinaire  ║")
print("╚══════════════════════════════════════════════════════╝")
print(f"\nÉtat initial : {eco}")

engine = Engine(game_state)

# --- Trajectoire de succession : composition du couvert installé ---------
# Échantillonnée en plein été (S26) : les annuelles pionnières sont encore
# vivantes (elles meurent à l'hiver, winter_strategy="die"), le couvert est
# donc représentatif. Comptage des plantes vivantes par archétype.
def composition_couvert(tile) -> Counter:
    c = Counter()
    for p in tile.plants:
        if p.is_alive:
            c[getattr(p.plant_class, "archetype", None) or "cultivée"] += 1
    return c

# Nombre d'années simulées : 1er argument CLI, sinon 500 par défaut.
# Permet « python3 main.py 60 » pour une simu courte (gain de temps).
N_YEARS    = int(sys.argv[1]) if len(sys.argv) > 1 else 500
SNAP_EVERY = 10    # un instantané tous les 10 ans
SNAP_WEEK  = 26    # plein été — couvert maximal

print("\nTRAJECTOIRE DE SUCCESSION — couvert vivant au plein été (S26)")
print(f"{'année':>6} {'pion':>5} {'fixe':>5} {'gram':>5} {'comp':>5} {'cult':>5} {'%vivace':>8}")
for y in range(1, N_YEARS + 1):
    for _ in range(52):
        wiy = ((engine.week - 1) % 52) + 1
        engine.tick_semaine()
        if wiy == SNAP_WEEK and (y == 1 or y == N_YEARS or y % SNAP_EVERY == 0):
            c    = composition_couvert(tile)
            pion = c["pioneer"]; fix = c["nitrogen_fixer"]
            gra  = c["grass"];   comp = c["competitor"]; cult = c["cultivée"]
            viv  = fix + gra + comp
            spont = pion + viv          # couvert spontané (hors cultivées)
            pct  = 100.0 * viv / spont if spont else 0.0
            print(f"{y:>6} {pion:>5} {fix:>5} {gra:>5} {comp:>5} {cult:>5} {pct:>7.0f}%")
    engine.game_state["log"].clear()    # éviter l'accumulation mémoire (non imprimé)

# --- Résumé final ---
print("\n" + "═"*52)
print("RÉSUMÉ FINAL")
print("═"*52)

alive = [p for p in tile.plants if p.is_alive]
dead  = [p for p in tile.plants if not p.is_alive]

print(f"\nPlantes survivantes ({len(alive)}) :")
for p in alive:
    r, c = p.position
    hum  = eco.humidite.at_plot(r, c)
    fert = eco.fertilite.at_plot(r, c)
    print(f"  {p}  hum={hum:.2f} fert={fert:.2f}")

if dead:
    print(f"\nPlantes mortes ({len(dead)}) :")
    for p in dead:
        print(f"  {p.name}@{p.position}")

print(f"\nChamps écologiques finaux :")
s = eco.summary()
for var, val in s.items():
    bar = "█" * int(val) + "░" * max(0, 3 - int(val))
    print(f"  {var:12s} {bar} {val:.2f}/3.00")

print(f"\nRondelles discrètes :")
for var in ["maladie", "pollinisateur", "paillage"]:
    count = tile.get_rondelle_count(var)
    if count:
        print(f"  {var:15s} {'●'*count}")

print(f"\nScores finaux :")
scores = game_state.get("scores", {})
if scores:
    for pid, sc in scores.items():
        total = sum(sc.values())
        print(f"  {pid} — récolte:{sc.get('recolte',0)} "
              f"luxuriance:{sc.get('luxuriance',0)} "
              f"biodiversité:{sc.get('biodiversite',0)} "
              f"TOTAL:{total}")

print(f"\nConflits : {sum(1 for c in tile.conflicts if c.resolved)} résolus, "
      f"{sum(1 for c in tile.conflicts if not c.resolved)} actifs")

# Carte de chaleur humidité finale
print(f"\nCarte humidité finale (grille 6×8) :")
print(eco.humidite.ascii_map(precision=2))

# Carte de vitalité dérivée (grandeur non stockée, calculée à la demande)
print(f"\nCarte vitalité dérivée (grille 6×8) :")
for r in range(eco.rows):
    prefix = "  " if r % 2 == 1 else ""
    cells = " ".join(f"{eco.vitalite(r, c):.2f}" for c in range(eco.cols))
    print(prefix + cells)
print(f"vitalité moyenne : {eco.vitalite_average():.3f}")
