"""
SYMBIOSE — sim/clonal.py
Densification clonale (sprint LUXURIANCE, tronçon ②, D65 §2.2 — absorbe D62).

Une plante MATURE de `clonal_mode != "none"` émet des RAMETS — des clones
génétiques (vecteur de gènes COPIÉ de la mère, PAS de brassage sexué, ≠
reproduction.py) — dans son voisinage. Émergent : le tapissage du couvre-sol et
les colonies envahissantes (bambou/menthe au rhizome), SANS flag « envahissant ».

UNE mécanique paramétrée (décision D4, pas 3 chemins de code) : `clonal_mode`
∈ {none, stolon, rhizome, drageon} module trois axes seulement —
  • portée  : `clonal_radius_cm` (drageon très court, rhizome long) ;
  • gate    : stolon/drageon exigent de la LUMIÈRE AU SOL (le stolon ne prend pas
              sous canopée fermée) ; rhizome tolère l'ombre (réserve) → c'est de là
              qu'ÉMERGE son caractère envahissant, pas d'un drapeau ;
  • cadence : `clonal_interval` (1 fenêtre d'émission toutes N semaines).

INVARIANTS (philo de design) :
  #1/#2 — le coût de cloner passe par un état PHYSIOLOGIQUE (stress_memory), pas
          par un malus direct sur la plante ; la contrainte (couverture, lumière)
          précède la réponse (établissement du ramet). Jamais de mort verdict.
  #3    — DÉTERMINISTE, zéro RNG live : décision d'émission, direction et distance
          via `_hash_noise` (mêmes canaux que reproduction.py, décalés).
  perf  — le gate de COUVERTURE (`couverture_sol`, tronçon ①) borne le nombre de
          ramets → protège le LightField d'une explosion de plantes (cap perf).

Couches : `sim` peut lire `fields` (couverture, lumière) et `plants` (traits).
Câblé dans `sim/engine` (boucle) APRÈS la croissance/vigueur du tick.
"""
from __future__ import annotations

import math

from constants import PLOT_CM
from fields import _hash_noise
from sim.vigueur_plante import vigueur_plante

# --- Constantes (près du module, pas dans plants — règle de couches) ---
# Gate de couverture : au-delà de cette fraction couverte, le plot cible est
# SATURÉ → le ramet ne prend pas. C'est l'auto-limitation de la colonie ET le cap
# perf (le nombre de ramets est mécaniquement borné par la place restante).
COUVERTURE_SATURATION = 0.85
# Gate de lumière au sol (modes stolon/drageon) : sous ce seuil d'éclairement, le
# stolon ne s'enracine pas (pas de tapissage sous canopée fermée). Le rhizome
# IGNORE ce gate (réserve souterraine → tolère l'ombre → envahissant émergent).
CLONAL_LIGHT_SEUIL = 0.30
# Vigueur minimale de la mère pour émettre (lecture de la façade read-only). En
# deçà, la plante n'a pas l'énergie de cloner → arbitrage émergent avec la graine.
# Calibré BAS : la façade `vigueur_plante` ≈ qi_local sur une couvre-sol saine
# (santé × maturité × gène ≈ 1) et le qi_local d'un plot réel plafonne vers ~0.05
# (fertilité/microbiome partiels, ombre) → un seuil trop haut n'émettrait JAMAIS.
# Ce plancher laisse cloner une mère mature bien portante tout en coupant net une
# mère mourante (santé → 0 annule la façade).
CLONAL_VIGUEUR_SEUIL = 0.02
# Coût de l'émission : puise l'énergie propre de la mère via une bouffée de
# stress physiologique (stress_memory ∈ [0,1], intégré comme les perturbations).
# stress↑ ⇒ la plante investit moins ailleurs (croissance/graines) → arbitrage
# émergent graines ↔ ramets (une plante qui tapisse se ressème moins).
CLONAL_STRESS_COST = 0.06

# Modes qui exigent de la lumière au sol pour établir un ramet (gate de mode).
_MODES_HELIOPHILES = ("stolon", "drageon")


def _mature(plant) -> bool:
    """La plante est-elle assez avancée pour émettre un ramet ? Réutilise le
    critère de maturité de stade (dernier stade atteint pour une non-ligneuse ;
    les clonales visées — trèfle, futures rampantes — ne sont pas des arbres)."""
    stages = plant.plant_class.growth_stages
    return plant.current_stage >= len(stages) - 1


def _plot_of(x_cm: float, y_cm: float) -> tuple:
    """Plot-foyer (row, col) d'une position continue (miroir de PlantInstance)."""
    return int(math.floor(y_cm / PLOT_CM)), int(math.floor(x_cm / PLOT_CM))


def _offset_hashe(mother, seed: int, week: int, radius: float) -> tuple:
    """Direction + distance du ramet, DÉTERMINISTES (philo #3). Deux canaux de
    `_hash_noise` décorrélés (décalés de reproduction.py par des multiplicateurs
    de semaine distincts) : l'un pour l'angle, l'autre pour la distance. Distance
    en sqrt(u) → répartition surfacique uniforme dans le disque (pas de
    sur-concentration au centre)."""
    r, c = mother.position
    u_angle = _hash_noise(seed, week * 31, r, c)
    u_dist = _hash_noise(seed, week * 37, r, c)
    angle = u_angle * 2.0 * math.pi
    dist = radius * math.sqrt(u_dist)
    return math.cos(angle) * dist, math.sin(angle) * dist


def _peut_etablir(cls, tr: int, tc: int, tile, eco) -> bool:
    """Gate d'établissement du ramet sur le plot cible (tr, tc) :
      • plot VALIDE sur la tuile ;
      • couverture < COUVERTURE_SATURATION → auto-limitation + cap perf ;
      • gate de MODE : stolon/drageon exigent de la lumière au sol ; rhizome non.
    Lecture seule des champs (`couverture_sol`, `lumiere`) — aucune mutation."""
    if not tile.is_valid_plot(tr, tc):
        return False
    if eco.couverture_sol.at_plot(tr, tc) >= COUVERTURE_SATURATION:
        return False
    if cls.clonal_mode in _MODES_HELIOPHILES:
        if eco.lumiere.at_plot(tr, tc) < CLONAL_LIGHT_SEUIL:
            return False
    return True


def emettre_ramets(tile, eco, seed: int, week: int) -> list[str]:
    """Émission clonale pour toute la tuile ce tick. Pour chaque plante VIVANTE,
    MATURE, de `clonal_mode != "none"`, dans sa fenêtre de cadence et assez
    vigoureuse : tire un offset hashé, teste le gate d'établissement, et — si tout
    passe — pose un ramet (clone génétique) via `tile.add_plant`, en imputant le
    coût à la mère. Un ramet AU PLUS par mère et par tick (borne perf simple).

    Déterministe (philo #3). No-op si aucune clonale mature → golden NEUTRE hors
    trèfle stolonifère du smoke. Renvoie les lignes de log (diégétiques)."""
    log = []
    for mother in list(tile.plants):
        if not mother.is_alive:
            continue
        cls = mother.plant_class
        if cls.clonal_mode == "none" or not _mature(mother):
            continue
        r, c = mother.position
        # Cadence : une fenêtre d'émission toutes `clonal_interval` semaines
        # (porte hashée, pas un modulo de calendrier → indépendant du décalage).
        if _hash_noise(seed, week * 41, r, c) >= 1.0 / max(1, cls.clonal_interval):
            continue
        # Vigueur : la mère doit avoir l'énergie de cloner (façade read-only).
        if vigueur_plante(mother, eco) < CLONAL_VIGUEUR_SEUIL:
            continue
        dx, dy = _offset_hashe(mother, seed, week, cls.clonal_radius_cm)
        tx, ty = mother.x_cm + dx, mother.y_cm + dy
        tr, tc = _plot_of(tx, ty)
        if not _peut_etablir(cls, tr, tc, tile, eco):
            continue
        ramet = tile.add_plant(cls, tr, tc)
        if ramet is None:
            continue
        # Clone : vecteur de gènes COPIÉ (pas de brassage). L'expression plastique
        # (priming maternel) suit le même principe que la graine → le ramet naît
        # dans l'état d'acclimatation de la mère.
        ramet.genes = dict(mother.genes)
        ramet.expression.update(mother.expression)
        # Position continue = le point d'enracinement réel du stolon/rhizome.
        ramet.x_cm, ramet.y_cm = tx, ty
        # Coût sur la MÈRE : bouffée de stress physiologique (puise l'énergie propre
        # → arbitrage graines ↔ ramets). Intégré comme les perturbations, clampé.
        mother.stress_memory = min(1.0, mother.stress_memory + CLONAL_STRESS_COST)
        log.append(f"    🌿 Ramet ({cls.clonal_mode}) : {cls.name} "
                   f"@{(tr, tc)} [clone de @{(r, c)}]")
    return log
