"""
SYMBIOSE — tests/simserver/actions.py
Section 7 : actions v1 (tranche 4). Bloc `player` au snapshot, régen + refill de
saison via le tick moteur, manger/deraciner par POSITION, URGENCE_MULT sur
ecraser, refus métier (applied:false) AVEC serveur survivant, déterminisme
2 runs aux mêmes actions.
"""
from .harness import check, ServerProc


def test_actions_v1():
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
    # Depuis 0.3.6 (vue·rattrapage 02), le snapshot N'EFFACE PLUS les morts : une
    # plante déracinée devient un SQUELETTE exposé (`dead=true`) au lieu de
    # « disparaître » (l'ancien `if not is_alive: continue` la masquait alors
    # qu'elle persistait déjà dans `tile.plants`). On vérifie donc qu'elle est
    # passée squelette à la MÊME clé (tile|x|y) — toujours un seul aller-retour.
    squelette = next((p for p in r["snapshot"]["plants"]
                      if p["tile"] == pos["tile"] and p["x_cm"] == pos["x_cm"]
                      and p["y_cm"] == pos["y_cm"]), None)
    check("la plante déracinée passe squelette (dead=true) dans le snapshot JOINT",
          squelette is not None and squelette.get("dead") is True,
          squelette and f"stade_mort={squelette.get('stade_mort')}")
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

    # Maladresse (protocole ⑥, `target.espece`) : on écrase le SPRITE cliqué, espèce
    # comprise — pas seulement le ravageur. Espèce inconnue → refus PUR (rien dépensé).
    r = s5.send(cmd="action", verb="ecraser",
                target={"tile": "T0", "r": 0, "c": 0, "espece": "licorne"})
    check("ecraser espèce inconnue → applied:false, serveur survivant",
          r["result"]["applied"] is False and s5.send(cmd="snapshot").get("ok") is True,
          r["result"]["message"])
    r = s5.send(cmd="action", verb="ecraser",
                target={"tile": "T0", "r": 0, "c": 0, "espece": "coccinelle"},
                params={"urgence": False})
    check("ecraser une espèce explicite (coccinelle, auxiliaire ④c) → appliqué ET nommé",
          r["result"]["applied"] is True and "coccinelle" in r["result"]["message"],
          r["result"]["message"])
    # Repli compat (clients < ⑥) : la clé legacy `guilde` est encore acceptée.
    r = s5.send(cmd="action", verb="ecraser",
                target={"tile": "T0", "r": 0, "c": 0, "guilde": "coccinelle"},
                params={"urgence": False})
    check("ecraser via clé legacy `guilde` → encore accepté (bascule client en ⑥b)",
          r["result"]["applied"] is True and "coccinelle" in r["result"]["message"],
          r["result"]["message"])

    # Vigueur insuffisante : drainer à la grelinette (sans cible) jusqu'au refus.
    refus = None
    for _ in range(8):
        r = s5.send(cmd="action", verb="grelinette",
                    target={"tile": "T0", "r": 2, "c": 2})
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
            s5.send(cmd="action", verb="grelinette",
                    target={"tile": "T0", "r": 2, "c": 2})
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
        s.send(cmd="action", verb="grelinette",
               target={"tile": "T0", "r": 2, "c": 2})
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
