"""
SYMBIOSE — plants/genetics.py
Vecteur de gènes héréditaire + compatibilité de croisement (D22).

Fondation pure : aucun import interne au projet → tout le monde peut s'appuyer
dessus sans créer de cycle (notamment fields/seedbank.py qui importe clamp_gene).
Seule dépendance : le registre voisin `caracteres.py`, lui aussi pur.
"""

from plants.caracteres import (CARACTERES, BORNES_FACTEUR, SIGMA_A_FACTEUR,  # noqa: F401
                               Caractere, parametres_espece, neutre, sigma_a, borne)

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
#  - `germination_thermique` : VARIABILITÉ intra-espèce de la fenêtre de levée
#    thermique (sprint germination thermique ④). Depuis D139 ③ en °C : c'est
#    directement l'ABAISSEMENT de l'optimum de levée (>0 = lève PLUS TÔT au froid,
#    `t_opt_eff = t_germ_opt − gène`, cf. succession.py). Neutre 0 °C. C'est le
#    support de la SÉLECTION DARWINIENNE ÉMERGENTE : sur un plot froid, les lignées
#    « lève-tôt » dominent le pool-sol au fil des saisons, sans code de sélection
#    dédié (reproduction + héritage + réensemencement déjà en place). AJOUTÉ EN
#    QUEUE (même garde-fou de canal de hash que `tolerance_asphyxie`/`port_trapu` :
#    `child_genes`/`sample_genes` indexent le bruit par POSITION → un ajout en queue
#    ne décale aucun gène antérieur).
#  - `tolerance_asphyxie`   : tolérance à l'hypoxie racinaire (excès d'eau soutenu).
#    >1 = racines plus tolérantes à l'anoxie → moins de dégât quand le sol reste
#    gorgé (miroir haut de `tolerance_secheresse`). Neutre 1.0. AJOUTÉ EN FIN du
#    tuple (sprint plasticité ①) pour préserver les canaux de hash des gènes
#    existants : `child_genes`/`sample_genes` indexent le bruit par POSITION, un
#    ajout en queue ne décale donc aucun gène antérieur (golden-neutre attendu —
#    tant qu'aucun site ne le lit, branché au ②).
#  - `port_trapu`     : THIGMOMORPHOGÉNÈSE (sprint VENT & ÉVAPOTRANSPIRATION ④).
#    Gène ADAPTOGÈNE dont l'EXPRESSION est induite par l'exposition mécanique au
#    vent (`wind_memory` ↔ `vent_local` au plot). Phénotype >1 = port TRAPU/robuste
#    (entre-nœuds courts → étiolement réduit, tige sollicitée → susceptibilité au
#    dégât de vent abaissée). Neutre 1.0 (génotype = port standard). AJOUTÉ EN QUEUE
#    (même garde-fou de canal de hash que `tolerance_asphyxie`).
#  - `phenologie_florale` : VARIABILITÉ intra-espèce de la DATE de floraison (sprint
#    bugs d'émergence ③, S2). Depuis D139 ③ en SEMAINES D'AVANCE du tempo de vie
#    (>0 = fleurit PLUS TÔT, abscission et sénescence suivent ; conversion par
#    horloge dans `sim/tempo.py`). Neutre 0. Coûte de la taille (K_PREC).
#    C'est le support de la SÉLECTION DARWINIENNE ÉMERGENTE qui DÉSYNCHRONISE la
#    floraison : le pool-sol porte une variance de dates → nectar SOUTENU (au lieu
#    d'un pic synchrone unique) → dynamique des pollinisateurs saine, sans code de
#    sélection dédié (reproduction + héritage + réensemencement déjà en place).
#    AJOUTÉ EN QUEUE (même garde-fou de canal de hash que `germination_thermique` :
#    `child_genes`/`sample_genes` indexent le bruit par POSITION → un ajout en queue
#    ne décale aucun gène antérieur).
#
# Depuis D139 ① la LISTE vit dans le registre des caractères (`caracteres.py`,
# qui déclare aussi unité, neutre, σ_A, bornes) : GENE_NAMES en est DÉRIVÉ, dans
# l'ordre de la table — les appelants (seedbank, reproduction, greffe, seeds,
# semiologie, bancs) n'ont rien à changer. Ajouter un gène = l'ajouter EN QUEUE
# du registre.
GENE_NAMES = tuple(CARACTERES)

# Plage « normale » du vecteur de gènes — gaussienne centrée 1.0, σ initial 0.10.
# L'introgression inter-espèces peut pousser HORS de [GENE_MIN, GENE_MAX]
# (vigueur hybride) → bornes dures plus larges au tirage.
# (GENE_INIT_SIGMA et les bornes dures viennent du registre : mêmes valeurs.)
GENE_INIT_SIGMA = SIGMA_A_FACTEUR
MUTATION_SIGMA  = 0.05      # OBSOLÈTE depuis D139 ② (ancienne mutation fixe par
                            # génération) — conservé, plus lu par `child_genes`.

# --- Hérédité infinitésimale (D139 ②, conception §4) ---------------------------
# Un enfant = moyenne de ses parents + BRASSAGE (échantillonnage mendélien : les
# deux parents transmettent chacun une moitié tirée au hasard de leurs allèles)
# + un petit FILET de mutation. Variance du brassage = ½·σ_A²·(1 − F̄) : plus les
# parents sont consanguins (F → 1, lignée fixée), moins leurs enfants diffèrent.
# Le filet `H_MUT·σ_A²` empêche une lignée autogame de se figer pour toujours.
# H_MUT = 0,01 est un choix de JEU (réel ≈ 0,001) : 10× plus vite qu'en nature.
H_MUT = 0.01

# Dépression de consanguinité (D139 ②, conception §6). Un individu consanguin
# d'une espèce ALLOGAME exprime des allèles délétères récessifs habituellement
# masqués → il pousse moins. Facteur sur la vigueur effective :
#     1 − DI · F · (1 − s)        s = neutre d'`autofecondation` de l'espèce
# Les autogames (s ≈ 0,95) ont « purgé » ces allèles au fil des générations :
# facteur ≈ 1. Une ortie (s = 0,05) totalement consanguine perd ≈ 28 %.
# Appliqué au MÊME endroit que `cout_defense` (croissance, convalescence) —
# jamais un malus direct de santé (philo #2).
DI = 0.3

# Compromis PRÉCOCITÉ ↔ TAILLE (D139 ③, conception §6). Une plante qui fleurit
# tôt a eu moins de semaines de croissance végétative avant de basculer ses
# ressources vers la fleur : elle reste plus petite. Une tardive, l'inverse.
#     facteur = 1 − K_PREC · avance        (avance = `phenologie_florale`, semaines)
# K_PREC = 0,03 → une semaine d'avance coûte 3 % de hauteur. Borné à
# [PREC_MIN, PREC_MAX] (garde-fou : aux bornes ±4 sem. du caractère le facteur
# vaut 0,88-1,12, la borne ne mord jamais en pratique). C'est la sélection qui
# arbitre : sur un plot froid à saison courte, fleurir tôt paie malgré la taille.
K_PREC = 0.03
PREC_MIN, PREC_MAX = 0.5, 1.5
GENE_MIN, GENE_MAX           = 0.70, 1.30
GENE_HARD_MIN, GENE_HARD_MAX = BORNES_FACTEUR


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
                     "tolerance_asphyxie",       # ↔ asphyxie_memory  (existe)
                     "port_trapu")               # ↔ wind_memory      (vent ④, à créer)

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

# Coût croissance/défense (sprint plasticité ③ — compromis growth–defense, philo #2).
# La SUR-expression (part de chaque expression au-dessus de 1.0) re-route la vigueur
# vers la défense au lieu de s'y ajouter : durcir ses tolérances coûte de la
# croissance/reproduction. cout_defense = max(PLANCHER, 1 − DEFENSE_COST × Σ_g
# max(0, expression[g]−1)). Désexprimer (≤ 1.0) ne coûte JAMAIS. Valeurs de DÉPART
# (calibrage itératif P6) : modéré → survivre sous stress reste gagnant, mais payant
# sous abondance (anti-emballement / anti-sélection). PLANCHER > 0 : la défense ne
# peut jamais annuler la vigueur (une plante blindée croît peu, pas zéro).
DEFENSE_COST = 0.15        # poids du budget défense mobilisé (par unité de sur-expression)
DEFENSE_PLANCHER = 0.5     # plancher du facteur coût (vigueur jamais sous la moitié)

# Priming transgénérationnel (sprint plasticité ④ — conception §2.5, P2). À la
# production de graine, l'enfant naît avec une expression INITIALE héritée de la
# MÈRE SEULE (épigénétique maternelle), pas neutre :
#   child.expression[g] = 1.0 + PRIMING_FRAC × (mother.expression[g] − 1.0)
# La fraction (< 1) atténue l'état d'alerte à chaque transmission : c'est l'un des
# deux ressorts de l'OUBLI ÉMERGENT (l'autre = la désacclimatation intra-vie). Si
# le stress cesse → la lignée retombe au neutre en 2-3 générations, sans compteur.
# Si le stress persiste → chaque génération recharge sa mémoire → le priming tient.
# Valeur de DÉPART (calibrage itératif P2).
PRIMING_FRAC = 0.4


def clamp_gene(x: float) -> float:
    """Borne un facteur génétique aux limites dures (l'introgression peut sortir
    de la plage normale, mais jamais des limites physiologiques)."""
    return max(GENE_HARD_MIN, min(GENE_HARD_MAX, x))


def facteur_precocite(avance_semaines: float) -> float:
    """Facteur de hauteur du compromis précocité ↔ taille (cf. K_PREC) : < 1 pour
    une plante précoce (avance > 0), > 1 pour une tardive. Neutre 0 → 1.0 exact."""
    return max(PREC_MIN, min(PREC_MAX, 1.0 - K_PREC * avance_semaines))


def neutral_genes(plant_class=None) -> dict:
    """Vecteur de gènes neutre : chaque caractère à son NEUTRE (1.0 pour un
    facteur ; selon le mode de pollinisation pour `autofecondation`, D139 ②)."""
    return {g: neutre(g, plant_class) for g in GENE_NAMES}


def species_compatible(a: type, b: type) -> bool:
    """
    Deux espèces peuvent-elles se croiser ? (groupe de compatibilité = famille
    botanique, décision 2026-06-03). Même espèce → croisement pur ; espèces
    distinctes de même famille → introgression (l'enfant garde l'espèce mère).
    """
    return bool(a.family) and a.family == b.family
