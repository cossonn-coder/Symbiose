"""
SYMBIOSE — sim/outil_corpus.py
CORPUS de l'ENCYCLOPÉDIE, onglet OUTIL — DONNÉE éditoriale pure (D60, ⑤).
Spec : `docs/faune/vie_macro/conception_vie_macro_identifiable.md` §5 + kickoff
`sprints/faune/vie_macro/sprint_vie_macro_identifiable/05_corpus_geste_outil.md`.

Miroir structurel de `sim/technique_corpus.py` mais pour les OUTILS — les OBJETS
manipulés (arrosoir, sécateur, bêche…) et les STRUCTURES posées (bac, pile, ruche,
pot). Un outil n'est ni un acte (geste) ni un savoir (technique) : c'est la chose
qu'on prend en main. Corpus à part, aligné SUR ce que `sim/encyclopedie_types.type_de`
classe `"outil"` (= membres de `OBJETS_TOUCHES` moins les `TECHNIQUES` ; vérifié
par le test).

⚠️ `grelinette` est ici (classé OUTIL par la priorité déterministe de ①, alors
qu'il est aussi un verbe `COUTS`) : l'objet vit dans l'onglet outil, son
SAVOIR-FAIRE est la technique `ameublissement`.

`FICHES_OUTIL[outil] = {1: "…N1…", 2: "…N2…", 3: "…N3…"}`
  - N1 (palier 1, découverte)     = l'OBJET : ce que c'est, à quoi il ressemble.
  - N2 (palier 2, investissement) = son USAGE JUSTE : ce qu'il fait bien, avec quelle
                                     technique il va, ce qu'il touche dans le milieu.
  - N3 (palier ≥ 3, maîtrise)     = QUAND S'EN PASSER : la sagesse écologique, la
                                     non-action, quand le milieu rend l'outil superflu.

Voix « naturaliste qui observe » (3ᵉ personne, factuelle — jamais impérative,
philo #6 ; aucun chiffre de gameplay, philo #5). Le N3 incarne la philo
transcendante : le meilleur outil est souvent celui qu'on n'a plus besoin de
prendre. DONNÉE PURE : aucun import moteur, read-only, golden NEUTRE.
"""
from __future__ import annotations

# --- Les 12 outils × 3 niveaux (membres de OBJETS_TOUCHES − TECHNIQUES) -------
FICHES_OUTIL: dict[str, dict[int, str]] = {

    "arrosoir": {
        1: "Un récipient à bec, souvent muni d'une pomme percée, pour porter l'eau à "
           "la main jusqu'aux plantes.",
        2: "L'arrosoir sert la technique de l'ARROSAGE : il dose et dirige l'eau au "
           "pied ou sur le feuillage. Sa pomme brise le jet en pluie fine qui ne "
           "creuse pas le sol ; sans elle, un filet nourri arrose profond au pied. Il "
           "comble la réserve d'eau à portée des racines (concept EAU).",
        3: "L'arrosoir est une béquille contre la sécheresse : un sol vivant, couvert "
           "d'un paillis et grumeleux, fait éponge et espace le besoin d'y recourir. "
           "Sur un jardin mûr et bien étagé, la rosée et l'ombre des voisines suffisent "
           "souvent. Le meilleur arrosage est celui qu'on n'a plus à faire.",
    },

    "sécateur": {
        1: "Une cisaille à main, deux lames courtes, pour couper net rameaux et tiges.",
        2: "Le sécateur sert deux gestes : la TAILLE, qui redirige la vigueur d'une "
           "ligneuse et aère son cœur, et la RÉCOLTE d'organes qu'on ne cueille pas à "
           "la main. Une coupe franche et propre cicatrise mieux qu'un arrachage — "
           "chaque plaie reste une porte d'entrée pour les maladies.",
        3: "Bien affûté, le sécateur accompagne la forme naturelle de la plante plutôt "
           "que de la forcer ; émoussé, il écrase et blesse. Mais tailler beaucoup "
           "affaiblit : une plante conduite selon son port réclame peu de coupes. Sur "
           "un jardin où chaque espèce a la place de sa silhouette, le sécateur se "
           "repose.",
    },

    "greffoir": {
        1: "Un couteau fin à lame très affûtée, parfois pourvu d'une spatule, pour "
           "tailler net greffon et porte-greffe et les assembler.",
        2: "Le greffoir sert la GREFFE : il ouvre une entaille propre dans le "
           "porte-greffe et biseaute le greffon pour que leurs tissus vivants — les "
           "cambiums — se touchent et se soudent. Une coupe lisse et juste conditionne "
           "la reprise : une plaie déchirée cicatrise mal et la greffe échoue.",
        3: "Le greffoir est l'outil du jardinier savant : il permet d'associer sous une "
           "seule plante les racines de l'une et la couronne de l'autre, pour la "
           "précocité ou la rusticité. Mais il n'abolit pas la barrière de famille — "
           "deux plantes trop éloignées ne se ressoudent jamais, si franche soit la "
           "coupe. Un outil de patience et de précision, réservé aux ligneuses "
           "fruitières.",
    },

    "bêche": {
        1: "Une lame plate emmanchée, qu'on enfonce au pied pour trancher et retourner "
           "la terre.",
        2: "La bêche sert le BÊCHAGE (retourner et enfouir) et le DÉRACINEMENT "
           "(extraire une plante entière). Elle ameublit vite et fort, mais inverse "
           "les couches du sol et tranche galeries de vers et RÉSEAU MYCÉLIEN — ce qui "
           "liait les grumeaux et reliait les racines.",
        3: "La bêche est la solution facile qui s'use : elle défait en un geste ce "
           "qu'un sol vivant met des saisons à bâtir. Casser le mycélium coupe le "
           "wood-wide-web et le transport de phosphore qu'il assurait. Un sol qu'on ne "
           "retourne plus se structure seul, par les racines et les vers ; la grelinette "
           "soulage sans saccager. Le jardinier de sol vivant range la bêche.",
    },

    "grelinette": {
        1: "Une fourche large à plusieurs dents et deux manches, qu'on bascule pour "
           "fissurer la terre sans la retourner.",
        2: "La grelinette sert l'AMEUBLISSEMENT : elle soulève et fissure le sol en "
           "profondeur sans inverser les couches. L'air et l'eau pénètrent, les racines "
           "suivent, mais la vie de chaque strate reste à son étage. Bien moins brutale "
           "que la bêche, elle épargne l'essentiel des galeries et du réseau fongique.",
        3: "La grelinette est le compromis du sol vivant — elle décompacte sans "
           "saccager là où la bêche repartirait de zéro. Mais sur un sol déjà "
           "structuré et couvert, même elle devient superflue : les racines des "
           "couvre-sols et les vers ouvrent la terre gratuitement. C'est une aide "
           "ponctuelle à la reprise, pas un rituel de saison.",
    },

    "paillage": {
        1: "La matière qu'on étale au sol pour le couvrir : paille, feuilles mortes, "
           "broyat de bois, aiguilles. Un tapis posé sur la terre nue.",
        2: "Le paillage est à la fois la couche et son effet : il ombre le sol (les "
           "adventices lèvent moins), freine l'évaporation (l'humidité reste piégée "
           "dessous) et se décompose lentement en humus. Sa NATURE compte — paille "
           "tendre, broyat ligneux, aiguilles acides n'ont ni la même durée ni les "
           "mêmes effets sur la faune et le sol.",
        3: "Un sol couvert est un sol vivant : le paillage imite la litière de la forêt "
           "— rien n'y reste nu. Il épuise la banque de graines enfouies, tempère les "
           "écarts de chaleur, nourrit les vers et le réseau fongique, et finit en terre. "
           "Le jardinier de sol vivant ne laisse jamais la terre à nu ; il l'habille et "
           "laisse la matière faire le travail du désherbage et de l'arrosage à sa place.",
    },

    "broyeur": {
        1: "Une machine à lames ou à rouleaux qui avale des branches et recrache des "
           "copeaux. Le bois brut en ressort en menus fragments.",
        2: "Le broyeur sert le BROYAGE : il réduit le bois de taille en broyat (BRF) "
           "utilisable comme paillage. Il traite ce qu'un sécateur laisse au sol — les "
           "rameaux, les squelettes ligneux — et les rend au jardin en couverture au lieu "
           "de les évacuer.",
        3: "Le broyeur ferme la boucle du bois : sans lui, la matière ligneuse s'entasse "
           "ou brûle ; avec lui, elle devient mulch et humus forestier. C'est l'outil qui "
           "relie la taille au paillage, le déchet à la ressource — l'esprit permacole fait "
           "machine. Le BRF qu'il produit nourrit d'abord les champignons, puis la terre.",
    },

    "fourche": {
        1: "Une fourche à dents, pour piquer, soulever et brasser des matières en vrac.",
        2: "Au compost, la fourche sert à RETOURNER le tas : elle le brasse et y "
           "réintroduit l'air dont les micro-organismes ont besoin pour digérer et "
           "chauffer. Elle homogénéise vert et brun, humide et sec, et relance une "
           "maturation qui s'essoufflait.",
        3: "La fourche accélère et lisse la maturation du compost, mais ce n'est qu'un "
           "coup de pouce : un tas bien monté — équilibré, aéré, humide — finit par "
           "mûrir seul sans qu'on le retourne. Comme partout au jardin, le brassage "
           "aide sans être obligatoire ; la patience fait aussi bien.",
    },

    "bac-à-compost": {
        1: "Un coffre ouvert, souvent de bois ou de grillage, où l'on rassemble les "
           "déchets tendres du jardin.",
        2: "Le bac contient et concentre le COMPOSTAGE : à l'abri, contenue, la matière "
           "verte et brune confiée à la faune détritivore chauffe et se transforme plus "
           "régulièrement qu'une litière éparse. C'est de là que sortira l'humus à "
           "épandre au sol.",
        3: "Le bac organise le retour de la matière au sol plutôt que de la laisser "
           "filer hors du terrain. Il est lui-même un petit écosystème qui abrite et "
           "essaime une faune détritivore. Mais la litière laissée sur place composte "
           "déjà, lentement, toute seule : le bac ne fait qu'accélérer et rassembler ce "
           "que le sol vivant sait faire.",
    },

    "pile-à-bois": {
        1: "Un tas de bois mort empilé et laissé en place, qui grise et se creuse au "
           "fil des saisons.",
        2: "La pile-à-bois abrite le COMPOSTAGE lent du bois : les champignons "
           "saprophytes attaquent les premiers le ligneux dur que peu d'autres savent "
           "digérer. Elle devient vite un HABITAT — abri d'hiver et garde-manger pour "
           "carabes, cloportes et faune fongivore.",
        3: "La pile-à-bois est recyclage patient et refuge à la fois : posée une fois, "
           "elle travaille seule des années durant, rendant au sol le carbone du bois "
           "en humus stable et hébergeant une faune qui rayonne alentour. C'est une "
           "structure de non-action par excellence : on la dresse, puis on la laisse "
           "vivre.",
    },

    "ruche": {
        1: "Une caisse à cadres où loge une colonie d'abeilles domestiques, entourée "
           "d'un va-et-vient de butineuses.",
        2: "La ruche héberge la colonie au service de l'APICULTURE : ses butineuses "
           "rayonnent sur toutes les fleurs à portée pour le nectar et le pollen, et "
           "fécondent au passage (concept POLLINISATION). Elle produit un surplus de "
           "miel qu'on peut prélever. Sa colonie dépend d'une floraison continue.",
        3: "La vraie valeur de la ruche n'est pas le miel mais la pollinisation qu'elle "
           "démultiplie : plus de butineuses, plus de fruits et de graines noués. Le "
           "couplage ruche↔floraison est le cœur du service. Une ruche révèle et "
           "amplifie la santé nectarifère du lieu — mais sans fleurs étalées dans le "
           "temps pour la nourrir, elle s'affame : c'est le jardin qui porte la ruche.",
    },

    "équipement-apicole": {
        1: "L'attirail du récoltant de miel : enfumoir, voile, lève-cadres, de quoi "
           "ouvrir la ruche sans heurt.",
        2: "L'équipement apicole sert la RÉCOLTE DU MIEL : il permet d'ouvrir la ruche "
           "et d'en prélever le surplus en dérangeant le moins possible la colonie. La "
           "fumée calme les abeilles, le voile protège le jardinier — un geste posé, "
           "pas une razzia.",
        3: "L'équipement n'a de sens que si l'on prélève avec mesure : le miel est le "
           "surplus stocké au-delà des besoins de la colonie, et lui en laisser assez "
           "l'aide à passer les saisons maigres. Prendre le surplus sans épuiser la "
           "source, c'est la même sagesse qu'à la récolte des plantes — et rappeler que "
           "la pollinisation vaut plus que le pot de miel.",
    },

    "pot": {
        1: "Un contenant mobile garni de substrat, où une plante vit sur un petit "
           "volume de terre transportable.",
        2: "Le pot sert le JARDINAGE HORS-SOL : c'est un milieu miniature et fermé dont "
           "la réserve d'eau, les minéraux et la vie microbienne tiennent dans peu de "
           "volume — donc se réchauffent, se dessèchent et s'épuisent vite. Son "
           "substrat fait presque tout ; son étroitesse bride la croissance. Il se "
           "déplace au gré de la lumière et du froid.",
        3: "Le pot échange l'autonomie du sol vivant contre la mobilité : on rentre une "
           "frileuse, on isole une terre acide, on rapproche du foyer. Mais rien n'y "
           "est gratuit — eau, fertilité, fraîcheur doivent être apportées, le grand "
           "cycle n'y coule pas. Un fond ouvert ou des lasagnes reconnectent le pot à "
           "la vie du dessous, et le rendent moins dépendant.",
    },

    "bac": {
        1: "Un grand contenant fixe garni de substrat, plus vaste qu'un pot, immobile "
           "une fois posé.",
        2: "Le bac de culture sert le JARDINAGE HORS-SOL à plus grande échelle : son "
           "volume, plus généreux qu'un pot, tempère mieux les à-coups d'eau et de "
           "chaleur, mais reste une terre choisie et fermée. Son substrat gouverne ce "
           "qui pourra y pousser ; fixé, il structure durablement l'espace.",
        3: "Le bac est un compromis entre le pot et la pleine terre : assez de volume "
           "pour la stabilité, assez contenu pour maîtriser une terre à part (une "
           "acidophile, un carré d'aromates). Comme tout hors-sol il reste à nourrir, "
           "mais des lasagnes ou un fond ouvert le relient peu à peu au cycle du sol "
           "vivant — le rapprochant de l'autonomie de la pleine terre.",
    },

    "amendement": {
        1: "Une matière qu'on répand sur le sol pour l'améliorer : ici le compost mûr, "
           "sombre et friable, sorti du bac.",
        2: "L'amendement sert le geste d'ÉPANDRE : déposé en surface, l'humus stable "
           "nourrit les plantes, colle les grumeaux et retient l'eau. Les vers et la "
           "faune l'incorporent peu à peu, sans brutaliser la structure — à l'inverse "
           "d'un apport violent enfoui à la bêche.",
        3: "L'amendement referme la boucle composter-retourner-épandre : il rend au sol "
           "ce que la récolte en avait sorti, relance le microbiome et arme les plantes "
           "contre le stress. Nourrir le SOL, pas la plante. Sur un jardin mûr où la "
           "litière tombe et se recycle sur place, le sol s'amende presque seul — "
           "l'apport n'est plus qu'un coup de pouce ponctuel.",
    },

    "tuteur": {
        1: "Un pieu fin planté à la verticale, à côté d'une plante qui a besoin de "
           "s'appuyer. Simple, discret, réutilisable d'une saison à l'autre.",
        2: "Le tuteur sert le PALISSAGE : sa tige mince est l'appui idéal des "
           "grimpantes à vrilles, qui l'enroulent d'elles-mêmes, et de tout pied "
           "élancé qui verse sous son poids ou le vent. On y noue aussi les cannes "
           "sans organe d'accroche. Il offre la verticale sans faire d'ombre.",
        3: "Le tuteur est l'appui minimal : juste assez pour tenir droit, sans "
           "encombrer. Une plante bien nourrie, endurcie par le vent qu'on l'a laissée "
           "affronter, développe un port trapu qui se passe souvent de béquille. Le "
           "tuteur soutient le temps que la plante s'affermisse — puis on l'oublie.",
    },

    "treillis": {
        1: "Une grille verticale, lattes de bois croisées ou fil tendu, dressée pour "
           "qu'une plante s'y étale à plat en montant.",
        2: "Le treillis sert le PALISSAGE des grimpantes sur une surface : ses "
           "mailles multiplient les prises pour les vrilles et reçoivent les tiges "
           "qu'on y noue. Étaler une plante contre lui l'expose au soleil et à l'air, "
           "aère son feuillage contre les maladies et met les fruits à hauteur d'œil.",
        3: "Le treillis organise l'espace vertical : contre un mur il crée un espalier, "
           "en clôture il fait écran vivant et brise-vent. Bien orienté, il gagne de la "
           "lumière sans voler celle des cultures basses. Mal placé, il devient le "
           "perchoir d'une grimpante qui étouffe tout le reste — l'appui range ou "
           "déchaîne selon la main qui l'installe.",
    },

    # --- Outils de PAYSAGE (sprint PÉRIPHÉRIE ④/⑤) ------------------------------
    # Le N3 de chacun tient la même leçon, déclinée : la hache défait ce qu'on ne
    # refera pas, la serpe prélève sans tuer, la pioche ouvre une plaie définitive.
    "hache": {
        1: "Une lourde lame emmanchée long, qu'on lance à deux mains pour fendre et "
           "abattre le bois debout.",
        2: "La hache sert l'ESSARTAGE : elle met à terre les arbres d'une lisière et "
           "ouvre la trouée. C'est l'outil de la coupe rase — celle qui rend d'un coup "
           "beaucoup de bois, beaucoup de lumière, et laisse une souche morte. Le bois "
           "abattu reste où il tombe : à charge d'aller le chercher.",
        3: "La hache est l'outil dont la trace dure le plus longtemps : ce qu'elle "
           "défait en une matinée, la lisière met des décennies à le rebâtir — le vent "
           "revient, la terre du talus descend, la faune du bord s'en va. Elle ne "
           "distingue rien : la même lame abat l'arbre qui aurait rejeté. Le paysan qui "
           "avait la serpe et la hache sortait la seconde le moins souvent possible.",
    },
    "serpe": {
        1: "Une petite lame courbe à manche court, tranchante à l'intérieur de la "
           "courbe, pour attaquer les tiges d'un geste tiré.",
        2: "La serpe sert les deux prélèvements qui ne tuent pas : le TAILLIS (couper au "
           "ras pour que la souche rejette) et la TROGNE (prendre la tête en laissant le "
           "fût). Sa lame courbe coupe le bois de brin près du sol ou sur le moignon "
           "sans arracher l'écorce — la plaie se referme et la repousse part de là.",
        3: "La serpe est l'outil du bocage : la même lame, revenant tous les quelques "
           "ans sur les mêmes souches et les mêmes têtes, a nourri des villages en bois "
           "de feu, en piquets et en fourrage sans jamais entamer le peuplement. Elle "
           "enseigne le rythme plus que la force — couper au bon endroit et revenir, "
           "plutôt que tout prendre une fois. Sur les essences qui ne rejettent pas, "
           "elle ne peut rien : là, ce qu'on croit récolter, on l'abat.",
    },
    "pioche": {
        1: "Une lame étroite et massive montée en travers d'un long manche, pour "
           "attaquer la terre dure et la roche.",
        2: "La pioche sert le TERRASSEMENT dans ce que la bêche ne peut pas : entailler "
           "un front de roche, ouvrir un passage dans un talus dur. Elle arrache la "
           "pierre par éclats, quelques dizaines de centimètres à chaque campagne.",
        3: "La pioche est le seul outil du jardin dont le travail ne se répare jamais : "
           "la roche retirée ne revient pas, et la paroi mise à nu continue de descendre "
           "en éboulis longtemps après le dernier coup. Ce qu'elle ouvre change l'ombre "
           "et l'abri du lieu pour toujours. Certaines échelles ne nous appartiennent "
           "pas : on la prend en sachant que le geste sera là après nous.",
    },

    # --- Le VOILE (sprint ACCÈS AUX GESTES ②) ---------------------------------
    # Vendu à l'Atelier (`sim/outils.py`), il est la porte de la technique
    # `protection-climatique` : sans fiche, l'outil qu'on vient d'acheter resterait
    # muet à l'encyclopédie. Les quatre autres outils neufs de l'Atelier (broyeur,
    # pots, tuteurs, greffoir) parlent déjà par les fiches `broyeur`, `pot`, `tuteur`
    # et `greffoir` ci-dessus.
    "voile": {
        1: "Une étoffe blanche, fine et légère, qu'on étend sur les rangs sans "
           "l'attacher serré. Elle laisse passer la pluie et la lumière.",
        2: "Le voile sert la PROTECTION CLIMATIQUE : posé avant une nuit claire, il "
           "retient la tiédeur que le sol rend après le coucher du soleil, et les "
           "jeunes pousses passent le gel dessous. Tendu avant l'orage, il amortit "
           "la grêle. Il agit sur l'air qui entoure la plante, jamais sur la plante.",
        3: "Le voile se pose sur un signe du ciel et se retire dès que le risque "
           "passe : laissé trop longtemps, il attendrit ce qu'il abrite. Une haie "
           "qui coupe le vent, un mur qui rend sa chaleur la nuit, une plante semée "
           "à son heure font le même office sans qu'on y pense. Le jardin abrité "
           "par sa propre forme n'a plus besoin d'étoffe.",
    },

    "pergola": {
        1: "Une structure haute, poteaux et traverses, sous laquelle on passe et sur "
           "laquelle une grimpante court en hauteur, formant une voûte de feuillage.",
        2: "La pergola sert le PALISSAGE en hauteur : elle porte une grimpante "
           "vigoureuse jusqu'au-dessus des têtes, où elle déploie une ombre fraîche "
           "l'été. Vrilles enroulées, cannes nouées, la plante y grimpe le long des "
           "montants puis s'étale sur le toit ajouré.",
        3: "La pergola fabrique un microclimat : l'ombre portée en été protège du "
           "dessèchement ce qui pousse dessous, tandis qu'une grimpante caduque laisse "
           "revenir le soleil d'hiver une fois ses feuilles tombées. Généreuse en "
           "appui, elle appelle l'exubérance — la voûte qu'on désire l'été peut, non "
           "conduite, condamner à l'ombre perpétuelle tout ce qui l'entoure.",
    },
}
