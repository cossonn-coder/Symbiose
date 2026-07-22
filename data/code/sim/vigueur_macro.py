"""
SYMBIOSE — sim/vigueur_macro.py
Vigueur des POPULATIONS macroscopiques (ravageur / auxiliaire / pollinisateur /
vers de terre) — façade dérivée, PURE, read-only (D31.3).
Spec de référence : `docs/faune/vie_macro/conception_vie_macro.md` §4 (façades `vigueur_*`,
`qi_local` TROPHIQUE, populations PAS individus) ; patron emprunté à
`sim/vigueur_plante.py` §1 (façade dérivée, la décision structurante).

MIROIR de `vigueur_plante.py`, avec UNE différence assumée (§4) : le `qi_local`
n'est PAS le sol racinaire mais la RESSOURCE TROPHIQUE de la guilde — exactement
le scalaire `activite()` que le `PopulationField` a déjà mémorisé au dernier tick
(`fields/population.py:157`/`activite`). Rien à recalculer, rien à dupliquer.

Populations, PAS individus (§4) : on lit la VITALITÉ D'UNE POPULATION à un endroit
(densité du champ × richesse de sa ressource locale), pas une Vigueur par sprite.
Les sprites sont des échantillons (`sample_sprites`) — ils ne portent aucune
Vigueur. C'est la différence structurelle avec les plantes (`PlantInstance`
individuelles, dont chacune porte santé/stade/gènes).

    vigueur_pop(r, c) = densité(r, c) × qi_local_trophique(r, c)

Les deux facteurs sont normalisés en [0, 1] (densité par `POP_MAX`, ressource
déjà [0, 1]) → la façade est bornée [0, 1]. Lecture pure : aucune écriture, aucun
nouvel état, aucun budget énergétique. Le tick ne l'appelle JAMAIS → le golden
écologique NE PEUT PAS bouger (même garantie que `vigueur_plante.py`).

Usages (lecture seule, §4) : descriptions carnet/encyclopédie (« la population de
coccinelles est vigoureuse »), overlay debug. JAMAIS un pilote de simulation. Le
gain signé de « manger un individu » reste en dette D19.
"""
from __future__ import annotations

from fields.population import POP_MAX, POLLINATOR_NAMES


def densite(field, r: int, c: int) -> float:
    """Densité locale normalisée ∈ [0, 1] — le champ est déjà borné [0, POP_MAX]
    (`fields/population.py`), on divise par le plafond pour rester [0, 1]."""
    return field.at_plot(r, c) / POP_MAX


def qi_local(field, r: int, c: int) -> float:
    """Qi territorial TROPHIQUE ∈ [0, 1] (spec §4) — « puiser ». Réutilise le
    scalaire `activite()` du champ : la dernière grille de RESSOURCE que la guilde
    exploite (feuillage-hôte, proie, fleurs, microbiome/OM selon la guilde),
    mémorisée au tick. Read-only — pas de recalcul, pas d'écriture."""
    return field.activite(r, c)


def _vigueur_pop(field, r: int, c: int) -> float:
    """Façade unificatrice (miroir `vigueur_plante`) : densité × Qi trophique.
    Une population dense SUR une ressource riche est vigoureuse ; dense sur une
    ressource épuisée (ou clairsemée sur une ressource riche) l'est moins."""
    return densite(field, r, c) * qi_local(field, r, c)


def _vigueur_categorie(category: str, r: int, c: int, eco) -> float:
    """Vitalité agrégée d'une CATÉGORIE (modèle B, docs/faune/vie_macro/conception_faune_dediee.md §1) :
    somme des `_vigueur_pop` (densité × Qi trophique) des espèces membres, bornée
    [0, 1]. Tant qu'une catégorie n'a qu'un membre (④a), == l'ancien champ unique →
    golden NEUTRE. La somme (pas la moyenne) reflète qu'une catégorie peuplée de
    plusieurs espèces vigoureuses est globalement plus vivante."""
    v = sum(_vigueur_pop(f, r, c) for f in eco.category_fields(category))
    return min(1.0, v)


def vigueur_nuisible(r: int, c: int, eco) -> float:
    """Vitalité de la population RAVAGEUR locale — ressource = feuillage-hôte (§4)."""
    return _vigueur_categorie("ravageur", r, c, eco)


def vigueur_auxiliaire(r: int, c: int, eco) -> float:
    """Vitalité de la population AUXILIAIRE locale — ressource = proie (ravageur)
    + nectar/habitat (§4)."""
    return _vigueur_categorie("auxiliaire", r, c, eco)


def vigueur_pollinisateur(r: int, c: int, eco) -> float:
    """Vitalité POLLINISATRICE locale — somme des types (abeille/syrphe/papillon,
    arc pollinisation §C/§E ; ressource = nectar = floraison × attractivite).
    Bornée [0, 1] (la somme des types peut dépasser 1 sur un plot très fleuri)."""
    v = sum(_vigueur_pop(eco.populations[n], r, c)
            for n in POLLINATOR_NAMES if n in eco.populations)
    return min(1.0, v)


def vigueur_ver(r: int, c: int, eco) -> float:
    """Vitalité de la population DÉTRITIVORE locale (lombric/cloporte dès ④d ;
    `vers_de_terre` seul en ④a) — ressource = microbiome/OM en décomposition (§4)."""
    return _vigueur_categorie("detritivore", r, c, eco)


# --- Lecture diégétique : descripteur qualitatif (philo #5 — pas de chiffre) ---
# Seuils PROVISOIRES (calibrage post-test, comme `decrire_vigueur` pour les
# plantes). Voix « naturaliste qui observe » (CLAUDE.md, trois voix narratives).
# Le bas de l'échelle ("absente") couvre l'hiver / la guilde non installée :
# l'œil ne distingue rien dans les deux cas.
def decrire_vigueur_pop(v: float) -> str:
    """Traduit la Vigueur d'une population en mot qualitatif pour le carnet /
    l'encyclopédie. Fonction pure sur le scalaire — testable sans monde."""
    if v <= 0.0:
        return "absente"
    if v < 0.20:
        return "clairsemée"
    if v < 0.50:
        return "vigoureuse"
    return "florissante"
