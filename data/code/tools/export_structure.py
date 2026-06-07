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


def export_maquette(path: str) -> dict:
    """Pont JSON de la MAQUETTE SAISONNIÈRE (sprint maison, tronçon 4) : les 3
    secteurs (S/NE/NO) × 4 saisons, poussés dans un vrai LightField + maison, pour
    qu'un futur rendu Godot dessine la MÊME scène (ombre déterministe + plants
    penchés) que le SVG. Réutilise EXACTEMENT les spécimens de render_structure.py
    (import direct → mêmes positions/SEED/strength → cohérence byte-stable). Dump
    la maison (projeteur d'ombre) + par secteur/saison : lumière reçue + géométrie
    du plant (`_specimen_dict`)."""
    from tools.render_structure import (SECTEURS_MAQ, SAISON_WEEK_MAQ, SAISONS_ORDRE,
                                        MAQ_SPECIES, _grow_sector)
    from world.building import House

    house = House()
    strength = 0.30                                   # marqué (défaut Q3)
    orig = MAQ_SPECIES.phototropism_strength
    MAQ_SPECIES.phototropism_strength = strength
    try:
        secteurs = []
        for name, ox, oy, rows, cols, lx, ly in SECTEURS_MAQ:
            snaps = _grow_sector(MAQ_SPECIES, ox, oy, rows, cols, lx, ly, house)
            secteurs.append((name, ox + lx, oy + ly, snaps))
    finally:
        MAQ_SPECIES.phototropism_strength = orig

    hx0, hy0, hx1, hy1 = house.footprint_bounds
    doc = {
        "phototropism_strength": strength,
        "house": {
            "footprint_cm": [_r(hx0), _r(hy0), _r(hx1), _r(hy1)],
            "height_cm": _r(house.height_cm),
            "wall_albedo": _r(house.wall_albedo),
            "latitude_deg": _r(house.latitude_deg),
        },
        "sectors": [
            {
                "name": name,
                "collet_world_cm": [_r(cwx), _r(cwy)],
                "saisons": [
                    {
                        "saison": s,
                        "light_received": _r(snaps[s][1]),
                        "specimen": _specimen_dict(snaps[s][0], f"{name} · {s}"),
                    }
                    for s in SAISONS_ORDRE
                ],
            }
            for (name, cwx, cwy, snaps) in secteurs
        ],
    }
    with open(path, "w") as f:
        json.dump(doc, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"[export maquette] écrit : {path}")
    for sec in doc["sectors"]:
        cells = "  ".join(f"{sa['saison'][:4]}:lum{sa['light_received']:.2f}/"
                          f"seg{len(sa['specimen']['segments'])}"
                          for sa in sec["saisons"])
        print(f"  {sec['name']:18s} {cells}")
    return doc


if __name__ == "__main__":
    here = os.path.dirname(__file__)
    if len(sys.argv) > 1 and sys.argv[1] == "structure":
        # Ancien pont structure (préservé) : python3 -m tools.export_structure structure [out.json]
        out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "structure.json")
        export(out)
    else:
        # Tronçon 4 : pont JSON de la maquette saisonnière (secteurs × saisons).
        export_maquette(os.path.join(here, "maquette_secteurs.json"))
