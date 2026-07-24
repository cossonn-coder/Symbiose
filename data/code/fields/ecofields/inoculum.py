"""
SYMBIOSE — fields/ecofields/inoculum.py
Champ de MÉMOIRE D'INOCULUM du sol (sprint mémoire d'inoculum, tronçon ①).

Le trou que ça comble : `infection_memory` (charge pathogène VÉCUE) est portée PAR
PLANTE et MEURT avec l'hôte → une tuile qui a porté une monoculture malade repart
VIERGE. Faux pour les pathogènes du sol et des résidus (mildiou hivernant, fonte,
verticillium). `InoculumField` est la MÉMOIRE édaphique qui survit à la plante.

Contrairement aux `GridField` denses, il est SPARSE et indexé par FAMILLE botanique
(décision D3) : l'inoculum est hôte-spécifique. Replanter la MÊME famille sur un plot
chargé = maladie amplifiée (couplage ②) ; TOURNER vers une autre famille échappe à la
charge, ÉMERGENT — aucune règle « rotation » : le bucket d'une famille absente décroît
simplement jusqu'à zéro (`tick_decay`). C'est la pédagogie de rotation (philo #2/#6).

Zéro RNG : accumulateur/décroissance PURS et déterministes (philo #3). Au tronçon ①
personne ne LIT ce champ dans la math du tick (DORMANT) → golden INTACT.
"""
from __future__ import annotations

from .constants import (INOC_MAX, INOC_EPSILON, INOC_DECAY,
                        INOC_MICRO_SUPPRESS, MICROBE_EFFECT_REF)


class InoculumField:
    """Charge pathogène PERSISTANTE par plot, indexée par famille botanique.

        load : dict[(r, c)] -> dict[famille -> charge ∈ [0, INOC_MAX]]

    Sparse : seuls les plots ayant hébergé une maladie ont une entrée ; un bucket
    retombé sous `INOC_EPSILON` est SUPPRIMÉ (borne le coût mémoire & de tick).
    """
    __slots__ = ("load",)

    def __init__(self):
        # dict SPARSE : jamais d'entrée pour un plot resté sain (§1). Ordre
        # d'insertion préservé par le dict → itération déterministe (philo #3).
        self.load: dict = {}

    def at(self, r: int, c: int, famille) -> float:
        """Charge d'inoculum de `famille` au plot (r, c) — 0.0 par défaut (sparse)."""
        return self.load.get((r, c), {}).get(famille, 0.0)

    def total(self, r: int, c: int) -> float:
        """Somme des charges de TOUTES les familles au plot (r, c). Sert la niche
        molène (③) et le rendu (④) : un plot durablement vicié, toutes familles
        confondues. 0.0 sur un plot jamais infecté."""
        return sum(self.load.get((r, c), {}).values())

    def deposit(self, r: int, c: int, famille, q: float) -> None:
        """Ajoute la charge `q` au bucket (plot, famille), bornée par INOC_MAX.
        No-op si `q <= 0` (n'ouvre pas un bucket vide inutile → sparse préservé)."""
        if q <= 0.0:
            return
        bucket = self.load.setdefault((r, c), {})
        bucket[famille] = min(INOC_MAX, bucket.get(famille, 0.0) + q)

    def tick_decay(self, eco) -> None:
        """Décroissance passive + suppression microbienne, une passe/tick sur les
        seuls buckets NON vides (coût borné par le nombre de plots infectés) :

            load ← load × INOC_DECAY − INOC_MICRO_SUPPRESS × microbiome_norm(r, c)
            load < INOC_EPSILON  → bucket PURGÉ (négatifs inclus : le max(0, ·) et le
                                   seuil de purge fusionnent en un seul test)

        `microbiome_norm` réutilise le levier existant (`microbiome / MICROBE_EFFECT_REF`,
        même normalisation que `disease_probability`/`vitalite`) : un sol vivant DIGÈRE
        l'inoculum plus vite (antagonistes). Itère sur des COPIES des clés (suppression
        pendant l'itération). Zéro RNG, ordre stable → déterministe."""
        for plot in list(self.load.keys()):
            r, c = plot
            micro_norm = min(1.0, eco.microbiome.at_plot(r, c) / MICROBE_EFFECT_REF)
            suppress = INOC_MICRO_SUPPRESS * micro_norm
            bucket = self.load[plot]
            for famille in list(bucket.keys()):
                v = bucket[famille] * INOC_DECAY - suppress
                if v < INOC_EPSILON:
                    del bucket[famille]        # purge (sparse) — négatif écrêté ici
                else:
                    bucket[famille] = v
            if not bucket:
                del self.load[plot]            # plus aucune famille → plot re-sparse
