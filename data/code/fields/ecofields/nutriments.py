"""
SYMBIOSE — fields/ecofields/nutriments.py
Chimie des nutriments du sol : helpers PURS de la loi du minimum de Liebig
(azote n / phosphore p / potasse k), isolés de `container.py` (déjà le fichier le
plus dense du dépôt), façon `ph.py`/`thermique.py` — le conteneur délègue ici.

Fonctions pures, zéro RNG, zéro log, aucune mutation cachée (déterminisme philo #3).
Trois services au cœur du re-figé du tronçon ③ :

  1. `split_miner(tissu, amount)` — répartit une quantité MINÉRALISÉE en (N, P, K)
     selon le tissu décomposé (`NPK_RELEASE`). La litière feuillue nourrit surtout
     l'azote, le bois capte peu, le fruit donne de la potasse. Les compartiments
     humifiés (om_active/om_stable, sans tissu) passent par la clé `"humus"`.

  2. `cec_norm_at(soil_type, om_stable_norm)` — capacité d'échange cationique
     DÉRIVÉE (texture + humus), bornée [0,1]. Un sol argilo-humique RETIENT ses
     cations, un sable les laisse filer.

  3. `leach_factor(nutrient, cec_norm)` — facteur multiplicatif de lessivage
     hebdomadaire d'un nutriment, modulé par la CEC : N très mobile, P quasi nul,
     K moyen. Remplace le `LEACHING_LOSS` unique.

La loi de Liebig elle-même (le `min` des disponibilités) n'a pas besoin d'helper :
elle se lit directement sur les trois champs (cf. `vigueur_plante.qi_local`). Le
conteneur expose un index dérivé LISSE (`fertilite_index`, moyenne des trois) pour
les lecteurs qui veulent une grandeur stable (soil_memory, vitalité, succession) —
distinct du `min` instantané que ressent la croissance/Vigueur.
"""

from __future__ import annotations

from math import exp

from .constants import (NPK_RELEASE, LEACHING, CEC_PAR_SOL, CEC_OM_COEF,
                        PH_OPT, PH_WIDTH)


def dispo(ph: float, nut: str) -> float:
    """Disponibilité en cloche d'un nutriment (ou de l'activité microbienne) au pH
    local : `exp(−((ph − PH_OPT[nut])/PH_WIDTH[nut])²)` ∈ ]0,1] (tronçon ④, lockout).

    Pic à 1.0 quand `ph == PH_OPT[nut]`, décroît en gaussienne de part et d'autre.
    `nut ∈ {"N","P","K","micro"}`. Le phosphore (width étroite) est bloqué des deux
    côtés ; l'azote (large) reste disponible sur une large plage. C'est un FLUX de
    disponibilité, jamais un gate de croissance (philo #2)."""
    return exp(-((ph - PH_OPT[nut]) / PH_WIDTH[nut]) ** 2)


def split_miner(tissu: str, amount: float) -> tuple[float, float, float]:
    """(dN, dP, dK) issus d'une quantité minéralisée `amount` d'un `tissu` donné.
    Tissu inconnu → repli sur `humus` (mélange om_active/stable). La somme des
    ratios pouvant être < 1 (cf. `bois`), une part du minéral peut n'être captée
    par aucun nutriment (perte assumée — immobilisation)."""
    r = NPK_RELEASE.get(tissu, NPK_RELEASE["humus"])
    return amount * r["N"], amount * r["P"], amount * r["K"]


def cec_norm_at(soil_type: str, om_stable_norm: float) -> float:
    """CEC normalisée [0,1] d'un plot : socle texture (`CEC_PAR_SOL`) + humus
    (`om_stable` normalisé × `CEC_OM_COEF`). `om_stable_norm` attendu déjà borné
    [0,1] par l'appelant (cohérent avec la normalisation /5.0 de `vitalite`)."""
    cec = CEC_PAR_SOL.get(soil_type, CEC_PAR_SOL["terre"]) + CEC_OM_COEF * om_stable_norm
    return min(1.0, cec)


def leach_factor(nutrient: str, cec_norm: float) -> float:
    """Facteur multiplicatif de rétention après lessivage d'un nutriment ce tick :
    `1 − LEACHING[i]·(1 − cec_norm)`. À CEC pleine (1.0) → 1.0 (rien ne lessive) ;
    à CEC nulle → 1 − LEACHING[i] (lessivage maximal). `champ_i *= ce_facteur`."""
    return 1.0 - LEACHING[nutrient] * (1.0 - cec_norm)
