"""
SYMBIOSE — sim/growth/dormance.py
Bourgeons DORMANTS (D129 ①, conception `docs/vegetal/croissance/conception_verger_vivant.md`
§4). Le bois garde des bourgeons latents : un arbre qui a perdu une partie de sa
couronne (tempête, neige, cladoptose, plafond) en réveille quelques-uns, à un rythme
borné, et reconstruit sa couronne vers son plafond `max_segments`.

Pédagogie (Nico) : jusqu'ici un segment n'avait QU'UN bourgeon (`has_bud`), consommé
à vie par `_debourrement`. Une branche perdue n'était jamais remplacée et le verger
« fondait » d'année en année. Ici on ne fait que REMETTRE `has_bud = True` sur un
segment choisi : c'est le `_debourrement` existant qui le fait partir en rameau, avec
le même angle et la même auxine que n'importe quelle branche. Aucun bonus direct
(philo #2) : la repousse dépend du FLUX (lumière locale, vitalité, place sous le
plafond), pas d'un chiffre ajouté à la plante.

Garde-fou anti-boucle avec la cladoptose : une branche tombée à l'ombre ne doit pas
repousser chaque semaine sous la même ombre. Le réveil exige donc, AU POINT de
réveil, une lumière d'au moins `DORMANCE_MARGE_LUMIERE` × le seuil de cladoptose de
l'arbre — même formule de lumière que `cladoptose.lumiere_pointes` (lumière de la
plante × transmission des grappes plus hautes de sa propre couronne).

Pure structurelle (couche growth, aucun `eco`) ; zéro RNG (philo #3) : le rythme et
le choix du segment passent par `fields._hash_noise` sur `form_seed`, la semaine et
l'indice du segment.
"""

from __future__ import annotations

from fields import _hash_noise, form_seed_at
from .constantes import (AUXIN_INHIB_THRESHOLD, CLADO_OPACITE_GRAPPE,
                         CLADO_DZ_CM, CLADO_RAYON_CM)
from .geometrie import _tip, _children

# Leviers (D129 ①). Fenêtre de 4 semaines et plafond à 85 % = patch brut mesuré à la
# conception (cerisier de `full` an 5 : 17 → 34 segments) [seed 42, n=1 run, VM].
DORMANCE_FENETRE       = 4      # semaines entre deux réveils possibles d'un même arbre
DORMANCE_PLAFOND       = 0.85   # pas de réveil au-dessus de cette part de max_segments
DORMANCE_MARGE_LUMIERE = 1.5    # lumière locale exigée = marge × seuil de cladoptose


def _fenetre(fs: int, week: int) -> bool:
    """Un arbre n'est examiné qu'une semaine sur DORMANCE_FENETRE, à une phase propre
    tirée de son identité de forme (sans état, comme `cladoptose.fenetre_ouverte`)."""
    phase = int(_hash_noise(fs, 0, 0, 29) * DORMANCE_FENETRE)
    return (week + phase) % DORMANCE_FENETRE == 0


def _lumiere_locale(segs: list, pointes: list, tips: dict, i: int,
                    l_plante: float, transmis: float) -> float:
    """Lumière à l'extrémité du segment `i` : l_plante × transmis^n, n = pointes de la
    couronne plus hautes de > CLADO_DZ_CM dans un rayon CLADO_RAYON_CM."""
    x, y, z = _tip(segs[i])
    r2 = CLADO_RAYON_CM * CLADO_RAYON_CM
    n = 0
    for j in pointes:
        u = tips[j]
        if j != i and u[2] > z + CLADO_DZ_CM and (u[0] - x) ** 2 + (u[1] - y) ** 2 < r2:
            n += 1
    return l_plante * transmis ** n


def peut_reveiller(plant, week: int) -> bool:
    """Gardes bon marché, testées AVANT de lire la lumière : vitalité > 0, couronne
    sous DORMANCE_PLAFOND × max_segments, fenêtre de l'arbre ouverte cette semaine."""
    segs = plant.segments
    if plant.vitalite <= 0.0 or len(segs) < 2:
        return False
    if len(segs) >= DORMANCE_PLAFOND * plant.plant_class.max_segments:
        return False
    return _fenetre(plant.form_seed or form_seed_at(0, plant.x_cm, plant.y_cm, 0), week)


def reveiller_bourgeon(plant, week: int, l_plante: float, densite: float,
                       seuil_clado: float) -> int | None:
    """Réveille AU PLUS un bourgeon latent sur `plant` ce tick ; renvoie l'indice du
    segment réveillé (ou None). À appeler après la mise à jour de l'auxine et avant
    `_debourrement`, qui le fera débourrer dans la même passe.

    Préalable : `peut_reveiller` (vitalité, plafond, fenêtre). Candidats : tout segment de bois (collet exclu, ni apex ni bourgeon
    déjà présent) libéré de la dominance apicale (auxine sous le seuil) et assez
    éclairé à son extrémité. Choix déterministe par hachage parmi les candidats."""
    segs = plant.segments
    fs = plant.form_seed or form_seed_at(0, plant.x_cm, plant.y_cm, 0)
    ch = _children(segs)
    pointes = [j for j in range(len(segs)) if not ch[j]]
    tips = {j: _tip(segs[j]) for j in pointes}
    transmis = 1.0 - densite * CLADO_OPACITE_GRAPPE
    exige = DORMANCE_MARGE_LUMIERE * seuil_clado
    meilleur, choix = -1.0, None
    for i in range(1, len(segs)):
        s = segs[i]
        if s.is_apex or s.has_bud or s.auxin >= AUXIN_INHIB_THRESHOLD:
            continue
        h = _hash_noise(fs, week, i, 23)
        if h <= meilleur:
            continue                      # tirage d'abord : la lumière ne se calcule que si utile
        if _lumiere_locale(segs, pointes, tips, i, l_plante, transmis) < exige:
            continue
        meilleur, choix = h, i
    if choix is not None:
        segs[choix].has_bud = True
    return choix
