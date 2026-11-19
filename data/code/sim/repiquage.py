"""
SYMBIOSE — sim/repiquage.py
Le CHOC DE REPIQUAGE (D140 C.5, sprint DÉPART DU JARDIN ④,
docs/vegetal/genetique/conception_depart_jardin.md §2 C.5).

📖 Pédagogie (Nico) — que se passe-t-il quand on sort un plant de son pot ?
  La motte part avec la plante, mais le CHEVELU (les radicelles fines, qui font
  l'essentiel de l'absorption) se déchire sur les bords. Si la plante était À
  L'ÉTROIT, ses racines tournaient en rond contre la paroi (le « chignon ») : il
  faut les défaire, on en casse beaucoup plus. Deux conséquences physiques, AUCUN
  malus de vitalité (philo #1/#2) :
    1. moins de radicelles → la plante ABSORBE moins, même en sol frais : ses
       feuilles ferment leurs stomates (`sim/bilan.f_eau`, plafond 1 − coupe) ;
    2. refaire ce chevelu COÛTE du carbone, payé sur le bilan de la semaine
       (`sim/bilan.semaine_bilan`) : la croissance ralentit tant qu'elle reconstruit.
  Le chevelu repousse quand la plante est active (pas dans un sol trop froid pour
  elle : un tendre repiqué trop tôt reste assoiffé — on apprend le calendrier).

Ce module porte aussi la LIGNE DE LOG du repiquage (patron `sim/lignee.py`) : le
geste l'écrit dans `game_state["log"]`, `sim/evenements` la relit pour le carnet.
Écrire et lire au même endroit : le format ne peut pas diverger.

Pur (sauf `couper_racines`/`reprendre_racines`, qui écrivent `racines_coupees`),
zéro RNG (philo #3). Couche `sim` : lit `plants` seulement. Golden : le smoke ne
repique jamais → `racines_coupees` reste 0 → aucun effet.
"""
from __future__ import annotations

import re

from plants.physiologie import parametres_bilan

# Part du chevelu perdue avec une motte BIEN TENUE (plant à l'aise dans son pot) :
# seules les radicelles du pourtour cassent. Ordre de grandeur horticole : un plant
# en motte reprend en une à deux semaines.
COUPE_MOTTE = 0.25
# Supplément quand les racines étaient À L'ÉTROIT (`serrage` = 1 : pot saturé, cf.
# `world.container.Container.serrage`) : chignon défait, ~70 % du chevelu perdu.
COUPE_CHIGNON = 0.45
# Au-delà de ce serrage, le carnet parle de chignon (la plante était à l'étroit).
SEUIL_CHIGNON = 0.5
# Part du chevelu refaite au plus par semaine d'activité — même rythme que la
# refeuillaison (`bilan.REFEUIL_MAX`) : quelques semaines pour une motte entière.
REPRISE_RACINES = 0.15


def couper_racines(plant, serrage: float) -> str:
    """Applique la perte de chevelu du repiquage à `plant` (cumulée avec ce qui
    n'a pas encore repoussé) et renvoie la cause du carnet (`motte`/`chignon`).
    `serrage` ∈ [0, 1] : 0 = racines à l'aise, 1 = pot saturé de racines."""
    s = max(0.0, min(1.0, serrage))
    coupe = COUPE_MOTTE + COUPE_CHIGNON * s
    plant.racines_coupees = min(1.0, plant.racines_coupees + coupe * (1.0 - plant.racines_coupees))
    return "chignon" if s >= SEUIL_CHIGNON else "motte"


def reprendre_racines(plant, active: bool) -> float:
    """Une semaine de reprise : refait jusqu'à `REPRISE_RACINES` du chevelu perdu
    si la plante est active (ni dormante ni figée par le froid) et renvoie le COÛT
    en semaines d'entretien, à retrancher du bilan. Le coût d'un chevelu complet est
    pris égal à celui d'un feuillage complet (`cout_feuillage`) : chez un plant
    herbacé, racines fines et feuilles pèsent du même ordre. 0 si rien à refaire."""
    coupe = plant.racines_coupees
    if coupe <= 0.0 or not active:
        return 0.0
    d = min(coupe, REPRISE_RACINES)
    reste = coupe - d
    plant.racines_coupees = reste if reste > 1e-6 else 0.0
    return parametres_bilan(plant.plant_class)["cout_feuillage"] * d


# --- Ligne de log du repiquage ------------------------------------------------
# `  🪴 Repiquage [S] @(9, 13) : tomate, chignon`
# La tuile est DANS la ligne (écrite hors tick, avant les en-têtes du tick suivant).
MARQUEUR = "🪴"
_RE = re.compile(r"🪴 Repiquage \[([^\]]+)\] @\((\d+), (\d+)\) : ([a-z_]+), ([a-z_]+)")


def ligne_repiquage(tile_id: str, r: int, c: int, espece: str, cause: str) -> str:
    """La ligne que `repiquer` écrit (espèce = clé du catalogue)."""
    return f"  {MARQUEUR} Repiquage [{tile_id}] @({r}, {c}) : {espece}, {cause}"


def lire_repiquage(line: str):
    """(tile_id, (r, c), espece, cause) d'une ligne de repiquage, sinon None."""
    if MARQUEUR not in line:
        return None
    m = _RE.search(line)
    if not m:
        return None
    return (m.group(1), (int(m.group(2)), int(m.group(3))), m.group(4), m.group(5))
