"""
SYMBIOSE — fields/ecofields/ph.py
Chimie acide-base du sol : calcul PUR de la dérive décennale du champ `ph`.

Isolé de `container.py` (déjà le fichier le plus dense du dépôt) pour le garder
sous le seuil de taille : le conteneur n'expose qu'une fine méthode `tick_ph` qui
délègue ici. Fonction pure, zéro RNG, zéro log — déterminisme philo #3.

Modèle (tronçon ①) — dérive lente vers une cible héritée puis acidifiée :

    cible[r,c] = ph_roche[soil_type]                      (état hérité, dominant)
               − ACIDIF_OM    · om_fresh_norm[r,c]        (acides humiques de la litière)
               − ACIDIF_LEACH · leach_norm[r,c]           (lessivage du calcium, climat humide)
    ph[r,c]   += (cible − ph[r,c]) · PH_INERTIA / (1 + cec[r,c])
    ph[r,c]    = clamp(ph, PH_MIN, PH_MAX)                (borné par le GridField)

`ph_roche[soil_type]` (table PH_PAR_SOL) est l'héritage roche-mère : une tuile
sableuse part acide (5.8), une calcaire alcaline (7.6). C'est l'état DOMINANT — la
litière et le lessivage ne font que l'infléchir lentement (forte inertie).

`om_fresh_norm` réutilise la masse de litière du plot normalisée par LITIERE_REF
(comme le terme isolation de la thermique) : un sol couvert d'humus frais
s'acidifie. `leach_norm` réutilise l'humidité normalisée (faute de grandeur de
drainage par plot) : un sol humide lessive son calcium → s'acidifie.

`cec` (capacité d'échange cationique, volet NPK B) amortira la dérive d'un sol
argilo-humique. Il n'existe pas encore → `cec = 0` (tampon neutre, dénominateur
= 1) ; le pH fonctionne sans, la dépendance est douce. L'amendement (`AMEND_PUSH`,
poussée chaux/soufre) est réservé au tronçon ⑥.

⚠️ Au tronçon ① ce champ est POSÉ mais lu par PERSONNE (ni uptake, ni croissance,
ni germination) → golden NEUTRE : on ajoute un champ qui n'influence aucun calcul.
"""

from __future__ import annotations

from .constants import (PH_PAR_SOL, PH_INERTIA, ACIDIF_OM, ACIDIF_LEACH,
                        LITIERE_REF)


def tick_ph(eco, cec: float = 0.0) -> None:
    """Met à jour `eco.ph` (dérive décennale) depuis le `soil_type` hérité de la
    tuile (cible roche-mère), la litière (`om_fresh_at`, acidification organique)
    et l'humidité (`humidite`, proxy de lessivage). `cec` = tampon optionnel du
    volet NPK (0 = aucun amortissement). Pure : n'écrit QUE `ph`."""
    base = PH_PAR_SOL.get(eco.soil_type, PH_PAR_SOL["terre"])
    damp = PH_INERTIA / (1.0 + cec)
    ph = eco.ph
    for r in range(eco.rows):
        for c in range(eco.cols):
            om_norm    = min(1.0, eco.om_fresh_at(r, c) / LITIERE_REF)
            leach_norm = min(1.0, eco.humidite.at_plot(r, c) / 3.0)
            cible = base - ACIDIF_OM * om_norm - ACIDIF_LEACH * leach_norm
            cur   = ph.data[r][c]
            ph.set(r, c, cur + (cible - cur) * damp)   # GridField clampe [PH_MIN, PH_MAX]
