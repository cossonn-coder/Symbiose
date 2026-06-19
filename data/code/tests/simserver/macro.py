"""
SYMBIOSE — tests/simserver/macro.py
Section 10 : vie macro (tranche 6·B). Bloc `sprites` au snapshot, par tuile et
par guilde, tableaux compacts [r, c, x_frac, y_frac, activite] issus de
sample_sprites (PUR, déterministe). Forme et bornes (cap 4/plot/guilde, fracs
∈ [0,1]), démarrage à zéro, émergence estivale, positions STABLES, lecture sans
effet de bord.
"""
import json

from .harness import check, ServerProc


def test_vie_macro():
    print("[vie macro]")
    GUILDES = {"puceron", "limace", "doryphore",
               "coccinelle", "chrysope", "carabe", "merle", "herisson",
               "abeille", "syrphe", "papillon", "bourdon", "osmie",
               "lombric", "cloporte"}
    s10 = ServerProc()
    r = s10.send(cmd="init", seed=42)
    snap = s10.send(cmd="snapshot")["snapshot"]
    spr = snap.get("sprites", {})
    check("bloc sprites présent, indexé par tuile",
          set(spr.keys()) == {t["id"] for t in r["world"]["tiles"]},
          f"tuiles={sorted(spr.keys())}")
    check("les 15 espèces par tuile (3 ravageurs + 5 auxiliaires + 5 pollinisateurs + 2 vers)",
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
