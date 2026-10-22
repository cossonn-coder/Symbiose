"""
SYMBIOSE — fields/ecofields/litiere.py
Types de la couche fraîche & du compostage : `Parcelle` (tas de litière typé
par plot, remplace le scalaire `om_fresh`) et `Structure` (bac à compost / pile
à bois posés par le joueur), avec leurs helpers de fusion et de lissage et les
constantes propres aux structures.

Types PURS (dataclasses + helpers déterministes), sans dépendance aux champs —
isolés du conteneur (`container.py`) qui les manipule. Comportement identique à
l'ancien `ecofields.py`.
"""

from __future__ import annotations
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# GROSSEUR DU BOIS (D111 ⑦bis, décision Nico : « le bois met plus de temps à se
# décomposer s'il est plus gros »)
# ---------------------------------------------------------------------------
# Écologie : brindilles (< 1 cm) disparaissent en 1-3 ans, branches (1-10 cm) en
# 5-10 ans, troncs et souches (> 10 cm) en plusieurs décennies. La surface offerte
# aux champignons par unité de masse décroît avec le diamètre (rapport surface /
# volume ∝ 1/d) : un gros bois se décompose LENTEMENT.
# Modèle : la vitesse de base du tissu `bois` (TISSU, 0,02/sem) est celle d'un bois
# de diamètre BOIS_DIAM_DEFAUT ; elle est multipliée par
#       facteur(d) = (1 + DEFAUT/REF) / (1 + d/REF)
# → 1,15 pour une brindille de 0,3 cm, 0,75 à 1 cm, 0,25 à 5 cm, 0,14 à 10 cm,
# 0,05 à 30 cm (demi-vie en sol moyen ≈ 0,7 an / 1 an / 2,7 ans / 5 ans / 14 ans).
# Un écrivain qui ne donne pas de grosseur dépose du bois « par défaut » (BRF,
# précharge de substrat…) au taux historique EXACT (facteur non appliqué).
BOIS_DIAM_DEFAUT = 0.5    # cm — diamètre implicite du bois sans grosseur connue
BOIS_DIAM_REF    = 1.0    # cm — échelle de la décroissance du taux avec le diamètre


def facteur_grosseur(diam_cm: float) -> float:
    """Multiplicateur du taux de décompo du `bois` selon son diamètre (cm)."""
    return (1.0 + BOIS_DIAM_DEFAUT / BOIS_DIAM_REF) / (1.0 + max(0.0, diam_cm) / BOIS_DIAM_REF)


def diam_pondere(segments) -> float:
    """Diamètre moyen PONDÉRÉ PAR LA MASSE d'un lot de segments (masse ∝ l·t²,
    donc Σ l·t³ / Σ l·t²). Défaut si le lot est vide ou sans volume."""
    m = sum(s.length_cm * s.thickness_cm ** 2 for s in segments)
    if m <= 0.0:
        return BOIS_DIAM_DEFAUT
    return sum(s.length_cm * s.thickness_cm ** 3 for s in segments) / m


# ---------------------------------------------------------------------------
# PARCELLE DE LITIÈRE — unité de stockage de la couche fraîche (remplace om_fresh)
# ---------------------------------------------------------------------------

@dataclass
class Parcelle:
    """Tas de litière d'un `tissu` donné sur un plot (CONCEPTION §1.1).

    La somme des masses des parcelles d'un plot = l'ancien `om_fresh` (lecture
    dérivée via `EcoFields.om_fresh_at`). `age_sem` (semaines depuis dépôt) sert
    aux sous-sprints ③④ (maturité fruit, signal animal) — non lu en ①.
    """
    tissu:   str
    masse:   float
    age_sem: float = 0.0
    # Diamètre moyen (cm) pondéré par la masse — lu par la décompo du SEUL `bois`
    # (⑦bis). Les autres tissus gardent le défaut, jamais lu.
    diam_cm: float = BOIS_DIAM_DEFAUT


def _fusion_parcelle(parcelles: list, tissu: str, masse: float,
                     diam_cm: float = BOIS_DIAM_DEFAUT) -> None:
    """Fusion par tissu (bornage déterministe, §1.1) — PARTAGÉE litière ↔ structures.

    Si une parcelle de même `tissu` existe → masse cumulée, `age_sem` = moyenne
    pondérée par la masse (le dépôt neuf, d'âge 0, rajeunit le tas), `diam_cm`
    idem (⑦bis : une brindille sur une souche affine le tas). Sinon append.
    Suppose `masse > 0` (l'appelant garde le no-op + tout filtre d'acceptation).
    """
    for p in parcelles:
        if p.tissu == tissu:
            total = p.masse + masse
            if diam_cm != p.diam_cm and total > 0:
                # garde : deux grosseurs égales ne recalculent rien (pas de dérive
                # flottante du défaut → décompo historique bit-identique)
                p.diam_cm = (p.diam_cm * p.masse + diam_cm * masse) / total
            p.age_sem = (p.age_sem * p.masse) / total if total > 0 else 0.0
            p.masse = total
            return
    parcelles.append(Parcelle(tissu, masse, 0.0, diam_cm))


# ---------------------------------------------------------------------------
# STRUCTURES POSABLES — bac à compost & pile à bois (décompo·compost ⑤, §5)
# ---------------------------------------------------------------------------

# Tissus recevables par chaque type de structure (§5, table). Le bac à compost
# digère la litière de SURFACE tendre ; il refuse le `bois` (trop lent) ET la
# parcelle `diffus` (exsudats racinaires DANS le sol, non ramassables, et parcelle
# permanente du plot — décision ⑤A : dévie de la lettre du §5 qui listait diffus).
# La pile à bois ne prend QUE le `bois` (BRF / hügelkultur).
STRUCTURE_ACCEPTE = {
    "bac":  frozenset(("feuille", "fleur", "herbace", "fruit")),
    "pile": frozenset(("bois",)),
    "ruche": frozenset(),     # apiculture (⑥, §H) : n'absorbe AUCUNE litière (ce n'est
                              # pas un composteur) → `accepte()` toujours faux, donc
                              # `composter`/`empiler` la refusent et `tick_structures`
                              # la traverse sans rien faire (contenu toujours vide).
}

# Maturation hybride (⑤ phase B, §5.2). La maturation est une décompo CONFINÉE :
# chaque parcelle du contenu mûrit à la cinétique de son tissu (`TISSU[tissu]`,
# `decay` = « tendre vite / bois lent », déjà calibré §1.2), la fraction
# humifiée+minéralisée s'accumule dans la jauge `compost_mur`, le reste est respiré
# (perte nette, comme un tas de compost qui fond). `MATUR_BAC`/`MATUR_PILE` =
# multiplicateurs de vitesse par type de structure (la pile à bois est très lente :
# BRF / hügelkultur). `retourner` MULTIPLIE la vitesse et LISSE les âges pendant
# `RETOURNE_DUREE` semaines. Knobs, calibrage post-test (n'affectent ni le golden,
# neutre, ni le déterminisme).
MATUR_BAC           = 0.40   # vitesse de maturation du bac (× decay du tissu)
MATUR_PILE          = 0.20   # pile à bois : ~25× plus lente que le bac sur son tissu
MATUR_RETOURNE_MULT = 2.0    # `retourner` double la vitesse pendant RETOURNE_DUREE sem
RETOURNE_DUREE      = 4       # semaines d'effet d'un retournement (drapeau décompté)


def _lisser_ages(parcelles: list) -> None:
    """Homogénéise les âges du contenu (`retourner`, §5.2) : chaque parcelle prend
    l'âge moyen pondéré par la masse. Conserve la masse, déterministe (zéro RNG)."""
    total = sum(p.masse for p in parcelles)
    if total <= 0.0:
        return
    moyen = sum(p.age_sem * p.masse for p in parcelles) / total
    for p in parcelles:
        p.age_sem = moyen


@dataclass
class Structure:
    """Structure de compostage posée par le joueur (CONCEPTION §5).

    Deux `kind` : `bac` (matière tendre → compost mûr) et `pile` (bois →
    amendement structure + habitat auxiliaire §4.1). Le `contenu` réutilise la
    `Parcelle` de la litière (mêmes tissus, même fusion par tissu) ; il mûrira en
    `compost_mur` (jauge mesurée) au tick `tick_structures` (phase B). `plot` =
    plot-foyer (r, c) du placement (phase planification). Posée VIDE.
    """
    kind:            str
    plot:            tuple                              # (r, c)
    contenu:         list  = field(default_factory=list)  # list[Parcelle]
    compost_mur:     float = 0.0
    retourne_restant: float = 0.0                       # semaines d'accélération restantes (⑤B, `retourner`)
    # Colonisation fongique du tas (mycélium ⑤, §3.3) ∈ [0,1] : 0 = tas neuf non
    # colonisé, 1 = tas pleinement habité par le réseau. Croît au `tick_structures`
    # tant qu'il reste du contenu à digérer (le tas humide riche en bois = habitat
    # fongique de choix), MODULE la vitesse de maturation (voie fongique) et ENSEMENCE
    # `eco.mycelium` autour (→ faune fongivore ④ + carpophores sur le bac, §3.4).
    # INUTILISÉ par la `ruche` (reste 0.0). Posée à 0.0 (tas neuf vierge).
    colonisation:    float = 0.0
    # Apiculture (⑥, §H/§I) — état d'une `ruche`, INUTILISÉ par bac/pile (restent 0.0,
    # pas de régression). `essaim` ∈ [0,1] = peuplement capturé (tick_ruches), `miel`
    # ∈ [0, MIEL_MAX] = réserve produite (intégrale du nectar mellifère butiné).
    essaim:          float = 0.0
    miel:            float = 0.0

    def accepte(self, tissu: str) -> bool:
        """Le tissu est-il recevable par cette structure (§5) ?"""
        return tissu in STRUCTURE_ACCEPTE[self.kind]
