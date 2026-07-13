"""
SYMBIOSE — fields/ecofields/marais.py
Responsabilité : la MÉMOIRE DE MARÉCAGE d'une tuile — l'état persistant qui naît
d'une flaque qui dure. Une lame d'eau (`eau_surface`) au-dessus de SEUIL_FLAQUE,
si elle SE MAINTIENT, fait lentement monter `marais_memory` vers 1 ; son absence
la fait redescendre vers 0. Une HYSTÉRÈSE (entrée haute `MARAIS_ON` / sortie basse
`MARAIS_OFF`) en tire l'état binaire `marais_etat` sans clignotement au seuil.

Mixin de comportement de `EcoFields` (sprint hydrologie & marécages ③). Appelé par
la boucle JUSTE APRÈS `tick_ruissellement` (qui pose la lame de surface) et AVANT
`tick_decomposition`/`tick_ph` — qui LISENT `marais_memory` du tick courant pour
raboter la décompo (anaérobie → tourbe émergente) et acidifier le pH (tourbière).
Aucun état propre : opère sur `self`.

Le marécage n'est PAS un type de sol scripté : c'est un état ÉMU (mémoire + seuil,
philo #2/#6). Fonction pure, zéro RNG (déterminisme philo #3). No-op strict tant
que `eau_surface` reste sous SEUIL_FLAQUE partout ET `marais_memory` nulle (aucune
flaque durable) → golden NEUTRE hors banc.
"""

from __future__ import annotations

from .constants import SEUIL_FLAQUE, MARAIS_LERP, MARAIS_ON, MARAIS_OFF


class MaraisMixin:
    """Intégration de la mémoire de marécage + hystérèse d'état persistant."""

    def tick_marais(self) -> None:
        """Un tick d'intégration de `marais_memory` vers sa cible (1 sous flaque,
        0 sinon), au rythme LENT `MARAIS_LERP` (bascule en ~une saison de flaque
        continue — un marais ne naît pas d'une averse). Met à jour ENSUITE l'état
        binaire `marais_etat` par HYSTÉRÈSE : un plot ENTRE en marais quand la mémoire
        franchit MARAIS_ON (haut) et n'en RESSORT que sous MARAIS_OFF (bas). Entre
        les deux seuils l'état PRÉCÉDENT est CONSERVÉ (zone morte anti-clignotement).

        No-op strict si `eau_surface` est nulle partout ET `marais_memory` déjà
        nulle : la cible et la mémoire valent 0, la mémoire reste 0 < MARAIS_OFF →
        `marais_etat` reste False (golden NEUTRE hors banc). Zéro RNG (philo #3)."""
        mem = self.marais_memory
        etat = self.marais_etat
        for r in range(self.rows):
            for c in range(self.cols):
                cible = 1.0 if self.eau_surface.data[r][c] > SEUIL_FLAQUE else 0.0
                cur = mem.data[r][c]
                if cible != 0.0 or cur != 0.0:
                    cur = cur + (cible - cur) * MARAIS_LERP
                    mem.set(r, c, cur)             # GridField borne [0,1]
                    cur = mem.data[r][c]           # relit la valeur bornée
                # Hystérèse : franchir ON entre, passer sous OFF sort, sinon on garde.
                if cur >= MARAIS_ON:
                    etat[r][c] = True
                elif cur < MARAIS_OFF:
                    etat[r][c] = False

    def est_marais(self, r: int, c: int) -> bool:
        """État binaire de marécage du plot, en HYSTÉRÈSE (grille `marais_etat`
        entretenue par `tick_marais`). Sert la SÉMANTIQUE d'état (niche des espèces
        marécageuses ⑤⑥, perception à la vue ⑧) ; les lecteurs GRADUELS des flux
        (décompo, pH) lisent la mémoire CONTINUE `marais_memory`, pas ce prédicat —
        l'hystérèse borne l'état, pas le dosage. False au repos (aucune flaque)."""
        return self.marais_etat[r][c]
