"""
SYMBIOSE — tools/simserver/genes_pont.py
Table des CARACTÈRES génétiques pour la vue (D139, sprint génétique infinitésimale ④).

Le snapshot exporte déjà, par plante neuve, `genes` = {nom: valeur} (dans l'unité du
caractère depuis ③ : °C, semaines, probabilité, facteur) et désormais `F`. Pour que
le survol de debug (touche G, `WorldView.Genes.cs`) écrive « optimum de levée
−2,1 °C » ou « autofécondation 93 % », la vue doit savoir, pour chaque caractère :
  - son UNITÉ (registre moteur `plants/caracteres.py`, source de vérité) ;
  - un LIBELLÉ court en français et un SENS d'affichage (+1/−1) — pure présentation,
    donc ici, côté pont, et pas dans le registre moteur ;
et les deux SEUILS de lecture de F (`sim/lignee.py`, partagés avec le carnet).

📖 Une fois par snapshot (≈ 1 Ko), jamais par plante. Table construite UNE fois à
l'import (registre et seuils sont des constantes) : rien n'est recalculé au tick.
Lecture pure → golden neutre.
"""
from __future__ import annotations

from plants.caracteres import CARACTERES
from sim.lignee import SEUIL_FIXEE, SEUIL_MELANGEE

# Libellé et sens d'affichage. `germination_thermique` est un ABAISSEMENT de
# l'optimum (+1,5 = lève à 1,5 °C plus froid) : la vue l'affiche en décalage
# d'optimum (sens −1 → « optimum de levée −1,5 °C »). `phenologie_florale` est une
# AVANCE (+1 = fleurit une semaine plus tôt). Caractère absent d'ici → son nom brut.
_LIBELLES = {
    "hauteur":               ("hauteur", 1),
    "rusticite_froid":       ("rusticité au froid", 1),
    "vigueur":               ("vigueur", 1),
    "resistance_pathogene":  ("résistance aux maladies", 1),
    "tolerance_secheresse":  ("tolérance à la sécheresse", 1),
    "tolerance_ombre":       ("tolérance à l'ombre", 1),
    "tolerance_asphyxie":    ("tolérance à l'asphyxie", 1),
    "port_trapu":            ("port trapu", 1),
    "germination_thermique": ("optimum de levée", -1),
    "phenologie_florale":    ("avance de floraison", 1),
    "autofecondation":       ("autofécondation", 1),
    "limite_froid":          ("tolérance au froid", 1),
    "limite_chaud":          ("tolérance à la chaleur", 1),
}

TABLE_CARACTERES = {
    "unites": {
        nom: {"unite": car.unite,
              "libelle": _LIBELLES.get(nom, (nom, 1))[0],
              "sens": _LIBELLES.get(nom, (nom, 1))[1]}
        for nom, car in CARACTERES.items()
    },
    # Ordre du REGISTRE (le serveur sérialise avec `sort_keys` : les clés de `unites`
    # arrivent triées par ordre alphabétique, la vue relit donc l'ordre ici).
    "ordre": list(CARACTERES),
    "lignee": {"fixee": SEUIL_FIXEE, "melangee": SEUIL_MELANGEE},
}


def _c(v) -> float | None:
    """°C arrondi au dixième ; None pour « aucune limite » (−∞) ou « pas encore lu »."""
    return None if v is None or v != v or abs(v) == float("inf") else round(v, 1)


def plage_thermique(p) -> dict:
    """PLAGE VIVABLE de la plante en °C (D139 niche thermique ⑤), pour le survol G :
    ses quatre limites EFFECTIVES (espèce + gènes + vécu, `PlantInstance.lim_*`, la
    même source que les dégâts et les signes) et les deux températures qu'elle a
    vécues cette semaine (nuit la plus froide, feuille au jour le plus chaud).
    Chiffres de DEBUG seulement (philo #5) : la vue ne les montre qu'au survol G.
    `froid` = None pour une espèce que le froid sans gel ne lèse pas. Lecture pure."""
    return {"gel": _c(p.lim_gel()), "froid": _c(p.lim_froid()),
            "chaud": _c(p.lim_chaud()), "brulure": _c(p.lim_brul()),
            "nuit": _c(p.t_nuit), "feuille": _c(p.t_feuille)}
