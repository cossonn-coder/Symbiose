"""
SYMBIOSE — fields/foragers.py
Butineurs déterministes : échantillonnage & marche fleur-en-fleur (arc
pollinisation, tronçon ③ — CONCEPTION_POLLINISATION §F).

Le basculement assumé (§F.1) : une PART de la perception passe dans la MÉCANIQUE.
Les butineurs (échantillonnés depuis les champs pollinisateurs §C/§E) marchent de
fleur en fleur et DÉPOSENT réellement le pollen → la nouaison (④) dépendra des
visites. Comme `sample_sprites`, la marche est PURE & déterministe (positions et
choix dérivés de seed + `_hash_noise`, jamais de RNG vivant, philo #3) et RECRÉÉE
chaque tick depuis le champ (aucun état persistant inter-tick au-delà du champ,
§F.2).

Cette fonction ne touche AUCUNE plante : elle rend des `deposits` que la couche
sim applique à `pollen_recu` (engine._tick_butineurs) — la couche `fields`
n'écrit jamais dans `plants`. Découpé de `fields.population` (garde-fou taille :
les agents sont un concept distinct des champs de population). Duck-typé sur le
champ (pas d'import de `population` → aucun cycle ; `population` importe d'ICI
`ForagerParams`).

Canaux _hash_noise (décorrélés des sprites) : on réutilise `spec.salt + aid`
(offset par agent) pour les tirages d'un agent, avec une coordonnée de tirage
distincte (1=row init, 2=col init, 3=x_frac, 4=y_frac, ≥10=tie-break de marche).
"""

from __future__ import annotations
from dataclasses import dataclass

from fields.noise import _hash_noise

_DRAW_ROW   = 1
_DRAW_COL   = 2
_DRAW_XFRAC = 3
_DRAW_YFRAC = 4
_DRAW_TIE   = 10   # base des tirages de tie-break pas-à-pas (+ step)


@dataclass(frozen=True)
class ForagerParams:
    """Paramètres d'agent butineur d'un type (§F). Pilotent l'échantillonnage et
    la marche fleur-en-fleur de `sample_foragers` (tronçon ③). Placeholders —
    calibrage post-test (un butineur sage : peu d'agents, tournée courte).

      - n_max      : nombre MAX d'agents échantillonnés par tuile (à densité=1) ;
                     l'effectif réel = round(densité_moyenne × n_max) (§F.2, pop bornée).
      - substeps   : sous-pas de marche par tick (longueur de la tournée).
      - perception : rayon (plots, Chebyshev) de perception / montée de gradient (§F.3).
      - deposit    : DEPOT — part de la charge déposée sur une fleur conspécifique (§F.4).
      - recharge   : gain de charge en visitant une fleur de l'espèce-cible.
    """
    n_max: int
    substeps: int
    perception: int
    deposit: float
    recharge: float


@dataclass(frozen=True)
class ForagerAgent:
    """Un butineur échantillonné — exposé au snapshot pour le rendu Godot. Porte
    sa position de FIN de tournée, son espèce-cible (constance) et s'il transporte
    une charge conspécifique. Donnée de rendu : aucune Vigueur, aucun feedback sim."""
    guild: str         # type pollinisateur (abeille/syrphe/papillon)
    agent_id: int
    row: int           # plot courant en fin de marche
    col: int
    x_frac: float      # position dans le plot ∈ [0,1] (rendu)
    y_frac: float
    target: str        # nom de l'espèce-cible ("" si aucune fleur trouvée)
    carrying: bool     # transporte une charge conspécifique


def _best_in_perception(grid, r, c, rad, rows, cols, seed, salt, step):
    """Plot de la fenêtre de perception (Chebyshev `rad`, centre INCLUS)
    maximisant `grid` — montée de gradient locale (§F.3). Tie-break déterministe
    par hash (philo #3 : aucune dépendance à l'ordre d'itération). Retourne
    (r, c, valeur_max). Si tout est nul, le centre est rendu avec valeur 0."""
    best_r, best_c, best_v, best_h = r, c, grid[r][c], -1.0
    for dr in range(-rad, rad + 1):
        nr = r + dr
        if not (0 <= nr < rows):
            continue
        for dc in range(-rad, rad + 1):
            nc = c + dc
            if not (0 <= nc < cols):
                continue
            v = grid[nr][nc]
            if v > best_v:
                best_r, best_c, best_v, best_h = nr, nc, v, -1.0
            elif v == best_v and v > 0.0:
                h = _hash_noise(seed, salt + _DRAW_TIE + step, nr, nc)
                if h > best_h:
                    best_r, best_c, best_h = nr, nc, h
    return best_r, best_c, best_v


def _dominant_in_perception(grids, names, r, c, rad, rows, cols):
    """Espèce dont la floraison CUMULÉE dans la fenêtre de perception est maximale
    (re-ciblage en fin de tournée, §F.3). None si aucune fleur à portée. Tie-break
    par ordre alphabétique de `names` (déterministe)."""
    best_name, best_sum = None, 0.0
    for name in names:
        g = grids[name]
        s = 0.0
        for dr in range(-rad, rad + 1):
            nr = r + dr
            if not (0 <= nr < rows):
                continue
            for dc in range(-rad, rad + 1):
                nc = c + dc
                if 0 <= nc < cols:
                    s += g[nr][nc]
        if s > best_sum:
            best_name, best_sum = name, s
    return best_name


def sample_foragers(field, species_grids: dict, params: ForagerParams,
                    seed: int, week_in_year: int):
    """
    Échantillonne et fait marcher les butineurs d'UN type sur UNE tuile (§F).
    PURE & déterministe ; ne touche aucune plante.

    `species_grids` : {nom_espèce → grille[r][c]} = la « carte des fleurs » perçue
    par CE type (floraison conspécifique PONDÉRÉE par l'attractivité du type — les
    anémophiles, attractivité ~0, en sont absentes). Construite par l'appelant.

    Marche (§F.3-4) : chaque agent a une espèce-cible (constance florale) ; à
    chaque sous-pas il VISITE son plot (dépose sa charge si conspécifique, puis
    recharge), puis monte le gradient de floraison de sa cible dans sa perception ;
    plus de fleur de l'espèce à portée → re-ciblage (charge perdue, comme dans la
    nature → la constance émerge sans règle ad hoc).

    Retourne (agents, deposits) :
      - agents  : list[ForagerAgent] pour le snapshot ;
      - deposits: list[(espèce, r, c, charge_déposée)] à appliquer par la couche sim.
    """
    spec = field.spec
    rows, cols = field.rows, field.cols
    n_plots = rows * cols
    if n_plots == 0 or not species_grids:
        return [], []
    # Réservoir : effectif = round(densité_moyenne × n_max) (§F.2, pop bornée).
    mean_d = sum(field.data[r][c] for r in range(rows) for c in range(cols)) / n_plots
    n_agents = min(params.n_max, int(round(mean_d * params.n_max)))
    if n_agents <= 0:
        return [], []
    names = sorted(species_grids)            # ordre déterministe
    agents: list[ForagerAgent] = []
    deposits: list[tuple] = []
    for aid in range(n_agents):
        salt = spec.salt + aid
        r = min(rows - 1, int(_hash_noise(seed, salt, week_in_year, _DRAW_ROW) * rows))
        c = min(cols - 1, int(_hash_noise(seed, salt, week_in_year, _DRAW_COL) * cols))
        target = _dominant_in_perception(species_grids, names, r, c,
                                         params.perception, rows, cols)
        carried, charge = None, 0.0
        for step in range(params.substeps):
            if target is None:
                target = _dominant_in_perception(species_grids, names, r, c,
                                                 params.perception, rows, cols)
                carried, charge = None, 0.0   # re-ciblage → charge précédente perdue
                if target is None:
                    break
            grid = species_grids[target]
            if grid[r][c] > 0.0:              # visite d'une fleur de l'espèce-cible
                if carried == target and charge > 0.0:
                    deposits.append((target, r, c, params.deposit * charge))
                carried = target
                charge = min(1.0, charge + params.recharge)
            nr, nc, best = _best_in_perception(grid, r, c, params.perception,
                                               rows, cols, seed, salt, step)
            if best <= 0.0:
                target = None                # plus de fleur à portée → fin de tournée
            else:
                r, c = nr, nc
        agents.append(ForagerAgent(
            guild=spec.name, agent_id=aid, row=r, col=c,
            x_frac=_hash_noise(seed, salt, week_in_year, _DRAW_XFRAC),
            y_frac=_hash_noise(seed, salt, week_in_year, _DRAW_YFRAC),
            target=target or "",
            carrying=(carried is not None and charge > 0.0),
        ))
    return agents, deposits
