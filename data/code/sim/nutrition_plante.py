"""
SYMBIOSE — sim/nutrition_plante.py
Facteur de NUTRITION d'une plante (D120 ②, conception `docs/champs/sol/
conception_sol_nourricier.md` §3.2) : ce que la carence N/P/K fait à la croissance.

Avant ce tronçon, la croissance était AVEUGLE à N/P/K (vitalité 0,8-0,9 sur un sol
à qi 0) : la carence ne se lisait que dans une façade (`qi_local`) que personne ne
subissait. Ici, la carence devient une CONTRAINTE écologique (philo #2) : elle
ESCOMPTE la cible du `growth_factor` — exactement le patron de l'allélopathie dans
`sim/engine/croissance.py`. Jamais de malus de santé, jamais de mort (D41).

Modèle, par nutriment i ∈ {N, P, K}, sur l'empreinte racinaire :

    ratio_i  = min(1, stock_moyen_i / équilibre_roche_i)       (relatif au SOL)
    poids_i  = BESOIN[i][stade] / max_j BESOIN[j][stade]       (ce que le stade réclame)
    sat_i    = 1 − poids_i · (1 − ratio_i)                     (satisfaction ∈ [0,1])
    s        = min_i sat_i                                     (loi de Liebig)
    facteur  = PLANCHER + (1 − PLANCHER) · min(1, s / SEUIL_PLEIN)   (rampe continue)

Pourquoi RELATIF À L'ÉQUILIBRE du sol (et pas à FIELD_NORM comme `qi_local`) : un
sable n'est pas « carencé » parce qu'il est un sable — sa flore y est adaptée ; il
l'est quand il est vidé SOUS ce que sa roche fournit. Pourquoi le POIDS du stade :
une plante en fructification réclame surtout N et K (BESOIN), un semis surtout P ;
un nutriment peu demandé à ce stade ne la freine presque pas. Pourquoi SEUIL_PLEIN :
une plante ne ralentit pas au premier gramme perdu — au-dessus de ce ratio la
nutrition n'est plus le facteur limitant (sol simplement « correct »).

Carnivore : N ignoré (son azote vient des proies, miroir de `qi_local`). Mycorhize :
le P effectivement prélevable est amplifié (miroir de `plant_uptake`/`qi_local`).

Lecture PURE (aucune mutation, zéro RNG — philo #3). Relue par la voix « faim » (③) :
`nutrition_plante` rend aussi le nutriment limitant. Couche `sim` (lit `fields`).
"""
from __future__ import annotations

from fields.ecofields import MYCO_P_BONUS
from fields.ecofields.constants import BESOIN
from fields.ecofields.nutriments import equilibre_roche

# Rampe de nutrition — PLACEHOLDERS (calibrage mesuré au ②, cf. 00_etat.md).
# PLANCHER : une plante affamée pousse encore (lentement) — jamais de croissance
# nulle. Combiné à la base lumière (0,6..1) et au clamp [0,3 ; 1] du growth_factor.
NUTRITION_PLANCHER = 0.4
# SEUIL_PLEIN : satisfaction (fraction de l'équilibre de la roche) au-dessus de
# laquelle la nutrition ne limite plus la croissance.
NUTRITION_SEUIL_PLEIN = 0.6

_NUTRIMENTS = ("N", "P", "K")


def nutrition_plante(plant, eco, roots=None) -> tuple[float, str | None]:
    """(facteur ∈ [PLANCHER, 1], nutriment limitant ou None si pleine nutrition).

    `roots` : empreinte racinaire DÉJÀ filtrée par l'appelant (la croissance la
    dérive une fois pour l'allélopathie et la réutilise ici — pas de relecture
    en double). À défaut : `plant.root_plots` borné à la grille, repli plot-foyer."""
    if roots is None:
        roots = [(r, c) for (r, c) in (plant.root_plots or [plant.plot_foyer])
                 if 0 <= r < eco.rows and 0 <= c < eco.cols] or [plant.plot_foyer]
    besoins = {nut: BESOIN[nut].get(plant.current_stage, 0.0) for nut in _NUTRIMENTS}
    if getattr(plant.plant_class, "carnivore", False):
        besoins["N"] = 0.0
    b_max = max(besoins.values())
    if b_max <= 0.0:                       # stade sans besoin : rien ne limite
        return 1.0, None
    n_tot = p_tot = k_tot = 0.0
    for (r, c) in roots:
        n_tot += eco.n.at_plot(r, c)
        p_tot += eco.p.at_plot(r, c) * (1.0 + MYCO_P_BONUS * eco.mycelium.at_plot(r, c))
        k_tot += eco.k.at_plot(r, c)
    nb = len(roots)
    stocks = {"N": n_tot / nb, "P": p_tot / nb, "K": k_tot / nb}
    equilibres = dict(zip(_NUTRIMENTS, equilibre_roche(eco.soil_type)))
    s, limitant = 1.0, None
    for nut in _NUTRIMENTS:
        if besoins[nut] <= 0.0:
            continue
        ratio = min(1.0, stocks[nut] / max(1e-6, equilibres[nut]))
        sat = 1.0 - (besoins[nut] / b_max) * (1.0 - ratio)
        if sat < s:
            s, limitant = sat, nut
    rampe = min(1.0, s / NUTRITION_SEUIL_PLEIN)
    if rampe >= 1.0:
        return 1.0, None
    return NUTRITION_PLANCHER + (1.0 - NUTRITION_PLANCHER) * rampe, limitant


def facteur_nutrition(plant, eco, roots=None) -> float:
    """Facteur seul (escompte de la cible du growth_factor). Cf. `nutrition_plante`."""
    return nutrition_plante(plant, eco, roots)[0]
