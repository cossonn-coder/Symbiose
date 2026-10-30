"""
SYMBIOSE — sim/mare_initiale.py
Responsabilité : poser, à l'INIT du monde `full`, une MARE déjà remplie et peuplée
dans la tuile NE (nord-est du monde) (sprint SOL NOURRICIER ④, D120,
docs/champs/sol/conception_sol_nourricier.md §3.4).

Pure composition de l'état du milieu — aucune mécanique de tick ici. On amorce ce
qu'une mare installée depuis des années serait déjà :
  - une CUVETTE (fond plat, berge en pente douce autour) → minimum hydraulique,
    l'eau du `tick_ruissellement` reste au fond au lieu de fuir ;
  - une SOURCE au fond (nappe affleurante, `fields/ecofields/source.py`) et un
    suintement plus faible en berge → la mare se REMPLIT d'elle-même chaque semaine ;
  - sol saturé, lame d'eau, mémoire de marais installée, pH déjà tourbeux (patron
    `bancs/hydrologie.tourbiere`, appliqué à un groupe de plots) ;
  - la guilde végétale de mare (aulne en berge, sphaigne + rossolis en bordure
    tourbeuse) et la faune de mare (moustique, libellule) amorcées.

Hors tick, hors golden : le smoke (`tests/test_golden.build_world`) ne passe jamais
par `main.build_world_full`. Déterministe (positions et valeurs fixes, semis
fondateurs seedés). Appelé par `main.build_world_full` → la mare existe aussi dans
la config `propre` (même monde) et dans la démo `main.py`.
"""

from __future__ import annotations

from plants import PLANT_CATALOGUE, PERENNIAL_CATALOGUE
from sim.seeds import semer_fondateur

# --- Géométrie (tuile NE 11×11 : lignes = nord→sud, colonnes = ouest→est) -------
# Fond 3×3 en (7..9, 4..6), au SUD de la tuile, là où `plant_garden` ne sème rien
# (ses semis occupent les lignes 0..5). PAS dans le coin nord-est : ce coin est à
# moins de 150 cm des bords nord et est du MONDE, donc sous la nappe de la ceinture
# (`tick_berge`, portée `BERGE_PORTEE_CM`) — mesuré au seed 1, une rivière en creux
# au nord y draine 0,75/sem. et la mare était sèche dès la 16ᵉ semaine. Ici elle est
# hors de portée des deux bords (lignes ≥ 3, colonnes ≤ 7) : remplie quel que soit
# le terrain. Fond DÉCOLLÉ des bords de tuile (une lame sur un plot de bord fuit
# au ruissellement). Berge = l'anneau autour du fond.
MARE_FOND = [(r, c) for r in range(7, 10) for c in range(4, 7)]
MARE_BERGE = ([(6, c) for c in range(3, 8)] + [(10, c) for c in range(3, 8)]
              + [(r, 3) for r in range(7, 10)] + [(r, 7) for r in range(7, 10)])

# --- Relief : fond PLAT, berge en pente douce (cm, cf. ALT_BASE=20 ± 20) ------
# Fond plat : la fraction ruisselée ne dépend pas de la pente, seulement de son
# signe — un fond creusé au centre vidait les 8 plots autour dans le seul plot
# central (mesuré : 3/9 plots en eau). À plat, chaque plot du fond garde sa lame ;
# la berge plus haute empêche toute fuite vers le jardin.
ALT_FOND = 2.0       # fond de cuvette (patron `tourbiere`)
ALT_BERGE = 12.0     # berge, au-dessus du fond et sous le terrain naturel moyen

# --- Eau (patron `tourbiere` : HUM_SATUREE 3.0, EAU_FLAQUE 1.2, MARAIS 0.85) ----
HUM_SATUREE = 3.0        # pores pleins (= HUM_CAP)
HUM_BERGE = 2.4          # berge gorgée sans être noyée
EAU_FLAQUE = 1.2         # lame installée (>> SEUIL_FLAQUE 0.10)
MARAIS_INSTALLE = 0.85   # mémoire déjà au-dessus de MARAIS_ON (0.60)
# Débits de la nappe (humidité/sem.). PLACEHOLDERS calibrés à la mesure (seed 42,
# 104 sem.) : le fond doit garder une lame toute l'année malgré EVAP_SURFACE (20 %)
# et le drainage du sable ; la berge reçoit un suintement qui la garde humide sans
# l'inonder (les pores la boivent, presque rien n'affleure).
DEBIT_FOND = 0.30
DEBIT_BERGE = 0.03

# pH d'une bordure tourbeuse installée (sable 5,8 → la sphaigne et le rossolis,
# acidophiles stricts ph_opt 4,2 ± 1,0, n'y lèveraient pas). Le marais pousse
# ensuite lui-même vers PH_TOURBE (4,5) : on amorce, la dérive entretient.
PH_TOURBE_INSTALLEE = 4.8

# --- Faune de mare amorcée (densités ∈ [0,1], ensuite la dynamique décide) ------
FAUNE_AMORCE = {"moustique": 0.10, "libellule": 0.05}

# --- Plantes de mare : (clé catalogue, ligne, colonne) --------------------------
# Aulnes sur la berge SUD : leur ombre, portée vers le nord, tombe d'abord sur la
# mare. Sphaigne et rossolis sur la bordure tourbeuse nord, ouest et est. (Mesuré
# dans un premier placement : un aulne posé dans un angle de tuile s'asphyxiait,
# vitalité 0,2 en fin d'an 2 — on le garde hors des angles.)
SEMIS_MARE = [
    ("aulne",    10, 3), ("aulne",    10, 7),
    ("sphaigne",  6, 4), ("sphaigne",  6, 5), ("sphaigne",  8, 3),
    ("drosera",   6, 6), ("drosera",   8, 7),
]


def poser_mare(tile, eco, seed: int) -> None:
    """Sculpte, remplit et peuple la mare sur `tile`/`eco` (tuile NE du monde
    `full`). Écrit seulement des champs du MILIEU + des semis fondateurs ; la
    suite (eau qui circule, marais qui se maintient, faune qui suit l'eau) émerge
    des ticks existants."""
    for r, c in MARE_FOND:
        eco.altitude.set(r, c, ALT_FOND)
        eco.humidite.set(r, c, HUM_SATUREE)
        eco.eau_surface.set(r, c, EAU_FLAQUE)
        eco.marais_memory.set(r, c, MARAIS_INSTALLE)
        eco.marais_etat[r][c] = True        # mémoire > MARAIS_ON : déjà un marais
        eco.ph.set(r, c, PH_TOURBE_INSTALLEE)
        for nom, densite in FAUNE_AMORCE.items():
            eco.populations[nom].set(r, c, densite)
    for r, c in MARE_BERGE:
        eco.altitude.set(r, c, ALT_BERGE)
        eco.humidite.set(r, c, HUM_BERGE)
        eco.ph.set(r, c, PH_TOURBE_INSTALLEE)
    eco.sources = ([(r, c, DEBIT_FOND) for r, c in MARE_FOND]
                   + [(r, c, DEBIT_BERGE) for r, c in MARE_BERGE])
    for espece, r, c in SEMIS_MARE:
        cls = PLANT_CATALOGUE.get(espece) or PERENNIAL_CATALOGUE[espece]
        p = semer_fondateur(tile, cls, r, c, seed)
        # Tapis de sphaigne et rosettes de rossolis DÉJÀ installés (la mare a des
        # années) : on les sort du stade semis, sans quoi la fonte des semis du sol
        # détrempé les emportait en ~6 semaines (mesuré). L'aulne reste un jeune
        # plant (ligneux procédural : sa structure suit son âge réel).
        if p is not None and not cls.procedural_growth:
            p.advance_stage()
