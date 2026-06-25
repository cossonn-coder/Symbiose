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


def _fusion_parcelle(parcelles: list, tissu: str, masse: float) -> None:
    """Fusion par tissu (bornage déterministe, §1.1) — PARTAGÉE litière ↔ structures.

    Si une parcelle de même `tissu` existe → masse cumulée, `age_sem` = moyenne
    pondérée par la masse (le dépôt neuf, d'âge 0, rajeunit le tas). Sinon append.
    Suppose `masse > 0` (l'appelant garde le no-op + tout filtre d'acceptation).
    """
    for p in parcelles:
        if p.tissu == tissu:
            total = p.masse + masse
            p.age_sem = (p.age_sem * p.masse) / total if total > 0 else 0.0
            p.masse = total
            return
    parcelles.append(Parcelle(tissu, masse))


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
