# SYMBIOSE — tools/banc_cadence.py (sprint FLUIDITÉ AN 2, tronçon ①)
# BANC DE CADENCE HEADLESS : ce que coûte UNE semaine côté Python, telle que la vue
# la reçoit, sur le vrai monde de jeu (`full`), répété pour être crédible.
#
# Par semaine on relève 5 grandeurs, toutes chronométrées AUTOUR du code existant :
#   - tick      : le tick moteur pur (`srv._last_ms_tick`, posé par cmd_step_week) ;
#   - automate  : la durée de `jouer_tick` (si l'automate est branché) ;
#   - snapshot  : la durée de `_snapshot()` (la photo envoyée à Godot) ;
#   - gc        : le temps passé dans le ramasse-miettes pendant la semaine (tick +
#                 snapshot), mesuré par `gc.callbacks` (start/stop) — PARTAGE ① ;
#   - Ko        : la taille du JSON de la réponse, sérialisé EXACTEMENT comme le pont
#                 (`sort_keys`, séparateurs compacts — cf. simserver/server.py) ;
#   - plantes   : plantes vivantes après la semaine.
# Sortie : moyenne / max par an, pour chaque run, puis l'agrégat des runs.
#
# 📖 Pédagogie (côté embarqué) : comme un banc de mesure de latence, on n'insère
# AUCUNE sonde dans le moteur. On remplace, sur l'INSTANCE du serveur seulement,
# deux méthodes par une enveloppe qui note l'heure avant/après puis appelle
# l'originale (« wrapper » = la sonde d'oscilloscope posée sur la broche, pas
# soudée dans le circuit). Le golden ne peut pas bouger : aucun code moteur touché.
# Pas de cProfile ici (il double les temps absolus) — la répartition par fonction
# reste le travail de `tools/profile_monde.py`.
#
# Runs EN SÉRIE (jamais en parallèle : ils se voleraient les cœurs) ; charge VM
# contrôlée comme `tools/perf_vm.sh` (> 4 = mesure peu fiable, on avertit).
#
# Usage (depuis data/code/) :
#   python3 -m tools.banc_cadence [--runs N] [--seed S] [--semaines W] [--automate]
#                                 [--delta] [--gc on|off]
#     --runs     N : runs successifs (défaut 3)
#     --seed     S : graine du monde (défaut 1521550718, référence du sprint)
#     --semaines W : semaines simulées par run (défaut 156 = 3 ans)
#     --automate   : branche l'automate (profil de la touche A : désherbage curatif)
#     --delta      : demande les semaines EN DELTA, comme le F5 (pont 0.6.0)
#     --gc on|off  : réglage du ramasse-miettes du serveur (`simserver/gc_pont`,
#                    défaut on = comme en jeu ; off = comportement CPython d'origine)

from __future__ import annotations
import argparse
import gc
import json
import statistics
import time

CHARGE_MAX = 4.0   # même seuil que tools/perf_vm.sh


def _charge_vm() -> float:
    """Charge moyenne sur 1 min (/proc/loadavg) ; -1 si illisible (hors Linux)."""
    try:
        with open("/proc/loadavg") as f:
            return float(f.read().split()[0])
    except (OSError, ValueError, IndexError):
        return -1.0


def _plantes_vivantes(engine) -> int:
    return sum(1 for t in engine.game_state["tiles"] for p in t.plants if p.is_alive)


def _sonder(srv, nom: str, releve: dict, cle: str) -> None:
    """Enveloppe la méthode `nom` de l'objet `srv` (instance seulement) : chaque
    appel ajoute sa durée (ms) à `releve[cle]`. L'original est appelé tel quel."""
    originale = getattr(srv, nom)

    def enveloppe(*args, **kwargs):
        t0 = time.perf_counter()
        try:
            return originale(*args, **kwargs)
        finally:
            releve[cle] += (time.perf_counter() - t0) * 1000.0

    setattr(srv, nom, enveloppe)


def _sonde_gc(releve: dict):
    """Branche sur `gc.callbacks` un chronomètre de collecte : chaque passe du
    ramasse-miettes ajoute sa durée (ms) à `releve["gc"]` (sonde, rien de modifié).
    Renvoie le rappel, à retirer en fin de run."""
    t0 = [0.0]

    def rappel(phase, info):
        if phase == "start":
            t0[0] = time.perf_counter()
        else:
            releve["gc"] += (time.perf_counter() - t0[0]) * 1000.0

    gc.callbacks.append(rappel)
    return rappel


def un_run(seed: int, semaines: int, automate: bool, delta: bool = False,
           gc_on: bool = True) -> list[dict]:
    """Monte `full` via le serveur (même fabrique que le F5), puis `semaines`
    appels `cmd_step_week`. Renvoie une ligne de relevés par semaine."""
    try:                     # absent d'un arbre antérieur à PARTAGE ① (mesure « avant »)
        from tools.simserver import gc_pont
        gc_pont.ACTIF = gc_on
    except ImportError:
        pass
    from tools.simserver.server import SimServer
    srv = SimServer()
    rep = srv.cmd_init({"config": "full", "seed": seed})
    if not rep.get("ok"):
        raise RuntimeError(f"cmd_init a échoué : {rep}")
    releve = {"automate": 0.0, "snapshot": 0.0, "gc": 0.0}
    if automate:
        rep = srv.cmd_automate({"op": "on", "profil": {"desherbage": "curatif"}})
        if not rep.get("ok"):
            raise RuntimeError(f"automate on a échoué : {rep}")
        _sonder(srv._automate, "jouer_tick", releve, "automate")
    _sonder(srv, "_snapshot", releve, "snapshot")
    rappel = _sonde_gc(releve)

    lignes = []
    for _ in range(semaines):
        releve["automate"] = releve["snapshot"] = releve["gc"] = 0.0
        rep = srv.cmd_step_week({"delta": True} if delta else {})
        if not rep.get("ok"):
            raise RuntimeError(f"step_week a échoué : {rep}")
        octets = len(json.dumps(rep, sort_keys=True, separators=(",", ":")).encode())
        lignes.append({"semaine": srv.engine.week - 1, "tick": srv._last_ms_tick,
                       "automate": releve["automate"], "snapshot": releve["snapshot"],
                       "gc": releve["gc"],
                       "ko": octets / 1024.0, "plantes": _plantes_vivantes(srv.engine)})
    gc.callbacks.remove(rappel)
    return lignes


COLONNES = ("tick", "automate", "snapshot", "gc", "ko", "plantes")


def _par_an(lignes: list[dict]) -> dict[int, dict]:
    """{an: {colonne: (moyenne, max)}} — an 0 = semaines 1-52 (semaine simulée)."""
    ans: dict[int, list[dict]] = {}
    for l in lignes:
        ans.setdefault((l["semaine"] - 1) // 52, []).append(l)
    return {an: {c: (statistics.fmean(l[c] for l in ls), max(l[c] for l in ls))
                 for c in COLONNES} | {"n": len(ls)}
            for an, ls in sorted(ans.items())}


def _imprimer(titre: str, table: dict[int, dict]) -> None:
    print(titre)
    print("  an  sem  tick moy/max ms   automate moy/max   snapshot moy/max   "
          "gc moy/max   réponse moy/max Ko   plantes moy/max")
    for an, r in table.items():
        cell = lambda c, f: f"{r[c][0]:{f}}/{r[c][1]:{f}}"
        print(f"  {an:>2}  {r['n']:>3}  {cell('tick', '6.0f'):>15}   "
              f"{cell('automate', '5.1f'):>16}   {cell('snapshot', '5.0f'):>16}   "
              f"{cell('gc', '4.0f'):>10}   "
              f"{cell('ko', '7.0f'):>18}   {cell('plantes', '4.0f'):>15}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Banc de cadence headless (fluidité an 2).")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--seed", type=int, default=1521550718)
    ap.add_argument("--semaines", type=int, default=156)
    ap.add_argument("--automate", action="store_true")
    ap.add_argument("--delta", action="store_true")
    ap.add_argument("--gc", choices=("on", "off"), default="on")
    a = ap.parse_args()

    print(f"banc_cadence : monde full · graine {a.seed} · {a.semaines} semaines · "
          f"automate {'ON (curatif)' if a.automate else 'OFF'} · "
          f"{'delta' if a.delta else 'complet'} · gc {a.gc} · {a.runs} run(s) en série")
    tous = []
    for i in range(a.runs):
        charge = _charge_vm()
        if charge > CHARGE_MAX:
            print(f"⚠️  charge VM {charge:.2f} > {CHARGE_MAX:.0f} au départ du run {i + 1} : "
                  "mesure peu fiable.")
        t0 = time.perf_counter()
        lignes = un_run(a.seed, a.semaines, a.automate, a.delta, a.gc == "on")
        tous.append(lignes)
        _imprimer(f"\nrun {i + 1}/{a.runs} ({time.perf_counter() - t0:.0f} s, "
                  f"charge départ {charge:.2f}, fin {_charge_vm():.2f})", _par_an(lignes))

    # Agrégat : moyenne des moyennes par an ; max = pire semaine tous runs confondus.
    tables = [_par_an(l) for l in tous]
    agg = {an: {c: (statistics.fmean(t[an][c][0] for t in tables),
                    max(t[an][c][1] for t in tables)) for c in COLONNES}
           | {"n": tables[0][an]["n"]} for an in tables[0]}
    _imprimer(f"\nAGRÉGAT [n={a.runs} runs] (moyenne des moyennes / pire semaine)", agg)
    # Déterminisme : mêmes populations d'un run à l'autre (sinon la mesure compare
    # deux jardins différents).
    pops = {tuple(l["plantes"] for l in lignes) for lignes in tous}
    print(f"populations identiques entre runs : {'oui' if len(pops) == 1 else 'NON'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
