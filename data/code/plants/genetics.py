"""
SYMBIOSE — plants/genetics.py
Vecteur de gènes héréditaire + compatibilité de croisement (D22).

Fondation pure : aucun import interne au projet → tout le monde peut s'appuyer
dessus sans créer de cycle (notamment fields/seedbank.py qui importe clamp_gene).
"""

# Vecteur de gènes héréditaire (D22) — extensible sans refactor. Ajouter un gène
# = l'ajouter ici ; `child_genes` (reproduction) le calcule alors automatiquement
# sur un canal de hash décorrélé (l'index dans ce tuple), sans toucher aux autres.
#  - `hauteur`        : module la hauteur effective (Sprint génétique).
#  - `rusticite_froid`: résistance au gel (météo 03). >1 = plus rustique → moins
#    de dégât tissulaire quand la température ambiante passe sous 0 °C. Neutre 1.0.
GENE_NAMES = ("hauteur", "rusticite_froid")

# Plage « normale » du vecteur de gènes — gaussienne centrée 1.0, σ initial 0.10.
# L'introgression inter-espèces peut pousser HORS de [GENE_MIN, GENE_MAX]
# (vigueur hybride) → bornes dures plus larges au tirage.
GENE_INIT_SIGMA = 0.10
MUTATION_SIGMA  = 0.05      # mutation gaussienne par génération
GENE_MIN, GENE_MAX           = 0.70, 1.30
GENE_HARD_MIN, GENE_HARD_MAX = 0.40, 1.60


def clamp_gene(x: float) -> float:
    """Borne un facteur génétique aux limites dures (l'introgression peut sortir
    de la plage normale, mais jamais des limites physiologiques)."""
    return max(GENE_HARD_MIN, min(GENE_HARD_MAX, x))


def neutral_genes() -> dict:
    """Vecteur de gènes neutre (tous les facteurs = 1.0)."""
    return {g: 1.0 for g in GENE_NAMES}


def species_compatible(a: type, b: type) -> bool:
    """
    Deux espèces peuvent-elles se croiser ? (groupe de compatibilité = famille
    botanique, décision 2026-06-03). Même espèce → croisement pur ; espèces
    distinctes de même famille → introgression (l'enfant garde l'espèce mère).
    """
    return bool(a.family) and a.family == b.family
