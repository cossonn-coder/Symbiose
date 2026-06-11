"""
SYMBIOSE — tests/test_sim_server.py
Golden du PONT (sprint Intégration Godot ↔ Python, tranche 1).

Lance tools/sim_server.py en vrai sous-process (comme Godot le fera) et joue le
protocole v0 par les pipes. Couvre les contrats du kickoff 01_pont_minimal.md :

  1. forme        — init/step_week/snapshot répondent {"ok": true, ...} bien
                    formés, engine_version présent, monde 2 tuiles + maison ;
  2. avancement   — step_week ×4 → week passe de 1 à 5, des plantes vivantes
                    dans le snapshot ;
  3. robustesse   — ligne malformée / cmd inconnue / step avant init →
                    {"ok": false} et le serveur SURVIT (répond encore après) ;
  4. déterminisme — 2 runs même seed → réponses byte-identiques ;
  5. arrêt propre — EOF sur stdin (Godot mort sans quit) → le process meurt ;
  6. monde full   — init(config="full") (tranche 2) : layout 3×3 de main.py
                    (8 tuiles SECTORS, sols variés, origins distincts, maison
                    [600,600]→[1400,1400], 53 plantes), config inconnue refusée ;
  7. actions v1   — (tranche 4) bloc `player` au snapshot, régen + refill de
                    saison via le tick moteur, manger/deraciner par POSITION,
                    URGENCE_MULT visible sur ecraser, refus métier
                    (applied:false) sur verbe inconnu / cible introuvable /
                    Vigueur insuffisante AVEC serveur survivant, déterminisme
                    2 runs avec les MÊMES actions. Le golden écolo, lui, ne
                    passe JAMAIS par ce serveur → intact par construction ;
  8. taille au segment — (tranche 5) `tailler` avec `target.segment` explicite
                    (la branche cliquée) : le snapshot JOINT perd exactement le
                    sous-arbre ciblé ; segment hors bornes / collet / non
                    entier → applied:false SANS coût et le serveur survit ;
                    le repli params.cible (t4) reste intact.

Mesure aussi la taille du snapshot (octets/semaine) — la donnée qui tranchera
« complet vs diffs » (cf. 00_etat.md, pas d'optimisation avant mesure).

Usage (depuis data/code/) :
  python3 -m tests.test_sim_server
"""
import json
import os
import subprocess
import sys

CODE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(CODE_DIR, "tools", "sim_server.py")

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


class ServerProc:
    """Pilote le serveur par les pipes, comme SimBridge.cs le fera côté Godot."""

    def __init__(self):
        self.proc = subprocess.Popen(
            [sys.executable, SERVER], cwd=CODE_DIR,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True)
        self.raw_lines = []          # réponses brutes (pour le déterminisme)

    def send_raw(self, line: str) -> str:
        """Écrit une ligne brute, lit UNE ligne de réponse (protocole 1↔1)."""
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()
        resp = self.proc.stdout.readline().rstrip("\n")
        self.raw_lines.append(resp)
        return resp

    def send(self, **msg) -> dict:
        return json.loads(self.send_raw(json.dumps(msg)))

    def close(self, timeout=10):
        self.proc.stdin.close()
        return self.proc.wait(timeout=timeout)


def run_scenario(seed: int) -> ServerProc:
    """Le scénario nominal : init → step ×4 → snapshot → quit."""
    s = ServerProc()
    s.send(cmd="init", seed=seed)
    for _ in range(4):
        s.send(cmd="step_week")
    s.send(cmd="snapshot")
    s.send(cmd="quit")
    return s


def main() -> int:
    # --- 1+2. forme + avancement -------------------------------------------
    print("[forme + avancement]")
    s = ServerProc()
    r = s.send(cmd="init", seed=42)
    check("init ok", r.get("ok") is True)
    check("engine_version présent", isinstance(r.get("engine_version"), str))
    world = r.get("world", {})
    check("monde smoke : 2 tuiles", len(world.get("tiles", [])) == 2,
          f"tuiles={[t['id'] for t in world.get('tiles', [])]}")
    check("maison présente", "footprint_cm" in world.get("house", {}))

    snap = None
    for _ in range(4):
        r = s.send(cmd="step_week")
        check("step_week ok", r.get("ok") is True)
        snap = r.get("snapshot", {})
    check("semaine avancée (1 → 5)", snap.get("week") == 5,
          f"week={snap.get('week')}")
    # Calendrier moteur : semaines 1-13 = printemps (SAISONS, sim/engine.py).
    check("saison cohérente", snap.get("season") == "printemps",
          f"season={snap.get('season')}")
    check("plantes vivantes dans le snapshot", len(snap.get("plants", [])) > 0,
          f"n={len(snap.get('plants', []))}")
    p0 = snap.get("plants", [{}])[0]
    check("schéma plante v0 complet",
          all(k in p0 for k in ("tile", "species", "x_cm", "y_cm",
                                "stage", "height_cm", "segments")))

    r = s.send(cmd="snapshot")
    check("snapshot == état du dernier step", r.get("snapshot") == snap)

    # Mesure (kickoff : la donnée qui tranchera complet vs diffs)
    size = len(json.dumps(r, sort_keys=True, separators=(",", ":")))
    n_seg = sum(len(p["segments"]) for p in snap["plants"])
    print(f"  📏 taille snapshot semaine 5 : {size} octets "
          f"({len(snap['plants'])} plantes, {n_seg} segments)")

    # --- 3. robustesse -------------------------------------------------------
    print("[robustesse]")
    r = json.loads(s.send_raw("pas du json"))
    check("ligne malformée → ok:false", r.get("ok") is False)
    r = s.send(cmd="nimporte_quoi")
    check("cmd inconnue → ok:false", r.get("ok") is False)
    r = s.send(cmd="snapshot")
    check("le serveur survit (snapshot répond encore)", r.get("ok") is True)
    s.send(cmd="quit")
    check("quit → exit 0", s.close() == 0)

    s2 = ServerProc()
    r = s2.send(cmd="step_week")
    check("step avant init → ok:false", r.get("ok") is False)
    s2.send(cmd="quit")
    s2.close()

    # --- 4. déterminisme ------------------------------------------------------
    print("[déterminisme]")
    a, b = run_scenario(seed=42), run_scenario(seed=42)
    a.close(); b.close()
    check("2 runs même seed → réponses byte-identiques",
          a.raw_lines == b.raw_lines)

    # --- 5. arrêt propre (EOF sans quit) -------------------------------------
    print("[arrêt propre]")
    s3 = ServerProc()
    s3.send(cmd="init", seed=42)
    try:
        code = s3.close(timeout=10)   # ferme stdin SANS quit → EOF
        check("EOF stdin → le serveur meurt", code == 0, f"exit={code}")
    except subprocess.TimeoutExpired:
        s3.proc.kill()
        check("EOF stdin → le serveur meurt", False, "timeout : process zombie")

    # --- 6. monde full (tranche 2) -------------------------------------------
    print("[monde full]")
    s4 = ServerProc()
    r = s4.send(cmd="init", seed=42, config="nimporte_quoi")
    check("config inconnue → ok:false", r.get("ok") is False)
    r = s4.send(cmd="init", seed=42, config="full")
    check("init full ok (le serveur a survécu à la config refusée)",
          r.get("ok") is True)
    world = r.get("world", {})
    tiles = world.get("tiles", [])
    check("monde full : 8 tuiles", len(tiles) == 8,
          f"tuiles={[t['id'] for t in tiles]}")
    check("ids = les 8 orientations",
          {t["id"] for t in tiles} == {"NO", "N", "NE", "O", "E", "SO", "S", "SE"})
    check("3 sols représentés",
          {t["soil"] for t in tiles} == {"terre", "argile", "sable"})
    check("origins tous distincts",
          len({(t["origin_x_cm"], t["origin_y_cm"]) for t in tiles}) == 8)
    check("layout dans le monde 20×20 m",
          all(0 <= t["origin_x_cm"] and 0 <= t["origin_y_cm"]
              and t["origin_x_cm"] + t["cols"] * 50 <= 2000
              and t["origin_y_cm"] + t["rows"] * 50 <= 2000 for t in tiles))
    check("maison 8×8 m centrée",
          world.get("house", {}).get("footprint_cm") == [600, 600, 1400, 1400],
          f"footprint={world.get('house', {}).get('footprint_cm')}")
    r = s4.send(cmd="snapshot")
    snap = r.get("snapshot", {})
    check("53 plantes posées (semaine 1, rien simulé)",
          len(snap.get("plants", [])) == 53, f"n={len(snap.get('plants', []))}")
    # Mesure full (critère kickoff t2 : noter la taille dans 00_etat.md)
    r = s4.send(cmd="step_week")
    size = len(json.dumps(r, sort_keys=True, separators=(",", ":")))
    n_seg = sum(len(p["segments"]) for p in r["snapshot"]["plants"])
    print(f"  📏 taille snapshot full semaine 2 : {size} octets "
          f"({len(r['snapshot']['plants'])} plantes, {n_seg} segments)")
    s4.send(cmd="quit")
    check("quit full → exit 0", s4.close() == 0)

    # --- 7. actions v1 (tranche 4) -------------------------------------------
    print("[actions v1]")
    s5 = ServerProc()
    r = s5.send(cmd="action", verb="grelinette")
    check("action avant init → ok:false", r.get("ok") is False)
    r = s5.send(cmd="init", seed=42)
    check("init (le serveur a survécu à l'action prématurée)", r.get("ok") is True)
    snap = s5.send(cmd="snapshot")["snapshot"]
    check("bloc player présent au snapshot",
          snap.get("player", {}).get("vigueur") == 100.0
          and snap["player"].get("vigueur_max") == 100.0,
          f"player={snap.get('player')}")

    # Refus métier : le geste échoue, le PROTOCOLE réussit (ok:true).
    r = s5.send(cmd="action", verb="trairelavache")
    check("verbe inconnu → ok:true + applied:false",
          r.get("ok") is True and r["result"]["applied"] is False)
    r = s5.send(cmd="action", verb="manger",
                target={"tile": "T0", "x_cm": 999.0, "y_cm": 999.0})
    check("cible introuvable → applied:false",
          r.get("ok") is True and r["result"]["applied"] is False)
    r = s5.send(cmd="action", verb="becher", target={"tile": "T0", "r": 99, "c": 0})
    check("plot hors tuile → applied:false", r["result"]["applied"] is False)
    check("rien de tout ça n'a coûté de Vigueur",
          r["result"]["vigueur"] == 100.0, f"vigueur={r['result']['vigueur']}")

    # Plante par POSITION (l'identité du kickoff §8) : manger puis deraciner.
    for _ in range(4):
        snap = s5.send(cmd="step_week")["snapshot"]
    cible = snap["plants"][0]
    pos = {"tile": cible["tile"], "x_cm": cible["x_cm"], "y_cm": cible["y_cm"]}
    r = s5.send(cmd="action", verb="manger", target=pos)
    check("manger par position → applied:true (coût NUL)",
          r["result"]["applied"] is True and r["result"]["cost"] == 0.0
          and r["result"]["gain"] >= 0.0)
    vig_avant = r["result"]["vigueur"]
    r = s5.send(cmd="action", verb="deraciner", target=pos)
    check("deraciner → applied:true, Vigueur débitée (coût ÉLEVÉ)",
          r["result"]["applied"] is True
          and r["result"]["vigueur"] == vig_avant - 30.0,
          f"vigueur {vig_avant} → {r['result']['vigueur']}")
    disparue = all(not (p["tile"] == pos["tile"] and p["x_cm"] == pos["x_cm"]
                        and p["y_cm"] == pos["y_cm"])
                   for p in r["snapshot"]["plants"])
    check("la plante a disparu du snapshot JOINT (1 aller-retour)", disparue)
    r = s5.send(cmd="action", verb="deraciner", target=pos)
    check("re-deraciner la même position → applied:false (plus personne)",
          r["result"]["applied"] is False)

    # URGENCE_MULT (la couture préparation/réaction §3.1) : 15 vs 22.5.
    v0 = r["result"]["vigueur"]
    r = s5.send(cmd="action", verb="ecraser",
                target={"tile": "T0", "r": 0, "c": 0}, params={"urgence": False})
    cout_calme = v0 - r["result"]["vigueur"]
    v1 = r["result"]["vigueur"]
    r = s5.send(cmd="action", verb="ecraser",
                target={"tile": "T0", "r": 0, "c": 0}, params={"urgence": True})
    cout_urgence = v1 - r["result"]["vigueur"]
    check("ecraser en urgence coûte URGENCE_MULT × le calme",
          cout_calme == 15.0 and cout_urgence == 22.5,
          f"calme={cout_calme}, urgence={cout_urgence}")

    # Vigueur insuffisante : drainer à la grelinette (sans cible) jusqu'au refus.
    refus = None
    for _ in range(8):
        r = s5.send(cmd="action", verb="grelinette")
        if r["result"]["applied"] is False:
            refus = r["result"]
            break
    check("Vigueur insuffisante → applied:false et le serveur répond toujours",
          refus is not None and s5.send(cmd="snapshot").get("ok") is True,
          f"vigueur au refus={refus and refus['vigueur']}")

    # Régen via le tick moteur (engine.py branche tick_player_vigueur seul).
    v_avant = refus["vigueur"]
    r = s5.send(cmd="step_week")
    v_apres = r["snapshot"]["player"]["vigueur"]
    check("step_week régénère (+10/sem via le tick moteur)",
          v_apres == v_avant + 10.0, f"{v_avant} → {v_apres}")

    # Refill au passage de saison : la semaine 14 (début été) remet à PLEIN —
    # la régen seule n'expliquerait pas le saut (10/sem ne suffit pas).
    snap = s5.send(cmd="snapshot")["snapshot"]
    while snap["week"] <= 14:
        if snap["player"]["vigueur"] > 60.0:    # garder un déficit > régen
            s5.send(cmd="action", verb="grelinette")
        snap = s5.send(cmd="step_week")["snapshot"]
    check("refill au passage de saison (plein à la semaine 14)",
          snap["player"]["vigueur"] == snap["player"]["vigueur_max"],
          f"vigueur={snap['player']['vigueur']} week={snap['week']}")
    s5.send(cmd="quit")
    check("quit actions → exit 0", s5.close() == 0)

    # Déterminisme AVEC actions : 2 runs, mêmes gestes → byte-identiques.
    def run_actions(seed):
        s = ServerProc()
        s.send(cmd="init", seed=seed)
        for _ in range(3):
            snap = s.send(cmd="step_week")["snapshot"]
        p = snap["plants"][0]
        s.send(cmd="action", verb="manger",
               target={"tile": p["tile"], "x_cm": p["x_cm"], "y_cm": p["y_cm"]})
        s.send(cmd="action", verb="grelinette")
        s.send(cmd="action", verb="ecraser",
               target={"tile": "T0", "r": 1, "c": 1}, params={"urgence": True})
        s.send(cmd="step_week")
        s.send(cmd="snapshot")
        s.send(cmd="quit")
        return s
    a2, b2 = run_actions(42), run_actions(42)
    a2.close(); b2.close()
    check("2 runs mêmes actions → réponses byte-identiques",
          a2.raw_lines == b2.raw_lines)

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

    # --- bilan ----------------------------------------------------------------
    n_fail = sum(1 for _, ok in _results if not ok)
    print(f"\n[test_sim_server] {'PASS' if n_fail == 0 else 'FAIL'} — "
          f"{len(_results) - n_fail}/{len(_results)} checks verts")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
