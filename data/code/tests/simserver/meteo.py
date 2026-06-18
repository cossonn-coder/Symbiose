"""
SYMBIOSE — tests/simserver/meteo.py
Section 16 : snapshot météo + carte température exposés au pont (sprint thermique
⑧, protocole 0.5.0). Le snapshot porte désormais DEUX blocs lecture-seule :
  - `weather` = scalaire GLOBAL du tick courant (météo de `week-1`, recalculée
    par le helper PUR sim.weather.weather_state) : kind/intensity/scope/
    nebulosite/t_air + `signs` (préavis diégétiques, weather_signs) ;
  - `temperature[tile]` = {snow (manteau ⑦), t_sol (grille 2D rows×cols ⑤)},
    états déjà calculés par le tick → lecture DIRECTE.
PURE lecture (zéro écriture moteur, weather_state/weather_signs sont pures) →
golden NEUTRE. On vérifie ici la FORME + la COHÉRENCE avec un recalcul pur
indépendant (la valeur du pont == le helper évalué côté test) + le déterminisme.
"""
import json

from sim.weather import weather_state, weather_signs
from .harness import check, ServerProc

SEED = 42


def _run(seed):
    """init smoke → step ×4 → snapshot. `week`=5 → météo courante = `week-1`=4."""
    s = ServerProc()
    world = s.send(cmd="init", seed=seed)["world"]
    snap = None
    for _ in range(4):
        snap = s.send(cmd="step_week")["snapshot"]
    return s, world, snap


def test_meteo():
    print("\n[16] snapshot météo + carte température exposés au pont (0.5.0)")
    s, world, snap = _run(SEED)
    last = snap["week"] - 1                     # météo qui a produit l'état courant

    # --- bloc `weather` : forme + cohérence avec un recalcul PUR indépendant ----
    check("snapshot porte un bloc `weather`", "weather" in snap, sorted(snap))
    w = snap.get("weather", {})
    check("schéma weather complet",
          all(k in w for k in ("kind", "intensity", "scope", "nebulosite",
                               "t_air", "signs")),
          sorted(w))

    # Le pont RECALCULE la météo par fonction pure → on la rejoue côté test (même
    # helper) et on exige l'égalité champ par champ (avec les arrondis du snapshot).
    ev, t_air, nebul = weather_state(SEED, last)
    check("weather.kind == helper pur (∈ catalogue)", w.get("kind") == ev.kind,
          f"{w.get('kind')} vs {ev.kind}")
    check("weather.scope ∈ {global, local}", w.get("scope") in ("global", "local"),
          w.get("scope"))
    check("weather.scope == helper pur", w.get("scope") == ev.scope)
    check("weather.intensity == round(helper, 3)",
          w.get("intensity") == round(ev.intensity, 3),
          f"{w.get('intensity')} vs {round(ev.intensity, 3)}")
    check("weather.nebulosite == round(helper, 3)",
          w.get("nebulosite") == round(nebul, 3),
          f"{w.get('nebulosite')} vs {round(nebul, 3)}")
    check("weather.t_air == round(helper, 2) (normale ± delta)",
          w.get("t_air") == round(t_air, 2),
          f"{w.get('t_air')} vs {round(t_air, 2)}")

    # `signs` : structure complète des préavis (kind/in_weeks/signs/signed),
    # identique à weather_signs rejoué côté test (cadeau de la fonction pure).
    expected_signs = weather_signs(SEED, last, horizon=2)
    sg = w.get("signs", [])
    check("signs est une liste", isinstance(sg, list), type(sg).__name__)
    check("signs == weather_signs pur (nombre)", len(sg) == len(expected_signs),
          f"{len(sg)} vs {len(expected_signs)}")
    check("signs : schéma par entrée",
          all(set(e) == {"kind", "in_weeks", "signs", "signed"} for e in sg),
          [sorted(e) for e in sg])
    check("signs : kind/in_weeks/signed fidèles au helper",
          all(e["kind"] == x.kind and e["in_weeks"] == x.in_weeks
              and e["signed"] == x.signed
              for e, x in zip(sg, expected_signs)))

    # --- bloc `temperature` par tuile : forme + dimensions + manteau ----------
    check("snapshot porte un bloc `temperature`", "temperature" in snap)
    temp = snap.get("temperature", {})
    check("une clé `temperature` par tuile (comme sprites)",
          set(temp) == set(snap["sprites"]), sorted(temp))
    dims = {t["id"]: (t["rows"], t["cols"]) for t in world["tiles"]}
    for tid, block in temp.items():
        check(f"[{tid}] schéma {{snow, t_sol}}",
              set(block) == {"snow", "t_sol"}, sorted(block))
        snow = block.get("snow")
        check(f"[{tid}] snow ∈ [0,1]",
              isinstance(snow, (int, float)) and 0.0 <= snow <= 1.0, snow)
        # Smoke = printemps (semaines 1-4), aucun événement Neige (fenêtre 44-52)
        # → manteau nul : la lecture pointe bien l'état moteur réel (eco.snow=0).
        check(f"[{tid}] snow == 0 au printemps (pas de Neige)", snow == 0.0, snow)
        rows, cols = dims[tid]
        t_sol = block.get("t_sol", [])
        check(f"[{tid}] t_sol = grille rows×cols ({rows}×{cols})",
              len(t_sol) == rows and all(len(r) == cols for r in t_sol),
              f"{len(t_sol)}×{len(t_sol[0]) if t_sol else 0}")
        check(f"[{tid}] t_sol = floats (températures de surface)",
              all(isinstance(v, (int, float)) for r in t_sol for v in r))

    s.send(cmd="quit")
    check("quit météo → exit 0", s.close() == 0)

    # Déterminisme byte-à-byte des deux blocs (round() déterministe, fonctions
    # pures) : même seed → même météo + même carte température, octet pour octet.
    s2, _, snap2 = _run(SEED)
    s2.send(cmd="quit"); s2.close()
    dump = lambda d: json.dumps(d, sort_keys=True, separators=(",", ":"))
    check("2 runs même seed → bloc weather byte-identique",
          dump(snap["weather"]) == dump(snap2["weather"]))
    check("2 runs même seed → bloc temperature byte-identique",
          dump(snap["temperature"]) == dump(snap2["temperature"]))
