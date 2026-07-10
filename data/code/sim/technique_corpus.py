"""
SYMBIOSE — sim/technique_corpus.py
CORPUS de l'ENCYCLOPÉDIE, onglet TECHNIQUE — DONNÉE éditoriale pure (D60, ④).
Spec : `docs/conception/CONCEPTION_VIE_MACRO_IDENTIFIABLE.md` §5 + kickoff
`sprints/sprint_vie_macro_identifiable/04_corpus_concept_technique.md`.

Miroir structurel de `sim/encyclopedie_corpus.py` (plantes) mais pour les
TECHNIQUES — les savoir-faire du jardinier (semer, arroser, tailler, composter…),
découverts à leur 1ʳᵉ utilisation réussie et affinés par la pratique (tronçon ③).
Une technique n'est ni une espèce ni un objet : c'est un GESTE-SAVOIR. Corpus à
part, aligné SUR `sim/encyclopedie_types.TECHNIQUES` (vérifié par le test).

`FICHES_TECHNIQUE[technique] = {1: "…N1…", 2: "…N2…", 3: "…N3…"}`
  - N1 (palier 1, découverte)     = ce qu'on FAIT : le geste, son effet visible.
  - N2 (palier 2, investissement) = le MÉCANISME : ce que ça change dans le milieu.
  - N3 (palier ≥ 3, maîtrise)     = le RÔLE ÉCOSYSTÉMIQUE : couplages, quand/pourquoi
                                     l'employer avec discernement, ses contreparties.

Voix « naturaliste qui observe » (3ᵉ personne, factuelle — jamais un tutoriel
impératif, philo #6 ; aucun chiffre de gameplay, philo #5). La contrepartie
écologique de chaque geste est NOMMÉE (le bêchage casse le réseau mycélien, etc.,
philo #1 : la solution facile s'use). DONNÉE PURE : aucun import moteur, read-only,
golden NEUTRE.
"""
from __future__ import annotations

# --- Les 11 techniques × 3 niveaux -------------------------------------------
FICHES_TECHNIQUE: dict[str, dict[int, str]] = {

    "semis": {
        1: "Déposer une graine dans la terre, à l'endroit et à la profondeur voulus. "
           "Plus tard, si tout va bien, une pousse perce.",
        2: "Semer, c'est placer une graine là où elle trouvera l'eau, la lumière et "
           "surtout la CHALEUR de sa levée : une graine ne germe pas à une date mais "
           "quand le sol atteint sa température de réveil. Semé trop tôt en terre "
           "froide, il attend — parfois pourrit. Chaque espèce a sa fenêtre.",
        3: "Le semis donne au jardinier la main sur la composition, là où la "
           "succession spontanée décide seule. Bien conduit, il respecte les vagues "
           "naturelles : rustiques d'abord sur sol frais, frileuses ensuite dans la "
           "chaleur. Il n'efface pas la banque-sol : autour du semis, les pionnières "
           "lèvent aussi. Associer les compagnes dès le semis prépare les couplages "
           "à venir.",
    },

    "broyage": {
        1: "Fragmenter du bois mort en copeaux. Le tas de branches devient un tas de "
           "broyat, prêt à couvrir le sol.",
        2: "Broyer le bois, c'est fabriquer sa propre matière de paillage à partir des "
           "déchets ligneux du jardin (tailles, arbres tombés). Le broyat de bois jeune "
           "(le BRF) est riche en carbone : posé au sol, il se décompose lentement et "
           "réveille les champignons décomposeurs plutôt que les bactéries.",
        3: "Le broyage boucle le cycle du carbone ligneux sans rien exporter : le bois "
           "qui aurait brûlé ou pourri en tas devient couverture nourricière. Frais, le "
           "BRF immobilise un temps l'azote de surface (les décomposeurs le réquisitionnent "
           "pour attaquer la lignine) — d'où l'intérêt de le laisser mûrir ou de l'associer "
           "à une source d'azote. Puis il rend tout, en humus stable et en réseau fongique.",
    },

    "arrosage": {
        1: "Apporter de l'eau à une plante ou à une parcelle. La terre fonce, le "
           "feuillage affaissé se redresse.",
        2: "Arroser comble la réserve d'eau du sol à portée des racines. L'eau "
           "s'infiltre, une part s'évapore aussitôt d'une surface nue, une autre est "
           "puisée et transpirée. Un arrosage rare et profond incite les racines à "
           "descendre ; des aspersions fréquentes et légères les maintiennent en "
           "surface, plus vulnérables à la sécheresse suivante.",
        3: "L'arrosage supplée le ciel, mais c'est une béquille : un sol vivant, "
           "couvert et grumeleux fait éponge et espace le besoin. En abuser tasse la "
           "surface et rend la plante dépendante ; trop d'eau chasse l'air des "
           "racines et les asphyxie. La bonne mesure suit la plante (pivot autonome "
           "ou racine traçante), la météo et le paillis en place — pas l'habitude.",
    },

    "récolte": {
        1: "Cueillir un organe mûr — feuille, fleur, fruit, racine. La plante se "
           "dégarnit un peu là où l'on prélève.",
        2: "Récolter prélève une part de la biomasse. Cueillir des fruits mûrs peut "
           "relancer la plante à en refaire ; couper des fleurs avant la graine "
           "(pincer le basilic) prolonge le feuillage. Ce qu'on emporte quitte le "
           "cycle du jardin : minéraux et matière partent avec l'organe récolté.",
        3: "La récolte est un flux sortant qu'il faut compenser. Ce qu'on prélève "
           "chez un gros consommateur appauvrit le sol : d'où l'intérêt de rendre par "
           "le compost, de faire suivre d'une fixatrice d'azote. Laisser monter "
           "quelques plantes à graine nourrit la banque-sol et les butineurs. "
           "Récolter, c'est arbitrer entre ce qu'on prend et ce qu'on laisse au "
           "cycle.",
    },

    "arrachage": {
        1: "Ôter une plante entière avec ses racines. Le sol se retrouve nu à cet "
           "endroit.",
        2: "Arracher supprime une plante d'un coup — racines comprises — pour libérer "
           "la place ou la lumière. Le geste perturbe : il ouvre le sol, expose la "
           "banque de graines dormantes qui lèvent alors en masse, et rompt les "
           "réseaux racinaires du voisinage.",
        3: "Le sol nu ne reste jamais nu : arracher relance la succession depuis le "
           "début, souvent au profit des pionnières qu'on voulait chasser. Agir sur "
           "le MILIEU (ombrer, concurrencer, couvrir) évince plus durablement qu'un "
           "arrachage répété. Retirer une plante, c'est aussi retirer ce qu'elle "
           "offrait : hôte d'auxiliaires, fixatrice d'azote, couvre-sol. Geste "
           "coûteux, à réserver.",
    },

    "bêchage": {
        1: "Retourner la terre en profondeur avec un outil. La surface est ameublie, "
           "les mottes brisées, la strate enfouie.",
        2: "Bêcher inverse les couches du sol : la vie de surface, qui aime l'air, se "
           "retrouve enfouie, et l'inverse. Le geste ameublit sur le moment mais "
           "tranche les galeries des vers et surtout le RÉSEAU MYCÉLIEN qui liait les "
           "grains de terre et reliait les racines entre elles.",
        3: "Le bêchage est la solution facile qui s'use : il défait ce qu'un sol "
           "vivant met des saisons à bâtir — structure grumeleuse, réseau fongique, "
           "étagement de la faune. Casser le mycélium coupe le wood-wide-web et prive "
           "les plantes du transport de phosphore qu'il assurait. Un sol qu'on ne "
           "retourne plus se structure seul, par les racines et les vers. Bêcher a un "
           "coût que le sol paie longtemps.",
    },

    "ameublissement": {
        1: "Décompacter la terre sans la retourner, en la fissurant en profondeur. "
           "Elle reste en place mais respire mieux.",
        2: "Ameublir — à la grelinette — soulève et fissure le sol sans inverser les "
           "couches : l'air et l'eau pénètrent plus profond, les racines suivent, "
           "mais la vie de chaque strate reste à son étage. Bien moins brutal que le "
           "bêchage, il préserve l'essentiel des galeries et du réseau fongique.",
        3: "L'ameublissement est le compromis du sol vivant : il soulage un sol tassé "
           "sans le saccager, là où le bêchage repartirait de zéro. Sur un sol déjà "
           "structuré et couvert, même lui devient superflu — les racines des "
           "couvre-sols et les vers ouvrent la terre gratuitement. C'est une aide "
           "ponctuelle à la reprise, pas un rituel.",
    },

    "taille": {
        1: "Couper des rameaux ou des tiges d'une plante ligneuse ou touffue. Sa "
           "silhouette se rééquilibre, la lumière entre.",
        2: "Tailler redirige la vigueur de la plante : en supprimant un rameau, on "
           "reporte sa croissance sur ceux qui restent (l'auxine et le jeu des "
           "bourgeons). On aère le cœur, on laisse entrer le jour, on limite "
           "l'encombrement et l'auto-ombrage.",
        3: "La taille arbitre entre feuillage et fructification, entre densité et "
           "aération. Un cœur ouvert sèche vite après la pluie et souffre moins des "
           "maladies fongiques ; une silhouette maîtrisée cesse de faire de l'ombre à "
           "ses voisines. Mais chaque coupe est une plaie et un stress : trop tailler "
           "affaiblit. Le geste juste accompagne la forme naturelle de la plante "
           "plutôt que de la forcer.",
    },

    "bouture": {
        1: "Séparer un fragment d'une plante — un bout de tige, de racine, une canne — "
           "et l'aider à faire ses propres racines pour former un pied entier.",
        2: "Bouturer, c'est exploiter le pouvoir de certaines plantes à se régénérer "
           "d'un morceau : maintenu au frais et à l'humide, le fragment referme sa "
           "plaie et émet des racines adventives. Le nouveau pied est un CLONE — pas "
           "un enfant issu de graine — identique à la mère, sans le hasard des "
           "croisements. Chaque espèce a ses aptitudes : les ligneuses souples et les "
           "aromatiques reprennent facilement, d'autres presque jamais.",
        3: "La bouture est l'outil de la FIDÉLITÉ : elle fixe et répand un individu "
           "qui plaît — une variété savoureuse, un port heureux, un pied bien adapté "
           "au lieu — là où la graine rebattrait les cartes. Mais elle a deux "
           "contreparties. Prélever un greffon puise dans les réserves de la mère et "
           "la fatigue. Et un jardin de clones perd la diversité qui le protège : "
           "partageant le même patrimoine, tous portent la même faiblesse. La bouture "
           "sert la constance ; c'est la graine qui sert l'adaptation.",
    },

    "compostage": {
        1: "Rassembler des déchets végétaux en tas ou en bac. Avec le temps, ils "
           "s'affaissent, chauffent, foncent et deviennent une terre sombre et "
           "friable.",
        2: "Composter, c'est confier de la matière organique à la faune détritivore "
           "et aux micro-organismes : vers, cloportes, bactéries, champignons la "
           "démontent. Un mélange équilibré entre matières vertes (azotées) et brunes "
           "(carbonées), aéré et humide, chauffe et se transforme en humus stable.",
        3: "Le compostage referme le cycle du jardin : ce que la récolte a emporté, "
           "il le rend au sol sous forme d'humus — nourriture des plantes, colle des "
           "grumeaux, réserve d'eau. Le tas est lui-même un écosystème : il attire et "
           "abrite une faune détritivore qui essaime ensuite au jardin. Épandre cet "
           "humus nourrit sans le brutaliser, à l'inverse d'un apport brutal. La "
           "litière laissée sur place composte déjà, lentement, toute seule.",
    },

    "apiculture": {
        1: "Installer et suivre une ruche. Un va-et-vient d'abeilles rayonne "
           "alentour, et l'on récolte parfois du miel.",
        2: "Tenir une ruche, c'est héberger une colonie de butineuses au cœur du "
           "jardin. Elles rayonnent sur toutes les fleurs à portée pour leur nectar "
           "et leur pollen, stockent le surplus en miel. La colonie dépend d'une "
           "floraison continue : une saison sans fleurs l'affame.",
        3: "L'apiculture couple étroitement la ruche et la floraison du jardin : plus "
           "de butineuses, c'est plus de fleurs fécondées, donc plus de fruits et de "
           "graines ; plus de fleurs étalées, c'est une colonie mieux nourrie. Le "
           "miel n'est que le surplus visible de ce service de pollinisation, bien "
           "plus précieux. Une ruche révèle et amplifie la santé nectarifère du lieu.",
    },

    "jardinage_hors_sol": {
        1: "Cultiver en pot, bac ou jardinière, avec un substrat rapporté, hors de "
           "la pleine terre. La plante y vit sur un volume clos et transportable.",
        2: "Hors-sol, le conteneur est un milieu MINIATURE et fermé : sa réserve "
           "d'eau, ses minéraux, sa vie microbienne tiennent dans un petit volume qui "
           "se réchauffe, se dessèche et s'épuise bien plus vite que la pleine terre. "
           "Le substrat (sa recette) fait tout ; un volume étroit brident la "
           "croissance et donne des plantes plus naines.",
        3: "Le hors-sol échange l'autonomie du sol vivant contre la mobilité et le "
           "contrôle : on rentre une frileuse au froid, on isole une terre acide pour "
           "la myrtille, on rapproche les aromates de la maison. Mais rien n'y est "
           "gratuit — l'eau, la fertilité, la fraîcheur doivent être apportées, car "
           "le grand cycle du jardin n'y coule pas. Un fond ouvert ou des lasagnes "
           "reconnectent partiellement le pot à la vie du dessous.",
    },

    "aménagement-habitat": {
        1: "Poser une structure qui abrite le vivant : tas de bois, pierrier, hôtel à "
           "insectes, haie, point d'eau. La petite faune s'y installe.",
        2: "Aménager un habitat, c'est offrir gîte, abri d'hiver et lieu de ponte à "
           "la faune auxiliaire : un tas de bois mort pour les carabes et les "
           "champignons saprophytes, une pierre chaude pour les lézards, des tiges "
           "creuses pour les abeilles solitaires. Chaque structure appelle son "
           "cortège d'espèces.",
        3: "L'habitat est l'infrastructure de l'équilibre : héberger les prédateurs "
           "et parasites naturels (coccinelles, syrphes, micro-guêpes, oiseaux) près "
           "des cultures, c'est laisser la régulation se faire seule plutôt que "
           "d'écraser chaque ravageur. Diversité d'abris, diversité d'auxiliaires, "
           "diversité de services. C'est l'inverse exact de la solution facile : on "
           "construit le milieu pour n'avoir plus à agir.",
    },

    "palissage": {
        1: "Guider une grimpante le long d'un appui et, s'il le faut, l'y attacher. "
           "La tige, au lieu de ramper au sol, s'élève et s'étale contre le support.",
        2: "Palisser, c'est donner à une plante volubile ou sarmenteuse la verticale "
           "qui lui manque : sans appui, une tige grêle ne se tient pas droite au-delà "
           "de sa hauteur autoportante et retombe. Certaines s'agrippent seules — "
           "vrilles qui enroulent, crampons qui adhèrent ; d'autres, sans organe "
           "d'accroche, doivent être nouées à la main à un tuteur, un treillis, une "
           "pergola. Attachée, la plante gagne la lumière du haut et résiste au vent.",
        3: "Le palissage discipline la lumière et l'air : étaler une grimpante contre "
           "un mur ou sur une pergola l'expose au soleil sans qu'elle étouffe ses "
           "voisines, aère son feuillage contre les maladies et met les fruits à "
           "portée. Mais un appui trop généreux invite l'exubérance — une vigoureuse "
           "palissée finit par ombrager tout ce qu'elle domine. L'appui bien placé "
           "range la croissance ; mal placé, il la déchaîne.",
    },
}
