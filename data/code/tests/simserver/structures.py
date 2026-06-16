"""
SYMBIOSE — tests/simserver/structures.py
Section 13 : structures posables (⑤, protocole 0.3.5). poser/composter/retourner/
epandre + exposition au snapshot (`eco.structures`). Index de structure invalide
ou kind incohérent → refus de désignation propre (ne coûte rien, pas de crash).
"""
from .harness import check, ServerProc


def test_structures():
    print("\n[13] structures posables : poser/composter/retourner/epandre + snapshot")
    s13 = ServerProc()
    init13 = s13.send(cmd="init", seed=42)
    check("engine_version 0.3.6", init13.get("engine_version") == "0.3.6",
          init13.get("engine_version"))
    rb = s13.send(cmd="action", verb="poser_bac",
                  target={"tile": "T0", "r": 1, "c": 1})
    check("poser_bac → applied", rb["result"]["applied"])
    st = rb["snapshot"]["structures"]["T0"]
    check("snapshot expose le bac (kind/plot/compost_mur)",
          len(st) == 1 and st[0]["kind"] == "bac" and st[0]["plot"] == [1, 1]
          and st[0]["compost_mur"] == 0.0)
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
