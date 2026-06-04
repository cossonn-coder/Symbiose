"""
SYMBIOSE — sim/vigueur_plante.py
Vigueur des ÊTRES VIVANTS — façade dérivée, PURE, read-only (D11, sous-sprint 3).
Spec de référence : `data/code/CONCEPTION_VIGUEUR.md` §1 (façade dérivée — la
décision structurante), §4 (Qi territorial = champs éco existants), §5
(déterminisme/golden), §6 (gène `vigueur` D22b stabilisé par la façade).

Deux strates distinctes (spec §0) :
  1. Cœur écologique déterministe (le tick `engine`) — la Vigueur d'une plante
     est une LECTURE de ses états existants, PAS un nouvel état stocké.
  2. Couche gameplay joueur (`sim/vigueur.py`) — l'unique vrai nouvel état.

CE module relève de la strate 1 : aucune écriture, aucun budget énergétique à
équilibrer, aucun nouvel état. C'est pourquoi le golden ÉCOLOGIQUE
(`tests/test_golden.py`) NE PEUT PAS bouger — le tick ne l'appelle jamais. La
façade sert (a) de lecture diégétique (carnet/encyclopédie, overlay debug) et
(b) de modulateur de la valeur des organes récoltés/consommés (§1) — JAMAIS de
variable pilote de la simulation.

    vigueur_plante = sante(p) × maturite(p) × qi_local(p) × p.gene("vigueur")

Les trois premiers facteurs sont normalisés en [0, 1]. Le quatrième, le gène
`vigueur` (D22b), est ENVELOPPÉ tel quel (§6) : c'est le modulateur génétique
(neutre = 1.0, peut dépasser 1.0). La façade est donc une lecture RELATIVE, pas
un scalaire borné — d'où le descripteur qualitatif plutôt qu'un chiffre brut
(philo #5).
"""
from __future__ import annotations

# Le « puiser » de §4 réutilise les constantes/normalisations de l'EcoField :
# la même rétroaction rhizosphère que `plant_uptake` (microbiome riche → meilleure
# assimilation). Pas de nouveau nombre introduit.
from fields.ecofields import UPTAKE_MICRO_BONUS

HEALTH_MAX = 3.0   # santé dynamique entière 3..0 de la sénescence (D27)
FIELD_NORM = 3.0   # normalisation canonique des champs fertilite/microbiome (cf. EcoFields)


def sante(plant) -> float:
    """Santé dynamique normalisée ∈ [0, 1] — lit l'attribut `health` 3..0 géré
    par la sénescence (D27). Une plante morte (0) a une Vigueur nulle."""
    return plant.health / HEALTH_MAX


def maturite(plant) -> float:
    """Avancement de stade ∈ [0, 1] : un semis ≈ 0, un adulte = 1 (spec §1). Helper
    partagé — `sim/actions.py` le réimporte d'ici (mutualisé, pas dupliqué)."""
    n = len(plant.plant_class.growth_stages)
    if n <= 1:
        return 1.0
    return plant.current_stage / (n - 1)


def qi_local(plant, eco) -> float:
    """Qi territorial sous l'empreinte racinaire ∈ [0, 1] (spec §4) — « puiser ».
    Lit `fertilite`/`microbiome` sur chaque plot de `plant.root_plots` via
    l'EcoField, en MIROIR de `plant_uptake` (microbiome riche → meilleure
    assimilation, bonus borné `UPTAKE_MICRO_BONUS`). Moyenne sur l'empreinte,
    clampée [0, 1]. Empreinte vide ⇒ repli sur le plot-foyer. Read-only : aucun
    `add`, donc aucun prélèvement réel — c'est une lecture, pas l'uptake."""
    plots = plant.root_plots or [plant.plot_foyer]
    total = 0.0
    for (r, c) in plots:
        fert = min(1.0, eco.fertilite.at_plot(r, c) / FIELD_NORM)
        micro = min(1.0, eco.microbiome.at_plot(r, c) / FIELD_NORM)
        total += fert * (1.0 + micro * UPTAKE_MICRO_BONUS)
    return max(0.0, min(1.0, total / len(plots)))


def vigueur_plante(plant, eco) -> float:
    """Façade unificatrice (spec §1) : lecture pure, aucune écriture. Produit des
    trois facteurs normalisés et du gène `vigueur` enveloppé tel quel (§6)."""
    return sante(plant) * maturite(plant) * qi_local(plant, eco) * plant.gene("vigueur")


# --- Lecture diégétique : descripteur qualitatif (philo #5 — pas de chiffre) ---
# Seuils PROVISOIRES (à calibrer post-test, comme le reste du modèle Vigueur).
# Voix « naturaliste qui observe » (CLAUDE.md, trois voix narratives). Le bas de
# l'échelle ("imperceptible") couvre aussi bien le semis (maturité ≈ 0) que la
# plante morte (santé 0) : l'œil ne distingue pas la vigueur dans les deux cas.
def decrire_vigueur(v: float) -> str:
    """Traduit la Vigueur dérivée en mot qualitatif pour le carnet/encyclopédie.
    Fonction pure sur le scalaire — testable sans monde."""
    if v <= 0.0:
        return "imperceptible"
    if v < 0.20:
        return "chétif"
    if v < 0.50:
        return "vigoureux"
    return "éclatant"
