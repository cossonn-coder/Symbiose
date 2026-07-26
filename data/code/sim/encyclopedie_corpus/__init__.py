"""
SYMBIOSE — sim/encyclopedie_corpus/
CORPUS de l'ENCYCLOPÉDIE — DONNÉE éditoriale pure (sprint Voix narratives,
tronçon ④, dette « 4ᵉ voix »).
Spec de référence : `docs/narration/voix/conception_voix_narratives.md` §6.

Ce paquet ne contient QUE de la donnée (aucune logique, aucun import du moteur).
Il est séparé de `sim/encyclopedie.py` (la logique) pour respecter la règle « un
fichier = une responsabilité » : ici, c'est l'OUVRAGE ; là-bas, le LECTEUR.

> Refactor de clôture du sprint PÉRIPHÉRIE : l'ex-module unique
> `sim/encyclopedie_corpus.py` atteignait 402 LDC pur (zone rouge > 400). Il est
> éclaté en paquet PAR THÈME — `potager.py`, `fonctionnelles.py`,
> `adventices.py`, `ligneux.py`, `concepts.py` — et ce `__init__.py` réassemble
> `FICHES` dans le MÊME ordre d'insertion qu'avant (`encyclopedie.lister()` rend
> `list(FICHES)` : l'ordre est de l'API). Les imports appelants
> (`from sim.encyclopedie_corpus import FICHES`) sont INCHANGÉS. Texte recopié
> FIDÈLEMENT, aucune fiche ajoutée ni retirée.

`FICHES[espèce] = {1: "…N1…", 2: "…N2…", 3: "…N3…"}`
  - N1 (palier 1, découverte)     = ce qu'on VOIT : silhouette, organes.
  - N2 (palier 2, investissement) = la BIOLOGIE : cycle, besoins, strate, famille.
  - N3 (palier ≥ 3, maîtrise)     = le RÔLE ÉCOSYSTÉMIQUE : compagnonnage,
                                     succession, sol, faune.

Voix « naturaliste qui observe » (3ᵉ personne, descriptive et factuelle, ≠ le
« je » du carnet). Les CLÉS sont les clés du catalogue moteur (`plants.catalogue`)
— l'alignement est VÉRIFIÉ par `tests/test_encyclopedie.py`. Texte hors expertise
de Nico (botanique réelle) : à relire/corriger côté éditorial, jamais à réinventer
côté code.
"""
from __future__ import annotations

from sim.encyclopedie_corpus.potager import FICHES_POTAGER
from sim.encyclopedie_corpus.fonctionnelles import FICHES_FONCTIONNELLES
from sim.encyclopedie_corpus.adventices import FICHES_ADVENTICES
from sim.encyclopedie_corpus.ligneux import FICHES_LIGNEUX
from sim.encyclopedie_corpus.concepts import CONCEPTS

# Les 43 fiches × 3 niveaux (doc §6 + Grimpantes ⑤ + Luxuriance ④/⑤ + sources de
# mulch équilibre invasion ⑤ : blé/chanvre/sapin + essences forestières RENDU
# AMBIANCE T1 : hêtre/bouleau/charme + émetteurs allélopathiques ⑤ :
# armoise/seigle). L'ordre de fusion reproduit l'ordre du monolithe : un `dict`
# Python conserve l'ordre d'insertion, et `**` le respecte thème après thème.
FICHES: dict[str, dict[int, str]] = {
    **FICHES_POTAGER,
    **FICHES_FONCTIONNELLES,
    **FICHES_ADVENTICES,
    **FICHES_LIGNEUX,
}

__all__ = ["FICHES", "CONCEPTS"]
