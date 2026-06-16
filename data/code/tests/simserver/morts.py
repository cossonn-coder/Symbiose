"""
SYMBIOSE — tests/simserver/morts.py
Section 14 : plantes mortes persistantes (vue·rattrapage 02, protocole 0.3.6).
Le snapshot n'ignore plus les squelettes (décompo·compost ②B) : il les expose en
LECTURE avec `dead=true` + {stade_mort, bois_restant, semaines_mort} pour que la
vue dessine la silhouette sèche/couchée. Les vivantes portent `dead=false`.

Levier déterministe : `deraciner` met `health=0` puis `deposer_mort` → squelette
persistant pour une vivace LIGNEUSE (l'AppleTree de la config full ; une herbacée,
bois=0, serait retirée au tick et jamais vue). Aucun step entre le déracinage et le
snapshot : le squelette est observé frais (seche, semaines_mort=0).
"""
import json

from .harness import check, ServerProc


def _appletree(snap):
    """La première AppleTree VIVANTE du snapshot, ou None."""
    return next((p for p in snap["plants"]
                 if p["species"] == "AppleTree" and not p.get("dead", False)),
                None)


def _run(seed):
    """init full → repère un pommier vivant → le déracine → re-snapshot.
    Renvoie (server, snap_avant, ack_deraciner, snap_apres)."""
    s = ServerProc()
    s.send(cmd="init", seed=seed)
    snap0 = s.send(cmd="snapshot")["snapshot"]
    tree = _appletree(snap0)
    ack = s.send(cmd="action", verb="deraciner",
                 target={"tile": tree["tile"],
                         "x_cm": tree["x_cm"], "y_cm": tree["y_cm"]})
    snap1 = s.send(cmd="snapshot")["snapshot"]
    return s, snap0, tree, ack, snap1


def test_morts():
    print("[plantes mortes / squelettes]")
    s, snap0, tree, ack, snap1 = _run(42)

    check("config full : un pommier vivant au départ", tree is not None,
          tree and f"{tree['species']} @{tree['tile']}")
    check("toutes les vivantes portent dead=false",
          all(p.get("dead") is False for p in snap0["plants"]),
          f"valeurs={ {p.get('dead') for p in snap0['plants']} }")
    check("déracinage ACK ok", ack.get("ok") is True, json.dumps(ack))

    # Le pommier déraciné = MÊME clé (tile|species|x|y) ; il n'a pas disparu du
    # snapshot, il est passé squelette.
    mort = next((p for p in snap1["plants"]
                 if p["species"] == "AppleTree" and p["tile"] == tree["tile"]
                 and abs(p["x_cm"] - tree["x_cm"]) < 0.1
                 and abs(p["y_cm"] - tree["y_cm"]) < 0.1), None)
    check("le pommier déraciné persiste (squelette, non retiré)", mort is not None)
    check("le squelette porte dead=true", mort and mort.get("dead") is True)
    check("stade_mort = 'seche' (debout, frais déraciné)",
          mort and mort.get("stade_mort") == "seche", mort and mort.get("stade_mort"))
    check("bois_restant > 0 (réservoir ligneux à fragmenter)",
          mort and mort.get("bois_restant", 0.0) > 0.0,
          mort and f"bois={mort.get('bois_restant')}")
    check("semaines_mort = 0 (aucun tick depuis la mort)",
          mort and mort.get("semaines_mort") == 0)
    check("le squelette garde sa structure (silhouette à dessiner)",
          mort and len(mort.get("segments", [])) > 0,
          mort and f"{len(mort.get('segments', []))} segments")
    check("un squelette n'expose ni fruits ni organ (mort = pas de biologie)",
          mort and "fruits" not in mort and "organ" not in mort)
    # Les AUTRES plantes restent vivantes (le déracinage ne touche qu'une cible).
    autres = [p for p in snap1["plants"] if p is not mort and p.get("dead") is not None]
    check("les autres plantes restent dead=false",
          all(p["dead"] is False for p in autres if p["species"] != "AppleTree"
              or (p["tile"], p["x_cm"]) != (mort["tile"], mort["x_cm"])))

    s.send(cmd="quit")
    check("quit morts → exit 0", s.close() == 0)

    # Déterminisme byte-à-byte : le même scénario (init + déracinage + snapshot)
    # rejoué au même seed doit produire le MÊME squelette, octet pour octet.
    s2, _, _, _, snap1b = _run(42)
    s2.send(cmd="quit"); s2.close()
    dump = lambda sn: json.dumps(sn, sort_keys=True, separators=(",", ":"))
    check("2 runs même seed → snapshot post-déracinage byte-identique",
          dump(snap1) == dump(snap1b))
