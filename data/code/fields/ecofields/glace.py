"""
SYMBIOSE — fields/ecofields/glace.py
Responsabilité : la GLACE qui prend sur l'eau libre (sprint MARE VIVANTE ①, D121).
Une lame d'eau (`eau_surface > SEUIL_FLAQUE`) se couvre de glace au fil des nuits de
gel et la perd au dégel. État `eco.glace` ∈ [0,1] par plot (0 = eau libre, 1 = prise).

📖 Pédagogie — pourquoi un BILAN et pas un seuil :
  Une mare ne gèle pas à la première nuit à −1 °C : la glace s'épaissit nuit après
  nuit et fond le jour quand l'air se réchauffe. Le tick hebdomadaire fait donc un
  bilan net de la semaine :
      prise = GLACE_PRISE · min(1, froid_nocturne / GLACE_T_REF)
      fonte = GLACE_FONTE · max(0, T_air − GLACE_T_FONTE)
      glace ← clamp(glace + prise − fonte, 0, 1)
  `froid_nocturne` = max(0, −T_min_nuit) lu sur le MÊME thermomètre que le gel des
  plantes (`thermique.t_min_nuit_at`) : neige ou voile posé isolent la mare comme ils
  isolent le sol (un manteau neigeux protège aussi la glace… et la retarde).
  Il faut ainsi plusieurs semaines franchement froides pour « prendre » la mare, et
  une semaine douce l'entame : c'est l'hystérèse naturelle du gel.
  Une lame disparue (évaporée, infiltrée) emporte sa glace : glace = 0 hors lame.

Mixin de comportement de `EcoFields`. Appelé par la boucle JUSTE APRÈS `tick_marais`
(la lame du tick est alors posée par hydrologie + ruissellement). AUCUN effet en
retour dans ce sprint (ni hydrologie, ni faune, ni plantes) : seule la VUE la lit,
via le bloc `marais` du pont → golden NEUTRE. Fonction pure, zéro RNG (philo #3).
"""

from __future__ import annotations

from .constants import SEUIL_FLAQUE
from .thermique import t_min_nuit_at

# PLACEHOLDERS calibrés à la mesure (monde `full`, mare NE, 104 sem.) : le climat
# simulé est DOUX (T_air hebdo ≥ 1,5 °C, nuits au centre de la mare rarement sous
# −0,5 °C [seeds 42/1/2, n=3]). Un 1er réglage « physique » (T_REF 4 °C, fonte dès
# 0 °C) ne prenait JAMAIS la mare. Retenu : mare prise 2 / 9 / 14 sem. sur 104
# [seeds 1/2/42, n=3], toutes au creux du froid (sem. 2-11 de l'année), jamais l'été.
GLACE_PRISE = 0.6     # glace gagnée par une semaine de nuits à −GLACE_T_REF ou plus froid
GLACE_T_REF = 1.0     # °C de froid nocturne qui donnent la prise pleine d'une semaine
GLACE_FONTE = 0.15    # glace perdue par °C de T_air au-dessus de GLACE_T_FONTE
# L'eau de surface d'une mare reste proche de 4 °C (densité maximale de l'eau) : une
# semaine dont l'air moyen ne dépasse pas ~4,5 °C n'apporte pas de quoi fondre la
# plaque que les nuits claires ont formée ; au-delà, l'air doux et le soleil la rongent.
GLACE_T_FONTE = 4.5


def glace_next(glace: float, lame: float, t_min_nuit: float, t_air: float) -> float:
    """Glace du plot après une semaine. PURE : (état, lame, thermomètres) → état."""
    if lame <= SEUIL_FLAQUE:
        return 0.0                                   # pas d'eau libre → pas de glace
    prise = GLACE_PRISE * min(1.0, max(0.0, -t_min_nuit) / GLACE_T_REF)
    fonte = GLACE_FONTE * max(0.0, t_air - GLACE_T_FONTE)
    return min(1.0, max(0.0, glace + prise - fonte))


class GlaceMixin:
    """Prise et fonte de la glace sur les plots en eau (état `self.glace`)."""

    def tick_glace(self, t_air: float, nebulosite: float) -> None:
        """Un pas hebdomadaire de `glace` sur chaque plot. Ne calcule le thermomètre
        nocturne que là où il y a de l'eau (le reste du monde est sec → 0 direct)."""
        lames, glace = self.eau_surface.data, self.glace
        for r in range(self.rows):
            for c in range(self.cols):
                lame, g = lames[r][c], glace.data[r][c]
                if lame <= SEUIL_FLAQUE:
                    if g != 0.0:
                        glace.set(r, c, 0.0)         # la lame partie emporte sa glace
                    continue
                t_min = t_min_nuit_at(self, r, c, t_air, nebulosite)
                glace.set(r, c, glace_next(g, lame, t_min, t_air))
