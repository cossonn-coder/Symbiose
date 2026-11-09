"""
SYMBIOSE — sim/souche.py
Rejets de souche à la mort d'un arbre (sprint frein_rejets_figuier ②, D130) et
après une grosse perte de couronne d'un arbre vivant (③).
Spec : `docs/vegetal/regeneration/conception_rejets_de_souche.md` §3.2-3.5.

Ce que fait la nature : quand un arbre perd sa partie aérienne, les bourgeons
dormants de sa souche partent, nourris par les réserves des racines. Les rejets
sortent AU PIED, sans avoir besoin de lumière au départ (la réserve les porte) ;
ensuite la compétition pour la lumière trie, comme pour un semis.

Ici, une passe par tick sur la tuile :
  • cible = un arbre MORT (`morte`) dont la souche a été jugée vivante à la mort
    (`souche_vivante`, figé par `sim.effects.deposer_mort` via le critère pur
    `sim.effects.perturbations.souche_vivante`) et pas encore traitée ;
  • en saison de végétation seulement (même test que la dormance clonale ①) : un
    arbre mort en hiver rejette à la 1ʳᵉ semaine de printemps ;
  • N = round(`rejet_souche` × N_REJETS_MAX), borné 0..4 — un taillis réel en fait
    des dizaines qui s'éclaircissent ; on ne simule que ceux qui comptent (cap perf) ;
  • chaque rejet est un CLONE (gènes, expression, form_seed copiés, comme un ramet
    de `sim/clonal.py`) posé dans un disque de RAYON_REJET_CM autour du mort ;
  • une seule vague par mort (`souche_traitee`).

Perte de couronne (③) — l'arbre VIVANT qui perd d'un coup une grosse part de son
bois (casse de tempête ou de neige, cladoptose, effondrement, taille du joueur)
perd ses bourgeons et sa dominance apicale : la souche réagit comme à une coupe.
  • mémoire `perte_couronne` composée avec bois perdu / bois juste avant la perte
    (`noter_perte_couronne`, appelée par `sim.engine.branches` et `tailler`) ; le
    « bois » est le volume `longueur × épaisseur²`, la même forme que le relais
    `deposer_bois_tombe` (la constante de masse s'annule dans le rapport) ;
  • elle s'OUBLIE de PERTE_COURONNE_OUBLI par semaine de VÉGÉTATION seulement :
    l'oubli, c'est la couronne qui repousse — un arbre dormant ne repousse pas,
    donc une taille d'hiver garde sa mémoire intacte jusqu'au printemps (le
    recépage classique se fait en hiver, les rejets partent au débourrement) ;
  • ≥ SEUIL_PERTE_COURONNE hors hiver → l'épisode est CONSOMMÉ (mémoire à 0, une
    seule vague par épisode) ; s'il reste une souche vivante (même critère pur
    qu'à la mort), N = round(rejet_souche × N_REJETS_MAX × intensité) rejets.
  Taille sévère = recépage émergent, sans geste neuf (philo #1, #2).

Pourquoi le squelette suffit à porter la souche : un arbre mort reste dans
`tile.plants` tant qu'il lui reste du bois (`engine._tick_skeletons`, fragmentation
géométrique FRAG_RATE 0,04 × vitesse locale → des années avant d'atteindre ~0),
bien plus que l'hiver le plus long. Les mortes « non marquées » retirées par le
filet de `_tick_skeletons` (jamais passées par `deposer_mort`) ne rejettent pas :
acceptable, c'est un chemin de secours.

Philo : #2 aucune prime à la plante — c'est la perte qui déclenche une réponse
biologique ; #3 déterministe, zéro RNG (`_hash_noise`). Canaux utilisés ici :
week·67 (+k) pour l'angle, week·71 (+k) pour la distance — distincts de ceux de
`sim/clonal.py` (week·31 angle, week·37 distance, week·41 cadence).
Couches : `sim` lit `plants` (traits) et `fields` (bruit) ; câblé dans `sim/engine`.
"""
from __future__ import annotations

import math

from calendrier import saison_de, wiy_de
from constants import PLOT_CM
from fields import _hash_noise
from sim.capacite import recrutement_bloque
from sim.effects.perturbations import souche_vivante as souche_saine   # critère pur ②

# Rayon du disque où partent les rejets autour de la souche [ordre de grandeur] :
# les bourgeons dormants sont sur le collet et les grosses racines superficielles.
RAYON_REJET_CM = 60.0
# Plafond de rejets par vague (cap perf, cf. §3.5) ; N = round(rejet_souche × max).
N_REJETS_MAX = 4
# Perte de couronne (③). Seuil : la moitié du bois perdue « d'un coup » (spec §3.4).
# Mesuré [labo, figuier et pommier de 10 ans, n=1 arbre chacun] : le collet porte
# ~30 % du volume, tronc + charpentières ~70 % → couper au ras passe le seuil ; une
# casse de tempête est plafonnée à FRAC_MAX_CASSE (¼ des segments, surtout fins) et
# reste dessous.
SEUIL_PERTE_COURONNE = 0.5
# Part de la mémoire oubliée par semaine de végétation [ordre de grandeur] :
# ×0,94/sem → ~0,09 après les 39 semaines actives d'une année (« vidée en ~1 an »).
PERTE_COURONNE_OUBLI = 0.06


def nombre_rejets(cls, intensite: float = 1.0) -> int:
    """Rejets d'une vague pour l'espèce `cls` : ∝ sa capacité × l'intensité du
    déclencheur (1 = mort ; perte de couronne ∈ [seuil, 1]), borné 0..N_REJETS_MAX."""
    n = round(getattr(cls, "rejet_souche", 0.0) * N_REJETS_MAX * intensite)
    return max(0, min(N_REJETS_MAX, n))


def _volume(segments) -> float:
    """Volume de bois ∝ Σ longueur × épaisseur² (forme de `deposer_bois_tombe`)."""
    return sum(s.length_cm * s.thickness_cm ** 2 for s in segments)


def noter_perte_couronne(plant, tombes) -> None:
    """Compose dans `perte_couronne` la part du bois que `tombes` représentait. À appeler
    APRÈS la coupe (`plant.segments` n'a plus les segments tombés) : bois avant =
    restant + tombé. No-op si rien n'est tombé. Pure mutation, zéro RNG."""
    if not tombes:
        return
    perdu = _volume(tombes)
    avant = _volume(plant.segments) + perdu
    if avant <= 0.0:
        return
    # Composition « part restante × part restante » et non somme : deux coupes
    # successives de 50 % ôtent 75 % de la couronne, pas 100 % ; la mémoire reste
    # la vraie part perdue quel que soit le découpage en coupes.
    plant.perte_couronne = 1.0 - (1.0 - plant.perte_couronne) * (1.0 - perdu / avant)


def _offset(souche, seed: int, week: int, k: int) -> tuple:
    """Offset (dx, dy) du k-ième rejet, déterministe. Distance en sqrt(u) → répartition
    surfacique uniforme dans le disque (miroir de `clonal._offset_hashe`)."""
    r, c = souche.position
    angle = _hash_noise(seed, week * 67 + k, r, c) * 2.0 * math.pi
    dist = RAYON_REJET_CM * math.sqrt(_hash_noise(seed, week * 71 + k, r, c))
    return math.cos(angle) * dist, math.sin(angle) * dist


def _vague(tile, souche, seed: int, week: int, n: int) -> list:
    """Pose jusqu'à `n` clones de `souche` dans le disque RAYON_REJET_CM autour d'elle.
    Renvoie les plots des rejets réellement posés (plot invalide → sauté)."""
    cls = souche.plant_class
    poses = []
    for k in range(n):
        dx, dy = _offset(souche, seed, week, k)
        tx, ty = souche.x_cm + dx, souche.y_cm + dy
        tr, tc = int(math.floor(ty / PLOT_CM)), int(math.floor(tx / PLOT_CM))
        # Pas de gate de lumière : la réserve racinaire porte le rejet.
        rejet = tile.add_plant(cls, tr, tc)      # None si plot invalide
        if rejet is None:
            continue
        rejet.genes = dict(souche.genes)
        rejet.expression.update(souche.expression)
        rejet.form_seed = souche.form_seed
        rejet.x_cm, rejet.y_cm = tx, ty
        poses.append((tr, tc))
    return poses


def emettre_rejets_souche(tile, seed: int, week: int) -> list[str]:
    """Vague de rejets de chaque souche vivante non traitée (arbre mort, ②) et de
    chaque arbre vivant dont la perte de couronne a passé le seuil (③) ; fait oublier
    la mémoire des autres. Renvoie une ligne de log par vague (format stable, lu au ④
    par le ledger des voix ; la cause est entre crochets : `[souche de @…]` = mort,
    `[perte de couronne de @…]` = arbre vivant). Emoji 🌳 et non 🌱 : `sim/evenements`
    lit toute ligne 🌱 comme une avance de stade (`_RE_AVANCE`) → elle produirait une
    germination fantôme ; 🌳 y est ignoré."""
    log = []
    if saison_de(wiy_de(week)) == "hiver":
        return log        # dormance : ni rejet ni oubli (la couronne ne repousse pas)
    for souche in list(tile.plants):
        if souche.morte:
            if not (souche.souche_vivante and not souche.souche_traitee):
                continue
            # Cap perf : tuile saturée → on attend (la souche reste « à traiter »).
            if recrutement_bloque(tile):
                continue
            souche.souche_traitee = True
            poses = _vague(tile, souche, seed, week, nombre_rejets(souche.plant_class))
            cause = "souche"
        elif souche.perte_couronne >= SEUIL_PERTE_COURONNE:
            if recrutement_bloque(tile):
                continue                          # l'épisode attend, mémoire intacte
            intensite = min(1.0, souche.perte_couronne)
            souche.perte_couronne = 0.0           # épisode consommé : une seule vague
            if not souche_saine(souche):
                continue                          # souche épuisée : pas de rejet
            poses = _vague(tile, souche, seed, week,
                           nombre_rejets(souche.plant_class, intensite))
            cause = "perte de couronne"
        else:
            souche.perte_couronne *= 1.0 - PERTE_COURONNE_OUBLI
            continue
        if poses:
            log.append(f"    🌳 Rejet de souche : {souche.plant_class.name} @{poses[0]} "
                       f"×{len(poses)} [{cause} de @{souche.position}]")
    return log
