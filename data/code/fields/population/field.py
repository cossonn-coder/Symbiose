"""
SYMBIOSE — fields/population/field.py
`PopulationField` — mécanisme générique de densité d'une guilde (sous-classe
`GridField`). Extrait de `population.py` (scission /refactor 2026-06-30).
"""
from fields.grids import GridField
from fields.population.constants import (
    POP_MAX, T_COLD_ZERO, T_WARM_FULL, W_SOLSTICE_ETE,
    _clamp01, _smoothstep, daylength,
)
from fields.population.spec import TrophicSpec


class PopulationField(GridField):
    """
    Champ de densité d'une guilde macroscopique. Persistant (mémoire/inertie),
    à la différence du scalaire `herbivory_pressure` recalculé sans mémoire.

    Tick (relaxation vers une cible, patron `DisturbanceField`) :
        capacité = clamp(resource_w·ressource + habitat_w·habitat, 0, 1)
        survie   = chaleur · (1 − min(1, pred_w·prédation))
                           · (1 − min(1, disturb_w·perturbation))
        cible    = capacité · survie
        champ'   = clamp(champ·inertie + cible·(1−inertie), 0, MAX)

    Forme MULTIPLICATIVE : la cible ne dépend pas de la pop courante → la guilde
    colonise depuis zéro là où ressource+habitat existent. L'inertie introduit le
    DÉCALAGE temporel proie↔prédateur → cycles boom-bust visibles (§2.1). Le
    froid (chaleur→0 l'hiver) et la famine (pop>capacité) sont implicites.
    """

    def __init__(self, spec: TrophicSpec, rows: int, cols: int):
        super().__init__(rows, cols, initial=0.0, max_val=POP_MAX)
        self.spec = spec
        # Dernière grille de ressource — sert au scalaire `activite` (pur rendu).
        self.activite_grid: list[list[float]] = [
            [0.0] * cols for _ in range(rows)
        ]

    def tick(self, eco, tile, plants, predator_fields: list["PopulationField"],
             week_in_year: int = W_SOLSTICE_ETE) -> None:
        """
        Intègre un tick de dynamique. Lit eco (température, perturbation), les
        plantes (via resource_fn/habitat_fn) et les champs prédateurs ; n'écrit
        QUE sur soi-même. Aucun log, aucune écriture sur les champs existants.

        `week_in_year` ∈ [1,52] pilote la PORTE saisonnière photopériodique
        (`phenology`, §3) — défaut = plein été (réveil maximal) pour que d'anciens
        appels de test sans saison restent neutres ; l'engine passe toujours la
        vraie semaine. `survie = phenology · warmth · (1−préd) · (1−perturb)` :
        phenology dit QUAND la guilde est active, warmth COMBIEN.
        """
        spec = self.spec
        res = spec.resource_fn(eco, tile, plants)
        hab = spec.habitat_fn(eco, tile, plants)
        # Terme additif optionnel (attraction par le fruit tombé, ④). None → 0
        # partout → capacité strictement inchangée (golden neutre sans fruit).
        sig = spec.signal_fn(eco, tile, plants) if spec.signal_fn else None
        # Effet de LISIÈRE (périphérie ③) : champ DU MILIEU `eco.lisiere`, lu SEULEMENT
        # par les guildes qui l'ont déclaré (`lisiere_w > 0`). Absent (aucune ceinture)
        # ou poids nul → `lis is None` → terme non calculé → capacité BIT-IDENTIQUE.
        lis = eco.lisiere if spec.lisiere_w > 0.0 else None
        self.activite_grid = res   # mémorise la ressource pour `activite()`
        # Porte saisonnière : scalaire GLOBAL à la tuile (la photopériode ne varie
        # pas d'un plot à l'autre) → calculé UNE fois hors de la boucle r×c.
        phenology = _smoothstep(daylength(week_in_year),
                                spec.daylen_min, spec.daylen_full)
        for r in range(self.rows):
            for c in range(self.cols):
                temp = eco.temperature.at_plot(r, c)
                warmth = _clamp01((temp - T_COLD_ZERO) / (T_WARM_FULL - T_COLD_ZERO))
                disturb = eco.disturbance.at_plot(r, c)
                predation = sum(pf.at_plot(r, c) for pf in predator_fields)
                pop = self.data[r][c]

                capacite = _clamp01(spec.resource_w * res[r][c]
                                    + spec.habitat_w * hab[r][c]
                                    + (sig[r][c] if sig else 0.0)
                                    + (spec.lisiere_w * lis.data[r][c]
                                       if lis is not None else 0.0))
                survie = (phenology * warmth
                          * (1.0 - min(1.0, spec.pred_w * predation))
                          * (1.0 - min(1.0, spec.disturb_w * disturb)))
                cible = capacite * survie
                # Inertie ASYMÉTRIQUE (§4) : décrue rapide / montée au rythme calibré.
                inertie = spec.inertia_decay if cible < pop else spec.inertia
                self.data[r][c] = max(0.0, min(
                    self.max_val,
                    pop * inertie + cible * (1.0 - inertie)
                ))

    def activite(self, r: int, c: int) -> float:
        """
        Scalaire d'ACTIVITÉ [0,1] — la ressource locale disponible (« en nombre
        ET en activité » de l'intention). Pilote la vitesse d'animation / le
        rayon d'errance côté Godot. PUR rendu, zéro impact simulation.
        """
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return self.activite_grid[r][c]
        return 0.0
