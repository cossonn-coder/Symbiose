# SYMBIOSE — tools/jardinier_auto/execution.py
# Étape 5 de la boucle (§3.5) : traduire un geste choisi en appel `sim.actions`.
# C'est la SEULE surface où l'automate touche le monde, et elle passe par les
# MÊMES fonctions que le joueur (philo #2 : aucune API privilégiée « soigner cette
# plante »). La vue Godot verra simplement leurs effets dans le snapshot suivant.
#
# Tronçon ① : deux verbes câblés — `arroser` (milieu, plot-foyer) et `recolter`
# (vivant, la plante). Les autres verbes de la table §5 arrivent au ②.
#
# NOTE budget : au ① le profil est LIBRE (paie_vigueur=False) mais les gestes de
# `sim.actions` dépensent TOUJOURS la Vigueur en interne et REFUSENT si le solde
# ne couvre pas le coût. On ne court-circuite rien ici : on rapporte fidèlement le
# résultat. Le vrai bridage/déblocage (respect de `gestes_debloques`, budget)
# est câblé au tronçon ③.

from __future__ import annotations

from sim import actions as ACT


def executer(game_state: dict, player: str, eco, plant, regle) -> str:
    """Joue le `verbe` de `regle` sur `plant` (ou son plot). Renvoie un résultat
    normalisé pour la trace : "ok" | "tronque" | "echec".
    `arroser` (bool) : True → "ok", False → "echec" (Vigueur insuffisante).
    `recolter` (ratio ∈ [0,1]) : 1 → "ok", 0 → "echec", entre-deux → "tronque"."""
    if regle.verbe == "arroser":
        r, c = plant.position
        ok = ACT.arroser(game_state, player, eco, r, c)
        return "ok" if ok else "echec"

    if regle.verbe == "recolter":
        ratio = ACT.recolter(game_state, player, plant, eco)
        if ratio >= 1.0:
            return "ok"
        if ratio <= 0.0:
            return "echec"
        return "tronque"

    # Défensif : un verbe non câblé ne doit jamais atteindre cette fonction en ①
    # (regles.py n'en émet que deux). Signale l'incohérence sans muter le monde.
    raise ValueError(f"verbe non câblé au tronçon ① : {regle.verbe!r}")
