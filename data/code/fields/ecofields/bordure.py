"""
SYMBIOSE — fields/ecofields/bordure.py
Responsabilité : ce que la CEINTURE écrit dans les champs de la tuile aux BORDS du
jardin — deux conditions aux limites, sprint PÉRIPHÉRIE ③ (D73), conception §3.4
et §4.2 :

  • `tick_berge`   — la NAPPE d'un secteur `riviere` pousse de l'eau dans les pores
                     de la première rangée (ou l'en retire si le lit est en creux) ;
  • `maj_lisiere`  — le champ du milieu `eco.lisiere` ∈ [0,1], gradient d'effet de
                     lisière depuis chaque bord, que chaque guilde lit à SA manière
                     (`TrophicSpec.lisiere_w`).

Ces deux flux ne sont PAS géométriques (contrairement à l'ombre et à l'abri du ②,
qui passent par les obstacles de `light`/`abri`) : ils s'écrivent directement dans
les champs, sur la bande de plots que `peripherie.plots_de_bord` délimite. Aucune
grille n'est balayée en entier (réflexe D32).

Mixin de comportement de `EcoFields`. Aucun état propre : opère sur `self`.
No-op strict sans ceinture (`None`) ⇒ champs bit-identiques ⇒ golden INTACT.
"""

from __future__ import annotations

from fields.grids import GridField
from fields.peripherie import plots_de_bord
from .constants import (HUM_CAP, BERGE_PORTEE_CM, BERGE_FLUX_PAR_CM,
                        LISIERE_PORTEE_CM, INTENSITE_LISIERE)


class BordureMixin:
    """Conditions aux limites de la périphérie : nappe de berge + champ de lisière."""

    # --- Nappe de berge : condition aux limites hydrique (§3.4) -------------

    def tick_berge(self, ceinture, tile_origin: tuple = (0.0, 0.0)) -> None:
        """Échange d'eau entre la nappe d'un secteur `riviere` et les pores des plots
        de son bord. À appeler JUSTE AVANT `tick_hydrology` : l'eau déposée suit
        ensuite TOUT le circuit existant sans une ligne de plus — évaporation,
        capture du surplus au-delà de `HUM_CAP` en lame de surface, ruissellement
        vers les creux, puis `marais_memory`. Le marécage de berge ÉMERGE donc, il
        n'est nulle part scripté (philo #2).

        Signe de `ligne_eau` : positif = nappe au-dessus du terrain (elle pousse),
        négatif = lit en creux (il draine). Un drainage n'assèche jamais au-delà du
        sec (le `GridField` borne à 0).

        ⚠️ Quand les pores sont PLEINS, l'excédent part en LAME DE SURFACE — on ne
        peut PAS se contenter de `humidite.add`, qui écrête silencieusement à
        `HUM_CAP` et ferait disparaître l'eau. C'est le même geste qu'à l'étape 5 de
        `tick_hydrology` : une nappe au-dessus du niveau du sol AFFLEURE, elle ne
        s'évapore pas par magie. Sans ça, aucun marécage de berge ne pourrait naître.

        No-op strict si la ceinture est absente ou ne porte aucune rivière à ligne
        d'eau non nulle. Zéro RNG (philo #3)."""
        for secteur in ceinture or ():
            if secteur["type"] != "riviere":
                continue
            ligne = secteur["ligne_eau"]
            if ligne == 0.0:
                continue
            flux = BERGE_FLUX_PAR_CM * ligne
            for r, c, poids in plots_de_bord(secteur["cote"],
                                             self.rows, self.cols,
                                             tile_origin, BERGE_PORTEE_CM):
                delta = flux * poids
                if delta < 0.0:                  # lit en creux : la nappe appelle l'eau
                    self.humidite.add(r, c, delta)
                    continue
                place = HUM_CAP - self.humidite.data[r][c]
                if delta <= place:
                    self.humidite.add(r, c, delta)
                else:                            # pores saturés → l'eau affleure
                    self.humidite.set(r, c, HUM_CAP)
                    self.eau_surface.add(r, c, delta - place)

    # --- Champ de lisière : le milieu, jamais un bonus (§4.2) --------------

    def maj_lisiere(self, ceinture, tile_origin: tuple = (0.0, 0.0)) -> None:
        """(Re)construit `eco.lisiere` — gradient d'effet de lisière ∈ [0,1] depuis
        les quatre bords, intensité selon le TYPE de secteur (`INTENSITE_LISIERE`),
        combinée par MAXIMUM entre bords (un coin n'est pas deux fois une lisière).

        MÉMOÏSÉ sur une signature (types des secteurs + offset de tuile) : la
        ceinture est quasi statique, le champ est donc calculé UNE fois et réutilisé
        tel quel — on ne recalcule jamais dans un tick ce qui l'a déjà été. Une coupe
        forestière (④) change le type d'un secteur ⇒ signature différente ⇒ recalcul.

        LAZY : sans ceinture, `eco.lisiere` reste **None** (aucune allocation) et son
        unique lecteur (`PopulationField.tick`) saute alors le terme → capacité de
        charge bit-identique → golden INTACT. Patron de `eco.turbulence` (②)."""
        sig = (tuple((s["cote"], s["type"]) for s in ceinture or ()), tile_origin)
        if sig == self._lisiere_sig:
            return
        self._lisiere_sig = sig

        actifs = [s for s in (ceinture or ())
                  if INTENSITE_LISIERE.get(s["type"], 0.0) > 0.0]
        if not actifs:
            self.lisiere = None
            return
        if self.lisiere is None:
            self.lisiere = GridField(self.rows, self.cols, max_val=1.0)
        else:
            self.lisiere.fill(0.0)        # ceinture changée : on repart d'un fond nul
        for secteur in actifs:
            intensite = INTENSITE_LISIERE[secteur["type"]]
            for r, c, poids in plots_de_bord(secteur["cote"],
                                             self.rows, self.cols,
                                             tile_origin, LISIERE_PORTEE_CM):
                valeur = intensite * poids
                if valeur > self.lisiere.data[r][c]:
                    self.lisiere.set(r, c, valeur)
