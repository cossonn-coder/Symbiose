"""
SYMBIOSE — tools/maquette/
Paquet des rendus SVG de maquette (aperçu structure + maquette saisonnière
maison/ombre/phototropisme). Éclaté de l'ex-monolithe `tools/render_structure.py`
au Sprint refactor global (SS⑤) : l'entrée CLI reste `tools/render_structure.py`
(mince), qui importe ce paquet et ré-exporte l'API publique.

Modules : `iso` (projection + géométrie), `organes` (feuilles/fleurs/fruits
procéduraux + `REPRO_BY_SEASON`), `apercu` (aperçu structure), `secteurs`
(maquette saisonnière 3 secteurs).

API ré-exportée (importeurs existants intacts : `tools/simserver`,
`tools/export_structure`) :
  - render, render_maquette        : les deux rendus
  - REPRO_BY_SEASON                : proxy saisonnier d'organe (pont snapshot)
  - SECTEURS_MAQ, SAISON_WEEK_MAQ, SAISONS_ORDRE, MAQ_SPECIES, _grow_sector
                                     : scène partagée avec export_structure
"""
from .apercu import render
from .organes import REPRO_BY_SEASON
from .secteurs import (render_maquette, SECTEURS_MAQ, SAISON_WEEK_MAQ,
                       SAISONS_ORDRE, MAQ_SPECIES, _grow_sector)

__all__ = ["render", "render_maquette", "REPRO_BY_SEASON", "SECTEURS_MAQ",
           "SAISON_WEEK_MAQ", "SAISONS_ORDRE", "MAQ_SPECIES", "_grow_sector"]
