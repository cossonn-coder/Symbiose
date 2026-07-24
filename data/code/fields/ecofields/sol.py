"""
SYMBIOSE — fields/ecofields/sol.py
Responsabilité : la mémoire et la santé du SOL — banque de graines, mémoire du
sol double-temps (annuelle + décennale), vitalité (grandeur dérivée) et
probabilité de maladie (réponse logistique au microbiome).

Mixin de comportement de `EcoFields` (scission refactor 2026-06-30, container
déjà dense). Aucun état propre : opère sur `self`. Comportement bit-identique
à l'ancien `container.py`.
"""

from __future__ import annotations
import math

from fields.seedbank import SEED_OM_FACILITATION_REF
from .constants import *          # SOIL_SIGNATURE, SOIL_*_RATE, VIT_W_*…


class _OmIndexField:
    """Vue LECTURE SEULE de l'indice de matière organique par plot, exposant la
    même interface `at_plot(r, c)` qu'un `GridField` — pour que la banque-sol
    (`tick_disturbance_enrichment` / `tick_late_succession_enrichment`) le lise
    comme n'importe quel champ, sans allouer une grille à chaque tick.

        om_index = clamp((om_active + om_stable) / SEED_OM_FACILITATION_REF, 0, 1)

    Signal de la facilitation écologique (tronçon ②) : la MO réactive bâtie par
    les pionnières, qui amorce les tardifs et bride le pioneer (cf. seedbank.py).
    """
    __slots__ = ("_active", "_stable")

    def __init__(self, om_active, om_stable):
        self._active = om_active
        self._stable = om_stable

    def at_plot(self, r: int, c: int) -> float:
        om = self._active.at_plot(r, c) + self._stable.at_plot(r, c)
        return min(1.0, max(0.0, om / SEED_OM_FACILITATION_REF))


class SolMixin:
    """Banque de graines, mémoire du sol, vitalité, maladie."""

    # --- Banque de graines ---

    def tick_seed_bank(self, plants: list, seed: int = 0, week: int = 0) -> None:
        """Mise à jour hebdomadaire de la banque de graines."""
        # Le paillage (③, D69) accélère le vieillissement des graines ENFOUIES sous le
        # mulch → épuisement durable de la banque locale. Champ NUL au repos (golden) →
        # vieillissement inchangé (cf. `SeedBank.tick_aging`).
        self.seed_bank.tick_aging(self.paillage)
        self.seed_bank.tick_species_aging()
        om_index = _OmIndexField(self.om_active, self.om_stable)
        self.seed_bank.tick_disturbance_enrichment(self.disturbance, om_index)
        self.seed_bank.tick_late_succession_enrichment(om_index)
        self.seed_bank.tick_plant_production(plants)

    # --- Soil memory ---

    def tick_soil_memory(self, plants: list) -> None:
        """
        Mémoire du sol double temps :
          soil_memory_fast : lerp 0.15 — changements annuels (activité biologique)
          soil_memory_deep : lerp 0.02 — changements décennaux (structure, mycorhizes)
          soil_memory      : 0.7*fast + 0.3*deep (mémoire effective)

        Le sol ne peut pas être réinitialisé instantanément.
        """
        for r in range(self.rows):
            for c in range(self.cols):
                micro = self.microbiome.at_plot(r, c) / 3.0
                fert  = min(1.0, self.fertilite_index(r, c) / 3.0)
                om    = min(1.0, (self.om_fresh_at(r, c) +
                                  self.om_active.at_plot(r, c) +
                                  self.om_stable.at_plot(r, c)) / 5.0)

                # Signature des plantes sur ce plot
                sig = 0.0
                for p in plants:
                    if not p.is_alive:
                        continue
                    if (r, c) == p.position or (r, c) in p.root_plots:
                        family_sig = SOIL_SIGNATURE.get(p.plant_class.family, {})
                        sig += family_sig.get("microbiome", 0.0) * 0.5
                sig = max(-0.2, min(0.2, sig))

                # Cible écologique
                target = (micro * 0.4 + fert * 0.2
                          + om * 0.2 + (0.5 + sig) * 0.2)
                target = max(0.0, min(1.0, target))

                # Mémoire rapide (annuelle)
                fast = self.soil_memory_fast.at_plot(r, c)
                fast += (target - fast) * SOIL_FAST_RATE
                self.soil_memory_fast.set(r, c, fast)

                # Mémoire profonde (décennale)
                deep = self.soil_memory_deep.at_plot(r, c)
                deep += (target - deep) * SOIL_DEEP_RATE
                self.soil_memory_deep.set(r, c, deep)

                # Mémoire effective composite
                effective = fast * 0.7 + deep * 0.3
                self.soil_memory.set(r, c, effective)

    # --- Probabilité de maladie (hybride probabiliste) ---

    def disease_probability(self, r: int, c: int, base_rate: float = 0.3,
                            family=None) -> float:
        """
        Probabilité de propagation maladie — réponse logistique.

        La réponse logistique produit :
          microbiome faible  → presque aucune protection
          microbiome moyen   → phase critique (grande sensibilité)
          microbiome mature  → protection forte et stable

        logistic(x, k=6) = 1 / (1 + exp(-k*(x-0.5)))
        protection = logistic(microbiome_normalisé)
        p = base_rate * (1 + INOC_GAIN·load[family]) * (1 - protection)

        `family` (tronçon ② mémoire d'inoculum, D5) : SI une famille botanique est
        passée, la charge d'inoculum HÔTE-SPÉCIFIQUE persistante du plot amplifie la
        proba de maladie de CETTE famille — replanter la même famille sur une terre
        viciée aggrave la maladie (rotation émergente, philo #2/#6). SANS famille
        (`family=None`, cas du signal SAR `croissance.py`), l'inoculum est IGNORÉ :
        la boucle inoculum→SAR→infection_memory→inoculum est cassée (anti-runaway).
        À INOC_GAIN=0 OU sur un plot vierge (charge=0), formule bit-identique à l'avant-②.
        """
        micro_norm = min(1.0, self.microbiome.at_plot(r, c) / MICROBE_EFFECT_REF)
        protection = 1.0 / (1.0 + math.exp(-6.0 * (micro_norm - 0.5)))
        charge = 0.0 if family is None else self.inoculum.at(r, c, family)
        amplif = 1.0 + INOC_GAIN * charge
        return base_rate * amplif * max(0.02, 1.0 - protection)

    # --- Vitalité (grandeur dérivée, non stockée) ---

    def vitalite(self, r: int, c: int) -> float:
        """
        Vitalité du sol en un plot — grandeur DÉRIVÉE calculée à la demande,
        jamais stockée (décision #2 : le Qi territorial = les champs existants).

        Synthèse lisible de la santé du sol vivant : vie microbienne, réserve de
        fertilité (om_active + fertilite), structure (humus), moins la perturbation.
        Bornée [0, 1]. Préfigure la Vigueur (D11) que plantes et joueur puiseront.
        """
        micro     = min(1.0, self.microbiome.at_plot(r, c) / MICROBE_EFFECT_REF)
        active    = min(1.0, self.om_active.at_plot(r, c) / OM_ACTIVE_REF)
        fert      = min(1.0, self.fertilite_index(r, c) / 3.0)
        structure = min(1.0, self.om_stable.at_plot(r, c) / 5.0)
        disturb   = self.disturbance.at_plot(r, c)
        v = (micro     * VIT_W_MICRO +
             active    * VIT_W_ACTIVE +
             fert      * VIT_W_FERT +
             structure * VIT_W_STRUCTURE -
             disturb   * VIT_W_DISTURB)
        return max(0.0, min(1.0, v))

    def vitalite_average(self) -> float:
        n = self.rows * self.cols
        if not n:
            return 0.0
        total = sum(self.vitalite(r, c)
                    for r in range(self.rows) for c in range(self.cols))
        return total / n
