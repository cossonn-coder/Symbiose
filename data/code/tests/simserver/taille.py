"""
SYMBIOSE — tests/simserver/taille.py
Section 8 : taille au segment (tranche 5) — `tailler` avec `target.segment`
explicite, le snapshot JOINT perd exactement le sous-arbre ciblé ; refus de
désignation sans coût ; repli params.cible (t4) intact.
Section 8b : écraser une PLANTE (volet 2, protocole 0.3.2) — routage sur la FORME
du target (Q6), effet émergent, collet valide, déterminisme byte-à-byte.
"""
from .harness import check, ServerProc


def test_taille_au_segment():
    # --- 8. taille au segment (tranche 5) ------------------------------------
    print("[taille au segment]")
    s7 = ServerProc()
    s7.send(cmd="init", seed=42)
    # Avancer jusqu'à une plante à ≥ 3 segments (assez de bois pour qu'un
    # sous-arbre ciblé se distingue du tout). Borné : le smoke en produit vite.
    proie = None
    for _ in range(30):
        snap = s7.send(cmd="step_week")["snapshot"]
        proie = next((p for p in snap["plants"] if len(p["segments"]) >= 3), None)
        if proie:
            break
    check("une plante à ≥ 3 segments existe", proie is not None,
          proie and f"{proie['species']}, {len(proie['segments'])} segments "
                    f"(semaine {snap['week']})")
    segs = proie["segments"]
    pos = {"tile": proie["tile"], "x_cm": proie["x_cm"], "y_cm": proie["y_cm"]}

    def meme_plante(snapshot):
        return next((p for p in snapshot["plants"]
                     if p["tile"] == pos["tile"] and p["x_cm"] == pos["x_cm"]
                     and p["y_cm"] == pos["y_cm"]), None)

    # Refus de désignation = ne coûte RIEN (validé serveur, façade jamais payée).
    vig0 = s7.send(cmd="snapshot")["snapshot"]["player"]["vigueur"]
    r = s7.send(cmd="action", verb="tailler", target={**pos, "segment": 999})
    check("segment hors bornes → applied:false", r["result"]["applied"] is False)
    r = s7.send(cmd="action", verb="tailler", target={**pos, "segment": 0})
    check("collet (segment 0) → applied:false (protégé)",
          r["result"]["applied"] is False, r["result"]["message"])
    r = s7.send(cmd="action", verb="tailler", target={**pos, "segment": "apex"})
    check("segment non entier → applied:false", r["result"]["applied"] is False)
    check("aucun de ces refus n'a coûté de Vigueur",
          r["result"]["vigueur"] == vig0, f"vigueur={r['result']['vigueur']}")

    # Sous-arbre attendu du segment visé = 1er enfant du collet (calcul TEST,
    # via les champs `parent` du snapshot — les parents précèdent toujours
    # leurs enfants dans structure_to_dict, un passage avant suffit).
    vise = next(i for i, sg in enumerate(segs) if sg["parent"] is not None)
    dans_sous_arbre = [False] * len(segs)
    dans_sous_arbre[vise] = True
    for i, sg in enumerate(segs):
        if sg["parent"] is not None and dans_sous_arbre[sg["parent"]]:
            dans_sous_arbre[i] = True
    n_coupe = sum(dans_sous_arbre)

    r = s7.send(cmd="action", verb="tailler", target={**pos, "segment": vise})
    check("tailler un segment explicite → applied:true",
          r["result"]["applied"] is True, r["result"]["message"])
    check("le message nomme le segment",
          f"segment {vise}" in r["result"]["message"])
    apres = meme_plante(r["snapshot"])
    check("le snapshot JOINT perd exactement le sous-arbre ciblé",
          apres is not None
          and len(apres["segments"]) == len(segs) - n_coupe,
          f"{len(segs)} − {n_coupe} → "
          f"{apres and len(apres['segments'])} segments")

    # Repli t4 intact : tailler SANS segment passe toujours par params.cible.
    r = s7.send(cmd="action", verb="tailler", target=pos,
                params={"cible": "apex"})
    check("repli params.cible (sans segment) → applied:true (compat t4)",
          r["result"]["applied"] is True, r["result"]["message"])
    check("le serveur survit (snapshot répond encore)",
          s7.send(cmd="snapshot").get("ok") is True)
    s7.send(cmd="quit")
    check("quit taille → exit 0", s7.close() == 0)

    # --- 8b. écraser une PLANTE (écraser·volet 2, protocole 0.3.2) ------------
    # Routage sur la FORME du target (Q6) : `ecraser` avec x_cm/y_cm (sans guilde)
    # vise la plante, pas une guilde animale. Effet ÉMERGENT (déformée/écimée/meurt).
    print("[écraser une plante (volet 2)]")
    s8 = ServerProc()
    s8.send(cmd="init", seed=42)
    proie = None
    for _ in range(30):
        snap = s8.send(cmd="step_week")["snapshot"]
        proie = next((p for p in snap["plants"] if len(p["segments"]) >= 2), None)
        if proie:
            break
    check("une plante à ≥ 2 segments existe", proie is not None,
          proie and f"{proie['species']}, {len(proie['segments'])} segments")
    pos = {"tile": proie["tile"], "x_cm": proie["x_cm"], "y_cm": proie["y_cm"]}
    vig0 = s8.send(cmd="snapshot")["snapshot"]["player"]["vigueur"]
    # Écraser par POSITION (ni guilde ni r/c) → routé PLANTE, coût = tailler (MODÉRÉ).
    r = s8.send(cmd="action", verb="ecraser", target=pos)
    msg = r["result"]["message"]
    check("écraser par position → routé plante (applied:true)",
          r["result"]["applied"] is True, msg)
    check("message nomme la plante + issue émergente (déformée/écimée/meurt)",
          ("déformée" in msg or "écimée" in msg or "meurt" in msg), msg)
    check("coût = base tailler (MODÉRÉ) débité",
          vig0 - r["result"]["vigueur"] == 15.0, f"Δvigueur={vig0 - r['result']['vigueur']}")
    # Le collet (segment 0) est une cible VALIDE pour écraser (≠ tailler qui le refuse).
    r = s8.send(cmd="action", verb="ecraser", target={**pos, "segment": 0})
    check("écraser le collet (segment 0) → applied:true (cible valide, Q2)",
          r["result"]["applied"] is True, r["result"]["message"])
    # Refus de désignation (segment hors bornes) → ne coûte rien.
    vig1 = s8.send(cmd="snapshot")["snapshot"]["player"]["vigueur"]
    r = s8.send(cmd="action", verb="ecraser", target={**pos, "segment": 999})
    check("segment hors bornes → applied:false sans coût",
          r["result"]["applied"] is False and r["result"]["vigueur"] == vig1,
          r["result"]["message"])
    # La guilde animale reste routée par r/c+guilde (non-régression du volet 1).
    r = s8.send(cmd="action", verb="ecraser",
                target={"tile": "T0", "r": 0, "c": 0, "guilde": "puceron"})
    check("écraser une guilde par r/c → toujours routé guilde (volet 1 intact)",
          r["result"]["applied"] is True and "puceron" in r["result"]["message"],
          r["result"]["message"])
    s8.send(cmd="quit")
    check("quit écraser-plante → exit 0", s8.close() == 0)

    # Déterminisme byte-à-byte de l'écrasement d'une plante (pas de RNG).
    def run_ecraser_plante(seed):
        s = ServerProc()
        s.send(cmd="init", seed=seed)
        snap = None
        for _ in range(30):
            snap = s.send(cmd="step_week")["snapshot"]
            if any(len(p["segments"]) >= 2 for p in snap["plants"]):
                break
        p = next(p for p in snap["plants"] if len(p["segments"]) >= 2)
        s.send(cmd="action", verb="ecraser",
               target={"tile": p["tile"], "x_cm": p["x_cm"], "y_cm": p["y_cm"]})
        s.send(cmd="snapshot")
        s.send(cmd="quit")
        return s
    a8, b8 = run_ecraser_plante(42), run_ecraser_plante(42)
    a8.close(); b8.close()
    check("2 runs écraser-plante même seed → byte-identiques",
          a8.raw_lines == b8.raw_lines)
