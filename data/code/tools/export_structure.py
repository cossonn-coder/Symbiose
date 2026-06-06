"""
SYMBIOSE — tools/export_structure.py
Pont JSON read-only : structure procédurale (Python, source de vérité) → Godot.

But : nourrir le RENDU Godot (tronçon 4) avec les VRAIES plantes du moteur, sans
porter le moteur en C# (dette D24). On rejoue le moteur déterministe
(sim.growth.grow_plant) sur les mêmes spécimens que render_structure.py, puis au
lieu d'émettre un SVG (maquette), on DUMP la géométrie en JSON. C# lira ce fichier
et le dessinera (cf. visuals/PlantRenderer.cs). Préfigure le save (§J) mais ne le
verrouille PAS (pas d'engine_version, pas de contrat de sérialisation).

GOLDEN INTACT : on ne LIT que grow_plant / l'empreinte (états déjà calculés), on
ne modifie rien du moteur → zéro impact sur le golden output.

Usage (depuis data/code/) :
  python3 -m tools.export_structure                  # → tools/structure.json
  python3 -m tools.export_structure tools/out.json   # chemin de sortie explicite

Déterminisme : même SEED + mêmes spécimens que render_structure.py → deux runs
produisent un fichier byte-identique (vérifiable, cf. kickoff).
"""
from __future__ import annotations
import json
import os
import sys

from plants import Tomato, AppleTree, PlantInstance
import sim.growth as G

SEED = 0x5AB1057E

# Arrondi des flottants exportés : assez fin pour le rendu (sub-pixel), assez
# court pour un fichier compact et stable. L'arrondi est déterministe → n'altère
# pas la reproductibilité byte-à-byte.
NDIGITS = 3


def _grow(cls, n: int, week_mode: str = "real") -> PlantInstance:
    """Rejoue grow_plant n ticks (déterministe). Copie EXACTE de la logique de
    render_structure.py pour garantir la même cible visuelle. week_mode 'real' =
    cycle saisonnier (1+k) ; 'summer' = été fixe (croissance non ralentie)."""
    p = PlantInstance(plant_class=cls, position=(2, 2))
    p.growth_factor = 1.0
    for k in range(n):
        week = (1 + k) if week_mode == "real" else 20
        G.grow_plant(p, SEED, week)
    return p


def _r(x: float) -> float:
    return round(float(x), NDIGITS)


def _specimen_dict(plant: PlantInstance, title: str) -> dict:
    """Sérialise une plante : empreinte dérivée (§G, pour la silhouette LOD) +
    collet + liste de segments (géométrie pure du bois — pas d'organes ici)."""
    cls = plant.plant_class
    collet = plant.segments[0].base
    segments = []
    for s in plant.segments:
        segments.append({
            "base": [_r(s.base[0]), _r(s.base[1]), _r(s.base[2])],
            "dir": [_r(s.dir[0]), _r(s.dir[1]), _r(s.dir[2])],
            "length_cm": _r(s.length_cm),
            "thickness_cm": _r(s.thickness_cm),
            "is_apex": bool(s.is_apex),
        })
    return {
        "title": title,
        "species": cls.__name__,
        "footprint": {
            "height_cm": _r(cls.height_at(plant)),
            "canopy_radius_cm": _r(cls.canopy_radius_at(plant)),
        },
        "collet_cm": [_r(collet[0]), _r(collet[1]), _r(collet[2])],
        "segments": segments,
    }


def export(path: str) -> dict:
    # Mêmes spécimens représentatifs que la maquette SVG (render_structure.py).
    specimens_src = [
        (_grow(Tomato, 80, "summer"),   "Tomate · flèche mûre"),
        (_grow(AppleTree, 3 * 52),      "Pommier · an 3 (jeune)"),
        (_grow(AppleTree, 7 * 52),      "Pommier · an 7 (étalement)"),
        (_grow(AppleTree, 10 * 52),     "Pommier · an 10 (etale)"),
    ]
    doc = {"specimens": [_specimen_dict(p, t) for (p, t) in specimens_src]}
    # indent + sort_keys : lisible (debug) ET stable (ordre des clés fixé →
    # deux runs = même fichier). newline final pour propreté.
    with open(path, "w") as f:
        json.dump(doc, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"[export] structure écrite : {path}")
    for spec in doc["specimens"]:
        fp = spec["footprint"]
        print(f"  {spec['title']:32s} h={fp['height_cm']:6.0f}cm "
              f"couronne={fp['canopy_radius_cm']:5.0f}cm "
              f"seg={len(spec['segments']):3d}")
    return doc


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else \
        os.path.join(os.path.dirname(__file__), "structure.json")
    export(out)
