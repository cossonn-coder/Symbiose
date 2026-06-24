"""
SYMBIOSE — world/substrat.py
Registre data-driven des SUBSTRATS de conteneur (pots / bacs).

> Conception : `docs/conception/CONCEPTION_POTS_BACS_SUBSTRATS.md` §2.
> Tronçon ① du sprint pots/bacs : DATA PURE. Aucun conteneur n'existe encore,
> aucune boucle n'est touchée → golden trivialement NEUTRE.

Un substrat est une **recette** : une fiche de DONNÉES qui (a) **initialise** les
champs d'un mini-sol (`EcoFields` miniature, posé en ②) et (b) **fixe ses
coefficients** — surtout le `drainage` qui remplacera, dans le conteneur, le
choix par `soil_type` des tuiles. Patron identique aux registres d'espèces et de
faune : la mécanique vit dans le moteur, les valeurs vivent dans une table
lisible et calibrable (philo de design #3 — knobs explicites).

Ici on ne BRANCHE rien : on ne fait que déclarer les recettes et un accès. Leur
injection dans un mini-sol (parcelles de `litiere_precharge`, copie de la tuile
pour `terre_jardin`) est le travail du tronçon ②.

Couches : ce module n'importe rien de lourd (juste `dataclass`). Le garde-fou de
validation des tissus lit `TISSU`/`FAIM_N_TISSUS` depuis `fields.ecofields`
(world → fields autorisé ; fields n'importe jamais world → pas de cycle).
"""

from __future__ import annotations

from dataclasses import dataclass

# Tissus connus du moteur de décomposition (clés de cinétique `TISSU`) PLUS les
# tissus C-riches qui n'ont pas de cinétique propre mais immobilisent l'azote
# (`FAIM_N_TISSUS` : `bois`, `substrat`). On valide la `litiere_precharge` contre
# cette UNION, fidèle à la conception §2 qui considère `substrat` comme « déjà au
# moteur » via la faim d'azote.
#
# ⚠️ NB pour ② : `substrat` est dans `FAIM_N_TISSUS` mais PAS dans `TISSU` → il n'a
# AUCUNE cinétique de décompo et n'est pas dans `TISSU_ORDER`. Injecter tel quel une
# parcelle `substrat` dans un mini-sol qui ticke la décompo plantera (KeyError
# `TISSU["substrat"]` / ValueError `TISSU_ORDER.index`). C'est un sujet du tronçon ②
# (gérer/écarter `substrat` à la décompo, ou lui donner une cinétique) — PAS de ①,
# qui ne fait que déclarer la donnée. Le garde-fou ci-dessous accepte donc `substrat`
# comme tissu CONNU, mais ce point est signalé à Nico.
from fields.ecofields import FAIM_N_TISSUS, TISSU

TISSUS_CONNUS: frozenset = frozenset(TISSU.keys()) | FAIM_N_TISSUS


@dataclass(frozen=True)
class SubstratRecette:
    """Recette d'un substrat de conteneur (CONCEPTION §2).

    `frozen=True` : une recette est une donnée de référence immuable, partagée
    par tous les conteneurs qui la choisissent (jamais mutée — déterminisme).

    Champs :
      - `nom`              : libellé lisible (UI / encyclopédie).
      - `drainage`         : coefficient passé en `drainage_override` au
                             `tick_hydrology` du mini-sol (∈ ]0,1[ ; proche de 1 =
                             retient l'eau, plus bas = évacue vite).
      - `structure_init`   : `structure_sol` initiale du mini-sol ∈ [0,1].
      - `ph_init`          : pH initial.
      - `npk_init`         : (N, P, K) initiaux.
      - `microbiome_init`  : microbiome initial.
      - `litiere_precharge`: ((tissu, masse), …) — parcelles déposées d'office
                             (lasagnes, substrat de champignon). DONNÉE en ① ;
                             injectée dans le mini-sol en ②.
      - `herite_tuile`     : si True (« terre du jardin »), les champs ci-dessus
                             sont IGNORÉS et le mini-sol copie le plot de tuile au
                             point de remplissage (pont conteneur↔jardin, ②).
    """
    nom:               str
    drainage:          float
    structure_init:    float
    ph_init:           float
    npk_init:          tuple
    microbiome_init:   float
    litiere_precharge: tuple = ()
    herite_tuile:      bool = False


# ---------------------------------------------------------------------------
# REGISTRE — 6 recettes de départ (CONCEPTION §2, tableau).
# Valeurs EXACTES du tableau. Knobs de calibrage post-test (philo #3) : ces
# nombres ne touchent NI le golden (aucun conteneur dans le smoke) NI le
# déterminisme — ils ne s'animent qu'au tronçon ② et au-delà.
# ---------------------------------------------------------------------------

SUBSTRATS: dict[str, SubstratRecette] = {
    # Terreau standard — équilibré, bon départ généraliste.
    "terreau": SubstratRecette(
        nom="terreau",
        drainage=0.990, structure_init=0.85, ph_init=6.5,
        npk_init=(1.2, 1.0, 1.0), microbiome_init=0.6,
    ),
    # Compost mûr — riche en NPK et en microbiome, légèrement basique.
    "compost": SubstratRecette(
        nom="compost",
        drainage=0.992, structure_init=0.90, ph_init=7.0,
        npk_init=(2.2, 1.5, 1.8), microbiome_init=1.5,
    ),
    # Drainant minéral (billes d'argile / perlite / sable) — ne se décompose pas,
    # pur modificateur de drainage/structure, NPK pauvre. Pour plantes qui
    # craignent l'excès d'eau.
    "drainant_mineral": SubstratRecette(
        nom="drainant_mineral",
        drainage=0.975, structure_init=0.95, ph_init=6.8,
        npk_init=(0.2, 0.2, 0.2), microbiome_init=0.1,
    ),
    # Lasagnes (mille-feuille de matières) — NPK initial PAUVRE mais une litière
    # pré-chargée que la décompo confinée du mini-sol libérera dans le temps
    # (cascade om_fresh→…→NPK déjà existante). Le `bois` initial crée une faim
    # d'azote de départ (réaliste pour une lasagne fraîche) puis se libère.
    "lasagnes": SubstratRecette(
        nom="lasagnes",
        drainage=0.988, structure_init=0.70, ph_init=6.5,
        npk_init=(0.5, 0.4, 0.4), microbiome_init=0.8,
        litiere_precharge=(("feuille", 2.0), ("herbace", 1.0), ("bois", 0.8)),
    ),
    # Terre du jardin — `herite_tuile=True` : les valeurs ci-dessous sont des
    # SENTINELLES jamais lues (le mini-sol copiera le plot de tuile au point de
    # remplissage, tronçon ②). Le pont le plus direct conteneur↔jardin.
    "terre_jardin": SubstratRecette(
        nom="terre_jardin",
        drainage=0.993, structure_init=0.70, ph_init=6.5,
        npk_init=(1.0, 1.0, 1.0), microbiome_init=0.5,
        herite_tuile=True,
    ),
    # Substrat usé de mycélium — pré-charge du tissu `substrat` (∈ FAIM_N_TISSUS) :
    # faim d'azote initiale forte puis libération. Pont vers les champignons
    # (acteurs futurs) — respecte l'interconnexion des acteurs.
    "mycelium_use": SubstratRecette(
        nom="mycelium_use",
        drainage=0.985, structure_init=0.80, ph_init=6.5,
        npk_init=(0.3, 0.3, 0.3), microbiome_init=0.5,
        litiere_precharge=(("substrat", 2.0),),
    ),
}


# ---------------------------------------------------------------------------
# Garde-fou — toute `litiere_precharge` ne référence que des tissus connus du
# moteur. Vérifié À L'IMPORT (échec franc tôt plutôt qu'un KeyError obscur au
# tronçon ②). Déterministe : ordre d'itération du dict registre = ordre stable.
# ---------------------------------------------------------------------------

def _valide_registre() -> None:
    for cle, rec in SUBSTRATS.items():
        for tissu, _masse in rec.litiere_precharge:
            if tissu not in TISSUS_CONNUS:
                raise ValueError(
                    f"substrat {cle!r} : tissu de pré-charge {tissu!r} inconnu "
                    f"du moteur (attendu ∈ {sorted(TISSUS_CONNUS)})"
                )


_valide_registre()


def get_substrat(cle: str) -> SubstratRecette:
    """Accès au registre par clé. Lève `KeyError` explicite si la clé est inconnue
    (pas de défaut silencieux : une recette manquante est un bug d'appelant)."""
    try:
        return SUBSTRATS[cle]
    except KeyError:
        raise KeyError(
            f"substrat inconnu : {cle!r} (clés valides : {sorted(SUBSTRATS)})"
        ) from None
