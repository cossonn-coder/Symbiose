"""
SYMBIOSE — sim/champignon_encyclo.py
Les VOIX des treize champignons (sprint « le sol qui respire » ⑤, D111 §3.4).
Spec : `docs/champs/sol/conception_sol_qui_respire.md` §3.4 +
`docs/narration/voix/conception_voix_narratives.md` (les 5 voix).

HISTORIQUE : ce module portait la fiche GÉNÉRIQUE unique « réseau mycélien »
(décision Q2 du sprint vie macro identifiable, clé `"champignon"`). Le tronçon ⑤
RENVERSE Q2 : chaque espèce du registre `fields/fongique.REGISTRE_FONGIQUE` a
désormais SA fiche, et la clé générique disparaît (le survol d'un carpophore envoie
la clé d'espèce, 7ᵉ champ du snapshot depuis 0.5.52).

DONNÉE éditoriale pure — aucun état, aucun RNG, jamais lue par le tick (golden
NEUTRE). Par espèce :
  - `concept`  : le concept de maîtrise que l'espèce enseigne (le carnet gate son
                 registre dessus) — saprophytie · mycorhize · parasitisme · sosies ;
  - `vu`       : ce que l'info-bulle dit AVANT le nom (ce qu'on VOIT ; les sosies se
                 ressemblent pour de vrai, un détail les sépare : lames, anneau…) ;
  - `comestibilite` : dite SEULEMENT une fois l'espèce nommée (`sim/champignon_voix`) ;
  - `fiche`    : encyclopédie 3 niveaux (1 voir · 2 cycle · 3 effets
                 écosystémiques + comestibilité — le niveau 3 s'ouvre au palier 3, le
                 même que le nom) ; voix « naturaliste qui observe » ;
  - `carnet`   : note de FRUCTIFICATION observée, descriptive (ce que je vois, sans
                 nom ni comestibilité) / interprétative (le rôle compris) — voix « je » ;
  - `article`  : rubrique du magazine (lecture, pas de geste d'inoculation).
Les pages secrètes (lore) vivent avec les autres dans `sim/pages_corpus.py` (P43-P47).
"""
from __future__ import annotations

# Concepts transversaux portés par le règne fongique (propres au carnet, comme
# `carnivorie` : hors `encyclopedie_types.CONCEPTS`).
SAPROPHYTIE, MYCORHIZE, PARASITISME, SOSIES = (
    "saprophytie", "mycorhize", "parasitisme", "sosies")

FICHES_CHAMPIGNON: dict[str, dict] = {
    # === Bois mort ===
    "pleurote": {
        "concept": SAPROPHYTIE,
        "vu": "éventails gris-bleu étagés sur le bois mort",
        "comestibilite": "comestible",
        "fiche": {
            1: "Chapeaux en éventail, gris ardoise à beige, serrés en consoles sur le "
               "bois tombé ; lames blanches qui descendent sur un pied court et latéral.",
            2: "Saprophyte du bois de feuillus : le mycélium digère la lignine et la "
               "cellulose de la branche morte, puis fructifie après les pluies d'automne. "
               "Revient sur la même pièce de bois tant qu'il reste à manger.",
            3: "Décomposeur de première ligne : il rend au sol ce que l'arbre a stocké, "
               "et le bois qu'il a travaillé devient humus et abri pour la petite faune. "
               "Comestible, sans sosie dangereux sur ce support — mais l'hypholome pousse "
               "sur le même bois.",
        },
        "carnet": {
            "descriptif": "Sur le bois tombé {l}, des éventails gris se sont étagés après la pluie.",
            "interprétatif": "Le bois mort {l} se mange de l'intérieur : la branche redevient sol, et les éventails gris en sont la récolte.",
        },
        "article": ("Le bois qui donne deux fois",
                    "Une bûche laissée à l'ombre humide nourrit le pleurote des années "
                    "durant : on cueille sur ce que le jardin a perdu."),
    },
    "hypholome": {
        "concept": SOSIES,
        "vu": "touffes serrées de chapeaux jaune soufre sur le bois mort",
        "comestibilite": "vénéneux — il pousse sur le même bois que les bons",
        "fiche": {
            1: "Petits chapeaux jaune soufre au centre roussâtre, en touffes denses sur "
               "les souches et le bois tombé ; lames jaunes virant au vert olive.",
            2: "Saprophyte du bois, très commun, fructifie de l'été aux gelées en "
               "touffes de dizaines de chapeaux. Même support, même saison que le "
               "pleurote et la collybie.",
            3: "Grand décomposeur des souches. Vénéneux : il partage le bois des espèces "
               "comestibles, et c'est la couleur des lames — verdâtres chez lui — qui "
               "les sépare, jamais le support.",
        },
        "carnet": {
            "descriptif": "Une touffe de chapeaux jaune vif a crevé l'écorce du bois mort {l}.",
            "interprétatif": "Cette touffe jaune {l} vit du même bois que les bons — ses lames verdâtres la trahissent, pas sa souche.",
        },
        "article": ("Même bois, autre lame",
                    "Sur une souche, plusieurs espèces se succèdent et se mêlent : on "
                    "n'y reconnaît rien au support, tout aux lames."),
    },
    "collybie": {
        "concept": SAPROPHYTIE,
        "vu": "chapeaux orangés et luisants, pied sombre velouté, en plein hiver",
        "comestibilite": "comestible",
        "fiche": {
            1: "Chapeaux orange miel, visqueux par temps humide, sur un pied brun "
               "noir velouté ; en bouquets sur le bois mort quand tout le reste a fané.",
            2: "Saprophyte du bois qui fructifie au cœur de l'hiver : il supporte le gel, "
               "dégèle et repart. Seul champignon du jardin entre les premiers froids et "
               "le printemps.",
            3: "Garde la décomposition active pendant la saison morte. Comestible ; son "
               "pied velouté sombre le distingue des touffes jaunes de l'automne.",
        },
        "carnet": {
            "descriptif": "Malgré le froid, des chapeaux orangés luisent sur le bois mort {l}.",
            "interprétatif": "Même en hiver le bois {l} se défait : un champignon du gel continue le travail que l'automne a commencé.",
        },
        "article": ("Cueillir en janvier",
                    "Le bois mort laissé au jardin est le seul garde-manger fongique de "
                    "l'hiver : là où il manque, il n'y a rien à trouver."),
    },
    # === Humus ===
    "coprin": {
        "concept": SAPROPHYTIE,
        "vu": "colonnes blanches écailleuses qui noircissent par le bord",
        "comestibilite": "comestible très jeune, avant que les lames noircissent",
        "fiche": {
            1: "Chapeau blanc en ogive, hérissé d'écailles, haut sur un pied creux ; en "
               "vieillissant ses lames noircissent et se liquéfient en encre.",
            2: "Saprophyte des sols riches et remués : compost, planches amendées, terre "
               "fraîchement travaillée. Pousse vite après la pluie et ne dure qu'un ou "
               "deux jours.",
            3: "Signe d'un humus abondant et actif — il répond aux gestes du jardinier "
               "plus qu'aucun autre. Comestible tout jeune seulement : l'encre le rend "
               "vite immangeable.",
        },
        "carnet": {
            "descriptif": "Des colonnes blanches écailleuses ont surgi {l} ; le lendemain, leur bord tournait à l'encre.",
            "interprétatif": "Le coprin sort {l} parce que la terre y est grasse : il dit ce que mes apports ont nourri.",
        },
        "article": ("Le champignon du tas de compost",
                    "Un sol riche et souvent remué appelle le coprin chevelu : il sort "
                    "en une nuit et noircit en deux jours."),
    },
    # === Prairie ===
    "rose_des_pres": {
        "concept": SAPROPHYTIE,
        "vu": "chapeau blanc dans l'herbe, lames roses sous le chapeau",
        "comestibilite": "comestible — mais le clitocybe pousse dans la même herbe",
        "fiche": {
            1: "Chapeau blanc soyeux, charnu, dans l'herbe rase ; lames libres rose vif "
               "qui brunissent avec l'âge ; un anneau fragile au pied.",
            2: "Saprophyte des prairies : il vit de la matière morte du gazon, à la fin "
               "de l'été, quand une pluie suit les chaleurs.",
            3: "Indicateur d'une prairie ancienne non retournée. Comestible ; ses lames "
               "roses le séparent du clitocybe blanc qui partage son herbe.",
        },
        "carnet": {
            "descriptif": "Dans l'herbe {l}, des chapeaux blancs aux lames roses sont apparus.",
            "interprétatif": "L'herbe {l} qu'on n'a pas retournée nourrit un champignon de prairie — il vit de ce que le gazon laisse mourir.",
        },
        "article": ("Laisser l'herbe vieillir",
                    "Une prairie jamais labourée finit par donner ses rosés à la fin de "
                    "l'été : il suffit de ne pas la retourner."),
    },
    "clitocybe": {
        "concept": SOSIES,
        "vu": "petit chapeau blanc dans l'herbe, lames blanches serrées",
        "comestibilite": "mortel — le sosie blanc du rosé des prés",
        "fiche": {
            1: "Petit chapeau blanc mat, comme givré, souvent creusé au centre ; lames "
               "blanches serrées qui descendent sur le pied. Pousse en cercles.",
            2: "Saprophyte des pelouses et prairies, même herbe et même saison que le "
               "rosé des prés ; son mycélium avance en rond, d'année en année.",
            3: "Les ronds qu'il dessine dans l'herbe sont l'avancée de son réseau. "
               "Mortel : il imite le rosé, et seules ses lames blanches — jamais roses — "
               "le dénoncent.",
        },
        "carnet": {
            "descriptif": "Un cercle de petits chapeaux blancs s'est dessiné dans l'herbe {l}.",
            "interprétatif": "Ce cercle blanc {l} partage l'herbe du rosé : même lieu, même saison — ce sont les lames qui disent lequel est lequel.",
        },
        "article": ("Les ronds dans l'herbe",
                    "Un cercle de chapeaux blancs n'est pas une récolte : dans la même "
                    "prairie, le plus beau et le plus dangereux se ressemblent."),
    },
    "psilocybe": {
        "concept": SAPROPHYTIE,
        "vu": "minuscule chapeau pointu brun sur un pied fin, dans l'herbe",
        "comestibilite": "psychédélique — il trouble les sens",
        "fiche": {
            1: "Minuscule chapeau conique terminé par un téton, brun ocre, sur un pied "
               "long et fin ; isolé dans l'herbe haute.",
            2: "Saprophyte des racines mortes de graminées, en prairie humide, après "
               "les pluies d'automne.",
            3: "Discret recycleur des prairies. Psychédélique : il ouvre une vision qui "
               "trouble les sens pour un temps — le savoir paysan s'en méfiait autant "
               "qu'il le cherchait.",
        },
        "carnet": {
            "descriptif": "Dans l'herbe haute {l}, quelques chapeaux minuscules, pointus comme des clochettes.",
            "interprétatif": "Ces petites clochettes {l} vivent des racines mortes de l'herbe : la prairie se recycle par en dessous.",
        },
        "article": ("La clochette des prés",
                    "Il pousse seul, dans l'herbe humide de l'automne. On l'a cherché et "
                    "craint pour la même raison."),
    },
    # === Verger ===
    "morille": {
        "concept": MYCORHIZE,
        "vu": "chapeau alvéolé comme une éponge, au printemps sous les arbres",
        "comestibilite": "comestible, toujours cuite",
        "fiche": {
            1: "Chapeau creux, alvéolé comme une éponge, brun miel, sur un pied blanc "
               "creux ; au pied des fruitiers, au printemps.",
            2: "Seul champignon du printemps au jardin : son mycélium vit autour des "
               "racines des vieux fruitiers et fructifie quand la terre se réchauffe, "
               "après une pluie.",
            3: "Lié aux racines des pommiers et cerisiers, il dit un verger installé de "
               "longue date. Comestible, toujours cuite — crue, elle rend malade.",
        },
        "carnet": {
            "descriptif": "Au pied de l'arbre {l}, une sorte d'éponge brune a percé au printemps.",
            "interprétatif": "Sous le fruitier {l}, le champignon de printemps tient aux racines de l'arbre : un verger qui dure a son réseau.",
        },
        "article": ("Le vieux verger de mars",
                    "Les morilles ne se sèment pas : elles viennent aux vieux fruitiers "
                    "qu'on laisse vieillir, quand le sol se réchauffe."),
    },
    # === Mycorhiziens ===
    "cepe": {
        "concept": MYCORHIZE,
        "vu": "gros chapeau brun sur un pied ventru, une éponge sous le chapeau",
        "comestibilite": "comestible",
        "fiche": {
            1: "Chapeau brun noisette, épais, sur un pied ventru clair réticulé ; sous le "
               "chapeau, des tubes serrés comme une éponge au lieu de lames.",
            2: "Mycorhizien des chênes et des hêtres : son réseau enveloppe les racines, "
               "échange l'eau et le phosphore contre les sucres de l'arbre. Fructifie de "
               "l'été à l'automne, après les pluies.",
            3: "Partie du réseau qui relie les arbres de la lisière. Comestible ; il "
               "partage le pied des mêmes arbres que l'amanite phalloïde mortelle.",
        },
        "carnet": {
            "descriptif": "Sous le grand arbre {l}, un champignon trapu au pied ventru est sorti.",
            "interprétatif": "Ce champignon {l} ne pousse que lié à l'arbre : il lui porte l'eau et le phosphore, l'arbre le nourrit de sucre.",
        },
        "article": ("Le champignon qui a besoin d'un chêne",
                    "Pas de cèpe sans arbre hôte : il ne se cultive pas, il s'invite là "
                    "où chênes et hêtres ont grandi."),
    },
    "amanite_phalloide": {
        "concept": SOSIES,
        "vu": "chapeau vert olive, anneau blanc, pied dans un sac blanc",
        "comestibilite": "mortel — le plus dangereux du jardin",
        "fiche": {
            1: "Chapeau lisse vert olive à jaunâtre, lames blanches ; un anneau pendant "
               "au pied, et la base enfoncée dans une volve blanche en forme de sac.",
            2: "Mycorhizienne des chênes et hêtres, comme le cèpe : même arbre, même "
               "saison. Fructifie après les pluies de l'été et de l'automne.",
            3: "Elle aussi nourrit l'arbre de son réseau — le danger n'ôte rien à son "
               "rôle. Mortelle : la volve au pied, qu'il faut déterrer pour la voir, la "
               "distingue des comestibles.",
        },
        "carnet": {
            "descriptif": "Sous l'arbre {l}, un chapeau verdâtre s'est dressé, le pied pris dans une sorte de sac.",
            "interprétatif": "Même arbre que le bon champignon {l} : le réseau ne choisit pas, c'est le pied qu'il faut regarder.",
        },
        "article": ("Ce qui se cache au pied",
                    "Sous les chênes, le meilleur et le pire partagent les racines. La "
                    "base du pied, enterrée, dit tout."),
    },
    "amanite_tue_mouches": {
        "concept": MYCORHIZE,
        "vu": "chapeau rouge vif constellé de flocons blancs",
        "comestibilite": "psychédélique et toxique",
        "fiche": {
            1: "Grand chapeau rouge écarlate semé de flocons blancs, lames blanches, "
               "anneau et volve en bourrelets au pied.",
            2: "Mycorhizienne des bouleaux et des résineux, à l'automne après la pluie. "
               "Le champignon des contes.",
            3: "Partenaire racinaire du bouleau. Psychédélique et toxique : la vision "
               "qu'elle ouvre se paie en forces perdues.",
        },
        "carnet": {
            "descriptif": "Sous le bouleau {l}, un chapeau rouge à pois blancs, comme dans les livres d'images.",
            "interprétatif": "Le chapeau rouge {l} tient compagnie au bouleau par les racines — l'arbre et lui ne vont pas l'un sans l'autre.",
        },
        "article": ("Le chapeau des contes",
                    "Rouge à pois blancs, il ne pousse que là où vit un bouleau ou un "
                    "résineux : il en est le partenaire."),
    },
    # === Parasites ===
    "armillaire": {
        "concept": PARASITISME,
        "vu": "touffes de chapeaux couleur miel au pied d'un arbre ou d'une souche",
        "comestibilite": "comestible cuit seulement",
        "fiche": {
            1: "Chapeaux couleur miel parsemés de petites écailles, en grosses touffes au "
               "pied des arbres ou sur les souches ; un anneau cotonneux au pied.",
            2: "Parasite de faiblesse : il attaque les racines d'un arbre déjà affaibli "
               "(sécheresse, blessure), puis continue sur la souche morte. Ses cordons "
               "noirs courent sous l'écorce et dans le sol.",
            3: "Il achève ce que le stress a commencé et fait de l'arbre du bois mort "
               "pour les autres. Ses touffes au pied d'un arbre vivant sont un signe "
               "d'alarme. Comestible cuit seulement.",
        },
        "carnet": {
            "descriptif": "Une touffe couleur miel a poussé au pied de l'arbre {l}.",
            "interprétatif": "Le miel au pied de l'arbre {l} n'est pas bon signe : le champignon attaque les racines d'un arbre qui faiblissait déjà.",
        },
        "article": ("Quand le miel pousse au pied",
                    "L'armillaire ne s'en prend qu'aux arbres déjà mis à mal : soigner "
                    "l'eau et les blessures vaut mieux que tout remède."),
    },
    "polypore_bouleau": {
        "concept": PARASITISME,
        "vu": "console blanche et lisse en sabot, sur un tronc",
        "comestibilite": "immangeable — trop coriace",
        "fiche": {
            1: "Console épaisse en forme de sabot, blanche à gris brun dessus, pores "
               "blancs dessous ; fixée au tronc du bouleau.",
            2: "Parasite de faiblesse du bouleau : il pénètre un arbre affaibli, le "
               "pourrit de l'intérieur puis vit sur le tronc mort plusieurs années.",
            3: "Il recycle les bouleaux vieillissants et ouvre le bois aux pics et aux "
               "insectes. Immangeable ; jadis amadou, pansement et porte-feu.",
        },
        "carnet": {
            "descriptif": "Un sabot blanc s'est fixé sur le tronc du bouleau {l}.",
            "interprétatif": "Le sabot blanc {l} dit un bouleau en fin de vie : il le pourrit par le cœur et le rend au bois mort.",
        },
        "article": ("L'amadou des anciens",
                    "On le cueillait sec pour garder le feu et panser les plaies. Il ne "
                    "vient qu'aux bouleaux fatigués."),
    },
}
