"""
SYMBIOSE — tests/simserver/structures.py
Section 13 : structures posables (⑤, protocole 0.3.5→0.3.8). poser/composter/
retourner/epandre + exposition au snapshot (`eco.structures`). Index de structure
invalide ou kind incohérent → refus de désignation propre (ne coûte rien, pas de
crash). Section 13b (0.3.8) : le bac SE REMPLIT (`contenu`) en compostant la
litière d'un AUTRE plot — la base du correctif F5 (clic litière → bac proche).
"""
from constants import PLOT_CM
from .harness import check, ServerProc


def test_structures():
    print("\n[13] structures posables : poser/composter/retourner/epandre + snapshot")
    s13 = ServerProc()
    init13 = s13.send(cmd="init", seed=42)
    check("engine_version 0.6.1", init13.get("engine_version") == "0.6.1",
          init13.get("engine_version"))
    rb = s13.send(cmd="action", verb="poser_bac",
                  target={"tile": "T0", "r": 1, "c": 1})
    check("poser_bac → applied", rb["result"]["applied"])
    # Bloc `supports` de grimpe présent au snapshot (0.5.18) : keyé par tuile,
    # VIDE tant qu'aucun support n'est posé (le smoke n'en pose aucun → golden NEUTRE).
    sup = rb["snapshot"]["supports"]
    check("snapshot expose le bloc supports (vide au départ)",
          "T0" in sup and sup["T0"] == [], sup)
    st = rb["snapshot"]["structures"]["T0"]
    check("snapshot expose le bac (kind/plot/compost_mur/contenu)",
          len(st) == 1 and st[0]["kind"] == "bac" and st[0]["plot"] == [1, 1]
          and st[0]["compost_mur"] == 0.0 and st[0]["contenu"] == 0.0)
    rp = s13.send(cmd="action", verb="poser_pile",
                  target={"tile": "T0", "r": 2, "c": 2})
    check("poser_pile → applied, 2 structures au snapshot",
          rp["result"]["applied"] and len(rp["snapshot"]["structures"]["T0"]) == 2)
    # Index de structure invalide → refus de désignation (pas de crash, ne coûte rien).
    rbad = s13.send(cmd="action", verb="retourner",
                    target={"tile": "T0", "structure": 9})
    check("structure hors liste → applied false (refus)",
          rbad["result"]["applied"] is False)
    # Cohérence kind/geste : composter sur la PILE (index 1) → refus.
    rmix = s13.send(cmd="action", verb="composter",
                    target={"tile": "T0", "r": 1, "c": 1, "structure": 1})
    check("composter sur une pile → refus de désignation",
          rmix["result"]["applied"] is False)
    rc = s13.send(cmd="action", verb="composter",
                  target={"tile": "T0", "r": 1, "c": 1, "structure": 0})
    check("composter sur le bac (index 0) → applied", rc["result"]["applied"])
    rr = s13.send(cmd="action", verb="retourner",
                  target={"tile": "T0", "structure": 0})
    check("retourner → applied", rr["result"]["applied"])
    # epandre : jauge vide au tick 1 (pas de litière tendre) → refus propre, message lu.
    re = s13.send(cmd="action", verb="epandre",
                  target={"tile": "T0", "r": 0, "c": 0, "structure": 0})
    check("epandre jauge vide → applied false + message",
          re["result"]["applied"] is False and "épand" in re["result"]["message"])
    s13.send(cmd="quit")
    check("quit structures → exit 0", s13.close() == 0)


def test_structure_contenu():
    """13b (0.3.8) — composter une litière déposée sur un AUTRE plot que le bac :
    le bac se remplit (`contenu` > 0) immédiatement, AVANT toute maturation
    (`compost_mur` reste 0), et la litière du plot source est ramassée. C'est le
    socle du correctif F5 : le geste prend (r,c) = plot de litière, indépendant du
    plot du bac (la vue route le clic-litière vers le bac le plus proche)."""
    print("\n[13b] remplissage du bac : composter une litière d'un autre plot (0.3.8)")
    s = ServerProc()
    s.send(cmd="init", seed=42)
    snap0 = s.send(cmd="snapshot")["snapshot"]
    tree = next(p for p in snap0["plants"]
                if p["species"] == "AppleTree" and not p.get("dead", False))
    tile = tree["tile"]
    lr, lc = int(tree["y_cm"] // PLOT_CM), int(tree["x_cm"] // PLOT_CM)   # plot de litière (source)
    # Déraciner le pommier → litière `feuille` (tendre) sur son plot-foyer (lr,lc).
    s.send(cmd="action", verb="deraciner",
           target={"tile": tile, "x_cm": tree["x_cm"], "y_cm": tree["y_cm"]})
    # Poser le bac sur un plot DIFFÉRENT du plot de litière (prouve l'indépendance).
    br, bc = (0, 0) if (lr, lc) != (0, 0) else (1, 1)
    s.send(cmd="action", verb="poser_bac", target={"tile": tile, "r": br, "c": bc})
    snapA = s.send(cmd="snapshot")["snapshot"]
    bac0 = snapA["structures"][tile][0]
    check("bac posé vide (contenu == 0)", bac0["contenu"] == 0.0, bac0)

    # Composter : target = plot de LITIÈRE (lr,lc) + index du bac (0). Le bac est
    # ailleurs (br,bc) → on vérifie que le geste puise bien la litière distante.
    rc = s.send(cmd="action", verb="composter",
                target={"tile": tile, "r": lr, "c": lc, "structure": 0})
    check("composter (litière distante) → applied", rc["result"]["applied"])
    snapB = s.send(cmd="snapshot")["snapshot"]
    bac1 = snapB["structures"][tile][0]
    check("le bac s'est REMPLI (contenu > 0)", bac1["contenu"] > 0.0, bac1["contenu"])
    check("compost_mur encore 0 (pas de maturation sans step)",
          bac1["compost_mur"] == 0.0, bac1["compost_mur"])
    lit = snapB["litiere"][tile]
    check("la litière du plot source est ramassée (plus à l'écran)",
          all(not (e[0] == lr and e[1] == lc) for e in lit), lit)

    s.send(cmd="quit")
    check("quit contenu → exit 0", s.close() == 0)
