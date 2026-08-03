"""
SYMBIOSE — sim/actions/couvertures.py
Gestes JOUEUR de COUVERTURE climatique (sprint effondrement météo ③,
`docs/champs/climat/conception_effondrement_meteo.md` §4/§7). Ils complètent
l'appareil de PRÉPARATION §6 de `conception_meteo.md` : trois structures posées en
phase PLANIFICATION (coût MODÉRÉ, philo #1 : préparer coûte moins que réagir dans
l'urgence) qui donnent au joueur le moyen d'ATTÉNUER l'effondrement (tronçon ①).

Modelés sur la famille pose (`compost.poser_bac`, `supports.poser_tuteur`) — geste
BINAIRE : la couverture n'est posée QUE si le coût est intégralement payé (un geste
à vide draine la Vigueur sans rien poser). Chaque geste écrit un CHAMP du milieu sur
`eco` (jamais un bonus direct sur la plante, philo #1/#2) :

  - `poser_voile`    : VOILE d'hivernage sur une ZONE (disque) — relève l'écran
    `couvert_pose` lu par le gel (`t_min_nuit_at`) ET la grêle (`_mediated_damage`).
  - `poser_cloche`   : CLOCHE sur UN plot (empreinte 1×1) — même écran, plus fort,
    pour protéger un individu précis (gel + grêle).
  - `poser_ombriere` : OMBRIÈRE sur une ZONE — occulte la lumière-sol (`ombre_pose`)
    → sol plus frais → moins d'évaporation (mitige canicule / sécheresse).

Concepts de maîtrise associés (déblocage §5, `deblocage.GESTE_UNLOCK`) : la maîtrise
du concept `météo` ouvre les trois gestes ET atténue leur coût (`couts.OBJETS_TOUCHES`
adosse la pose au concept `météo`, déjà fiché) — sans palier acquis → atténuation
neutre 1.0 (dégradation gracieuse §10.5).

Event-driven, hors tick : le smoke n'en pose aucun → `couvert_pose`/`ombre_pose`
restent None → golden NEUTRE par construction.
"""
from __future__ import annotations

from sim.vigueur import spend
from .couts import cout_action, OBJETS_TOUCHES

# Doses et emprises (placeholders de calibrage F5, §4). L'écran d'un voile/cloche
# ∈ [0,1] : 1 = protection quasi totale du plot (le couvert sature → T_min_nuit →
# T_air, plus de gel ; grêle interceptée). L'ombrière occulte la moitié de la
# lumière-sol. Rayons en PLOTS (le voile/l'ombrière couvrent une petite zone, la
# cloche un seul plot).
VOILE_COUVERT     = 0.85   # écran du voile d'hivernage (zone)
CLOCHE_COUVERT    = 0.95   # cloche individuelle (verre/plastique fermé, plus étanche)
OMBRIERE_OMBRE    = 0.5    # l'ombrière coupe la moitié de la lumière-sol
RAYON_VOILE_PLOTS    = 1.5   # une petite planche voilée
RAYON_OMBRIERE_PLOTS = 1.5   # une petite zone ombrée
RAYON_CLOCHE_PLOTS   = 0.0   # empreinte 1×1 (un individu)


def poser_voile(game_state: dict, player: str, eco, r: int, c: int) -> bool:
    """Poser un VOILE d'hivernage centré sur le plot (r,c) — écran `couvert_pose` sur
    une ZONE (§4). Phase PLANIFICATION, coût MODÉRÉ, binaire (posé QUE si payé).
    Renvoie True si posé, False (Vigueur insuffisante)."""
    cost = cout_action(game_state, player, "poser_voile", OBJETS_TOUCHES["poser_voile"])
    if spend(game_state, player, cost) < 1.0:
        return False
    eco.poser_couvert(r, c, VOILE_COUVERT, RAYON_VOILE_PLOTS)
    return True


def poser_cloche(game_state: dict, player: str, eco, r: int, c: int) -> bool:
    """Poser une CLOCHE sur le plot (r,c) — écran `couvert_pose` sur UN plot (§4),
    protection individuelle plus étanche que le voile. Phase PLANIFICATION, coût
    MODÉRÉ, binaire. Renvoie True si posé, False sinon."""
    cost = cout_action(game_state, player, "poser_cloche", OBJETS_TOUCHES["poser_cloche"])
    if spend(game_state, player, cost) < 1.0:
        return False
    eco.poser_couvert(r, c, CLOCHE_COUVERT, RAYON_CLOCHE_PLOTS)
    return True


def poser_ombriere(game_state: dict, player: str, eco, r: int, c: int) -> bool:
    """Poser une OMBRIÈRE centrée sur le plot (r,c) — occultation `ombre_pose` sur une
    ZONE (§4) : atténue la lumière-sol → sol plus frais → moins d'évaporation. Phase
    PLANIFICATION, coût MODÉRÉ, binaire. Renvoie True si posé, False sinon."""
    cost = cout_action(game_state, player, "poser_ombriere", OBJETS_TOUCHES["poser_ombriere"])
    if spend(game_state, player, cost) < 1.0:
        return False
    eco.poser_ombre(r, c, OMBRIERE_OMBRE, RAYON_OMBRIERE_PLOTS)
    return True
