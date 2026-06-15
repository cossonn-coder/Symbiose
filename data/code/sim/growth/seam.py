"""
SYMBIOSE — sim/growth/seam.py
Seam de perturbation (§F) : l'UNIQUE point d'entrée par lequel quoi que ce soit
abîme la structure (taille, écrasement, grêle…), + la fonction de lignification
(résistance à l'écrasement croissante avec l'âge). Pur structurel, déterministe.
"""

from __future__ import annotations

from .constantes import COUPE_NETTE, LIGNIFICATION_SCALE
from .geometrie import _children, _subtree, _rebuild


def f_lignification(age_weeks: float) -> float:
    """Fraction de lignification ∈ [0,1] (Q4) — croissante bornée de l'âge. Un semis
    (age_weeks ≈ 0) ⇒ ≈ 0 : sa résistance effective est quasi nulle, il s'écrase. Un
    sujet établi (age_weeks ≥ LIGNIFICATION_SCALE) ⇒ 1 : résistance pleine (un tronc
    ne s'écrase pas). Pure, déterministe (zéro RNG)."""
    return min(1.0, max(0.0, age_weeks) / LIGNIFICATION_SCALE)


# ---------------------------------------------------------------------------
# Seam de perturbation §F — point d'entrée UNIQUE de l'altération de structure
# ---------------------------------------------------------------------------

def atteindre_segment(plant, segment_id: int, intensite: float) -> list:
    """Seam de perturbation (CONCEPTION_CROISSANCE §F) — l'UNIQUE point d'entrée par
    lequel quoi que ce soit abîme la structure. Le mécanisme ne sait PAS qui :
    `tailler` aujourd'hui ; grêle / ravageur / vent plus tard appelleront le MÊME
    seam. Pur structurel — couche `sim`, déterministe, zéro RNG, zéro Vigueur.

    `intensite` ∈ [0,1] continue :
      - DOUX (< COUPE_NETTE) : baisse SEULEMENT l'auxine locale → lève l'inhibition
        en aval (modélise notching / courbure). La structure reste intacte ; le
        débourrement local peut SUIVRE au prochain `grow_plant` si l'auxine retombe
        sous AUXIN_INHIB_THRESHOLD — émergent, non codé ici.
      - NET (≥ COUPE_NETTE) : écimage = retrait du segment ciblé ET de tout son
        sous-arbre (décision #2 : segment INCLUS). COLLET PROTÉGÉ : si le segment est
        le collet (`parent is None`) on ne retire rien (la baisse d'auxine suffit ;
        `grow_plant` a déjà le rejet de souche s'il ne reste aucun apex).

    Le seam n'écrit QUE l'ÉTAT (auxine / liste de segments). L'architecture de
    réponse (débourrement des bourgeons survivants) ÉMERGE au tick de croissance
    suivant — c'est tout l'intérêt du découplage (philo #2).

    Retourne la LISTE des segments réellement retirés (décompo·compost ② : la
    matière coupée doit retourner au sol en litière `bois`, option (a) du kickoff).
    `[]` en régime DOUX ou sur le collet protégé → l'appelant ne dépose rien."""
    segs = plant.segments
    seg = segs[segment_id]
    seg.auxin = max(0.0, seg.auxin - intensite)             # douce : lève l'inhibition
    if intensite >= COUPE_NETTE and seg.parent is not None:  # net, hors collet → écimage
        ch = _children(segs)
        kill = _subtree(segment_id, ch)                      # seg INCLUS (décision #2)
        removed = [segs[i] for i in kill]                    # matière coupée → litière (②)
        _rebuild(plant, set(kill))
        return removed
    return []
