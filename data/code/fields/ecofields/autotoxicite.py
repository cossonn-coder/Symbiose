"""
SYMBIOSE — fields/ecofields/autotoxicite.py
Autotoxicité / fatigue du sol : calcul PUR de la MONTÉE saisonnière du champ
`autotox ∈ [0, AUTOTOX_MAX]` (accumulateur d'allélochimiques de la MÊME espèce
émettrice qui ré-occupe un plot sans rotation) et de sa REDESCENTE (rotation /
sol nu / détox microbienne).

Acteur du sprint ALLÉLOPATHIE tronçon ④ (D3, `04_autotoxicite.md`). Isolé de
`container.py` (le fichier le plus dense du dépôt) sur le modèle de
`allelopathie.py`/`mycelium.py` : le conteneur n'expose qu'une fine méthode
`tick_autotoxicite` qui délègue ici. Fonction pure, zéro RNG, zéro log —
déterminisme philo #3.

MODÈLE (cadence SAISONNIÈRE, appelée en fin de saison depuis la boucle) :

    E = espèce ÉMETTRICE (`allelopathie_emission > 0`) qui occupe le plot ce tick
        (position + empreinte racinaire). Aucune / non émettrice → E = None.

    si E is not None et E == autotox_espece[r][c] :        (même espèce récurrente)
        autotox[r,c] += AUTOTOX_MONTEE                      (la monoculture s'empoisonne)
    sinon :                                                 (rotation / sol nu / 1re occupation)
        detox        = AUTOTOX_MICROBE · min(1, microbiome[r,c]/3)
        autotox[r,c] *= (1 − AUTOTOX_REPOS − detox)         (le sol se repose)
    autotox_espece[r][c] = E                                (mémoire de l'occupant émetteur)

`autotox` est LU par l'espèce traceée SEULE, via `EcoFields.allelo_effectif`
(allelopathie + autotox si la plante EST l'émetteur récurrent du plot) → la
fatigue ne frappe QUE l'espèce fatigante (spécificité, rotation = échappatoire).

INVARIANT GOLDEN : tant qu'aucune espèce n'a `allelopathie_emission > 0` (avant
le tronçon ⑤), `emetteur_du_plot` renvoie toujours None → aucune montée, et un
`autotox` déjà nul reste nul (branche `sinon` sur 0 = no-op) → `allelo_effectif
== allelopathie` partout → germination ET croissance STRICTEMENT identiques au
pré-④. La seule dérive golden POSSIBLE est attribuable au traceur — nulle ici.
"""

from __future__ import annotations

from .constants import AUTOTOX_MONTEE, AUTOTOX_REPOS, AUTOTOX_MICROBE


def emetteur_du_plot(plants: list, r: int, c: int):
    """Classe de l'espèce ÉMETTRICE (`allelopathie_emission > 0`) qui occupe le
    plot `(r, c)` — par sa position OU son empreinte racinaire (l'émetteur exsude
    par ses racines, donc il fatigue tout son territoire souterrain). Renvoie la
    `plant_class` (clé stable, hashable) ou None si aucun émetteur vivant n'y est.

    Tie-break déterministe : la PREMIÈRE plante émettrice de la liste (ordre
    d'insertion de `tile.plants`, stable, zéro RNG). Pure lecture. Tant que le
    catalogue n'a aucune espèce émettrice (avant le ⑤), renvoie TOUJOURS None →
    invariant golden (le traceur ne s'arme jamais)."""
    for p in plants:
        if not p.is_alive:
            continue
        if getattr(p.plant_class, "allelopathie_emission", 0.0) <= 0.0:
            continue
        if (r, c) == p.position or (r, c) in p.root_plots:
            return p.plant_class
    return None


def emetteurs_par_plot(plants: list) -> dict:
    """`emetteur_du_plot` pour TOUS les plots d'un coup : plot → `plant_class` de
    la PREMIÈRE plante émettrice vivante (ordre de `plants`) qui l'occupe par sa
    position ou son empreinte racinaire. Plot absent → None (aucun émetteur)."""
    out: dict = {}
    for p in plants:
        if not p.is_alive:
            continue
        if getattr(p.plant_class, "allelopathie_emission", 0.0) <= 0.0:
            continue
        out.setdefault(p.position, p.plant_class)
        for plot in p.root_plots:
            out.setdefault(plot, p.plant_class)
    return out


def tick_autotoxicite(eco, plants: list) -> None:
    """Fait MONTER `eco.autotox` sur les plots ré-occupés par la même espèce
    émettrice, REDESCENDRE ailleurs (rotation / sol nu, détox ∝ microbiome), et
    met à jour le traceur d'identité `eco.autotox_espece`. À appeler EN FIN DE
    SAISON (cadence lente, cf. boucle §17). Borné [0, AUTOTOX_MAX] par le
    GridField. Aucun émetteur au repos ⇒ E=None partout ⇒ champ nul reste nul ⇒
    golden NEUTRE."""
    autotox  = eco.autotox
    tracer   = eco.autotox_espece
    micro    = eco.microbiome
    # Émetteur de chaque plot préparé en UNE passe sur les plantes (FLUIDITÉ AN 2
    # ②) au lieu d'appeler `emetteur_du_plot` (qui reparcourt toutes les plantes)
    # pour chacun des plots. Même règle, même tie-break (1re plante de la liste).
    emetteurs = emetteurs_par_plot(plants)
    for r in range(eco.rows):
        row = tracer[r]
        for c in range(eco.cols):
            E = emetteurs.get((r, c))
            if E is not None and E is row[c]:
                # Même espèce émettrice qu'à la saison précédente → accumulation.
                autotox.add(r, c, AUTOTOX_MONTEE)
            else:
                # Rotation / sol nu / 1re occupation → le sol se repose. Détox
                # accélérée par un sol vivant (microbiome). No-op si déjà à 0.
                a = autotox.at_plot(r, c)
                if a > 0.0:
                    detox = AUTOTOX_MICROBE * min(1.0, micro.at_plot(r, c) / 3.0)
                    autotox.set(r, c, a * max(0.0, 1.0 - AUTOTOX_REPOS - detox))
            row[c] = E
