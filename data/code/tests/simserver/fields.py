"""
SYMBIOSE — tests/simserver/fields.py
Section 11 : champs debug (tranche 6·C). Commande `fields` HORS snapshot :
registre découvert par introspection (12 GridField d'EcoFields + 4 guildes),
grilles par tuile row-major, guilde interrogeable aussi, champ inconnu → ok:false
AVEC serveur survivant, avant init → ok:false, lecture pure.
"""
from .harness import check, ServerProc


def test_champs_debug():
    print("[champs debug]")
    GUILDES = {"ravageur", "auxiliaire", "pollinisateur", "vers_de_terre"}
    s11 = ServerProc()
    r = s11.send(cmd="fields")
    check("fields avant init → ok:false", r.get("ok") is False)
    rw = s11.send(cmd="init", seed=42)
    r = s11.send(cmd="fields")
    noms = r.get("fields", [])
    check("registre : champs du sol présents",
          {"microbiome", "humidite", "fertilite", "lumiere",
           "temperature", "disturbance"} <= set(noms),
          f"n={len(noms)}")
    check("registre : les 4 guildes présentes", GUILDES <= set(noms))
    check("registre : aucun doublon", len(noms) == len(set(noms)))

    rows_cols = {t["id"]: (t["rows"], t["cols"]) for t in rw["world"]["tiles"]}
    for nom in ("microbiome", "ravageur"):   # un champ direct + une guilde
        r = s11.send(cmd="fields", field=nom)
        ok_grille = r.get("ok") is True and r.get("field") == nom
        for tid, (trows, tcols) in rows_cols.items():
            g = r.get("tiles", {}).get(tid, {})
            ok_grille &= (g.get("rows") == trows and g.get("cols") == tcols
                          and len(g.get("values", [])) == trows * tcols
                          and all(isinstance(v, (int, float))
                                  for v in g.get("values", [])))
        check(f"grille {nom} : par tuile, row-major, dimensions exactes",
              ok_grille)
    r = s11.send(cmd="fields", field="le_flux_vital")
    check("champ inconnu → ok:false", r.get("ok") is False)
    check("le serveur survit (fields répond encore)",
          s11.send(cmd="fields").get("ok") is True)
    # Lecture pure : interroger ne modifie rien (ni champ, ni RNG).
    s11.send(cmd="step_week")
    a_f = s11.send(cmd="fields", field="humidite")
    b_f = s11.send(cmd="fields", field="humidite")
    check("2 lectures sans step → identiques (instrument, pas une règle)",
          a_f == b_f)
    s11.send(cmd="quit")
    check("quit champs debug → exit 0", s11.close() == 0)
