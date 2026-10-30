"""
SYMBIOSE — bancs/mesure_calendrier.py
BANC DE MESURE (hors golden, hors registre F5) du sprint CALENDRIER UNIQUE (D122,
docs/champs/climat/conception_calendrier_unique.md §6) : photographie chiffrée de
« QUAND se passe QUOI » dans l'année simulée, rejouée à l'identique avant (①), après
le décalage du climat (②) et après le recalibrage (③) — décision C3 « mesurer
d'abord, recalibrer après ».

Le script ne touche à AUCUNE mécanique : il déroule le moteur et LIT l'état réel
(`eco.temperature`, `eco.humidite`, `eco.glace`, `plant.floraison`/`bloom_week`/
`is_alive`, `eco.populations`, lignes du log) — frère de `bancs.mesure_floraison`.
Toutes les semaines sont étiquetées par la saison du moteur (`saison_de`).

Trois mondes (aucun ne porte TOUS les acteurs), même seed moteur par défaut :
  - SMOKE = le monde du golden (`tests.test_golden.build_world`, 2 tuiles terre/
    argile, maison) : seul monde déterministe qui plante la TOMATE. Sert aux
    indicateurs 1,2,5,6,7,8 et à la neige (événement météo global).
  - FLORAISON = banc `floraison_saisons` via `mesure_floraison._monde()` : le
    pommier du smoke est trop jeune pour fleurir en 3 ans (mesuré : aucune
    floraison) ; celui-ci fleurit → indicateur 4 (bloom, recouvrement, fruits).
  - TOURBIÈRE = banc `tourbiere` (cuvette avec lame d'eau) : seul monde avec de
    l'eau de surface → sert à la GLACE (indicateur 3). Le smoke n'a pas de mare.

Usage (depuis data/code/) :
  python3 -m bancs.mesure_calendrier        # 3 années (défaut)
  python3 -m bancs.mesure_calendrier 2      # 2 années (jamais plus de 3)
"""
from __future__ import annotations
import re
import sys
from collections import Counter, defaultdict
from statistics import median

from bancs import BANCS
from bancs.mesure_floraison import _monde as monde_floraison
from fields import POLLINATOR_NAMES, daylength
from sim.engine import Engine
from sim.engine.calendrier import saison_de
from sim.weather import weather_state
from sim.champignon_manger import carpophores_tuile
from tests.test_golden import build_world
from world import House

N_ANS_MAX = 3            # garde-fou du sprint : mesures ≤ 3 ans
SEUIL_BUTINEURS = 0.05   # densité totale (seuil de `mesure_floraison`)
SAISONS = ("printemps", "ete", "automne", "hiver")
_RE_ABSC = re.compile(r"🍂\s+Abscission\s+")
_RE_NOUAISON_POMMIER = re.compile(r"🍎 Nouaison Pommier@.*→ (\d+) fruits")


def _moy(field) -> float:
    """Valeur moyenne d'un `GridField` sur la tuile."""
    return sum(sum(row) for row in field.data) / (field.rows * field.cols)


def _game_state(tiles, ecos, house) -> dict:
    """game_state minimal identique à celui du golden (pas de seed → défaut moteur)."""
    return {"tiles": tiles, "eco": ecos, "house": house, "scores": {},
            "current_player": "joueur_1", "week": 1, "log": []}


def _semaine(gs) -> tuple[int, int, str]:
    """(année, semaine-dans-l'année, saison) de la semaine QUI VA être simulée."""
    w = gs["week"]
    wiy = ((w - 1) % 52) + 1
    return (w - 1) // 52 + 1, wiy, saison_de(wiy)


def mesurer_smoke(n_ans: int) -> dict:
    """Déroule le monde smoke et collecte les indicateurs 1,2,5,6,7,8 + neige."""
    tiles, ecos = build_world()
    gs = _game_state(tiles, ecos, House())
    engine = Engine(gs)
    an_ = defaultdict(lambda: {"temps": [], "tomates": [], "absc": None})
    sai = defaultdict(lambda: {"gel": 0, "neige": 0, "hum": [], "carpo": Counter()})
    tomates_vivantes: set = set()
    for _ in range(n_ans * 52):
        an, wiy, saison = _semaine(gs)
        event = weather_state(gs["seed"], gs["week"])[0]   # seed posé par Engine
        log = engine.tick_semaine()
        A, S = an_[an], sai[(an, saison)]
        t_air = ecos[tiles[0].tile_id].temperature.data[0][0]   # T_air uniforme
        A["temps"].append((t_air, wiy, saison))
        S["gel"] += t_air < 0.0
        S["neige"] += event.kind == "Neige"
        S["hum"].append(median(v for e in ecos.values() for row in e.humidite.data
                               for v in row))
        for line in log:
            if A["absc"] is None and _RE_ABSC.search(line):
                A["absc"] = (wiy, t_air)                             # 8. abscission
        # 5. Tomates : semaine de disparition (morte ou retirée) de chaque individu.
        vivantes = {id(p) for t in tiles for p in t.plants
                    if p.is_alive and p.plant_class.__name__ == "Tomato"}
        for _mort in tomates_vivantes - vivantes:
            A["tomates"].append((wiy, saison))
        tomates_vivantes = vivantes
        A["tomates_fin"] = len(vivantes)
        gs["log"].clear()
        # 7. Carpophores : échantillonnés comme le snapshot (horloge post-tick).
        an_c, _wc, saison_c = _semaine(gs)
        if an_c <= n_ans:
            for tile in tiles:
                for k in carpophores_tuile(gs, tile)[0]:
                    sai[(an_c, saison_c)]["carpo"][k.espece] += 1
    return {"an": an_, "sai": sai, "seed": gs["seed"]}


def mesurer_pommier(n_ans: int) -> dict:
    """Banc `floraison_saisons` : ouverture florale du pommier (armée 1×/an, remise
    à zéro en s1), recouvrement fleur ouverte × butineurs sur la tuile, fruits noués
    (lignes « 🍎 Nouaison Pommier » du log)."""
    gs, engine, plants, eco = monde_floraison()
    pom = dict(plants)["AppleTree"]
    res = defaultdict(lambda: {"bloom": None, "flo": [], "fruits": 0})
    for _ in range(n_ans * 52):
        an, _wiy, _s = _semaine(gs)
        log = engine.tick_semaine()
        gs["log"].clear()
        R = res[an]
        if pom.is_alive and pom.bloom_week >= 0 and R["bloom"] is None:
            R["bloom"] = pom.bloom_week
        if pom.is_alive and pom.floraison >= 0.5:
            dens = sum(_moy(eco.populations[n]) for n in POLLINATOR_NAMES
                       if eco.populations and n in eco.populations)
            R["flo"].append(dens >= SEUIL_BUTINEURS)
        for line in log:
            m = _RE_NOUAISON_POMMIER.search(line)
            if m:
                R["fruits"] += int(m.group(1))
    return res


def mesurer_glace(n_ans: int) -> dict:
    """Banc `tourbiere` : semaines où `eco.glace` > 0 sur au moins un plot."""
    tiles, ecos, house, _banque = BANCS["tourbiere"]()
    gs = _game_state(tiles, ecos, house)
    engine = Engine(gs)
    glace = Counter()
    for _ in range(n_ans * 52):
        an, _wiy, saison = _semaine(gs)
        engine.tick_semaine()
        gs["log"].clear()
        if any(e.glace is not None and any(v > 0.0 for row in e.glace.data for v in row)
               for e in ecos.values()):
            glace[(an, saison)] += 1
    return glace


def _fmt_t(item) -> str:
    t, wiy, saison = item
    return f"{t:+.1f} °C s{wiy} ({saison})"


def rapport(n_ans: int) -> str:
    sm = mesurer_smoke(n_ans)
    po = mesurer_pommier(n_ans)
    gl = mesurer_glace(n_ans)
    wl = max(range(1, 53), key=daylength)
    out = [f"## Calendrier — monde smoke (seed moteur 0x{sm['seed']:X}) + banc "
           f"floraison_saisons (pommier) + banc tourbière (glace), {n_ans} an(s)\n",
           f"Jour le plus long (`daylength`, pur) : s{wl} ({saison_de(wl)}), "
           f"{daylength(wl):.1f} h — identique chaque année.\n",
           "### Par année\n",
           "| an | T min | T max | pommier bloom_week | recouvrement fleur×butineurs "
           "| fruits noués pommier | tomates disparues (semaine) | tomates vivantes fin "
           "| 1ʳᵉ abscission (T) |",
           "|---|---|---|---|---|---|---|---|---|"]
    for an in range(1, n_ans + 1):
        A, P = sm["an"][an], po[an]
        bloom = (f"s{P['bloom']} ({saison_de(P['bloom'])})" if P["bloom"] is not None
                 else "pas de floraison")
        rec = (f"{sum(P['flo'])}/{len(P['flo'])} sem." if P["flo"]
               else "aucune sem. floraison ≥ 0,5")
        tom = ", ".join(f"s{w} ({s})" for w, s in A["tomates"]) or "aucune"
        absc = (f"s{A['absc'][0]} ({A['absc'][1]:+.1f} °C)" if A["absc"]
                else "aucune")
        out.append(f"| {an} | {_fmt_t(min(A['temps']))} | {_fmt_t(max(A['temps']))} "
                   f"| {bloom} | {rec} | {P['fruits']} | {tom} | {A['tomates_fin']} "
                   f"| {absc} |")
    out += ["\n### Par année × saison étiquetée\n",
            "| an | saison | sem. gel (T_air<0) | sem. neige | sem. glace (tourbière) "
            "| humidité sol médiane | carpophores (échantillons cumulés, par espèce) |",
            "|---|---|---|---|---|---|---|"]
    for an in range(1, n_ans + 1):
        for s in SAISONS:
            S = sm["sai"][(an, s)]
            carpo = ", ".join(f"{k} {v}" for k, v in sorted(S["carpo"].items())) or "—"
            hum = f"{median(S['hum']):.3f}" if S["hum"] else "—"
            out.append(f"| {an} | {s} | {S['gel']} | {S['neige']} | {gl[(an, s)]} "
                       f"| {hum} | {carpo} |")
    return "\n".join(out)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else N_ANS_MAX
    if not 1 <= n <= N_ANS_MAX:
        sys.exit(f"n_ans ∈ [1, {N_ANS_MAX}] (garde-fou du sprint D122)")
    print(rapport(n))
