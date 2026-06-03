"""
SYMBIOSE — reproduction.py
Héritage génétique biparental (D22).

À la production de graines sur une plante mère fécondée :
  - on cherche un PÈRE compatible (même famille) à portée de pollinisation ;
  - gène_enfant = moyenne(mère, père) + mutation gaussienne, par gène ;
  - pas de partenaire / espèce autogame → AUTOFÉCONDATION (mère + mutation
    réduite, consanguinité = faible diversité).

Pollinisation par espèce : `pollination_mode` (wind/insect/self) +
`pollination_radius_cm`. En mode insecte, les rondelles `pollinisateur` et
`auxiliaire` de la tuile élargissent le rayon → favoriser les auxiliaires =
plus de brassage = meilleures graines (mécanique permaculture).

Introgression : un père d'une AUTRE espèce de la même famille décale les gènes
de l'enfant, qui garde l'espèce de la MÈRE — aucune nouvelle espèce générée.

Déterministe : appariement et mutation via les hash (_hash_noise / hash_gauss).
Aucun RNG live (règle de design #3).
"""
from __future__ import annotations

from models import species_compatible, GENE_NAMES, MUTATION_SIGMA, clamp_gene
from fields import _hash_noise, hash_gauss

# Modulation insecte du rayon de croisement (mode "insect" uniquement).
INSECT_BASE_REACH   = 0.5   # rayon effectif sans pollinisateurs (× rayon nominal)
INSECT_FULL_BONUS   = 1.0   # bonus de rayon à saturation des rondelles
SELFING_SIGMA_RATIO = 0.5   # mutation réduite en autofécondation (consanguinité)


def is_seed_bearing(plant) -> bool:
    """La plante est-elle en âge/stade de porter des graines ?"""
    cls = plant.plant_class
    if hasattr(cls, "age_curve"):        # pérenne ligneuse (courbe d'âge)
        return plant.age_years >= getattr(cls, "maturity_years", 0.0)
    return plant.current_stage >= len(cls.growth_stages) - 1


def _euclid2(a, b) -> float:
    return (a.x_cm - b.x_cm) ** 2 + (a.y_cm - b.y_cm) ** 2


def pollinator_reach(mother, tile) -> float:
    """
    Rayon de croisement effectif (cm). Anémophile/autogame : rayon nominal.
    Insecte : modulé par les rondelles `pollinisateur` + `auxiliaire` (saturation
    à ~6 rondelles cumulées). Sans pollinisateur → rayon réduit → autofécondation.
    """
    cls = mother.plant_class
    if cls.pollination_mode != "insect":
        return cls.pollination_radius_cm
    sat = min(1.0, (tile.get_rondelle_count("pollinisateur")
                    + tile.get_rondelle_count("auxiliaire")) / 6.0)
    return cls.pollination_radius_cm * (INSECT_BASE_REACH + INSECT_FULL_BONUS * sat)


def find_father(mother, plants, tile, seed, week):
    """
    Père compatible (même famille) à portée, en âge de fleurir, le plus proche
    prioritaire (tie-break déterministe par hash). None si la mère est autogame
    ou si aucun partenaire n'est à portée → autofécondation.
    """
    if mother.plant_class.pollination_mode == "self":
        return None
    reach2 = pollinator_reach(mother, tile) ** 2
    candidates = []
    for p in plants:
        if p is mother or not p.is_alive:
            continue
        if not species_compatible(mother.plant_class, p.plant_class):
            continue
        if not is_seed_bearing(p):
            continue
        d2 = _euclid2(mother, p)
        if d2 <= reach2:
            candidates.append((d2, p))
    if not candidates:
        return None
    candidates.sort(key=lambda t: t[0])
    nearest = candidates[0][0]
    tied = [p for d2, p in candidates if d2 <= nearest * 1.0001]
    if len(tied) == 1:
        return tied[0]
    r, c = mother.position
    idx = int(_hash_noise(seed, week * 23, r, c) * len(tied)) % len(tied)
    return tied[idx]


def child_genes(mother, father, seed, week) -> dict:
    """
    Vecteur de gènes de l'enfant.
      biparental    : moyenne(mère, père) + mutation gaussienne ;
      autofécondation: gènes de la mère + mutation réduite ;
      introgression : père d'une autre espèce (même famille) → ses gènes décalent
                      l'enfant, qui reste de l'espèce de la mère.
    L'introgression peut pousser un gène HORS de la plage normale [0.7, 1.3]
    (vigueur hybride) ; seul clamp_gene borne les limites dures.
    """
    r, c = mother.position
    genes = {}
    for i, g in enumerate(GENE_NAMES):
        m = mother.gene(g)
        if father is None:
            base, sigma = m, MUTATION_SIGMA * SELFING_SIGMA_RATIO
        else:
            base, sigma = 0.5 * (m + father.gene(g)), MUTATION_SIGMA
        z = hash_gauss(seed, week * 29 + i, r, c, k=4 * i)
        genes[g] = clamp_gene(base + z * sigma)
    return genes
