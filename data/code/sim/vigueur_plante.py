"""
SYMBIOSE — sim/vigueur_plante.py
Vigueur des ÊTRES VIVANTS — façade dérivée, PURE, read-only (D11, sous-sprint 3).
Spec de référence : `docs/joueur/vigueur/conception_vigueur.md` §1 (façade dérivée — la
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
from fields.ecofields import (UPTAKE_MICRO_BONUS, MYCO_P_BONUS, bell,
                             CHLOROSE_PH, SEUIL_ACIDOPHILE, CHLOROSE_MALUS,
                             MICROBE_EFFECT_REF)

FIELD_NORM = 3.0   # normalisation canonique des champs fertilite/microbiome (cf. EcoFields)


def sante(plant) -> float:
    """Santé dynamique normalisée ∈ [0, 1] — lit désormais `vitalite` (continue,
    sprint SANTÉ & RÉSILIENCE ① ; ex-`health/3`). Une plante morte (0) a une
    Vigueur nulle."""
    return plant.vitalite


def maturite(plant) -> float:
    """Avancement de stade ∈ [0, 1] : un semis ≈ 0, un adulte = 1 (spec §1). Helper
    partagé — `sim/actions.py` le réimporte d'ici (mutualisé, pas dupliqué)."""
    n = len(plant.plant_class.growth_stages)
    if n <= 1:
        return 1.0
    return plant.current_stage / (n - 1)


def qi_local(plant, eco) -> float:
    """Qi territorial sous l'empreinte racinaire ∈ [0, 1] (spec §4) — « puiser ».
    Lit la nutrition (loi de Liebig : le MINIMUM de N/P/K, ③) et `microbiome` sur
    chaque plot de `plant.root_plots` via l'EcoField, en MIROIR de `plant_uptake`
    (microbiome riche → meilleure assimilation, bonus borné `UPTAKE_MICRO_BONUS`).
    Moyenne sur l'empreinte, clampée [0, 1]. Empreinte vide ⇒ repli sur le
    plot-foyer. Read-only : aucun `add`, donc aucun prélèvement réel — c'est une
    lecture, pas l'uptake.

    Modulé par la FENÊTRE pH d'espèce (tronçon ⑤) : la cloche `bell(ph_local,
    ph_opt, ph_tol)` réduit le Qi puisé hors fenêtre (une espèce mal placée
    « puise/croît moins », elle dépérit doucement en bord de fenêtre) ; plus la
    CHLOROSE alcaline (acidophile sur sol > CHLOROSE_PH → lockout du fer →
    CHLOROSE_MALUS). Défauts NEUTRES (`ph_tol` large) ⇒ `bell ≈ 1.0`, aucun
    acidophile ⇒ pas de chlorose : façade inchangée pour les espèces non
    spécifiées (et le golden ne lit JAMAIS cette façade — cf. en-tête module)."""
    plots = plant.root_plots or [plant.plot_foyer]
    total = 0.0
    ph_sum = 0.0
    # FAIM D'AZOTE NEUTRALISÉE pour la carnivore (hydrologie & marécages ⑥) : son
    # azote vient des PROIES (le puits `_tick_carnivore` sur `moustique`), pas du sol
    # → le N édaphique ne la LIMITE plus. On retire donc N de la loi de Liebig pour
    # une espèce `carnivore` : le minimum ne porte que sur P et K (qui restent
    # limitants → aucun bonus de vitesse, philo #1, elle SURVIT là où les autres
    # carencent en N, elle ne pousse pas plus vite). Read-only, aucun dépôt d'azote
    # dans le sol (son N est INTERNE → ne profite pas aux voisines). NEUTRE : par
    # défaut `carnivore=False` → minimum N/P/K inchangé (aucune carnivore au smoke).
    carnivore = getattr(plant.plant_class, "carnivore", False)
    for (r, c) in plots:
        # ③ MYCORHIZE (miroir de `plant_uptake`) : là où le réseau touche la racine,
        # le P EFFECTIVEMENT prélevable est amplifié (P SEULEMENT). La façade doit
        # suivre l'uptake réel sinon la vigueur perçue ment — mais c'est une LECTURE,
        # aucune mutation de champ (read-only, cf. en-tête module).
        p_eff = eco.p.at_plot(r, c) * (1.0 + MYCO_P_BONUS * eco.mycelium.at_plot(r, c))
        nutri = (min(p_eff, eco.k.at_plot(r, c)) if carnivore
                 else min(eco.n.at_plot(r, c), p_eff, eco.k.at_plot(r, c)))
        fert = min(1.0, nutri / FIELD_NORM)
        micro = min(1.0, eco.microbiome.at_plot(r, c) / MICROBE_EFFECT_REF)
        total += fert * (1.0 + micro * UPTAKE_MICRO_BONUS)
        ph_sum += eco.ph.at_plot(r, c)
    ph_local = ph_sum / len(plots)
    fenetre = bell(ph_local, plant.plant_class.ph_opt, plant.plant_class.ph_tol)
    chlorose = (CHLOROSE_MALUS
                if plant.plant_class.ph_opt < SEUIL_ACIDOPHILE and ph_local > CHLOROSE_PH
                else 1.0)
    return max(0.0, min(1.0, total / len(plots))) * fenetre * chlorose


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
