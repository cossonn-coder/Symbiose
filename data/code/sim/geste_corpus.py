"""
SYMBIOSE — sim/geste_corpus.py
CORPUS de l'ENCYCLOPÉDIE, onglet GESTE — DONNÉE éditoriale pure (D60, ⑤).
Spec : `docs/conception/CONCEPTION_VIE_MACRO_IDENTIFIABLE.md` §5 + kickoff
`sprints/sprint_vie_macro_identifiable/05_corpus_geste_outil.md`.

Miroir structurel de `sim/technique_corpus.py` mais pour les GESTES — les VERBES
d'action du joueur (planter, arroser, tailler, composter…), les clés de
`sim/actions/couts.COUTS`. Un geste est l'ACTE ; une technique est le savoir-faire
qui le sous-tend, un outil l'objet manipulé — trois onglets distincts qui se
répondent (les fiches se renvoient l'une à l'autre). Corpus à part, aligné SUR ce
que `sim/encyclopedie_types.type_de` classe `"geste"` (vérifié par le test).

⚠️ `grelinette` est classé OUTIL (collision verbe/objet tranchée en ① par la
priorité déterministe) : il vit dans `outil_corpus.py`, PAS ici — son SAVOIR-FAIRE
est la technique `ameublissement`.

`FICHES_GESTE[geste] = {1: "…N1…", 2: "…N2…", 3: "…N3…"}`
  - N1 (palier 1, découverte)     = ce que le geste FAIT de visible.
  - N2 (palier 2, investissement) = le MÉCANISME écologique qu'il engage.
  - N3 (palier ≥ 3, maîtrise)     = son RÔLE dans l'équilibre + ses effets de bord.

Voix « naturaliste qui observe » (3ᵉ personne, factuelle — jamais un tutoriel
impératif, philo #6 ; aucun chiffre de gameplay, philo #5). La contrepartie de
chaque geste direct sur le vivant est NOMMÉE (déraciner rouvre la banque-sol,
écraser ne touche qu'un individu, philo #1 : la solution facile s'use). DONNÉE
PURE : aucun import moteur, read-only, golden NEUTRE.
"""
from __future__ import annotations

# --- Les 20 gestes × 3 niveaux (clés de COUTS classées "geste") --------------
FICHES_GESTE: dict[str, dict[int, str]] = {

    "planter": {
        1: "Mettre une graine en terre à l'endroit choisi. Rien ne paraît d'abord, "
           "puis, les jours passant, une pousse perce le sol.",
        2: "Planter dépose la graine dans la couche de terre : elle y attend l'eau, "
           "la chaleur et la lumière de sa levée. Le geste engage la technique du "
           "SEMIS — la bonne profondeur, la bonne saison, la fenêtre de température "
           "propre à l'espèce. Placée trop tôt en sol froid, la graine patiente ou "
           "pourrit.",
        3: "Planter, c'est prendre la main sur la composition du jardin là où la "
           "succession déciderait seule. Le geste ne fait pas taire la banque-sol : "
           "autour de la graine choisie, les pionnières lèvent aussi. Bien conduit, "
           "il respecte les vagues naturelles et prépare les compagnonnages — associer "
           "dès le semis les plantes qui s'entraident.",
    },

    "arroser": {
        1: "Verser de l'eau sur une plante ou une parcelle. La terre fonce, le "
           "feuillage affaissé se relève.",
        2: "Arroser comble la réserve d'eau du sol à portée des racines (concept "
           "EAU). Une part s'infiltre en profondeur, une autre s'évapore d'une "
           "surface nue. Un apport rare et profond invite les racines à descendre ; "
           "des aspersions fréquentes les maintiennent en surface, fragiles.",
        3: "L'arrosage supplée le ciel, mais c'est une béquille : un sol vivant, "
           "couvert et grumeleux fait éponge et espace le besoin. En abuser tasse la "
           "surface et rend la plante dépendante ; noyer les racines chasse leur air "
           "et les asphyxie. La juste mesure suit la plante, la météo et le paillis en "
           "place — pas l'habitude.",
    },

    "recolter": {
        1: "Cueillir un organe mûr — feuille, fleur, fruit, racine. La plante se "
           "dégarnit un peu là où l'on prélève.",
        2: "Récolter emporte une part de la biomasse et, avec elle, des minéraux hors "
           "du cycle. Cueillir des fruits mûrs peut relancer la plante à en refaire ; "
           "pincer les fleurs avant la graine prolonge le feuillage. Le geste nourrit "
           "aussi le jardinier — un organe mûr consommé rend de la Vigueur.",
        3: "La récolte est un flux sortant qu'il faut compenser. Ce qu'on prélève chez "
           "un gros consommateur appauvrit le sol : d'où l'intérêt de rendre par le "
           "compost et de faire suivre d'une fixatrice d'azote. Laisser monter quelques "
           "plantes à graine nourrit la banque-sol et les butineurs. Récolter, c'est "
           "arbitrer entre ce qu'on prend et ce qu'on laisse au cycle.",
    },

    "deraciner": {
        1: "Arracher une plante entière, racines comprises. Le sol se retrouve nu et "
           "remué à cet endroit.",
        2: "Déraciner supprime une plante d'un coup pour libérer la place ou la "
           "lumière. Le geste perturbe fortement : il ouvre le sol, expose la banque "
           "de graines dormantes qui lèvent alors en masse, et tranche les réseaux "
           "racinaires du voisinage. C'est une action DIRECTE sur le vivant, coûteuse "
           "en Vigueur.",
        3: "Le sol nu ne reste jamais nu : déraciner relance la succession depuis le "
           "début, souvent au profit des pionnières qu'on voulait chasser. Agir sur le "
           "MILIEU — ombrer, concurrencer, couvrir — évince plus durablement qu'un "
           "arrachage répété. Retirer une plante, c'est aussi perdre ce qu'elle offrait : "
           "hôte d'auxiliaires, fixatrice d'azote, couvre-sol. Geste de dernier recours.",
    },

    "ecraser": {
        1: "Presser du doigt un ravageur — puceron, chenille, limace — pour le "
           "supprimer sur-le-champ.",
        2: "Écraser retire UN individu, ici et maintenant. Le geste est immédiat mais "
           "myope : il ne touche qu'une bête à la fois, jamais la cause de sa "
           "pullulation. C'est une action directe sur le vivant, coûteuse en Vigueur "
           "et perturbatrice.",
        3: "Écraser un à un est la solution facile qui s'use : tant que le milieu "
           "reste favorable au ravageur, il revient. Héberger ses PRÉDATEURS "
           "naturels — coccinelles, syrphes, micro-guêpes, oiseaux — par l'aménagement "
           "d'habitats régule sans effort et durablement. Le doigt dépanne dans "
           "l'urgence ; l'équilibre se construit dans le milieu.",
    },

    "favoriser_auxiliaire": {
        1: "Disposer un abri pour la petite faune utile : tas de bois, tiges creuses, "
           "pierre chaude, point d'eau. Peu à peu, des bêtes s'y installent.",
        2: "Favoriser un auxiliaire, c'est aménager un HABITAT — gîte, abri d'hiver, "
           "lieu de ponte — pour attirer et fixer la faune qui rend service : "
           "prédateurs de ravageurs, pollinisateurs, décomposeurs. Chaque structure "
           "appelle son cortège d'espèces.",
        3: "Ce geste bâtit l'infrastructure de l'équilibre : héberger près des cultures "
           "les régulateurs naturels, c'est laisser la lutte se faire seule plutôt que "
           "d'écraser chaque ravageur. Diversité d'abris, diversité d'auxiliaires, "
           "diversité de services. C'est l'inverse exact de la solution facile : on "
           "construit le milieu pour n'avoir plus à agir.",
    },

    "becher": {
        1: "Retourner la terre en profondeur à la bêche. La surface est ameublie, les "
           "mottes brisées, la strate du dessus enfouie.",
        2: "Bêcher inverse les couches du sol : la vie de surface, qui aime l'air, se "
           "retrouve enfouie, et l'inverse. Le geste ameublit sur le moment mais "
           "tranche les galeries des vers et surtout le RÉSEAU MYCÉLIEN qui liait les "
           "grains de terre et reliait les racines entre elles.",
        3: "Le bêchage est la solution facile qui s'use : il défait ce qu'un sol vivant "
           "met des saisons à bâtir — structure grumeleuse, réseau fongique, étagement "
           "de la faune. Casser le mycélium coupe le wood-wide-web et prive les plantes "
           "du transport de phosphore qu'il assurait. Un sol qu'on ne retourne plus se "
           "structure seul ; l'ameublissement à la grelinette soulage sans saccager. "
           "Bêcher a un coût que le sol paie longtemps.",
    },

    "pailler": {
        1: "Étaler une couche de matière au sol — paille, feuilles, broyat — autour "
           "des plantes. La terre nue disparaît sous un tapis protecteur.",
        2: "Le paillage couvre le sol : les graines d'adventices, privées de lumière "
           "et de terre nue, lèvent beaucoup moins, et l'eau s'évapore plus lentement "
           "sous le tapis qui coupe le soleil et le vent. La couche se décompose peu à "
           "peu et nourrit l'humus — ce qui protège finit par enrichir.",
        3: "Le paillage est le levier discret de la permaculture contre l'invasion : "
           "il n'arrache aucune adventice, il rend leur levée impossible et ÉPUISE peu "
           "à peu la banque de graines enfouies sous lui. Il tempère le sol, retient "
           "l'humidité, abrite la petite faune et se change en terre. Mais rien n'est "
           "gratuit : le mulch se décompose, il faut le renouveler — un sol qu'on couvre "
           "reste jeune tant qu'on l'entretient. C'est l'inverse du désherbage répété.",
    },

    "broyer": {
        1: "Réduire du bois mort — branches, rameaux, squelette d'une plante ligneuse "
           "au sol — en menus fragments. Un tas de copeaux remplace le bois brut.",
        2: "Le broyage transforme le bois du jardin en Bois Raméal Fragmenté (BRF), une "
           "matière de paillage à part : riche en carbone, elle se décompose lentement "
           "et nourrit d'abord les champignons du sol. Le bois mort ne s'évacue pas, il "
           "se recycle en couverture de sol.",
        3: "Broyer ferme une boucle : le bois d'une taille, d'un arbre tombé ou d'une "
           "pile devient le mulch de demain. Le BRF est le préféré des champignons "
           "saprophytes qui digèrent la lignine ; jeune, il capte un peu d'azote au sol "
           "(la faim d'azote), le temps que le réseau fongique l'installe — puis il "
           "restitue tout, en humus forestier. Rien ne se perd, tout se transforme.",
    },

    "tailler": {
        1: "Couper des rameaux ou des tiges d'une plante ligneuse ou touffue. Sa "
           "silhouette se rééquilibre, la lumière entre.",
        2: "Tailler redirige la vigueur de la plante : en supprimant un rameau, on "
           "reporte sa croissance sur ceux qui restent (l'auxine et le jeu des "
           "bourgeons). On aère le cœur, on laisse entrer le jour, on limite "
           "l'encombrement et l'auto-ombrage. C'est un geste direct sur le vivant.",
        3: "La taille arbitre entre feuillage et fructification, entre densité et "
           "aération. Un cœur ouvert sèche vite après la pluie et souffre moins des "
           "maladies fongiques ; une silhouette maîtrisée cesse d'ombrer ses voisines. "
           "Mais chaque coupe est une plaie et un stress : trop tailler affaiblit. Le "
           "geste juste accompagne la forme naturelle de la plante plutôt que de la "
           "forcer.",
    },

    "couper": {
        1: "Sectionner d'un coup un rameau ou une tige avec un sécateur. La branche "
           "tombe, la plaie reste nette là où la lame a passé.",
        2: "Couper est le geste BRUT de la coupe : on retranche une branche sans "
           "viser un point précis. C'est le premier pas — savoir manier l'outil, "
           "ouvrir une plaie franche — avant d'apprendre OÙ couper. La plante répond "
           "en reportant sa poussée sur les rameaux qui restent.",
        3: "Couper est l'apprentissage rudimentaire d'où naîtra la TAILLE, geste plus "
           "fin et ciblé. Manier la lame apprend le respect de la plaie : une coupe "
           "franche cicatrise mieux qu'un arrachage. Mais couper sans discernement "
           "épuise ou déséquilibre la plante — c'est en observant sa réponse qu'on "
           "passe du geste brut au geste juste.",
    },

    "bouturer": {
        1: "Prélever un fragment sur une plante et le mettre en terre ailleurs. "
           "Après un temps, le morceau reprend racine et devient une nouvelle plante, "
           "en tout point semblable à celle dont il vient.",
        2: "Bouturer multiplie une plante SANS graine : le greffon n'est pas un "
           "enfant issu de deux parents, c'est un CLONE — il porte exactement le même "
           "patrimoine que la mère, et jusqu'à l'état d'acclimatation qu'elle avait "
           "acquis. Aucun brassage, aucune surprise : la lignée se recopie à "
           "l'identique. Toutes les plantes ne s'y prêtent pas — seules les ligneuses "
           "souples et les aromatiques repartent aisément d'un fragment.",
        3: "La bouture fige un individu heureux et le répand : un pied vigoureux, bien "
           "adapté au lieu, se démultiplie tel quel. C'est le moyen de fixer un "
           "caractère qu'une graine dissoudrait dans le hasard des croisements. Mais "
           "prélever un greffon est une plaie pour la mère — elle y puise, se fatigue "
           "et se ressème d'autant moins. Et cloner, c'est renoncer à la diversité : "
           "un rang de clones partage la même faille et tombe ensemble devant la même "
           "maladie. Le geste sert la fidélité, jamais l'adaptation.",
    },

    "manger": {
        1: "Consommer un organe de plante — feuille, fleur, fruit. Le jardinier "
           "reprend des forces là, sur place.",
        2: "Manger un organe mûr rend de la Vigueur au joueur, d'autant plus que "
           "l'organe est arrivé à maturité. Le geste puise dans ce que la plante a "
           "élaboré à partir de lumière, d'eau et de minéraux : c'est le fruit du cycle "
           "qui revient au corps.",
        3: "Se nourrir au jardin ferme un cycle intime : le territoire nourrit le "
           "jardinier qui, par sa présence et ses soins, entretient le territoire. Un "
           "organe cueilli et mangé quitte le cycle du sol — comme toute récolte, il "
           "faudra le rendre autrement, par le compost ou la litière. Manger relie "
           "directement la santé du lieu à celle de qui l'habite.",
    },

    "poser_bac": {
        1: "Installer un bac à compost sur une tuile. On pourra y rassembler les "
           "déchets tendres du jardin.",
        2: "Poser un bac ouvre un lieu de COMPOSTAGE délimité : on y confie la matière "
           "verte et brune à la faune détritivore et aux micro-organismes qui la "
           "démontent. Fermé et contenu, le tas chauffe et se transforme plus "
           "régulièrement qu'une litière éparse.",
        3: "Le bac est une pièce d'infrastructure du cycle : il concentre la "
           "décomposition en un point d'où l'humus sera ensuite épandu au sol. Il est "
           "lui-même un écosystème — il attire et abrite une faune détritivore qui "
           "essaime au jardin. Poser un bac, c'est organiser le retour de la matière "
           "plutôt que de laisser filer la fertilité hors du terrain.",
    },

    "poser_pile": {
        1: "Dresser une pile de bois mort sur une tuile. Elle reste là, à se "
           "décomposer lentement.",
        2: "Poser une pile de bois engage un COMPOSTAGE lent du bois : ce sont les "
           "champignons saprophytes qui, les premiers, attaquent le ligneux dur que "
           "peu d'autres savent digérer. La pile devient un abri d'hiver et un "
           "garde-manger pour la petite faune.",
        3: "La pile de bois est à la fois recyclage lent et HABITAT : carabes, "
           "cloportes, champignons et faune fongivore s'y installent, puis rayonnent "
           "alentour. Elle rend au sol, sur des années, le carbone du bois sous forme "
           "d'humus stable. C'est une structure posée une fois qui travaille seule "
           "longtemps — de la non-action patiente.",
    },

    "composter": {
        1: "Déplacer la litière tendre d'une parcelle vers le bac à compost. Le tas "
           "s'y étoffe.",
        2: "Composter rassemble en un point la matière organique tendre pour la confier "
           "à la faune détritivore et aux micro-organismes. Un mélange équilibré de "
           "vert (azoté) et de brun (carboné), aéré et humide, chauffe et se change en "
           "humus stable — la technique du COMPOSTAGE au travail.",
        3: "Ce geste referme le cycle du jardin : ce que la récolte a emporté, il "
           "l'achemine vers le bac pour le rendre au sol en humus — nourriture des "
           "plantes, colle des grumeaux, réserve d'eau. Rassembler la litière plutôt "
           "que de la laisser filer, c'est retenir la fertilité sur le terrain. La "
           "litière laissée sur place composte aussi, plus lentement, toute seule.",
    },

    "empiler_bois": {
        1: "Porter le bois mort d'une parcelle vers la pile. La pile grossit d'autant.",
        2: "Empiler le bois concentre le ligneux dur en un lieu où les champignons "
           "saprophytes peuvent le décomposer (COMPOSTAGE lent du bois). Rassemblé, il "
           "forme un abri stable ; épars, il pourrit dispersé et nourrit peu.",
        3: "Ce geste range le carbone lent du jardin : le bois mis en pile devient à la "
           "fois recyclage de long terme et refuge de faune, au lieu d'encombrer les "
           "parcelles. Il alimente le réseau saprophyte qui, à terme, enrichit le sol "
           "en humus stable. Organiser le bois mort, c'est laisser travailler les "
           "décomposeurs à notre place.",
    },

    "retourner": {
        1: "Brasser le contenu du bac à compost à la fourche. Le tas s'affaisse, "
           "chauffe et se mélange.",
        2: "Retourner le compost y réintroduit de l'air : les micro-organismes qui "
           "digèrent la matière ont besoin d'oxygène pour travailler et chauffer. Le "
           "brassage homogénéise vert et brun, humide et sec, et relance une "
           "décomposition qui s'essoufflait — la maturation du COMPOSTAGE s'accélère et "
           "se lisse.",
        3: "Retourner est le petit soin qui fait mûrir le tas plus vite et plus "
           "également, vers un humus fin et stable. C'est un coup de pouce, pas une "
           "obligation : un tas bien monté finit par mûrir seul, sans qu'on le brasse. "
           "Le geste s'inscrit dans le trio du cycle — composter, retourner, épandre — "
           "qui ramène la matière au sol.",
    },

    "epandre": {
        1: "Répandre le compost mûr du bac sur une parcelle. La terre se couvre d'une "
           "couche sombre et friable.",
        2: "Épandre restitue au sol l'humus élaboré dans le bac : matière stable qui "
           "nourrit les plantes, colle les grumeaux et retient l'eau. Déposé en surface "
           "sans être enfoui, il est incorporé peu à peu par les vers et la faune, "
           "sans brutaliser la structure — à l'inverse d'un apport violent.",
        3: "L'épandage est le dernier maillon du trio composter-retourner-épandre : il "
           "referme la boucle en rendant au sol ce que la récolte en avait sorti. "
           "L'humus stable ainsi restitué relance le microbiome, améliore la structure "
           "et arme les plantes contre le stress. Nourrir le sol plutôt que la plante : "
           "c'est le geste qui incarne le cycle refermé du jardin.",
    },

    "poser_ruche": {
        1: "Installer une ruche dans le jardin. Un va-et-vient d'abeilles commence à "
           "rayonner alentour.",
        2: "Poser une ruche héberge une colonie de butineuses au cœur du jardin "
           "(technique de l'APICULTURE). Elles rayonnent sur toutes les fleurs à portée "
           "pour leur nectar et leur pollen, et fécondent au passage (concept "
           "POLLINISATION). La colonie dépend d'une floraison continue.",
        3: "La ruche couple étroitement la colonie et la floraison du lieu : plus de "
           "butineuses, c'est plus de fleurs fécondées, donc plus de fruits et de "
           "graines ; plus de fleurs étalées dans le temps, c'est une colonie mieux "
           "nourrie. Le miel n'est que le surplus visible d'un service de pollinisation "
           "bien plus précieux. Une ruche révèle et amplifie la santé nectarifère du "
           "jardin.",
    },

    "recolter_miel": {
        1: "Prélever du miel dans la ruche à l'aide de l'équipement apicole. On en "
           "retire une part, la colonie garde le reste.",
        2: "Récolter le miel emporte le SURPLUS que la colonie a stocké au-delà de ses "
           "besoins. Ce miel est du nectar de fleurs concentré et transformé : il rend "
           "de la Vigueur au jardinier. Prélever avec mesure laisse à la colonie de "
           "quoi passer les saisons maigres.",
        3: "Le miel récolté n'est que la face visible du vrai service de la ruche : la "
           "pollinisation qui noue les fruits et les graines de tout le jardin. Une "
           "récolte modérée respecte la colonie et le couplage ruche↔floraison dont "
           "dépend la fructification. Prendre le surplus sans épuiser la source, c'est "
           "la même sagesse qu'à la récolte des plantes.",
    },

    "poser_pot": {
        1: "Déposer un pot déjà garni de substrat et de plante à l'endroit voulu. Il "
           "reste mobile, on pourra le déplacer.",
        2: "Poser un pot installe un milieu HORS-SOL miniature et fermé : sa réserve "
           "d'eau, ses minéraux, sa vie microbienne tiennent dans un petit volume qui "
           "se réchauffe, se dessèche et s'épuise plus vite que la pleine terre. Le "
           "substrat choisi fait presque tout ; un volume étroit bride la croissance.",
        3: "Le pot échange l'autonomie du sol vivant contre la mobilité et le contrôle : "
           "on approche une aromate de la maison, on isole une terre acide pour la "
           "myrtille. Mais rien n'y est gratuit — l'eau, la fertilité, la fraîcheur "
           "doivent être apportées, car le grand cycle du jardin n'y coule pas. Un fond "
           "ouvert reconnecte partiellement le pot à la vie du dessous.",
    },

    "poser_bac_culture": {
        1: "Installer un bac de culture, plus vaste qu'un pot et fixé au sol, garni de "
           "substrat. Il ne se déplacera plus.",
        2: "Poser un bac de culture crée un milieu HORS-SOL de plusieurs parcelles, "
           "immobile : plus de volume qu'un pot, donc une réserve d'eau et de minéraux "
           "plus stable, mais toujours fermée. Le substrat et sa recette gouvernent ce "
           "qui pourra y pousser ; on y maîtrise une terre à part.",
        3: "Le bac de culture offre un compromis entre le pot et la pleine terre : "
           "assez de volume pour tempérer les à-coups d'eau et de chaleur, tout en "
           "restant une terre choisie et contenue. Fixé, il structure durablement "
           "l'espace. Comme tout hors-sol il reste à nourrir, mais des lasagnes ou un "
           "fond ouvert le relient peu à peu au cycle du sol vivant.",
    },

    "deplacer_pot": {
        1: "Prendre un pot et le porter ailleurs. Sa plante voyage avec sa terre.",
        2: "Déplacer un pot est un effort du seul jardinier — la plante et son milieu "
           "ne changent pas, seul leur emplacement bouge. On suit ainsi la lumière au "
           "fil des saisons, on met à l'abri du gel, on rapproche du soin. C'est le "
           "privilège du HORS-SOL : le milieu est transportable.",
        3: "La mobilité du pot est ce que la pleine terre ne permet pas : composer avec "
           "la course du soleil et les caprices du climat en déplaçant la plante plutôt "
           "que le milieu. Rentrer une frileuse, suivre l'ombre l'été, réunir les "
           "aromates près du foyer. Cette liberté a pour prix la dépendance du pot — "
           "coupé du grand cycle, il vit de ce qu'on lui apporte.",
    },

    "poser_tuteur": {
        1: "Planter un pieu fin à la verticale, à côté d'une plante qui a besoin de "
           "s'appuyer pour monter ou pour tenir droit.",
        2: "Poser un tuteur, c'est offrir la verticale à une grimpante à vrilles ou à "
           "un pied élancé : au-delà de sa hauteur autoportante, une tige grêle "
           "retombe faute d'appui. Le pieu lui rend la lumière du haut et l'ancre "
           "contre le vent. La plante s'y accroche ensuite d'elle-même, ou on l'y noue.",
        3: "Le tuteur est l'appui juste — le minimum pour tenir, sans faire d'ombre. "
           "Bien nourrie et endurcie par le vent qu'on l'a laissée affronter, une "
           "plante forge un port trapu qui se passe de béquille. On tuteure le temps "
           "de l'établissement, puis le geste devient inutile.",
    },

    "poser_treillis": {
        1: "Dresser une grille verticale contre laquelle une grimpante s'étalera à "
           "plat en montant.",
        2: "Poser un treillis multiplie les prises d'une surface verticale : les "
           "vrilles y trouvent des mailles à enrouler, les tiges nues s'y nouent. "
           "Étaler la plante contre lui l'expose au soleil et à l'air, aère son "
           "feuillage et met ses fruits à portée.",
        3: "Le treillis organise l'espace vertical du jardin : espalier contre un mur, "
           "écran vivant en clôture, brise-vent. Bien orienté, il gagne de la lumière "
           "sans voler celle des cultures basses ; mal placé, il devient le perchoir "
           "d'une grimpante qui étouffe le reste.",
    },

    "poser_pergola": {
        1: "Monter une structure haute — poteaux et traverses — sur laquelle une "
           "grimpante courra en hauteur, formant une voûte de feuillage.",
        2: "Poser une pergola porte une grimpante vigoureuse au-dessus des têtes, où "
           "elle déploie une ombre fraîche l'été. La plante grimpe le long des "
           "montants, s'accroche ou se noue, puis s'étale sur le toit ajouré — un "
           "microclimat ombragé naît dessous.",
        3: "La pergola fabrique un microclimat durable : ombre estivale qui protège du "
           "dessèchement, soleil d'hiver rendu par une grimpante caduque défeuillée. "
           "Généreuse en appui, elle appelle l'exubérance — non conduite, la voûte "
           "désirée l'été condamne à l'ombre perpétuelle ce qu'elle recouvre.",
    },

    "palisser": {
        1: "Nouer à la main la tige d'une grimpante à un support voisin, là où elle "
           "ne sait pas s'accrocher seule. La plante, attachée, se met à monter.",
        2: "Palisser attache une sarmenteuse — longues cannes sans vrille ni crampon — "
           "à un tuteur, un treillis ou une pergola : c'est le seul moyen pour elle de "
           "gagner la verticale. Nouée, elle s'élève vers la lumière du haut et le "
           "support la porte contre le vent, là où libre elle resterait prostrée.",
        3: "Le palissage discipline la lumière et l'air d'une plante qui, autrement, "
           "s'affalerait : on l'étale où on la veut, on aère son feuillage contre les "
           "maladies, on range sa croissance. Mais l'appui bien placé range quand "
           "l'appui mal placé déchaîne — une vigoureuse palissée finit par dominer et "
           "ombrager tout ce qui l'entoure.",
    },
}
