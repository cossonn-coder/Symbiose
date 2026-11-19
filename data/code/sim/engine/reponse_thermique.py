"""
SYMBIOSE — sim/engine/reponse_thermique.py
La plante répond à SA plage vivable (D139, sprint niche thermique ③).

📖 Pédagogie — trois façons dont la température abîme une plante :
  - le GEL : l'eau des cellules cristallise, les membranes éclatent. Tous les stades y
    passent (un basilic adulte noircit en une nuit) ; la limite dépend de l'espèce, des
    gènes et de l'endurcissement vécu (`lim_gel`). Un pommier endurci tient −30 °C en
    janvier, ses jeunes feuilles gèlent à −3 °C en avril.
  - le FROID SANS GEL : les plantes tropicales (basilic, tomate, courgette…) souffrent
    déjà sous ~10 °C, sans un cristal de glace — leurs membranes se figent, la feuille
    devient translucide puis noircit. Le dégât s'ACCUMULE nuit après nuit
    (`lim_froid`, espèces à `t_froid_lesion` seulement).
  - la BRÛLURE : au jour le plus chaud, une feuille assoiffée au soleil ne transpire
    plus et dépasse l'air de +10 à +15 °C ; au-delà de `lim_brul` le tissu meurt.
    (Sous ce seuil, entre `lim_chaud` et `lim_brul`, la plante ne pousse plus et ne noue
    pas : c'est lu dans `_avancer_stades` et `_tick_fruits`.)

Le moteur ne tue pas, la plante meurt (décision T1). Depuis le sprint STRESS AU BILAN ②
(D140 G), chaque insulte RETIRE ce qu'elle détruit vraiment (`PerteTissus`, marque de
symptôme `gel`/`froid`/`brulure` pour la sémiologie) — plus l'adaptateur `erode` :
  - froid sans gel et brûlure : des FEUILLES perdues ∝ l'écart. La plante vit si ses
    réserves paient la refeuillaison ; sinon elle meurt de faim (bilan) ;
  - gel : feuilles gelées ∝ l'écart sous `lim_gel` ; plus bas encore (marge
    `MARGE_BOURGEONS`, plus large chez les ligneux aux bourgeons écailleux et au bois
    dur), les BOURGEONS et le COLLET gèlent → destruction (cause `gel`) ;
  - ligneux : chaque semaine de gel-dégel embolise un peu les vaisseaux
    (`sim/embolie.maj_gel_degel`, défaillance hydraulique lue par la physiologie).
Les signes par paliers (④) se lisent dans `posture_thermique.py`, sur les MÊMES
limites et pentes (`FROID_LESION_K`, `BRULURE_K` gardés en « points »/°C).

Mixin hérité par l'`Engine` (boucle.py). Déterministe, zéro RNG (philo #3).
"""

from __future__ import annotations

from fields.ecofields.thermique import t_min_nuit_at
from fields.ecofields.constants import VITALITE_STEP
from sim.effects import apply_mutations, deposer_mort
from sim.effects.mutations import PerteTissus
from sim.embolie import maj_gel_degel
from .aleas import FROST_SEVERITY_REF

# Dégât de FROID SANS GEL, en « points » de `ReduceHealth` (1 point = VITALITE_STEP
# = 1/3 de vitalité) par °C sous `lim_froid`, chaque semaine. Calibré au banc
# (`mesures/banc_reponse_mort.py`) : un basilic neutre exposé à des nuits de 6-8 °C
# décline en 3-5 semaines et meurt [cible conception §5].
FROID_LESION_K = 0.25

# Dégât de BRÛLURE (échaudage), en points par °C de feuille au-dessus de `lim_brul`.
# Plus raide que le froid : un tissu cuit ne se répare pas, 3 °C de trop emportent
# la moitié de la plante (resilience 1).
BRULURE_K = 0.5

# Stress au bilan ② : les mêmes pentes en FEUILLAGE retiré (1 point = VITALITE_STEP).
# Plus de division par la constitution `resilience_base` : la tolérance au froid et au
# chaud est DÉJÀ dans les limites d'espèce (`lim_froid`, `lim_brul`, D139).
FROID_FEUILLE_K = FROID_LESION_K * VITALITE_STEP      # 1/12 du feuillage par °C·sem
BRULURE_FEUILLE_K = BRULURE_K * VITALITE_STEP         # 1/6 par °C

# GEL : sous `lim_gel` (premiers dégâts foliaires), la part du feuillage gelée croît
# LINÉAIREMENT avec l'écart effectif (après paillage) et atteint tout le feuillage à la
# marge des bourgeons : une plante dont les bourgeons gèlent n'a déjà plus une feuille.
# Sous `lim_gel − MARGE`, bourgeons et collet gèlent : DESTRUCTION. Herbacée : collet
# au ras du sol (une tomate noircit à −1 °C, meurt vers −5 °C ; une rosette de carotte
# non endurcie perd ses feuilles à −8 °C et repart du collet). Ligneux : bourgeons
# écailleux et bois bien plus durs que la jeune feuille (une gelée d'avril à −6 °C
# noircit les pousses d'un pommier, l'arbre refait ses feuilles). Calibré sur les
# semis posés en plein hiver des bancs catalogue (carotte, bourrache, chanvre).
MARGE_BOURGEONS = 4.0
MARGE_BOURGEONS_LIGNEUX = 8.0


def _marge_bourgeons(plant) -> float:
    return (MARGE_BOURGEONS_LIGNEUX if getattr(plant.plant_class, "ligneux", False)
            else MARGE_BOURGEONS)


def _gel_tissus(plant, effectif: float) -> list:
    """Réponse au GEL (passée à `_mediated_damage`) : `effectif` = sévérité médiée
    (paillage), en unités de `FROST_SEVERITY_REF` → écart effectif en °C sous `lim_gel`.
    Feuilles gelées ∝ l'écart ; au-delà de la marge des bourgeons, destruction."""
    ecart = effectif * FROST_SEVERITY_REF
    if ecart >= _marge_bourgeons(plant):
        return [PerteTissus(plant, plant.feuillage, reason="gel (bourgeons et collet gelés)",
                            cause="gel", destruction=True)]
    return [PerteTissus(plant, min(plant.feuillage, ecart / _marge_bourgeons(plant)),
                        reason="gel (feuilles gelées)", cause="gel")]


class ReponseThermiqueMixin:
    def _tick_nuit_froide(self, tile, eco, t_air: float, nebulosite: float) -> list[str]:
        """Gel (tous stades) puis froid sans gel, lus sur la nuit la plus froide de la
        semaine au plot de chaque plante — calculée UNE fois par plante ici."""
        log = []
        nuit = {id(p): t_min_nuit_at(eco, *p.position, t_air, nebulosite)
                for p in tile.plants if p.is_alive}
        if not nuit:
            return log
        # Mémorisée pour les SIGNES (④, `posture_thermique`) — jamais relue au tick.
        for p in tile.plants:
            if p.is_alive:
                p.t_nuit = nuit[id(p)]

        # 1. GEL — sévérité ∝ (lim_gel − nuit) / FROST_SEVERITY_REF, médiée par le
        #    couvert local dans `_mediated_damage` (paillage, voile). Plus de filtre
        #    `semis` (T5) : la limite endurcie des ligneux remplace l'ancienne exclusion.
        def frost_sev(p):
            return max(0.0, (p.lim_gel() - nuit[id(p)]) / FROST_SEVERITY_REF)
        sevs = [frost_sev(p) for p in tile.plants if p.is_alive]
        if max(sevs) > 0.0:
            log.append(f"  ❄  gel [{tile.tile_id}] t_air={t_air:.1f}°C "
                       f"sév {min(sevs):.2f}→{max(sevs):.2f}")
            log += self._mediated_damage(tile, eco, 0.0, "gel (tissu tendre)",
                                         severity_fn=frost_sev, cause="gel",
                                         seulement_semis=False, reponse=_gel_tissus)

        # 1b. GEL-DÉGEL des ligneux (stress au bilan ②) : sève gelée la nuit, dégel le
        #     jour (`t_air` = moyenne de la semaine) → embolie. Lu par la physiologie.
        for p in tile.plants:
            if p.is_alive and getattr(p.plant_class, "ligneux", False):
                maj_gel_degel(p, nuit[id(p)], t_air)

        # 2. FROID SANS GEL — espèces sensibles seulement (`lim_froid` = −∞ sinon).
        #    Cumulatif : chaque nuit trop froide érode un peu ; la convalescence
        #    (`_tick_senescence_health`) ne rattrape pas une série de nuits fraîches.
        morts = []
        for p in tile.plants:
            if not p.is_alive:
                continue
            ecart = p.lim_froid() - nuit[id(p)]
            if ecart <= 0.0:
                continue
            # SUPPLANTÉ (stress au bilan ②) — adaptateur `erode`, conservé pour mémoire :
            # log += apply_mutations([ReduceHealth(p, ecart * FROID_LESION_K,
            #                                      "froid (lésion sans gel)",
            #                                      cause="froid")], self.game_state)
            perte = min(p.feuillage, ecart * FROID_FEUILLE_K)
            log += apply_mutations([PerteTissus(p, perte, reason="froid (lésion sans gel)",
                                                cause="froid")], self.game_state)
            if not p.is_alive:
                morts.append(p)
        for p in morts:
            deposer_mort(p, eco)
        return log

    def _tick_brulure(self, tile, eco) -> list[str]:
        """Échaudage : la feuille au jour le plus chaud (`plant.t_feuille`, posée par
        `_avancer_stades` ce tick) dépasse `lim_brul` → érosion ∝ l'excès."""
        log = []
        morts = []
        for p in tile.plants:
            if not p.is_alive or p.t_feuille is None:
                continue
            exces = p.t_feuille - p.lim_brul()
            if exces <= 0.0:
                continue
            # SUPPLANTÉ (stress au bilan ②) — adaptateur `erode`, conservé pour mémoire :
            # log += apply_mutations([ReduceHealth(p, exces * BRULURE_K,
            #                                      "brûlure (feuille échaudée)",
            #                                      cause="brulure")], self.game_state)
            perte = min(p.feuillage, exces * BRULURE_FEUILLE_K)
            log += apply_mutations([PerteTissus(p, perte, reason="brûlure (feuille échaudée)",
                                                cause="brulure")], self.game_state)
            if not p.is_alive:
                morts.append(p)
        for p in morts:
            deposer_mort(p, eco)
        return log
