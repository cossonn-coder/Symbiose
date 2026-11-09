"""
SYMBIOSE — sim/pages_corpus.py
CORPUS des PAGES SECRÈTES (sprint Voix narratives, tronçon ⑤, dette D18).
DONNÉE PURE — aucun import moteur, aucune logique. Spec : §7 de
`docs/narration/voix/conception_voix_narratives.md` (recopié VERBATIM).

Les pages secrètes sont du LORE PUR : elles ne débloquent rien, ne donnent aucun
bonus mécanique (décision adoptée §2.3). Elles RÉSONNENT avec ce que le joueur
vit — un thème qu'il commence à maîtriser — et récompensent l'exploration. Cinq
voix éditoriales (pastiche en STYLE, jamais de citation réelle longue → §7).

Chaque entrée :
  - `id`            : identifiant stable (P01..P33), clé du set `gs["pages"]`.
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

# --- Liste ordonnée des 33 entrées (doc §7 + Grimpantes ⑤ + Luxuriance ④/⑤ +
#     sources de mulch équilibre invasion ⑤ + émetteurs allélopathie ⑤ + règne
#     fongique ⑤ du sol qui respire) ---------------------------------------------
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

    # --- Pages du CLONAL (sprint LUXURIANCE ④) — lore pur, zéro effet ---
    ("P25", "C", "succession", 3, "fouille",
     "Le fraisier des bois ne se sème pas, il marche. Chaque printemps il lance ses "
     "coulants comme autant de bras qui tâtent le sol, et là où la lumière tombe "
     "encore, une fille prend racine et s'affranchit de la mère. Là où l'ombre a "
     "gagné, le coulant sèche sans prendre : la plante sait s'arrêter d'elle-même. "
     "Laisse-lui un coin clair et reviens dans trois ans : tu trouveras un tapis que "
     "tu n'auras pas planté."),
    ("P26", "E", "compagnonnage", 4, "récompense",
     "Prends garde à la menthe. On la met en terre pour une tisane et l'on se "
     "retrouve, trois étés plus tard, avec une planche qu'elle a tout entière "
     "conquise par-dessous. Elle ne fait pas de graine ; elle rampe sous la terre, "
     "aveugle et patiente, et ressort où on ne l'attend pas, même sous les grands. "
     "Les anciennes la plantaient dans un vieux seau percé, enterré au ras du sol : "
     "on ne la garde qu'en lui posant des murs."),

    # --- Pages du TRIO CLONAL (sprint LUXURIANCE ⑤) — lore pur, zéro effet ---
    ("P27", "C", "succession", 3, "hasard",
     "La ronce et la framboise, c'est la même engeance : elles avancent par en "
     "dessous, à petits pas. Un rejet cette année, trois l'an prochain, et te voilà "
     "avec un fourré. Mais la framboise est honnête : elle ne sort ses rejets qu'au "
     "clair, jamais sous l'ombre épaisse. Qui veut des framboises sans corvée lui "
     "laisse un carré de lumière et la regarde s'y épaissir toute seule ; qui la "
     "néglige la retrouve trois rangs plus loin."),
    ("P28", "C", "compagnonnage", 4, "fouille",
     "On m'a donné trois brins de bambou dans un pot. J'ai cru faire un rideau vert "
     "au bout du potager. Cinq étés plus tard, c'est le potager qui était au bout du "
     "bambou. Il ne monte pas en graine, il ne fleurit pour ainsi dire jamais : il "
     "marche sous la terre, aveugle, et ressort où il veut, à l'ombre comme au soleil. "
     "La seule chose qui l'arrête, c'est un sol déjà pris — ou une tôle enfoncée "
     "droit, plus profond qu'on ne croit. Ne le plante jamais sans lui creuser sa "
     "prison d'abord."),
    ("P29", "E", "floraison", 2, "récompense",
     "La violette fleurit quand il n'y a rien d'autre, au sortir du froid, quand le "
     "bourdon sort de terre affamé. C'est pour cela qu'on l'aimait aux pieds des "
     "haies : non pour son parfum seul, mais parce qu'elle ouvre la table la "
     "première. Elle vit à l'ombre et s'y plaît, mais ses coulants ne s'enracinent "
     "qu'aux trouées de lumière — alors elle borde les clairières sans jamais "
     "étouffer le sous-bois. Une plante qui sait où s'arrêter est une plante de "
     "sage."),

    # --- Pages des SOURCES DE MULCH (sprint équilibre invasion ⑤) — lore pur ---
    ("P30", "A", "paillage", 3, "récompense",
     "Le chanvre, je ne le sème pas pour le récolter : je le sème pour qu'il "
     "travaille à ma place. En un été il monte plus haut qu'un homme et fait sous "
     "lui une ombre si épaisse que pas une herbe folle n'y lève. Quand je le couche "
     "à l'automne, sa tige donne une paille qui tient tout l'hiver là où celle du "
     "blé aurait fondu. Certaines plantes se cultivent pour la table ; celle-ci se "
     "cultive pour la terre, et la terre s'en souvient."),
    ("P31", "C", "sol", 2, "fouille",
     "Ne mets pas les aiguilles de sapin partout, disaient les anciens : elles "
     "aigrissent la terre. Longtemps j'ai cru à une superstition, jusqu'à voir "
     "dépérir mes salades au pied du conifère et prospérer, au même endroit, la "
     "myrtille et la bruyère. Ce que le sapin acidifie n'est pas perdu pour tout le "
     "monde : garde son tapis d'aiguilles pour les plantes de terre de bruyère, et "
     "porte ailleurs le reste. Chaque litière a son sol."),

    # --- Pages des ÉMETTEURS ALLÉLOPATHIQUES (sprint ALLÉLOPATHIE ⑤) — lore pur ---
    ("P32", "E", "allélopathie", 3, "fouille",
     "L'armoise, on la cueillait à la Saint-Jean pour en ceindre les reins et "
     "passer l'année sans fatigue ; on la brûlait pour chasser les mauvais esprits, "
     "on la pendait aux portes. Mais le jardinier sait l'autre face de sa vertu : là "
     "où l'armoise s'installe, plus rien ne lève. Elle empoisonne patiemment la "
     "terre autour d'elle pour n'y régner que seule. Herbe de sorcière, oui — mais "
     "sorcière jalouse, qui ne partage sa tache avec personne. Plante-la loin de ce "
     "que tu aimes, ou fais d'elle la gardienne d'une bordure que tu veux nue."),
    ("P33", "C", "allélopathie", 2, "récompense",
     "Sème le seigle épais quand les jours raccourcissent, disait le vieux, et ne "
     "touche plus à rien de l'hiver. Au printemps, couche-le sous ton pied et plante "
     "à travers son tapis : tu verras tes salades prospérer là où l'herbe folle ne "
     "reviendra pas. Ce n'est pas seulement l'ombre qui étouffe l'intruse, c'est le "
     "seigle lui-même qui empoisonne le sol contre elle — sans se nuire, car le grain "
     "ne craint pas son propre poison. Le meilleur désherbage est celui qu'une plante "
     "fait à ta place pendant que tu dors."),

    # --- Page de la FAUNE DE MARE (sprint HYDROLOGIE & MARÉCAGES ④) — lore pur ----
    ("P34", "C", "eau", 3, "hasard",
     "Ne comble pas la flaque qui s'attarde au bas du jardin : c'est là que le monde "
     "grouille. L'eau qui dort n'est pas une eau morte. Sur elle danse au soir la nuée "
     "grêle des moustiques, et sur eux fond, immobile puis foudroyante, la demoiselle "
     "de gaze — la libellule, qui fut d'abord larve carnassière tapie sous cette même "
     "surface. Un jardin sans point d'eau est un jardin à demi peuplé. Le paysan qui "
     "creusait une mare au coin de son pré ne le faisait pas pour la beauté : il "
     "savait qu'une eau qui stagne appelle tout un peuple d'ailes, et que ce peuple "
     "dévore ce qui, ailleurs, nous dévore."),

    # --- Page de la SPHAIGNE / TOURBE (sprint HYDROLOGIE & MARÉCAGES ⑤) — lore ----
    ("P35", "C", "eau", 3, "fouille",
     "La mousse des marais garde tout et ne rend rien. Les anciens tiraient de la "
     "tourbière une eau brune et froide où la viande ne se gâtait pas, où le beurre se "
     "conservait des saisons, où l'on retrouvait parfois, intacts sous des siècles de "
     "sphaigne, des hommes et des bêtes que l'acide avait tannés comme du cuir. Rien "
     "n'y pourrit : la mousse boit l'air en même temps que l'eau, et sans air, la mort "
     "elle-même s'endort. Chaque coussin qui meurt s'ajoute au précédent sans se "
     "défaire — et c'est ainsi que naît la tourbe, un pouce par cent ans, mémoire "
     "empilée de tout ce qui a bu à cette eau. Qui assèche une tourbière ne détruit "
     "pas une flaque : il ouvre un livre que la mousse écrivait depuis mille ans."),

    # --- Page du ROSSOLIS / carnivore (sprint HYDROLOGIE & MARÉCAGES ⑥) — lore ----
    ("P36", "E", "carnivorie", 3, "fouille",
     "On l'appelle rossolis, la rosée du soleil, car ses feuilles perlent au matin "
     "d'une glu qui brille comme mille larmes — et c'est un piège. La mouche qui s'y "
     "pose ne repart plus : la feuille se referme lentement sur elle et la boit. Les "
     "vieilles cueillaient cette herbe des tourbières pour les poitrines prises et "
     "les verrues, mais s'en méfiaient : une plante qui se nourrit de chair n'est "
     "pas tout à fait une plante. Elle prospère pourtant là où rien d'autre ne veut "
     "pousser — dans l'acide, dans le vide, dans la faim. Là où la terre ne donne "
     "pas d'azote, le rossolis le prend au ciel, une aile après l'autre. C'est le "
     "secret des lieux pauvres : qui ne peut puiser apprend à chasser."),

    # Molène / bouillon-blanc (sprint MÉMOIRE D'INOCULUM ③) — lore médicinal & théorie
    # des signatures (voix D, herbiers anciens). Résonne avec le concept « maladie ».
    ("P37", "D", "maladie", 3, "récompense",
     "Le bouillon-blanc, herbe à mille vertus, dresse sa hampe laineuse là où la "
     "terre a été malade — sur les décombres, les friches lasses, les coins que le "
     "jardinier a trop tourmentés. Les anciens y voyaient un signe : quand la molène "
     "s'installe, écoute-la, car elle dit que le sol demande à reposer. Ses feuilles "
     "duveteuses, on les faisait sécher pour les poitrines encombrées, et sa fleur "
     "jaune, infusée, apaisait les toux de l'hiver — mèche de lampe des pauvres, "
     "flanelle du bon Dieu, on lui donnait cent noms. Mais sa vertu première n'est "
     "pas dans la tisane : c'est de pousser sans faiblir là où tout le reste "
     "pourrit. Elle ne guérit pas la terre — elle la nomme, et laisse le temps faire."),

    # --- Pages de la PÉRIPHÉRIE (sprint PÉRIPHÉRIE ⑥, conception §7) — lore pur ----
    # Le gisement le plus riche du projet : le bocage était une INFRASTRUCTURE, et son
    # arasement au XXᵉ siècle a rendu le vent et l'érosion. Aucune de ces pages ne dit
    # au joueur quoi faire (philo #6) : ce sont des voix qui ont vécu la leçon.
    ("P38", "C", "brise_vent", 3, "récompense",
     "Du temps de mon grand-père, entre chaque champ il y avait un talus, et sur le "
     "talus une haie. On croyait que c'était pour marquer les limites. C'était pour "
     "tout : le vent qu'elle cassait, le bois qu'elle donnait chaque hiver, les "
     "feuilles que mangeaient les bêtes, l'eau qu'elle buvait au bas des pentes. Puis "
     "sont venus les grands engins, et l'on nous a expliqué que ces haies "
     "encombraient. En dix ans le pays est devenu lisse. Le vent, lui, n'a pas "
     "attendu dix ans : dès le premier printemps il a couché les blés et emporté la "
     "terre fine des labours. On a rendu les champs plus grands et le sol plus "
     "maigre. Ce qu'on avait mis trois siècles à tresser, une saison de tracteurs "
     "l'a défait."),
    ("P39", "C", "erosion", 2, "fouille",
     "L'essartage, chez nous, c'était l'affaire d'une génération et le remords de la "
     "suivante. On abattait le bord du bois pour gagner un carré de terre neuve, et "
     "cette terre-là donnait comme aucune autre — trois, quatre récoltes grasses, la "
     "richesse de la forêt qu'on venait de brûler. Puis la pluie prenait le talus nu, "
     "et ce que la forêt avait mis mille ans à faire descendait au ruisseau en deux "
     "orages. Mon père disait : on n'ouvre pas un bois, on l'emprunte. Ceux qui ne "
     "replantaient rien derrière eux laissaient à leurs fils un champ de cailloux et "
     "une source tarie."),
    ("P40", "C", "rejet_de_souche", 2, "récompense",
     "Le têtard, c'est l'arbre qu'on coupe pour qu'il dure. On lui prend la tête tous "
     "les cinq ou six ans, jamais le pied, et on le laisse recommencer. À force, le "
     "fût s'épaissit, se boursoufle, se creuse ; il s'y amasse du terreau, il s'y "
     "installe la chouette, la chauve-souris, tout un peuple qu'on ne voit pas. Les "
     "vieux d'ici montraient un saule au bord du pré en disant qu'il avait connu "
     "leurs arrière-grands-pères — et de fait, un têtard bien mené passe trois vies "
     "d'homme, quand son frère laissé libre se fend sous le poids de sa propre tête "
     "avant la centaine. C'est le seul arbre qui gagne à la serpe. Toute la sagesse "
     "du bocage est là : prends la tête, laisse le pied, et reviens."),
    ("P41", "C", "eau", 4, "fouille",
     "Qui possède la rivière ? Le meunier disait : l'eau qui tourne ma roue. Le "
     "pêcheur disait : l'eau qui porte mes truites. Le pré d'en bas disait : l'eau "
     "qui me vient. Et l'on plaidait des vies entières pour un batardeau de trois "
     "planches. La vérité que le procès n'écrivait jamais, c'est que celui qui relève "
     "l'eau chez lui l'enlève à celui d'en dessous — il ne fabrique rien, il "
     "déplace. Les anciens règlements de moulin obligeaient à ouvrer les vannes "
     "certains jours : non par charité, mais parce qu'un bief tenu fermé finit "
     "toujours par rompre, et l'eau, ce jour-là, reprend son chemin d'avant et "
     "n'épargne personne."),
    ("P42", "E", "lisiere", 3, "hasard",
     "Ne fais jamais tomber le vieux saule creux du bas du jardin. Ce n'est plus un "
     "arbre, c'est une maison. Passe-lui la main dans le ventre : de la terre, du "
     "bois pourri chaud, des bêtes que le jour n'a jamais vues. Au crépuscule il en "
     "sort une chouette, silencieuse comme un mensonge, et cette chouette-là mange "
     "chaque nuit les mulots qui te rongeaient les racines. On m'a dit que la dame "
     "blanche portait malheur ; j'ai vu qu'elle portait surtout mes récoltes. Un "
     "arbre à moitié mort travaille pour toi plus qu'un jeune bien portant — et il "
     "n'y a pas de sortilège là-dedans, seulement un creux, du noir, et le temps "
     "qu'il a fallu pour les faire."),

    # --- Pages du RÈGNE FONGIQUE (sol qui respire ⑤, D111 §3.4) — lore pur ------
    # Une page par champignon qui porte une histoire (règle « toute espèce = ses
    # voix », pages optionnelles). Concepts = ceux du carnet fongique : la page due
    # se révèle quand le concept atteint le palier 3 (robinet récompense,
    # `sim/champignon_voix.crediter_concept`) ou se trouve en fouillant.
    ("P43", "D", "parasitisme", 3, "récompense",
     "On a retrouvé dans la glace un homme mort depuis cinq mille ans, et dans sa "
     "bourse, deux champignons de bouleau enfilés sur une lanière. L'un, coriace, "
     "pour le feu : l'amadou, qu'on battait et qu'on séchait, prenait l'étincelle "
     "du silex et gardait la braise d'une halte à l'autre. L'autre pour le corps, "
     "contre les vers et les fièvres. Le polypore ne vient qu'aux bouleaux "
     "fatigués ; il les pourrit lentement par le cœur. Ce que l'arbre perdait, "
     "l'homme le portait à sa ceinture : le feu et le remède, tirés d'une mort "
     "lente."),
    ("P44", "E", "saprophytie", 3, "fouille",
     "Il y a dans l'herbe des prés, à l'automne, une petite clochette brune au pied "
     "si fin qu'on la prend pour une herbe. Les vieilles ne la cueillaient pas pour "
     "la soupe. Qui la mange voit, dit-on, ce que les bêtes savent : la couleur des "
     "choses se met à parler, l'herbe a un avis, la haie respire. Le lendemain on "
     "ne se souvient que d'une lumière trop forte et d'une grande fatigue. Je n'en "
     "dis pas plus : celle qui l'a goûtée une fois sait pourquoi on la laisse où "
     "elle est, et pourquoi pourtant on revient voir si elle a poussé."),
    ("P45", "E", "mycorhize", 3, "récompense",
     "Le chapeau rouge à pois blancs ne vient jamais seul : cherche le bouleau, il "
     "est là, ou le pin. Ils se tiennent par les racines comme deux vieux qui ne "
     "se parlent plus mais ne se quittent pas. Dans le Nord, on le faisait sécher, "
     "on le trempait dans le lait pour tuer les mouches qui venaient y boire — "
     "d'où son nom. D'autres le mangeaient pour voyager loin sans bouger, et le "
     "payaient de vomissements et d'une semaine de faiblesse. Il ne tue pas souvent. "
     "Il prend toujours quelque chose."),
    ("P46", "C", "mycorhize", 4, "fouille",
     "Ma grand-mère connaissait un pommier, au bas du clos, sous lequel les "
     "morilles revenaient chaque printemps depuis avant sa naissance. Elle n'y "
     "menait personne. Elle disait qu'il fallait un arbre vieux, une terre jamais "
     "retournée, et une pluie tiède en mars — et qu'on ne plante pas une morille "
     "comme on plante un chou. L'année où l'on a arraché le vieux verger pour en "
     "planter un neuf, plus rien n'est venu, et rien n'est jamais revenu. Le "
     "champignon n'était pas dans la terre : il était entre la terre et l'arbre, "
     "et c'est cela qu'on avait arraché."),
    ("P47", "E", "sosies", 3, "récompense",
     "Les ronds de sorcière, on les voit au matin dans les prés : un cercle d'herbe "
     "plus verte, et dessus, en couronne, des petits chapeaux blancs. On disait que "
     "les fées y avaient dansé, et que celui qui entrait dans le cercle dansait "
     "jusqu'à mourir. La vérité est plus simple et plus froide : le champignon "
     "pousse en rond parce qu'il grandit depuis son centre, d'année en année, comme "
     "une onde dans l'eau. Et ces chapeaux blancs, si pareils au rosé qu'on cueille "
     "pour l'omelette, sont de ceux qui tuent. Regarde les lames : rose, tu manges ; "
     "blanc, tu passes. Les fées n'y sont pour rien."),

    # Plantain lancéolé (sprint TRÈFLE DOMINANT ②) : lore de la plante des chemins.
    ("P48", "D", "succession", 3, "hasard",
     "L'herbe aux cinq coutures, on la trouve où l'on marche : aux seuils, aux "
     "ornières, le long des chemins de vaches. Plus on la foule, mieux elle se plaque. "
     "Les bergers en froissaient une feuille sur la piqûre d'abeille ou la coupure de "
     "serpe, et la douleur passait le temps de finir la journée. On disait qu'elle "
     "suivait les pas de l'homme d'un pays à l'autre, et c'est vrai : là où un sentier "
     "s'ouvre, elle est déjà dessus. Quand tu ne sais plus où passait un vieux chemin, "
     "cherche-la."),

    # Trèfle à quatre feuilles (sprint TRÈFLE DOMINANT ③) : le folklore du pied rare.
    # Id P49 : le kickoff prévoyait P34, déjà prise (« Ne comble pas la flaque »).
    ("P49", "C", "reproduction", 3, "hasard",
     "Chez nous on ne cherchait pas le trèfle à quatre feuilles. Qui se met à quatre "
     "pattes pour ça rentre bredouille avec les genoux verts. On le trouvait en menant "
     "les vaches, en regardant ailleurs. Une feuille pour la foi, une pour l'espoir, une "
     "pour l'amour, et la quatrième pour la chance, disaient les Irlandaises de passage. "
     "Ma tante le glissait dans le soulier droit de qui partait au loin, et le séchait "
     "dans le missel pour les autres. Il n'en vient jamais deux au même endroit : j'ai "
     "retourné dix fois le pied de celui que j'avais trouvé, l'année d'après il n'y "
     "avait que des trois. Ne le cherche pas. Quand tu l'as, baisse-toi, et remercie."),

    # Noisetier (sprint ZOOCHORIE ③) : le coudrier des sourciers, savoir paysan.
    ("P50", "C", "eau", 3, "hasard",
     "Le sourcier de chez nous coupait sa baguette dans le coudrier, jamais ailleurs : "
     "une fourche de l'année, prise au levant, avant que la sève monte. Il la tenait "
     "les paumes en l'air, les coudes au corps, et marchait le pré à pas comptés. Là "
     "où la pointe plongeait, il plantait un piquet, et le puisatier creusait. Mon père "
     "disait que c'était le bois qui savait, pas l'homme ; ma mère, que l'homme "
     "regardait surtout où poussaient les joncs. Toujours est-il que le noisetier aime "
     "les pieds frais, et qu'on trouve de l'eau plus souvent sous une haie de coudriers "
     "que sous une lande d'ajoncs."),
]

# Titres recopiés du doc §7 (gras de chaque entrée), indexés par id — gardés à
# part pour ne pas alourdir le tuple éditorial et rester relisibles.
_TITRES = {
    "P50": "La baguette de coudrier",
    "P48": "L'herbe aux cinq coutures",
    "P49": "Celui qu'on ne cherche pas",
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
    "P25": "Le fraisier qui marche",
    "P26": "La menthe qu'on garde en cage",
    "P27": "Le fourré qui avance",
    "P28": "La prison du bambou",
    "P29": "La première table de l'année",
    "P30": "Le chanvre qui travaille pour moi",
    "P31": "Chaque litière a son sol",
    "P32": "L'herbe jalouse de la Saint-Jean",
    "P33": "Le seigle qui désherbe en dormant",
    "P34": "Ne comble pas la flaque",
    "P35": "La mousse qui garde tout",
    "P36": "Le rossolis qui chasse",
    "P37": "L'herbe qui nomme les terres malades",
    "P38": "Le pays qu'on a rendu lisse",
    "P39": "On n'ouvre pas un bois, on l'emprunte",
    "P40": "L'arbre que l'on coupe pour qu'il dure",
    "P41": "À qui appartient la rivière",
    "P42": "La dame blanche du saule creux",
    "P43": "L'homme des glaces et l'amadou",
    "P44": "La clochette qui fait parler l'herbe",
    "P45": "Le chapeau rouge et son bouleau",
    "P46": "Le pommier aux morilles",
    "P47": "Les ronds de sorcière",
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
