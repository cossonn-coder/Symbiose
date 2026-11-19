"""
SYMBIOSE — tests/test_reponse_thermique.py
La plante répond à sa plage vivable et meurt d'elle-même (D139, sprint niche
thermique ③). Hors golden : plantes et EcoFields à conditions forcées.

Vérifie :
  - le gel frappe un basilic ADULTE (plus de filtre `semis`), pas une mâche ;
  - un basilic à des nuits de 6 °C s'abîme sans gel (marque `froid`) ;
  - une plante dont la feuille dépasse `lim_chaud` ne pousse pas ; au-delà de
    `lim_brul` elle brûle ;
  - une annuelle ne meurt plus à la transition hivernale (semaine 49) ;
  - elle s'éteint après floraison + maturation (fin de cycle) et sème la banque ;
  - la grêle épargne toujours les adultes.

Usage (depuis data/code/) :
  python3 -m tests.test_reponse_thermique
"""
import sys

from world import Tile
from plants import Basil, CornSalad, BursaPastoris
from fields import init_eco
from fields.ecofields.thermique import t_min_nuit_at
from sim.engine import Engine
import sim.engine.reponse_thermique as RT
from sim.engine.fin_de_cycle import MATURATION_DEFAUT

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'OK ' if cond else 'XX '} {name}" + (f" — {detail}" if detail else ""))


def lab(*especes, week=1):
    """Tuile 6×6 nue ; une plante par espèce, sur la diagonale."""
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = init_eco("T0", 6, 6, humidite=1.2, fertilite=1.2, microbiome=0.3)
    plantes = [tile.add_plant(cls, 1 + 2 * i, 1 + 2 * i) for i, cls in enumerate(especes)]
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {}, "seed": 42,
          "current_player": "j1", "week": week, "log": []}
    return Engine(gs), tile, eco, plantes


def adulte(p):
    p.current_stage = len(p.plant_class.growth_stages) - 1
    return p


def test_gel():
    print("\n[1] gel : tous stades, sous la limite de chaque plante")
    eng, tile, eco, (b, m) = lab(Basil, CornSalad)
    adulte(b), adulte(m)
    t_air = -1.0
    nuit = t_min_nuit_at(eco, *b.position, t_air, 0.0)
    check("nuit forcée entre lim_gel mâche et basilic",
          m.lim_gel() < nuit < b.lim_gel(), f"nuit {nuit:.1f} °C")
    RT_nuit = RT.t_min_nuit_at
    RT.t_min_nuit_at = lambda *a: nuit
    try:
        log = eng._tick_nuit_froide(tile, eco, t_air, 0.0)
    finally:
        RT.t_min_nuit_at = RT_nuit
    # Stress au bilan ② : 8 °C sous sa limite, bourgeons et collet gèlent → détruit.
    gel_b = any("Basilic" in l and "gel (bourgeons" in l for l in log)
    check("le basilic ADULTE gèle", gel_b and not b.is_alive, f"vit {b.vitalite:.2f}")
    check("la mâche adulte ne gèle pas", m.vitalite == 1.0 and "gel" not in m.symptom_marks)


def _nuit_forcee(eng, tile, eco, nuit, t_air):
    RT_nuit = RT.t_min_nuit_at
    RT.t_min_nuit_at = lambda *a: nuit
    try:
        return eng._tick_nuit_froide(tile, eco, t_air, 0.0)
    finally:
        RT.t_min_nuit_at = RT_nuit


def test_gel_tissus():
    print("\n[1b] gel : feuilles d'abord, bourgeons ensuite (stress au bilan ②)")
    from plants import Tomato, OakTree
    from plants.genetics import EXPR_MAX
    eng, tile, eco, (t,) = lab(Tomato)
    adulte(t)
    r0 = t.reserves
    _nuit_forcee(eng, tile, eco, t.lim_gel() - 1.5, 2.0)
    # (Tropicale : la lésion par le froid de la même nuit s'ajoute — feuillage à 0.)
    check("tomate, gel léger (−1,5 °C sous sa limite) : feuilles perdues, bourgeons vivants",
          t.is_alive and t.feuillage < 1.0 and t.reserves == r0
          and t.symptom_marks.get("gel", 0.0) > 0.0,
          f"feuillage {t.feuillage:.2f}, réserves {t.reserves:.2f}")
    eng, tile, eco, (t,) = lab(Tomato)
    adulte(t)
    log = _nuit_forcee(eng, tile, eco, t.lim_gel() - 4.5, 2.0)
    check("tomate, gel profond (−4,5 °C sous sa limite) : bourgeons gelés, morte",
          not t.is_alive and any("bourgeons et collet" in l and "meurt" in l for l in log))
    eng, tile, eco, (c,) = lab(OakTree)
    c.expression["rusticite_froid"] = EXPR_MAX
    _nuit_forcee(eng, tile, eco, -10.0, 1.0)
    check("chêne endurci à −10 °C : ne perd rien", c.feuillage == 1.0 and c.vitalite == 1.0,
          f"lim_gel {c.lim_gel():.1f}")
    check("… mais le gel-dégel embolise un peu ses vaisseaux", 0.0 < c.embolie < 0.05,
          f"embolie {c.embolie:.3f}")
    eng, tile, eco, (c,) = lab(OakTree)
    _nuit_forcee(eng, tile, eco, c.lim_gel() - 5.0, 1.0)
    check("chêne désendurci, gelée d'avril (−5 °C sous sa limite) : dégarni mais vivant",
          c.is_alive and c.feuillage < 0.5, f"feuillage {c.feuillage:.2f}")
    eng, tile, eco, (c,) = lab(OakTree)
    _nuit_forcee(eng, tile, eco, -10.0, -3.0)
    check("pas de dégel (journée sous 0 °C) : pas d'embolie de gel-dégel", c.embolie == 0.0)


def test_froid():
    print("\n[2] froid sans gel : basilic à 6 °C")
    eng, tile, eco, (b, m) = lab(Basil, CornSalad)
    RT_nuit = RT.t_min_nuit_at
    RT.t_min_nuit_at = lambda *a: 6.0
    try:
        eng._tick_nuit_froide(tile, eco, 12.0, 0.5)
        v1 = b.vitalite
        eng._tick_nuit_froide(tile, eco, 12.0, 0.5)
    finally:
        RT.t_min_nuit_at = RT_nuit
    check("le basilic décline nuit après nuit", 1.0 > v1 > b.vitalite, f"{v1:.2f} → {b.vitalite:.2f}")
    check("marque de symptôme `froid`", b.symptom_marks.get("froid", 0.0) > 0.0)
    check("la mâche (non sensible) n'a rien", m.vitalite == 1.0)


def test_chaleur():
    print("\n[3] chaleur : pas de croissance au-dessus de lim_chaud, brûlure au-delà")
    def essai(t_air, hum):
        eng, tile, eco, (p,) = lab(BursaPastoris)
        p.age_weeks = 50
        eco.temperature.fill(t_air)
        eco.temperature_sol.fill(t_air)
        eco.humidite.at_plot = lambda r, c, _h=hum: _h
        eco.lumiere.light_received = lambda q: 1.0
        stade = p.current_stage
        # D140 G ② : l'avancement lit le DERNIER bilan (`bilan_net`, `limitant`,
        # posés par la physiologie au tick précédent). On le pose « à blanc » avec les
        # fonctions PURES de `sim.bilan` (sans débiter les réserves : à 30 °C sur sol
        # sec, une semaine de vraie physiologie affamerait la plante — autre sujet).
        from sim.bilan import f_lum, f_eau, rampes_thermiques, bilan, facteur_limitant
        eng._avancer_stades(tile, eco, 0.0)          # pose T_feuille
        p.age_weeks -= 1                              # (sans compter 2 semaines)
        froid, chaud = rampes_thermiques(p, t_air, p.t_feuille)
        fl, fe = f_lum(1.0), f_eau(p, hum)
        p.bilan_net = bilan(p, 1.0, fl, fe, froid * chaud, 1.0, 1.0, t_air, False)
        p.limitant = facteur_limitant(fl, fe, froid, chaud, hum)
        log = eng._avancer_stades(tile, eco, 0.0)
        return eng, tile, eco, p, stade, log
    _, _, _, p, stade, log = essai(15.0, 1.2)
    check("au frais, elle avance de stade", p.current_stage > stade, f"T_f {p.t_feuille:.1f}")
    eng, tile, eco, p, stade, log = essai(30.0, 0.0)
    check("feuille > lim_chaud : pas de croissance",
          p.t_feuille > p.lim_chaud() and p.current_stage == stade
          and any("stagne (chaud" in l for l in log), f"T_f {p.t_feuille:.1f}")
    check("feuille > lim_brul : brûlure",
          p.t_feuille > p.lim_brul() and eng._tick_brulure(tile, eco)
          and p.symptom_marks.get("brulure", 0.0) > 0.0, f"vit {p.vitalite:.2f}")


def test_hiver():
    print("\n[4] fin de la mort calendaire")
    eng, tile, eco, (b,) = lab(Basil, week=49)
    adulte(b)
    eng._winter_transition(tile, eco, 49)
    check("une annuelle ne meurt plus en semaine 49", b.is_alive)


def test_fin_de_cycle():
    print("\n[5] fin de cycle : après floraison + maturation")
    eng, tile, eco, (b,) = lab(BursaPastoris)
    adulte(b)
    b.floraison_abs = 10
    b.fecondation = 1.0   # fleurs fécondées à la fanaison (D139 ①b)
    fin = 10 + BursaPastoris.bloom_duration + MATURATION_DEFAUT
    eng.game_state["week"] = fin - 1
    eng._tick_senescence_health(tile, eco)
    check("avant la fin : intacte", b.vitalite == 1.0)
    log = []
    for w in range(fin, fin + 3):
        eng.game_state["week"] = w
        log += eng._tick_senescence_health(tile, eco)
    check("trois semaines plus tard : éteinte", not b.is_alive)
    check("log « meurt (fin de cycle) »", any("meurt (fin de cycle)" in l for l in log))
    r, c = b.position
    check("graines (gènes) à la banque",
          BursaPastoris in eco.seed_bank.species[r][c]
          and eco.seed_bank.data[r][c]["pioneer"] > 0.0)


# Avant stress au bilan ②bis (grêle sur les semis seuls) — test supplanté, conservé :
# def test_grele():
#     print("\n[6] la grêle épargne les adultes")
#     eng, tile, eco, (a, s) = lab(Basil, Basil)
#     adulte(a)
#     eng._mediated_damage(tile, eco, 1.0, "grêle (feuillage)", cause="grele")
#     check("adulte épargné", a.vitalite == 1.0)
#     check("semis touché", s.vitalite < 1.0, f"vit {s.vitalite:.2f}")


def _grele(eng, tile, eco, sev):
    from sim.engine.reponse_grele import grele_tissus
    return eng._mediated_damage(tile, eco, sev, "grêle (feuillage)", cause="grele",
                                species_base="hail_resistance_base",
                                seulement_semis=False, reponse=grele_tissus)


def test_grele():
    print("\n[6] grêle sur tous les stades (stress au bilan ②bis)")
    eng, tile, eco, (a, s) = lab(Basil, Basil)
    adulte(a)
    r0 = a.reserves
    _grele(eng, tile, eco, 1.0)
    check("adulte : feuilles hachées, vivant, réserves intactes",
          a.is_alive and 0.0 < a.feuillage < 1.0 and a.reserves == r0
          and a.symptom_marks.get("grele", 0.0) > 0.0, f"feuillage {a.feuillage:.2f}")
    check("semis touché (ancienne voie)", s.vitalite < 1.0, f"vit {s.vitalite:.2f}")
    perte_1 = 1.0 - a.feuillage
    eng, tile, eco, (a, s) = lab(Basil, Basil)
    adulte(a)
    _grele(eng, tile, eco, 4.0)
    check("grêle extrême : adulte défolié mais pas tué ; semis tué",
          a.is_alive and a.feuillage == 0.0 and not s.is_alive)
    eng, tile, eco, (a,) = lab(Basil)
    adulte(a)
    _grele(eng, tile, eco, 0.5)
    check("graduée : grêle moitié moins forte, perte moitié moindre",
          abs((1.0 - a.feuillage) - perte_1 / 2) < 1e-9, f"{1 - a.feuillage:.3f}")
    eng, tile, eco, (a,) = lab(Basil)
    adulte(a)
    tile.get_rondelle_count = lambda v: 2 if v == "paillage" else 0
    _grele(eng, tile, eco, 1.0)
    check("paillage (2 rondelles) : la moitié du dégât",
          abs((1.0 - a.feuillage) - perte_1 / 2) < 1e-9, f"{1 - a.feuillage:.3f}")


if __name__ == "__main__":
    test_gel()
    test_gel_tissus()
    test_froid()
    test_chaleur()
    test_hiver()
    test_fin_de_cycle()
    test_grele()
    ok = sum(r for _, r in _results)
    print(f"\n{ok}/{len(_results)} OK")
    sys.exit(0 if ok == len(_results) else 1)
