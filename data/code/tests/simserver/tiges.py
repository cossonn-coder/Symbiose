"""
SYMBIOSE — tests/simserver/tiges.py
Section 26 : tiges d'herbacée au sol (LISIBILITÉ DU BILAN ③, protocole 0.6.23).

Scène : banc `plante_vivante`, les trois poivrons au pied du mur nord (tuile OMBRE,
rangée 7) meurent de faim à l'ombre. Leur nécromasse tombe en parcelle `herbace` sur
leur plot ; le pont l'expose (index 9-10 de `litiere` : masse, âge propres) et la vue
la couche en tiges paille. Puis le geste EXISTANT `composter` (aucun geste neuf) la
ramasse vers un bac posé sur la tuile : la masse `herbace` du plot tombe à zéro.
"""
from .harness import check, ServerProc

TUILE, RANG, COLS = "OMBRE", 7, (2, 4, 6)


def _herbace(snap, c):
    """(masse, âge) de la parcelle `herbace` du plot (RANG, c) de OMBRE, ou (0, 0)."""
    for e in snap["litiere"].get(TUILE, []):
        if e[0] == RANG and e[1] == c:
            return e[9], e[10]
    return 0.0, 0.0


def _poivrons(snap):
    return [p for p in snap["plants"] if p["tile"] == TUILE
            and p["species"] == "Pepper" and not p.get("dead", False)]


def test_tiges_herbace():
    print("\n[26] tiges d'herbacée au sol + composter (0.6.23)")
    s = ServerProc()
    s.send(cmd="init", config="plante_vivante", seed=42, vigueur_infinie=True)
    snap = s.send(cmd="snapshot")["snapshot"]
    check("au départ : trois poivrons vivants à l'ombre", len(_poivrons(snap)) == 3,
          len(_poivrons(snap)))
    for _ in range(20):                    # mort mesurée en s17-s19 (départ s12) [seed 42]
        snap = s.send(cmd="step_week")["snapshot"]
        if not _poivrons(snap):
            break
    check("les poivrons de l'ombre meurent de faim", not _poivrons(snap), snap["week"])
    masses = [_herbace(snap, c) for c in COLS]
    check("leurs plots portent une litière `herbace` (masse > 0, âge ≥ 0)",
          all(m > 0.0 and a >= 0.0 for m, a in masses), masses)

    rb = s.send(cmd="action", verb="poser_bac", target={"tile": TUILE, "r": 1, "c": 1})
    check("poser_bac sur la tuile OMBRE → applied", rb["result"]["applied"], rb["result"])
    rc = s.send(cmd="action", verb="composter",
                target={"tile": TUILE, "r": RANG, "c": COLS[0], "structure": 0})
    check("composter sur le plot d'un poivron mort → applied",
          rc["result"]["applied"], rc["result"])
    apres = _herbace(rc["snapshot"], COLS[0])[0]
    check("la litière `herbace` du plot est ramassée (masse 0)", apres == 0.0, apres)
    check("les plots voisins non ramassés gardent leurs tiges",
          _herbace(rc["snapshot"], COLS[1])[0] > 0.0, _herbace(rc["snapshot"], COLS[1]))
    s.send(cmd="quit")
