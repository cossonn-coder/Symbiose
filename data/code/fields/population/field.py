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
        # FAIM (D120 ③, pur rendu, jamais relu par la dynamique) : grille servie au
        # scalaire `faim`, + mémoire du tick précédent (capacité, survie) et part du
        # déclin imputée au lieu — de quoi dire POURQUOI la guilde décline.
        self.faim_grid = [[0.0] * cols for _ in range(rows)]
        self._cap_prec = [[0.0] * cols for _ in range(rows)]
        self._surv_prec = [[0.0] * cols for _ in range(rows)]
        self._part_lieu = [[0.0] * cols for _ in range(rows)]

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
        # Boucle CHAUDE (20 guildes × 8 tuiles × ~150 plots par tick) : attributs
        # de `spec` et lignes de grilles hissés en variables locales, lecture
        # directe `data[r][c]` au lieu de `at_plot` (tous ces champs ont les
        # dimensions de la tuile → toujours dans les bornes, le garde-fou de
        # `at_plot` ne servait jamais). Expressions et ORDRE des opérations
        # flottantes strictement inchangés → bit-identique (sprint FLUIDITÉ AN 2 ②).
        resource_w, habitat_w = spec.resource_w, spec.habitat_w
        pred_w, disturb_w = spec.pred_w, spec.disturb_w
        inertia, inertia_decay = spec.inertia, spec.inertia_decay
        lisiere_w = spec.lisiere_w
        max_val = self.max_val
        temp_data, dist_data = eco.temperature.data, eco.disturbance.data
        lis_data = lis.data if lis is not None else None
        pred_datas = [pf.data for pf in predator_fields]
        # Grilles de FAIM (D120 ③, pur rendu) : elles ne font que LIRE `pop`,
        # `capacite`, `survie` déjà calculés — aucune expression de `row[c]` ne
        # change → dynamique bit-identique.
        for r in range(self.rows):
            row = self.data[r]
            faim_row, part_row = self.faim_grid[r], self._part_lieu[r]
            cap_prec_row, surv_prec_row = self._cap_prec[r], self._surv_prec[r]
            temp_row, dist_row = temp_data[r], dist_data[r]
            res_row, hab_row = res[r], hab[r]
            sig_row = sig[r] if sig else None
            lis_row = lis_data[r] if lis_data is not None else None
            pred_rows = [d[r] for d in pred_datas]
            # 0 ou 1 prédateur (la majorité des guildes) : `sum` rendrait 0 (entier)
            # ou 0 + x == x au bit près → on l'évite ; ≥ 2 → `sum` d'origine.
            pred_seul = pred_rows[0] if len(pred_rows) == 1 else None
            for c in range(self.cols):
                temp = temp_row[c]
                warmth = _clamp01((temp - T_COLD_ZERO) / (T_WARM_FULL - T_COLD_ZERO))
                disturb = dist_row[c]
                # `sum` conservé tel quel dès 2 prédateurs (Python ≥ 3.12 : somme
                # flottante compensée, départ entier 0) → même résultat au bit près.
                if pred_seul is not None:
                    predation = pred_seul[c]
                elif pred_rows:
                    predation = sum(pr[c] for pr in pred_rows)
                else:
                    predation = 0
                pop = row[c]

                capacite = _clamp01(resource_w * res_row[c]
                                    + habitat_w * hab_row[c]
                                    + (sig_row[c] if sig else 0.0)
                                    + (lisiere_w * lis_row[c]
                                       if lis is not None else 0.0))
                survie = (phenology * warmth
                          * (1.0 - min(1.0, pred_w * predation))
                          * (1.0 - min(1.0, disturb_w * disturb)))
                cible = capacite * survie
                # FAIM = la part du DÉCLIN que le lieu explique. La guilde décline
                # quand sa cible tombe sous elle : (pop − cible)/pop. Cette cible
                # (capacité × survie) est tombée parce que l'un des deux facteurs a
                # BAISSÉ : le lieu (nourriture + habitat) ou la survie (froid,
                # photopériode, prédateurs, perturbation). On impute le déclin au
                # prorata des baisses relatives de ce tick ; sans baisse nouvelle,
                # l'imputation précédente tient (la décrue d'une chute passée se
                # poursuit). Le déclin d'automne (survie) ou sous les crocs n'est
                # PAS de la faim ; une guilde stable, même rare, n'a pas faim.
                cp, sp = cap_prec_row[c], surv_prec_row[c]
                d_cap = (cp - capacite) / cp if capacite < cp else 0.0
                d_surv = (sp - survie) / sp if survie < sp else 0.0
                if d_cap + d_surv > 0.0:
                    part_row[c] = d_cap / (d_cap + d_surv)
                cap_prec_row[c], surv_prec_row[c] = capacite, survie
                faim_row[c] = (pop - cible) / pop * part_row[c] if pop > cible else 0.0
                # Inertie ASYMÉTRIQUE (§4) : décrue rapide / montée au rythme calibré.
                inertie = inertia_decay if cible < pop else inertia
                row[c] = max(0.0, min(
                    max_val,
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

    def faim(self, r: int, c: int) -> float:
        """
        Scalaire de FAIM [0,1] (D120 ③) — écart relatif population → cible au
        dernier tick, imputé au lieu (nourriture + habitat) au prorata de sa
        baisse (0 = la guilde est stable ou croît, même rare ; ou décline de
        froid / de prédation).
        Lu par la voix des bêtes (`sim/voix_etres`). PUR rendu, zéro impact simulation.
        """
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return self.faim_grid[r][c]
        return 0.0
