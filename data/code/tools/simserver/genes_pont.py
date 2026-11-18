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
    # D139 caractères vivants ①-④ (conception §2) : les 20 caractères de la plante
    # vivante. `couleur_fleur` est une POSITION sur l'axe de couleur de l'espèce
    # (−1 = première couleur, +1 = seconde) ; les deux goûts sont dans [−1, 1]
    # (< 0 amer, < −0,3 toxique) ; `aptitude_bouture` est une probabilité.
    "taille_fleur":          ("taille des fleurs", 1),
    "nectar":                ("nectar", 1),
    "pollen":                ("pollen offert", 1),
    "couleur_fleur":         ("couleur sur l'axe", 1),
    "guide_nectar":          ("guides à nectar", 1),
    "parfum":                ("parfum", 1),
    "taille_fruit":          ("taille des fruits", 1),
    "appetence_fruit":       ("goût du fruit", 1),
    "appetence_feuille":     ("goût de la feuille", 1),
    "coriacite_feuille":     ("coriacité de la feuille", 1),
    "repousse":              ("repousse", 1),
    "aptitude_bouture":      ("reprise de bouture", 1),
    "dormance_graine":       ("dormance des graines", 1),
    "dominance_apicale":     ("dominance apicale", 1),
    "vigueur_clonale":       ("vigueur clonale", 1),
    "portee_graine":         ("portée des graines", 1),
    "fixation_azote":        ("fixation d'azote", 1),
    "allelopathie":          ("allélopathie", 1),
    "mycorhization":         ("mycorhization", 1),
}

# GROUPES du survol G (kickoff ⑤ §2) : la vue range les caractères sous ces titres,
# dans cet ordre (lignée en tête, lue à part). Un caractère absent d'ici → « autres »
# (la vue ne perd jamais une ligne si le registre grandit avant cette table).
_GROUPES = (
    ("fleurs", ("taille_fleur", "nectar", "pollen", "couleur_fleur", "guide_nectar",
                "parfum", "phenologie_florale", "autofecondation")),
    ("fruits", ("taille_fruit", "appetence_fruit")),
    ("feuille", ("appetence_feuille", "coriacite_feuille", "hauteur", "port_trapu",
                 "dominance_apicale", "vigueur", "resistance_pathogene")),
    ("gestes", ("repousse", "aptitude_bouture")),
    ("sol", ("vigueur_clonale", "portee_graine", "dormance_graine", "fixation_azote",
             "allelopathie", "mycorhization", "tolerance_secheresse",
             "tolerance_asphyxie", "tolerance_ombre")),
    ("chaleur et froid", ("rusticite_froid", "limite_froid", "limite_chaud",
                          "germination_thermique")),
)

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
    # Groupes du survol G (⑤) : [[titre, [noms]]…], ordre d'affichage.
    "groupes": [[titre, [n for n in noms if n in CARACTERES]] for titre, noms in _GROUPES],
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


def fecondation_pont(p) -> dict:
    """LIGNÉE VÉCUE de la plante pour le survol G (D139 caractères vivants ⑤) :
    `fec` = fécondation figée à la fanaison (0 = pas fleurie cette année),
    `donne` = pollen exporté vers d'autres fleurs (paternité), `auto` = part
    autofécondée de ses graines, même règle que `sim/reproduction.heredite`
    (`a / fec` borné à 1 ; hors cycle floral, `a` seul). Chiffres de DEBUG."""
    a, fec = p.gene("autofecondation"), p.fecondation
    auto = min(1.0, a / fec) if fec > 0.0 else a
    return {"fec": round(fec, 3), "donne": round(p.pollen_donne, 3), "auto": round(auto, 3)}
