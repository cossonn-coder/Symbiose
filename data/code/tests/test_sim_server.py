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
                    le repli params.cible (t4) reste intact ;
  9. hints organes — (tranche 6·A) chaque plante du snapshot porte
                    foliage_density (0..1, saisonnier), organ (proxy
                    REPRO_BY_SEASON + repli DEFAUT) et organ_site
                    (terminal|lateral) ; caduc en hiver → densité 0 et
                    organ null pour tout le monde. Pur rendu, lecture seule.
 10. vie macro    — (tranche 6·B) bloc `sprites` au snapshot : par tuile et
                    par guilde, tableaux compacts [r, c, x_frac, y_frac,
                    activite] issus de sample_sprites (PUR, déterministe).
                    Forme et bornes (cap 4/plot/guilde, fracs ∈ [0,1]),
                    démarrage à zéro (populations vides semaine 1), émergence
                    estivale, positions STABLES d'une semaine à l'autre (un
                    slot vit toujours au même point), lecture sans effet de
                    bord. Le déterminisme byte-à-byte (section 4) couvre
                    aussi ce bloc.
 12. planter·arroser — (sprint éponyme, protocole 0.3.3) gestes de milieu par
                    POSITION (x_cm/y_cm → plot-foyer côté serveur). `planter` :
                    refus espèce inconnue / lot vide / hors tuile / tuile
                    introuvable SANS coût ; banque-joueur exposée au snapshot
                    (`player.seeds`, vide à l'init, remplie à la récolte) ; un
                    dépôt réussi DÉCROÎT le lot de 1 et paie FAIBLE. `arroser` :
                    le champ humidité monte de DOSE au plot visé, coût MODÉRÉ
                    (× URGENCE_MULT en urgence), cumul PLAFONNÉ à 3.0.
                    Déterminisme byte-à-byte des deux gestes.
 11. champs debug — (tranche 6·C) commande `fields` HORS snapshot : registre
                    découvert par introspection (12 GridField d'EcoFields +
                    4 guildes), grilles par tuile row-major (rows×cols
                    cohérents, len(values) exact), guilde interrogeable
                    aussi, champ inconnu → ok:false AVEC serveur survivant,
                    avant init → ok:false, lecture pure (2 appels
                    identiques).

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

# Tranche 7 (packaging) : si SIM_SERVER_BIN pointe un binaire gelé
# (PyInstaller), la suite ENTIÈRE tourne contre lui au lieu du script —
# mêmes 87 checks, déterminisme byte-à-byte compris. Sans la variable,
# rien ne change (script + interpréteur courant, comme avant).
SERVER_BIN = os.environ.get("SIM_SERVER_BIN")
SERVER_CMD = [SERVER_BIN] if SERVER_BIN else [sys.executable, SERVER]

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


class ServerProc:
    """Pilote le serveur par les pipes, comme SimBridge.cs le fera côté Godot."""

    def __init__(self):
        self.proc = subprocess.Popen(
            SERVER_CMD, cwd=CODE_DIR,
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

    # Maladresse (protocole 0.3.1) : on écrase le SPRITE cliqué, guilde comprise —
    # pas seulement le ravageur. Guilde inconnue → refus PUR (rien dépensé).
    r = s5.send(cmd="action", verb="ecraser",
                target={"tile": "T0", "r": 0, "c": 0, "guilde": "licorne"})
    check("ecraser guilde inconnue → applied:false, serveur survivant",
          r["result"]["applied"] is False and s5.send(cmd="snapshot").get("ok") is True,
          r["result"]["message"])
    r = s5.send(cmd="action", verb="ecraser",
                target={"tile": "T0", "r": 0, "c": 0, "guilde": "auxiliaire"},
                params={"urgence": False})
    check("ecraser une guilde explicite (auxiliaire) → appliqué ET nommé",
          r["result"]["applied"] is True and "auxiliaire" in r["result"]["message"],
          r["result"]["message"])

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
                target={"tile": "T0", "r": 0, "c": 0, "guilde": "ravageur"})
    check("écraser une guilde par r/c → toujours routé guilde (volet 1 intact)",
          r["result"]["applied"] is True and "ravageur" in r["result"]["message"],
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

    # --- 9. hints organes (tranche 6·A) ---------------------------------------
    print("[hints organes]")
    ORGANES = {None, "flower", "fruit_unripe", "fruit_ripe"}
    s9 = ServerProc()
    s9.send(cmd="init", seed=42)
    snap = s9.send(cmd="snapshot")["snapshot"]
    check("schéma plante : les 3 hints présents",
          all(all(k in p for k in ("foliage_density", "organ", "organ_site"))
              for p in snap["plants"]))
    check("foliage_density ∈ [0,1]",
          all(0.0 <= p["foliage_density"] <= 1.0 for p in snap["plants"]))
    check("organ_site ∈ {terminal, lateral}",
          all(p["organ_site"] in ("terminal", "lateral")
              for p in snap["plants"]))
    check("organ ∈ {null, flower, fruit_unripe, fruit_ripe}",
          all(p["organ"] in ORGANES for p in snap["plants"]))
    # Semaine 1 = printemps : la table (Tomato/AppleTree) ET le repli DEFAUT
    # disent « flower » — personne ne fructifie au printemps.
    check("printemps : organ = flower partout",
          all(p["organ"] == "flower" for p in snap["plants"]),
          f"organes={ {p['organ'] for p in snap['plants']} }")
    pommier = next(p for p in snap["plants"] if p["species"] == "AppleTree")
    dens_printemps = pommier["foliage_density"]
    check("pommier feuillé au printemps", dens_printemps > 0.0,
          f"densité={dens_printemps}")

    # Traverser été (sem 14 : pommier fruit_unripe ≠ tomate fruit_ripe — les
    # cycles d'espèces divergent, critère F5) puis hiver (sem 40 : caduc nu).
    while snap["week"] < 14:
        snap = s9.send(cmd="step_week")["snapshot"]
    par_espece = {p["species"]: p["organ"] for p in snap["plants"]}
    check("été : pommier fruit_unripe, tomate fruit_ripe (cycles distincts)",
          par_espece.get("AppleTree") == "fruit_unripe"
          and par_espece.get("Tomato", "fruit_ripe") == "fruit_ripe",
          f"été={par_espece}")
    while snap["week"] < 40:
        snap = s9.send(cmd="step_week")["snapshot"]
    check("hiver : organ null partout",
          snap["season"] == "hiver"
          and all(p["organ"] is None for p in snap["plants"]),
          f"semaine {snap['week']}, organes="
          f"{ {p['organ'] for p in snap['plants']} }")
    pommier = next((p for p in snap["plants"] if p["species"] == "AppleTree"),
                   None)
    check("hiver : le pommier (caduc) a foliage_density = 0",
          pommier is not None and pommier["foliage_density"] == 0.0,
          pommier and f"densité={pommier['foliage_density']}")
    # Mesure du surcoût des hints (kickoff : ~+60 o/plante attendu, vérifier).
    size = len(json.dumps(snap, sort_keys=True, separators=(",", ":")))
    print(f"  📏 taille snapshot semaine {snap['week']} avec hints : {size} "
          f"octets ({len(snap['plants'])} plantes)")
    s9.send(cmd="quit")
    check("quit hints → exit 0", s9.close() == 0)

    # --- 10. vie macro (tranche 6·B) -------------------------------------------
    print("[vie macro]")
    GUILDES = {"ravageur", "auxiliaire", "pollinisateur", "vers_de_terre"}
    s10 = ServerProc()
    r = s10.send(cmd="init", seed=42)
    snap = s10.send(cmd="snapshot")["snapshot"]
    spr = snap.get("sprites", {})
    check("bloc sprites présent, indexé par tuile",
          set(spr.keys()) == {t["id"] for t in r["world"]["tiles"]},
          f"tuiles={sorted(spr.keys())}")
    check("les 4 guildes par tuile",
          all(set(g.keys()) == GUILDES for g in spr.values()))
    check("semaine 1 : aucun sprite (populations à zéro, rien simulé)",
          all(not lst for g in spr.values() for lst in g.values()))

    # Avancer en fin d'été : la vie macro a émergé (mesuré ~170 sprites smoke
    # semaine 20 — chaleur + feuillage + sol vivant nourrissent les 4 guildes).
    while snap["week"] < 20:
        snap = s10.send(cmd="step_week")["snapshot"]
    spr = snap["sprites"]
    n_tot = sum(len(lst) for g in spr.values() for lst in g.values())
    check("fin d'été : des sprites ont émergé", n_tot > 0, f"n={n_tot}")
    rows_cols = {t["id"]: (t["rows"], t["cols"]) for t in r["world"]["tiles"]}
    ok_forme = ok_cap = True
    for tid, guilds in spr.items():
        rows, cols = rows_cols[tid]
        for lst in guilds.values():
            par_plot = {}
            for e in lst:
                ok_forme &= (len(e) == 5
                             and isinstance(e[0], int) and 0 <= e[0] < rows
                             and isinstance(e[1], int) and 0 <= e[1] < cols
                             and 0.0 <= e[2] <= 1.0 and 0.0 <= e[3] <= 1.0
                             and 0.0 <= e[4] <= 1.0)
                par_plot[(e[0], e[1])] = par_plot.get((e[0], e[1]), 0) + 1
            ok_cap &= all(n <= 4 for n in par_plot.values())
    check("forme [r, c, x_frac, y_frac, activite] et bornes", ok_forme)
    check("cap respecté (≤ 4 sprites par plot et par guilde)", ok_cap)

    # Positions stables entre 2 semaines : un slot vit toujours au même point
    # (hash indépendant de la semaine) — pour chaque (guilde, plot), la liste
    # de la semaine N+1 partage son préfixe de positions avec la semaine N.
    suiv = s10.send(cmd="step_week")["snapshot"]["sprites"]
    def par_plot_xy(guilds):
        d = {}
        for g, lst in guilds.items():
            for e in lst:
                d.setdefault((g, e[0], e[1]), []).append((e[2], e[3]))
        return d
    stable = True
    for tid in spr:
        avant, apres = par_plot_xy(spr[tid]), par_plot_xy(suiv[tid])
        for k in avant.keys() & apres.keys():
            n = min(len(avant[k]), len(apres[k]))
            stable &= avant[k][:n] == apres[k][:n]
    check("positions stables d'une semaine à l'autre (slots ancrés)", stable)

    # Lecture sans effet de bord : 2 snapshots consécutifs sans step sont
    # identiques (sample_sprites est PURE — elle n'avance aucun RNG vivant).
    check("2 snapshots sans step → identiques (échantillonnage pur)",
          s10.send(cmd="snapshot")["snapshot"]
          == s10.send(cmd="snapshot")["snapshot"])
    # Mesure du surcoût sprites (kickoff §4 : mesurer, noter dans 00_etat.md).
    size = len(json.dumps(snap, sort_keys=True, separators=(",", ":")))
    print(f"  📏 taille snapshot semaine {snap['week']} avec sprites : {size} "
          f"octets ({n_tot} sprites)")
    s10.send(cmd="quit")
    check("quit vie macro → exit 0", s10.close() == 0)

    # --- 11. champs debug (tranche 6·C) ----------------------------------------
    print("[champs debug]")
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

    # --- 12. planter & arroser (protocole 0.3.3) ------------------------------
    # Gestes sur le MILIEU désignés par POSITION continue (x_cm/y_cm, locale
    # tuile) résolue en plot-foyer côté serveur. `planter` dépose une graine de
    # la banque-joueur (puis la succession la lève au bon moment, cf.
    # test_planter) ; `arroser` mouille le champ humidité (cap 3, cumulatif).
    print("[planter & arroser]")
    s12 = ServerProc()
    s12.send(cmd="init", seed=42)

    def hum_at(srv, tid, r, c):
        g = srv.send(cmd="fields", field="humidite")["tiles"][tid]
        return g["values"][r * g["cols"] + c]

    snap = s12.send(cmd="snapshot")["snapshot"]
    check("bloc player.seeds présent, vide à l'init (banque non remplie)",
          snap["player"].get("seeds") == {}, f"seeds={snap['player'].get('seeds')}")

    # Refus de planter (vigueur 100, RIEN ne doit bouger) : espèce inconnue,
    # lot vide, position hors tuile, tuile introuvable — tous applied:false.
    PT = {"tile": "T0", "x_cm": 75.0, "y_cm": 75.0}          # plot (1,1) de T0
    r = s12.send(cmd="action", verb="planter",
                 target=PT, params={"species": "licorne"})
    check("planter espèce inconnue → applied:false",
          r["result"]["applied"] is False and "non plantable" in r["result"]["message"],
          r["result"]["message"])
    r = s12.send(cmd="action", verb="planter",
                 target=PT, params={"species": "tomate"})
    check("planter lot vide (espèce valide, banque vide) → applied:false",
          r["result"]["applied"] is False and "lot vide" in r["result"]["message"],
          r["result"]["message"])
    r = s12.send(cmd="action", verb="planter",
                 target={"tile": "T0", "x_cm": 99999.0, "y_cm": 0.0},
                 params={"species": "tomate"})
    check("planter hors tuile → applied:false", r["result"]["applied"] is False,
          r["result"]["message"])
    r = s12.send(cmd="action", verb="planter",
                 target={"tile": "TZZ", "x_cm": 75.0, "y_cm": 75.0},
                 params={"species": "tomate"})
    check("planter tuile introuvable → applied:false",
          r["result"]["applied"] is False)
    check("aucun refus de planter n'a coûté de Vigueur",
          r["result"]["vigueur"] == 100.0, f"vigueur={r['result']['vigueur']}")

    # Arroser : le champ humidité monte de DOSE au plot visé, coût MODÉRÉ (15).
    h0 = hum_at(s12, "T0", 1, 1)
    r = s12.send(cmd="action", verb="arroser", target=PT)
    check("arroser → applied:true, coût MODÉRÉ (15)",
          r["result"]["applied"] is True and r["result"]["vigueur"] == 85.0,
          f"vigueur={r['result']['vigueur']}")
    h1 = hum_at(s12, "T0", 1, 1)
    check("le champ humidité monte de DOSE_ARROSAGE (0.5) au plot visé",
          abs((h1 - h0) - 0.5) < 1e-6, f"{h0} → {h1}")
    # Urgence (phase Saison, couture §3.1) : × URGENCE_MULT = 22.5.
    r = s12.send(cmd="action", verb="arroser", target=PT, params={"urgence": True})
    check("arroser en urgence coûte URGENCE_MULT × MODÉRÉ (22.5)",
          85.0 - r["result"]["vigueur"] == 22.5, f"Δ={85.0 - r['result']['vigueur']}")
    # Cumul borné : marteler le même plot → l'humidité PLAFONNE à 3.0 (les
    # arrosages refusés faute de Vigueur ne touchent pas le champ).
    for _ in range(8):
        s12.send(cmd="action", verb="arroser", target=PT)
    check("humidité plafonne à 3.0 (cumul borné, cap Q9)",
          abs(hum_at(s12, "T0", 1, 1) - 3.0) < 1e-6, hum_at(s12, "T0", 1, 1))

    # Planter pour de vrai : avancer jusqu'à ce que la récolte d'automne
    # remplisse la banque-joueur, puis déposer une graine → le lot DÉCROÎT de 1
    # et la Vigueur paie FAIBLE (5). Le passage de saison a remis la Vigueur au
    # plein → on lit un débit propre. La germination différée, elle, est couverte
    # par test_planter (la succession lève le grain au bon moment).
    snap = s12.send(cmd="snapshot")["snapshot"]
    while not snap["player"]["seeds"] and snap["week"] < 20:
        snap = s12.send(cmd="step_week")["snapshot"]
    seeds_av = snap["player"]["seeds"]
    check("la récolte d'automne a rempli la banque-joueur",
          len(seeds_av) > 0, f"seeds={seeds_av} (semaine {snap['week']})")
    espece = next(iter(seeds_av))            # sorted (JSON sort_keys) → déterministe
    vig_av = snap["player"]["vigueur"]
    r = s12.send(cmd="action", verb="planter",
                 target={"tile": "T0", "x_cm": 25.0, "y_cm": 25.0},
                 params={"species": espece})
    check("planter une graine en banque → applied:true, coût FAIBLE (5)",
          r["result"]["applied"] is True and vig_av - r["result"]["vigueur"] == 5.0,
          f"Δvigueur={vig_av - r['result']['vigueur']} ({r['result']['message']})")
    seeds_ap = r["snapshot"]["player"]["seeds"]
    check("le lot de l'espèce plantée a décru de 1 (graine sortie de la banque)",
          seeds_ap.get(espece, 0) == seeds_av[espece] - 1,
          f"{espece} : {seeds_av[espece]} → {seeds_ap.get(espece, 0)}")
    s12.send(cmd="quit")
    check("quit planter/arroser → exit 0", s12.close() == 0)

    # Déterminisme byte-à-byte (planter/arroser sont des fonctions PURES de
    # l'état : aucun RNG, la levée différée réutilise le hash de niche).
    def run_pa(seed):
        s = ServerProc()
        s.send(cmd="init", seed=seed)
        snap = s.send(cmd="snapshot")["snapshot"]
        while not snap["player"]["seeds"] and snap["week"] < 20:
            snap = s.send(cmd="step_week")["snapshot"]
        sp = next(iter(snap["player"]["seeds"]), None)
        if sp:
            s.send(cmd="action", verb="planter",
                   target={"tile": "T0", "x_cm": 25.0, "y_cm": 25.0},
                   params={"species": sp})
        s.send(cmd="action", verb="arroser",
               target={"tile": "T0", "x_cm": 75.0, "y_cm": 75.0},
               params={"urgence": True})
        s.send(cmd="snapshot")
        s.send(cmd="quit")
        return s
    a12, b12 = run_pa(42), run_pa(42)
    a12.close(); b12.close()
    check("2 runs planter+arroser même seed → byte-identiques",
          a12.raw_lines == b12.raw_lines)

    # --- bilan ----------------------------------------------------------------
    n_fail = sum(1 for _, ok in _results if not ok)
    print(f"\n[test_sim_server] {'PASS' if n_fail == 0 else 'FAIL'} — "
          f"{len(_results) - n_fail}/{len(_results)} checks verts")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
