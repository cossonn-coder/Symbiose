"""
SYMBIOSE — tests/test_plasticite.py
Test ciblé, lancé À LA DEMANDE (hors smoke test).

Couvre le SUBSTRAT de plasticité (sprint plasticité ①) : l'EXPRESSION plastique
des gènes adaptogènes dérive du stress vécu, distincte du génotype figé.
Conception : docs/conception/CONCEPTION_PLASTICITE_EXPRESSION.md (§2.1-2.3).

Au tronçon ① PERSONNE ne lit `expressed_gene` (acclimatation INERTE) ; on teste
donc la TUYAUTERIE en isolation, pas un effet écologique :
  ① expressed_gene = clamp_gene(génotype × expression), == génotype si neutre,
     borné par les limites dures (clamp_gene) ;
  ② acclimatation : sous stress installé (mémoire haute), expression monte vers
     1 + EXPR_GAIN à la vitesse TAU_UP ;
  ③ HYSTÉRÈSE : stress levé → expression redescend à TAU_DOWN < TAU_UP (la plante
     garde un temps son endurcissement) ; bornée [EXPR_MIN, EXPR_MAX].

On appelle directement `engine._update_physiology(tile, eco)` (une étape de mise à
jour des mémoires + expression, sans le reste du tick) en ÉPINGLANT la mémoire de
stress via une surcharge d'`eco.humidite.at_plot` (patron du test stress chronique)
→ pas/peu de RNG, assertions numériques exactes.

Lancement (depuis data/code/) :
  python3 -m tests.test_plasticite
"""

import sys

from world import Tile
from plants import (Zucchini, clamp_gene,
                    EXPR_GAIN, EXPR_MIN, EXPR_MAX, TAU_UP, TAU_DOWN, GENE_HARD_MAX)
from fields import init_eco
from sim.engine import Engine
from sim.effects.perturbations import drought_stress_damage, DROUGHT_DAMAGE_THRESHOLD
from sim.growth.phases import shade_tolerance_effective

_GENE = "tolerance_secheresse"   # gène adaptogène ↔ drought_memory (le plus simple à piloter)
_EPS  = 1e-9


def _lab():
    """Tuile 6×6 terre + plante + Engine ; renvoie (engine, tile, eco, plant)."""
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = init_eco("T0", 6, 6, humidite=1.2, fertilite=1.2, microbiome=0.3)
    plant = tile.add_plant(Zucchini, 3, 3)
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {},
          "current_player": "j1", "week": 1, "log": []}
    return Engine(gs), tile, eco, plant


def _pin_humidite(eco, hum: float):
    """Épingle l'humidité lue partout → drought_memory pilotée à volonté.
    hum=0   → drought_stress 1.0 (sécheresse sévère, cible mémoire 1.0) ;
    hum≥2.5 → drought_stress 0   (confort, cible mémoire 0)."""
    eco.humidite.at_plot = lambda r, c, _h=hum: _h


def test_expressed_gene_math():
    """expressed_gene = clamp_gene(génotype × expression) : neutre ⇒ == génotype ;
    sur-exprimé ⇒ > génotype ; jamais hors des limites dures (clamp_gene)."""
    _, _, _, p = _lab()
    p.genes = {_GENE: 1.2}
    # Neutre (défaut 1.0) → phénotype = génotype
    assert abs(p.expressed_gene(_GENE) - 1.2) < _EPS, "neutre : expressed ≠ génotype"
    # Sur-expression → phénotype relevé
    p.expression[_GENE] = 1.1
    assert abs(p.expressed_gene(_GENE) - clamp_gene(1.2 * 1.1)) < _EPS
    assert p.expressed_gene(_GENE) > p.gene(_GENE), "sur-expression n'élève pas le phénotype"
    # Borne dure : génotype haut × expression haute → plafonné à GENE_HARD_MAX
    p.genes[_GENE] = 1.5
    p.expression[_GENE] = EXPR_MAX
    assert abs(p.expressed_gene(_GENE) - GENE_HARD_MAX) < _EPS, "clamp_gene ne plafonne pas"
    # Gène NON adaptogène (absent d'expression) → expressed == gene
    p.genes["hauteur"] = 1.3
    assert abs(p.expressed_gene("hauteur") - 1.3) < _EPS, "gène non adaptogène altéré"
    print("[plasticité ①·math] PASS — expressed_gene = clamp(génotype×expression), bornes OK")


def test_acclimatation_vitesse_montee():
    """Sous stress installé (drought_memory épinglée 1.0), l'expression fait UN pas
    vers la cible 1+EXPR_GAIN exactement à la vitesse TAU_UP."""
    engine, tile, eco, p = _lab()
    _pin_humidite(eco, 0.0)              # sécheresse sévère → cible mémoire 1.0
    p.drought_memory = 1.0              # épinglée (hum=0 la maintient)
    p.expression[_GENE] = 1.0
    engine._update_physiology(tile, eco)
    cible = 1.0 + EXPR_GAIN             # 1.30
    attendu = 1.0 + (cible - 1.0) * TAU_UP
    assert abs(p.expression[_GENE] - attendu) < 1e-6, (
        f"montée à TAU_UP fausse : {p.expression[_GENE]:.6f} ≠ {attendu:.6f}")
    # Saturation : après beaucoup de pas, asymptote vers la cible sans la dépasser
    for _ in range(500):
        p.drought_memory = 1.0
        engine._update_physiology(tile, eco)
    assert p.expression[_GENE] <= EXPR_MAX + _EPS, "expression dépasse EXPR_MAX"
    assert abs(p.expression[_GENE] - cible) < 1e-3, "n'asymptote pas vers la cible"
    print(f"[plasticité ①·montée] PASS — un pas = TAU_UP ({TAU_UP}), "
          f"asymptote {p.expression[_GENE]:.4f}≈{cible}")


def test_hysterese_descente_plus_lente():
    """Stress levé : l'expression redescend à TAU_DOWN < TAU_UP (désacclimatation
    plus lente que l'acclimatation, à distance-à-la-cible ÉGALE → hystérèse)."""
    engine, tile, eco, p = _lab()
    gap = EXPR_GAIN                     # même écart 0.30 pour comparer les vitesses
    # MONTÉE : expression EXPR_MIN, cible EXPR_MIN+gap (mémoire 1.0)
    _pin_humidite(eco, 0.0)
    p.drought_memory = 1.0
    p.expression[_GENE] = EXPR_MIN
    engine._update_physiology(tile, eco)
    frac_montee = (p.expression[_GENE] - EXPR_MIN) / gap
    # DESCENTE : expression EXPR_MIN+gap, cible EXPR_MIN (mémoire 0)
    _pin_humidite(eco, 3.0)            # confort → drought_stress 0
    p.drought_memory = 0.0
    p.expression[_GENE] = EXPR_MIN + gap
    engine._update_physiology(tile, eco)
    frac_descente = (EXPR_MIN + gap - p.expression[_GENE]) / gap
    assert abs(frac_montee - TAU_UP) < 1e-6 and abs(frac_descente - TAU_DOWN) < 1e-6, (
        f"fractions ≠ τ : montée {frac_montee:.4f}/{TAU_UP}, descente {frac_descente:.4f}/{TAU_DOWN}")
    assert frac_descente < frac_montee, (
        f"pas d'hystérèse : descente {frac_descente:.4f} ≥ montée {frac_montee:.4f}")
    assert p.expression[_GENE] >= EXPR_MIN - _EPS, "expression sous EXPR_MIN"
    print(f"[plasticité ①·hystérèse] PASS — descente {frac_descente} < montée "
          f"{frac_montee} (TAU_DOWN<TAU_UP)")


def _compte_degats_secheresse(plant, eco, expression: float) -> int:
    """Nombre de tics où drought_stress_damage tape, sur 300 semaines déterministes,
    à drought_memory saturée (1.0) et expression `expression` épinglée. Plus l'expression
    monte, plus expressed_gene monte, plus la proba 1/expressed_gene baisse → moins de
    dégâts. _hash_noise(seed, week·37, r, c) varie par semaine → échantillonnage sans RNG."""
    plant.drought_memory = 1.0                      # > seuil → sévérité 1.0
    plant.expression[_GENE] = expression
    return sum(1 for wk in range(1, 301)
               if drought_stress_damage(plant, eco, seed=42, week=wk))


def test_branchement_acclimatation():
    """Tronçon ② : les consommateurs lisent expressed_gene, donc l'acclimatation agit.
      • NON-RÉGRESSION : à expression neutre (1.0) le point de lecture rend EXACTEMENT
        le génotype → dégât et gate identiques au comportement d'avant branchement ;
      • ACCLIMATATION : à expression haute, le dégât (sécheresse) et la gate (ombre)
        sont MESURABLEMENT plus doux."""
    _, _, eco, p = _lab()
    p.genes = {_GENE: 1.0, "tolerance_ombre": 0.8}   # héliophile (tol ombre < 1)

    # — Chemin de DÉGÂT (drought_stress_damage) —
    assert DROUGHT_DAMAGE_THRESHOLD < 1.0            # garde-fou : mémoire 1.0 franchit le seuil
    n_neutre = _compte_degats_secheresse(p, eco, 1.0)
    # Non-régression : à neutre, le point de lecture == génotype brut (expression vient
    # d'être épinglée à 1.0 par le comptage neutre)
    assert abs(p.expressed_gene(_GENE) - p.gene(_GENE)) < _EPS, "neutre ≠ génotype au point de lecture"
    n_endurci = _compte_degats_secheresse(p, eco, EXPR_MAX)
    assert n_neutre > 0, "le test n'exerce pas le dégât (aucun tic touché)"
    assert n_endurci < n_neutre, (
        f"acclimatation n'adoucit pas le dégât : endurci {n_endurci} ≥ neutre {n_neutre}")

    # — GATE (tolérance ombre effective, déterministe) —
    base = p.plant_class.shade_tolerance_base()
    p.expression["tolerance_ombre"] = 1.0
    assert abs(shade_tolerance_effective(p) - base * p.gene("tolerance_ombre")) < _EPS, (
        "neutre : gate ombre ≠ base×génotype")
    p.expression["tolerance_ombre"] = EXPR_MAX
    assert shade_tolerance_effective(p) > base * p.gene("tolerance_ombre"), (
        "acclimatation n'assouplit pas la gate ombre")
    print(f"[plasticité ②·branchement] PASS — neutre=génotype ; endurci {n_endurci} dégât(s) "
          f"< neutre {n_neutre}, gate ombre relevée")


if __name__ == "__main__":
    try:
        test_expressed_gene_math()
        test_acclimatation_vitesse_montee()
        test_hysterese_descente_plus_lente()
        test_branchement_acclimatation()
    except AssertionError as e:
        print(f"[plasticité ①] FAIL — {e}")
        sys.exit(1)
    sys.exit(0)
