"""
SYMBIOSE — fields/ecofields/transport.py
Transport ÉOLIEN de la litière de surface (sprint VENT & ÉVAPOTRANSPIRATION ⑦).
Spec : CONCEPTION_VENT_EVAPOTRANSPIRATION.md §5.6 + §4 (géométrie d'abri).

Le vent ne fait pas que dessécher : il CHARRIE la litière LÉGÈRE de surface
(feuilles mortes, brins d'herbe sèche) et la dépose SOUS LE VENT, là où le flux
ralentit — c'est-à-dire dans la zone ABRITÉE (faible `eco.vent`). Émergence
recherchée (philo #2 : flux vent → contrainte → hétérogénéité du sol) : un coin
au pied d'un brise-vent (maison, haie) s'enrichit en matière organique, exactement
comme une congère s'amasse derrière un obstacle. Couple décompo/structure (la
matière transportée se décompose là où elle se dépose).

MODÈLE SOBRE (§5.6) : transfert NET d'une fraction de la litière transportable d'un
plot EXPOSÉ vers son voisin SOUS LE VENT, *seulement si ce voisin est plus abrité*
(le vent dépose là où il ralentit). Seuls les tissus LÉGERS volent (`TRANSPORT_TISSUS`
= feuille/herbace) ; le bois, les fruits, les exsudats (`diffus`) restent au sol.

DÉTERMINISME (philo #3, ZÉRO RNG) : on lit un SNAPSHOT des masses donneuses AVANT
de muter (double buffer, comme `GridField.diffuse`) → le résultat ne dépend pas de
l'ordre de parcours. Direction du vent discrétisée en UN plot voisin (cartésien).

PERF (§7B, levier 5 — passe CONDITIONNELLE) : `tick_transport` est SAUTÉE les jours
calmes (`wind_force < TRANSPORT_SEUIL`) → coût NUL hors coup de vent. Quand elle
tourne, c'est une seule passe O(plots) sans capsule ni scatter cher (la géométrie
d'abri est déjà portée par `eco.vent`, calculé au ③ — on ne fait que la LIRE).

Couche : `fields` (helper du conteneur). N'importe que `constants` (knobs) + lit
`eco.litiere` / `eco.vent`. Aucun import de couche haute.
"""
from __future__ import annotations

import math

from .constants import (TRANSPORT_SEUIL, TRANSPORT_FRAC, TRANSPORT_TISSUS,
                        TRANSPORT_LOG_SEUIL)


def _aval(wind_dir: float):
    """Plot voisin SOUS LE VENT (offset `(dr, dc)` cartésien). `wind_dir` = direction
    D'OÙ VIENT le vent (`WindState.direction`) ; le vent VA à l'opposé. Même
    convention que `fields.abri` : vecteur aval `(gx, gy) = (sin, cos)(wind_dir)`
    avec x→colonne, y→ligne. On le discrétise au plot voisin DOMINANT (le plus grand
    axe l'emporte → un seul voisin, pas de diagonale ambiguë)."""
    gx = math.sin(wind_dir)   # composante colonne
    gy = math.cos(wind_dir)   # composante ligne
    if abs(gx) >= abs(gy):
        return (0, 1 if gx >= 0 else -1)
    return (1 if gy >= 0 else -1, 0)


def tick_transport(eco, wind_dir: float, wind_force: float) -> list:
    """Charrie la litière légère des plots EXPOSÉS vers leur voisin SOUS LE VENT,
    SI ce voisin est plus abrité (§5.6). PASSE CONDITIONNELLE : no-op strict (liste
    vide) tant que `wind_force < TRANSPORT_SEUIL` (jour calme → coût nul, levier 5).

    Pour chaque plot donneur `d` plus VENTÉ que son voisin aval `a`
    (`vent[d] > vent[a]`), on déplace `TRANSPORT_FRAC × (vent[d] − vent[a])` de la
    masse de chaque tissu transportable de `d` vers `a` (même fusion par tissu que
    `deposer_litiere`). Le différentiel de vent module l'intensité : plus la marche
    d'abri est franche, plus le dépôt s'accumule. Conservation stricte de la masse
    (ce qui part de `d` arrive en `a`). Émet un marqueur `🍃` de tuile si le transport
    net dépasse `TRANSPORT_SEUIL` de masse (signe diégétique, philo #5 ; consommé par
    le ledger des voix HORS tick).

    PUR au sens RNG (zéro tirage). Re-figeage golden MAÎTRISÉ attendu (la litière de
    surface se redistribue par plot) — annoncé par le kickoff ⑦."""
    if wind_force < TRANSPORT_SEUIL:
        return []
    vent = getattr(eco, "vent", None)
    if vent is None:
        return []
    rows, cols = eco.rows, eco.cols
    dr, dc = _aval(wind_dir)
    # SNAPSHOT des masses transportables par plot (double buffer → ordre-indépendant).
    # On ne lit la litière qu'UNE fois ; toutes les écritures se font ensuite.
    snap = [[{t: sum(p.masse for p in eco.litiere[r][c] if p.tissu == t)
              for t in TRANSPORT_TISSUS}
             for c in range(cols)] for r in range(rows)]
    deplace_total = 0.0
    for r in range(rows):
        ar = r + dr
        if not (0 <= ar < rows):
            continue
        for c in range(cols):
            ac = c + dc
            if not (0 <= ac < cols):
                continue
            # On ne charrie QUE vers un voisin plus abrité (le vent dépose où il
            # ralentit). Plot aval aussi venté ou plus venté → rien (pas de remontée).
            delta_vent = vent.at_plot(r, c) - vent.at_plot(ar, ac)
            if delta_vent <= 0.0:
                continue
            frac = min(1.0, TRANSPORT_FRAC * delta_vent)
            for t in TRANSPORT_TISSUS:
                masse = snap[r][c][t]
                if masse <= 0.0:
                    continue
                m = masse * frac
                if m <= 0.0:
                    continue
                # Conservation stricte : on REDÉPOSE exactement ce qui a pu être
                # retiré (la masse vivante peut différer du snapshot si la décompo a
                # déjà raboté la parcelle ce tick — improbable ici, mais sûr).
                pris = eco.retirer_litiere(r, c, t, m)
                if pris > 0.0:
                    eco.deposer_litiere(ar, ac, t, pris)
                    deplace_total += pris
    if deplace_total >= TRANSPORT_LOG_SEUIL:
        return [f"    🍃 Le vent charrie la litière vers l'abri "
                f"(+{deplace_total:.2f} sous le vent)"]
    return []
