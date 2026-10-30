"""
SYMBIOSE — fields/ecofields/source.py
Responsabilité : les SOURCES d'une tuile — des points où la NAPPE affleure
(résurgence, fond de mare creusé jusqu'à l'eau) et pousse de l'eau dans les pores
chaque semaine. Mixin de comportement de `EcoFields` (sprint SOL NOURRICIER ④,
mare du nord-est). Aucun état propre hors `self.sources`.

📖 Pédagogie — pourquoi une mare a besoin d'une source.
Une mare n'est pas un seau qu'on remplit une fois : la lame libre s'évapore vite
(`EVAP_SURFACE`, 20 %/sem.) et, sur sable, les pores la boivent dès qu'ils ont de
la place. Mesuré (seed 42) : une cuvette remplie à l'init est SÈCHE en 4 semaines
et n'est plus un marais en ~25. Une vraie mare de jardin vit d'une ALIMENTATION —
une nappe qui affleure au fond. C'est la même physique que la nappe de berge de la
ceinture (`bordure.tick_berge`), mais en un POINT au lieu d'une bande de bord :
l'eau entre dans les pores, l'excédent AFFLEURE en lame de surface, puis TOUT le
circuit existant s'en charge sans une ligne de plus (ruissellement vers le fond de
la cuvette, évaporation, mémoire de marais). Le marais ÉMERGE ; rien n'est écrit
sur une plante ni sur une bête (philo #2).

`self.sources` = liste `[(r, c, debit), …]` (débit en unités d'humidité/sem.),
posée à l'init du monde (`sim/mare_initiale.py`). None / vide ⇒ no-op strict ⇒
tuiles sans source (golden smoke, bancs, conteneurs) BIT-IDENTIQUES. Zéro RNG.
"""

from __future__ import annotations

from .constants import HUM_CAP


class SourceMixin:
    """Apport d'eau ponctuel d'une nappe affleurante (résurgence)."""

    def tick_source(self) -> None:
        """Pousse le débit de chaque source dans les pores de son plot ; quand les
        pores sont PLEINS, l'excédent part en LAME DE SURFACE (même geste que
        `tick_berge` : `humidite.add` écrêterait silencieusement à `HUM_CAP` et
        ferait disparaître l'eau). À appeler JUSTE AVANT `tick_hydrology`, comme la
        nappe de berge, pour que l'eau suive tout le circuit hydrologique."""
        for r, c, debit in self.sources or ():
            place = HUM_CAP - self.humidite.data[r][c]
            if debit <= place:
                self.humidite.add(r, c, debit)
            else:                                # pores saturés → l'eau affleure
                self.humidite.set(r, c, HUM_CAP)
                self.eau_surface.add(r, c, debit - place)
