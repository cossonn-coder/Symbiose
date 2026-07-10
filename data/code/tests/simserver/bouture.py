"""
SYMBIOSE — tests/simserver/bouture.py
Section 19 : bouturer au pont (protocole 0.5.24). Geste à 2 TEMPS côté VUE
(mémoire des 2 clics dans Godot) : un seul appel `action verb=bouturer` porte la
MÈRE par position continue (`target.x_cm`/`y_cm`) ET le plot cible par
`params.r`/`params.c`. Le serveur est STATELESS ; la façade `sim.actions.bouturer`
fait foi. On vérifie ici le ROUTAGE et les REFUS de désignation (sans coût) — le
contrat métier du geste (clone, stress mère, tout-ou-rien) est couvert par
`tests/test_bouture.py`. Déterminisme byte-à-byte du refus.
"""
from .harness import check, ServerProc


def test_bouture_pont():
    print("[bouturer au pont]")
    s = ServerProc()
    s.send(cmd="init", seed=42)

    # Fait avancer le smoke jusqu'à ce qu'une plante VIVANTE existe (n'importe
    # laquelle : le smoke ne sème AUCUNE espèce bouturable → toute mère du monde
    # refuse le geste, ce qui exerce exactement le gate `bouturable`).
    proie = None
    for _ in range(20):
        snap = s.send(cmd="step_week")["snapshot"]
        proie = next((p for p in snap["plants"]), None)
        if proie:
            break
    check("une plante vivante existe (mère candidate)", proie is not None,
          proie and f"{proie['species']} (semaine {snap['week']})")
    pos = {"tile": proie["tile"], "x_cm": proie["x_cm"], "y_cm": proie["y_cm"]}
    vig0 = s.send(cmd="snapshot")["snapshot"]["player"]["vigueur"]

    # Refus de désignation (aucun ne coûte de Vigueur) :
    # a) tuile introuvable.
    r = s.send(cmd="action", verb="bouturer",
               target={"tile": "TZZ", "x_cm": 0.0, "y_cm": 0.0},
               params={"r": 1, "c": 1})
    check("tuile introuvable → applied:false", r["result"]["applied"] is False)
    # b) aucune plante à la position.
    r = s.send(cmd="action", verb="bouturer",
               target={"tile": proie["tile"], "x_cm": 99999.0, "y_cm": 0.0},
               params={"r": 1, "c": 1})
    check("mère introuvable → applied:false", r["result"]["applied"] is False,
          r["result"]["message"])
    # c) plot cible hors tuile (mère valide, mais r/c hors bornes).
    r = s.send(cmd="action", verb="bouturer", target=pos,
               params={"r": 999, "c": 999})
    check("plot cible hors tuile → applied:false", r["result"]["applied"] is False,
          r["result"]["message"])
    # d) mère non bouturable (aucune espèce du smoke ne l'est) → gate d'espèce.
    r = s.send(cmd="action", verb="bouturer", target=pos, params={"r": 1, "c": 1})
    check("mère non bouturable → applied:false + message clair",
          r["result"]["applied"] is False
          and "ne se bouture pas" in r["result"]["message"],
          r["result"]["message"])

    # Aucun de ces refus n'a coûté de Vigueur (validé serveur, façade jamais payée).
    vig1 = s.send(cmd="snapshot")["snapshot"]["player"]["vigueur"]
    check("aucun refus de bouturer n'a coûté de Vigueur", vig1 == vig0,
          f"{vig0} → {vig1}")
