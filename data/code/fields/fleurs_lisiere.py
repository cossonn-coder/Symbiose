"""
SYMBIOSE — fields/fleurs_lisiere.py
Responsabilité : les COLONIES de fleurs des bords (sprint LISIÈRE NUE, D124,
conception §3.1 à §3.3). Vérité moteur, peinte par la vue.

Une colonie n'est PAS une espèce du catalogue : c'est un milieu, comme l'effet de
lisière. Pas de graines, pas de voix narrative, pas de réaction aux gestes.

Trois étages, tous PURS et déterministes (hash, zéro RNG — philo #3) :
  • géométrie : `colonies_secteur(seed, cote, type)`, dans le repère de la vue
    (`u` le long du bord, `depth` vers l'extérieur, cf. `DecorLayer.EdgePoint` et
    `peripherie.rect_secteur`) ;
  • floraison : `floraison_couleur(couleur, wiy)`, fenêtre par couleur ;
  • nourriture : `plots_nourris` (la partie statique, calculée une fois par
    `EcoFields.maj_fleurs_bord`) × `fleurs_actives` (le scalaire de la semaine),
    versés dans la ressource des butineurs par `ajouter_nourriture`.

📖 Pédagogie : c'est le découpage « table précalculée × gain courant » de
l'embarqué. La carte des plots ne change qu'avec la ceinture ; chaque semaine on ne
recalcule qu'un scalaire par couleur, jamais la géométrie (philo : pas de recalcul
dans un tick). Philo #2 : c'est un flux de nourriture, la population répond seule.
"""

from __future__ import annotations

from functools import lru_cache
from math import hypot
from typing import NamedTuple

from constants import PLOT_CM
from fields.peripherie import EST, MONDE_CM, NORD, SUD, _entre, _tirage

# Nombre de colonies par type (min, max inclus). Forêt et falaise : aucune.
COLONIES_PAR_TYPE = {"prairie": (3, 4), "friche": (1, 2), "riviere": (0, 1)}

# Centre de la colonie en profondeur (cm vers l'extérieur) et demi-étendue. La
# rivière garde ses fleurs sur la rive côté jardin : le lit est peint plus loin
# (`DecorLayer.Eau`, axe + 2 demi-largeurs). [Ordres de grandeur, à juger au F5.]
PROFONDEUR_COLONIE_CM = {"prairie": (180.0, 550.0), "friche": (160.0, 500.0),
                         "riviere": (70.0, 100.0)}
RAYON_D_CM = {"prairie": (120.0, 220.0), "friche": (120.0, 220.0),
              "riviere": (50.0, 70.0)}
RAYON_U_CM = (120.0, 220.0)   # 4 taches au pire : 1760 cm sur 2000, des vides restent

# Couleur → famille botanique : c'est le GOÛT de chaque butineur (`attractivite`)
# qui décide ensuite. Ranunculaceae n'est dans aucune table : défaut 0,30, le bouton
# d'or nourrit peu.
FAMILLE = {"blanc": "Asteraceae", "jaune": "Ranunculaceae"}
COULEURS = tuple(FAMILLE)

# Fenêtre de floraison en wiy : (début, plein, fin du plein, fin). wiy 3 = 1ᵉʳ avril,
# 6 ≈ fin avril, 15 ≈ fin juin, 20 = 1ᵉʳ août (table de `calendrier.py`).
# [Ordres de grandeur de mémoire, non sourcés — conception §3.1.]
FENETRES = {"jaune": (3.0, 5.0, 12.0, 15.0),   # bouton d'or : avril-juin
            "blanc": (6.0, 8.0, 17.0, 20.0)}   # marguerite : fin avril-juillet

PORTEE_CM = 600.0          # rayon d'action au-delà du bord de la tache
NOURRITURE_COLONIE = 0.5   # ressource en pleine fleur au contact (goût 1,0)
BUTINEURS_MAX = 10         # compte de vue borné par colonie (hint pur)
BUTINEURS_PAR_DENSITE = 5.0
PLOTS_HINT = 12            # plots lus par colonie pour ce compte

K_COLONIES = 92_000        # canal de hash, disjoint des K_* de `peripherie`
_PAS_COLONIE = 16
POIDS_VIDE_MIN = 0.3       # aucun vide entre taches ne tend vers zéro


class Colonie(NamedTuple):
    cote: int
    u_cm: float
    depth_cm: float
    rayon_u_cm: float
    rayon_d_cm: float
    couleur: str
    graine: int        # pour les bords irréguliers côté vue


@lru_cache(maxsize=64)
def colonies_secteur(seed: int, cote: int, type_secteur: str) -> tuple[Colonie, ...]:
    """Colonies d'un secteur : fonction pure de (seed, côté, type). Le vide restant
    le long du bord est partagé en n+1 parts inégales au hash : les taches ne se
    chevauchent jamais et ne sont pas régulièrement espacées (pas de quadrillage)."""
    bornes = COLONIES_PAR_TYPE.get(type_secteur)
    if bornes is None:
        return ()
    nmin, nmax = bornes
    n = nmin + min(int(_tirage(seed, cote, (K_COLONIES, 0)) * (nmax - nmin + 1)),
                   nmax - nmin)
    if n == 0:
        return ()

    def t(i: int, k: int) -> float:
        return _tirage(seed, cote, (K_COLONIES + (i + 1) * _PAS_COLONIE, k))

    rayons = [_entre(t(i, 2), RAYON_U_CM) for i in range(n)]
    parts = [POIDS_VIDE_MIN + t(i, 0) for i in range(n + 1)]
    unite = (MONDE_CM - 2.0 * sum(rayons)) / sum(parts)
    out = []
    u = 0.0
    for i in range(n):
        u += parts[i] * unite + rayons[i]
        out.append(Colonie(
            cote=cote, u_cm=round(u, 3),
            depth_cm=_entre(t(i, 1), PROFONDEUR_COLONIE_CM[type_secteur]),
            rayon_u_cm=rayons[i],
            rayon_d_cm=_entre(t(i, 3), RAYON_D_CM[type_secteur]),
            couleur=COULEURS[min(int(t(i, 4) * len(COULEURS)), len(COULEURS) - 1)],
            graine=int(t(i, 5) * 0x7FFFFFFF),
        ))
        u += rayons[i]
    return tuple(out)


def floraison_couleur(couleur: str, wiy: int) -> float:
    """Floraison ∈ [0,1] d'une couleur à la semaine `wiy` : trapèze, 0 hors fenêtre."""
    debut, plein, fin_plein, fin = FENETRES[couleur]
    if wiy <= debut or wiy >= fin:
        return 0.0
    if wiy < plein:
        return (wiy - debut) / (plein - debut)
    if wiy > fin_plein:
        return (fin - wiy) / (fin - fin_plein)
    return 1.0


def _centre_monde(col: Colonie) -> tuple[float, float]:
    """Centre en coordonnées MONDE (x = Est, y = Sud), miroir de `EdgePoint`."""
    if col.cote == NORD:
        return col.u_cm, -col.depth_cm
    if col.cote == EST:
        return MONDE_CM + col.depth_cm, col.u_cm
    if col.cote == SUD:
        return col.u_cm, MONDE_CM + col.depth_cm
    return -col.depth_cm, col.u_cm      # OUEST


def _poids_plots(col: Colonie, rows: int, cols: int,
                 origin: tuple[float, float]) -> list[tuple[int, int, float]]:
    """Plots d'une tuile atteints par une colonie : poids ∈ ]0,1], 1 au contact de la
    tache, 0 à `PORTEE_CM` au-delà."""
    cx, cy = _centre_monde(col)
    rayon = (col.rayon_u_cm + col.rayon_d_cm) / 2.0
    ox, oy = origin
    out = []
    for r in range(rows):
        y = r * PLOT_CM + PLOT_CM / 2.0 + oy
        for c in range(cols):
            x = c * PLOT_CM + PLOT_CM / 2.0 + ox
            d = max(0.0, hypot(x - cx, y - cy) - rayon)
            if d < PORTEE_CM:
                out.append((r, c, 1.0 - d / PORTEE_CM))
    return out


def _colonies(seed: int, ceinture) -> list[Colonie]:
    return [col for s in ceinture or ()
            for col in colonies_secteur(seed, s["cote"], s["type"])]


def plots_nourris(seed: int, ceinture, rows: int, cols: int,
                  origin: tuple[float, float]) -> dict[str, list]:
    """Carte STATIQUE d'une tuile : {couleur: [(r, c, poids)]}, combinée par maximum
    entre colonies (deux taches voisines ne nourrissent pas deux fois un plot).
    Couleur absente si elle n'atteint aucun plot de la tuile."""
    par_couleur: dict[str, dict] = {}
    for col in _colonies(seed, ceinture):
        cible = par_couleur.setdefault(col.couleur, {})
        for r, c, p in _poids_plots(col, rows, cols, origin):
            if p > cible.get((r, c), 0.0):
                cible[(r, c)] = p
    return {coul: [(r, c, p) for (r, c), p in sorted(cible.items())]
            for coul, cible in par_couleur.items() if cible}


def fleurs_actives(plots_par_couleur: dict, wiy: int):
    """[(famille, floraison, plots)] de la semaine, ou `None` si rien n'est en fleur :
    hors saison, le lecteur ne fait aucun travail et la ressource reste celle des
    seules plantes (invariant « floraison nulle ⇒ champ nul »)."""
    actives = [(FAMILLE[coul], flo, plots)
               for coul, plots in plots_par_couleur.items()
               if (flo := floraison_couleur(coul, wiy)) > 0.0]
    return actives or None


def ajouter_nourriture(grille: list[list[float]], actives, attractivite: dict,
                       defaut: float) -> None:
    """Verse la nourriture des colonies dans une grille de ressource, déjà normalisée :
    même plafond à 1 que les fleurs des plantes. Pondérée par le goût du butineur."""
    for famille, flo, plots in actives:
        w = NOURRITURE_COLONIE * flo * attractivite.get(famille, defaut)
        if w <= 0.0:
            continue
        for r, c, poids in plots:
            grille[r][c] = min(1.0, grille[r][c] + w * poids)


# ---------------------------------------------------------------------------
# VUE : compte de butineurs par colonie (lecture pure, jamais d'écriture moteur)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=8)
def _index_hint(seed: int, sig_ceinture: tuple, sig_tuiles: tuple) -> dict:
    """{Colonie: [(tile_id, r, c, poids)]} : les `PLOTS_HINT` plots les plus proches.
    Mémoïsé : la géométrie ne change qu'avec la ceinture, le snapshot arrive par semaine."""
    index = {}
    for cote, typ in sig_ceinture:
        for col in colonies_secteur(seed, cote, typ):
            plots = [(tid, r, c, p) for tid, rows, cols, origin in sig_tuiles
                     for r, c, p in _poids_plots(col, rows, cols, origin)]
            plots.sort(key=lambda e: (-e[3], e[0], e[1], e[2]))
            index[col] = plots[:PLOTS_HINT]
    return index


def butineurs_par_colonie(game_state: dict) -> dict:
    """{Colonie: compte} dérivé de la population réelle des plots voisins, borné à
    `BUTINEURS_MAX`, multiplié par la floraison (pas de fleur : aucun insecte). Colonie
    absente = 0. Monde sans tuile (test du bloc) : dict vide."""
    wiy = (game_state.get("week", 1) - 1) % 52 + 1
    flo = {coul: floraison_couleur(coul, wiy) for coul in COULEURS}
    if not any(flo.values()) or not game_state.get("tiles"):
        return {}
    ecos = game_state["eco"]
    sig_tuiles = tuple((t.tile_id, ecos[t.tile_id].rows, ecos[t.tile_id].cols,
                        (t.origin_x_cm, t.origin_y_cm)) for t in game_state["tiles"])
    sig_ceinture = tuple((s["cote"], s["type"]) for s in game_state["ceinture"])
    index = _index_hint(game_state.get("seed", 0), sig_ceinture, sig_tuiles)
    comptes = {}
    for col, plots in index.items():
        total = sum(p for *_, p in plots)
        if flo[col.couleur] <= 0.0 or total <= 0.0:
            continue
        dens = sum(ecos[tid].pollinator_density(r, c) * p for tid, r, c, p in plots) / total
        comptes[col] = min(BUTINEURS_MAX,
                           int(BUTINEURS_PAR_DENSITE * dens * flo[col.couleur] + 0.5))
    return comptes
