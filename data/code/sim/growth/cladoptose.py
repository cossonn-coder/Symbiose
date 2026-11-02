"""
SYMBIOSE — sim/growth/cladoptose.py
Mort de BRANCHES (D111 ②bis) — la partie STRUCTURELLE et PURE : quelles branches
latérales meurent, et la coupe elle-même. Aucun `eco` ici (couche growth) : c'est
`sim/engine/branches.py` qui décide QUAND (saison feuillée, tempête, neige) et fait
de la coupe de la litière `bois`.

Deux causes structurelles :
  1. CLADOPTOSE par l'ombre — une branche basse que la couronne prive de lumière
     coûte plus qu'elle ne rapporte : l'arbre la laisse mourir, elle tombe.
  2. CASSE mécanique (tempête, charge de neige) — la coupe vise de préférence les
     branches LONGUES et FINES (bras de levier), choix déterministe par hachage.

Pédagogie (Nico) : un ARBRE ici = liste de segments (parent → enfant). Une
« branche » = un sous-arbre LATÉRAL enraciné en un segment. On ne coupe JAMAIS le
collet ni l'AXE PORTEUR (le tronc + la flèche, suivi en prenant à chaque fourche
l'enfant le plus épais — pipe model : le plus épais porte le plus de bois).
Zéro RNG (philo #3) : tout aléa passe par `fields._hash_noise`.
"""

from __future__ import annotations
import math

from fields import _hash_noise
from .constantes import (CLADO_OPACITE_GRAPPE, CLADO_DZ_CM, CLADO_RAYON_CM,
                         CLADO_SEUIL, CLADO_AGE_MIN, CLADO_FENETRE)
from .geometrie import _tip, _children, _subtree, _rebuild, chemin_fleche


def axe_porteur(segs: list, ch: dict) -> set:
    """Indices du tronc + flèche : depuis le collet, on suit à chaque nœud l'enfant
    le plus ÉPAIS (à égalité, le plus petit indice = le plus ancien). Protégé de
    toute mort de branche (l'arbre ne s'étête pas tout seul). AUTOMNE VISIBLE ② : le
    chemin vers le point le plus haut l'est aussi. Le plus épais n'y mène pas toujours :
    une rafale ramenait un cerisier de 500 à 211 cm [seed 42, n=1, VM]."""
    axe, i = chemin_fleche(segs), 0
    while True:
        axe.add(i)
        if not ch[i]:
            return axe
        i = max(ch[i], key=lambda j: (segs[j].thickness_cm, -j))


def _pointes(segs: list, ch: dict) -> list:
    """Segments TERMINAUX (aucun enfant) = grappes de feuillage de la couronne."""
    return [i for i in range(len(segs)) if not ch[i]]


def lumiere_pointes(segs: list, ch: dict, l_plante: float,
                    densite: float) -> dict:
    """Lumière reçue à chaque pointe terminale ∈ [0,1] :
        l_plante × (1 − densite·OPACITE)^n_dessus
    `l_plante` = lumière reçue par la plante (ombre des VOISINS plus hauts, déjà
    calculée par LightField) ; `n_dessus` = nombre d'AUTRES pointes de la même
    plante plus hautes de > CLADO_DZ_CM dans un rayon horizontal CLADO_RAYON_CM
    (auto-ombrage de la couronne, que LightField exclut par construction).
    O(pointes²), pointes ≤ max_segments (~70) → borné."""
    pts = _pointes(segs, ch)
    tips = {i: _tip(segs[i]) for i in pts}
    transmis = 1.0 - densite * CLADO_OPACITE_GRAPPE
    r2 = CLADO_RAYON_CM * CLADO_RAYON_CM
    out = {}
    for i in pts:
        x, y, z = tips[i]
        n = 0
        for j in pts:
            if j == i:
                continue
            u = tips[j]
            if u[2] > z + CLADO_DZ_CM and (u[0] - x) ** 2 + (u[1] - y) ** 2 < r2:
                n += 1
        out[i] = l_plante * transmis ** n
    return out


def fenetre_ouverte(plant, seed: int, week: int) -> bool:
    """Bornage SANS ÉTAT du rythme de cladoptose (D111 ②ter) : un arbre n'est
    examiné qu'une semaine sur CLADO_FENETRE, à une phase propre tirée de sa
    position (deux arbres voisins ne lâchent pas leurs branches la même semaine)."""
    r, c = plant.position
    phase = int(_hash_noise(seed, 0, r * 131 + c, 13) * CLADO_FENETRE)
    return (week + phase) % CLADO_FENETRE == 0


def branches_ombragees(plant, l_plante: float, densite: float,
                       seuil: float, age_min: int, frac_max: float = 0.25,
                       n_max: int | None = None) -> list:
    """Racines des sous-arbres LATÉRAUX à faire tomber par l'ombre.

    Un sous-arbre meurt si TOUTES ses pointes sont sous `seuil` (aucune partie de
    la branche n'est encore rentable) ET si sa racine a au moins `age_min` semaines.
    Approche SANS ÉTAT (kickoff) : l'ombre d'une couronne évolue lentement, donc
    « ombragée maintenant et assez vieille » ≈ « ombragée depuis longtemps » — un
    rameau intérieur l'est depuis sa naissance. On ne renvoie que les racines
    MAXIMALES (pas un sous-sous-arbre d'une branche déjà condamnée). Une branche
    plus grosse que `frac_max` × la plante ne tombe pas d'un bloc : ce sont ses
    rameaux sombres qui tombent, un à un (l'arbre « remonte » sa couronne)."""
    segs = plant.segments
    if len(segs) <= 2:
        return []
    ch = _children(segs)
    axe = axe_porteur(segs, ch)
    lum = lumiere_pointes(segs, ch, l_plante, densite)
    # Lumière MAX du sous-arbre (la branche vit si une seule de ses pointes est
    # rentable). Parents avant enfants dans `segs` (append) → passe inverse = O(n).
    best = [0.0] * len(segs)
    taille = [1] * len(segs)
    for i in range(len(segs) - 1, -1, -1):
        b = lum.get(i, 0.0)
        for c in ch[i]:
            if best[c] > b:
                b = best[c]
            taille[i] += taille[c]
        best[i] = b
    cap = max(1, int(frac_max * len(segs)))
    roots = []
    for i in range(1, len(segs)):
        s = segs[i]
        if i in axe or taille[i] > cap:
            continue        # tronc + flèche protégés ; grosse charpentière : par rameaux
        if best[i] < seuil and s.age_weeks >= age_min:
            roots.append(i)
    roots = _maximales(segs, roots)
    if n_max is not None:
        # Rythme borné (②ter) : la branche la plus SOMBRE d'abord (à égalité, la
        # plus grosse : l'arbre lâche d'abord ce qui lui coûte le plus).
        roots = sorted(roots, key=lambda i: (best[i], -taille[i], i))[:n_max]
    return roots


def _maximales(segs: list, roots: list) -> list:
    """Ne garde que les racines dont aucun ancêtre n'est déjà une racine."""
    rs = set(roots)
    out = []
    for i in roots:
        p, inclus = segs[i].parent, False
        while p is not None:
            if p in rs:
                inclus = True
                break
            p = segs[p].parent
        if not inclus:
            out.append(i)
    return out


def branches_a_casser(plant, k: int, seed: int, week: int, frac_max: float) -> list:
    """Choisit au plus `k` sous-arbres latéraux à CASSER (tempête, neige) :
    score = levier (longueur cumulée du sous-arbre / épaisseur de la racine) ×
    hachage déterministe (graine ⊕ identité de forme, semaine, segment). Un sous-arbre plus gros que
    `frac_max` × la plante est écarté (on arrache une branche, pas la moitié de
    l'arbre). Racines disjointes (une branche cassée emporte ses rameaux)."""
    segs = plant.segments
    if k <= 0 or len(segs) <= 2:
        return []
    ch = _children(segs)
    axe = axe_porteur(segs, ch)
    cap = max(1, int(frac_max * len(segs)))
    cands = []
    for i in range(1, len(segs)):
        if i in axe:
            continue
        sub = _subtree(i, ch)
        if len(sub) > cap:
            continue
        levier = sum(segs[j].length_cm for j in sub) / max(segs[i].thickness_cm, 0.05)
        h = _hash_noise(seed ^ (plant.form_seed or 0), week, i, 7)
        cands.append((levier * (0.25 + h), i))
    cands.sort(reverse=True)
    pris, exclus = [], set()
    for _, i in cands:
        if len(pris) >= k:
            break
        if i in exclus:
            continue
        sub = _subtree(i, ch)
        pris.append(i)
        exclus.update(sub)
        p = segs[i].parent            # un ancêtre d'une branche prise ne peut plus l'être
        while p is not None:
            exclus.add(p)
            p = segs[p].parent
    return pris


def couper_branches(plant, roots: list) -> list:
    """Retire les sous-arbres enracinés en `roots` et RENVOIE leurs segments (même
    contrat que `_elaguer` : capturés AVANT réindexation, à passer au relais
    `deposer_bois_tombe`). Collet jamais coupé ; rejet de souche si plus d'apex."""
    segs = plant.segments
    roots = [i for i in roots if 0 < i < len(segs)]
    if not roots:
        return []
    ch = _children(segs)
    kill = set()
    for i in roots:
        kill.update(_subtree(i, ch))
    tombes = [segs[i] for i in sorted(kill)]
    _rebuild(plant, kill)
    if not any(s.is_apex for s in plant.segments):
        plant.segments[0].has_bud = True
    return tombes


def seuil_et_age(tol: float) -> tuple:
    """Seuil de lumière et âge minimal de la cladoptose, DÉRIVÉS de la tolérance à
    l'ombre effective (aucune donnée neuve) : un héliophile (tol < 1) lâche plus
    tôt une branche moins sombre ; un sciaphile (tol > 1) la garde plus longtemps
    sous une ombre plus profonde."""
    t = max(0.3, tol)
    return CLADO_SEUIL / t, int(math.ceil(CLADO_AGE_MIN * t))
