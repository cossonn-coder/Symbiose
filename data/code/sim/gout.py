"""
SYMBIOSE — sim/gout.py
Le GOÛT d'un organe mangé par le jardinier (D139 caractères vivants ②, conception §2.2).

Deux caractères héritables, organe par organe : `appetence_feuille` et
`appetence_fruit`, ∈ [−1, 1]. Ce module en fait la VALEUR d'une bouchée et la NOTE
du carnet, sans rien calculer d'autre :

  - `valeur_bouchee(base, appetence, perte_ref)` : un organe savoureux nourrit mieux
    (`base × (1 + a)`), un organe amer nourrit moins ; SOUS le seuil de toxicité
    (`SEUIL_TOXIQUE`), la bouchée ne nourrit plus du tout, elle RETIRE de la Vigueur,
    en proportion de |a| (dette D31/D19 : valeur nutritive SIGNÉE par organe).
    Le geste `manger` reste GRATUIT : c'est l'organe qui a une valeur négative ;
  - `cause(organe, a)` : ce que le carnet retient de la bouchée (amère ou toxique ;
    une bouchée bonne ne laisse pas de note, elle se sent dans la Vigueur) ;
  - la LIGNE DE LOG (`ligne_gout` / `lire_gout`) : `manger` l'écrit dans le canal
    `game_state["log"]` (absent hors serveur → rien), `evenements` la relit pour le
    ledger du carnet. Écrire et lire au même endroit : le format ne peut pas diverger
    (patron `sim/lignee.py`).

📖 Pourquoi un seuil ? Une feuille un peu amère reste mangeable (on en tire moins) ;
au-delà d'une dose, la plante se défend chimiquement (solanine de la tomate,
saponines du lierre) et c'est le corps qui paie. Le joueur l'apprend en goûtant
(philo #6), le carnet le note.

Module PUR : aucun import interne, aucun RNG, aucun effet de bord. Hors tick → le
golden ne le voit pas (le smoke ne mange rien).
"""
from __future__ import annotations

import re

# Concept du carnet (propre au carnet, comme « maladie ») : ce qu'on mange.
CONCEPT = "comestibilité"

# Sous ce goût, l'organe est TOXIQUE pour le jardinier : la bouchée coûte.
SEUIL_TOXIQUE = -0.3
# Perte d'une bouchée de goût −1 = cette fraction de la valeur d'un organe mûr
# (`perte_ref`, `HARVEST_GAIN_FULL` côté gestes). Placeholder, calibrage F5 : une
# feuille de tomate (−0,6) coûte ≈ 4,5 de Vigueur, une baie de lierre (−0,8) ≈ 6 —
# moins qu'une demi-semaine de repos, assez pour qu'on s'en souvienne.
PERTE_TOXIQUE = 0.5

FEUILLE, FRUIT = "feuille", "fruit"
AMER, TOXIQUE = "amer", "toxique"


def valeur_bouchee(base: float, appetence: float, perte_ref: float) -> float:
    """Valeur SIGNÉE d'une bouchée. `base` = ce que l'organe nourrit à goût neutre
    (≥ 0) ; `appetence` ∈ [−1, 1]. Toxique → `−PERTE_TOXIQUE × perte_ref × |a|`
    (la maturité n'y change rien : la plante se défend à tout âge)."""
    if appetence < SEUIL_TOXIQUE:
        return -PERTE_TOXIQUE * perte_ref * abs(appetence)
    return base * (1.0 + appetence)


def cause(organe: str, appetence: float) -> str | None:
    """Cause de la note du carnet (`toxique_feuille`, `amer_fruit`…), ou None pour
    une bouchée sans amertume (rien à noter)."""
    if appetence < SEUIL_TOXIQUE:
        return f"{TOXIQUE}_{organe}"
    if appetence < 0.0:
        return f"{AMER}_{organe}"
    return None


# --- Ligne de log de la bouchée ------------------------------------------------
# `  👅 Goûté [T0] @(3, 4) : Tomate, toxique_feuille`
# La tuile est DANS la ligne (écrite hors tick, avant les en-têtes du tick suivant).
# L'espèce est son NOM affiché (`plant.name`, comme les lignes du tick) : le lecteur
# la retraduit en clé de catalogue (`evenements._CLE_DE_NOM`).
MARQUEUR = "👅"
_RE_GOUT = re.compile(r"👅 Goûté \[([^\]]*)\] @\((\d+), (\d+)\) : (.+), ([a-z_]+)\s*$")


def ligne_gout(tile_id, r: int, c: int, nom: str, cause_: str) -> str:
    """La ligne que `manger` écrit quand la bouchée était amère ou toxique."""
    return f"  {MARQUEUR} Goûté [{tile_id}] @({r}, {c}) : {nom}, {cause_}"


def lire_gout(line: str):
    """(tile_id, (r, c), nom affiché, cause) d'une ligne de goût, sinon None."""
    if MARQUEUR not in line:
        return None
    m = _RE_GOUT.search(line)
    if not m:
        return None
    return (m.group(1), (int(m.group(2)), int(m.group(3))), m.group(4), m.group(5))
