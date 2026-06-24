"""
SYMBIOSE — tests/simserver/conteneurs.py
Section 17 : conteneurs pots/bacs au pont (④, protocole 0.5.7). Snapshot du bloc
`containers` (VIDE à l'init = golden NEUTRE), pose pot/bac par POSITION monde
(Vigueur débitée, conteneur exposé, index = `target.container`), `deplacer_pot`
(change x_cm/y_cm + lumière recalculée ; bac REFUSE sans coût), `planter_conteneur`
(place une plante du banc-graines dans le mini-sol), refus de désignation
(substrat/volume/index/espèce invalides) SANS coût + serveur survivant.
"""
from .harness import check, ServerProc


def test_conteneurs():
    print("\n[17] conteneurs pots/bacs : pose/déplace/plante + snapshot (0.5.7)")
    s = ServerProc()
    # "full" : monde réel (maison → ombre) + banque de départ (planter_conteneur).
    init = s.send(cmd="init", config="full", seed=42)
    check("engine_version 0.5.7", init.get("engine_version") == "0.5.7",
          init.get("engine_version"))
    snap0 = s.send(cmd="snapshot")["snapshot"]
    check("snapshot expose `containers` VIDE à l'init (golden neutre)",
          snap0.get("containers") == [], snap0.get("containers"))

    # --- poser_pot par position monde --------------------------------------
    v_avant = snap0["player"]["vigueur"]
    rp = s.send(cmd="action", verb="poser_pot",
                target={"x_cm": 1000.0, "y_cm": 400.0},
                params={"substrat": "terreau", "volume": 10.0})
    check("poser_pot → applied + coût > 0",
          rp["result"]["applied"] and rp["result"]["cost"] > 0.0)
    check("Vigueur débitée par poser_pot",
          rp["result"]["vigueur"] < v_avant, (v_avant, rp["result"]["vigueur"]))
    cont = rp["snapshot"]["containers"]
    check("snapshot expose le pot (kind/substrat/mobile/eco_summary)",
          len(cont) == 1 and cont[0]["kind"] == "pot"
          and cont[0]["substrat"] == "terreau" and cont[0]["mobile"] is True
          and cont[0]["x_cm"] == 1000.0 and "eco_summary" in cont[0], cont)

    # --- poser_bac immobile N×M --------------------------------------------
    rb = s.send(cmd="action", verb="poser_bac_culture",
                target={"x_cm": 800.0, "y_cm": 800.0},
                params={"substrat": "compost", "volume": 200.0,
                        "rows": 2, "cols": 2})
    check("poser_bac_culture → applied", rb["result"]["applied"])
    bac = rb["snapshot"]["containers"][1]
    check("le bac est immobile N×M (mobile false, rows/cols 2, fond_ouvert)",
          bac["kind"] == "bac" and bac["mobile"] is False
          and bac["rows"] == 2 and bac["cols"] == 2
          and bac["fond_ouvert"] is True, bac)

    # --- substrat / volume invalides → refus SANS coût ---------------------
    rbadsub = s.send(cmd="action", verb="poser_pot",
                     target={"x_cm": 0.0, "y_cm": 0.0},
                     params={"substrat": "n_existe_pas", "volume": 5.0})
    check("substrat inconnu → applied false, coût 0 (refus de désignation)",
          rbadsub["result"]["applied"] is False and rbadsub["result"]["cost"] == 0.0)
    rbadvol = s.send(cmd="action", verb="poser_pot",
                     target={"x_cm": 0.0, "y_cm": 0.0},
                     params={"substrat": "terreau", "volume": -5.0})
    check("volume ≤ 0 → applied false sans coût",
          rbadvol["result"]["applied"] is False and rbadvol["result"]["cost"] == 0.0)
    check("toujours 2 conteneurs après refus (rien posé)",
          len(rbadvol["snapshot"]["containers"]) == 2)

    # --- deplacer_pot : position + lumière recalculée ----------------------
    # Le pot #0 est sous l'ombre maison (1000,400). On le déplace au plein soleil
    # (loin) → le snapshot reflète la nouvelle position (la lumière se recalcule au
    # tick — ici on prouve la MOBILITÉ + l'exposition de la position).
    rm = s.send(cmd="action", verb="deplacer_pot",
                target={"container": 0, "x_cm": 2500.0, "y_cm": 2500.0})
    check("deplacer_pot → applied + coût > 0",
          rm["result"]["applied"] and rm["result"]["cost"] > 0.0)
    moved = rm["snapshot"]["containers"][0]
    check("position du pot mise à jour au snapshot",
          moved["x_cm"] == 2500.0 and moved["y_cm"] == 2500.0, moved)

    # --- bac REFUSE le déplacement (immobile, sans coût) -------------------
    rbacmove = s.send(cmd="action", verb="deplacer_pot",
                      target={"container": 1, "x_cm": 50.0, "y_cm": 50.0})
    check("déplacer un bac → applied false, coût 0 (immobile)",
          rbacmove["result"]["applied"] is False
          and rbacmove["result"]["cost"] == 0.0)
    check("la position du bac est INTACTE après refus",
          rbacmove["snapshot"]["containers"][1]["x_cm"] == 800.0)

    # --- index de conteneur invalide → refus -------------------------------
    rbadidx = s.send(cmd="action", verb="deplacer_pot",
                     target={"container": 9, "x_cm": 0.0, "y_cm": 0.0})
    check("container hors liste → applied false (refus)",
          rbadidx["result"]["applied"] is False)

    # --- planter_conteneur : place une plante du banc-graines --------------
    rplant = s.send(cmd="action", verb="planter_conteneur",
                    target={"container": 0}, params={"species": "tomate"})
    check("planter_conteneur (tomate) → applied + coût > 0",
          rplant["result"]["applied"] and rplant["result"]["cost"] > 0.0)
    pot0 = rplant["snapshot"]["containers"][0]
    check("le mini-sol du pot porte la plante au snapshot",
          len(pot0["plants"]) == 1 and pot0["plants"][0]["species"] == "Tomato",
          pot0["plants"])
    # espèce non plantable → refus sans coût
    rbadsp = s.send(cmd="action", verb="planter_conteneur",
                    target={"container": 0}, params={"species": "licorne"})
    check("espèce non plantable → applied false, coût 0",
          rbadsp["result"]["applied"] is False and rbadsp["result"]["cost"] == 0.0)

    # --- serveur survivant après tous ces refus ----------------------------
    rsurv = s.send(cmd="snapshot")
    check("serveur survit à tous les refus (snapshot encore ok)", rsurv["ok"])
    s.send(cmd="quit")
    check("quit conteneurs → exit 0", s.close() == 0)
