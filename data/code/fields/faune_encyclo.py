"""
SYMBIOSE — fields/faune_encyclo.py
Métadonnée d'ENCYCLOPÉDIE de la faune nommée (tronçon ④e, modèle B
docs/faune/vie_macro/conception_faune_dediee.md §1.1/§3). DONNÉE PURE : jamais lue par le tick de la
simulation → golden NEUTRE. Le RENDU (l'entrée d'encyclopédie côté Godot, voix
naturaliste philo #5) est le tronçon ⑥ ; ici on ne porte que le texte et le
graphe relationnel, prêts à splatter dans `TrophicSpec`.

Module SÉPARÉ de population.py à dessein : ce dernier dépasse déjà le garde-fou
de taille (~350 LDC pur) ; on n'y ajoute pas 10 blurbs de données (kickoff ④e §4).
Aucun import (donnée pure) → aucun cycle de couche.

  blurb           : texte d'observation du naturaliste (ce qu'on VOIT, pas la
                    cause cachée — l'interprétation se mérite au palier de maîtrise).
  interconnexions : noms LIÉS dans le graphe §3 — proies/prédateurs nommés (les 10
                    espèces trophiques) + éléments du milieu qui font la niche
                    (`fruit` tombé/noué, `pile` de bois, `ail` répulsif, `ruche`/
                    `miel`, stades larvaires `chenille`/`syrphe_larve` des ponts ⑤).
                    Donnée PURE : les vraies boucles vivent dans `predators`/
                    `resource_fn`, pas ici. INVARIANT (testé) : tout `predators`
                    d'une espèce est inclus dans ses `interconnexions`, et le
                    sous-graphe entre les 10 espèces trophiques nommées est
                    SYMÉTRIQUE (si A cite B, B cite A). Les 5 pollinisateurs
                    (abeille/syrphe/papillon/bourdon/osmie, ⑥) sont décrits ici aussi
                    mais hors du sous-graphe trophique symétrique (ils pointent vers
                    la floraison/niche, pas vers des proies réciproques).
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
        ("carabe", "herisson", "cloporte", "couleuvre"),
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
        "picore volontiers les fruits tombés ; l'été il se gave de cerises et de "
        "framboises sur la branche, et sous ses perchoirs pointent des noyaux. Il "
        "guette pourtant le ciel, où plane plus grand que lui.",
        ("lombric", "fruit", "rapace", "cerisier", "framboisier", "fraisier"),
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
    # --- catégorie herbivore_vertebre (sommet trophique ①) ------------------
    # Le campagnol est la PROIE du sprint : ses prédateurs (rapace/couleuvre)
    # arrivent en ②, mais on POSE déjà le lien vers eux dans le graphe
    # relationnel (donnée pure, encyclopédie — la réciproque côté rapace/couleuvre
    # est ajoutée en ②, où la symétrie du sous-graphe sera vérifiée).
    "campagnol": (
        "Petit rongeur invisible qui vit sous terre : on ne voit de lui que ses "
        "monticules de terre fraîche et, çà et là, une plante qui flétrit sans "
        "raison apparente, racine ou collet rongés au ras du sol.",
        ("rapace", "couleuvre"),
    ),
    # --- catégorie super_predateur (sommet trophique ②) ---------------------
    # Ferment la chaîne PAR LE HAUT : leurs `predators` sont vides (ce sont les
    # sommets), mais leurs interconnexions listent leurs PROIES — réciproques des
    # liens posés côté campagnol/merle/limace (invariant de symétrie du graphe §3).
    "rapace": (
        "Silhouette en croix haut dans le ciel, immobile face au vent puis piqué "
        "foudroyant : il fond sur ce qui court à découvert, rongeur au ras du sol "
        "comme oiseau imprudent. Sa seule ombre fige le jardin.",
        ("campagnol", "merle", "mulot"),
    ),
    "couleuvre": (
        "Longue et lustrée, elle se love au soleil sur une pierre chaude ou près "
        "d'un tas de bois, immobile des heures ; à la fraîche, elle glisse traquer "
        "le rongeur dans sa galerie et la limace sous la litière. Inoffensive pour "
        "qui la laisse filer.",
        ("campagnol", "limace", "mulot"),
    ),
    # --- catégorie aquatique : faune de mare (hydrologie ④) -----------------
    # Mini-chaîne de l'eau stagnante : le moustique (proie, pond dans la flaque et
    # le marais) et la libellule (prédateur, chasse en vol stationnaire au-dessus
    # de l'eau). Leur niche = les tokens de MILIEU `eau`/`marais` (l'eau libre et le
    # marécage persistant). Sous-graphe SYMÉTRIQUE entre elles (moustique↔libellule).
    "moustique": (
        "Nuée grêle et vibrante qui monte des flaques et de l'eau qui dort ; ses "
        "larves frétillent sous la surface avant que l'adulte ne prenne l'air aux "
        "premières chaleurs.",
        ("libellule", "eau", "marais"),
    ),
    "libellule": (
        "Chasseresse ailée de gaze, immobile en vol stationnaire puis fulgurante "
        "au-dessus de la mare ; elle fond sur les moustiques qu'elle a vus éclore de "
        "l'eau où, larve carnassière, elle-même a grandi.",
        ("moustique", "eau", "marais"),
    ),
    # --- catégorie disperseur (zoochorie ⑤, D42) ----------------------------
    # Ils cachent des fruits à coque et en oublient : liés aux ARBRES qu'ils
    # plantent (clés catalogue chene/hetre/noyer/noisetier), pas à des proies. Hors
    # du sous-graphe trophique symétrique (aucune espèce animale citée).
    "geai": (
        "Oiseau criard au miroir d'ailes bleu ; à l'automne il fait la navette, le "
        "jabot gonflé de glands, et les enfouit un à un en terrain découvert, au "
        "pied d'un repère. Il en oublie plus qu'on ne croit.",
        ("chene", "hetre", "noyer", "noisetier"),
    ),
    "ecureuil": (
        "Petit roux à queue en panache qui court de cime en cime sans toucher terre ; "
        "il enterre noisettes et noix à la lisière des arbres et ne les retrouve "
        "pas toutes.",
        ("noisetier", "noyer", "hetre", "chene"),
    ),
    # Le MULOT (⑥) mange les graines tombées et en cache sous couvert : lié aux
    # arbres dont il vit les graines ET à ses deux prédateurs (symétrique).
    "mulot": (
        "Petit rongeur aux grands yeux noirs et aux longues oreilles, qui file la "
        "nuit sous les feuilles mortes ; au matin on trouve des noisettes percées "
        "d'un trou net, des noyaux rongés, et sous le bois mort une réserve oubliée.",
        ("rapace", "couleuvre", "chene", "hetre", "noisetier", "noyer", "cerisier"),
    ),
    # --- pollinisateurs (catalogue enrichi ⑤/⑥) ------------------------------
    # Liés à la FLORAISON qu'ils fécondent (→ `fruit`, nouaison), et selon le
    # type à un stade larvaire (pont ⑤ : `chenille`, `syrphe_larve`), une niche
    # (`ruche`, `miel` pour l'abeille sociale ; `pile` de bois pour l'osmie
    # maçonne) ou une proie de leur larve (`puceron` pour la syrphe). Donnée pure :
    # ces liens nourrissent l'encyclopédie ET les synergies de cartes (§8 physique).
    "abeille": (
        "Butineuse sociale infatigable ; elle relie la ruche aux corolles "
        "ouvertes et, de fleur en fleur, noue les fruits sans qu'on la voie "
        "travailler.",
        ("ruche", "miel", "fruit"),
    ),
    "syrphe": (
        "Mouche déguisée en guêpe, immobile en vol stationnaire au-dessus des "
        "fleurs ; sa larve, elle, dévore les pucerons sous les feuilles.",
        ("syrphe_larve", "puceron", "fruit"),
    ),
    "papillon": (
        "Visiteur diurne aux ailes larges butinant de fleur en fleur ; on "
        "l'admire sans songer que sa chenille, plus tôt, a brouté le feuillage.",
        ("chenille", "fruit"),
    ),
    "bourdon": (
        "Gros butineur pelucheux, premier levé par temps frais ; il fait vibrer "
        "les fleurs cachées que d'autres délaissent et féconde jusqu'aux "
        "Solanacées.",
        ("fruit",),
    ),
    "osmie": (
        "Abeille solitaire et maçonne ; elle niche dans le bois mort et "
        "pollinise les premiers arbres fruitiers avant l'éveil des ruches.",
        ("pile", "fruit"),
    ),
}


def encyclo_meta(name: str) -> dict:
    """Métadonnée d'une espèce, prête à splatter dans `TrophicSpec(**...)`.
    Couvre les espèces trophiques (faune nommée ④ + sommets ①② + faune de mare
    hydrologie ④) + les 5 pollinisateurs (⑥). Nom inconnu
    (champ larvaire intermédiaire, futur ajout) → métadonnée vide : blurb absent,
    graphe vide — pas d'erreur, pas de fausse entrée d'encyclo."""
    blurb, liens = FAUNE_ENCYCLO.get(name, ("", ()))
    return {"blurb": blurb, "interconnexions": liens}
