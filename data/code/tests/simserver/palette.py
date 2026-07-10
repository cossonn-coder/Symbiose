"""
SYMBIOSE — tests/simserver/palette.py
Section 21 : palette de gestes ⑤ au pont (protocole 0.5.26). Deux contrats :
  · EXPO snapshot — le bloc `player` porte `palette` = {slots, macros} de l'avatar,
    et le banc « palette_gestes » ouvre d'emblée les gestes savants (bouturer/greffer)
    via son hook post-init.
  · PERSISTANCE — la commande `palette` écrit le layout curé + les macros envoyés par
    la vue, en VALIDANT la cohérence de cible des macros (refus en bloc, transaction).
    Le contrat métier de la validation est couvert par `tests/test_palette.py` ; ici
    on vérifie le ROUTAGE (commande reconnue, écriture reflétée au snapshot suivant).
"""
from .harness import check, ServerProc


def test_palette_pont():
    print("[palette de gestes au pont]")
    s = ServerProc()
    # Le banc « palette_gestes » ouvre bouturer/greffer via son hook post-init.
    s.send(cmd="init", config="palette_gestes")
    snap = s.send(cmd="snapshot")["snapshot"]
    pl = snap["player"]

    check("le bloc player porte `palette`", "palette" in pl, sorted(pl.keys()))
    check("palette par défaut = slots+macros vides",
          pl["palette"] == {"slots": [], "macros": []}, str(pl["palette"]))
    check("banc ouvre bouturer", "bouturer" in pl["gestes_debloques"])
    check("banc ouvre greffer", "greffer" in pl["gestes_debloques"])

    # Persistance d'un layout COHÉRENT (slots curés + macro mono-famille « plot »).
    r = s.send(cmd="palette", slots=["planter", "arroser", "pailler"],
               macros=[{"nom": "trou",
                        "sequence": ["planter", "pailler", "arroser"]}])
    check("persist layout cohérent → ok", r["ok"] is True, str(r.get("error")))
    check("réponse reflète le layout écrit",
          r.get("palette", {}).get("slots") == ["planter", "arroser", "pailler"])

    # Le snapshot suivant expose le layout persisté.
    snap = s.send(cmd="snapshot")["snapshot"]
    check("snapshot suivant porte les slots persistés",
          snap["player"]["palette"]["slots"] == ["planter", "arroser", "pailler"])
    check("snapshot suivant porte la macro persistée",
          snap["player"]["palette"]["macros"]
          == [{"nom": "trou", "sequence": ["planter", "pailler", "arroser"]}])

    # Macro INCOHÉRENTE (plot + plante) → refus en bloc, rien n'écrase l'existant.
    r = s.send(cmd="palette",
               macros=[{"nom": "x", "sequence": ["planter", "recolter"]}])
    check("macro incohérente → ok:false + message", r["ok"] is False,
          str(r.get("error")))
    snap = s.send(cmd="snapshot")["snapshot"]
    check("macro cohérente PRÉCÉDENTE intacte après le refus",
          snap["player"]["palette"]["macros"]
          == [{"nom": "trou", "sequence": ["planter", "pailler", "arroser"]}])

    s.send(cmd="quit")
