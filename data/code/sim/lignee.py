"""
SYMBIOSE — sim/lignee.py
La LIGNÉE vue par les voix (D139, sprint génétique infinitésimale ④).

Le moteur porte, par plante et par graine, une consanguinité `F` (② : 0 = issue
d'un croisement, → 1 = lignée fixée par autofécondations répétées). Ce module en
fait un VOCABULAIRE partagé, sans rien calculer de neuf :

  - `categorie(F)` : trois mots — « fixée », « en voie de fixation », « mélangée ».
    Seuils UNIQUES, lus par le carnet (cause de la note) ET par la vue (le pont les
    exporte au snapshot ; le survol G les relit, il ne les recopie pas) ;
  - la LIGNE DE LOG du ressemis (`ligne_semis` / `lire_semis`) : quand le joueur
    sème une graine qu'il a lui-même récoltée, `planter` écrit une ligne dans le
    canal existant `game_state["log"]` ; `evenements` (carnet) et
    `maitrise_detection` (palier du concept « lignée ») la relisent. Écrire et lire
    au même endroit : le format ne peut pas diverger.

📖 Pourquoi un module à part ? `planter` (sim/actions), `evenements`,
`maitrise_detection` et le pont en ont besoin ; aucun ne doit importer l'autre
(couches). Ici : AUCUN import interne, aucun RNG, aucun effet de bord. Le golden ne
voit rien (le smoke ne sème pas de graine récoltée, et sans clé `log` hors serveur
la ligne n'est jamais écrite).
"""
from __future__ import annotations

import re

# Concept de maîtrise / d'encyclopédie (accentué comme « lumière », « météo »).
CONCEPT = "lignée"

# Seuils de lecture de F (kickoff ④). Au-dessus de 0,75, plus des trois quarts des
# gènes sont en double exemplaire identique : les frères se ressemblent. Sous 0,25,
# la lignée reste brassée.
SEUIL_FIXEE = 0.75
SEUIL_MELANGEE = 0.25

# Causes du carnet (clé ASCII, comme les autres causes du ledger).
FIXEE, EN_VOIE, MELANGEE = "fixee", "en_voie", "melangee"


def categorie(F: float) -> str:
    """Catégorie de lignée d'une consanguinité F (cause du carnet)."""
    if F >= SEUIL_FIXEE:
        return FIXEE
    if F <= SEUIL_MELANGEE:
        return MELANGEE
    return EN_VOIE


# --- Ligne de log du ressemis ------------------------------------------------
# `  🫘 Ressemis de ma récolte [T0] @(3, 4) : tomate, fixee`
# La tuile est DANS la ligne (pas d'en-tête `[T0]` : la ligne est écrite hors tick,
# avant les en-têtes du tick suivant). L'espèce est la clé du catalogue.
MARQUEUR = "🫘"
_RE_SEMIS = re.compile(r"🫘 Ressemis de ma récolte \[([^\]]+)\] @\((\d+), (\d+)\) : "
                       r"([a-z_]+), ([a-z_]+)")


def ligne_semis(tile_id: str, r: int, c: int, espece: str, F: float) -> str:
    """La ligne que `planter` écrit quand la graine semée vient de la récolte."""
    return (f"  {MARQUEUR} Ressemis de ma récolte [{tile_id}] @({r}, {c}) : "
            f"{espece}, {categorie(F)}")


def lire_semis(line: str):
    """(tile_id, (r, c), espece, cause) d'une ligne de ressemis, sinon None."""
    if MARQUEUR not in line:
        return None
    m = _RE_SEMIS.search(line)
    if not m:
        return None
    return (m.group(1), (int(m.group(2)), int(m.group(3))), m.group(4), m.group(5))
