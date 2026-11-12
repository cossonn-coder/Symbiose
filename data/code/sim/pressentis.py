"""
SYMBIOSE — sim/pressentis.py
Gestes PRESSENTIS (sprint ACCÈS AUX GESTES ③, conception
`docs/joueur/gestes/conception_refonte_palette.md` §3.4).

Un geste a trois états pour le joueur :
  - INCONNU   : il n'apparaît nulle part ;
  - PRESSENTI : le joueur en a entrevu l'existence — une silhouette dans le tiroir
                de la palette, et une phrase d'ambiance au survol ;
  - OUVERT    : il est dans la palette (`deblocage.gestes_debloques`).

« Pressenti » est CALCULÉ à chaque lecture, JAMAIS stocké : il se déduit de ce que
le joueur sait déjà (maîtrise, compteurs, marqueurs, courrier). Rien à sauvegarder,
rien à migrer, et aucune écriture → le golden ne peut pas bouger par ici.

Un geste fermé est pressenti si SA TECHNIQUE est entrevue, c'est-à-dire :
  - la technique est déjà découverte (palier ≥ 1) mais le geste attend encore
    autre chose (chaîne interne : le bac n'est pas posé, l'outil manque…) ;
  - ou un INDICE de la technique est vrai (`INDICES_TECHNIQUE`) : un geste voisin
    fait une fois, un concept voisin compris, une lettre qui en parle.

Philo #6 : ce n'est pas un arbre de compétences. La phrase (`PHRASE_PRESSENTI`) est
une pensée du jardinier, à la première personne. Elle ne dit NI où aller NI quoi
faire — elle laisse deviner qu'il y a quelque chose à comprendre.

COUCHES : module de `sim`, au-dessus du tick, lecture seule. Il importe
`sim.quetes` (lettres actives) ET `sim.actions.deblocage` ; c'est pour cela qu'il
vit ici et non dans `deblocage` (qui reste data/état et n'importe jamais `quetes`).
"""
from __future__ import annotations

from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE
from sim import maitrise as M
from sim import quetes as Q
from sim.actions import deblocage as D
from sim.actions.couts import OBJETS_TOUCHES

# --- Geste gaté → la technique qui le porte ----------------------------------
# Règle : le PREMIER élément du tuple d'`OBJETS_TOUCHES` est la technique (les
# suivants sont des outils). Vérifié sur les 32 gestes gatés au ③ : l'ordre est
# fiable partout. Seule exception, `planter_conteneur`, qui est dans `GESTE_UNLOCK`
# mais pas dans `OBJETS_TOUCHES` (constat du ①) → on le nomme à la main.
_TECHNIQUE_EXPLICITE: dict[str, str] = {"planter_conteneur": "jardinage_hors_sol"}

TECHNIQUE_DE_GESTE: dict[str, str] = {
    verbe: _TECHNIQUE_EXPLICITE.get(verbe) or OBJETS_TOUCHES[verbe][0]
    for verbe in D.GESTE_UNLOCK
}

# Espèces GRIMPANTES du catalogue (haricot, lierre, jasmin aujourd'hui), dérivées
# du moteur : en découvrir une fait pressentir le palissage. Jamais de liste figée.
_GRIMPANTES: tuple[str, ...] = tuple(sorted(
    cle for cle, cls in {**PLANT_CATALOGUE, **PERENNIAL_CATALOGUE}.items()
    if getattr(cls, "mode_grimpe", None) is not None
))

# --- Table des INDICES (conception §3.4) -------------------------------------
# Technique → liste d'indices ALTERNATIFS (OU implicite). Même grammaire que
# `deblocage.GESTE_UNLOCK` / `PORTES_TECHNIQUE`, plus deux formes propres à ce
# module (elles lisent ce que `deblocage` n'a pas le droit d'importer) :
#   ("lettre", technique) — une lettre ACTIVE (reçue, désir pas encore comblé)
#                           promet cette technique en récompense ;
#   ("geste", verbe)      — ce geste est déjà OUVERT dans la palette.
# Un indice est toujours PLUS FACILE que la porte de la même technique : on glane
# une fois, on pressent ; on glane trois fois, on sait.
# Seuils = point de départ, calibrage F5 comme les portes (R7).
INDICES_TECHNIQUE: dict[str, list] = {
    # Un premier glanage : on a des feuilles dans les mains, on se demande quoi en faire.
    "compostage": [("compte", "glaner", 1)],
    "paillage":   [("compte", "glaner", 1)],
    # Qui taille produit du bois, et finit par se demander où il va.
    "broyage":    [("maitrise", "taille", 1)],
    "jardinage_hors_sol": [("lettre", "jardinage_hors_sol")],
    # Une lettre en parle, ou bien on connaît déjà une plante qui grimpe.
    "palissage":  [("lettre", "palissage")]
                  + [("maitrise", cle, 1) for cle in _GRIMPANTES],
    # Qui sait bouturer n'est plus très loin de l'idée de souder deux bois.
    "greffe":     [("lettre", "greffe"), ("geste", "bouturer")],
    "protection-climatique": [("lettre", "protection-climatique")],
    # Le concept voisin : on a compris que les fleurs ont besoin des butineuses.
    "apiculture": [("maitrise", "pollinisation", 1), ("lettre", "apiculture")],
    # Un tuteur planté (les oiseaux s'y posent), ou le merle qu'on a regardé.
    "perchoir":   [("action", "poser_tuteur"), ("maitrise", "merle", 1)],
}

# --- Phrases d'ambiance, UNE par technique gatante ---------------------------
# Voix intérieure du jardinier, première personne. Règles d'écriture (testées) :
# aucun chiffre, aucun lieu du hub (pas d'« Atelier »), aucune consigne, rien qui
# nomme la piste. La phrase fait sentir un MANQUE ou une CURIOSITÉ, pas un chemin.
# Toute technique de `TECHNIQUE_DE_GESTE` a la sienne, même celles sans indice
# aujourd'hui (essartage, taillis…) : un indice ajouté demain trouve sa phrase.
PHRASE_PRESSENTI: dict[str, str] = {
    "compostage": "Ces feuilles que je ramasse, il doit bien y avoir mieux à en "
                  "faire qu'un tas.",
    "paillage": "La terre nue me semble frileuse. Sous les feuilles tombées, elle "
                "reste sombre et fraîche.",
    "broyage": "Tout ce bois coupé que j'entasse… Plus menu, la terre saurait "
               "peut-être le reprendre.",
    "jardinage_hors_sol": "Je me demande si une plante a vraiment besoin de la "
                          "pleine terre. Un peu de terre à elle lui suffirait "
                          "peut-être.",
    "palissage": "Cette tige cherche à quoi se tenir. Je la regarde tâtonner dans "
                 "le vide, puis retomber.",
    "perchoir": "Les oiseaux se posent toujours un peu plus haut que le reste. Je "
                "me demande ce qu'ils laissent en dessous.",
    "greffe": "J'ai vu un rameau coupé reprendre vie dans la terre. Reprendrait-il "
              "sur le bois d'un autre ?",
    "apiculture": "Tant de butineuses sur mes fleurs. Elles rentrent bien quelque "
                  "part, le soir.",
    "protection-climatique": "Le ciel fait ce qu'il veut. Mais ce que j'ai vu "
                             "pousser à l'abri en souffre moins.",
    "taille": "Mes doigts ne suffisent plus sur ce bois dur. La plaie que je "
              "laisse est bien vilaine.",
    "bouture": "Ce rameau tombé a gardé ses feuilles vertes bien longtemps. Je me "
               "demande ce qu'il ferait, piqué en terre.",
    "essartage": "Ces grands arbres gardent toute la lumière pour eux. Dessous, je "
                 "ne vois rien lever.",
    "taillis": "Une souche coupée ne meurt pas toujours. J'en ai vu repartir en "
               "bouquet.",
    "trogne": "J'ai vu cet arbre recoupé repartir de plus belle. Plus haut, hors "
              "de portée des bêtes, il ferait sans doute de même.",
    "terrassement": "La terre se laisse déplacer sous mes mains. L'eau et la "
                    "pierre doivent bien pouvoir suivre.",
}


# --- Lecture -----------------------------------------------------------------
def _lettre_active(game_state: dict, technique: str) -> bool:
    """Une lettre ACTIVE promet-elle cette technique ? Récompense de la forme
    `("technique", objet[, marqueur])` (`sim/quetes_corpus.py`). Lecture pure."""
    for quete in Q.quetes_actives(game_state):
        r = quete.recompense
        if isinstance(r, tuple) and len(r) >= 2 and r[0] == "technique" and r[1] == technique:
            return True
    return False


def _indice_vrai(game_state: dict, player: str, indice: tuple) -> bool:
    """Évalue UN indice. Les deux formes locales d'abord, puis la grammaire commune
    de `deblocage`. La forme `action` est relue ici SANS créer la tranche
    `actions_faites` (l'évaluateur de `deblocage` la crée à la volée ; une lecture
    appelée à chaque snapshot ne doit rien écrire)."""
    forme = indice[0]
    if forme == "lettre":
        return _lettre_active(game_state, indice[1])
    if forme == "geste":
        return D.est_debloque(game_state, player, indice[1])
    if forme == "action":
        return indice[1] in ((game_state.get("actions_faites") or {}).get(player) or ())
    return D.condition_remplie(game_state, player, indice)


def technique_entrevue(game_state: dict, player: str, technique: str) -> bool:
    """La technique est-elle découverte, ou l'un de ses indices est-il vrai ?"""
    if M.palier(game_state, player, technique) >= 1:
        return True
    return any(_indice_vrai(game_state, player, indice)
               for indice in INDICES_TECHNIQUE.get(technique, ()))


def gestes_pressentis(game_state: dict, player: str) -> list[str]:
    """Liste TRIÉE des gestes FERMÉS dont la technique est entrevue. Lecture PURE :
    aucune clé créée, rien de stocké (un joueur sans aucun état → liste vide).

    Coût : une trentaine de gestes pour une quinzaine de techniques ; chaque
    technique n'est évaluée qu'UNE fois par appel (mémo local `vues`)."""
    vues: dict[str, bool] = {}
    pressentis = []
    for verbe, technique in TECHNIQUE_DE_GESTE.items():
        if D.est_debloque(game_state, player, verbe):
            continue
        if technique not in vues:
            vues[technique] = technique_entrevue(game_state, player, technique)
        if vues[technique]:
            pressentis.append(verbe)
    return sorted(pressentis)


def bloc_pressentis(game_state: dict, player: str) -> list[dict]:
    """Forme d'EXPO au pont : `[{verbe, phrase}, …]`, triée par verbe. La phrase est
    celle de la TECHNIQUE du geste (plusieurs gestes d'une même technique partagent
    la même pensée)."""
    return [{"verbe": verbe, "phrase": PHRASE_PRESSENTI[TECHNIQUE_DE_GESTE[verbe]]}
            for verbe in gestes_pressentis(game_state, player)]
