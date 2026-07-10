"""
SYMBIOSE — tests/simserver/greffe.py
Section 20 : greffer au pont (protocole 0.5.25). Geste à 2 TEMPS côté VUE
(mémoire des 2 clics dans Godot) : un seul appel `action verb=greffer` porte le
PORTE-GREFFE par position continue (`target.x_cm`/`y_cm`) ET le GREFFON par
`params.scion_x_cm`/`scion_y_cm` (1er clic, même tuile). Le serveur est STATELESS ;
la façade `sim.actions.greffer` fait foi. On vérifie ici le ROUTAGE et les REFUS de
désignation (sans coût) — le contrat métier du geste (recomposition D8, greffon
consommé, tout-ou-rien) est couvert par `tests/test_greffe.py`. Déterminisme du refus.
"""
from .harness import check, ServerProc


def test_greffe_pont():
    print("[greffer au pont]")
    s = ServerProc()
    s.send(cmd="init", seed=42)

    # Fait avancer le smoke jusqu'à ce qu'une plante VIVANTE existe (n'importe
    # laquelle : le smoke ne sème AUCUNE espèce greffable → tout porte-greffe du
    # monde refuse le geste, ce qui exerce exactement le gate `greffable`/famille).
    proie = None
    for _ in range(20):
        snap = s.send(cmd="step_week")["snapshot"]
        proie = next((p for p in snap["plants"]), None)
        if proie:
            break
    check("une plante vivante existe (porte-greffe candidat)", proie is not None,
          proie and f"{proie['species']} (semaine {snap['week']})")
    pos = {"tile": proie["tile"], "x_cm": proie["x_cm"], "y_cm": proie["y_cm"]}
    vig0 = s.send(cmd="snapshot")["snapshot"]["player"]["vigueur"]

    # Refus de désignation (aucun ne coûte de Vigueur) :
    # a) tuile introuvable.
    r = s.send(cmd="action", verb="greffer",
               target={"tile": "TZZ", "x_cm": 0.0, "y_cm": 0.0},
               params={"scion_x_cm": 0.0, "scion_y_cm": 0.0})
    check("tuile introuvable → applied:false", r["result"]["applied"] is False)
    # b) porte-greffe introuvable à la position.
    r = s.send(cmd="action", verb="greffer",
               target={"tile": proie["tile"], "x_cm": 99999.0, "y_cm": 0.0},
               params={"scion_x_cm": proie["x_cm"], "scion_y_cm": proie["y_cm"]})
    check("porte-greffe introuvable → applied:false", r["result"]["applied"] is False,
          r["result"]["message"])
    # c) greffon introuvable (porte-greffe valide, scion hors plante).
    r = s.send(cmd="action", verb="greffer", target=pos,
               params={"scion_x_cm": 99999.0, "scion_y_cm": 0.0})
    check("greffon introuvable → applied:false", r["result"]["applied"] is False,
          r["result"]["message"])
    # d) greffon == porte-greffe (même plante désignée deux fois) → refus explicite.
    r = s.send(cmd="action", verb="greffer", target=pos,
               params={"scion_x_cm": proie["x_cm"], "scion_y_cm": proie["y_cm"]})
    check("même plante deux fois → applied:false + message clair",
          r["result"]["applied"] is False
          and "même plante" in r["result"]["message"],
          r["result"]["message"])

    # Aucun de ces refus n'a coûté de Vigueur (validé serveur, façade jamais payée).
    vig1 = s.send(cmd="snapshot")["snapshot"]["player"]["vigueur"]
    check("aucun refus de greffer n'a coûté de Vigueur", vig1 == vig0,
          f"{vig0} → {vig1}")
