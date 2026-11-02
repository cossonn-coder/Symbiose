"""
SYMBIOSE — tests/simserver/base.py
Sections 1–6 : contrats v0 + premières tranches. Forme & avancement, robustesse
(le serveur survit à tout), déterminisme byte-à-byte, arrêt propre (EOF sans
quit), monde full (tranche 2). Mesure aussi la taille du snapshot (octets/sem).
"""
import json
import subprocess

from .harness import check, ServerProc, run_scenario, _scrub


def test_v0_contract():
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
    # D96 : le bloc `perf` (ms_tick, rss_mo) dépend de la charge machine et
    # diffère entre les deux lectures → on le neutralise via `_scrub`, comme
    # pour les autres comparaisons de déterminisme. Sinon ce check est flaky.
    check("snapshot == état du dernier step",
          _scrub(json.dumps({"snapshot": r.get("snapshot")}))
          == _scrub(json.dumps({"snapshot": snap})))

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
    # 53 cultivées de base + 28 de la démo « planche paillée plein sud » (équilibre
    # invasion ⑧ : 4 cultures × 7 plots pré-mulchés sur la tuile S) = 81, + 7 de la
    # mare NE (SOL NOURRICIER ④ : 2 aulnes, 3 sphaignes, 2 rossolis) = 88, + 3 caducs
    # de démo (AUTOMNE VISIBLE ② : bouleau, cerisier, charme) = 91.
    check("91 plantes posées (semaine 1, rien simulé)",
          len(snap.get("plants", [])) == 91, f"n={len(snap.get('plants', []))}")
    # Mesure full (critère kickoff t2 : noter la taille dans 00_etat.md)
    r = s4.send(cmd="step_week")
    size = len(json.dumps(r, sort_keys=True, separators=(",", ":")))
    n_seg = sum(len(p["segments"]) for p in r["snapshot"]["plants"])
    print(f"  📏 taille snapshot full semaine 2 : {size} octets "
          f"({len(r['snapshot']['plants'])} plantes, {n_seg} segments)")
    s4.send(cmd="quit")
    check("quit full → exit 0", s4.close() == 0)
