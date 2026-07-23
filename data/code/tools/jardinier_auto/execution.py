# SYMBIOSE — tools/jardinier_auto/execution.py
# Étape 5 de la boucle (§3.5) : traduire un `Plan` décidé en appel `sim.actions`.
# C'est la SEULE surface où l'automate touche le monde, et elle passe par les MÊMES
# fonctions que le joueur (philo #2 : aucune API privilégiée « soigner cette
# plante »). La vue Godot verra simplement leurs effets dans le snapshot suivant.
#
# Tronçon ② : toute la table §5 est câblée — arroser, recolter, pailler, broyer,
# recolter_paille, deraciner, tailler, grelinette. Chaque verbe renvoie un résultat
# NORMALISÉ pour la trace : "ok" | "tronque" | "echec".
#
# NOTE budget : le budget de Vigueur (coupe des gestes qui ne rentrent pas) est géré
# EN AMONT par la boucle (mode paie_vigueur). Ici on exécute et on rapporte
# fidèlement : les gestes `sim.actions` dépensent la Vigueur en interne et REFUSENT
# si le solde ne couvre pas — un "echec" reflète ce refus. Le respect fin de
# `gestes_debloques` (verrouillage par maîtrise) est câblé au ③.

from __future__ import annotations

from sim import actions as ACT
from sim.magazine import acheter_au_magazine


def _ratio(r: float) -> str:
    """Normalise un ratio d'effort ∈ [0,1] en résultat de trace."""
    if r >= 1.0:
        return "ok"
    if r <= 0.0:
        return "echec"
    return "tronque"


def executer(game_state: dict, player: str, eco, plant, plan) -> str:
    """Joue le `verbe` du `plan`. `plant` = la cultivée en cours ; `plan.cible_obj` =
    la plante visée pour un geste sur le vivant (deraciner/tailler/broyer/
    recolter_paille). Renvoie "ok" | "tronque" | "echec"."""
    v = plan.verbe
    if v == "arroser":
        r, c = plant.position
        return "ok" if ACT.arroser(game_state, player, eco, r, c) else "echec"

    if v == "pailler":
        r, c = plant.position
        ok = ACT.pailler(game_state, player, eco, r, c, nature=plan.nature)
        return "ok" if ok else "echec"

    if v == "glaner":
        # Canal 1 de ravitaillement (moyens d'agir ③) : ramasse la litière tendre du
        # plot-foyer de `plant` → stock `feuilles`. >0 = de la matière a été glanée.
        r, c = plant.position
        return "ok" if ACT.glaner(game_state, player, eco, r, c) > 0.0 else "echec"

    if v == "recolter":
        return _ratio(ACT.recolter(game_state, player, plant, eco))

    if v == "broyer":
        # GRADUÉ : crédit de BRF ∝ effort. >0 = du bois a été broyé (ravitaillement).
        return "ok" if ACT.broyer(game_state, player, plan.cible_obj, eco) > 0.0 else "echec"

    if v == "recolter_paille":
        return "ok" if ACT.recolter_paille(game_state, player, plan.cible_obj, eco) > 0.0 else "echec"

    if v == "grelinette":
        r, c = plant.position
        return "ok" if ACT.grelinette(game_state, player, eco, r, c) else "echec"

    if v == "deraciner":
        return "ok" if ACT.deraciner(game_state, player, plan.cible_obj, eco) else "echec"

    if v == "tailler":
        # Écimage de l'apex meneur du voisin ombrageant (réponse ÉMERGENTE, philo #2).
        return "ok" if ACT.tailler(game_state, player, plan.cible_obj, eco, cible="apex") else "echec"

    # --- Gestes CRÉATIFS (③) : faire ADVENIR la cible (planification.py). `plant`
    # est None (aucune cultivée en cours) ; la charge vit dans `plan.cible_obj`
    # (CibleCreative espece/tile/r/c). Mêmes fonctions que le joueur (philo #2) : elles
    # dépensent la Vigueur en interne et REFUSENT si le solde ne couvre pas → "echec".
    if v == "planter":
        cr = plan.cible_obj
        return "ok" if ACT.planter(game_state, player, cr.tile, eco,
                                   cr.espece, cr.r, cr.c) else "echec"

    if v == "favoriser_auxiliaire":
        # Habitat auxiliaire posé « au plus tôt » (C4) : rondelle persistante sur la tuile.
        return "ok" if ACT.favoriser_auxiliaire(game_state, player, plan.cible_obj.tile) else "echec"

    if v == "acheter_magazine":
        # Voie n°2 d'acquisition de graine (magazine, palier 3 famille). Sans lieu :
        # écrit UNIQUEMENT l'état joueur (Vigueur + banque), débite COUT_MAGAZINE.
        return "ok" if acheter_au_magazine(game_state, player, plan.cible_obj.espece) else "echec"

    # Défensif : un verbe non câblé ne doit jamais atteindre cette fonction.
    raise ValueError(f"verbe non câblé : {v!r}")
