"""
SYMBIOSE — tests/simserver/delta.py
Section 23 : pont EN DELTA (FLUIDITÉ PC LEVIERS ④, protocole 0.6.0).

Deux serveurs, même graine, MÊMES commandes : l'un en format complet (référence),
l'autre en delta (`"delta": true`). Un client miroir (ce fichier) applique les
deltas exactement comme `core/PontDelta.cs` ; à chaque réponse, les plantes
reconstruites doivent être ÉGALES au snapshot complet (segments, âges, gènes, et
tous les autres champs). Le scénario passe par une taille au segment (liste
réindexée), un déracinement (plante disparue), une resynchro `complet` et des
semaines ordinaires. Le reste du snapshot (hors plantes / bloc delta) est identique.
"""
from .harness import check, ServerProc

_SEG_PLANTE = ("pid", "segd", "segments", "genes")


class ClientMiroir:
    """Miroir Python du `PontDelta` C# : pid → (charges, gènes)."""

    def __init__(self):
        self.etat = {}
        self.erreurs = []

    def appliquer(self, snap: dict) -> list:
        bloc = snap["delta"]
        if bloc["complet"]:
            self.etat = {}
        semaine = snap["week"]
        plantes = []
        for p in snap["plants"]:
            anc_charges, genes = self.etat.get(p["pid"], ([], None))
            if "genes" in p:
                genes = p["genes"]
            neuves, j = [], 0
            for op in p["segd"]:
                if isinstance(op, list):
                    neuves.append(tuple(op))
                elif op > 0:
                    if j + op > len(anc_charges):
                        self.erreurs.append(f"pid {p['pid']} recopie hors bornes")
                    neuves.extend(anc_charges[j:j + op])
                    j += op
                else:
                    j -= op
            self.etat[p["pid"]] = (neuves, genes)
            q = {k: v for k, v in p.items() if k not in _SEG_PLANTE}
            q["segments"] = [
                {"parent": c[0], "base": [c[1], c[2], c[3]], "dir": [c[4], c[5], c[6]],
                 "length_cm": c[7], "thickness_cm": c[8], "age_weeks": semaine - c[10],
                 "is_apex": bool(c[9])} for c in neuves]
            if genes is not None and not p.get("dead"):
                q["genes"] = genes
            plantes.append(q)
        for pid in bloc["disparues"]:
            self.etat.pop(pid, None)
        return plantes


def _comparer(nom, plein, delta, miroir, stats):
    """Plantes reconstruites == snapshot complet ; reste du snapshot identique."""
    reconstruites = miroir.appliquer(delta)
    ok = reconstruites == plein["plants"] and not miroir.erreurs
    reste_p = {k: v for k, v in plein.items() if k not in ("plants", "perf")}
    reste_d = {k: v for k, v in delta.items() if k not in ("plants", "perf", "delta")}
    stats["n"] += 1
    stats["ok"] += ok and reste_p == reste_d
    stats["disparues"] += len(delta["delta"]["disparues"])
    if not ok and stats["premier_ko"] is None:
        stats["premier_ko"] = nom


def test_delta_pont():
    print("[pont en delta (0.6.0)]")
    ref, dlt = ServerProc(), ServerProc()
    miroir = ClientMiroir()
    stats = {"n": 0, "ok": 0, "disparues": 0, "premier_ko": None}

    def deux(nom, **msg):
        r = ref.send(**msg)
        d = dlt.send(delta=msg.pop("_mode", True), **msg)
        _comparer(nom, r["snapshot"], d["snapshot"], miroir, stats)
        return r, d

    ref.send(cmd="init", seed=42)
    init = dlt.send(cmd="init", seed=42)
    check("engine_version 0.6.9", init.get("engine_version") == "0.6.9",
          init.get("engine_version"))
    # Opt-in : SANS la clé, le serveur delta répond au format complet historique.
    brut = dlt.send(cmd="snapshot")["snapshot"]
    check("sans `delta` : snapshot complet (segments, pas de pid ni de bloc delta)",
          "delta" not in brut and all("segments" in p and "pid" not in p
                                      for p in brut["plants"]))
    r, d = deux("snapshot initial", cmd="snapshot")
    check("1er snapshot delta = complet", d["snapshot"]["delta"]["complet"] is True)

    proie = None
    for w in range(30):
        r, d = deux(f"step {w}", cmd="step_week")
        proie = next((p for p in r["snapshot"]["plants"]
                      if len(p["segments"]) >= 3 and not p.get("dead")), None)
        if proie:
            break
    check("une plante à ≥ 3 segments pour la taille", proie is not None)
    pos = {"tile": proie["tile"], "x_cm": proie["x_cm"], "y_cm": proie["y_cm"]}
    vise = next(i for i, sg in enumerate(proie["segments"]) if sg["parent"] is not None)
    r, d = deux("taille", cmd="action", verb="tailler", target={**pos, "segment": vise})
    check("taille au segment appliquée (liste réindexée)", r["result"]["applied"])
    for w in range(3):
        deux(f"après taille {w}", cmd="step_week")
    autre = next(p for p in r["snapshot"]["plants"]
                 if not p.get("dead") and (p["x_cm"], p["y_cm"]) != (pos["x_cm"], pos["y_cm"]))
    n_disp = stats["disparues"]
    r, d = deux("déracinement", cmd="action", verb="deraciner",
                target={"tile": autre["tile"], "x_cm": autre["x_cm"], "y_cm": autre["y_cm"]})
    deux("après déracinement", cmd="step_week")   # l'herbacée morte part au tick
    check("déracinement → la plante figure dans `disparues`",
          r["result"]["applied"] and stats["disparues"] > n_disp)
    r, d = deux("resynchro", cmd="snapshot", _mode="complet")
    check("`delta: complet` → snapshot marqué complet (resynchro)",
          d["snapshot"]["delta"]["complet"] is True)
    for w in range(20):
        r, d = deux(f"semaines {w}", cmd="step_week")
    check("semaines suivantes : delta non complet",
          d["snapshot"]["delta"]["complet"] is False)
    check(f"reconstruction == snapshot complet sur {stats['n']} réponses",
          stats["ok"] == stats["n"], f"1er écart : {stats['premier_ko']}")
    plein_o = len(str(r["snapshot"]["plants"]))
    delta_o = len(str(d["snapshot"]["plants"]))
    check("le delta allège les plantes", delta_o < plein_o,
          f"{plein_o} → {delta_o} caractères (repr) en semaine {r['snapshot']['week']}")
    for s in (ref, dlt):
        s.send(cmd="quit")
    check("quit delta → exit 0", ref.close() == 0 and dlt.close() == 0)
