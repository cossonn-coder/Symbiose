#!/usr/bin/env python3
"""mesure_da — banc de MESURE de la grammaire 16 bits sur les PNG du banc de capture.

Outil *du dépôt* (pas du moteur ; sprint CASSÉ À L'ÉCRAN ①). Il transforme la
checklist du brief (`docs/rendu/pixelart/etude_brief_da_16bits.md`) en CHIFFRES,
pour que les tronçons de rendu ③→⑥ se valident seuls ; le F5 de Nico ne juge plus
que le ressenti. Lecture seule, déterministe, sans dépendance (cf. `da_image.py`).

ISOLER LES SPRITES — deux modes :
  --ref REF.png  (mode monde) : REF est la MÊME capture (même banc, seed, zoom,
      centre, nombre d'images) avec la couche des plantes masquée
      (`capture_vm.sh … -x Objects,…`). Tout pixel qui diffère appartient à un
      objet ; on retire ceux qui ne sont qu'un ASSOMBRISSEMENT uniforme du sol
      (= ombre portée) pour ne garder que les sprites.
  sans --ref (mode planche) : le fond est la couleur la plus fréquente de l'image
      (fond uni de la planche du kit, `capture_vm.sh -k`).
Chaque composante connexe du masque = un sprite (deux plantes qui se touchent
fusionnent : le rapport le dit par leur taille).

MESURES par sprite (pixels LOGIQUES, `--pas 2` par défaut) :
  tons      couleurs distinctes (brut : > 5 = fondu non indexé) / tons « qui se lisent »
            (regroupés à ΔE OKLab < 0,03, couvrant ≥ max(2 px, 1 %) du sprite)
  noir      % de #000 exact / % de quasi-noirs neutres (seuils : da_image.py)
  contour   % des pixels de BORD de silhouette quasi-noirs (contour noir sur masse)
  derive    teinte HSV du quartile sombre → quartile clair, et l'écart à 60° (jaune)
            gagné par l'éclat : > 0 = « l'éclat va vers le jaune » (règle 3)
  aplat     plus grande zone connexe d'UNE seule couleur à l'intérieur du sprite
  eclat     angle écran (0° = droite, 90° = haut) du barycentre des pixels les plus
            clairs vu du centre du sprite, et cos avec la direction du soleil
puis, sur l'image : VOISINS identiques (paires de sprites de même gabarit).

Usage :
    python3 tools/mesure_da.py IMG.png [--ref REF.png] [--soleil 135] [--pas 2]
    python3 tools/mesure_da.py planche/*.png        # mode planche, plusieurs images
    python3 tools/mesure_da.py --charte visuals/RampesDa.cs   # contrôle de la table
"""

import argparse
import math
import sys
from collections import Counter, deque

from da_image import ecart_angle, hsv, lire_png, oklab, quasi_noir, rgb

# ── Seuils documentés (chaque seuil = une ligne de rationale) ──────────────
DIFF_MIN = 24          # Σ|ΔRGB| : sous ce seuil deux pixels sont « le même » (bruit d'encodage, lueurs).
OMBRE_K = (0.45, 0.97) # ombre = sol × k : PlantShadow (noir α 0,18) donne k ≈ 0,82 ; marge large.
OMBRE_RESIDU = 8       # |p − k·q| max par canal : une ombre TEINTÉE (#071010 à α) reste sous 8.
TAILLE_MIN = 40        # px logiques : sous ~3 motifs 3×4 du brief, un sprite ne se mesure pas.
TON_LISIBLE = 0.01     # part du sprite : un ton qui couvre < 1 % (ou < 2 px) ne « se lit » pas (lueur, fondu).
TON_DE = 0.03          # ΔE OKLab : 2 couleurs plus proches = UN ton (seuil de discernement ≈ 0,02 ;
                       # les crans du brief valent ≥ 0,05 de L) — absorbe le bruit de fondu ±2/255.
APLAT_MAX = 24         # px logiques : 2 motifs du brief (feuille 3×4) — au-delà, c'est un aplat.
ECLAT_QUANTILE = 0.95  # « ton le plus clair » = les 5 % de pixels les plus clairs (≥ 1 px).
SAT_MIN = 0.08         # sous cette saturation HSV la teinte n'est pas définie (gris) → « n/d ».
DERIVE_MIN = 3.0       # degrés : ±10 % de quantification du brief ; au-dessus, la dérive est réelle.
GABARIT = 0.20         # voisins comparés si largeur ET hauteur diffèrent de ≤ 20 %.
IDENTIQUE = 0.02       # voisins « identiques » si < 2 % des pixels de l'union diffèrent.


def masque_ref(pix, ref):
    """Mode monde : pixels qui diffèrent de la référence, ombres portées retirées."""
    m = bytearray(len(pix))
    for i, (p, q) in enumerate(zip(pix, ref)):
        if p == q:
            continue
        pr, qr = rgb(p), rgb(q)
        if sum(abs(a - b) for a, b in zip(pr, qr)) < DIFF_MIN:
            continue
        sq = sum(qr)
        k = sum(pr) / sq if sq else 0.0
        if OMBRE_K[0] <= k <= OMBRE_K[1] and all(abs(a - k * b) <= OMBRE_RESIDU for a, b in zip(pr, qr)):
            continue                                   # assombrissement uniforme = ombre
        m[i] = 1
    return m


def masque_fond(pix):
    """Mode planche : tout ce qui n'est pas la couleur dominante (le fond uni)."""
    fond = Counter(pix).most_common(1)[0][0]
    return bytearray(0 if p == fond else 1 for p in pix)


def composantes(m, larg, haut, autorise=None):
    """Composantes 4-connexes de `m` (liste de listes d'indices). Si `autorise`
    (fonction indice → clé) est donnée, deux voisins ne se relient que s'ils ont
    la même clé (sert à l'aplat : même couleur)."""
    vu = bytearray(len(m))
    res = []
    for s in range(len(m)):
        if not m[s] or vu[s]:
            continue
        cle = autorise(s) if autorise else None
        file, comp = deque([s]), []
        vu[s] = 1
        while file:
            i = file.popleft()
            comp.append(i)
            x, y = i % larg, i // larg
            for j, ok in ((i - 1, x > 0), (i + 1, x < larg - 1), (i - larg, y > 0), (i + larg, y < haut - 1)):
                if ok and m[j] and not vu[j] and (autorise is None or autorise(j) == cle):
                    vu[j] = 1
                    file.append(j)
        res.append(comp)
    return res


def tons_lus(compte, n):
    """Tons qui « se lisent » : couleurs regroupées à ΔE < TON_DE (glouton, de la plus
    fréquente à la plus rare, ordre stable), groupes couvrant ≥ max(2 px, 1 %)."""
    centres, poids = [], []
    for c, v in sorted(compte.items(), key=lambda kv: (-kv[1], kv[0])):
        lab = oklab(c)
        for k, ce in enumerate(centres):
            if math.dist(lab, ce) < TON_DE:
                poids[k] += v
                break
        else:
            centres.append(lab)
            poids.append(v)
    return sum(1 for v in poids if v >= max(2, TON_LISIBLE * n))


def teinte_moyenne(couleurs):
    """Teinte HSV de la couleur MOYENNE d'un lot (None si quasi grise)."""
    n = len(couleurs)
    r = sum(rgb(c)[0] for c in couleurs) / n
    g = sum(rgb(c)[1] for c in couleurs) / n
    b = sum(rgb(c)[2] for c in couleurs) / n
    h, s, _ = hsv(r, g, b)
    return h if s >= SAT_MIN else None


def mesurer_sprite(comp, pix, larg, soleil):
    """Toutes les mesures d'UN sprite → dict."""
    ens = set(comp)
    cols = [pix[i] for i in comp]
    n = len(comp)
    compte = Counter(cols)
    xs = [i % larg for i in comp]
    ys = [i // larg for i in comp]
    cx, cy = sum(xs) / n, sum(ys) / n
    bord = [i for i in comp if any(j not in ens for j in (i - 1, i + 1, i - larg, i + larg))]
    qn = {c: quasi_noir(c) for c in compte}
    # Dérive : tri par clarté OKLab, quartiles sombre et clair.
    tri = sorted(comp, key=lambda i: oklab(pix[i])[0])
    q = max(1, n // 4)
    hs, hc = teinte_moyenne([pix[i] for i in tri[:q]]), teinte_moyenne([pix[i] for i in tri[-q:]])
    derive = None if hs is None or hc is None else ecart_angle(hs, 60.0) - ecart_angle(hc, 60.0)
    # Aplat : plus grande zone d'une seule couleur, sur l'intérieur (bord exclu).
    interieur = bytearray(len(pix))
    for i in ens.difference(bord):
        interieur[i] = 1
    zones = composantes(interieur, larg, len(pix) // larg, autorise=lambda i: pix[i])
    aplat = max((len(z) for z in zones), default=0)
    # Éclat : barycentre des pixels les plus clairs, vu du centre du sprite.
    k = max(1, int(round(n * (1 - ECLAT_QUANTILE))))
    clairs = tri[-k:]
    dx = sum(i % larg for i in clairs) / k - cx
    dy = cy - sum(i // larg for i in clairs) / k             # écran : y vers le bas → on inverse
    ang = math.degrees(math.atan2(dy, dx)) % 360.0 if (dx or dy) else None
    cos = None
    if ang is not None and soleil is not None:
        cos = math.cos(math.radians(ang - soleil))
    return {
        "n": n, "bbox": (min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1),
        "tons": len(compte), "tons_lus": tons_lus(compte, n),
        "noir": 100.0 * compte.get(0, 0) / n,
        "quasi_noir": 100.0 * sum(v for c, v in compte.items() if qn[c]) / n,
        "contour_noir": 100.0 * sum(1 for i in bord if qn[pix[i]]) / max(1, len(bord)),
        "h_sombre": hs, "h_clair": hc, "derive": derive,
        "aplat": aplat, "eclat_ang": ang, "eclat_cos": cos,
        "_pix": {i: pix[i] for i in comp},
    }


def distance_voisins(a, b, larg):
    """Part des pixels de l'union qui diffèrent (au-delà de DIFF_MIN), sprites
    calés sur leur PIED (bas-centre de la boîte englobante — là où la plante
    touche le sol), meilleur calage à ±1 px près."""
    def cale(s):
        x0, y0, w, h = s["bbox"]
        pied = (x0 + w // 2, y0 + h - 1)
        return {(i % larg - pied[0], i // larg - pied[1]): c for i, c in s["_pix"].items()}
    def proche(c1, c2):
        if c1 is None or c2 is None:
            return False
        return sum(abs(u - v) for u, v in zip(rgb(c1), rgb(c2))) < DIFF_MIN
    pa, pb = cale(a), cale(b)
    meilleure = 1.0
    for ox in (-1, 0, 1):                    # ±1 px : le pied tombe entre deux pixels
        for oy in (-1, 0, 1):
            pbo = {(x + ox, y + oy): c for (x, y), c in pb.items()}
            union = pa.keys() | pbo.keys()
            d = sum(1 for p in union if not proche(pa.get(p), pbo.get(p))) / len(union)
            meilleure = min(meilleure, d)
    return meilleure


def voisins(sprites, larg):
    """Distances des paires de même gabarit (proxy de « même espèce »)."""
    d = []
    for i, a in enumerate(sprites):
        for b in sprites[i + 1:]:
            (_, _, wa, ha), (_, _, wb, hb) = a["bbox"], b["bbox"]
            if abs(wa - wb) <= GABARIT * max(wa, wb) and abs(ha - hb) <= GABARIT * max(ha, hb):
                d.append(distance_voisins(a, b, larg))
    return d


def _f(v, fmt="{:.1f}"):
    return "n/d" if v is None else fmt.format(v)


def mediane(v):
    v = sorted(x for x in v if x is not None)
    return None if not v else (v[len(v) // 2] if len(v) % 2 else (v[len(v) // 2 - 1] + v[len(v) // 2]) / 2)


def rapport(nom, sprites, dist, soleil):
    """Imprime le rapport texte d'une image."""
    print(f"== {nom} : {len(sprites)} sprite(s)  [soleil {_f(soleil, '{:.0f}°')}]")
    print("  #    px  boîte(x,y,l,h)       tons lus noir% qnoir% contour% h_somb h_clair derive aplat eclat° cos")
    for k, s in enumerate(sprites):
        x, y, w, h = s["bbox"]
        print(f"  {k:<3}{s['n']:>5}  ({x:>3},{y:>3},{w:>3},{h:>3})  {s['tons']:>6}{s['tons_lus']:>5}"
              f"{s['noir']:>6.1f}{s['quasi_noir']:>7.1f}{s['contour_noir']:>9.1f}"
              f"{_f(s['h_sombre'], '{:>7.0f}'):>7}{_f(s['h_clair'], '{:>8.0f}'):>8}{_f(s['derive'], '{:>7.1f}'):>7}"
              f"{s['aplat']:>6}{_f(s['eclat_ang'], '{:>6.0f}'):>6}{_f(s['eclat_cos'], '{:>6.2f}'):>6}")
    if not sprites:
        return
    ok_der = [s for s in sprites if s["derive"] is not None]
    print(f"  SYNTHÈSE  tons lus méd {_f(mediane([s['tons_lus'] for s in sprites]), '{:.0f}')}"
          f" (> 6 : {sum(s['tons_lus'] > 6 for s in sprites)}/{len(sprites)})"
          f" · qnoir méd {_f(mediane([s['quasi_noir'] for s in sprites]))} %"
          f" · contour noir méd {_f(mediane([s['contour_noir'] for s in sprites]))} %"
          f" · dérive méd {_f(mediane([s['derive'] for s in sprites]))}° (> {DERIVE_MIN:.0f}° : "
          f"{sum(s['derive'] > DERIVE_MIN for s in ok_der)}/{len(ok_der)})"
          f" · aplat méd {_f(mediane([s['aplat'] for s in sprites]), '{:.0f}')} px (> {APLAT_MAX} : "
          f"{sum(s['aplat'] > APLAT_MAX for s in sprites)}/{len(sprites)})"
          + ("" if soleil is None else
             f" · éclat côté soleil (cos > 0) {sum((s['eclat_cos'] or -1) > 0 for s in sprites)}/{len(sprites)}"))
    if dist:
        print(f"  VOISINS  {len(dist)} paire(s) de même gabarit · distance min {min(dist):.3f}"
              f" méd {mediane(dist):.3f} · identiques (< {IDENTIQUE}) : {sum(d < IDENTIQUE for d in dist)}")


def charte(chemin):
    """Contrôle la table des rampes C# (`visuals/RampesDa.cs`, ①) : relit chaque
    rampe LITTÉRALE `["matière"] = Hex("…", …)` et vérifie la discipline du brief —
    ≤ 5 tons (6 avec éclat isolé), aucun quasi-noir, clarté croissante, dérive de
    teinte vers le jaune. Les rampes DÉRIVÉES (Deriver, calculées au jeu) ne sont
    pas relues ici : leurs garanties sont construites (anti-noir, base inchangée)."""
    import re
    motif = re.compile(r'\["(\w+)"\]\s*=\s*Hex\(([^)]*)\)')
    defauts = 0
    with open(chemin, encoding="utf-8") as f:
        for nom, args in motif.findall(f.read()):
            tons = [int(h, 16) for h in re.findall(r'"([0-9a-fA-F]{6})"', args)]
            L = [oklab(c)[0] for c in tons]
            hs, hc = (teinte_moyenne([c]) for c in (tons[0], tons[-1]))
            der = None if hs is None or hc is None else ecart_angle(hs, 60.0) - ecart_angle(hc, 60.0)
            ko = [m for m, bad in (("> 6 tons", len(tons) > 6), ("quasi-noir", any(map(quasi_noir, tons))),
                                   ("clarté non croissante", L != sorted(L))) if bad]
            defauts += len(ko)
            print(f"  {nom:<15}{len(tons):>2} tons  L {L[0]:.2f}→{L[-1]:.2f}  dérive {_f(der)}°"
                  f"  {'OK' if not ko else 'KO : ' + ', '.join(ko)}")
    print(f"  CHARTE  {defauts} défaut(s)")
    return 1 if defauts else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("images", nargs="*")
    ap.add_argument("--charte", help="contrôle la table des rampes C# (visuals/RampesDa.cs) au lieu d'images")
    ap.add_argument("--ref", help="capture de référence, couche des plantes masquée (mode monde)")
    ap.add_argument("--soleil", type=float, default=135.0,
                    help="direction ÉCRAN vers le soleil, degrés (0 = droite, 90 = haut) ; "
                         "défaut 135 = haut-gauche du brief")
    ap.add_argument("--pas", type=int, default=2, help="sous-échantillonnage (2 = pixel logique du banc)")
    ap.add_argument("--zone", help="x0,y0,x1,y1 en px ÉCRAN : ne mesure que ce rectangle (exclut le HUD)")
    a = ap.parse_args(argv)
    if a.charte:
        return charte(a.charte)
    ref = lire_png(a.ref, a.pas)[2] if a.ref else None
    for chemin in a.images:
        larg, haut, pix = lire_png(chemin, a.pas)
        m = masque_ref(pix, ref) if ref is not None else masque_fond(pix)
        if a.zone:
            x0, y0, x1, y1 = (int(v) // a.pas for v in a.zone.split(","))
            for i in range(len(m)):
                if not (x0 <= i % larg < x1 and y0 <= i // larg < y1):
                    m[i] = 0
        comps = [c for c in composantes(m, larg, haut) if len(c) >= TAILLE_MIN]
        comps.sort(key=lambda c: (min(c) // larg, min(c) % larg))   # ordre de lecture, stable
        sprites = [mesurer_sprite(c, pix, larg, a.soleil) for c in comps]
        rapport(chemin, sprites, voisins(sprites, larg), a.soleil)
    return 0


if __name__ == "__main__":
    sys.exit(main())
