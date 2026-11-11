"""
SYMBIOSE — world/support.py
Structures-support de GRIMPE posables (D49 volet A, CONCEPTION_GRIMPANTES §4).
Un `Support` est un obstacle vertical NEUF (position + hauteur) auquel une plante
grimpante compatible peut s'accrocher pour monter — patron des bac/pile posables.

⚠️ À NE PAS confondre avec `StakeSlot` (world/tile.py) : celui-ci est le
porte-RONDELLES du système MTG (aucune position, aucune hauteur). Le `Support`
de grimpe est une donnée spatiale à part entière.

DONNÉE + helper PUR (couche `world`). La recherche d'accroche et le biais de
grimpe vivent dans `sim` (sim/grimpe.py) : ici, rien qui tourne au tick.
"""

from __future__ import annotations
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Compatibilité mode de grimpe × support (helper pur, testable)
# ---------------------------------------------------------------------------

# Sentinelle du mur maison : ce n'est PAS un `Support` posable (il vit dans
# `world/building.py`), mais la table de compatibilité le traite comme un type de
# support « surface » à part.
MUR = "mur"

# Sentinelle de la plante-hôte VIVANTE (tronçon ③) : une grimpante peut prendre
# appui sur une voisine plus haute comme sur un support inerte. Ce n'est pas non
# plus un `Support` posable (l'hôte est une `PlantInstance`), juste un type de prise
# reconnu par la table de compatibilité — une tige vivante offre une prise à ce qui
# s'enroule (vrille_volubile) ou s'agrippe (crampon), jamais au sarmenteux (nu).
HOTE = "hote"

# Table §4 : quels supports chaque mode de grimpe peut saisir AUTOMATIQUEMENT (au
# tick, tronçon ②/③). Le `sarmenteux` n'accroche RIEN seul — il faut le geste
# `palisser` (tronçon ④) ; il n'apparaît donc dans aucune entrée automatique.
_COMPATIBILITE: dict[str, frozenset[str]] = {
    # crampon (lierre) : s'agrippe à toute surface, mur nu compris (espalier) ; une
    # tige d'hôte vivant lui offre aussi une prise (crampons sur l'écorce).
    "crampon": frozenset({MUR, HOTE, "tuteur", "treillis", "pergola"}),
    # vrille_volubile (haricot) : enroule sa vrille sur un appui fin ou une grille,
    # mais GLISSE sur le mur nu (rien à enrouler) → mur EXCLU. Une tige d'hôte
    # vivant, elle, est un appui fin idéal à enrouler → HOTE inclus.
    "vrille_volubile": frozenset({HOTE, "tuteur", "treillis", "pergola"}),
    # sarmenteux (jasmin) : longues cannes sans organe d'accroche → aucune saisie
    # automatique. Attaché seulement à la main (`palisser`, ④).
    "sarmenteux": frozenset(),
}


def support_compatible(mode_grimpe: str | None, support_type: str) -> bool:
    """Vrai si une grimpante de mode `mode_grimpe` peut s'accrocher AUTOMATIQUEMENT
    à un support de type `support_type` (l'un des trois types de `Support`, ou la
    sentinelle `MUR`, ou `HOTE` pour une plante-hôte vivante — ③). Pure,
    déterministe (philo #3). Un `mode_grimpe` None (non-grimpante) ⇒ False : aucune
    non-grimpante ne s'accroche jamais."""
    if mode_grimpe is None:
        return False
    return support_type in _COMPATIBILITE.get(mode_grimpe, frozenset())


# Relais d'appui (sprint HOUPPIER ②, `sim/grimpe.relais_appui`) : une liane DÉJÀ accrochée
# dont la tige dépasse son appui en cherche un autre. Le sarmenteux n'a pas d'organe
# d'accroche, mais ses cannes s'appuient sur ce qu'elles rencontrent : structures et
# plantes. Le mur nu ne lui offre rien, il reste au geste `palisser`.
_RELAIS_SARMENTEUX = frozenset({HOTE, "tuteur", "treillis", "pergola"})


def relais_compatible(mode_grimpe: str | None, support_type: str) -> bool:
    """Comme `support_compatible`, pour le relais : seul le sarmenteux y diffère."""
    if mode_grimpe == "sarmenteux":
        return support_type in _RELAIS_SARMENTEUX
    return support_compatible(mode_grimpe, support_type)


# ---------------------------------------------------------------------------
# Structure-support posable
# ---------------------------------------------------------------------------

@dataclass
class Support:
    """Support de grimpe posé dans une tuile (repère TUILE-local, en cm — même
    convention que `PlantInstance.x_cm/y_cm`). `height_cm` = hauteur d'appui
    maximale. `finesse` ∈ {"fin","surface"} qualifie la prise (pieu fin vs grille
    ou paroi) — INERTE au tronçon ② (aucun consommateur ne le lit encore ; la
    pergola occulteuse et le rendu le liront plus tard)."""
    support_type: str            # "tuteur" | "treillis" | "pergola" | "perchoir" (zoochorie ④)
    x_cm: float
    y_cm: float
    height_cm: float
    finesse: str = "fin"         # "fin" | "surface"
