"""
SYMBIOSE — fields/faune_encyclo.py
Métadonnée d'ENCYCLOPÉDIE de la faune nommée (tronçon ④e, modèle B
CONCEPTION_FAUNE_DEDIEE.md §1.1/§3). DONNÉE PURE : jamais lue par le tick de la
simulation → golden NEUTRE. Le RENDU (l'entrée d'encyclopédie côté Godot, voix
naturaliste philo #5) est le tronçon ⑥ ; ici on ne porte que le texte et le
graphe relationnel, prêts à splatter dans `TrophicSpec`.

Module SÉPARÉ de population.py à dessein : ce dernier dépasse déjà le garde-fou
de taille (~350 LDC pur) ; on n'y ajoute pas 10 blurbs de données (kickoff ④e §4).
Aucun import (donnée pure) → aucun cycle de couche.

  blurb           : texte d'observation du naturaliste (ce qu'on VOIT, pas la
                    cause cachée — l'interprétation se mérite au palier de maîtrise).
  interconnexions : noms LIÉS dans le graphe §3 — proies/prédateurs nommés (les 10
                    espèces) + éléments du milieu qui font la niche (`fruit` tombé,
                    `pile` de bois, `ail` répulsif, `syrphe_larve` du pont ⑤). Donnée
                    PURE : les vraies boucles vivent dans `predators`/`resource_fn`,
                    pas ici. INVARIANT (testé) : tout `predators` d'une espèce est
                    inclus dans ses `interconnexions`, et le sous-graphe entre les 10
                    espèces nommées est SYMÉTRIQUE (si A cite B, B cite A).
"""
from __future__ import annotations

# name -> (blurb, interconnexions)
FAUNE_ENCYCLO: dict[str, tuple[str, tuple[str, ...]]] = {
    # --- catégorie ravageur -------------------------------------------------
    "puceron": (
        "Petit suceur de sève agglutiné sous les jeunes pousses tendres ; sa "
        "pullulation estivale attire aussitôt ceux qui s'en nourrissent.",
        ("coccinelle", "chrysope", "syrphe_larve"),
    ),
    "limace": (
        "Brouteuse nocturne des matières molles et de la litière humide ; on la "
        "trouve d'abord dans le paillis, parfois sur un semis tendre.",
        ("carabe", "herisson", "cloporte"),
    ),
    "doryphore": (
        "Coléoptère rayé inféodé aux Solanacées ; absent là où ne pousse ni "
        "pomme de terre ni tomate, il fuit le voisinage de l'ail.",
        ("carabe", "ail"),
    ),
    # --- catégorie auxiliaire ----------------------------------------------
    "coccinelle": (
        "Chasseuse de pucerons par excellence, adulte comme larve ; se tient "
        "près des fleurs nectarifères et des coins peu remués.",
        ("puceron",),
    ),
    "chrysope": (
        "Aux ailes vertes translucides ; sa larve dévore les pucerons tandis "
        "que l'adulte fréquente les fleurs ouvertes.",
        ("puceron",),
    ),
    "carabe": (
        "Coureur nocturne du sol, il traque limaces, cloportes et larves ; se "
        "réfugie le jour sous le bois mort et les pierres.",
        ("limace", "doryphore", "cloporte", "pile"),
    ),
    "merle": (
        "Oiseau résident omnivore : il sonde la terre pour en tirer les vers et "
        "picore volontiers les fruits tombés.",
        ("lombric", "fruit"),
    ),
    "herisson": (
        "Insectivore nocturne friand de limaces, de cloportes et de vers ; ne "
        "s'installe que si un tas de bois ou de feuilles lui offre un gîte.",
        ("limace", "lombric", "cloporte", "pile"),
    ),
    # --- catégorie detritivore ---------------------------------------------
    "lombric": (
        "Laboureur silencieux du sol : il digère la matière organique en humus "
        "et aère la terre par ses galeries.",
        ("merle", "herisson"),
    ),
    "cloporte": (
        "Crustacé terrestre des coins humides, il fragmente la litière et les "
        "fruits pourris ; fuit la sécheresse et le plein soleil.",
        ("carabe", "herisson", "limace", "fruit"),
    ),
}


def encyclo_meta(name: str) -> dict:
    """Métadonnée d'une espèce, prête à splatter dans `TrophicSpec(**...)`.
    Espèce inconnue (un pollinisateur, hors périmètre ④) → métadonnée vide :
    blurb absent, graphe vide — pas d'erreur, pas de fausse entrée d'encyclo."""
    blurb, liens = FAUNE_ENCYCLO.get(name, ("", ()))
    return {"blurb": blurb, "interconnexions": liens}
