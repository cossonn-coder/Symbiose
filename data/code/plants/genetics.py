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
#  - `vigueur`        : fitness générale (Sprint gènes du vecteur). >1 = croît
#    plus vite (avancement de stade accéléré) et se rétablit plus vite
#    (convalescence). Sens PROVISOIRE : à recâbler sur la Vigueur universelle
#    (D11) une fois cette couche conçue. Neutre 1.0.
#  - `resistance_pathogene` : résistance aux maladies fongiques (fonte des semis
#    + maladie adulte). >1 = moins sensible (susceptibilité = 1/gène). Neutre 1.0.
#  - `tolerance_secheresse` : tolérance au stress hydrique. >1 = croît en sol plus
#    sec (seuil de stagnation abaissé) ET tissu plus résistant à la sécheresse
#    sévère prolongée (susceptibilité = 1/gène). Neutre 1.0.
#  - `tolerance_ombre`      : MODULATEUR individuel de la tolérance à l'ombre, en
#    facteur de la base d'espèce (`PlantBase.shade_tolerance_base`, défaut par
#    strate). Neutre 1.0 → la plante prend la tolérance de son espèce ; le gène
#    fait dériver l'individu (variation + sélection naturelle de la sciaphilie,
#    compétition intra-plot). Lu en germination (lumière effective) et en
#    croissance (growth_factor sur lumière corrigée).
#  - `tolerance_asphyxie`   : tolérance à l'hypoxie racinaire (excès d'eau soutenu).
#    >1 = racines plus tolérantes à l'anoxie → moins de dégât quand le sol reste
#    gorgé (miroir haut de `tolerance_secheresse`). Neutre 1.0. AJOUTÉ EN FIN du
#    tuple (sprint plasticité ①) pour préserver les canaux de hash des gènes
#    existants : `child_genes`/`sample_genes` indexent le bruit par POSITION, un
#    ajout en queue ne décale donc aucun gène antérieur (golden-neutre attendu —
#    tant qu'aucun site ne le lit, branché au ②).
GENE_NAMES = ("hauteur", "rusticite_froid", "vigueur",
              "resistance_pathogene", "tolerance_secheresse",
              "tolerance_ombre", "tolerance_asphyxie")

# Plage « normale » du vecteur de gènes — gaussienne centrée 1.0, σ initial 0.10.
# L'introgression inter-espèces peut pousser HORS de [GENE_MIN, GENE_MAX]
# (vigueur hybride) → bornes dures plus larges au tirage.
GENE_INIT_SIGMA = 0.10
MUTATION_SIGMA  = 0.05      # mutation gaussienne par génération
GENE_MIN, GENE_MAX           = 0.70, 1.30
GENE_HARD_MIN, GENE_HARD_MAX = 0.40, 1.60


# --- Plasticité / expression plastique des gènes (sprint plasticité ①) ---------
# Sous-ensemble DÉFENSIF des gènes dont l'EXPRESSION (≠ génotype) est modulée par
# le stress vécu : phénotype = clamp_gene(génotype × expression). Chaque gène est
# apparié à une mémoire d'exposition déterministe (cf. _update_physiology). Les
# traits constitutifs (`hauteur`, `vigueur`) n'en sont PAS — ils ne se « durcissent »
# pas. Extensible : ajouter un gène ici + lui fournir une mémoire d'exposition.
ADAPTOGENIC_GENES = ("tolerance_secheresse",   # ↔ drought_memory   (existe)
                     "tolerance_ombre",         # ↔ shade_memory     (existe)
                     "rusticite_froid",         # ↔ cold_memory      (①, à créer)
                     "resistance_pathogene",    # ↔ infection_memory (①, à créer)
                     "tolerance_asphyxie")       # ↔ asphyxie_memory  (existe)

# Dynamique d'expression (valeurs de DÉPART — calibrage itératif P6). cible(g) =
# 1.0 + EXPR_GAIN × mémoire(g) ; l'expression glisse vers la cible en lerp lent à
# HYSTÉRÈSE (montée TAU_UP rapide / descente TAU_DOWN lente → la plante garde un
# temps son endurcissement, pas de yo-yo). Bornée [EXPR_MIN, EXPR_MAX] ; le produit
# génotype×expression repasse ENSUITE par clamp_gene (borne dure 1.6).
EXPR_GAIN = 0.30           # gain mémoire saturée → cible d'expression (1.0 → 1.30)
EXPR_MIN  = 1.0            # plancher : l'expression ne descend pas sous le génotype
EXPR_MAX  = 1.30           # plafond modeste (anti-emballement, < GENE_HARD_MAX)
TAU_UP    = 0.08           # vitesse d'acclimatation (montée)
TAU_DOWN  = 0.04           # vitesse de désacclimatation (descente, plus lente)


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
