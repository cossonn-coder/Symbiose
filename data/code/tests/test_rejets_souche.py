"""
SYMBIOSE — tests/test_rejets_souche.py
Test ciblé, lancé À LA DEMANDE (hors smoke test). Sprint FREIN REJETS FIGUIER ②.

La souche rejette à la mort de l'arbre (`sim/souche.py`), si elle est restée
vivante (`sim.effects.perturbations.souche_vivante`, figé par `deposer_mort`) :
  (a) figuier mort de vieillesse (mémoires basses), au printemps → rejets au pied
      (≤ RAYON_REJET_CM), clones (gènes, form_seed) ;
  (b) même figuier mort avec `shade_memory` au-dessus de `seuil_ombre` → 0 rejet ;
  (c) sapin mort → 0 rejet (`rejet_souche` = 0) ;
  (d) mort en HIVER → rien avant la 1ʳᵉ semaine de printemps, la vague y part,
      et c'est la seule ;
  (e) figuier vivant mûr, 200 semaines → 0 rejet (plus d'émission de fond).

Perte de couronne d'un arbre VIVANT (③, `perte_couronne`) :
  (f) figuier de 10 ans taillé au ras (`tailler` sur tout ce que porte le collet)
      EN HIVER → rien pendant l'hiver, une vague au 1ᵉʳ printemps, au pied, clones ;
  (g) casse de vent normale (2 branches, `branches_a_casser` comme une tempête)
      → mémoire sous le seuil, aucun rejet en 1 an ;
  (h) figuier à `shade_memory` haute taillé au ras → aucun rejet (souche épuisée),
      épisode consommé ; sapin taillé au ras → aucun rejet ;
  (i) une seule vague par épisode : 2 ans après la vague, aucune autre.

Lancement (depuis data/code/) :
  python3 -m tests.test_rejets_souche
"""

import math
import sys

from calendrier import saison_de, wiy_de
from world import Tile
from fields import init_eco
from plants import Fig, FirTree
from sim.clonal import emettre_ramets
from sim.effects import deposer_mort
from sim.effects.perturbations import seuil_ombre
from sim.souche import (emettre_rejets_souche, nombre_rejets, RAYON_REJET_CM,
                        SEUIL_PERTE_COURONNE, noter_perte_couronne)
from sim.engine.branches import FRAC_MAX_CASSE
from sim.growth import branches_a_casser, couper_branches
from sim import actions as ACT
from sim import vigueur as V
from sim.growth import grow_plant
from sim.growth.geometrie import _children

SEED = 42
S_PRINTEMPS = 5          # une semaine de printemps (wiy 5)
S_HIVER = 45             # une semaine d'hiver de la 1ʳᵉ année


def _monde(cls=Fig):
    """Un arbre mûr au centre d'une tuile 20×20, plein soleil imposé."""
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=20, grid_cols=20)
    eco = init_eco("T0", 20, 20, humidite=1.0, fertilite=1.0, microbiome=0.3)
    arbre = tile.add_plant(cls, 10, 10)
    arbre.age_years = cls.maturity_years + 20.0
    arbre.genes = {k: v * 1.01 for k, v in arbre.genes.items()}   # marqueur de clone
    arbre.form_seed = 12345
    eco.lumiere.at_plot = lambda r, c: 0.9
    return tile, eco, arbre


def _tuer(arbre, eco):
    arbre.vitalite = 0.0
    deposer_mort(arbre, eco)


def _rejets(tile, arbre):
    return [p for p in tile.plants if p is not arbre and p.is_alive]


def test_mort_de_vieillesse():
    tile, eco, fig = _monde()
    _tuer(fig, eco)
    assert fig.souche_vivante, "souche jugée morte alors que les mémoires sont basses"
    log = emettre_rejets_souche(tile, SEED, S_PRINTEMPS)
    rejets = _rejets(tile, fig)
    assert len(rejets) == nombre_rejets(Fig) >= 1, f"{len(rejets)} rejet(s)"
    assert len(log) == 1 and "Rejet de souche" in log[0], log
    for p in rejets:
        d = math.hypot(p.x_cm - fig.x_cm, p.y_cm - fig.y_cm)
        assert d <= RAYON_REJET_CM + 1e-9, f"rejet à {d:.0f} cm"
        assert p.genes == fig.genes and p.form_seed == fig.form_seed, "pas un clone"
    print(f"[souche (a)] PASS — {len(rejets)} rejets au pied, clones : {log[0].strip()}")


def test_souche_epuisee_par_ombre():
    tile, eco, fig = _monde()
    fig.shade_memory = seuil_ombre(fig) + 0.05
    _tuer(fig, eco)
    n = len(emettre_rejets_souche(tile, SEED, S_PRINTEMPS))
    assert not fig.souche_vivante and n == 0 and not _rejets(tile, fig)
    print("[souche (b)] PASS — mort d'ombre : 0 rejet")


def test_sapin():
    tile, eco, sapin = _monde(FirTree)
    _tuer(sapin, eco)
    emettre_rejets_souche(tile, SEED, S_PRINTEMPS)
    assert not sapin.souche_vivante and not _rejets(tile, sapin)
    print("[souche (c)] PASS — sapin : 0 rejet")


def test_mort_en_hiver():
    tile, eco, fig = _monde()
    _tuer(fig, eco)
    vagues = []
    for wk in range(S_HIVER, S_HIVER + 30):
        if emettre_rejets_souche(tile, SEED, wk):
            vagues.append(wk)
    assert len(vagues) == 1, f"vagues aux semaines {vagues}"
    wk = vagues[0]
    assert saison_de(wiy_de(wk)) == "printemps" and saison_de(wiy_de(wk - 1)) == "hiver", \
        f"vague semaine {wk} ({saison_de(wiy_de(wk))}), pas la 1re de printemps"
    print(f"[souche (d)] PASS — mort semaine {S_HIVER} (hiver) : une vague, semaine {wk}")


def test_figuier_vivant_sans_rejet():
    tile, eco, fig = _monde()
    n = 0
    for wk in range(1, 201):
        n += len(emettre_ramets(tile, eco, SEED, wk))
        n += len(emettre_rejets_souche(tile, SEED, wk))
    assert n == 0 and not _rejets(tile, fig), f"{n} émission(s) d'un figuier vivant"
    print("[souche (e)] PASS — figuier vivant mûr : 0 rejet en 200 semaines")


# --- ③ Perte de couronne d'un arbre vivant ---

def _arbre_structure(cls=Fig):
    """Arbre de 10 ans à STRUCTURE réelle (520 semaines de `grow_plant`), plein soleil."""
    tile, eco, arbre = _monde(cls)
    for w in range(1, 521):
        grow_plant(arbre, SEED, w, None)
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {},
          "current_player": "joueur_1", "week": 1, "log": [], "seed": SEED}
    return tile, eco, arbre, gs


def _tailler(gs, arbre, eco, seg_id):
    V.ensure_player(gs, "joueur_1")["courante"] = 100.0      # Vigueur toujours suffisante
    assert ACT.tailler(gs, "joueur_1", arbre, eco, segment_id=seg_id)


def _tailler_au_ras(gs, arbre, eco):
    """Coupe tout ce que porte le collet (tronc + charpentières) : recépage."""
    while _children(arbre.segments)[0]:
        _tailler(gs, arbre, eco, _children(arbre.segments)[0][0])


def test_taille_severe_rejette():
    tile, eco, fig, gs = _arbre_structure()
    _tailler_au_ras(gs, fig, eco)
    perte = fig.perte_couronne
    assert perte >= SEUIL_PERTE_COURONNE, f"perte_couronne {perte:.2f} sous le seuil"
    vagues = []
    for wk in range(S_HIVER, S_HIVER + 30):
        log = emettre_rejets_souche(tile, SEED, wk)
        if log:
            vagues.append((wk, log))
    assert len(vagues) == 1, f"vagues : {[w for w, _ in vagues]}"
    wk, log = vagues[0]
    assert saison_de(wiy_de(wk)) == "printemps" and saison_de(wiy_de(wk - 1)) == "hiver", \
        f"vague semaine {wk} ({saison_de(wiy_de(wk))}), pas la 1re de printemps"
    assert "perte de couronne" in log[0], log
    rejets = _rejets(tile, fig)
    assert len(rejets) == nombre_rejets(Fig, perte) >= 1, f"{len(rejets)} rejet(s)"
    for p in rejets:
        assert math.hypot(p.x_cm - fig.x_cm, p.y_cm - fig.y_cm) <= RAYON_REJET_CM + 1e-9
        assert p.genes == fig.genes and p.form_seed == fig.form_seed, "pas un clone"
    assert fig.is_alive and fig.perte_couronne == 0.0
    print(f"[souche (f)] PASS — taille au ras en hiver (perte {perte:.2f}) : vague "
          f"semaine {wk} : {log[0].strip()}")
    return tile, fig


def test_petite_casse():
    tile, eco, fig, gs = _arbre_structure()
    tombes = couper_branches(fig, branches_a_casser(fig, 2, SEED, S_PRINTEMPS,
                                                     FRAC_MAX_CASSE))
    assert tombes, "la casse n'a rien fait tomber"
    noter_perte_couronne(fig, tombes)          # même appel que `mort_des_branches`
    perte = fig.perte_couronne
    assert 0.0 < perte < SEUIL_PERTE_COURONNE, f"perte {perte:.3f}"
    n = sum(len(emettre_rejets_souche(tile, SEED, wk)) for wk in range(1, 53))
    assert n == 0 and not _rejets(tile, fig), f"{n} vague(s) pour un rameau"
    print(f"[souche (g)] PASS — casse de 2 branches (perte {perte:.3f}) : 0 rejet en 1 an, "
          f"mémoire oubliée à {fig.perte_couronne:.4f}")


def test_souche_epuisee_ou_sapin():
    tile, eco, fig, gs = _arbre_structure()
    fig.shade_memory = seuil_ombre(fig) + 0.05
    _tailler_au_ras(gs, fig, eco)
    assert fig.perte_couronne >= SEUIL_PERTE_COURONNE
    n = sum(len(emettre_rejets_souche(tile, SEED, wk)) for wk in range(S_PRINTEMPS, 60))
    assert n == 0 and not _rejets(tile, fig) and fig.perte_couronne == 0.0
    tile, eco, sapin, gs = _arbre_structure(FirTree)
    _tailler_au_ras(gs, sapin, eco)
    perte = sapin.perte_couronne
    n = sum(len(emettre_rejets_souche(tile, SEED, wk)) for wk in range(S_PRINTEMPS, 60))
    assert perte >= SEUIL_PERTE_COURONNE and n == 0 and not _rejets(tile, sapin), \
        f"sapin : perte {perte:.2f}, {n} vague(s)"
    print(f"[souche (h)] PASS — figuier ombragé taillé : 0 rejet ; sapin taillé au ras "
          f"(perte {perte:.2f}) : 0 rejet")


def test_une_vague_par_episode():
    tile, fig = test_taille_severe_rejette()
    avant = len(_rejets(tile, fig))
    n = sum(len(emettre_rejets_souche(tile, SEED, wk))
            for wk in range(S_HIVER + 30, S_HIVER + 30 + 104))
    assert n == 0 and len(_rejets(tile, fig)) == avant, f"{n} vague(s) de plus"
    print("[souche (i)] PASS — une seule vague : rien dans les 2 ans qui suivent")


if __name__ == "__main__":
    tests = [test_mort_de_vieillesse, test_souche_epuisee_par_ombre, test_sapin,
             test_mort_en_hiver, test_figuier_vivant_sans_rejet,
             test_taille_severe_rejette, test_petite_casse,
             test_souche_epuisee_ou_sapin, test_une_vague_par_episode]
    echecs = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            echecs += 1
            print(f"[souche] FAIL {t.__name__} : {e}")
    sys.exit(1 if echecs else 0)
