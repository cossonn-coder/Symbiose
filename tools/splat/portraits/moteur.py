"""
SYMBIOSE — tools/splat/portraits/moteur.py (sprint PRÉCUISSON SPLATS ⑥)
Ce que le MOTEUR sait d'une espèce, pour ses portraits (lecture seule, golden intact).

Sortie JSON (stdout) : pour chaque classe du catalogue (`plants/catalogue.py`, toutes
tables) → clé du catalogue (⑦), cycle de vie (`life_cycle`, `deciduous`), stades (nom, hauteur, rayon de
canopée) ; et pour les espèces demandées en argument (`Espece:sem1,sem2`), la
STRUCTURE de segments rejouée par `tools.export_structure._grow` à ces âges — le
squelette du portrait (lianes et arbres, comme le prototype tomate).

Usage (depuis la racine du dépôt) :
  python3 tools/splat/portraits/moteur.py Tomato:8,30 AppleTree:156,520 > moteur.json

📖 Pédagogie : l'outil de cuisson (JS) ne réimplémente rien du moteur. Il lui
demande ses états déjà calculés, comme le pont du jeu : une seule vérité (Python),
plusieurs lecteurs. Déterministe : SEED fixe de export_structure, aucun aléa.
"""
from __future__ import annotations
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'code'))

from plants import catalogue as C                     # noqa: E402
from tools.export_structure import _grow, _specimen_dict   # noqa: E402

# Âges longs (≥ 1 an) : saisons réelles ; courts : été fixe, comme le prototype.
SEMAINES_REELLES = 52


def especes() -> dict[str, type]:
    """Toutes les classes du catalogue (cultivées, vivaces, adventices, flore)."""
    out: dict[str, type] = {}
    for table in (C.PLANT_CATALOGUE, C.PERENNIAL_CATALOGUE, C.WEED_CATALOGUE):
        for cls in table.values():
            out[cls.__name__] = cls
    for cls in C.ESPECES_SPONTANEES:
        out[cls.__name__] = cls
    return out


def cles_catalogue() -> dict[str, str]:
    """Classe → clé du catalogue (`tomate`, `bourse_pasteur`…) : la clé que le pont
    donne aux fiches d'encyclopédie et aux offres du magazine (⑦). Tables à clés
    d'espèce seulement (WEED_CATALOGUE est indexée par archétype)."""
    out: dict[str, str] = {}
    for table in (C.PLANT_CATALOGUE, C.PERENNIAL_CATALOGUE):
        for cle, cls in table.items():
            out.setdefault(cls.__name__, cle)
    return out


def fiche(cls, cle: str | None) -> dict:
    return {
        "cle": cle,
        "life_cycle": cls.life_cycle,
        "deciduous": bool(cls.deciduous),
        "stades": [{"nom": g.name, "hauteur_cm": g.canopy_height, "rayon_cm": g.canopy_radius}
                   for g in cls.growth_stages],
    }


def main(args: list[str]) -> None:
    table = especes()
    cles = cles_catalogue()
    doc = {nom: fiche(cls, cles.get(nom)) for nom, cls in sorted(table.items())}
    for arg in args:
        nom, ages = arg.split(':')
        structures = []
        for sem in (int(a) for a in ages.split(',')):
            p = _grow(table[nom], sem, "real" if sem >= SEMAINES_REELLES else "summer")
            structures.append({"semaines": sem, **_specimen_dict(p, f"{nom} · {sem} sem.")})
        doc[nom]["structures"] = structures
    json.dump(doc, sys.stdout, sort_keys=True)


if __name__ == "__main__":
    main(sys.argv[1:])
