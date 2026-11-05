"""
SYMBIOSE — sim/encyclopedie_corpus/ligneux.py
Fiches des LIGNEUX et de la guilde humide : arbres pérennes, essences
forestières, guilde marécageuse (HYDROLOGIE ⑤), arbre de la trogne (PÉRIPHÉRIE ⑥).
DONNÉE éditoriale pure — aucune logique, aucun import moteur. Éclaté de
l'ex-monolithe `sim/encyclopedie_corpus.py` (402 LDC, zone rouge) au refactor de
clôture du sprint PÉRIPHÉRIE ; `__init__.py` réassemble `FICHES` dans le MÊME
ordre, l'API publique lue par les appelants est inchangée.

Voix « naturaliste qui observe » (3ᵉ personne, descriptive et factuelle), 3 niveaux
par entrée — cf. le docstring du paquet pour le contrat complet.
"""
from __future__ import annotations

FICHES_LIGNEUX: dict[str, dict[int, str]] = {
    # === Arbres pérennes ===
    "figuier": {
        1: "Petit arbre à grandes feuilles lobées, écorce grise lisse, figues "
           "vertes/violettes.",
        2: "Pérenne caduc méditerranéen, résistant à la sécheresse une fois établi ; "
           "aime la chaleur réverbérée d'un mur. Méridional, il ne lève spontanément de "
           "graine que sur sol bien chaud — contrairement aux ligneux tempérés qui "
           "germent au frais du printemps. Figue commune : elle noue sans pollinisateur et mûrit "
           "de la fin d'été au début de l'automne.",
        3: "Idéal en espalier sud (microclimat chaud, albédo du mur) ; figues = manne "
           "pour oiseaux et insectes en fin d'été. Ombre dense estivale.",
    },
    "pommier": {
        1: "Arbre à houppier arrondi, floraison blanche-rosée au printemps, pommes.",
        2: "Pérenne caduc nécessitant du froid hivernal (vernalisation) et une "
           "pollinisation croisée (deux variétés). Pommes mûres en septembre-octobre. "
           "Longévité de plusieurs décennies.",
        3: "Cœur du verger : fleurs = ressource pollinisatrice majeure du printemps ; "
           "sensible au carpocapse (guetter les auxiliaires/mésanges). Porte tout un "
           "cortège d'espèces.",
    },
    "cerisier": {
        1: "Arbre élancé, écorce annelée brillante, floraison blanche abondante, "
           "cerises.",
        2: "Pérenne caduc à floraison très précoce, sensible aux gelées tardives ; "
           "croissance rapide. Cerises mûres dès le début de l'été, vite tombées.",
        3: "Sa floraison hâtive est une des premières grandes tables des "
           "pollinisateurs ; cerises = aimant à oiseaux (dispersion des noyaux).",
    },
    "noyer": {
        1: "Grand arbre à large couronne, feuilles composées aromatiques, noix en brou.",
        2: "Pérenne caduc de grande taille, croissance lente, longévité séculaire ; "
           "émet de la juglone. Pollen porté par le vent : un noyer seul noue peu. Noix "
           "mûres en automne.",
        3: "Allélopathique : la juglone inhibe nombre de plantes sous sa couronne — crée "
           "une niche particulière. Ombre profonde ; noix nourrissent la faune.",
    },
    "chene": {
        1: "Arbre massif à couronne étalée, feuilles lobées, glands.",
        2: "Pérenne caduc de très longue vie, croissance lente ; symbiose "
           "ectomycorhizienne étendue.",
        3: "Espèce clé de voûte : héberge une biodiversité immense (insectes, oiseaux, "
           "champignons) ; glands = ressource majeure ; pivot du wood-wide-web de la "
           "lisière.",
    },
    # Essences forestières normandes (sprint RENDU AMBIANCE T1, D58)
    "hetre": {
        1: "Grand arbre au houppier ovoïde très dense, écorce lisse gris argenté, "
           "feuilles ovales luisantes bordées de cils, faînes en bogue hérissée.",
        2: "Pérenne caduc de grande taille, croissance lente et longévité séculaire ; "
           "anémophile (chatons). Son houppier fermé projette une ombre profonde : "
           "peu de choses poussent sous une hêtraie. Aime les sols frais et bien "
           "drainés ; marcescent, il garde souvent ses feuilles rousses tout l'hiver.",
        3: "Bâtisseur de la « hêtraie cathédrale » : son ombre dense trie la flore du "
           "sous-bois (sciaphiles strictes) et étouffe la concurrence. Ses faînes "
           "nourrissent la faune les années de fainée ; sa litière lente et son réseau "
           "ectomycorhizien tissent un humus forestier profond — climax de nos forêts.",
    },
    "bouleau": {
        1: "Arbre élancé à écorce blanche se détachant en lambeaux, houppier léger et "
           "retombant, petites feuilles triangulaires qui frémissent au moindre vent.",
        2: "Pérenne caduc PIONNIER à croissance rapide et vie brève (pour un arbre) ; "
           "anémophile. Ses graines ailées, produites en masse, colonisent au loin les "
           "sols nus et remués. Houppier clairsemé → ombre légère, sous-bois lumineux. "
           "Rustique, frugal, il s'installe là où rien d'autre ne tient encore.",
        3: "Éclaireur de la succession forestière : premier arbre à gagner une friche "
           "ou une trouée, il abrite et ombrage légèrement les essences climaciques "
           "(chêne, hêtre) qui le remplaceront. Son couvert clair, sa litière rapide à "
           "se décomposer et ses nombreux hôtes (insectes, champignons) amorcent le "
           "sol forestier. Arbre de lisière par excellence.",
    },
    "charme": {
        1: "Arbre moyen au tronc CANNELÉ, sinueux et « musclé », écorce grise lisse, "
           "feuilles ovales plissées et doublement dentées, fruits en grappes d'ailettes.",
        2: "Pérenne caduc du bocage, à bois très dur et dense ; anémophile. Houppier de "
           "densité moyenne, ombre modérée. Supporte remarquablement la taille répétée — "
           "d'où son emploi ancestral en haies et charmilles. Marcescent comme le hêtre. "
           "Croissance moyenne, longévité intermédiaire.",
        3: "Charpente vivante du bocage normand : conduit en haie ou en têtard, il "
           "structure le paysage, brise le vent et abrite une faune dense (oiseaux "
           "nicheurs, auxiliaires). Compagnon fréquent du chêne dans la chênaie-charmaie. "
           "Son bois dur fut le bois de feu et d'outil des campagnes.",
    },

    # === Guilde marécageuse (sprint HYDROLOGIE & MARÉCAGES ⑤) ===
    "aulne": {
        1: "Arbre de bord d'eau au tronc droit, écorce sombre crevassée, feuilles "
           "arrondies au bout comme échancré, petits « cônes » ligneux persistant "
           "l'hiver et chatons pendants.",
        2: "Pérenne caduc PIONNIER des berges et sols gorgés, anémophile (chatons). "
           "Il pousse LES PIEDS DANS L'EAU là où les autres arbres pourrissent : ses "
           "racines abritent des nodosités où vit la bactérie Frankia, qui FIXE "
           "l'azote de l'air — comme une légumineuse, mais un arbre. Il enrichit ainsi "
           "un sol pauvre et noyé.",
        3: "Bâtisseur des ripisylves : il stabilise les berges, ombrage l'eau, et sa "
           "fixation d'azote AMÉLIORE le sol autour de lui — un vrai pionnier "
           "améliorateur des terrains humides que rien ne colonise. Sa litière et son "
           "azote amorcent une zone humide vivante ; ses graines flottantes essaiment "
           "au fil de l'eau. Là où une cuvette se gorge, l'aulne prospère quand le "
           "fruitier de terrain sec dépérit — il RÉVÈLE l'eau qui stagne.",
    },
    # === L'arbre de la trogne (sprint PÉRIPHÉRIE ⑥) ===
    # N1 = la SILHOUETTE seule (philo #6 : le rejet de souche est une DÉCOUVERTE, pas
    # une consigne — il n'apparaît qu'au N2, quand le joueur a fait le cycle).
    "saule": {
        1: "Arbre de bord d'eau au houppier ample et retombant, longues feuilles "
           "étroites d'un vert argenté au revers, rameaux souples et flexibles ; "
           "au sortir de l'hiver, des chatons duveteux couvrent le bois encore nu.",
        2: "Pérenne caduc de ripisylve, à croissance TRÈS rapide et à vie brève pour un "
           "arbre. Il pousse les pieds dans l'eau, là où les racines des autres "
           "pourrissent. Ses chatons s'ouvrent AVANT les feuilles et donnent nectar et "
           "pollen quand presque rien d'autre n'est fleuri — les butineurs sortis "
           "d'hibernation y trouvent leur première table. Un rameau cassé, tombé dans "
           "la vase, refait des racines tout seul : il se bouture sans qu'on l'aide.",
        3: "Arbre-atelier du bocage : coupé au ras, il ne meurt pas — la souche rejette "
           "en une gerbe de tiges droites, bonnes à la vannerie et au chauffage, "
           "indéfiniment. Étêté haut et régulièrement, il devient une TROGNE : un fût "
           "trapu qui se creuse avec les années et abrite chouettes, chauves-souris et "
           "insectes du bois mort. Paradoxe qui fut le savoir des paysans : le saule "
           "qu'on prélève tous les dix ans vit bien plus vieux que celui qu'on laisse "
           "libre — la coupe le rajeunit là où sa tête, trop lourde, finirait par le "
           "fendre. Ses racines tiennent la berge, son ombre tempère l'eau.",
    },
    "sphaigne": {
        1: "Coussin ras et spongieux d'un vert glauque à roussâtre, gorgé d'eau, sans "
           "vraie tige ni racine — une mousse molle qui tapisse les creux détrempés.",
        2: "Mousse (bryophyte) INGÉNIEUR des tourbières : elle ne prend pas racine, "
           "elle POMPE l'eau par capillarité et en retient des dizaines de fois son "
           "poids. En échangeant ses ions, elle ACIDIFIE le sol sous elle ; sa "
           "nécromasse antiseptique ne se décompose presque pas et s'accumule.",
        3: "Elle FABRIQUE son propre milieu : en retenant l'eau, en acidifiant et en "
           "empilant une litière imputrescible, elle transforme lentement une flaque "
           "en TOURBIÈRE — un sol acide, gorgé, où seules les acidophiles (myrtille, "
           "carnivores) tiennent. La tourbe qu'elle bâtit, couche après couche sur des "
           "siècles, est une mémoire du sol et un puits de carbone. Là où elle "
           "s'installe, elle ferme la porte aux plantes de sol riche et l'ouvre à un "
           "tout autre cortège.",
    },
    "drosera": {
        1: "Minuscule rosette rouge plaquée au sol, aux feuilles rondes hérissées de "
           "poils luisants coiffés d'une gouttelette gluante ; au-dessus, une frêle "
           "hampe portant de petites fleurs blanches.",
        2: "Petite carnivore des tourbières acides : ses poils gluants CAPTURENT les "
           "insectes (moustiques, moucherons) qu'elle digère. C'est ainsi qu'elle se "
           "procure l'AZOTE que le sol tourbeux, très pauvre, ne lui offre pas — elle "
           "chasse au lieu de puiser. Acidophile stricte, elle vit les pieds dans la "
           "tourbe gorgée que la sphaigne a fabriquée.",
        3: "Végétal-prédateur : en prélevant la nuée de moustiques au-dessus d'elle, "
           "elle RARÉFIE la faune de mare autour de son tapis — un flux insectes→azote "
           "qui l'AFFRANCHIT de la faim d'azote. Elle prospère précisément là où toute "
           "herbacée ordinaire dépérirait, faute d'azote, sur la tourbe acide et "
           "maigre : sa niche est un manque que sa chasse comble. Là où le rossolis "
           "abonde, l'eau dort acide et pauvre depuis longtemps — il SIGNE la "
           "tourbière mûre.",
    },
}
