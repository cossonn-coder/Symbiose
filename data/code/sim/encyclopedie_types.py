"""
SYMBIOSE — sim/encyclopedie_types.py
Table de CLASSIFICATION string → type de l'encyclopédie multi-règnes (D60, ①).
Spec : `docs/faune/vie_macro/conception_vie_macro_identifiable.md` §5 + kickoff
`sprints/faune/vie_macro/sprint_vie_macro_identifiable/01_backend_encyclo_unifiee.md`.

C'est le module PIVOT du sprint : la source de vérité UNIQUE qui range chaque
clé de maîtrise dans l'un des 7 onglets de l'encyclopédie. `type_de(cle)` est
lu par `encyclopedie.py` (pour taguer l'index et dispatcher la fiche) et, aux
tronçons ③/④/⑤, par le routeur de crédit de preuves.

Les 7 TYPES : plante · animal · champignon · concept · technique · outil · geste.

Chaque catégorie DÉRIVE des tables moteur déjà existantes (jamais de liste figée
dupliquée) :
  - plante     ← clés de `{PLANT_CATALOGUE, PERENNIAL_CATALOGUE}` ;
  - animal     ← clés de `FAUNE_ENCYCLO` (`fields/faune_encyclo.py`) ;
  - champignon ← la clé générique `CLE_CHAMPIGNON` (constante, une seule fiche) ;
  - concept    ← concepts transversaux (causes de stagnation + pollinisation) ;
  - technique  ← set explicite (les gestes-savoirs dans `OBJETS_TOUCHES`) ;
  - outil      ← reste des membres de `OBJETS_TOUCHES` MOINS les techniques ;
  - geste      ← clés de `COUTS` (`sim/actions/couts.py`).

ORDRE DE PRIORITÉ déterministe (§5) en cas d'ambiguïté d'une clé :
  plante → animal → champignon → concept → technique → outil → geste.
Aucune collision réelle n'existe aujourd'hui (garanti par un assert de test).
Une clé qu'aucune catégorie ne réclame → `type_de` renvoie `None` (robuste :
l'index l'ignore, pas de crash).

DONNÉE / lecture pure : ce module ne dépend que de tables statiques (catalogues,
faune, coûts) — aucun `game_state`, aucun tick. Golden NEUTRE.
"""
from __future__ import annotations

from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE
from fields.faune_encyclo import FAUNE_ENCYCLO
from sim.champignon_encyclo import CLE_CHAMPIGNON
from sim.maitrise_detection import CONCEPT_PAR_STAGNATION
from sim.actions.couts import COUTS, OBJETS_TOUCHES

# --- plante : les deux catalogues d'espèces vivantes -------------------------
PLANTES: frozenset[str] = frozenset({**PLANT_CATALOGUE, **PERENNIAL_CATALOGUE})

# --- animal : la faune nommée de l'encyclopédie ------------------------------
ANIMAUX: frozenset[str] = frozenset(FAUNE_ENCYCLO)

# --- concept : concepts transversaux (crédités par la détection) -------------
# Dérivé des causes de stagnation (eau/lumière/météo) + la pollinisation (créditée
# à part par `detecter`, §3.3). Set unique → source de vérité de l'onglet concept.
CONCEPTS: frozenset[str] = frozenset(CONCEPT_PAR_STAGNATION.values()) | {"pollinisation"}

# --- technique vs outil : on démêle les tuples mélangés de OBJETS_TOUCHES -----
# `OBJETS_TOUCHES` range dans un même tuple par geste une TECHNIQUE (un savoir-
# faire) ET des OUTILS/structures. On sépare par un set EXPLICITE des techniques ;
# tout autre membre des tuples est un outil. Set explicite = source de vérité
# lisible (les techniques sont des gestes-savoirs, pas des objets manipulés).
TECHNIQUES: frozenset[str] = frozenset({
    "semis", "arrosage", "récolte", "arrachage", "bêchage", "ameublissement",
    "taille", "compostage", "apiculture", "jardinage_hors_sol",
    "aménagement-habitat", "palissage", "broyage",
    "bouture",   # multiplication végétative (palette de gestes ②)
    "greffe",    # soudure aérien/racinaire (palette de gestes ③)
    # Savoir-faire de TERRASSEMENT (hydrologie ⑦ : creuser/drainer ; périphérie ⑤ :
    # endiguer/deriver/entailler). Il manquait au set explicite → il tombait dans
    # `OUTILS` par défaut et se voyait réclamer une fiche d'outil, alors que ce n'est
    # pas un objet qu'on prend en main. Rangé ici avec les autres gestes-savoirs.
    "terrassement",
    # Savoir-faire FORESTIERS (sprint PÉRIPHÉRIE ④) : les trois manières de prélever
    # du bois sur une lisière — essartage (on ouvre et on ne revient pas), taillis
    # (on coupe au ras pour que ça rejette), trogne (on prend la tête, le fût reste).
    "essartage", "taillis", "trogne",
})

# Tous les membres statiques touchés par un geste (union des tuples), puis les
# outils = ce reste MOINS les techniques. Dérivé → rien ne se perd si un geste
# neuf ajoute un objet.
_MEMBRES_OBJETS: frozenset[str] = frozenset(
    membre for tuple_objets in OBJETS_TOUCHES.values() for membre in tuple_objets
)
OUTILS: frozenset[str] = _MEMBRES_OBJETS - TECHNIQUES

# --- geste : les verbes d'action (clés de COUTS) -----------------------------
GESTES: frozenset[str] = frozenset(COUTS)

# Ordre de priorité déterministe : chaque (type, ensemble) testé dans CET ordre.
_PRIORITE: tuple[tuple[str, frozenset[str]], ...] = (
    ("plante",      PLANTES),
    ("animal",      ANIMAUX),
    ("champignon",  frozenset({CLE_CHAMPIGNON})),
    ("concept",     CONCEPTS),
    ("technique",   TECHNIQUES),
    ("outil",       OUTILS),
    ("geste",       GESTES),
)


def type_de(cle: str) -> str | None:
    """Type d'onglet d'une clé de maîtrise (§5), selon l'ordre de priorité
    déterministe. `None` si aucune catégorie ne la réclame (clé inconnue →
    ignorée par l'index, jamais de crash). Lecture pure."""
    for nom_type, membres in _PRIORITE:
        if cle in membres:
            return nom_type
    return None
