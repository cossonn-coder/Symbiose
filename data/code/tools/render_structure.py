"""
SYMBIOSE — tools/render_structure.py
Aperçu VISUEL de la structure de croissance procédurale (D29 réorienté).

But : « voir où on en est » SANS attendre le rendu Godot (tronçon 4). On rejoue
le VRAI moteur (sim.growth.grow_plant, source de vérité déterministe) sur
quelques plantes représentatives, puis on projette leurs segments en isométrie
et on émet un SVG (pur Python, zéro dépendance — s'ouvre dans un navigateur ou
Nextcloud). C'est une maquette de ce que rastérisera le tronçon 4 (§H.1), pas le
rendu final : ici on dessine des lignes vectorielles, là-bas des pixels au palier
de zoom. Le bois est brun (épaisseur ∝ thickness_cm), les apex actifs verts ; une
ellipse au sol figure l'empreinte de couronne dérivée (§G).

> Refactor structurel (Sprint refactor global, SS⑤) : ce FICHIER reste l'entrée
> CLI (et le module importé `tools.render_structure`), mais n'est plus qu'un MINCE
> point d'entrée. La logique vit dans le paquet voisin `tools/maquette/` (iso,
> organes, apercu, secteurs). L'API publique historique reste ré-exportée ici :
> `render`, `render_maquette`, `REPRO_BY_SEASON` (pont `tools/simserver`),
> `SECTEURS_MAQ`/`SAISON_WEEK_MAQ`/`SAISONS_ORDRE`/`MAQ_SPECIES`/`_grow_sector`
> (`tools/export_structure`).

Usage (depuis data/code/) :
  python3 -m tools.render_structure            # → maquettes saisonnières (subtil + marqué)
  python3 -m tools.render_structure apercu     # → tools/apercu_structure.svg
  python3 -m tools.render_structure apercu mon.svg   # chemin de sortie explicite
"""
from __future__ import annotations
import os
import sys

# API ré-exportée depuis le paquet (importeurs existants intacts).
from tools.maquette import (render, render_maquette, REPRO_BY_SEASON,  # noqa: F401
                            SECTEURS_MAQ, SAISON_WEEK_MAQ, SAISONS_ORDRE,
                            MAQ_SPECIES, _grow_sector)


if __name__ == "__main__":
    here = os.path.dirname(__file__)
    if len(sys.argv) > 1 and sys.argv[1] == "apercu":
        # Ancien aperçu structure (préservé) : python3 -m tools.render_structure apercu [out.svg]
        out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "apercu_structure.svg")
        render(out)
    else:
        # Tronçon 4 : maquette saisonnière, subtil ET marqué (Nico tranche à l'œil).
        render_maquette(os.path.join(here, "maquette_saison_subtil.svg"), 0.10, "subtil")
        render_maquette(os.path.join(here, "maquette_saison_marque.svg"), 0.30, "marqué")
