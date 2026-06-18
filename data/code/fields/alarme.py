"""
SYMBIOSE — fields/alarme.py
Phéromone d'alarme apienne (arc pollinisation ⑦, CONCEPTION §J — couche joueur).

§J FIGÉ : la piqûre n'est PAS une pénalité forfaitaire en dur, mais une RÉACTION
ÉMERGENTE (philo #1+#2). Une action directe coûteuse — **écraser une abeille** ou
**récolter du miel sans équipement** (§I.2) — libère une **phéromone d'alarme**
LOCALE au point d'action. Tant qu'elle est active, les abeilles présentes dans le
rayon **piquent le curseur** : chaque piqûre coûte de la Vigueur joueur + ajoute de
la perturbation locale (la guilde se replie).

PARTAGE DES RÔLES (§J.3) : ce module est la PART MOTEUR — il ne fait que POSER et
FAIRE DÉCROÎTRE le signal spatial (`eco.alarme`, un GridField transitoire), et
l'exposer au snapshot. La PIQÛRE elle-même (réaction temps réel au curseur, coût
Vigueur, atténuation par l'équipement apicole) est **temps réel côté Godot**, qui
lit l'alarme + la densité `abeille` du snapshot. Le moteur ne touche donc NI la
Vigueur NI la perturbation ici : l'alarme est un PUR PUITS lu par la vue.

Module PURE & déterministe, duck-typé sur `eco` (miroir de `fields/apiculture.py`,
`fields/foragers.py`, `fields/lifecycle.py` — garde-fou taille : on ne gonfle pas
`container.py`). Aucun import de `sim`, aucun RNG, aucun log → aucun cycle de couche
(`plants ← fields ← sim` : `sim/actions` appelle `declencher_alarme`, jamais l'inverse).

**Golden NEUTRE** (§J.4) : le smoke n'écrase aucune abeille et ne récolte aucun miel
→ l'alarme reste à 0 partout. Et même active, l'alarme n'est lue QUE par le snapshot
(jamais réinjectée dans un champ figé du golden) → elle ne peut pas dériver le tick.
"""
from __future__ import annotations

# Paramètres d'alarme — PLACEHOLDERS NOMMÉS, calibrage post-test (n'affectent ni le
# golden, neutre, ni le déterminisme). La phéromone est un signal FUGACE : dépôt
# plein à l'action, demi-vie d'une semaine simulée (côté moteur ; Godot anime la
# décroissance fine en temps réel par-dessus).
ALARME_DEPOT = 1.0     # intensité déposée par déclenchement (écraser / récolte nue)
ALARME_DECAY = 0.5     # facteur multiplicatif hebdo (≈ demi-vie 1 semaine)
ALARME_FLOOR = 0.01    # en-dessous, on remet à 0 (garde la liste snapshot creuse)


def declencher_alarme(eco, r: int, c: int, intensite: float = ALARME_DEPOT) -> None:
    """Pose une phéromone d'alarme au plot (r,c) — point d'entrée UNIQUE pour les
    déclencheurs joueur (`sim.actions.ecraser` sur une abeille, `recolter_miel` sans
    équipement). Cumulatif (`GridField.add`, déjà borné [0, max_val]) : deux gestes
    rapprochés renforcent le foyer. No-op si `intensite ≤ 0` ou plot hors tuile, et
    dégradation gracieuse si le champ n'existe pas (`getattr`)."""
    field = getattr(eco, "alarme", None)
    if field is None or intensite <= 0.0:
        return
    if 0 <= r < eco.rows and 0 <= c < eco.cols:
        field.add(r, c, intensite)


def tick_alarme(eco) -> None:
    """Décroissance hebdomadaire de la phéromone d'alarme (§J.1 : « terme transitoire
    qui décroît dans le temps »). Multiplie chaque foyer actif par `ALARME_DECAY` et
    le SNAPPE à 0 sous `ALARME_FLOOR` (la liste snapshot reste creuse). Ne touche que
    les cellules > 0 → no-op de fait quand aucune alarme n'est posée (golden §J.4).

    Pur, déterministe, zéro RNG. Écrit UNIQUEMENT `eco.alarme` (jamais un champ du
    golden) → ne peut pas dériver le tick déterministe."""
    field = getattr(eco, "alarme", None)
    if field is None:
        return
    data = field.data
    for r in range(eco.rows):
        row = data[r]
        for c in range(eco.cols):
            v = row[c]
            if v > 0.0:
                v *= ALARME_DECAY
                row[c] = v if v >= ALARME_FLOOR else 0.0
