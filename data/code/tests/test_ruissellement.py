"""
SYMBIOSE — tests/test_ruissellement.py
Tests ciblés du RUISSELLEMENT latéral de la lame d'eau de surface (sprint
hydrologie & marécages ②). Exercent `EcoFields.tick_ruissellement` hors golden,
sur des topographies `altitude` forcées à la main.

Couvre :
  1. Conservation de masse : dans une CUVETTE (bords hauts, aucun exutoire) et
     sol saturé (aucune infiltration), la masse totale de la lame ne varie que
     de l'évaporation de surface (× (1−EVAP_SURFACE)). Rien ne se crée/se perd
     latéralement — ce qui sort d'un plot entre chez ses voisins.
  2. Déterminisme au balayage : la redistribution lit un DOUBLE BUFFER → le
     résultat est indépendant de l'ordre de parcours (invariant par transposition
     d'une topographie symétrique).
  3. Cuvette accumule : sur une pente régulière, l'eau MIGRE vers le point bas
     (le creux se gorge, la bosse s'assèche) au fil des ticks.
  4. Repos NEUTRE : `eau_surface` nulle partout → tick no-op (golden neutre).
  5. Anti-emballement (proxy « 500 ans ») : sur une pente arrosée en continu à
     saturation, la lame se STABILISE et reste bornée [0, HUM_CAP] sur un long
     run (aucune divergence numérique, aucun NaN).

Usage (depuis data/code/) :
  python3 -m tests.test_ruissellement
"""
import sys

from fields import EcoFields
from fields.ecofields.constants import HUM_CAP, SEUIL_FLAQUE, EVAP_SURFACE

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK " if cond else "XX "
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _eco(rows=5, cols=5, hum=1.0):
    """Un EcoFields nu (construction directe : altitude plate, eau_surface nulle,
    aucun tick de fond). On force ensuite `altitude`, `humidite`, `eau_surface`
    plot à plot pour isoler la mécanique d'écoulement."""
    eco = EcoFields(tile_id="T0", rows=rows, cols=cols)
    eco.humidite.fill(hum)
    eco.structure_sol.fill(1.0)   # sol grumeleux → infiltration maximale quand testée
    return eco


def _total(eco):
    return sum(v for row in eco.eau_surface.data for v in row)


# ---------------------------------------------------------------------------
# 1. Conservation de masse latérale (cuvette fermée, sol saturé)
# ---------------------------------------------------------------------------
def test_conservation_masse():
    print("\n[1] conservation de masse : eau interne à une cuvette + sol saturé → seule l'évaporation retire")
    eco = _eco(rows=7, cols=7, hum=HUM_CAP)     # sol saturé → AUCUNE infiltration
    # Altitude en CUVETTE : bords hauts, centre bas → l'eau converge vers le CENTRE.
    # ⚠️ Un plot de BORD écoule vers l'extérieur (exutoire du monde) → pour isoler la
    # SEULE conservation latérale, on ne dépose la lame que sur les plots INTÉRIEURS,
    # et en un seul tick elle converge vers le bas SANS atteindre l'anneau de bord.
    for r in range(eco.rows):
        for c in range(eco.cols):
            bord = min(r, c, eco.rows - 1 - r, eco.cols - 1 - c)
            eco.altitude.set(r, c, 40.0 - 10.0 * bord)   # 40 au bord, 10 au centre
    for r in range(1, eco.rows - 1):
        for c in range(1, eco.cols - 1):
            eco.eau_surface.set(r, c, 0.5)
    avant = _total(eco)
    eco.tick_ruissellement()
    apres = _total(eco)
    attendu = avant * (1.0 - EVAP_SURFACE)      # sol saturé → seule l'évaporation ôte
    # La lame n'a pas atteint l'anneau de bord en 1 tick → aucune fuite à l'exutoire.
    ring = sum(eco.eau_surface.data[r][c]
               for r in range(eco.rows) for c in range(eco.cols)
               if r in (0, eco.rows - 1) or c in (0, eco.cols - 1))
    check("l'eau n'a pas atteint le bord (aucun exutoire touché en 1 tick)", ring == 0.0,
          f"ring={ring:.6f}")
    check("aucune fuite latérale : masse = masse initiale × (1−EVAP_SURFACE)",
          abs(apres - attendu) < 1e-9, f"avant={avant:.4f} après={apres:.4f} attendu={attendu:.4f}")


# ---------------------------------------------------------------------------
# 2. Déterminisme au balayage (double buffer) — symétrie par transposition
# ---------------------------------------------------------------------------
def test_determinisme_double_buffer():
    print("\n[2] déterminisme : résultat indépendant de l'ordre de balayage (topo symétrique)")
    # Topographie SYMÉTRIQUE par transposition (alt[r][c] == alt[c][r]) + lame
    # symétrique → si le balayage introduisait un biais directionnel, la symétrie
    # serait cassée. Sol saturé pour isoler l'écoulement (infiltration nulle).
    eco = _eco(hum=HUM_CAP)
    for r in range(eco.rows):
        for c in range(eco.cols):
            eco.altitude.set(r, c, 10.0 * (r + c))      # symétrique en (r,c)
            eco.eau_surface.set(r, c, 1.0)
    eco.tick_ruissellement()
    symetrique = all(
        abs(eco.eau_surface.data[r][c] - eco.eau_surface.data[c][r]) < 1e-12
        for r in range(eco.rows) for c in range(eco.cols))
    check("lame résiduelle symétrique par transposition (aucun biais d'ordre)", symetrique)


# ---------------------------------------------------------------------------
# 3. Cuvette accumule : l'eau migre vers le point bas
# ---------------------------------------------------------------------------
def test_cuvette_accumule():
    print("\n[3] une cuvette accumule : l'eau migre vers le creux INTÉRIEUR, la bosse s'assèche")
    eco = _eco(rows=7, cols=7, hum=HUM_CAP)     # saturé → l'eau ne fait que ruisseler
    # Cuvette conique à minimum INTÉRIEUR (r=c=3) : altitude ∝ distance de Manhattan
    # au centre → le point bas ne touche aucun bord (il ACCUMULE au lieu de fuir).
    cr, cc = 3, 3
    for r in range(eco.rows):
        for c in range(eco.cols):
            d = abs(r - cr) + abs(c - cc)
            eco.altitude.set(r, c, 10.0 * d)    # 0 au centre, monte vers les bords
            eco.eau_surface.set(r, c, 0.4)      # lame uniforme au départ
    bosse = (0, 0)                              # coin haut
    for _ in range(20):
        eco.tick_ruissellement()
    lame_creux = eco.eau_surface.at_plot(cr, cc)
    lame_bosse = eco.eau_surface.at_plot(*bosse)
    # La bosse se draine vers ~0 (elle donne, ne reçoit rien) ; le creux RETIENT une
    # flaque durable (il reçoit toute la pente, l'écoulement s'annule au point bas).
    check("la bosse s'est ASSÉCHÉE (lame → 0)", lame_bosse < 1e-3,
          f"bosse={lame_bosse:.5f}")
    check("le creux RETIENT bien plus que la bosse", lame_creux > lame_bosse,
          f"creux={lame_creux:.3f} bosse={lame_bosse:.5f}")
    check("flaque durable perçue au creux (lame > SEUIL_FLAQUE)", lame_creux > SEUIL_FLAQUE,
          f"lame_creux={lame_creux:.3f} seuil={SEUIL_FLAQUE}")


# ---------------------------------------------------------------------------
# 4. Repos NEUTRE : lame nulle → tick no-op
# ---------------------------------------------------------------------------
def test_repos_neutre():
    print("\n[4] repos NEUTRE : eau_surface nulle → tick sans effet (golden neutre)")
    eco = _eco(hum=1.2)
    for r in range(eco.rows):
        for c in range(eco.cols):
            eco.altitude.set(r, c, 40.0 - 4.0 * (r + c))   # relief présent…
    hum_avant = [row[:] for row in eco.humidite.data]
    eco.tick_ruissellement()
    check("lame reste nulle partout", _total(eco) == 0.0)
    check("humidité INTACTE (aucune infiltration sans lame)",
          eco.humidite.data == hum_avant)


# ---------------------------------------------------------------------------
# 4b. Infiltration : un sol NON saturé boit la lame (∝ structure)
# ---------------------------------------------------------------------------
def test_infiltration():
    print("\n[4b] infiltration : un sol non saturé boit la lame → humidité ↑, lame ↓")
    eco = _eco(rows=3, cols=3, hum=1.0)         # sol loin de la saturation → il peut boire
    eco.altitude.fill(20.0)                     # PLAT → aucun ruissellement, on isole l'infiltration
    eco.eau_surface.set(1, 1, 1.0)              # une flaque au centre
    hum0 = eco.humidite.at_plot(1, 1)
    lame0 = eco.eau_surface.at_plot(1, 1)
    eco.tick_ruissellement()
    check("humidité du plot montée (le sol a bu une part de la flaque)",
          eco.humidite.at_plot(1, 1) > hum0, f"hum {hum0:.3f} → {eco.humidite.at_plot(1, 1):.3f}")
    check("lame résiduelle réduite (infiltration + évaporation)",
          eco.eau_surface.at_plot(1, 1) < lame0, f"lame {lame0:.3f} → {eco.eau_surface.at_plot(1, 1):.3f}")


# ---------------------------------------------------------------------------
# 5. Anti-emballement sur un long run (proxy « 500 ans »)
# ---------------------------------------------------------------------------
def test_anti_emballement():
    print("\n[5] anti-emballement : arrosage continu à saturation → lame BORNÉE, stable")
    eco = _eco(hum=1.0)
    for r in range(eco.rows):
        for c in range(eco.cols):
            eco.altitude.set(r, c, 40.0 - 4.0 * (r + c))
    # 2000 ticks (~40 ans à 52 sem/an, largement au-delà d'un régime permanent),
    # avec réinjection d'une lame en tête de pente chaque tick (source amont).
    lame_max = 0.0
    for _ in range(2000):
        eco.eau_surface.add(0, 0, 0.3)          # source amont continue
        eco.tick_ruissellement()
        for row in eco.eau_surface.data:
            for v in row:
                lame_max = max(lame_max, v)
    total = _total(eco)
    borne_ok = all(0.0 <= v <= HUM_CAP + 1e-9
                   for row in eco.eau_surface.data for v in row)
    fini = total == total and total != float("inf")   # pas de NaN / inf
    check("lame toujours bornée [0, HUM_CAP] (aucune divergence)", borne_ok,
          f"lame_max={lame_max:.3f} cap={HUM_CAP}")
    check("total fini (aucun NaN/inf après 2000 ticks)", fini, f"total={total:.3f}")


def main():
    test_conservation_masse()
    test_determinisme_double_buffer()
    test_cuvette_accumule()
    test_repos_neutre()
    test_infiltration()
    test_anti_emballement()
    n_ok = sum(1 for _, ok in _results if ok)
    n = len(_results)
    print(f"\n[test_ruissellement] {n_ok}/{n} OK")
    if n_ok != n:
        echecs = [name for name, ok in _results if not ok]
        print("ÉCHECS : " + ", ".join(echecs))
        sys.exit(1)
    print("[test_ruissellement] PASS")


if __name__ == "__main__":
    main()
