"""
SYMBIOSE — tests/simserver/litiere.py
Section 15 : litière typée par plot exposée au snapshot (vue·rattrapage 03,
protocole 0.3.7). Le snapshot porte désormais `litiere[tile] = [[r, c,
tissu_dominant, masse], …]` — la couche fraîche de nécromasse de SURFACE que la
vue dessinera (03·B). PURE lecture (`eco.litiere` est rempli par le tick) →
golden NEUTRE. La parcelle `diffus` (exsudats/humus permanent) est ÉCARTÉE :
elle n'est pas de la litière de surface et ne se dessine pas.

Levier déterministe = `deraciner` un pommier (config full) : `deposer_mort`
dépose ses tissus MOUS en litière `feuille` sur son plot-foyer (même levier que
la section 14). Avant le geste, aucun plot ne porte de litière de surface → on
vérifie l'apparition ciblée + l'omission des plots vides + le déterminisme.
"""
import json

from constants import PLOT_CM
from .harness import check, ServerProc


def _appletree(snap):
    return next((p for p in snap["plants"]
                 if p["species"] == "AppleTree" and not p.get("dead", False)),
                None)


def _run(seed):
    """init full → snapshot (litière vide) → déracine un pommier → re-snapshot."""
    s = ServerProc()
    s.send(cmd="init", seed=seed)
    snap0 = s.send(cmd="snapshot")["snapshot"]
    tree = _appletree(snap0)
    ack = s.send(cmd="action", verb="deraciner",
                 target={"tile": tree["tile"],
                         "x_cm": tree["x_cm"], "y_cm": tree["y_cm"]})
    snap1 = s.send(cmd="snapshot")["snapshot"]
    return s, snap0, tree, ack, snap1


def test_litiere():
    print("\n[15] litière typée par plot exposée au snapshot (0.3.7)")
    s, snap0, tree, ack, snap1 = _run(42)

    check("snapshot porte un bloc `litiere`", "litiere" in snap0,
          sorted(snap0.keys()))
    check("une clé `litiere` par tuile (comme sprites/structures)",
          set(snap0["litiere"]) == set(snap0["sprites"]),
          sorted(snap0["litiere"]))
    check("au départ : aucune litière de surface (diffus non rendu)",
          all(len(v) == 0 for v in snap0["litiere"].values()),
          {k: len(v) for k, v in snap0["litiere"].items()})

    check("déracinage ACK ok", ack.get("ok") is True, json.dumps(ack))

    # Le plot-foyer du pommier (position continue → floor(/PLOT_CM)).
    pr, pc = int(tree["y_cm"] // PLOT_CM), int(tree["x_cm"] // PLOT_CM)
    lit = snap1["litiere"][tree["tile"]]
    check("la litière du plot du pommier apparaît (1 plot non vide)",
          len(lit) == 1, lit)
    entry = lit[0] if lit else None
    check("format compact [r, c, tissu, masse, age_sem, bois_masse, bois_age, bois_diam, feuille] (0.6.3)",
          entry is not None and len(entry) == 9, entry)
    check("masse de feuilles exposée (0.6.3 : 9ᵉ champ, ici tissu dominant)",
          entry is not None and entry[8] > 0.0, entry)
    check("bois_diam ≥ 0 (⑦bis : grosseur du bois mort exposée)",
          entry is not None and entry[7] >= 0.0, entry)
    check("bois_masse/bois_age ≥ 0 (D111 ② : bois mort exposé sous les feuilles)",
          entry is not None and entry[5] >= 0.0 and entry[6] >= 0.0, entry)
    check("le plot exposé = plot-foyer du pommier",
          entry is not None and entry[0] == pr and entry[1] == pc,
          entry and f"exposé={entry[:2]} attendu=[{pr}, {pc}]")
    check("tissu dominant = 'feuille' (tissu mou d'un ligneux mort)",
          entry is not None and entry[2] == "feuille", entry and entry[2])
    check("masse de surface > 0", entry is not None and entry[3] > 0.0,
          entry and entry[3])
    # age_sem (0.5.6) = état de décompo. Litière tout juste déposée → âge 0
    # (dépôt au tick courant, pas encore vieilli) ; la vue dérive la teinte ∝.
    check("age_sem présent et ≥ 0 (état de décompo, dérive de teinte côté vue)",
          entry is not None and isinstance(entry[4], (int, float))
          and entry[4] >= 0.0, entry and entry[4])

    # Les autres tuiles n'ont reçu aucune nécromasse → restent vides (creux).
    autres = {t: v for t, v in snap1["litiere"].items() if t != tree["tile"]}
    check("les autres tuiles restent vides (liste creuse)",
          all(len(v) == 0 for v in autres.values()),
          {k: len(v) for k, v in autres.items()})

    s.send(cmd="quit")
    check("quit litière → exit 0", s.close() == 0)

    # Déterminisme byte-à-byte du bloc litière (round() déterministe, ordre de
    # plot stable) : même seed → même litière exposée, octet pour octet.
    s2, _, _, _, snap1b = _run(42)
    s2.send(cmd="quit"); s2.close()
    dump = lambda lt: json.dumps(lt, sort_keys=True, separators=(",", ":"))
    check("2 runs même seed → bloc litière byte-identique",
          dump(snap1["litiere"]) == dump(snap1b["litiere"]))
