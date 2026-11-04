#!/usr/bin/env python3
"""mesure_silhouettes — les 40 espèces se ressemblent-elles encore à l'écran ?

Outil *du dépôt* (pas du moteur ; sprint FORMES DES PLANTES ①). Il capture le banc
`planche_especes` puis compare les sprites deux à deux, pour que les tronçons de
rendu se valident par la mesure ; le F5 de Nico ne juge que le ressenti. Sans
dépendance : réutilise `da_image.py` et le masque de `mesure_da.py --ref`.

  capturer DOSSIER   une paire de PNG par espèce et par palier (avec / sans plantes)
  mesurer  DOSSIER   descripteurs par espèce, paires confondues (Markdown sur stdout)

📖 Pédagogie — isoler UN sprite
  Le banc de capture cadre chaque pied au centre, mais ses voisins restent dans
  l'image. On retire le fond par différence avec la capture sans plantes (`-x
  Objects`), puis chaque tache connexe du masque va à la plante dont l'AXE (segment
  vertical du pied à sa hauteur) est le plus proche. Une feuille détachée de sa
  tige reste ainsi rattachée à son pied, et un voisin n'est jamais compté.

📖 Pédagogie — comparer deux silhouettes de tailles différentes
  Le recouvrement se calcule sur le masque ramené à la boîte englobante (grille
  CELLULES×CELLULES, chaque case = part de pixels pleins), puis Σmin/Σmax (un IoU
  « doux », qui ne dépend pas de la résolution : il vaut à ×1 comme à ×4). Il dit si
  les FORMES se superposent ; le gabarit, lui, compare les tailles absolues. À ×1 un
  sprite fin fait 8 px de large : un décalage d'un pixel y ruinerait une grille 16×16,
  d'où une grille plus grossière à ce palier (GRILLE_PAR_ZOOM).

Déterministe : aucune horloge, aucun aléa ; capture à graine, vent et images fixes.
Usage :
    python3 tools/mesure_silhouettes.py capturer /tmp/planche [--zoom 1 4] [--jobs 4]
    python3 tools/mesure_silhouettes.py mesurer  /tmp/planche [--zoom 1 4] > avant.md
"""

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import threading
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

from da_image import lire_png, oklab, rgb
from mesure_da import composantes, masque_ref

OUTILS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(OUTILS, "..", "data", "code"))

# ── Seuils de la paire confondue (conception_formes_plantes §6) ────────────
GABARIT_MAX = 0.15     # largeur et hauteur à 15 % près [choix].
PROPORTION_MAX = 0.15  # hauteur/largeur à 15 % près [choix].
RECOUVREMENT_MIN = 0.7 # formes superposées à plus de 70 % [choix].
DELTA_E_MAX = 0.05     # teinte moyenne, ΔE OKLab : ≈ 2× le seuil de discernement (0,02) [choix].
HAUTEUR_REL = 0.20     # hauteur dessinée à ±20 % de height_cm…
HAUTEUR_ABS_CM = 15.0  # …ou ±15 cm sous 75 cm : la boîte d'un pied bas compte sa nappe au sol [choix].

# ── Géométrie de la vue (world/WorldView.Projection.cs) ────────────────────
PX_CM = 0.39           # PxPerCmX = PxPerCmZ, en px internes par cm.
PX_CM_Y = 0.195        # PxPerCmY.
LARG, HAUT = 960, 540  # pixels logiques (monde rendu en 960×540, agrandi ×2).
AXE_MAX_CM = 180.0     # l'axe s'arrête sous le pied du voisin de diagonale (2 m derrière).
CELLULES = 16          # grille de comparaison des formes.
GRILLE_PAR_ZOOM = {1.0: 4}  # ×1 : cases de 2-3 px, absorbent le décalage d'un pixel (recalibré, ①).
BANC = "planche_especes"
# Hors du cadre de toute plante, sinon le survol dessine une étiquette sur le pied.
SOURIS = "1900,1070"
COUCHES = "Weather,MacroLife,House"
IMAGES = 3             # suffit : les sprites sont stables dès la 3ᵉ image [vérifié à ×4, n=1].


def table_especes():
    """{espèce : (x_cm, y_cm, height_cm)} du banc, lue dans sa fabrique."""
    from bancs.planche_especes import POSITIONS, composer
    par_pied = {pos: nom for nom, pos in POSITIONS.items()}
    table = {}
    for tuile in composer(forcer=False)[0]:
        for p in tuile.plants:
            pied = (round(tuile.origin_x_cm + p.x_cm), round(tuile.origin_y_cm + p.y_cm))
            table[par_pied[pied]] = (pied[0], pied[1], p.current_height)
    return table


def cadrage(h_cm):
    """Recul du point visé le long de la diagonale nord, en cm : le pied descend à
    l'écran d'une demi-hauteur et la plante entière tient au cadre à ×4."""
    return h_cm / 2.0


def pied_ecran(x, y, centre, zoom):
    """Pied (x, y) en pixels logiques d'une image cadrée sur `centre` à `zoom`."""
    dx, dy = x - centre[0], y - centre[1]
    return (LARG / 2 + zoom * (dx - dy) * PX_CM, HAUT / 2 + zoom * (dx + dy) * PX_CM_Y)


def centre_de(x, y, h_cm):
    return x - cadrage(h_cm), y - cadrage(h_cm)


# ─────────────────────────────── Capture ──────────────────────────────────

def _capturer_une(args):
    """Une image (`suffixe` t = avec plantes, r = sans) d'une espèce à un palier."""
    tache, ecran = args
    dossier, espece, zoom, (x, y, h), suffixe = tache
    sortie = os.path.join(dossier, f"x{zoom:g}", espece)
    os.makedirs(sortie, exist_ok=True)
    tmp = os.path.join(sortie, f"tmp_{suffixe}")
    cx, cy = centre_de(x, y, h)
    cacher = COUCHES + (",Objects" if suffixe == "r" else "")
    subprocess.run([os.path.join(OUTILS, "capture_vm.sh"), "--no-build", "-b", BANC, "-w", "0",
                    "-z", f"{zoom:g}", "-c", f"{cx:g},{cy:g}", "-v", "0", "-O", "-x", cacher,
                    "-s", SOURIS, "-n", str(IMAGES), "-o", tmp],
                   check=True, stdout=subprocess.DEVNULL,
                   env={**os.environ, "CAPTURE_DISPLAY": str(ecran)})
    shutil.move(os.path.join(tmp, f"frame{IMAGES - 1:08d}.png"),
                os.path.join(sortie, f"{suffixe}.png"))
    shutil.rmtree(tmp)
    return f"{espece} ×{zoom:g} {suffixe}"


def capturer(dossier, zooms, jobs, especes):
    """Lance les captures en parallèle, chaque Godot sur son écran Xvfb. Le build C#
    reste à faire avant (`dotnet build`) : `--no-build` évite qu'ils se le disputent."""
    table = table_especes()
    taches = [(dossier, e, z, table[e], s)
              for z in zooms for e in (especes or sorted(table)) for s in "tr"]
    # Un écran par fil : chaque fil de la réserve prend le sien et le garde.
    local, restants = threading.local(), [100 + i for i in range(jobs)]

    def lance(tache):
        if not hasattr(local, "ecran"):
            local.ecran = restants.pop()
        return _capturer_une((tache, local.ecran))

    with ThreadPoolExecutor(jobs) as pool:
        for fait in pool.map(lance, taches):
            print(fait, file=sys.stderr)


# ──────────────────────────── Descripteurs ────────────────────────────────

def _distance_axe(px, py, pied, haut_px):
    """Distance du point au segment vertical pied → pied − haut_px."""
    y = min(pied[1], max(pied[1] - haut_px, py))
    return math.hypot(px - pied[0], py - y)


def _isoler(masque, espece, centre, zoom, table):
    """Pixels des taches dont l'axe le plus proche est celui de `espece`."""
    axes = []
    for nom, (x, y, h) in table.items():
        axes.append((nom, pied_ecran(x, y, centre, zoom), zoom * PX_CM * min(h, AXE_MAX_CM)))
    garde = []
    for comp in composantes(masque, LARG, HAUT):
        cx = sum(i % LARG for i in comp) / len(comp)
        cy = sum(i // LARG for i in comp) / len(comp)
        proche = min(axes, key=lambda a: (_distance_axe(cx, cy, a[1], a[2]), a[0]))
        if proche[0] == espece:
            garde.extend(comp)
    return garde


def decrire(args):
    """Descripteurs d'un sprite : boîte, teinte moyenne OKLab, grille normalisée."""
    dossier, espece, zoom, table = args
    x, y, h = table[espece]
    d = os.path.join(dossier, f"x{zoom:g}", espece)
    _, _, pix = lire_png(os.path.join(d, "t.png"), 2)
    _, _, ref = lire_png(os.path.join(d, "r.png"), 2)
    px = _isoler(masque_ref(pix, ref), espece, centre_de(x, y, h), zoom, table)
    if not px:
        return espece, {"vide": True, "height_cm": h}
    xs, ys = [i % LARG for i in px], [i // LARG for i in px]
    x0, y0 = min(xs), min(ys)
    w, ht = max(xs) - x0 + 1, max(ys) - y0 + 1
    labs = [oklab(pix[i]) for i in px]
    plein = [[0] * CELLULES for _ in range(CELLULES)]
    for xi, yi in zip(xs, ys):
        plein[(yi - y0) * CELLULES // ht][(xi - x0) * CELLULES // w] += 1
    # Part de pixels pleins par case (aire d'une case = w·ht / CELLULES², min 1 px).
    aire = max(1.0, w * ht / CELLULES ** 2)
    grille = [min(1.0, v / aire) for ligne in plein for v in ligne]
    return espece, {
        "largeur": w, "hauteur": ht, "pixels": len(px), "height_cm": h,
        "hauteur_cm": ht / (zoom * PX_CM),
        "lab": [sum(c[k] for c in labs) / len(labs) for k in range(3)],
        "couleur": "#%02x%02x%02x" % tuple(
            round(sum(rgb(pix[i])[k] for i in px) / len(px)) for k in range(3)),
        "grille": [round(v, 3) for v in grille],
    }


def descripteurs(dossier, zoom, jobs):
    """Descripteurs d'un palier, recalculés une seule fois (lire un PNG en Python pur
    prend ~10 s [VM chargée, n=1]) : recalibrer un seuil ne relit aucune image."""
    cache = os.path.join(dossier, f"descripteurs_x{zoom:g}.json")
    if os.path.exists(cache):
        with open(cache, encoding="utf-8") as f:
            return json.load(f)
    table = table_especes()
    # Un dossier partiel se mesure aussi : seules les espèces capturées comptent.
    presentes = [e for e in sorted(table)
                 if os.path.exists(os.path.join(dossier, f"x{zoom:g}", e, "r.png"))]
    with ProcessPoolExecutor(jobs) as pool:
        res = dict(pool.map(decrire, [(dossier, e, zoom, table) for e in presentes]))
    with open(cache, "w", encoding="utf-8") as f:
        json.dump(res, f, sort_keys=True)
    return res


# ─────────────────────────────── Paires ───────────────────────────────────

def _ecart(a, b):
    return abs(a - b) / max(a, b, 1e-9)


def reduire(g, n):
    """Grille CELLULES² ramenée à n² par moyenne (n divise CELLULES)."""
    k = CELLULES // n
    r = [0.0] * (n * n)
    for y in range(CELLULES):
        for x in range(CELLULES):
            r[(y // k) * n + x // k] += g[y * CELLULES + x] / (k * k)
    return r


def recouvrement(g1, g2):
    """IoU doux de deux grilles normalisées (cf. en-tête)."""
    somme_max = sum(max(a, b) for a, b in zip(g1, g2))
    return sum(min(a, b) for a, b in zip(g1, g2)) / somme_max if somme_max else 0.0


def comparer(d1, d2, n=CELLULES):
    """Écarts d'une paire : gabarit (pire de largeur, hauteur), proportions,
    recouvrement, ΔE."""
    return {
        "gabarit": max(_ecart(d1["largeur"], d2["largeur"]), _ecart(d1["hauteur"], d2["hauteur"])),
        "proportion": _ecart(d1["hauteur"] / d1["largeur"], d2["hauteur"] / d2["largeur"]),
        "recouvrement": recouvrement(reduire(d1["grille"], n), reduire(d2["grille"], n)),
        "delta_e": math.dist(d1["lab"], d2["lab"]),
    }


def paires(desc, seuils, n=CELLULES):
    """Toutes les paires, triées de la plus confondue à la moins, `confondue` posé."""
    noms = sorted(n for n, d in desc.items() if not d.get("vide"))
    res = []
    for i, a in enumerate(noms):
        for b in noms[i + 1:]:
            c = comparer(desc[a], desc[b], n)
            c.update(a=a, b=b, confondue=(
                c["gabarit"] <= seuils["gabarit"] and c["proportion"] <= seuils["proportion"]
                and c["recouvrement"] > seuils["recouvrement"]
                and c["delta_e"] < seuils["delta_e"]))
            res.append(c)
    return sorted(res, key=lambda c: (not c["confondue"], -c["recouvrement"], c["a"], c["b"]))


# ─────────────────────────────── Rapport ──────────────────────────────────

def _ligne(*cols):
    return "| " + " | ".join(str(c) for c in cols) + " |"


def hauteur_tenue(d):
    """Hauteur dessinée dans la tolérance (conception §6, recalibrée au ①)."""
    return abs(d["hauteur_cm"] - d["height_cm"]) <= max(HAUTEUR_REL * d["height_cm"], HAUTEUR_ABS_CM)


def rapport(zoom, desc, seuils, n_paires):
    lim = f"[seed 42, n=1 capture, VM, ×{zoom:g}]"
    print(f"\n## Palier ×{zoom:g}\n")
    print(_ligne("espèce", f"boîte l×h px {lim}", f"hauteur dessinée cm {lim}", "height_cm",
                 f"dessinée / height_cm {lim}", f"couleur moyenne {lim}"))
    print(_ligne(*["---"] * 6))
    for nom, d in sorted(desc.items()):
        if d.get("vide"):
            print(_ligne(nom, "vide", "-", f"{d['height_cm']:.0f}", "-", "-"))
            continue
        print(_ligne(nom, f"{d['largeur']}×{d['hauteur']}", f"{d['hauteur_cm']:.0f}",
                     f"{d['height_cm']:.0f}", f"{d['hauteur_cm'] / d['height_cm']:.2f}",
                     d["couleur"]))
    hors = [n for n, d in sorted(desc.items()) if not d.get("vide") and not hauteur_tenue(d)]
    print(f"\n**Hauteur hors tolérance {lim} : {len(hors)} sur {len(desc)}** ({', '.join(hors)}).")
    liste = paires(desc, seuils, GRILLE_PAR_ZOOM.get(zoom, CELLULES))
    conf = [c for c in liste if c["confondue"]]
    touchees = {c[k] for c in conf for k in "ab"}
    print(f"\n**Paires confondues {lim} : {len(conf)} sur {len(liste)}.** Seuils : gabarit "
          f"≤ {seuils['gabarit']}, proportions ≤ {seuils['proportion']}, recouvrement > "
          f"{seuils['recouvrement']}, ΔE < {seuils['delta_e']}. Espèces dans au moins une paire : "
          f"{len(touchees)}.\n")
    print(f"Paires passant chaque critère seul {lim} : gabarit "
          f"{sum(c['gabarit'] <= seuils['gabarit'] for c in liste)}, proportions "
          f"{sum(c['proportion'] <= seuils['proportion'] for c in liste)}, recouvrement "
          f"{sum(c['recouvrement'] > seuils['recouvrement'] for c in liste)}, ΔE "
          f"{sum(c['delta_e'] < seuils['delta_e'] for c in liste)}.\n")
    print(_ligne("paire", f"gabarit {lim}", "proportions", "recouvrement", "ΔE", "confondue"))
    print(_ligne(*["---"] * 6))
    for c in liste[:n_paires or None]:
        print(_ligne(f"{c['a']} / {c['b']}", f"{c['gabarit']:.2f}", f"{c['proportion']:.2f}",
                     f"{c['recouvrement']:.2f}", f"{c['delta_e']:.3f}",
                     "oui" if c["confondue"] else "non"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("action", choices=("capturer", "mesurer"))
    ap.add_argument("dossier")
    ap.add_argument("--zoom", type=float, nargs="+", default=[1.0, 4.0])
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--especes", help="capturer : liste séparée par des virgules (défaut : toutes)")
    ap.add_argument("--paires", type=int, default=30, help="mesurer : lignes de paires à afficher, 0 = toutes")
    ap.add_argument("--gabarit", type=float, default=GABARIT_MAX)
    ap.add_argument("--proportion", type=float, default=PROPORTION_MAX)
    ap.add_argument("--recouvrement", type=float, default=RECOUVREMENT_MIN)
    ap.add_argument("--delta-e", type=float, default=DELTA_E_MAX)
    a = ap.parse_args(argv)
    if a.action == "capturer":
        capturer(a.dossier, a.zoom, a.jobs, a.especes.split(",") if a.especes else None)
        return
    seuils = {"gabarit": a.gabarit, "proportion": a.proportion,
              "recouvrement": a.recouvrement, "delta_e": a.delta_e}
    for z in a.zoom:
        rapport(z, descripteurs(a.dossier, z, a.jobs), seuils, a.paires)


if __name__ == "__main__":
    main()
