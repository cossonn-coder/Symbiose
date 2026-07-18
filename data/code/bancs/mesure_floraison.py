"""
SYMBIOSE — bancs/mesure_floraison.py
BANC DE MESURE (hors golden, hors registre F5) : journalise, sur l'ANNÉE, la
`floraison` de chaque espèce du banc `floraison_saisons` ET l'activité
pollinisatrice (densité des butineurs) sur la tuile — pour VOIR le RECOUVREMENT
(ou son absence) entre la floraison et la présence des pollinisateurs.

Motivation (décalage phénologique remonté au tronçon ②, décision design réservée
à Nico) : la floraison retypée (①) place le pommier/la violette au PRINTEMPS
précoce, alors que la population de pollinisateurs (gâtée par `warmth` + nectar)
ne culmine qu'en ÉTÉ. Ce script rend le désaccord LISIBLE en une table annuelle :
colonne par espèce (floraison ∈ [0,1]) + colonnes butineurs (densité moyenne).
Quand une fleur est ouverte (floraison ≥ 0.5) sans butineur en regard, la nouaison
entomophile SANS PLANCHER (philo #2) ne peut pas se faire → « aucune / une seule
pomme ». Le script ne touche à AUCUNE mécanique : il déroule le moteur et LIT
l'état réel (`plant.floraison`, `eco.populations`), au même endroit que la vue.

Ce n'est PAS un banc F5 (pas de fabrique dans `BANCS[]`) mais un script de
diagnostic exécutable — sœur de `bancs.mesure_nouaison` / `tools.diag_population`.

Usage (depuis data/code/) :
  python3 -m bancs.mesure_floraison          # 1 année, banc floraison_saisons
  python3 -m bancs.mesure_floraison 2        # 2 années
"""
from __future__ import annotations
import sys

from bancs import BANCS
from sim.engine import Engine
from sim import vigueur as VIG
from fields import POLLINATOR_NAMES


def _dens(field) -> float:
    """Densité moyenne d'un `GridField` de population sur la tuile."""
    n = field.rows * field.cols
    return sum(field.data[r][c] for r in range(field.rows)
               for c in range(field.cols)) / n


def _monde():
    """Monte le banc `floraison_saisons` et emballe le game_state minimal + engine.
    Retourne (game_state, engine, plants_par_nom, eco_tuile)."""
    tiles, ecos, house, banque = BANCS["floraison_saisons"]()
    tile = tiles[0]
    game_state = {
        "tiles": tiles, "eco": ecos, "house": house, "scores": {},
        "current_player": "joueur_1", "week": 1, "log": [],
        "player_seed_bank": banque,
    }
    VIG.ensure_player(game_state, "joueur_1")
    engine = Engine(game_state)
    # Une plante par espèce (le banc n'en pose qu'une de chaque) — ordre de saison.
    ordre = ["SweetViolet", "AppleTree", "Borage", "Sunflower", "Mugwort"]
    par_nom = {}
    for p in tile.plants:
        par_nom.setdefault(p.plant_class.__name__, p)
    plants = [(nom, par_nom[nom]) for nom in ordre if nom in par_nom]
    return game_state, engine, plants, ecos[tile.tile_id]


def mesurer(n_years: int = 1) -> None:
    """Déroule le banc `n_years` années et imprime, chaque semaine, la floraison de
    chaque espèce + la densité de chaque pollinisateur sur la tuile. Marque d'un
    `*` toute semaine où AU MOINS une fleur est ouverte (floraison ≥ 0.5) mais où
    l'activité pollinisatrice totale reste faible (< 0.05) = fenêtre de recouvrement
    manquée (le cœur du décalage à trancher)."""
    game_state, engine, plants, eco = _monde()
    pollen = [(name, eco.populations.get(name)) for name in POLLINATOR_NAMES
              if eco.populations and eco.populations.get(name) is not None]

    esp = [nom for nom, _ in plants]
    print("Banc floraison_saisons — floraison ∈[0,1] par espèce + densité "
          "butineurs (moyenne tuile).")
    print("'*' = ≥1 fleur ouverte (≥0.5) mais activité pollinisatrice totale "
          "faible (<0.05) → recouvrement manqué.\n")
    head = f"{'an':>2} {'S':>3} " + " ".join(f"{n[:5]:>6}" for n in esp) \
        + " | " + " ".join(f"{n[:4]:>5}" for n, _ in pollen) + "  flag"
    print(head)
    for y in range(1, n_years + 1):
        for _ in range(52):
            engine.tick_semaine()
            wiy = game_state["week"] if isinstance(game_state["week"], int) else 0
            wiy = ((game_state["week"] - 1) % 52) + 1
            flo = [p.floraison for _, p in plants]
            pol = [_dens(f) for _, f in pollen]
            fleur_ouverte = any(v >= 0.5 for v in flo)
            act = sum(pol)
            manque = fleur_ouverte and act < 0.05
            if fleur_ouverte or act > 1e-3:
                line = f"{y:>2} {wiy:>3} " \
                    + " ".join(f"{v:>6.2f}" for v in flo) + " | " \
                    + " ".join(f"{v:>5.3f}" for v in pol) \
                    + ("  *" if manque else "")
                print(line)
        game_state["log"].clear()


if __name__ == "__main__":
    ny = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    mesurer(ny)
