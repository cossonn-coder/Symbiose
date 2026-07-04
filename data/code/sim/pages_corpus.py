"""
SYMBIOSE — sim/pages_corpus.py
CORPUS des PAGES SECRÈTES (sprint Voix narratives, tronçon ⑤, dette D18).
DONNÉE PURE — aucun import moteur, aucune logique. Spec : §7 de
`docs/conception/CONCEPTION_VOIX_NARRATIVES.md` (recopié VERBATIM).

Les pages secrètes sont du LORE PUR : elles ne débloquent rien, ne donnent aucun
bonus mécanique (décision adoptée §2.3). Elles RÉSONNENT avec ce que le joueur
vit — un thème qu'il commence à maîtriser — et récompensent l'exploration. Cinq
voix éditoriales (pastiche en STYLE, jamais de citation réelle longue → §7).

Chaque entrée :
  - `id`            : identifiant stable (P01..P24), clé du set `gs["pages"]`.
  - `voix`          : registre éditorial (A maraîcher · B jardinière · C savoirs
                      paysans · D herbiers · E sorcières) — purement informatif.
  - `concept`       : résonance thématique, sert au robinet *récompense* (la page
                      due d'un concept est celle dont `concept` == contexte).
  - `palier_theme`  : ordre de révélation INDICATIF (pas un gate dur, doc §2.3) —
                      la « prochaine page due » est la non-trouvée de plus petit
                      `palier_theme` (tri stable secondaire = `id`).
  - `robinet`       : canal d'obtention PRESSENTI (hasard / récompense / fouille).
  - `texte`         : le corps de la page (multi-lignes, recopié du doc).

Ce module est la SOURCE ÉDITORIALE ; toute la logique (les 3 robinets, l'état
opt-in, l'épuisement) vit dans `sim/pages.py` — séparation donnée / logique
(CLAUDE.md « un fichier = une responsabilité »). Dépassement de seuil toléré ici :
c'est un corpus de texte, pas du code (CLAUDE.md « garde-fou, pas dogme »).
"""
from __future__ import annotations

# --- Liste ordonnée des 24 entrées (doc §7 + sprint Grimpantes ⑤) -------------
# Format : (id, voix, concept, palier_theme, robinet, texte). On construit ensuite
# `PAGES` (dict id → champs) ET `ORDRE` (ids dans l'ordre du corpus) pour des
# itérations stables et déterministes.
_ENTREES = [
    # --- Voix A — le maraîcher de la non-action (pastiche Fukuoka) ------------
    ("P01", "A", "non-action", 4, "récompense",
     "On me demande quoi ajouter au sol. Je réponds : enlevez d'abord vos mains. "
     "La terre savait faire avant nous et fera après nous. Chaque geste qu'on "
     "s'épargne, c'est un geste que la nature reprend — et elle le fait mieux. Le "
     "jardinier accompli se reconnaît à ce qu'il a cessé de faire."),
    ("P02", "A", "succession", 2, "fouille",
     "Je n'ouvre plus la terre. J'enrobe mes graines d'argile et je les laisse au "
     "sol nu ; celles qui doivent lever lèvent, à leur heure, sans que je choisisse "
     "pour elles. Le sol couvert se ressème seul. Le sol retourné n'engendre que des "
     "herbes qu'on appelle mauvaises parce qu'elles arrivent avant qu'on les ait "
     "invitées."),
    ("P03", "A", "paillage", 2, "hasard",
     "La paille n'est pas un déchet : c'est la peau du sol. Sous elle, l'humidité "
     "reste, les vers travaillent, les graines d'herbe étouffent. J'ai rendu à la "
     "terre ce que la moisson lui avait pris, et la terre, l'année suivante, m'a "
     "rendu davantage."),
    ("P04", "A", "transcendance", 5, "récompense",
     "La dernière année, je n'ai presque rien fait. Les arbres se taillaient par "
     "leurs propres branches mortes, les bêtes mangeaient les bêtes, le trèfle "
     "nourrissait les racines. J'ai compris que mon rôle n'était pas de commander le "
     "jardin, mais d'apprendre à m'en retirer sans qu'il s'effondre."),

    # --- Voix B — la jardinière des allées (pastiche Sackville-West) ----------
    ("P05", "B", "floraison", 3, "fouille",
     "Plantez le blanc pour le soir : les fleurs pâles s'allument quand le reste "
     "s'éteint, et le jardin vous offre une seconde journée après le coucher du "
     "soleil. Le tabac, la bourrache au crépuscule, l'achillée qui retient la "
     "dernière lueur — c'est un luxe qui ne coûte que de l'attention."),
    ("P06", "B", "compagnonnage", 3, "récompense",
     "On ne plante pas une espèce, on compose une conversation. Le basilic chuchote "
     "à la tomate, la capucine attire les pucerons loin des choux comme une hôtesse "
     "détourne un fâcheux. Le mauvais jardin est un monologue ; le beau jardin, un "
     "dîner où chacun tient sa place."),
    ("P07", "B", "pollinisation", 2, "hasard",
     "Laissez une lisière folle au bout de l'allée. C'est là, dans ce désordre "
     "toléré, que vivent les alliés discrets : la guêpe minuscule, le syrphe déguisé "
     "en abeille, le crapaud sous la pierre. Un jardin trop propre est un jardin "
     "sans défenseurs."),
    ("P08", "B", "non-action", 4, "fouille",
     "La première année, elles dorment ; la deuxième, elles rampent ; la troisième, "
     "elles bondissent. Qui plante une vivace plante pour la jardinière qu'il sera "
     "dans trois ans. J'ai appris à aimer cette lenteur — elle me survivra, et c'est "
     "très bien ainsi."),

    # --- Voix C — les savoirs paysans (dictons, lune, météo) ------------------
    ("P09", "C", "météo", 2, "hasard",
     "Quand l'hirondelle rase le sol, garde ton foin ; quand l'araignée tisse au "
     "matin, le beau temps tient. Le ciel rouge du soir réjouit le berger, le ciel "
     "rouge du matin l'inquiète. Nos grands-parents lisaient le temps sur le dos des "
     "bêtes avant qu'on ne l'imprime sur du papier."),
    ("P10", "C", "lune", 3, "fouille",
     "Sème les feuilles en lune montante, les racines en lune descendante, dit-on "
     "depuis toujours. Que la sève écoute vraiment l'astre ou non, le dicton oblige à "
     "observer le ciel chaque nuit — et c'est l'observation, peut-être, le vrai "
     "secret."),
    ("P11", "C", "sol", 2, "récompense",
     "Ne maudis pas l'ortie : elle te dit que ta terre est grasse et vivante. Le "
     "chardon parle d'un sol compact, le pissenlit d'un sol tassé qu'il viendra "
     "percer. Les herbes que tu n'as pas semées sont les premières à te renseigner — "
     "encore faut-il savoir lire."),
    ("P12", "C", "azote", 3, "fouille",
     "Après les pois et les fèves, plante les gourmandes — choux, courges — car la "
     "légumineuse laisse derrière elle une richesse invisible. Nos aïeux ne "
     "connaissaient pas le mot azote ; ils savaient seulement qu'après la fève, tout "
     "pousse mieux."),
    ("P13", "C", "succession", 4, "hasard",
     "Une bonne glandée annonce un hiver rude, prétend-on. Vrai ou faux, l'arbre qui "
     "charge ses fruits prépare la forêt de dans cent ans. Le paysan plante des noix "
     "qu'il ne verra jamais mûres : c'est sa façon de croire en l'avenir."),

    # --- Voix D — les herbiers anciens (théorie des signatures, vertus) -------
    ("P14", "D", "indicatrices", 2, "fouille",
     "Les anciens enseignaient que Dieu avait marqué chaque herbe du signe de son "
     "usage : la feuille en forme de foie pour soigner le foie, la fleur jaune contre "
     "la jaunisse. Naïveté, sans doute — mais derrière la fable, l'idée juste que la "
     "forme d'une plante raconte sa vie et son lieu."),
    ("P15", "D", "accumulation", 3, "récompense",
     "On la nommait consolida car on lui prêtait le pouvoir de ressouder les chairs "
     "et les os. Ses racines plongent où nulle autre ne descend et remontent les "
     "trésors du sous-sol dans ses feuilles. Coupe-la, couche-la au pied de tes "
     "plants : ce qu'elle a volé à la profondeur, elle le donne à la surface."),
    ("P16", "D", "mycélium", 4, "fouille",
     "Sous l'écorce et sous la terre court un fil que l'œil ne voit pas. Les anciens "
     "parlaient d'un réseau d'âmes reliant les arbres d'une même forêt ; nous dirions "
     "aujourd'hui filaments. L'arbre malade est nourri par le bien portant, par des "
     "routes souterraines plus vieilles que nos chemins."),
    ("P17", "D", "allélopathie", 3, "hasard",
     "Garde-toi de planter sous le noyer : rien n'y prospère, et l'on disait jadis "
     "que son ombre rendait fou qui s'y endormait. Vérité paysanne sous la "
     "superstition — l'arbre empoisonne le sol autour de lui pour régner seul. Toute "
     "puissance se paie d'une solitude."),

    # --- Voix E — les cahiers de sorcières (préparations, décoctions) ---------
    ("P18", "E", "compost", 3, "récompense",
     "Emplis un seau d'orties fraîches, noie-les d'eau de pluie, oublie-les jusqu'à "
     "ce que ça pue le diable. Cette eau noire et puante, étendue au pied des plants, "
     "les fait bondir. Ce que la civilisation appelle engrais, la grand-mère "
     "l'appelait sa potion — c'était la même chose."),
    ("P19", "E", "non-action", 4, "fouille",
     "Fais bouillir la prêle, ce végétal d'avant les fleurs, et asperge-en tes "
     "rosiers au petit matin. On dit qu'elle arme la plante contre les moisissures. "
     "Mais la vraie sorcière sait que la meilleure potion est celle qu'on n'a pas eu "
     "besoin de faire : soigne le sol, et la plante ne tombera pas malade."),
    ("P20", "E", "transcendance", 5, "récompense",
     "Au bout de bien des saisons, j'ai cessé de commander à mon jardin et j'ai "
     "commencé à l'écouter. Il m'a appris que je n'étais pas sa maîtresse mais sa "
     "voisine. Le dernier sortilège n'est pas de plier la nature à ta volonté — c'est "
     "de désirer ce qu'elle fait déjà. Alors le jardin se garde tout seul, et tu es "
     "libre."),

    # --- Pages de la ROSÉE (sprint météo→champs ⑤, §6) — lore pur, zéro effet ---
    ("P21", "E", "météo", 3, "récompense",
     "On disait que la rosée de la nuit de la Saint-Jean n'était pas une eau "
     "ordinaire. Les filles s'en lavaient le visage avant l'aube pour garder le teint "
     "frais l'année durant ; les anciens y trempaient un linge pour soigner les yeux. "
     "Je n'en sais rien — mais j'ai vu que le jardin qui porte la rosée du matin "
     "traverse mieux les jours secs que celui qu'on a couvert trop tôt."),
    ("P22", "D", "météo", 2, "fouille",
     "Note d'herbier, page jaunie : « La gelée blanche n'est point la mort du jardin, "
     "mais sa rosée durcie. Au soleil revenu, le givre se résout en eau et désaltère "
     "la terre qu'il semblait mordre. Observe au matin clair d'hiver le sol nu qui "
     "blanchit le premier : c'est lui qui rend le plus à la nuit ce qu'il lui a "
     "emprunté. »"),

    # --- Pages des GRIMPANTES (sprint Grimpantes ⑤) — lore pur, zéro effet ---
    ("P23", "E", "lumière", 3, "fouille",
     "On dit le lierre traître parce qu'il monte sur le mur d'autrui. Sottise. Le "
     "lierre ne prend rien à qui le porte : il ne s'accroche qu'à ce qui ne lui "
     "sert plus, la vieille pierre, l'arbre mort, la ruine. Il ne vole pas la "
     "lumière — il va la chercher là où personne ne l'attendait, tout en haut, par "
     "des mille petites mains. Ce que tu abandonnes, lui le fait reverdir, et "
     "l'hiver, quand tout est nu, c'est chez lui seul que l'oiseau trouve un toit."),
    ("P24", "B", "pollinisation", 2, "récompense",
     "Le jasmin ne s'agrippe pas ; il faut lui tendre la main. Attache-le, guide-le "
     "le long du fil, et il te rendra ta patience au centuple — mais seulement le "
     "soir. Le parfum du jasmin est une horloge : il attend que le soleil tombe "
     "pour s'ouvrir et appeler les papillons de nuit. Plante-le sous une fenêtre "
     "qu'on ouvre l'été, jamais au fond du jardin : ce qu'il offre, il l'offre à "
     "l'heure où l'on ne jardine plus, où l'on ne fait que respirer."),
]

# Titres recopiés du doc §7 (gras de chaque entrée), indexés par id — gardés à
# part pour ne pas alourdir le tuple éditorial et rester relisibles.
_TITRES = {
    "P01": "Ne rien faire est le travail le plus difficile",
    "P02": "La graine et la boue",
    "P03": "L'ombre du fruitier",
    "P04": "Le verger qui se passe de moi",
    "P05": "Un jardin de lune",
    "P06": "De l'art de marier les voisines",
    "P07": "Éloge des bordures",
    "P08": "La patience des vivaces",
    "P09": "Le calendrier des anciens",
    "P10": "La lune montante",
    "P11": "Là où pousse l'ortie",
    "P12": "Ce que la fève rend à la terre",
    "P13": "L'année du gland",
    "P14": "De la signature des plantes",
    "P15": "La consoude, dite herbe à recoller",
    "P16": "Vertu du sureau et de l'aulne",
    "P17": "Du noyer et de son ombre maudite",
    "P18": "Le purin qui réveille la terre",
    "P19": "Décoction de prêle contre les fièvres du feuillage",
    "P20": "Le pacte du jardin",
    "P21": "La rosée de la Saint-Jean",
    "P22": "La gelée blanche n'est pas la mort",
    "P23": "Le lierre ne prend rien",
    "P24": "L'horloge du jasmin",
}

# `PAGES` = dict id → fiche complète. `ORDRE` = ids dans l'ordre du corpus (tri
# stable indépendant de l'ordre d'insertion d'un set côté logique).
PAGES = {
    pid: {
        "id": pid,
        "titre": _TITRES[pid],
        "voix": voix,
        "concept": concept,
        "palier_theme": palier_theme,
        "robinet": robinet,
        "texte": texte,
    }
    for (pid, voix, concept, palier_theme, robinet, texte) in _ENTREES
}

ORDRE = [pid for (pid, *_rest) in _ENTREES]
