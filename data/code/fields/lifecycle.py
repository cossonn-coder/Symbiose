"""
SYMBIOSE — fields/lifecycle.py
Ponts de cycle de vie (chenille→papillon, syrphe_larve→syrphe) — arc
pollinisation, tronçon ⑤ (docs/faune/pollinisation/conception_pollinisation_cycle_vie.md §D).

Un cycle de vie n'est PAS une 5ᵉ guilde trophique : c'est un STADE, traité à
part dans le tick (décision Nico, cohérent avec la décompo ④). Le patron est
GÉNÉRAL et data-driven — un *pont de cycle de vie* = `(champ_larvaire, ressource
de la larve, → type_adulte)` :

  | Pont      | Champ larvaire | Effet trophique de la LARVE      | → Adulte   |
  | Papillon  | chenille       | +herbivorie (mange le feuillage) | papillon   |
  | Syrphe    | syrphe_larve   | −ravageur (prédateur de pucerons)| syrphe     |

Le syrphe est le SYMÉTRIQUE exact de la chenille : même moule (champ larvaire +
maturité + ponte + famine + métamorphose), mais l'effet larvaire est *bénéfique*
(il mange du ravageur) au lieu de nuisible. Boucle d'interconnexion (philo #6) :
pucerons → nourrissent syrphe_larve → métamorphose → syrphe pollinisateur ; et
chenilles → papillon pollinisateur.

Couche `fields` (mirror de `foragers.py`, garde-fou taille) : ce module ne
contient QUE de la donnée (`LifeCycleBridge`) + le tick PUR `tick_bridges`,
duck-typé sur `eco` (lit `eco.larvae`/`eco.populations`, écrit les champs
larvaires + le terme-source de métamorphose dans le champ adulte). Il N'IMPORTE
PAS `population` (les ponts y sont CONSTRUITS — `build_lifecycle_bridges` — avec
leurs `resource_fn`) → aucun cycle. Déterminisme TOTAL : zéro RNG, tout dérive
de la densité des champs + la photopériode passée par l'appelant (philo #3).

INVARIANT GOLDEN (§D.6) : à `chenille = 0` ET `syrphe_larve = 0` partout (aucun
adulte pour pondre, ou hors fenêtre), les champs larvaires restent nuls → les
LECTEURS (herbivorie lit `ravageur + chenille` ; le ravageur prédaté par
`syrphe_larve`) retrouvent EXACTEMENT le comportement d'avant ⑤. Toute dérive du
golden est donc attribuable aux SEULS cycles larvaires (re-figeage MAÎTRISÉ).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable


# ---------------------------------------------------------------------------
# CONSTANTES DE CYCLE (placeholders — calibrage post-test, §D.5)
# ---------------------------------------------------------------------------
# Le cycle vise l'effet émergent §D.4 : pic de larves → métamorphose → bouffée de
# pollinisateurs (pile pour la floraison/nouaison §B). Régulation boom-bust : trop
# de larves épuisent leur ressource et s'effondrent (famine). Tous à régler jeu
# en main — knobs conservatifs (un pont ne sature pas l'écosystème).
PONTE_RATE  = 0.20   # ponte/sem ∝ adulte_local × ressource_larve_local × fenêtre
MATUR_RATE  = 0.12   # maturation/sem ∝ nourriture consommée (∝ min(larve, ressource))
METAM_SEUIL = 0.50   # maturité cumulée au-delà de laquelle la cohorte se métamorphose
METAM_PERTE = 0.50   # fraction perdue à la métamorphose (prédation/parasitisme/échec)
FAMINE_RATE = 0.35   # mortalité/sem de la fraction de larves excédant la ressource


@dataclass(frozen=True)
class LifeCycleBridge:
    """Un pont de cycle de vie, déclaré PAR DONNÉE (§D.1). Attaché à un
    `PollinatorSpec` adulte (champ `bridge`, registre §E).

      - larva / larva_nourrie : clés des deux grilles `eco.larvae` (densité de
                                larves ∈[0,1] ; maturité moyenne cumulée ∈[0,1]).
      - adult                 : clé du champ adulte `eco.populations` ALIMENTÉ par
                                la métamorphose (boucle larve → adulte).
      - resource_fn           : (eco, tile, plants) → grille [rows][cols] ∈[0,1] =
                                nourriture de la larve ET lieu de ponte (le
                                feuillage pour la chenille, le ravageur pour le
                                syrphe). → boucle adulte → larve.
      - daylen_min/full       : fenêtre de PONTE (photopériode, heures de jour).

    Les taux ont des défauts de module, surchargeables par pont.
    """
    larva: str
    larva_nourrie: str
    adult: str
    resource_fn: Callable
    daylen_min: float
    daylen_full: float
    ponte_rate: float = PONTE_RATE
    matur_rate: float = MATUR_RATE
    metam_seuil: float = METAM_SEUIL
    metam_perte: float = METAM_PERTE
    famine_rate: float = FAMINE_RATE


def larval_field_names(bridges: list[LifeCycleBridge]) -> list[str]:
    """Noms des grilles larvaires à instancier dans `EcoFields` (densité +
    maturité par pont). Ordre déterministe (ordre du registre)."""
    names: list[str] = []
    for b in bridges:
        names += [b.larva, b.larva_nourrie]
    return names


def _smoothstep(x: float, a: float, b: float) -> float:
    """Rampe LISSE [0,1] entre a (→0) et b (→1) — Hermite. Copie locale (4 lignes)
    pour garder ce module INDÉPENDANT de `population` (qui en importe la donnée)."""
    if a == b:
        return 0.0 if x < a else 1.0
    t = (x - a) / (b - a)
    t = 0.0 if t < 0.0 else 1.0 if t > 1.0 else t
    return t * t * (3.0 - 2.0 * t)


def tick_bridges(eco, tile, plants, bridges: list[LifeCycleBridge],
                 daylight_hours: float) -> None:
    """Ticke TOUS les ponts (cycle §D.3, après les guildes & les butineurs).
    PURE & déterministe ; n'écrit que `eco.larvae[...]` et le terme-source de
    métamorphose dans `eco.populations[adult]`. `daylight_hours` (= `daylength(wiy)`)
    est calculé par l'appelant (évite d'importer `population` → pas de cycle).

    Cycle par plot, dans l'ordre §D.3 :
      1. PONTE (fenêtre photopériodique) : larve += ponte_rate · adulte · ressource
         · fenêtre — l'adulte pond là où il y a la ressource de la larve.
      2. action trophique larvaire : portée par les LECTEURS (herbivorie lit
         `ravageur + chenille` ; `syrphe_larve` prédate le ravageur) — rien ici.
      3. MATURATION par la nourriture : nourrie += matur_rate · min(larve, ressource).
      4. FAMINE : la fraction de larves excédant la ressource décline (boom-bust).
      5. MÉTAMORPHOSE : nourrie ≥ seuil → adulte += larve · (1−perte), puis remise
         à zéro de la cohorte (larve = 0, nourrie = 0).
    """
    for b in bridges:
        adult = eco.populations.get(b.adult)
        if adult is None:
            continue
        res = b.resource_fn(eco, tile, plants)
        gate = _smoothstep(daylight_hours, b.daylen_min, b.daylen_full)
        larva = eco.larvae[b.larva]
        nourrie = eco.larvae[b.larva_nourrie]
        for r in range(eco.rows):
            for c in range(eco.cols):
                a = adult.at_plot(r, c)
                rr = res[r][c]
                lv = larva.at_plot(r, c)
                no = nourrie.at_plot(r, c)
                # 1. Ponte (adulte → larve, là où il y a la ressource larvaire).
                lv += b.ponte_rate * a * rr * gate
                # 3. Maturation par la nourriture consommée (∝ min(larve, res)).
                food = lv if lv < rr else rr
                no += b.matur_rate * food
                # 4. Famine : l'excédent de larves sur la ressource s'effondre.
                deficit = lv - rr
                if deficit > 0.0:
                    lv -= b.famine_rate * deficit
                lv = 0.0 if lv < 0.0 else 1.0 if lv > 1.0 else lv
                # 5. Métamorphose (larve → adulte), puis reset de la cohorte.
                if no >= b.metam_seuil:
                    adult.add(r, c, lv * (1.0 - b.metam_perte))
                    lv = 0.0
                    no = 0.0
                larva.set(r, c, lv)
                nourrie.set(r, c, no)
