"""
SYMBIOSE — sim/engine/decompo.py
Litière issue du vivant (décompo·compost ②③) : squelettes post-mortem (seul
point de RETRAIT des plantes mortes), abscission d'automne des caducs, et
organes-fruits traçables (nouaison/maturation/chute).

Regroupés en `DecompoMixin` — le thème « ce que les plantes (mortes ou vivantes)
rendent au sol sous forme de litière ». Hérité par l'`Engine` (boucle.py).
Comportement identique à l'ancien engine.py.
"""

from __future__ import annotations
import math
from plants import Fruit, organ_sites
from fields import (T_SECHE, FRAG_RATE, ABSCISSION_BASE,
                    ABSCISSION_JITTER, ABSCISSION_MIN, ABSCISSION_MAX,
                    CHUTE_SEMAINES, FEUILLE_PAR_PLOT, FRUIT_MASSE, FRUIT_DMAT,
                    MATURITE_CHUTE)
from fields.ecofields.constants import BOIS_MORT_PAR_CM3   # D111 ② (sous-paquet propriétaire)
from fields.ecofields.litiere import BOIS_DIAM_DEFAUT      # grosseur inconnue (⑦bis)
from constants import PLOT_CM
from sim.effects.perturbations import frac_bois_mort
from sim.reproduction import (find_father, child_genes, child_expression,
                              recrue_par_fruits, facteur_glandee)
from fields import _hash_noise
from fields.seedbank import grain_sauvage, deposer_grain_sauvage

# Nouaison « en fin de floraison, par plante » (arc pollinisation ④ — §B.2).
# `floraison` (état floral ∈[0,1], écrit par engine._tick_floraison) monte vers 1
# pendant la fenêtre de floraison puis retombe vers 0 (fanaison). On arme la
# plante quand elle dépasse SEUIL_FLEURI (« en fleurs »), on NOUE quand elle
# repasse sous SEUIL_NOUAISON (« fleurs fanées »). Knobs de calibrage (post-test).
SEUIL_FLEURI   = 0.5
SEUIL_NOUAISON = 0.2
# Demi-saturation de la rampe douce g(pollen_recu) = pollen / (pollen + POLLEN_DEMI)
# ∈ [0,1[ (Monod) : dose faible → quelques fruits, dose forte → nouaison ≈ pleine,
# JAMAIS de plancher (0 pollen → 0 fruit). Knob de calibrage (post-test, §B.2).
# CALIBRÉ 2.0 → 1.0 au sprint FLORAISON·FRUCTIFICATION ② (D86 secondaire) : le banc
# `bancs/mesure_nouaison.py` (monde full, seed 42) mesure qu'un pommier verger BIEN
# VISITÉ intègre ~1.55 de pollen sur sa floraison → g(1.55)=0.44 avec DEMI=2.0
# (sous le seuil « une belle floraison = beaucoup de fruits »). À DEMI=1.0 la même
# dose donne g(1.55)=0.61 (≥0.5, cible du kickoff) SANS toucher l'invariant (0→0)
# ni le débit des butineurs. Levier unique, le plus simple (§ démarche perf-first).
POLLEN_DEMI    = 1.0
# Part des fruits tombés dont la graine devient un GRAIN SAUVAGE en terre (zoochorie ②,
# D42). La plupart sont mangés, pourrissent ou ne lèvent jamais ; le grain gardé lève
# ensuite par la niche (`_lever_grains_en_attente`). Levier unique de la relève des
# fruitiers pérennes, calibré sur le critère D130 (`tools/diag_releve.py`, verger_mur,
# seed 42, 200 ans [n=1 run par valeur]) : 0,02 → fourré 18 (cerisier) ; 0,008 → 12 ;
# 0,005 → fourré 9, remplacement noyer 2,5 / pommier 31 / cerisier 322 (≥ 1).
P_GRAIN_CHUTE  = 0.005
# Canal de hash des grains de chute : `week * 73` (aucun autre canal `week * 73`).
_CANAL_CHUTE   = 73


def semaine_abscission(plant) -> int:
    """Semaine de largage PROPRE à un caduc, dérivée de son gène-tempo
    `phenologie_florale` (sprint DÉSYNC PHÉNOLOGIE ①). Convention partagée avec la
    floraison/la sénescence : gène > 1 (individu PRÉCOCE) → largue plus tôt. Bornée
    à la fenêtre d'automne [ABSCISSION_MIN, ABSCISSION_MAX]. Déterministe (le gène
    vient d'un hash, aucun RNG). Factorisé ici pour que le pont (② `serialize.py`)
    calcule la MÊME rampe `automne` sans dupliquer la formule."""
    g = plant.gene("phenologie_florale")
    w = round(ABSCISSION_BASE - ABSCISSION_JITTER * (g - 1.0))
    return max(ABSCISSION_MIN, min(ABSCISSION_MAX, w))


def masse_feuillage(plant, plots_tuile: list) -> float:
    """Masse de feuilles qu'un caduc rend à SA tuile sur une année (AUTOMNE VISIBLE ③).

    Elle suit la surface de la couronne : `FEUILLE_PAR_PLOT` par plot-équivalent couvert.
    `plots_tuile` = les plots de `foliar_plots` situés sur la tuile. La part de couronne
    qui déborde tombe sur le chemin ou chez le voisin, que le moteur ne simule pas : elle
    n'est ni déposée ailleurs, ni reportée sur les plots restants (sinon les bords de
    tuile recevraient le double). Une petite couronne compte sa vraie surface, pas un
    plot entier : un semis ne fait pas un tapis."""
    rayon = plant.plant_class.canopy_radius_at(plant)
    surface_plots = math.pi * rayon * rayon / (PLOT_CM * PLOT_CM)
    return FEUILLE_PAR_PLOT * surface_plots * len(plots_tuile) / len(plant.foliar_plots)


def frac_nouaison(pollen_recu: float) -> float:
    """g(pollen_recu) : fraction de sites qui nouent, rampe douce saturante
    (Monod). Sans plancher (pollen=0 → 0) → un fruitier entomophile sans
    butineur ne fait pas de fruit (pression écologique assumée, §B.2)."""
    return pollen_recu / (pollen_recu + POLLEN_DEMI)


def nouer(plant, frac: float) -> list:
    """Cohortes nouées à la fanaison, `frac` = part des fleurs fécondées (VERGER VIVANT ③).

    Sans levier `fruits_par_site` (herbacées) : comportement d'avant, un fruit sur
    chacun des `round(frac × sites)` premiers sites (≤ MAX_ORGANS). Avec levier (arbres) :
    tous les apex sont des sites et `round(frac × fruits_par_site × sites)` fruits s'y
    répartissent, le reste de la division sur les premiers sites ; un site sans fruit
    ne porte pas de cohorte. Peu de pollen = peu de fruits, sur tout l'arbre. Zéro RNG."""
    cls = plant.plant_class
    par_site = cls.fruits_par_site
    if par_site is None:
        sites = organ_sites(plant)
        return [Fruit(seg_id, 0.0, FRUIT_MASSE)
                for seg_id, _pos in sites[:round(frac * len(sites))]]
    sites = organ_sites(plant, plafond=None)
    if not sites:
        return []
    masse = FRUIT_MASSE if cls.fruit_masse is None else cls.fruit_masse
    base, reste = divmod(round(frac * par_site * len(sites)), len(sites))
    cohortes = [Fruit(seg_id, 0.0, masse, base + (1 if k < reste else 0))
                for k, (seg_id, _pos) in enumerate(sites)]
    return [f for f in cohortes if f.nombre > 0]


def deposer_fruits(plant, tile, eco, fruit, seed: int, week: int) -> None:
    """Litière `fruit` d'une cohorte qui tombe : `nombre × masse`.

    Herbacées (sans `fruits_par_site`) : au plot du pied, comme avant. Arbres : sous
    toute la couronne (plots de la tuile, patron de l'abscission) ; les fruits tombent
    des branches, pas du tronc, et des centaines de fruits sur un seul plot satureraient
    la faune et le sol de ce plot. Toute la masse reste sur les plots de la tuile.

    Fruitier pérenne à graine fertile (zoochorie ②) : la chute SÈME aussi
    (`semer_chute`) — même plots que la chair."""
    masse = fruit.nombre * fruit.masse
    if plant.plant_class.fruits_par_site is None:
        eco.deposer_litiere(*plant.position, "fruit", masse)
        if recrue_par_fruits(plant.plant_class):
            semer_chute(plant, tile, eco, fruit, [plant.position], seed, week)
        return
    plots = [rc for rc in plant.foliar_plots if tile.is_valid_plot(*rc)]
    if not plots:
        plots = [plant.position]
    part = masse / len(plots)
    for r, c in plots:
        eco.deposer_litiere(r, c, "fruit", part)
    if recrue_par_fruits(plant.plant_class):
        semer_chute(plant, tile, eco, fruit, plots, seed, week)


def semer_chute(plant, tile, eco, fruit, plots: list, seed: int, week: int) -> int:
    """Grains SAUVAGES (`origine="chute"`) d'une cohorte qui tombe (zoochorie ②, D42).

    `n = nombre × P_GRAIN_CHUTE`, la partie fractionnaire tranchée par hash ; chaque
    grain va sur un plot tiré par hash parmi `plots` (couronne de l'arbre, ou pied
    d'une herbacée). Gènes = `child_genes(mère, find_father)`, priming =
    `child_expression(mère)` — l'héritage de l'ancien `_reproduction`. Un plot plein
    (plafond ①) refuse le grain : il est perdu. Position sous-plot : None → offset
    féral déterministe à la levée. Renvoie le nombre de grains déposés. Zéro RNG."""
    pr, pc = plant.position
    sel = pr * 1009 + fruit.segment_id      # décorrèle les cohortes d'une même mère
    attendu = fruit.nombre * P_GRAIN_CHUTE
    n = int(attendu)
    if _hash_noise(seed, week * _CANAL_CHUTE, sel, pc) < attendu - n:
        n += 1
    if n == 0:
        return 0
    father = find_father(plant, tile.plants, tile, eco, seed, week)
    genes = child_genes(plant, father, seed, week)
    expr = child_expression(plant)
    ordre = sorted(plots)
    poses = 0
    for k in range(n):
        h = _hash_noise(seed, week * _CANAL_CHUTE, sel, pc * 1009 + k + 1)
        r, c = ordre[min(int(h * len(ordre)), len(ordre) - 1)]
        grain = grain_sauvage(plant.plant_class, genes, expr, "chute", week, None, None)
        poses += deposer_grain_sauvage(tile, r, c, grain)
    return poses


def deposer_bois_tombe(plant, tombes, eco) -> float:
    """Bois mort qui TOMBE (D111 ②) : les segments que la croissance vient d'élaguer
    (`grow_plant` les renvoie) deviennent de la litière `bois` au sol, au lieu de
    disparaître. Seuls les LIGNEUX déposent (même critère de donnée que le squelette
    post-mortem, `frac_bois_mort` > 0) : les tiges mortes des herbacées ont déjà leur
    voie (litière molle à la mort, abscission).

    Chaque segment tombe à la VERTICALE de son milieu : `base` est dans le repère
    cm de la tuile (le collet = `(x_cm, y_cm, 0)`, cf. `PlantInstance.__post_init__`),
    plot = `floor(pos / PLOT_CM)` borné à la tuile (une branche qui déborde du bord
    tombe sur le plot de bordure). Masse ∝ volume `length × thickness²`.
    Renvoie la masse totale déposée (0.0 si rien). Zéro RNG."""
    if not tombes or frac_bois_mort(plant) <= 0.0:
        return 0.0
    total = 0.0
    for s in tombes:
        masse = s.length_cm * s.thickness_cm ** 2 * BOIS_MORT_PAR_CM3
        if masse <= 0.0:
            continue
        mx = s.base[0] + s.dir[0] * s.length_cm * 0.5
        my = s.base[1] + s.dir[1] * s.length_cm * 0.5
        r = min(eco.rows - 1, max(0, int(my // PLOT_CM)))
        c = min(eco.cols - 1, max(0, int(mx // PLOT_CM)))
        eco.deposer_litiere(r, c, "bois", masse, s.thickness_cm)   # grosseur ⑦bis
        total += masse
    return total


class DecompoMixin:
    def _tick_skeletons(self, tile, eco):
        """Squelettes post-mortem (décompo·compost ②, phase B). SEUL point de retrait
        des plantes mortes. Pour chaque morte :
          1. `seche` debout : `semaines_mort += 1` ; ≥ T_SECHE → bascule `couchee` ;
          2. fragmentation : libère `bois_restant × FRAG_RATE × vitesse_locale` en
             litière `bois` au plot (vitesse = décompo locale, comme tick_decomposition) ;
          3. retrait centralisé en fin de pass : morte à bois épuisé OU non ligneuse
             (bois=0 d'emblée → retrait dès ce tick, équivalent à l'ancien filtre).
        Filet de sécurité : une plante morte NON marquée (chemin de dégât hebdo qui
        n'est jamais passé par deposer_mort) est retirée silencieusement, comme le
        faisait l'ancien filtre is_alive de la sénescence.

        Déterministe : itération en ordre `tile.plants`, fragmentation = pur calcul,
        zéro RNG. La litière déposée ici est décomposée au tick SUIVANT (cohérence
        de cascade : _tick_skeletons tourne en fin de tick, après tick_decomposition)."""
        log = []
        for plant in tile.plants:
            if plant.is_alive or not plant.morte:
                continue
            r, c = plant.position
            if plant.stade_mort == "seche":
                plant.semaines_mort += 1
                if plant.semaines_mort >= T_SECHE:
                    plant.stade_mort = "couchee"
            if plant.bois_restant > 1e-9:
                d = min(plant.bois_restant,
                        plant.bois_restant * FRAG_RATE * eco.decomp_speed(r, c))
                eco.deposer_litiere(r, c, "bois", d,
                                    plant.bois_diam_cm or BOIS_DIAM_DEFAUT)
                plant.bois_restant -= d
                if d > 1e-4:
                    log.append(f"    🪵 Fragmentation +{d:.3f} bois @{plant.position} "
                               f"(reste {plant.bois_restant:.2f})")
        # Retrait : vivantes conservées ; mortes conservées TANT QU'il reste du bois.
        tile.plants = [p for p in tile.plants
                       if p.is_alive or (p.morte and p.bois_restant > 1e-9)]
        return log

    def _abscission(self, tile, eco, week_in_year):
        """Abscission d'automne (décompo·compost ②, phase C.1 ; DÉSYNC PHÉNOLOGIE ① ;
        AUTOMNE VISIBLE ③) : les caducs VIVANTS (deciduous, PerennialWoody) larguent leur
        feuillage → litière `feuille`, sous TOUTE leur couronne (plots de la tuile) et sur
        CHUTE_SEMAINES à partir de leur semaine propre (`semaine_abscission`, dérivée du
        gène-tempo). Sans RNG, persistants : rien.

        La ligne 🍂 ne sort qu'à la PREMIÈRE semaine : le ledger des voix (`sim/evenements`)
        en fait UN événement carnet par ligne, et un arbre perd ses feuilles une fois l'an."""
        log = []
        for plant in tile.plants:
            if not plant.is_alive or not plant.plant_class.deciduous:
                continue
            depuis = week_in_year - semaine_abscission(plant)
            if not 0 <= depuis < CHUTE_SEMAINES:
                continue
            plots = [rc for rc in plant.foliar_plots if tile.is_valid_plot(*rc)]
            masse = masse_feuillage(plant, plots)
            if masse <= 0.0:
                continue
            part = masse / (CHUTE_SEMAINES * len(plots))
            for r, c in plots:
                eco.deposer_litiere(r, c, "feuille", part)
            if depuis == 0:
                log.append(f"    🍂 Abscission {plant.name}@{plant.position} "
                           f"→ feuille +{masse:.3f}")
        return log

    def _tick_fruits(self, tile, eco, week_in_year):
        """Organes-fruits traçables (décompo·compost ③, absorbe D19 ; nouaison
        POLLINISÉE ④ — §B). Donne aux fruits un VRAI état moteur (≠ proxy de
        rendu). Trois temps :
          1. Nouaison EN FIN DE FLORAISON, par plante (remplace le rendez-vous
             global FRUIT_NOUAISON_WEEK) : une fruitière mûre s'arme quand sa
             `floraison` dépasse SEUIL_FLEURI puis NOUE quand sa floraison
             retombe sous SEUIL_NOUAISON (fleurs fanées). La fraction de sites
             qui nouent dépend du MODE de pollinisation : `self` court-circuite
             (frac=1, nouaison pleine sans vecteur) ; `insect` lit la dose
             `pollen_recu` des butineurs (§F), `wind` celle du panache anémophile
             (⑤, §5.3) — les deux via g() SANS plancher (0 dose → 0 fruit, §B.2).
             On pose des cohortes vertes
             (maturité 0) sur les sites reproducteurs (`nouer` : 1 fruit par site
             pour une herbacée, `fruits_par_site` répartis pour un arbre) ; `pollen_recu` est
             remis à 0 (cohorte suivante repart de zéro). Les fruits non récoltés
             de l'an passé chutent d'abord en litière `fruit`.
          2. Maturation hebdomadaire : `maturite += FRUIT_DMAT`, ou 1 / durée pour
             une espèce à `fruit_semaines_maturation` (sprint HOUPPIER ③).
          3. Chute (§2.4) : un fruit dont la maturité dépasse MATURITE_CHUTE est
             sur-mûr → tombe en litière `fruit` (déclenche la cascade fertilité).

        Le geste `manger` ciblé (sim.actions, D19) retire un fruit précis hors de
        ce pas. Déterministe : `floraison`/`pollen_recu`/`organ_sites` dérivent de
        la météo pure et des butineurs déterministes (zéro RNG), itération en
        ordre `tile.plants`. NEUTRE pour le golden tant qu'aucune espèce
        `fruitier` mûre ne fleurit dans la fenêtre (tomate : meurt w2-3 ;
        AppleTree : maturity_years=5 > 2 ans simulés → floraison nulle)."""
        log = []
        seed, week = self.game_state.get("seed", 42), self.week
        for plant in tile.plants:
            if not plant.is_alive:
                continue
            cls = plant.plant_class
            if not getattr(cls, "fruitier", False):
                continue
            # 1. Armement à la pleine floraison, nouaison à la fanaison (par plante).
            if plant.floraison >= SEUIL_FLEURI:
                plant.a_fleuri = True
            if (plant.a_fleuri and plant.floraison < SEUIL_NOUAISON
                    and plant.age_years >= cls.maturity_years):
                for f in plant.fruits:          # cohorte précédente non récoltée
                    deposer_fruits(plant, tile, eco, f, seed, week)
                # Fraction nouée selon le mode (philo #2 : flux de pollinisation →
                # contrainte → fruits). `insect` lit la dose des butineurs (§F),
                # `wind` lit la dose ANÉMOPHILE déposée par le vent (⑤, §5.3) — les
                # deux via g() SANS plancher (0 dose → 0 fruit). Seule l'autogamie
                # (`self`) court-circuite (frac=1, nouaison pleine sans vecteur).
                frac = (1.0 if cls.pollination_mode == "self"
                        else frac_nouaison(plant.pollen_recu))
                # Glandée (zoochorie ②) : année forte ×1, maigre ×GLANDEE_MAIGRE,
                # synchrone pour toute l'espèce. Sans masting → ×1 (inchangé).
                frac *= facteur_glandee(cls, (week - 1) // 52, seed)
                plant.fruits = nouer(plant, frac)
                plant.a_fleuri = False          # cohorte posée → ré-armée l'an prochain
                plant.pollen_recu = 0.0         # nouvelle cohorte repart de zéro (§B.1)
                if plant.fruits:
                    log.append(f"    🍎 Nouaison {plant.name}@{plant.position} "
                               f"→ {sum(f.nombre for f in plant.fruits)} fruits "
                               f"(frac {frac:.2f})")
            # 2-3. Maturation + chute des sur-mûrs.
            if plant.fruits:
                duree = cls.fruit_semaines_maturation
                dmat = FRUIT_DMAT if duree is None else 1.0 / duree
                survivors = []
                for f in plant.fruits:
                    f.maturite += dmat
                    if f.maturite > MATURITE_CHUTE:
                        deposer_fruits(plant, tile, eco, f, seed, week)
                        log.append(f"    🍂 Chute fruit (mûr {f.maturite:.2f}) "
                                   f"{plant.name}@{plant.position} → fruit "
                                   f"+{f.nombre * f.masse:.3f}")
                    else:
                        survivors.append(f)
                plant.fruits = survivors
        return log
