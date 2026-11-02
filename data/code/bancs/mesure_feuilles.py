"""
SYMBIOSE — bancs/mesure_feuilles.py
BANC DE MESURE (hors golden, hors registre F5) du sprint AUTOMNE VISIBLE (③,
docs/rendu/ambiance/conception_automne_visible.md §3.2) : où tombent les feuilles et
ce que le sol en fait. Déroule le monde `full` par le serveur, en lecture seule.

Trois tableaux :
  1. par arbre, s30 → s45 : plots de la couronne (sur la tuile), plots portant des
     feuilles, masse de feuilles sous la couronne, `feuillage` du pont ;
  2. sol sous la couronne contre plots témoins de la même tuile, en fin d'hiver de
     chaque année : azote et matière organique, pour repérer une dérive ;
  3. taille du snapshot au pic d'automne.

« Témoin » = plot de la même tuile hors de toute couronne caduque de plus de 3 m, et hors
plot-foyer d'un ligneux. La vie du plot (autres plantes, faune) n'est pas contrôlée : l'écart
reste une comparaison de deux sous-ensembles d'un seul run.

Usage (depuis data/code/) :
  python3 -m bancs.mesure_feuilles        # 2 années (défaut)
  python3 -m bancs.mesure_feuilles 3      # 3 années (jamais plus)
"""
from __future__ import annotations
import json
import sys

from tools.simserver.server import SimServer

SEED = 42
N_ANS_MAX = 3            # garde-fou du sprint : mesures ≤ 3 ans
HAUTEUR_ARBRE = 300.0    # cm, en dessous c'est un semis : hors tableaux
SEMAINES = (30, 32, 34, 36, 37, 38, 40, 42, 45)
SEUIL_TAPIS = 0.005      # masse de feuilles à partir de laquelle un plot compte


def _feuilles(eco, r, c) -> float:
    return sum(p.masse for p in eco.litiere[r][c] if p.tissu == "feuille")


def _arbres(gs) -> list:
    """Les caducs vivants de plus de 3 m : (tuile, plante)."""
    return [(t, p) for t in gs["tiles"] for p in t.plants
            if p.is_alive and p.plant_class.deciduous
            and p.current_height >= HAUTEUR_ARBRE]


def _couronne(tile, p) -> list:
    return [rc for rc in p.foliar_plots if tile.is_valid_plot(*rc)]


def _temoins(tile, arbres) -> list:
    """Plots de `tile` sous aucune couronne d'arbre."""
    couverts = {rc for t, p in arbres if t is tile for rc in _couronne(t, p)}
    foyers = {p.position for p in tile.plants
              if p.plant_class.deciduous and p.is_alive}
    return [(r, c) for r in range(tile.grid_rows) for c in range(tile.grid_cols)
            if (r, c) not in couverts and (r, c) not in foyers]


def _moyenne(plots, lire) -> float:
    return sum(lire(r, c) for r, c in plots) / len(plots) if plots else 0.0


def _ligne_sol(eco, plots) -> tuple:
    return (_moyenne(plots, eco.n.at_plot),
            _moyenne(plots, eco.om_active.at_plot),
            _moyenne(plots, eco.om_stable.at_plot))


def main(n_ans: int) -> None:
    serveur = SimServer()
    assert serveur.cmd_init({"config": "full", "seed": SEED})["ok"]
    gs = serveur.engine.game_state
    print(f"# Feuilles au sol, monde `full`, seed {SEED} [n=1 run, VM]\n")
    print("## Par arbre, an 1\n")
    print("| arbre | tuile | sem. | plots couronne | plots avec feuilles | masse sous couronne | feuillage |")
    print("|---|---|---|---|---|---|---|")
    pic = None
    sols = []
    for k in range(n_ans * 52):
        snap = serveur.cmd_step_week({})["snapshot"]
        semaine = ((gs["week"] - 1) % 52) + 1
        an = (gs["week"] - 1) // 52 + 1
        if an == 1 and semaine in SEMAINES:
            hints = {(q["tile"], q["species"], q["x_cm"], q["y_cm"]): q.get("feuillage")
                     for q in snap["plants"]}
            for tile, p in _arbres(gs):
                eco = gs["eco"][tile.tile_id]
                plots = _couronne(tile, p)
                masses = [_feuilles(eco, r, c) for r, c in plots]
                couverts = sum(m >= SEUIL_TAPIS for m in masses)
                hint = hints.get((tile.tile_id, p.plant_class.__name__, p.x_cm, p.y_cm))
                print(f"| {p.name} | {tile.tile_id} | s{semaine} | {len(plots)} | "
                      f"{couverts} | {sum(masses):.3f} | {hint} |")
        if semaine == 39 and an == 1:
            pic = len(json.dumps(snap, separators=(",", ":")))
        if semaine == 52:
            arbres = _arbres(gs)
            for tile in gs["tiles"]:
                if not any(t is tile for t, _ in arbres):
                    continue
                eco = gs["eco"][tile.tile_id]
                dessous = sorted({rc for t, p in arbres if t is tile
                                  for rc in _couronne(t, p)})
                sols.append((an, tile.tile_id, len(dessous), _ligne_sol(eco, dessous),
                             _ligne_sol(eco, _temoins(tile, arbres))))
    print("\n## Sol, fin de chaque année\n")
    print("| an | tuile | plots sous couronne | N couronne | N témoin | om_active couronne | "
          "om_active témoin | om_stable couronne | om_stable témoin |")
    print("|---|---|---|---|---|---|---|---|---|")
    for an, tid, n, (n1, a1, s1), (n2, a2, s2) in sols:
        print(f"| {an} | {tid} | {n} | {n1:.3f} | {n2:.3f} | {a1:.3f} | {a2:.3f} | "
              f"{s1:.3f} | {s2:.3f} |")
    print(f"\n## Taille du snapshot\n\ns39, an 1 : {pic} octets.")


if __name__ == "__main__":
    demande = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    main(min(demande, N_ANS_MAX))
