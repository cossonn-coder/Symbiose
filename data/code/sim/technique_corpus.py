"""
SYMBIOSE — sim/technique_corpus.py
CORPUS de l'ENCYCLOPÉDIE, onglet TECHNIQUE — DONNÉE éditoriale pure (D60, ④).
Spec : `docs/faune/vie_macro/conception_vie_macro_identifiable.md` §5 + kickoff
`sprints/faune/vie_macro/sprint_vie_macro_identifiable/04_corpus_concept_technique.md`.

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

# --- Les techniques × 3 niveaux (alignées sur `encyclopedie_types.TECHNIQUES`) --
FICHES_TECHNIQUE: dict[str, dict[int, str]] = {

    "protection-climatique": {
        1: "Poser au-dessus des cultures une protection amovible — voile, cloche, "
           "ombrière — pour les mettre à l'abri d'un excès du ciel. La planche disparaît "
           "sous un écran le temps de l'épisode.",
        2: "Protéger du climat, c'est glisser un ÉCRAN entre la plante et le ciel pour "
           "corriger le milieu, jamais la plante : le voile et la cloche renvoient au sol "
           "la chaleur qu'il rayonnerait la nuit (moins de gel) et amortissent la grêle ; "
           "l'ombrière tamise le soleil d'été, si bien que la terre chauffe moins et perd "
           "moins d'eau. On agit sur le flux — chaleur, lumière — et la plante répond.",
        3: "C'est l'art de la PRÉPARATION : posé à temps, au calme, un écran sauve ce "
           "qu'une réaction en catastrophe ne rattraperait plus. Tout tient au discernement "
           "— couvrir contre le gel mais retirer avant que la cloche ne cuise au soleil, "
           "ombrer contre la canicule sans voler à la feuille la lumière dont elle vit. "
           "Aucun de ces abris n'est permanent : ils dépannent l'épisode. La résilience "
           "durable, elle, vient du sol vivant et de la diversité — l'écran n'est qu'un "
           "filet, tendu pour les coups les plus rudes.",
    },

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

    "greffe": {
        1: "Assembler deux plantes en soudant un rameau de l'une — le greffon — sur "
           "le tronc ou une branche de l'autre. Bien liées, elles cicatrisent "
           "ensemble et ne forment plus qu'un seul pied.",
        2: "Greffer, c'est exploiter la capacité des tissus de deux plantes proches à "
           "se ressouder : cambium contre cambium, la sève passe et la greffe reprend. "
           "Le porte-greffe fournit le SYSTÈME RACINAIRE et l'ancrage ; le greffon "
           "fournit la COURONNE — feuilles, fleurs, fruits. La compatibilité tient à "
           "la parenté botanique : même famille, la soudure prend ; trop éloignées, "
           "les tissus se rejettent.",
        3: "La greffe est l'outil du DÉCOUPLAGE : elle sépare le destin des racines de "
           "celui de la couronne, pour associer les qualités de deux plantes qu'un "
           "semis mêlerait au hasard — un porte-greffe vigoureux ou sobre en eau sous "
           "un fruit de choix. Elle offre aussi la précocité : sur un pied déjà "
           "établi, le greffon fructifie sans attendre. Mais chaque greffe est une "
           "double plaie à refermer, un geste précis, et la barrière de famille reste "
           "un mur : on ne greffe que dans une même lignée.",
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

    # --- Terrassement (hydrologie ⑦ + périphérie ⑤) : donner une FORME au terrain ---
    "terrassement": {
        1: "Remuer et déplacer de la terre pour changer la forme du sol : creuser un "
           "creux, ouvrir un fossé, relever une berge. Le terrain garde la trace du "
           "chantier.",
        2: "Terrasser ne fabrique pas d'eau : ça la fait ALLER ailleurs. L'eau de "
           "surface suit la pente et s'accumule au point bas — un creux devient donc un "
           "réservoir qui se remplit tout seul, un fossé une porte de sortie, une berge "
           "relevée une retenue. Rien de tout cela n'est instantané : on façonne la "
           "forme, et l'eau met des semaines à s'y installer. Remuer la terre a aussi "
           "un coût invisible : la vie du sol y est brassée et met du temps à revenir.",
        3: "Toute la sagesse du terrassement tient dans une distinction : la FORME "
           "dure, l'OUVRAGE s'entretient. Un creux excavé reste creux pour toujours ; "
           "une digue ou une dérivation sont des artefacts que le temps défait — l'eau "
           "reprend son cours à la première crue passée quelques années. Et ce qu'on "
           "retire ici manque là : gorger une berge assèche l'aval, drainer une "
           "cuvette prive la mare et son peuple. Le jardinier avisé façonne les creux "
           "et les pentes une fois, puis laisse l'eau faire le reste ; il se méfie des "
           "ouvrages qu'il devra surveiller jusqu'à la fin.",
    },

    # --- Techniques FORESTIÈRES (sprint PÉRIPHÉRIE ④) --------------------------
    # ⚠️ Philo #6 : le fait que certaines essences NE rejettent PAS est une DÉCOUVERTE.
    # Elle n'apparaît qu'au N3 (maîtrise), jamais en consigne préalable.
    "essartage": {
        1: "Abattre les arbres d'une lisière pour ouvrir la terre à la lumière. Une "
           "trouée franche remplace le couvert ; le bois abattu jonche le sol.",
        2: "Essarter, c'est prendre le terrain à la forêt. La lumière tombe d'un coup "
           "sur un sol qui n'en recevait plus, l'air et le vent y entrent, et la banque "
           "de graines dormantes se réveille : ronces, herbes hautes, pionnières "
           "comblent le vide en quelques saisons. Mais un couvert d'arbres n'est pas "
           "une haie : ce qui repousse vite est un fourré, pas une forêt.",
        3: "L'essartage est la coupe dont on ne revient pas vite : le vide se referme en "
           "quelques années, la STRUCTURE — les fûts, l'ombre, l'abri, le réseau du sol "
           "forestier — demande des décennies. Entre-temps le jardin paie : le vent "
           "n'est plus freiné et décroche en rafales, la terre nue du talus part en "
           "colluvions vers les premiers rangs, la faune de lisière déserte. C'est "
           "ainsi qu'un pays se déboise sans qu'aucune génération ne le décide : "
           "chaque coupe semblait raisonnable.",
    },
    "taillis": {
        1: "Couper les tiges au ras de la souche, tout près du sol. Le peuplement "
           "disparaît, il ne reste qu'un moignon de bois vif à terre.",
        2: "Le taillis exploite une propriété du bois vif : coupée bas, une souche "
           "VIVANTE relance des rejets depuis ses réserves racinaires, plus nombreux et "
           "plus vigoureux que la tige unique qu'on a prise. La souche est déjà "
           "enracinée, elle n'a pas à recommencer — c'est pourquoi le peuplement revient "
           "bien plus vite qu'après un abattage, et pourquoi le geste se répète toute la "
           "vie de la souche.",
        3: "Le taillis est le seul flux de bois qui ne s'épuise pas : couper le fait "
           "durer. Le bocage a vécu là-dessus des siècles — chauffage, piquets, "
           "fascines, sans jamais entamer le capital. Mais tout dépend de l'ESSENCE : "
           "le charme, l'aulne, le saule rejettent avec force ; le hêtre et le bouleau, "
           "eux, ne rejettent pas — sur eux le recépage n'est qu'un abattage déguisé, et "
           "la souche pourrit. Ça ne se lit pas sur l'arbre : ça s'apprend en le "
           "faisant, ou en écoutant ceux qui l'ont fait.",
    },
    "trogne": {
        1: "Couper la tête de l'arbre haut sur le tronc, en laissant le fût debout. La "
           "silhouette est rabattue mais rien n'est retiré du sol.",
        2: "Étêter prélève la tête sans toucher au pied : le fût reste, les tiges "
           "restent en place, et la couronne se reforme en une gerbe de rejets sur le "
           "moignon. C'est le prélèvement le plus rapide à se refaire — quelques années "
           "seulement, contre une décennie pour un taillis et une vie humaine pour une "
           "coupe rase. Comme rien n'est arraché, le sol reste couvert et l'abri du "
           "rideau tient.",
        3: "La trogne est l'arbre que l'on coupe pour qu'il DURE. Régulièrement rabattu, "
           "il ne porte jamais la tête trop lourde qui finirait par le fendre : un "
           "têtard vit des siècles là où son voisin libre en aurait vécu un. Son fût "
           "s'épaissit, se creuse, s'emplit de terreau — et devient un habitat à lui "
           "seul : chouettes, chauves-souris, insectes du bois mort, mousses. Fourrage, "
           "vannerie, bois de feu, ombre pour les bêtes : les paysans en ont tiré tout "
           "cela d'un arbre qu'ils n'ont jamais tué. C'est le geste le plus fréquentable "
           "de la lisière — celui qui prend sans défaire.",
    },

    "perchoir": {
        1: "Donner aux oiseaux un endroit où se poser, pour qu'ils sèment dessous les "
           "graines des fruits qu'ils ont mangés.",
        2: "Le merle avale la cerise, la framboise, la fraise des bois, et rejette le "
           "noyau ou la graine plus loin, là où il se pose : sous un arbre, sur un "
           "piquet, sur une branche morte. Une partie seulement des graines ressort "
           "capable de germer. Sans perchoir, il ne s'arrête pas au milieu de "
           "l'herbe et rien n'est semé.",
        3: "Les forestiers appellent cela la nucléation : un perchoir isolé dans une "
           "friche devient le noyau d'un bosquet. Les premiers buissons à baies "
           "attirent d'autres oiseaux, qui apportent d'autres graines, et le "
           "bosquet s'élargit à partir de ce point. Un arbre mort debout ou une haie "
           "jouent le même rôle sans qu'on ait rien à planter.",
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
