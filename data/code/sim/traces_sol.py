"""
SYMBIOSE — sim/traces_sol.py
Registre des TRACES DE GESTES au sol (sprint GESTES LISIBLES ①, conception
`docs/joueur/gestes/conception_gestes_lisibles.md` §3.1).

Le sol est un CANVAS : un geste payé y laisse un souvenir visible (mottes
retournées, empreinte de botte, auréole mouillée…) qui s'estompe avec les
semaines. Règle cardinale (D3, Nico) : **la vue n'invente rien** — elle ne dessine
une trace que si ce registre la porte. C'est donc ici, côté moteur, que vit la
liste des traces ; la vue n'en est que la lectrice (export au pont).

Ce que ce module N'EST PAS : un effet écologique. Une trace est un SOUVENIR de
geste, pas une cause (philo #1/#2) : aucun champ du sol n'est lu ni écrit ici, le
tick ne lit jamais le registre. Les conséquences réelles du geste (structure du
sol, humidité, altitude…) restent écrites par les façades `sim/actions`.

État : `game_state["traces_sol"]` = liste d'entrées
`{tuile, r, c, x_cm, y_cm, sorte, semaine}` (JSON-sérialisable, sauvée avec le
profil). Créée PARESSEUSEMENT par la première écriture — jamais par une lecture :
le smoke du golden n'a pas de joueur, la clé n'y apparaît donc jamais.

Purge (expiration + plafond FIFO) à l'écriture et à l'export, **jamais dans le
tick** → golden neutre par construction. Déterministe : l'âge se compte en
semaines simulées (`game_state["week"]`), zéro RNG (philo #3).
"""
from __future__ import annotations

# Durée de vie d'une trace par SORTE, en semaines simulées (table §3.1 — calibrage
# F5). Une seule table data-driven : la sorte est la clé, la vue choisit l'aspect
# (mottes, raies, botte, voile, auréole, rebord) à partir du même nom.
DUREE_SEMAINES: dict[str, int] = {
    "becher":     6,   # mottes retournées, terre sombre et grumeleuse
    "grelinette": 4,   # raies parallèles d'aération, terre claire ameublie
    "pas":        2,   # empreinte de botte (ecraser)
    "epandre":    4,   # voile de compost brun foncé
    "arroser":    1,   # auréole de terre mouillée
    "creuser":    6,   # rebord de terre rejetée autour de la cuvette
}

# Quel geste laisse quelle sorte de trace. `ecraser` laisse un PAS (qu'il vise une
# bête ou une plante) ; les autres portent le nom de leur geste.
SORTE_DU_VERBE: dict[str, str] = {
    "becher": "becher", "grelinette": "grelinette", "ecraser": "pas",
    "epandre": "epandre", "arroser": "arroser", "creuser": "creuser",
}

# Plafond du registre (FIFO : les plus anciennes partent d'abord). Borne la taille
# du save et le coût de l'export, même pour un joueur frénétique.
PLAFOND_TRACES = 400


def _vivante(trace: dict, semaine: int) -> bool:
    """Une trace est encore visible tant que son âge n'atteint pas sa durée."""
    return semaine - trace["semaine"] < DUREE_SEMAINES.get(trace["sorte"], 0)


def purger(game_state: dict) -> None:
    """Retire les traces expirées puis applique le plafond FIFO. No-op si le
    registre n'existe pas (on ne le crée jamais en purgeant)."""
    traces = game_state.get("traces_sol")
    if traces is None:
        return
    semaine = game_state.get("week", 0)
    vivantes = [t for t in traces if _vivante(t, semaine)]
    traces[:] = vivantes[-PLAFOND_TRACES:]


def ecrire_trace(game_state: dict, tuile: str, r: int, c: int,
                 x_cm: float, y_cm: float, sorte: str) -> None:
    """Note la trace d'un geste APPLIQUÉ (payé) au point cliqué. Appelée hors tick,
    par le pont, après le geste. Crée le registre au premier appel."""
    if sorte not in DUREE_SEMAINES:
        raise ValueError(f"sorte de trace inconnue : {sorte!r}")
    traces = game_state.setdefault("traces_sol", [])
    traces.append({"tuile": tuile, "r": r, "c": c,
                   "x_cm": round(float(x_cm), 1), "y_cm": round(float(y_cm), 1),
                   "sorte": sorte, "semaine": game_state.get("week", 0)})
    purger(game_state)


def traces_par_tuile(game_state: dict) -> dict:
    """Lecture pour l'export : `{tuile: [[r, c, x_cm, y_cm, sorte, age], …]}` (liste
    creuse, seules les tuiles marquées apparaissent), âge en semaines (la vue
    estompe). Purge d'abord ; registre absent → `{}` sans le créer."""
    purger(game_state)
    semaine = game_state.get("week", 0)
    out: dict[str, list] = {}
    for t in game_state.get("traces_sol") or ():
        out.setdefault(t["tuile"], []).append(
            [t["r"], t["c"], t["x_cm"], t["y_cm"], t["sorte"],
             semaine - t["semaine"]])
    return out
