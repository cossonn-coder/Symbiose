"""
SYMBIOSE — fields/ecofields/bordure.py
Responsabilité : ce que la CEINTURE écrit dans les champs de la tuile aux BORDS du
jardin — deux conditions aux limites, sprint PÉRIPHÉRIE ③ (D73), conception §3.4
et §4.2 :

  • `tick_berge`   — la NAPPE d'un secteur en eau pousse de l'eau dans les pores
                     de la première rangée (ou l'en retire si le lit est en creux) ;
  • `maj_lisiere`  — le champ du milieu `eco.lisiere` ∈ [0,1], gradient d'effet de
                     lisière depuis chaque bord, que chaque guilde lit à SA manière
                     (`TrophicSpec.lisiere_w`) ;
  • `tick_erosion` — les COLLUVIONS d'un secteur dénudé ou d'une falaise entaillée
                     (⑤, §4.5) : `structure_sol` déstructurée, humus dilué.

Ces deux flux ne sont PAS géométriques (contrairement à l'ombre et à l'abri du ②,
qui passent par les obstacles de `light`/`abri`) : ils s'écrivent directement dans
les champs, sur la bande de plots que `peripherie.plots_de_bord` délimite. Aucune
grille n'est balayée en entier (réflexe D32).

Mixin de comportement de `EcoFields`. Aucun état propre : opère sur `self`.
No-op strict sans ceinture (`None`) ⇒ champs bit-identiques ⇒ golden INTACT.
"""

from __future__ import annotations

from fields.fleurs_lisiere import fleurs_actives, plots_nourris
from fields.grids import GridField
from fields.peripherie import (plots_de_bord, DENSITE_FORET, NOMS_COTES,
                               erosion_secteur)
from .constants import (HUM_CAP, BERGE_PORTEE_CM, BERGE_FLUX_PAR_CM,
                        LISIERE_PORTEE_CM, INTENSITE_LISIERE,
                        LISIERE_TYPES_LIGNEUX, LISIERE_SOCLE,
                        EROSION_PORTEE_CM, EROSION_STRUCTURE, EROSION_HUMUS,
                        EROSION_SIGNE_SEUIL)

# Marqueur de log du signe d'ÉBOULIS (philo #5 : le sol qui part se VOIT, il ne se
# lit pas sur un compteur). Style des marqueurs de tuile du tick (💧 rosée, ❄ gelée,
# 🍂 transport éolien). Le parseur de `sim/evenements.py` l'apprendra au tronçon ⑥
# (événement « 1ᵉʳ éboulis », conception §7) ; d'ici là une ligne non reconnue est
# ignorée sans dommage.
MARQUEUR_EBOULIS = "🪨"

# Densité de référence d'une strate ligneuse PLEINE = le haut de la plage des forêts
# du générateur. DÉRIVÉE, jamais recopiée : si le ① recalibre `DENSITE_FORET`, la
# normalisation suit.
_DENSITE_PLEINE = DENSITE_FORET[1]


def intensite_lisiere(secteur: dict) -> float:
    """Intensité d'effet de lisière d'UN secteur, au contact de son bord.

    `INTENSITE_LISIERE[type]` donne l'ARCHÉTYPE (une forêt est une lisière au sens
    plein, une prairie un simple ourlet) ; pour les types à strate ligneuse
    (`LISIERE_TYPES_LIGNEUX`) la `densite_ligneuse` en module l'intensité de façon
    AFFINE et MONOTONE croissante, entre `LISIERE_SOCLE` (coupe rase : il reste la
    litière et l'ourlet) et 1.0 (canopée pleine). C'est ce qui fait qu'un abattage du
    ④ se VOIT sur le corridor : le type ne change pas, la densité, elle, s'effondre.

    Les types sans strate ligneuse ne sont PAS modulés (leur densité est nulle par
    construction — les moduler les annulerait). PURE, aucun effet de bord."""
    base = INTENSITE_LISIERE.get(secteur["type"], 0.0)
    if base <= 0.0 or secteur["type"] not in LISIERE_TYPES_LIGNEUX:
        return base
    norm = min(1.0, max(0.0, secteur["densite_ligneuse"] / _DENSITE_PLEINE))
    return base * (LISIERE_SOCLE + (1.0 - LISIERE_SOCLE) * norm)


class BordureMixin:
    """Conditions aux limites de la périphérie : nappe de berge + champ de lisière."""

    # --- Nappe de berge : condition aux limites hydrique (§3.4) -------------

    def tick_berge(self, ceinture, tile_origin: tuple = (0.0, 0.0)) -> None:
        """Échange d'eau entre la nappe d'un secteur EN EAU et les pores des plots
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

        Le critère est la LIGNE D'EAU, pas le type de secteur (généralisation du ⑤) :
        le générateur ne pose `ligne_eau` que sur les `riviere` (donc les ceintures
        générées se comportent BIT POUR BIT comme au ③), mais le joueur peut creuser
        une mare dans une prairie de bordure — et une mare est une nappe comme une
        autre. Tester le type aurait rendu `creuser` muet hors rivière.

        No-op strict si la ceinture est absente ou ne porte aucune ligne d'eau non
        nulle. Zéro RNG (philo #3)."""
        for secteur in ceinture or ():
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
        les quatre bords, intensité donnée par `intensite_lisiere` (archétype du TYPE
        × densité ligneuse pour les types boisés), combinée par MAXIMUM entre bords
        (un coin n'est pas deux fois une lisière).

        MÉMOÏSÉ sur une signature (type ET densité ligneuse de chaque secteur, +
        offset de tuile) : la ceinture est quasi statique, le champ est donc calculé
        UNE fois et réutilisé tel quel — on ne recalcule jamais dans un tick ce qui
        l'a déjà été. La densité entre dans la signature depuis le ④ : une coupe ne
        change pas le TYPE d'un secteur (une forêt rasée reste une forêt qui se
        régénère), donc sans elle une éclaircie ne serait JAMAIS vue.

        LAZY : sans ceinture, `eco.lisiere` reste **None** (aucune allocation) et son
        unique lecteur (`PopulationField.tick`) saute alors le terme → capacité de
        charge bit-identique → golden INTACT. Patron de `eco.turbulence` (②)."""
        sig = (tuple((s["cote"], s["type"], s["densite_ligneuse"])
                     for s in ceinture or ()), tile_origin)
        if sig == self._lisiere_sig:
            return
        self._lisiere_sig = sig

        # Intensité calculée UNE fois par secteur (pas par plot) — elle ne dépend que
        # de l'état du secteur, la distance au bord n'entre que dans `poids`.
        actifs = [(s, i) for s, i in ((s, intensite_lisiere(s))
                                      for s in (ceinture or ())) if i > 0.0]
        if not actifs:
            self.lisiere = None
            return
        if self.lisiere is None:
            self.lisiere = GridField(self.rows, self.cols, max_val=1.0)
        else:
            self.lisiere.fill(0.0)        # ceinture changée : on repart d'un fond nul
        for secteur, intensite in actifs:
            for r, c, poids in plots_de_bord(secteur["cote"],
                                             self.rows, self.cols,
                                             tile_origin, LISIERE_PORTEE_CM):
                valeur = intensite * poids
                if valeur > self.lisiere.data[r][c]:
                    self.lisiere.set(r, c, valeur)

    # --- Colonies de fleurs : le garde-manger des butineurs (D124, §3.2) --------

    def maj_fleurs_bord(self, ceinture, seed: int, week_in_year: int,
                        tile_origin: tuple = (0.0, 0.0)) -> None:
        """Publie `eco.fleurs_bord` pour la semaine : ce que les colonies en fleur
        offrent à cette tuile, ou `None`. La carte des plots est MÉMOÏSÉE sur la
        ceinture (patron `maj_lisiere`) ; seul le scalaire de floraison change chaque
        semaine. Sans ceinture : `None`, ressource bit-identique, golden INTACT."""
        if not ceinture:
            return
        sig = (seed, tuple((s["cote"], s["type"]) for s in ceinture), tile_origin)
        if sig != self._fleurs_sig:
            self._fleurs_sig = sig
            self._fleurs_plots = plots_nourris(seed, ceinture, self.rows, self.cols,
                                               tile_origin)
        self.fleurs_bord = fleurs_actives(self._fleurs_plots, week_in_year)

    # --- Érosion de bordure : les colluvions (§4.5) -------------------------

    def tick_erosion(self, ceinture, tile_origin: tuple = (0.0, 0.0)) -> list[str]:
        """Dépose les COLLUVIONS d'un secteur dénudé (coupe rase) ou d'une falaise
        entaillée sur les plots de son bord : `structure_sol` déstructurée et
        `om_stable` dilué, avec décroissance sur 3 plots. Renvoie les marqueurs de log
        du signe d'éboulis (liste VIDE le reste du temps).

        C'est le SEUL retour de ce sprint qui laisse une trace dans le sol, et le seul
        qui rende l'entaille de falaise (irréversible) visible. Pas un malus : un flux
        de matière minérale, dont les mécaniques en place tirent ensuite les
        conséquences (infiltration, asphyxie, uptake, rétention) — philo #2.

        L'intensité vient de `peripherie.erosion_secteur` (état du secteur SEUL). Elle
        se referme d'elle-même quand la repousse ramène le couvert : l'érosion cesse
        quand la végétation revient, sans qu'aucune ligne ne le dise (philo #6).

        Le SIGNE est émis une fois par ÉPISODE, pas chaque semaine — verrou
        `secteur["erosion_signalee"]`, ré-armé quand le sol cesse de partir. C'est
        l'événement « 1ᵉʳ éboulis » de la conception §7 ; sans ce verrou une cicatrice
        de falaise (permanente) noierait le carnet d'une ligne hebdomadaire.

        No-op strict sans ceinture (cas du golden) ou sans secteur érodant : aucune
        écriture, aucune allocation. Une tuile qui ne touche aucun bord érodant ne
        reçoit RIEN et ne déclenche AUCUN signe (`touche`). Zéro RNG (philo #3)."""
        lignes: list[str] = []
        for secteur in ceinture or ():
            intensite = erosion_secteur(secteur)
            if intensite <= 0.0:
                secteur["erosion_signalee"] = False      # le sol tient : signe ré-armé
                continue
            touche = False
            for r, c, poids in plots_de_bord(secteur["cote"],
                                             self.rows, self.cols,
                                             tile_origin, EROSION_PORTEE_CM):
                part = intensite * poids
                self.structure_sol.add(r, c, -EROSION_STRUCTURE * part)
                self.om_stable.add(r, c, -EROSION_HUMUS * part)
                touche = True
            if (touche and intensite >= EROSION_SIGNE_SEUIL
                    and not secteur.get("erosion_signalee")):
                secteur["erosion_signalee"] = True
                lignes.append(f"  {MARQUEUR_EBOULIS} le sol part au bord "
                              f"{NOMS_COTES[secteur['cote']]} [{self.tile_id}] : "
                              f"de la terre nue descend sur les premiers plots")
        return lignes
