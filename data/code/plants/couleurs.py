"""
SYMBIOSE — plants/couleurs.py
Couleur des fleurs et préférence des butineurs (D139 caractères vivants ①,
conception §2.1). Fondation pure : aucun import interne (lu par `fields`).

POURQUOI UNE COULEUR EN DEUX NOMBRES ?
Une couleur est notée (teinte en degrés, saturation ∈ [0, 1]) puis placée dans le
plan « chroma » : x = s·cos(teinte), y = s·sin(teinte). Le BLANC (saturation 0)
tombe au centre, les couleurs vives sur le bord. Une seule représentation sert à
tout : l'axe de couleur d'une espèce, la teinte d'une plante, les couleurs
préférées d'un butineur. La distance dans ce plan dit « à quel point deux couleurs
se ressemblent » — un lavande est proche du violet ET du blanc, ce qu'un simple
angle de teinte ne saurait pas dire (le blanc n'a pas de teinte).

AXE DE COULEUR D'UNE ESPÈCE (`PlantBase.axe_couleur`) : deux couleurs extrêmes
(la bourrache va du bleu au rose). Le caractère `couleur_fleur` ∈ [−1, 1] place la
plante sur le segment : −1 = première couleur, +1 = seconde, 0 = milieu.

PRÉFÉRENCE D'UN BUTINEUR : la couleur la plus proche parmi ses préférées donne un
facteur ∈ [PREF_MIN, PREF_MAX] (cloche gaussienne de largeur `largeur`). L'abeille
voit l'ultraviolet mais pas le rouge : bleu, violet, jaune ; le papillon voit le
rouge. Une espèce sans axe (anémophile, non florale) ou un butineur sans
préférence ⇒ facteur 1 exact : rien ne change pour eux.
"""

import math

# --- Palette (teinte °, saturation) — valeurs de départ, lisibles par la vue ⑥ ---
ROUGE      = (0.0, 1.0)
ORANGE     = (30.0, 1.0)
JAUNE      = (55.0, 1.0)
JAUNE_VERT = (75.0, 0.5)     # ombelles du lierre
BLEU       = (225.0, 1.0)
BLEU_PALE  = (215.0, 0.4)
VIOLET     = (275.0, 1.0)
LAVANDE    = (265.0, 0.45)
ROSE       = (330.0, 0.55)
ROSE_PALE  = (340.0, 0.25)
BLANC      = (0.0, 0.0)

# Amplitude de la préférence de couleur (valeurs de départ, calibrage post-test).
# Modeste : le goût de FAMILLE (`attractivite`) reste le premier tri ; la couleur
# départage les individus d'une même espèce — c'est elle que la sélection lit.
PREF_MIN = 0.75
PREF_MAX = 1.25


def chroma(couleur: tuple) -> tuple:
    """(teinte °, saturation) → point (x, y) du plan chroma."""
    h, s = couleur
    a = math.radians(h)
    return (s * math.cos(a), s * math.sin(a))


# Mémo axe → (x1, y1, dx, dy) : un axe d'espèce est une constante de classe, sa
# conversion en chroma (trigonométrie) n'est faite qu'UNE fois par partie, jamais à
# chaque appel du tick (mémoire « pas de recalcul dans un tick »). Clé = le tuple
# de l'axe lui-même (immuable) → aucune invalidation à gérer.
_AXES: dict = {}


def _segment(axe: tuple) -> tuple:
    seg = _AXES.get(axe)
    if seg is None:
        (x1, y1), (x2, y2) = chroma(axe[0]), chroma(axe[1])
        seg = _AXES[axe] = (x1, y1, x2 - x1, y2 - y1)
    return seg


def point_sur_axe(axe: tuple, position: float) -> tuple:
    """Point chroma d'une plante : `position` ∈ [−1, 1] sur l'axe (c1, c2)."""
    x1, y1, dx, dy = _segment(axe)
    t = 0.5 * (position + 1.0)
    return (x1 + t * dx, y1 + t * dy)


def couleur_sur_axe(axe: tuple, position: float) -> tuple:
    """(teinte °, saturation) d'une plante — pour la vue et le survol."""
    x, y = point_sur_axe(axe, position)
    return (math.degrees(math.atan2(y, x)) % 360.0, math.hypot(x, y))


def preferences(couleurs: tuple, largeur: float) -> tuple | None:
    """Préférence d'un butineur pré-calculée (points chroma, 2·largeur²) — faite UNE
    fois au registre, jamais dans le tick. Aucune couleur ⇒ None (facteur 1)."""
    if not couleurs:
        return None
    return (tuple(chroma(c) for c in couleurs), 2.0 * largeur * largeur)


def preference_couleur(axe: tuple | None, position: float, pref: tuple | None) -> float:
    """Facteur de préférence d'un butineur (`pref`, cf. `preferences`) pour une
    plante d'axe `axe` placée en `position`. O(nombre de couleurs préférées ≤ 3).
    Maximal (PREF_MAX) sur une couleur préférée, PREF_MIN loin de toutes."""
    if axe is None or pref is None:
        return 1.0
    x, y = point_sur_axe(axe, position)
    points, deux_l2 = pref
    d2 = min((x - px) ** 2 + (y - py) ** 2 for (px, py) in points)
    return PREF_MIN + (PREF_MAX - PREF_MIN) * math.exp(-d2 / deux_l2)
