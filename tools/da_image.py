#!/usr/bin/env python3
"""da_image — lecture PNG + science des couleurs pour le banc de mesure DA.

Outil *du dépôt* (pas du moteur, sprint CASSÉ À L'ÉCRAN ①) : la moitié
« instrument » de `tools/mesure_da.py`. Deux responsabilités voisines, toutes
deux SANS dépendance (ni PIL ni numpy ne sont installés sur la VM, et un outil de
mesure ne doit pas dépendre du réseau) :

  1. décoder un PNG 8 bits RGB/RGBA (ceux du Movie Maker de Godot) avec la seule
     bibliothèque standard (`zlib` + `struct`) ;
  2. convertir une couleur sRGB en OKLab / HSV, et dire si elle est « quasi-noire
     neutre » (l'interdit n° 2 du brief DA).

📖 Pédagogie — un PNG, c'est quoi ?
  Une suite de « chunks » (longueur, type sur 4 lettres, données, CRC). `IHDR`
  donne largeur/hauteur/format ; les `IDAT` mis bout à bout forment UN flux zlib
  (deflate, comme un .zip). Décompressé, chaque ligne commence par un octet de
  FILTRE (0 à 4) : le PNG ne stocke pas les octets bruts mais leur différence avec
  un voisin (gauche, haut, moyenne, « Paeth »), plus compressible. On défait le
  filtre ligne par ligne — exactement comme un décodeur DPCM en embarqué.

Déterministe : aucune horloge, aucun aléa, aucun réseau.
"""

import math
import struct
import zlib


# ─────────────────────────────────────────────────────────────────────────
# 1. Décodage PNG
# ─────────────────────────────────────────────────────────────────────────

def _paeth(a, b, c):
    """Prédicteur Paeth (RFC 2083 §6.6) : le voisin (gauche a, haut b,
    haut-gauche c) le plus proche de a + b − c."""
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def _defiltrer(typ, ligne, prec, bpp):
    """Défait le filtre PNG d'UNE ligne (bytearray modifié en place).
    `prec` = ligne précédente déjà défiltrée (zéros pour la première)."""
    n = len(ligne)
    if typ == 0:
        return
    if typ == 1:                                   # Sub : + gauche
        for i in range(bpp, n):
            ligne[i] = (ligne[i] + ligne[i - bpp]) & 255
    elif typ == 2:                                 # Up : + haut
        for i in range(n):
            ligne[i] = (ligne[i] + prec[i]) & 255
    elif typ == 3:                                 # Average : + moyenne(gauche, haut)
        for i in range(n):
            g = ligne[i - bpp] if i >= bpp else 0
            ligne[i] = (ligne[i] + ((g + prec[i]) >> 1)) & 255
    elif typ == 4:                                 # Paeth
        for i in range(n):
            g = ligne[i - bpp] if i >= bpp else 0
            hg = prec[i - bpp] if i >= bpp else 0
            ligne[i] = (ligne[i] + _paeth(g, prec[i], hg)) & 255
    else:
        raise ValueError(f"filtre PNG inconnu : {typ}")


def lire_png(chemin, pas=1):
    """Lit un PNG 8 bits RGB(A) non entrelacé → (largeur, hauteur, pixels).

    `pixels` = liste plate d'entiers 0xRRGGBB, ligne par ligne (l'alpha est
    ignoré : le Movie Maker écrit des images opaques). `pas` = sous-échantillonnage
    (1 pixel gardé sur `pas` dans chaque direction) : le banc de capture rend le
    monde en 960×540 agrandi ×2 → `pas=2` retrouve le PIXEL LOGIQUE du jeu, celui
    où se comptent les tons et les motifs du brief.
    """
    with open(chemin, "rb") as f:
        donnees = f.read()
    if donnees[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{chemin} : pas un PNG")
    i, idat = 8, []
    larg = haut = canaux = 0
    while i < len(donnees):
        n, typ = struct.unpack(">I4s", donnees[i:i + 8])
        corps = donnees[i + 8:i + 8 + n]
        if typ == b"IHDR":
            larg, haut, prof, couleur, _, _, entrel = struct.unpack(">IIBBBBB", corps)
            if prof != 8 or couleur not in (2, 6) or entrel:
                raise ValueError(f"{chemin} : seul le PNG 8 bits RGB/RGBA non entrelacé est lu")
            canaux = 3 if couleur == 2 else 4
        elif typ == b"IDAT":
            idat.append(corps)
        elif typ == b"IEND":
            break
        i += 12 + n
    brut = zlib.decompress(b"".join(idat))
    pas_ligne = larg * canaux
    prec = bytearray(pas_ligne)
    pixels = []
    for y in range(haut):
        debut = y * (pas_ligne + 1)
        ligne = bytearray(brut[debut + 1:debut + 1 + pas_ligne])
        _defiltrer(brut[debut], ligne, prec, canaux)
        prec = ligne
        if y % pas:
            continue
        for x in range(0, larg, pas):
            k = x * canaux
            pixels.append((ligne[k] << 16) | (ligne[k + 1] << 8) | ligne[k + 2])
    return (larg + pas - 1) // pas, (haut + pas - 1) // pas, pixels


# ─────────────────────────────────────────────────────────────────────────
# 2. Couleurs : RGB → OKLab, HSV ; quasi-noir neutre
# ─────────────────────────────────────────────────────────────────────────
#
# 📖 OKLab (Björn Ottosson, 2020) : un espace où une même distance « se voit »
# pareil partout. L = clarté perçue (0 noir → 1 blanc) ; (a, b) = axes vert-rouge
# et bleu-jaune ; C = √(a²+b²) = chroma (« combien c'est coloré »). On l'utilise
# pour la CLARTÉ (trier les tons du sombre au clair) et la CHROMA (neutre ou non).
# La TEINTE, elle, se mesure en HSV : c'est l'espace des chiffres du brief
# (#115920 « à 133° »), pour qu'une dérive mesurée se compare au brief.

def rgb(c):
    """0xRRGGBB → (r, g, b) entiers 0-255."""
    return (c >> 16) & 255, (c >> 8) & 255, c & 255


def _lin(v):
    v /= 255.0
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def oklab(c):
    """0xRRGGBB → (L, a, b) OKLab."""
    r, g, b = (_lin(v) for v in rgb(c))
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def hsv(r, g, b):
    """(r, g, b) 0-255 (flottants admis) → (teinte en degrés, saturation 0-1, valeur 0-1)."""
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    if d == 0:
        return 0.0, 0.0, mx / 255.0
    if mx == r:
        h = ((g - b) / d) % 6
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return h * 60.0, d / mx, mx / 255.0


# Seuils du « quasi-noir neutre » (interdits n° 2-3 du brief : ni noir pur, ni
# ombre noire, ni contour noir). Rationale, valeurs mesurées en OKLab :
#  - L < 0.33 : couvre le gris foncé #303030 (L 0,31) et le contour maître actuel
#    `MaitreSombre` #2e3038 (L 0,31) ; au-delà, un ton n'est plus « noir » à l'œil.
#  - C/L < 0.07 : un sombre très foncé a mécaniquement peu de chroma, d'où un
#    critère RELATIF (chroma rapportée à la clarté). Le pixel le plus sombre
#    AUTORISÉ du brief, #071010 vert-noir, vaut C/L 0,085 → coloré, accepté ;
#    #2e3038 vaut 0,047 et le merle #1e1e22 0,032 → neutres, refusés.
QUASI_NOIR_L = 0.33
QUASI_NOIR_CL = 0.07


def quasi_noir(c):
    """Vrai si la couleur est noire ou un sombre neutre (cf. seuils ci-dessus)."""
    L, a, b = oklab(c)
    return L < QUASI_NOIR_L and math.hypot(a, b) < QUASI_NOIR_CL * max(L, 1e-6)


def ecart_angle(h1, h2):
    """Distance angulaire entre deux teintes (degrés, 0-180)."""
    d = abs(h1 - h2) % 360.0
    return 360.0 - d if d > 180.0 else d
