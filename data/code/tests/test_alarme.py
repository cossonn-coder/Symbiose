"""
SYMBIOSE — tests/test_alarme.py
Tronçon ⑦ (arc pollinisation) — piqûre / alarme émergente (§J, couche joueur).

§J FIGÉ : la piqûre n'est pas un malus forfaitaire, mais une RÉACTION ÉMERGENTE.
Une action directe coûteuse — ÉCRASER une abeille ou RÉCOLTER du miel SANS
équipement — pose une phéromone d'alarme LOCALE (`eco.alarme`) qui décroît au tick.
La piqûre proprement dite (coût Vigueur au curseur, atténuation par l'équipement)
est temps réel CÔTÉ GODOT (§J.3) ; ce module ne teste que la PART MOTEUR : le dépôt
du signal, sa décroissance, sa neutralité et son déterminisme.

Vérifications :
  A. DÉCLENCHEUR ÉCRASER — écraser une ABEILLE pose l'alarme au plot ; écraser un
     non-pollinisateur (ravageur) n'en pose AUCUNE (§J.1, la phéromone est apienne).
  B. DÉCLENCHEUR RÉCOLTE — `recolter_miel` SANS équipement pose l'alarme au plot de
     la ruche ; AVEC équipement (palier maîtrise) → aucune alarme (l'enfumoir calme).
  C. DÉCROISSANCE — `tick_alarme` fait décroître chaque foyer (× ALARME_DECAY) et le
     SNAPPE à 0 sous ALARME_FLOOR (la liste snapshot reste creuse).
  D. NEUTRALITÉ — sans aucun déclencheur, l'alarme reste à 0 et `tick_alarme` n'écrit
     rien (PUR PUITS, jamais réinjecté dans un champ figé → golden §J.4).
  E. DÉTERMINISME — deux runs identiques → même état (zéro RNG).

Lancement (depuis data/code/) :
  python3 -m tests.test_alarme
"""
import sys

from world import Tile
from fields import init_eco
from fields.alarme import (tick_alarme, declencher_alarme,
                           ALARME_DEPOT, ALARME_DECAY, ALARME_FLOOR)
from sim import actions as ACT
from sim import vigueur as V
from sim import maitrise as M

ROWS, COLS = 6, 8
RR, CC = 3, 4    # plot de l'action (abeille écrasée / ruche)

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'OK ' if cond else 'XX '} {name}" + (f" — {detail}" if detail else ""))


def _eco():
    tile = Tile(tile_id="TA", soil_type="terre")
    eco = init_eco("TA", ROWS, COLS, humidite=1.5, fertilite=1.0, microbiome=0.3)
    return tile, eco


def _gs(courante=None):
    gs = {"current_player": "joueur_1", "week": 1, "log": []}
    V.ensure_player(gs, "joueur_1")
    if courante is not None:
        gs["vigueur"]["joueur_1"]["courante"] = courante
    return gs


def _equiper(gs):
    """Force le palier de maîtrise pollinisation au seuil d'équipement (§I.3)."""
    st = M.ensure_player_maitrise(gs, "joueur_1")
    st["objets"][ACT.CONCEPT_ABEILLES] = {"palier": ACT.SEUIL_EQUIPEMENT, "preuves": 0}


def _somme(eco):
    return sum(eco.alarme.data[r][c] for r in range(ROWS) for c in range(COLS))


# ---------------------------------------------------------------------------
def test_ecraser():
    print("\n[A] écraser une abeille pose l'alarme ; un ravageur n'en pose pas")
    tile, eco = _eco()
    gs = _gs()
    eco.populations["abeille"].fill(0.6)
    ok = ACT.ecraser(gs, "joueur_1", eco, RR, CC, guilde="abeille")
    check("écraser abeille appliqué", ok)
    check("alarme posée au plot écrasé", eco.alarme.data[RR][CC] == ALARME_DEPOT,
          f"{eco.alarme.data[RR][CC]:.3f}")
    check("alarme strictement LOCALE (ailleurs 0)", _somme(eco) == ALARME_DEPOT)
    # Écraser un NON-pollinisateur : aucune phéromone apienne.
    tile2, eco2 = _eco()
    gs2 = _gs()
    eco2.populations["ravageur"].fill(0.6)
    ACT.ecraser(gs2, "joueur_1", eco2, RR, CC, guilde="ravageur")
    check("écraser un ravageur → AUCUNE alarme (§J.1)", _somme(eco2) == 0.0)


def test_recolte():
    print("\n[B] recolter_miel : sans équipement → alarme ; avec → aucune")
    tile, eco = _eco()
    gs = _gs()
    ruche = ACT.poser_ruche(gs, "joueur_1", eco, RR, CC)
    ruche.miel = 5.0
    g = ACT.recolter_miel(gs, "joueur_1", ruche, eco)
    check("récolte nue → gain partiel", g > 0.0, f"{g:.2f}")
    check("récolte SANS équipement → alarme au plot ruche",
          eco.alarme.data[RR][CC] == ALARME_DEPOT, f"{eco.alarme.data[RR][CC]:.3f}")
    # AVEC équipement : l'enfumoir calme → aucune alarme.
    tile2, eco2 = _eco()
    gs2 = _gs()
    _equiper(gs2)
    ruche2 = ACT.poser_ruche(gs2, "joueur_1", eco2, RR, CC)
    ruche2.miel = 5.0
    ACT.recolter_miel(gs2, "joueur_1", ruche2, eco2)
    check("récolte AVEC équipement → AUCUNE alarme (§I.3)", _somme(eco2) == 0.0)
    # eco absent (appel de test legacy) : récolte OK, pas de signal (dégradation gracieuse).
    tile3, eco3 = _eco()
    gs3 = _gs()
    ruche3 = ACT.poser_ruche(gs3, "joueur_1", eco3, RR, CC)
    ruche3.miel = 5.0
    g3 = ACT.recolter_miel(gs3, "joueur_1", ruche3)        # sans eco
    check("récolte sans eco → fonctionne, aucun signal posé", g3 > 0.0 and _somme(eco3) == 0.0)


def test_decroissance():
    print("\n[C] tick_alarme : décroissance géométrique + snap à 0 sous le plancher")
    tile, eco = _eco()
    declencher_alarme(eco, RR, CC, ALARME_DEPOT)
    serie = [eco.alarme.data[RR][CC]]
    for _ in range(10):
        tick_alarme(eco)
        serie.append(eco.alarme.data[RR][CC])
    check("1er tick = × ALARME_DECAY", abs(serie[1] - ALARME_DEPOT * ALARME_DECAY) < 1e-9,
          f"{serie[1]:.4f}")
    check("monotone décroissante", all(serie[i + 1] <= serie[i] for i in range(len(serie) - 1)))
    check("s'éteint à 0 (snap sous ALARME_FLOOR)", serie[-1] == 0.0,
          f"plancher={ALARME_FLOOR}, fin={serie[-1]}")
    # Dépôts cumulatifs bornés [0,1].
    declencher_alarme(eco, 0, 0, ALARME_DEPOT)
    declencher_alarme(eco, 0, 0, ALARME_DEPOT)
    check("dépôts cumulés bornés ≤ 1", eco.alarme.data[0][0] <= 1.0, f"{eco.alarme.data[0][0]:.3f}")


def test_neutralite():
    print("\n[D] neutralité : sans déclencheur, alarme 0 et tick_alarme n'écrit rien")
    tile, eco = _eco()
    check("alarme nulle au repos", _somme(eco) == 0.0)
    for _ in range(5):
        tick_alarme(eco)
    check("tick_alarme sur champ vide reste 0 (PUR PUITS, golden §J.4)", _somme(eco) == 0.0)
    # Hors tuile / intensité nulle → no-op.
    declencher_alarme(eco, -1, 0, ALARME_DEPOT)
    declencher_alarme(eco, RR, CC, 0.0)
    check("dépôt hors tuile / intensité nulle → no-op", _somme(eco) == 0.0)


def test_determinisme():
    print("\n[E] déterminisme : deux runs identiques → même champ d'alarme")
    def run():
        tile, eco = _eco()
        gs = _gs()
        eco.populations["abeille"].fill(0.6)
        ACT.ecraser(gs, "joueur_1", eco, RR, CC, guilde="abeille")
        for _ in range(4):
            tick_alarme(eco)
        return round(eco.alarme.data[RR][CC], 9), round(_somme(eco), 9)
    a, b = run(), run()
    check("deux runs → alarme identique", a == b, f"{a} vs {b}")


def main():
    test_ecraser()
    test_recolte()
    test_decroissance()
    test_neutralite()
    test_determinisme()
    n_ok = sum(1 for _, ok in _results if ok)
    n = len(_results)
    print(f"\n[alarme] {n_ok}/{n} OK")
    sys.exit(0 if n_ok == n else 1)


if __name__ == "__main__":
    main()
