"""
SYMBIOSE — tests/simserver/vent.py
Section 22 : le VENT au pont (sprint JARDIN VIVANT T3, protocole 0.5.44).
  - `weather.wind = {force, direction, gusts}` == `wind_at`/`gust_profile` rejoués
    côté test sur la dernière semaine simulée (`week − 1`) ; calme à l'init ;
  - clé `abri` par plante vivante : ABSENTE à l'init (champ d'abri jamais calculé,
    jamais forcé — D99), PRÉSENTE après un step, finie et positive ;
  - `snapshot` == état du dernier step (via `_scrub`) ; déterminisme byte-à-byte.
PURE lecture → golden NEUTRE.
"""
import json

from sim.wind import wind_at, gust_profile
from .harness import check, ServerProc, _scrub

SEED = 42


def _run(seed):
    """init smoke → (snapshot init) → step ×4 → snapshot (semaine 5)."""
    s = ServerProc()
    init = s.send(cmd="init", seed=seed)
    snap0 = init.get("snapshot") or s.send(cmd="snapshot")["snapshot"]
    snap = None
    for _ in range(4):
        snap = s.send(cmd="step_week")["snapshot"]
    return s, snap0, snap


def test_vent_pont():
    print("\n[22] vent au pont : weather.wind + abri par plante (0.5.44)")
    s, snap0, snap = _run(SEED)

    # --- init : calme, aucune clé abri (champ jamais calculé, jamais forcé) ---
    w0 = snap0.get("weather", {}).get("wind", {})
    check("init : weather.wind présent", set(w0) == {"force", "direction", "gusts"},
          sorted(w0))
    check("init : force nulle (rien simulé = calme)", w0.get("force") == 0.0,
          w0.get("force"))
    vivantes0 = [p for p in snap0.get("plants", []) if not p.get("dead")]
    check("init : aucune clé `abri` (champ d'abri paresseux non forcé)",
          all("abri" not in p for p in vivantes0),
          sum("abri" in p for p in vivantes0))

    # --- après 4 steps : fidèle au helper pur, semaine `last` --------------------
    last = snap["week"] - 1
    w = snap.get("weather", {}).get("wind", {})
    ref = wind_at(SEED, last)
    check("weather.wind.force == wind_at(last).force", w.get("force") == ref.force,
          f"{w.get('force')} vs {ref.force}")
    check("weather.wind.direction == wind_at(last).direction",
          w.get("direction") == ref.direction,
          f"{w.get('direction')} vs {ref.direction}")
    check("weather.wind.gusts == gust_profile(last)",
          w.get("gusts") == list(gust_profile(SEED, last)), w.get("gusts"))

    vivantes = [p for p in snap.get("plants", []) if not p.get("dead")]
    check("après step : `abri` sur chaque plante vivante",
          len(vivantes) > 0 and all("abri" in p for p in vivantes),
          f"{sum('abri' in p for p in vivantes)}/{len(vivantes)}")
    check("abri : flottant fini et > 0",
          all(isinstance(p.get("abri"), (int, float)) and 0.0 < p["abri"] < 3.0
              for p in vivantes))

    r = s.send(cmd="snapshot")
    check("snapshot == état du dernier step (vent compris)",
          _scrub(json.dumps({"snapshot": r.get("snapshot")}))
          == _scrub(json.dumps({"snapshot": snap})))
    s.send(cmd="quit")
    check("quit vent → exit 0", s.close() == 0)

    # Déterminisme : même seed → même vent, mêmes facteurs d'abri, octet pour octet.
    s2, _, snap2 = _run(SEED)
    s2.send(cmd="quit"); s2.close()
    dump = lambda d: json.dumps(d, sort_keys=True, separators=(",", ":"))
    check("2 runs même seed → weather.wind byte-identique",
          dump(snap["weather"]["wind"]) == dump(snap2["weather"]["wind"]))
    check("2 runs même seed → abri byte-identique",
          dump([p.get("abri") for p in snap["plants"]])
          == dump([p.get("abri") for p in snap2["plants"]]))
