"""
SYMBIOSE — fields/abri.py
Champ d'ABRI spatial (brise-vent + venturi) — sprint VENT & ÉVAPOTRANSPIRATION ③.
Spec : docs/champs/climat/conception_vent_evapotranspiration.md §4 + §2.4 + §7B (perf, CONTRAINTE #1).

La masse d'air (`sim.wind.wind_at`, ①) est UNIFORME sur la tuile. La force LOCALE
par plot résulte de la GÉOMÉTRIE d'abri : un obstacle (mur de maison, plante haute)
projette une zone abritée SOUS LE VENT (force réduite), portée ∝ hauteur. Une haie
(plantes hautes alignées) devient un brise-vent ÉMERGENT (philo #1 : agir sur le
milieu). On stocke `eco.vent` (GridField, force locale ∈ [0, 1+]) lu par
l'évaporation (③ remplace la masse d'air uniforme du ②) et le wind chill (§5.5).

PERF (§7B, CONTRAINTE #1) — deux leviers OBLIGATOIRES, sinon ce tronçon double le
poste le plus cher (`_point_in_capsule`, déjà 35 % du tick) :
  1. MUTUALISATION : la capsule d'abri RÉUTILISE `_point_in_capsule` de `light.py`
     et le même SCATTER par bbox (D32) — chaque obstacle ne visite que les plots de
     sa boîte englobante, pas toute la grille.
  2. CACHE : `eco.vent` ne dépend que de (obstacles, direction du vent). Les
     obstacles sont quasi statiques, la direction est une marche LENTE → on ne
     recalcule QUE quand la direction franchit un PAS ANGULAIRE ou qu'une signature
     d'obstacles change. En régime permanent : coût ≈ 0 (juste une mise à l'échelle
     du champ figé par la force du tick).

Couche : `fields` — n'importe que `fields.light` (même couche, pour la machinerie
de capsule) + `constants`. Aucun import de `sim` (le vent/direction arrivent en
ARGUMENTS, calculés par la boucle ; la couche basse n'importe jamais la haute).
"""

from __future__ import annotations
import math

from constants import PLOT_CM
from fields.grids import GridField
from fields.light import _point_in_capsule
from fields.peripherie import obstacles_abri
from fields.ecofields.constants import (
    ABRI_HAUTEUR_MIN_CM, ABRI_PORTEE_HAUTEUR, ABRI_REDUCTION_MAX,
    ABRI_RAYON_FRAC, ABRI_ANGULAR_STEP, ABRI_VENTURI_BOOST,
    REDUCTION_LISIERE_MAX, TURBULENCE_MUR, TURBULENCE_PLAFOND,
)


def _obstacles(plants, house, tile_origin, ceinture=None):
    """Liste des obstacles brise-vent de la tuile, en coordonnées TUILE (cm) :
    `(cx, cy, hauteur_cm, rayon_cm, porosite)`. Trois sources :

      • la MAISON (pavé opaque global) — son centre/demi-diagonale ramenés en repère
        tuile via `tile_origin` (offset monde) ;
      • les PLANTES HAUTES vivantes (≥ `ABRI_HAUTEUR_MIN_CM`) — une haie alignée
        devient un brise-vent émergent (philo #1) ;
      • les SECTEURS de CEINTURE boisés/rocheux (sprint PÉRIPHÉRIE ②, D73), ramenés
        eux aussi du repère MONDE au repère tuile.

    `porosite` est **None** pour la maison et les plantes → branche historique
    BIT-IDENTIQUE dans `_build_facteur` (donner leur vraie porosité aux haies du
    jardin est un calibrage ultérieur, dette D94). Elle vaut φ = 1 − densité pour
    une lisière, ce qui module réduction (linéaire) et turbulence (quadratique).

    PURE, déterministe (ordre des plantes = ordre de la liste, zéro RNG). Sert AUSSI
    de SIGNATURE de cache (cf. `_signature`)."""
    ox, oy = tile_origin
    obs = []
    if house is not None:
        hx0, hy0, hx1, hy1 = house.footprint_bounds
        # Centre du pavé en repère tuile + rayon = demi-diagonale (capsule englobante
        # sobre : on ne raffine pas la forme du mur, l'abri reste une approximation).
        cx = (hx0 + hx1) / 2.0 - ox
        cy = (hy0 + hy1) / 2.0 - oy
        rayon = math.hypot(hx1 - hx0, hy1 - hy0) / 2.0
        obs.append((cx, cy, house.height_cm, rayon, None))
    for p in plants:
        if not p.is_alive:
            continue
        h = p.current_height
        if h < ABRI_HAUTEUR_MIN_CM:
            continue
        rayon = max(PLOT_CM * ABRI_RAYON_FRAC,
                    p.plant_class.canopy_radius_at(p))
        obs.append((p.x_cm, p.y_cm, h, rayon, None))
    for cx, cy, h, rayon, poro in obstacles_abri(ceinture):
        obs.append((cx - ox, cy - oy, h, rayon, poro))
    return obs


def _signature(obs, wind_dir):
    """Signature de CACHE : le champ d'abri ne dépend que de (obstacles, direction).
    La direction est DISCRÉTISÉE en pas angulaires (`ABRI_ANGULAR_STEP`) → tant que
    le vent tourne moins d'un pas, la géométrie d'abri est INCHANGÉE (régime
    permanent = recalcul sauté). Les obstacles entrent par leur géométrie arrondie
    au cm (les micro-variations de hauteur d'une plante qui pousse d'un poil ne
    forcent pas un recalcul — pas angulaire et arrondi = grain de cache). La
    POROSITÉ entre aussi (②) : sans elle, une coupe forestière (④) qui éclaircit un
    secteur sans changer sa hauteur ne serait jamais vue par le cache."""
    step = int(wind_dir / ABRI_ANGULAR_STEP)
    geo = tuple((round(cx), round(cy), round(h), round(ray), poro)
                for cx, cy, h, ray, poro in obs)
    return (step, geo)


def compute_abri(eco, plants, house, tile_origin,
                 wind_dir: float, wind_force: float, ceinture=None) -> None:
    """Recalcule `eco.vent` (force locale par plot) depuis la masse d'air + abris.

    `wind_dir` = direction D'OÙ VIENT le vent (rad, `WindState.direction`) ;
    `wind_force` = force de la masse d'air du tick (`WindState.force`).

    Modèle (§4) : on part d'un FACTEUR d'abri par plot (1.0 = pleine exposition).
    Chaque obstacle projette une capsule SOUS LE VENT (orientée vers où le vent VA
    = direction + π) sur une portée ∝ hauteur (`ABRI_PORTEE_HAUTEUR`× la hauteur,
    règle empirique réelle ≈ 10×). Dans la capsule, le facteur tombe (jusqu'à
    `1 − ABRI_REDUCTION_MAX`) ∝ la proximité de l'obstacle (dégressif le long du
    sillage). VENTURI : un plot EXPOSÉ voisin d'un plot abrité reçoit un léger
    surcroît (le flux contourne l'obstacle et s'engouffre dans le goulet, §2.2).
    Enfin `eco.vent = facteur × wind_force` (la masse d'air mise à l'échelle).

    CACHE (§7B, levier 2) : si (obstacles, direction discrétisée) n'a pas changé
    depuis le dernier appel, on NE recalcule PAS le facteur — on se contente de
    re-multiplier le facteur figé par `wind_force` (régime permanent → coût ≈ 0).

    MUTUALISATION (§7B, levier 1) : capsule = `_point_in_capsule` de `light.py`,
    scatter par bbox (D32) — chaque obstacle ne visite que sa boîte englobante.

    `ceinture` (②) : les 4 secteurs de périphérie ou None. Un secteur boisé/rocheux
    entre comme un obstacle de plus, POREUX — il module en plus `eco.turbulence`
    (multiplicateur de RAFALE locale lu par `_wind_damage`). Sans lisière ce champ
    reste **None** (donc facteur 1.0 implicite) → casse mécanique inchangée.

    PURE écriture de `eco.vent`/`eco.turbulence` (philo #2 : aucune plante touchée ;
    flux → contrainte). Déterministe, zéro RNG. À facteur figé (cache), aucun appel à
    `_point_in_capsule` → le poste cher reste sauté en régime permanent.
    """
    rows, cols = eco.vent.rows, eco.vent.cols
    obs = _obstacles(plants, house, tile_origin, ceinture)
    sig = _signature(obs, wind_dir)

    cache = eco._abri_cache
    if cache is None or cache[0] != sig:
        # Direction VERS OÙ VA le vent (sillage sous le vent = à l'opposé de l'origine).
        gx = -math.sin(wind_dir + math.pi)
        gy = -math.cos(wind_dir + math.pi)
        facteur, turbulence = _build_facteur(obs, rows, cols, gx, gy)
        eco._abri_cache = (sig, facteur, turbulence)
    else:
        facteur, turbulence = cache[1], cache[2]

    # Mise à l'échelle par la force du tick (la SEULE opération en régime permanent).
    for r in range(rows):
        frow = facteur[r]
        for c in range(cols):
            eco.vent.set(r, c, frow[c] * wind_force)
    # Champ de turbulence : LAZY (None sans lisière → aucune allocation, aucun
    # lecteur touché). La rafale n'est pas mise à l'échelle par la force : c'est un
    # MULTIPLICATEUR géométrique, la force arrive déjà par `eco.vent`.
    if turbulence is None:
        eco.turbulence = None
    else:
        if eco.turbulence is None:
            eco.turbulence = GridField(rows, cols, initial=1.0,
                                       max_val=TURBULENCE_PLAFOND)
        for r in range(rows):
            trow = turbulence[r]
            for c in range(cols):
                eco.turbulence.set(r, c, trow[c])


def _build_facteur(obs, rows, cols, gx, gy):
    """Construit `(facteur, turbulence)` : la grille de FACTEUR d'abri (1.0 = pleine
    exposition, < 1 abrité, > 1 venturi) et — SEULEMENT si un obstacle est poreux
    (lisière) — la grille de TURBULENCE (multiplicateur de rafale ≥ 1, `None` sinon).
    Scatter par bbox de capsule (D32) : chaque obstacle ne visite que sa boîte. C'est
    l'opération CHÈRE — appelée SEULEMENT au franchissement d'un pas angulaire ou
    d'un changement d'obstacle (cache). `(gx, gy)` = direction unitaire vers où VA le
    vent (axe du sillage)."""
    facteur = [[1.0] * cols for _ in range(rows)]
    turbulence = ([[1.0] * cols for _ in range(rows)]
                  if any(o[4] is not None for o in obs) else None)
    for cx, cy, h, rayon, poro in obs:
        portee = h * ABRI_PORTEE_HAUTEUR        # longueur du sillage abrité (∝ hauteur)
        bx = cx + gx * portee                   # extrémité aval de la capsule
        by = cy + gy * portee
        xmin = (cx if cx < bx else bx) - rayon  # bbox = sur-ensemble strict (marge ±rayon)
        xmax = (cx if cx > bx else bx) + rayon
        ymin = (cy if cy < by else by) - rayon
        ymax = (cy if cy > by else by) + rayon
        c0 = int(xmin // PLOT_CM); c1 = int(xmax // PLOT_CM)
        r0 = int(ymin // PLOT_CM); r1 = int(ymax // PLOT_CM)
        if c0 < 0: c0 = 0
        if r0 < 0: r0 = 0
        if c1 > cols - 1: c1 = cols - 1
        if r1 > rows - 1: r1 = rows - 1
        for r in range(r0, r1 + 1):
            cyp = r * PLOT_CM + PLOT_CM / 2
            frow = facteur[r]
            for c in range(c0, c1 + 1):
                cxp = c * PLOT_CM + PLOT_CM / 2
                if not _point_in_capsule(cxp, cyp, cx, cy, gx, gy, portee, rayon):
                    continue
                # Atténuation DÉGRESSIVE le long du sillage : pleine près de
                # l'obstacle, s'estompe en bout de portée (distance projetée sur l'axe).
                dist = (cxp - cx) * gx + (cyp - cy) * gy   # avancement dans le sillage
                frac = 1.0 - min(1.0, max(0.0, dist) / portee) if portee > 0 else 1.0
                if poro is None:
                    reduction = ABRI_REDUCTION_MAX * frac
                else:
                    # LISIÈRE POREUSE (②, conception §3.2) : la réduction du vent
                    # moyen est LINÉAIRE en (1−φ), le surcroît de rafale est
                    # QUADRATIQUE → seul le TRÈS dense fait tomber des rafales.
                    plein = 1.0 - poro
                    reduction = REDUCTION_LISIERE_MAX * plein * frac
                    turbulence[r][c] *= 1.0 + TURBULENCE_MUR * plein * plein
                # Multiplicatif : deux obstacles alignés (haie) cumulent leur abri.
                frow[c] *= (1.0 - reduction)
    _venturi(facteur, rows, cols)
    return facteur, turbulence


def _venturi(facteur, rows, cols):
    """VENTURI (§2.2/§4) : un plot EXPOSÉ (facteur ≈ 1) bordant un plot ABRITÉ reçoit
    un léger SURCROÎT — le flux dévié par l'obstacle s'engouffre dans le goulet. Une
    passe voisinage (4-connexité) bon marché : on ne détecte pas les vrais goulets
    fluides (hors périmètre, modèle sobre §2.4), on capte la frange du sillage. À
    facteur figé partout (aucun abri) → aucun voisin abrité → no-op (champ neutre)."""
    boosts = []
    for r in range(rows):
        for c in range(cols):
            if facteur[r][c] < 1.0:
                continue                      # plot déjà abrité : pas de venturi sur lui
            abrite_voisin = False
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < rows and 0 <= cc < cols and facteur[rr][cc] < 1.0:
                    abrite_voisin = True
                    break
            if abrite_voisin:
                boosts.append((r, c))
    for r, c in boosts:                       # appliqué APRÈS détection (évite la cascade)
        facteur[r][c] = 1.0 + ABRI_VENTURI_BOOST
