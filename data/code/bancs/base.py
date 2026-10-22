"""
SYMBIOSE — bancs/base.py
Briques communes des BANCS D'ESSAI (sprint « bancs d'essai », tronçon ①).

Un banc est un MONDE PARAMÉTRÉ qui FORCE une condition observable au-delà du
seuil de sa cause, pour qu'un phénomène (un signe foliaire) apparaisse vite et de
façon déterministe — instrument d'observation, pas jardin de démo. Ce module ne
fait que COMPOSER l'état existant du moteur (sol, champs éco, plantes, mémoires
physiologiques) ; il n'introduit AUCUNE mécanique nouvelle. C'est ce qui garantit
le golden NEUTRE : rien ici n'est branché pour `smoke`/`full` (cf. `cmd_init`).

Couche : `bancs/` est au niveau de `main.py` (peut tout importer) ; les couches
basses (plants/fields/sim) ne l'importent jamais → règle de couches préservée.

Trois familles d'helpers :
  - `build_banc_tile` : une tuile + ses champs éco, n'importe lequel forçable.
  - `monde` : emballe le tuple de retour standard `(tiles, ecos, house, banque)`.
  - `force_memoire` / `vieillir` : ACCÉLÉRATION déterministe (pré-charge d'un état
    physiologique / pré-vieillissement) — pose le phénomène « déjà installé » au
    seuil, comme `cmd_init` pré-vieillit les fruitiers du verger en config "full".
"""
from __future__ import annotations

from world import Tile, House
from fields import init_eco
from sim.seeds import PlayerSeedBank
from sim.precroissance import pre_croitre

# Graine de la morphogénèse pré-déroulée par `vieillir` (la forme ne dépend pas
# de la graine du monde, mesuré ②ter : 3 graines → structure identique).
BANC_PRECROISSANCE_SEED = 0


def build_banc_tile(name: str, soil: str, rows: int, cols: int,
                    ox: float = 0.0, oy: float = 0.0, *,
                    humidite: float = 0.0, fertilite: float | None = None,
                    microbiome: float = 0.2, **champs):
    """Une tuile de banc + son `EcoFields`, avec forçage UNIFORME de champs.

    `humidite`/`fertilite`/`microbiome` passent par `init_eco` (mêmes sémantiques
    que `main.build_tile`). Tout champ supplémentaire (`ph`, `n`, `p`, `k`,
    `structure_sol`…) se force via `**champs` : chaque clé doit être un champ
    connu de `EcoFields.get_field`, rempli UNIFORMÉMENT à la valeur donnée
    (`GridField.fill`). C'est la brique unique au-dessus de laquelle chaque banc
    compose sa condition (sol acide, sol engorgé, sol carencé…).

    Retourne `(tile, eco)`.
    """
    tile = Tile(tile_id=name, soil_type=soil, grid_rows=rows, grid_cols=cols,
                origin_x_cm=float(ox), origin_y_cm=float(oy))
    eco = init_eco(name, rows, cols, humidite=humidite, fertilite=fertilite,
                   microbiome=microbiome, soil_type=soil, heterogene=True)
    for nom, valeur in champs.items():
        field = eco.get_field(nom)
        if field is None:
            raise KeyError(f"champ éco inconnu pour le forçage de banc : {nom!r}")
        field.fill(float(valeur))
    return tile, eco


def monde(tiles, ecos, house=None, banque=None):
    """Emballe le tuple de retour standard d'une fabrique de banc, avec défauts.
    `house=None` → maison par défaut (centrée, inerte ici sauf si un banc la pose
    haute/proche pour forcer l'ombre, cf. ③). `banque=None` → banque-joueur vide
    (le branchement `cmd_init` retombe alors sur la banque smoke)."""
    return (tiles, ecos, house or House(), banque or PlayerSeedBank())


def force_memoire(plant, nom: str, valeur: float) -> None:
    """ACCÉLÉRATION : pré-charge une mémoire physiologique de la plante au seuil
    voulu (`drought_memory`, `shade_memory`, `asphyxie_memory`, `cold_memory`…).
    Déterministe et ponctuel : on pose l'état « le stress est DÉJÀ installé » sans
    dérouler les semaines d'accumulation que la météo seedée pourrait d'ailleurs
    interrompre (une pluie de fond ramène l'humidité). L'environnement composé du
    banc (sol drainant, humidité basse…) MAINTIENT ensuite cette mémoire."""
    setattr(plant, nom, float(valeur))


def force_faune(eco, espece: str, densite: float) -> None:
    """ACCÉLÉRATION (volet biotique) : pré-charge UNIFORMÉMENT la densité d'une
    espèce de faune (`puceron`, `abeille`…) dans son champ de population. Pose une
    pression/présence DÉJÀ installée sans dérouler les semaines de colonisation —
    que la porte saisonnière hivernale rendrait d'ailleurs nulles (warmth=0 sous
    T_COLD_ZERO). Le champ relaxe ensuite vers sa cible écologique au tick : la
    fenêtre d'observation du banc se lit AVANT que la décrue saisonnière ne le
    ramène sous le seuil (cf. oracle). Symétrique de `force_memoire` côté plante."""
    field = eco.populations.get(espece) if eco.populations else None
    if field is None:
        raise KeyError(f"espèce de faune inconnue pour le forçage de banc : {espece!r}")
    field.fill(float(densite))


def vieillir(plant, ans: float) -> None:
    """ACCÉLÉRATION : pré-vieillit une plante de `ans` années (âge en années ET en
    semaines, cohérents). Sert aux bancs qui veulent une vivace en fin de longévité
    (sénescence) ou un fruitier mûr sans dérouler des années en Turbo — même geste
    que la config "full" de `cmd_init` sur les fruitiers du verger. Depuis D111
    ②ter (ferme D105) la STRUCTURE pousse aussi sur ces années (espèce
    procédurale) : un pommier de 5 ans n'est plus une pousse invisible au F5."""
    pre_croitre(plant, BANC_PRECROISSANCE_SEED, ans)
    plant.age_years += float(ans)
    plant.age_weeks += int(round(ans * 52))
