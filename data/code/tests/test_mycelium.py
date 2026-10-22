"""
SYMBIOSE — tests/test_mycelium.py
Tests ciblés du tronçon ① du sprint mycélium & interconnexions : le champ scalaire
`mycelium` (`EcoFields.mycelium`) + sa dynamique pure `tick_mycelium` (croissance sur
le bois humide tempéré, déclin au sec / substrat épuisé, bornage [0,1], déterminisme).

Tronçon FONDATION : le champ existe et tique, mais AUCUN rôle §2 n'est branché
(saprophyte/mycorhize/faune) → le golden ÉCOLOGIQUE reste l'autorité du déterminisme,
ici on exerce uniquement la dynamique propre du champ, hors golden.

Usage (depuis data/code/) :
  python3 -m tests.test_mycelium
"""
import sys

from fields import init_eco
from fields.ecofields import MYCEL_SUBSTRAT_REF, MYCEL_TEMP_OPT

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK " if cond else "XX "
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


# --- A. Champ présent + NUL à l'init ---
eco0 = init_eco("nul", 2, 2)
check("champ mycelium déclaré", eco0.mycelium is not None)
check("get_field('mycelium') == champ", eco0.get_field("mycelium") is eco0.mycelium)
check("mycelium nul partout à l'init",
      all(eco0.mycelium.data[r][c] == 0.0 for r in range(2) for c in range(2)))


def _tick_n(eco, n):
    for _ in range(n):
        eco.tick_mycelium()


# --- B. Croissance sur un plot jouet (bois + humide + tempéré → MONTE) ---
eco = init_eco("pousse", 1, 1, humidite=2.4)         # humide (sur [0,3])
eco.temperature_sol.set(0, 0, MYCEL_TEMP_OPT)        # plein régime thermique
eco.deposer_litiere(0, 0, "bois", MYCEL_SUBSTRAT_REF)  # substrat saturé en bois
before = eco.mycelium.data[0][0]
_tick_n(eco, 5)
after = eco.mycelium.data[0][0]
check("mycelium MONTE en conditions favorables (bois+humide+tempéré)",
      after > before, detail=f"{before:.4f} → {after:.4f}")


# --- C. Déclin (sec + sans bois → REDESCEND) ---
eco_sec = init_eco("sec", 1, 1, humidite=0.1)        # quasi sec
eco_sec.temperature_sol.set(0, 0, MYCEL_TEMP_OPT)
eco_sec.mycelium.set(0, 0, 0.8)                      # réseau préexistant à dégrader
top = eco_sec.mycelium.data[0][0]
_tick_n(eco_sec, 5)
low = eco_sec.mycelium.data[0][0]
check("mycelium REDESCEND au sec sans substrat", low < top,
      detail=f"{top:.4f} → {low:.4f}")


# --- D. Bornage [0,1] ---
eco_max = init_eco("max", 1, 1, humidite=3.0)
eco_max.temperature_sol.set(0, 0, MYCEL_TEMP_OPT)
eco_max.deposer_litiere(0, 0, "bois", 10.0)          # substrat largement saturé
eco_max.mycelium.set(0, 0, 0.99)
_tick_n(eco_max, 200)
check("mycelium plafonne à 1.0 (jamais > max_val)",
      eco_max.mycelium.data[0][0] <= 1.0,
      detail=f"{eco_max.mycelium.data[0][0]:.6f}")
eco_floor = init_eco("floor", 1, 1, humidite=0.0)
eco_floor.mycelium.set(0, 0, 0.01)
_tick_n(eco_floor, 200)
check("mycelium plancher à 0.0 (jamais < 0)",
      eco_floor.mycelium.data[0][0] >= 0.0,
      detail=f"{eco_floor.mycelium.data[0][0]:.6f}")


# --- E. Déterminisme (h1 == h2 sur deux runs identiques) ---
def _run():
    e = init_eco("det", 2, 2, humidite=2.0)
    for r in range(2):
        for c in range(2):
            e.temperature_sol.set(r, c, MYCEL_TEMP_OPT - 2.0 * (r + c))
            e.deposer_litiere(r, c, "bois", 1.5 + 0.3 * (r + c))
    _tick_n(e, 8)
    return tuple(e.mycelium.data[r][c] for r in range(2) for c in range(2))


check("déterminisme : deux runs identiques → état identique", _run() == _run())


# --- F. Repos NEUTRE : sans bois ni mycélium, le champ reste à 0 ---
eco_neutre = init_eco("repos", 1, 1, humidite=2.0)
eco_neutre.temperature_sol.set(0, 0, MYCEL_TEMP_OPT)
_tick_n(eco_neutre, 20)
check("repos sans substrat ni réseau préexistant → reste 0",
      eco_neutre.mycelium.data[0][0] == 0.0,
      detail=f"{eco_neutre.mycelium.data[0][0]:.6f}")


# --- G. SAPROPHYTE (②) : à mycélium FORT, une parcelle `bois` décompose plus
#        vite qu'à mycélium NUL (même état initial). ---
def _bois_restant(mycel_init, ticks=3):
    e = init_eco("sapro", 1, 1, humidite=2.0)
    e.temperature_sol.set(0, 0, MYCEL_TEMP_OPT)
    e.deposer_litiere(0, 0, "bois", 1.0)
    e.mycelium.set(0, 0, mycel_init)
    for _ in range(ticks):
        # fige le mycélium à sa consigne (on isole le TERME saprophyte de la
        # dynamique de croissance) : on ne tique QUE la décompo.
        e.mycelium.set(0, 0, mycel_init)
        e.tick_decomposition()
    return sum(p.masse for p in e.litiere[0][0] if p.tissu == "bois")


bois_nul  = _bois_restant(0.0)
bois_fort = _bois_restant(1.0)
check("SAPROPHYTE : bois décompose PLUS vite sous mycélium fort",
      bois_fort < bois_nul, detail=f"nul={bois_nul:.5f} > fort={bois_fort:.5f}")

# --- H. Non-régression : mycélium NUL ⇒ décompo `bois` strictement INCHANGÉE.
#        (On reconstruit la décompo `bois` sans aucun mycélium déclaré n'est pas
#        possible — le champ existe ① — mais mycelium=0 ⇒ facteur ×1.0 exact.) ---
e_ref = init_eco("ref", 1, 1, humidite=2.0)
e_ref.temperature_sol.set(0, 0, MYCEL_TEMP_OPT)
e_ref.deposer_litiere(0, 0, "bois", 1.0)
# masse attendue après 1 tick SANS mycélium = masse·decay·speed retiré.
m0 = next(p.masse for p in e_ref.litiere[0][0] if p.tissu == "bois")
e_ref.mycelium.set(0, 0, 0.0)
e_ref.tick_decomposition()
m1 = next(p.masse for p in e_ref.litiere[0][0] if p.tissu == "bois")
check("non-régression : mycélium nul ⇒ bois décompose (facteur ×1.0, pas figé)",
      m1 < m0, detail=f"{m0:.5f} → {m1:.5f}")

# --- I. LIANT : sous un réseau présent, `om_stable` MONTE lentement. ---
e_liant = init_eco("liant", 1, 1, humidite=2.0)
e_liant.temperature_sol.set(0, 0, MYCEL_TEMP_OPT)
e_liant.deposer_litiere(0, 0, "bois", MYCEL_SUBSTRAT_REF)
e_liant.mycelium.set(0, 0, 0.8)
om_before = e_liant.om_stable.data[0][0]
for _ in range(5):
    e_liant.tick_mycelium()
om_after = e_liant.om_stable.data[0][0]
check("LIANT : om_stable monte lentement sous un réseau",
      om_after > om_before, detail=f"{om_before:.6f} → {om_after:.6f}")

# --- J. Déterminisme du ② (décompo + liant, deux runs identiques) ---
def _run2():
    e = init_eco("det2", 2, 2, humidite=2.0)
    for r in range(2):
        for c in range(2):
            e.temperature_sol.set(r, c, MYCEL_TEMP_OPT - 2.0 * (r + c))
            e.deposer_litiere(r, c, "bois", 1.0 + 0.2 * (r + c))
            e.mycelium.set(r, c, 0.5 + 0.1 * (r + c))
    for _ in range(4):
        e.tick_mycelium()
        e.tick_decomposition()
    return tuple(e.om_stable.data[r][c] for r in range(2) for c in range(2))


check("déterminisme ② : deux runs identiques → état identique", _run2() == _run2())


# --- K. MYCORHIZE (③) : sous un réseau, l'uptake de P MONTE (P SEULEMENT) ----
#        Empreinte = plot-foyer ; pH fixé à l'optimum P (6.5) pour isoler le boost
#        mycorhizien de la fenêtre pH ; stock de nutriments généreux pour rester
#        SOUS le plafond Liebig (on teste le FLUX, pas le bornage par stock).
def _uptake(mycel_init, p_stock=3.0, stage=2):
    e = init_eco("myco", 1, 1, humidite=2.0, microbiome=0.0, fertilite=p_stock)
    e.ph.set(0, 0, 6.5)                 # optimum P → dispo(ph,"P") ≈ 1.0, non confondant
    e.mycelium.set(0, 0, mycel_init)
    return e.plant_uptake(0, 0, stage)


up_nul  = _uptake(0.0)
up_fort = _uptake(1.0)
check("MYCORHIZE : P prélevé PLUS GRAND sous mycélium fort",
      up_fort.get("p", 0.0) > up_nul.get("p", 0.0),
      detail=f"nul={up_nul.get('p', 0.0):.5f} < fort={up_fort.get('p', 0.0):.5f}")
check("MYCORHIZE : N STRICTEMENT inchangé par le mycélium",
      up_fort.get("n", 0.0) == up_nul.get("n", 0.0),
      detail=f"nul={up_nul.get('n', 0.0):.5f} == fort={up_fort.get('n', 0.0):.5f}")
check("MYCORHIZE : K STRICTEMENT inchangé par le mycélium",
      up_fort.get("k", 0.0) == up_nul.get("k", 0.0),
      detail=f"nul={up_nul.get('k', 0.0):.5f} == fort={up_fort.get('k', 0.0):.5f}")

# Bornage par stock (Liebig) : sol QUASI vide en P → même un réseau saturé ne peut
# prélever plus que le stock (pas de miracle). On compare le P prélevé au stock.
up_pauvre = _uptake(1.0, p_stock=0.0001)
check("MYCORHIZE : bornage Liebig — sol pauvre en P ⇒ pas de miracle",
      up_pauvre.get("p", 0.0) <= 0.0001 + 1e-9,
      detail=f"p_prélevé={up_pauvre.get('p', 0.0):.6f} ≤ stock 0.0001")

# Non-régression : mycélium NUL ⇒ uptake bit-identique à un EcoFields sans réseau.
# (Le champ existe depuis ① ; mycelium=0 ⇒ facteur ×1.0 EXACT sur P.)
check("MYCORHIZE : mycélium nul ⇒ P prélevé = repos (facteur ×1.0)",
      up_nul.get("p", 0.0) > 0.0, detail=f"p={up_nul.get('p', 0.0):.5f} (uptake normal)")

# Déterminisme du ③ (deux uptakes identiques → résultat identique).
check("déterminisme ③ : deux uptakes identiques → identique", _uptake(0.7) == _uptake(0.7))


# --- L. FAUNE FONGIVORE (④) : sous un réseau, le détritivore du sol (lombric)
#        gonfle vs mycélium NUL (terme additif `_mycelium_signal`). ----
from world import Tile
from fields import POP_MAX


def _lombric_apres_tick(mycel_init):
    """Densité `lombric` au plot (3,4) après UN tick de populations, à mycélium
    figé. On laisse une densité de départ pour exercer la relaxation vers la cible
    (la capacité additive du signal fongivore monte la cible)."""
    e = init_eco("fong", 6, 8, humidite=2.0, fertilite=1.0, microbiome=0.5)
    e.mycelium.fill(mycel_init)               # réseau uniforme
    e.temperature.fill(20.0)                  # chaud → survie non nulle
    e.populations["lombric"].fill(0.2)        # densité de départ
    e.tick_populations(Tile(tile_id="fong", soil_type="terre"), [], week_in_year=25)
    return e.populations["lombric"].at_plot(3, 4)


fong_nul  = _lombric_apres_tick(0.0)
fong_fort = _lombric_apres_tick(1.0)
check("FAUNE FONGIVORE : lombric MONTE sous un réseau dense",
      fong_fort > fong_nul, detail=f"nul={fong_nul:.5f} < fort={fong_fort:.5f}")
check("FAUNE FONGIVORE : densité bornée par POP_MAX",
      fong_fort <= POP_MAX, detail=f"{fong_fort:.5f} ≤ {POP_MAX}")

# Non-régression : mycélium NUL ⇒ détritivore strictement INCHANGÉ (signal = 0).
e_ref_f = init_eco("fongref", 6, 8, humidite=2.0, fertilite=1.0, microbiome=0.5)
e_ref_f.mycelium.fill(0.0)
e_ref_f.temperature.fill(20.0)
e_ref_f.populations["lombric"].fill(0.2)
e_nomyc = init_eco("nomyc", 6, 8, humidite=2.0, fertilite=1.0, microbiome=0.5)
e_nomyc.temperature.fill(20.0)
e_nomyc.populations["lombric"].fill(0.2)
tile_f = Tile(tile_id="x", soil_type="terre")
e_ref_f.tick_populations(tile_f, [], week_in_year=25)
e_nomyc.tick_populations(tile_f, [], week_in_year=25)
check("FAUNE FONGIVORE : mycélium nul ⇒ lombric = repos (signal ×0)",
      e_ref_f.populations["lombric"].at_plot(3, 4)
      == e_nomyc.populations["lombric"].at_plot(3, 4))


# --- M. CARPOPHORES (④) : perception PURE échantillonnée du champ `mycelium`. ----
from fields import sample_carpophores
from fields.population import (CARPO_MYCEL_MIN, CARPO_HUMIDE_MIN)

# D111 ③ : la fructification suit la PLUIE (pas l'automne seul) et l'espèce vient
# de la niche. Sol riche (om_active) = niche humus du coprin, fenêtre sem. 8-45.
_WIY_AUTOMNE = 30                              # coprin en fenêtre
_WIY_ETE = 50                                  # hors fenêtre du coprin (hiver)
_SEED_C = 0x5AB1057E


def _eco_carpo(mycel, humidite):
    e = init_eco("carpo", 4, 4, humidite=humidite)
    e.mycelium.fill(mycel)
    e.om_active.fill(1.0)                      # humus riche → niche du coprin
    return e


# Réseau dense + sol humide + automne → carpophores PRÉSENTS.
e_dense = _eco_carpo(0.8, 2.5)
carpos = sample_carpophores(e_dense, _SEED_C, _WIY_AUTOMNE, True)
check("CARPOPHORES : présents (réseau dense + humide + automne)",
      len(carpos) > 0, detail=f"{len(carpos)} carpophores")
check("CARPOPHORES : positions ∈ [0,1] (frac dans le plot)",
      all(0.0 <= k.x_frac <= 1.0 and 0.0 <= k.y_frac <= 1.0 for k in carpos))

# Déterminisme : deux échantillonnages du MÊME état → identiques (zéro RNG).
c1 = sample_carpophores(e_dense, _SEED_C, _WIY_AUTOMNE, True)
c2 = sample_carpophores(e_dense, _SEED_C, _WIY_AUTOMNE, True)
check("CARPOPHORES : déterministes (h1 == h2, mêmes positions)",
      [(k.row, k.col, k.slot, k.x_frac, k.y_frac) for k in c1]
      == [(k.row, k.col, k.slot, k.x_frac, k.y_frac) for k in c2])

# Mycélium NUL → liste VIDE (golden/pont neutres).
check("CARPOPHORES : VIDE si mycélium nul",
      sample_carpophores(_eco_carpo(0.0, 2.5), _SEED_C, _WIY_AUTOMNE, True) == [])
# Sous le seuil de densité → VIDE.
check("CARPOPHORES : VIDE si réseau trop ténu (< seuil)",
      sample_carpophores(_eco_carpo(CARPO_MYCEL_MIN - 0.05, 2.5),
                         _SEED_C, _WIY_AUTOMNE, True) == [])
# Sol sec → VIDE (pas de fructification sans pluie).
check("CARPOPHORES : VIDE si sol sec (< seuil humidité)",
      sample_carpophores(_eco_carpo(0.8, CARPO_HUMIDE_MIN - 0.2),
                         _SEED_C, _WIY_AUTOMNE, True) == [])
# Hors fenêtre de l'espèce → VIDE ; pas de pluie la semaine d'avant → VIDE.
check("CARPOPHORES : VIDE hors fenêtre de l'espèce de la niche",
      sample_carpophores(e_dense, _SEED_C, _WIY_ETE, True) == [])
check("CARPOPHORES : VIDE si la semaine précédente n'a pas plu",
      sample_carpophores(e_dense, _SEED_C, _WIY_AUTOMNE, False) == [])
check("CARPOPHORES : espèce de la niche humus = coprin",
      {k.espece for k in carpos} == {"coprin"}, str({k.espece for k in carpos}))

# Indépendance position/semaine : un slot occupe le MÊME point quel que soit
# `week_in_year` (positions par hash de seed/position/slot, pas de la semaine).
e_dense2 = _eco_carpo(0.8, 2.5)
pos_a = {(k.row, k.col, k.slot): (k.x_frac, k.y_frac)
         for k in sample_carpophores(e_dense2, _SEED_C, _WIY_AUTOMNE, True)}
pos_b = {(k.row, k.col, k.slot): (k.x_frac, k.y_frac)
         for k in sample_carpophores(e_dense2, _SEED_C, 40, True)}
check("CARPOPHORES : positions indépendantes de la semaine (slot stable)",
      pos_a == pos_b)


# --- N. BÊCHAGE EVENT-DRIVEN (⑤ §1.2) : `becher` casse le réseau (retire un quantum
#        `mycelium`), `grelinette` le PRÉSERVE (ne le touche pas). Miroir EXACT des
#        autres malus de `becher` ; jamais via le champ `disturbance`. ----
from sim import actions as ACT
from sim import vigueur as V
from fields.ecofields import BECHAGE_MYCELIUM_MALUS


def _gs_plein():
    gs = {"current_player": "joueur_1", "week": 1, "log": []}
    V.ensure_player(gs, "joueur_1")
    return gs


# Bêcher RETIRE BECHAGE_MYCELIUM_MALUS au plot bêché (réseau préexistant 0.7).
e_b = init_eco("becher", 3, 3)
e_b.mycelium.set(1, 1, 0.7)
ACT.becher(_gs_plein(), "joueur_1", e_b, 1, 1)
check("BÊCHAGE : `becher` RETIRE un quantum de mycélium au plot",
      abs(e_b.mycelium.at_plot(1, 1) - (0.7 - BECHAGE_MYCELIUM_MALUS)) < 1e-9,
      f"{e_b.mycelium.at_plot(1, 1):.4f}")
check("BÊCHAGE : `becher` ne touche QUE le plot ciblé (voisin intact)",
      e_b.mycelium.at_plot(0, 0) == 0.0)

# Bêcher sur réseau NUL → clampé à 0, pas de plantage (piège kickoff).
e_b0 = init_eco("becher0", 2, 2)
ok_nul = ACT.becher(_gs_plein(), "joueur_1", e_b0, 0, 0)
check("BÊCHAGE : `becher` sur mycélium nul → 0 (clampé, ne plante pas)",
      ok_nul and e_b0.mycelium.at_plot(0, 0) == 0.0)

# Grelinette PRÉSERVE le réseau (ne touche pas `mycelium`).
e_g = init_eco("grelinette", 3, 3)
e_g.mycelium.set(1, 1, 0.7)
ACT.grelinette(_gs_plein(), "joueur_1", e_g, 1, 1)
check("BÊCHAGE : `grelinette` PRÉSERVE le mycélium (réseau intact)",
      e_g.mycelium.at_plot(1, 1) == 0.7,
      f"{e_g.mycelium.at_plot(1, 1):.4f}")


# --- Bilan ---
fails = [n for n, ok in _results if not ok]
if fails:
    print(f"\n[test_mycelium] FAIL — {len(fails)}/{len(_results)} rouges : {fails}")
    sys.exit(1)
print(f"\n[test_mycelium] PASS — {len(_results)}/{len(_results)} OK")
