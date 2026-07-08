"""
SYMBIOSE — fields/ecofields/paillage.py
Responsabilité : le champ scalaire `paillage` (profondeur/densité du mulch au sol,
∈ [0,1] par plot) + sa NATURE (`paillage_nature`, sprint équilibre invasion ④) et sa
dynamique de tick — le LEVIER PERMACOLE central contre l'invasion d'adventices
(sprint équilibre invasion ③/④, D69).

Mixin de comportement d'`EcoFields` (comme couverture/hydrologie/ticks). Aucun état
propre : opère sur `self`. Le champ est POSÉ par le geste joueur `pailler`
(`sim/actions/gestes.py`, event-driven) et LU par :
  (a) la germination férale (`sim/succession`) — mulch dense = adventices étouffées,
      + frein allélopathique SUPPLÉMENTAIRE pour les aiguilles (`allelo`) ;
  (b) le vieillissement des graines enfouies (`fields/seedbank.tick_aging`) — sous
      mulch la banque locale s'épuise plus vite ;
  (c) l'évaporation (`hydrologie.tick_hydrology`) — mulch = barrière d'évaporation,
      le sol reste plus frais/humide, MODULÉE par la nature (`humidite_w`).
Ici on ne fait QUE la dynamique propre du champ : décroissance (le mulch se décompose
/ s'incorpore, VITESSE selon la nature) et REVERSEMENT de la part décomposée SELON LA
NATURE — vers l'humus `om_stable` (paille/aiguilles) OU vers la litière `bois` (BRF,
C-riche : route la FAIM D'AZOTE et le MYCÉLIUM via les lecteurs existants), plus une
poussée de pH pour les aiguilles (acidifiantes, patron amendement). La rétention
d'humidité est LUE côté hydrologie (pas un écrit ici) → un seul lecteur écrit
`humidite`, pas de double comptage.

NUL partout au repos (le smoke ne paille jamais, nature "" → NATURE_NEUTRE) → tous les
lecteurs et termes neutres → golden INTACT. Déterministe, zéro RNG (philo #3). C'est un
FLUX (philo #2) : on écrit un CHAMP du milieu, jamais un bonus direct sur une plante.
"""

from __future__ import annotations

from .constants import (PAILLAGE_DECAY, PAILLAGE_OM_W, NATURES_MULCH,
                        NATURE_NEUTRE, AMEND_PUSH, PH_INERTIA)


class PaillageMixin:
    """Champ `paillage` + sa nature + sa décroissance→humus/bois (mixin d'`EcoFields`)."""

    def nature_at(self, r: int, c: int) -> dict:
        """Propriétés (dict `NATURES_MULCH`) de la nature de mulch DOMINANTE du plot,
        ou `NATURE_NEUTRE` si le plot n'est pas paillé (`paillage_nature[r][c] == ""`,
        ou paillage nul). Un seul point de lecture pour tous les consommateurs de nature
        (succession, hydrologie, ici) → data-driven, pas de branche par nature dispersée.
        Repos (nature "") → NATURE_NEUTRE (tous multiplicateurs 1.0, termes extra nuls)
        → lecteurs bit-identiques → golden INTACT."""
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return NATURE_NEUTRE          # hors grille (tile > eco) → neutre, comme GridField.at_plot
        nat = self.paillage_nature[r][c]
        if not nat or self.paillage.data[r][c] <= 0.0:
            return NATURE_NEUTRE
        return NATURES_MULCH.get(nat, NATURE_NEUTRE)

    def poser_mulch(self, r: int, c: int, nature: str, dose: float, cap: float = 1.0) -> None:
        """Déposer `dose` de mulch de `nature` au plot (r,c), cap `cap` (patron du geste
        `pailler`). Fixe la NATURE du plot à `nature` (dernier paillage l'emporte : on
        n'entrelace pas deux natures sur un même plot — modèle SOBRE, la nature dominante
        est celle du dernier geste). Champ borné [0,1] par le GridField."""
        depth = self.paillage.data[r][c]
        self.paillage.set(r, c, min(cap, depth + dose))
        self.paillage_nature[r][c] = nature

    def tick_paillage(self) -> None:
        """Fait DÉCROÎTRE le mulch de chaque plot (`paillage *= 1 − PAILLAGE_DECAY·decay`,
        vitesse selon la nature) et reverse la part décomposée SELON LA NATURE :
          - `vers_bois` (BRF) → litière `bois` (C-riche) : route la FAIM D'AZOTE
            (`bois` ∈ FAIM_N_TISSUS) ET le MYCÉLIUM (`bois_fresh_at`) via les lecteurs
            existants — l'interconnexion sans code neuf ;
          - le complément → humus `om_stable` (paille, aiguilles) ;
          - `ph_shift` (aiguilles) → pousse la CIBLE de pH vers le bas tant que le mulch
            est là (patron amendement AMEND_PUSH, réversible : le mulch parti, la dérive
            repart vers l'héritage). Acidification lente, cohérente avec l'inertie pH.
        Quand le mulch tombe à ~0, la nature du plot est RÉINITIALISÉE ("") → retour à
        NATURE_NEUTRE.

        Le mulch n'est pas éternel : il se décompose et s'incorpore semaine après
        semaine → il faut RE-pailler pour maintenir l'effet (usure de la solution
        facile, philo #1). Ce qui disparaît n'est pas perdu : il NOURRIT le sol
        (flux → contrainte → réponse, philo #2), exactement comme la litière.

        Recalcul par plot, borné par les GridField. Champ NUL partout (repos) → aucun
        plot décomposé → aucun écrit → golden INTACT tant que le joueur ne paille pas.
        À placer dans la boucle APRÈS les lecteurs qui ont besoin de la valeur du tick
        (germination, évaporation) — cf. `sim/engine/boucle.py`."""
        p = self.paillage
        for r in range(self.rows):
            for c in range(self.cols):
                depth = p.data[r][c]
                if depth <= 0.0:
                    continue
                nat = self.nature_at(r, c)
                decompose = depth * PAILLAGE_DECAY * nat["decay"]
                nouveau = depth - decompose
                p.set(r, c, nouveau)
                rendu = decompose * PAILLAGE_OM_W
                vers_bois = nat["vers_bois"]
                if vers_bois > 0.0:                          # BRF : C-riche → litière `bois`
                    self.deposer_litiere(r, c, "bois", rendu * vers_bois)
                if vers_bois < 1.0:                          # complément → humus stable
                    self.om_stable.add(r, c, rendu * (1.0 - vers_bois))
                if nat["ph_shift"] != 0.0:                   # aiguilles : acidification lente (patron amendement)
                    ph = self.ph.at_plot(r, c)
                    cible = ph + nat["ph_shift"] * AMEND_PUSH
                    self.ph.set(r, c, ph + (cible - ph) * PH_INERTIA)
                if nouveau <= 0.001:                         # mulch effacé → oublie la nature
                    p.set(r, c, 0.0)
                    self.paillage_nature[r][c] = ""
