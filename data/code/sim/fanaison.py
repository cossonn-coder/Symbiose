"""
SYMBIOSE — sim/fanaison.py
« Elle a fleuri mais n'a presque rien grainé » (D139 caractères vivants ⑤,
conception §6 : le signe de la fécondation faible).

À la fanaison, le moteur fige `plant.fecondation = a + (1 − a)·g(pollen reçu)`
(`sim/engine/decompo.feconder`) ; la mise en graine la lit jusqu'à la récolte
d'automne, puis elle retombe à 0. Ce module en fait un SIGNE et une NOTE, sans
rien calculer de neuf :

  - `sans_graines(plant)` : la plante a fleuri (fécondation posée, > 0) mais
    presque aucun ovule n'a été fécondé (sous `SEUIL_SANS_GRAINES`). Source UNIQUE,
    lue par le pont (signe par plante) ET par la note du carnet ;
  - `noter_fanaisons(game_state, notees)` : HORS TICK (le pont l'appelle après le
    tick, avant `consigner`), rend les lignes de log à ajouter — une par ESPÈCE et
    par ANNÉE, sinon quarante trèfles rempliraient le carnet du même constat ;
  - la LIGNE DE LOG (`ligne_fanaison` / `lire_fanaison`) : écrite et relue ici
    (patron `sim/gout.py`, `sim/lignee.py`), le format ne peut pas diverger.

📖 Pourquoi ce seuil ? Une plante sans aucun butineur garde sa part autofécondée
`a` (≈ 0,15 chez une allogame entomophile, 0,05 chez une anémophile) : sa
fécondation plafonne à `a`. Sous 0,35, moins d'un ovule sur trois a trouvé du
pollen — ce qu'un jardinier voit comme « des fleurs fanées sans graines ».
Une autogame stricte (mode `self`) vaut 1 : elle ne montre jamais ce signe.

Module PUR (aucun RNG) ; la seule écriture est le dict `notees` que l'appelant
possède. Le golden ne le voit pas : il tourne sans serveur, rien ne l'appelle.
"""
from __future__ import annotations

import re

# Sous cette fécondation, la plante a « fleuri pour rien » (presque pas de graines).
SEUIL_SANS_GRAINES = 0.35

# Causes du ledger : la note dit le constat, le palier dit la raison — qui n'est pas
# la même chez une fleur à insectes (peu de butineurs) et chez une anémophile (aulne,
# bouleau, graminées : trop peu de pollen porté par le vent, congénères trop loin).
CAUSE = "sans_graines"
CAUSE_VENT = "sans_graines_vent"


def cause(plant) -> str:
    return CAUSE_VENT if plant.plant_class.pollination_mode == "wind" else CAUSE


# Semaines par année du calendrier moteur (1 an = 52 semaines, `calendrier.py`).
_SEMAINES_AN = 52


def sans_graines(plant) -> bool:
    """La plante a-t-elle fané en ne nouant presque rien ? `fecondation == 0` =
    pas fleurie cette année (ou déjà consommée) : pas de signe."""
    return 0.0 < plant.fecondation < SEUIL_SANS_GRAINES


# --- Ligne de log -------------------------------------------------------------
# `  🥀 Fané sans graines [T0] @(3, 4) : Bourrache, sans_graines`
# Tuile DANS la ligne (écrite hors tick, avant les en-têtes du tick suivant), espèce
# = nom affiché (`plant.name`, comme les lignes du tick ; `evenements` le retraduit).
MARQUEUR = "🥀"
_RE_FANAISON = re.compile(
    r"🥀 Fané sans graines \[([^\]]*)\] @\((\d+), (\d+)\) : (.+), ([a-z_]+)\s*$")


def ligne_fanaison(tile_id, r: int, c: int, nom: str, cause_: str) -> str:
    return f"  {MARQUEUR} Fané sans graines [{tile_id}] @({r}, {c}) : {nom}, {cause_}"


def lire_fanaison(line: str):
    """(tile_id, (r, c), nom affiché, cause) d'une ligne de fanaison, sinon None."""
    if MARQUEUR not in line:
        return None
    m = _RE_FANAISON.search(line)
    if not m:
        return None
    return (m.group(1), (int(m.group(2)), int(m.group(3))), m.group(4), m.group(5))


def noter_fanaisons(game_state: dict, notees: dict) -> list[str]:
    """Lignes à ajouter au log du tick : la PREMIÈRE plante de chaque espèce qui
    montre le signe cette année. `notees` = {nom d'espèce: année déjà notée},
    possédé par l'appelant (le serveur). Ordre déterministe (tuiles puis plantes)."""
    annee = (game_state.get("week", 1) - 1) // _SEMAINES_AN
    lignes = []
    for tile in game_state.get("tiles") or ():
        for p in tile.plants:
            if not p.is_alive or notees.get(p.name) == annee or not sans_graines(p):
                continue
            notees[p.name] = annee
            lignes.append(ligne_fanaison(tile.tile_id, *p.position, p.name, cause(p)))
    return lignes
