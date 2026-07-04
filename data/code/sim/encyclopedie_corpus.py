"""
SYMBIOSE — sim/encyclopedie_corpus.py
CORPUS de l'ENCYCLOPÉDIE — DONNÉE éditoriale pure (sprint Voix narratives,
tronçon ④, dette « 4ᵉ voix »).
Spec de référence : `docs/conception/CONCEPTION_VOIX_NARRATIVES.md` §6.

Ce module ne contient QUE de la donnée (aucune logique, aucun import du moteur).
Il est séparé de `sim/encyclopedie.py` (la logique) pour respecter la règle « un
fichier = une responsabilité » : ici, c'est l'OUVRAGE ; là-bas, le LECTEUR. Le
corpus dépasse forcément le seuil ~350 ldc de code pur (32 fiches × 3 niveaux),
mais c'est de la DONNÉE recopiée FIDÈLEMENT du doc §6 — pas du code à relire vite
(dépassement signalé + justifié, cf. CLAUDE.md « garde-fou, pas dogme »).

`FICHES[espèce] = {1: "…N1…", 2: "…N2…", 3: "…N3…"}`
  - N1 (palier 1, découverte)     = ce qu'on VOIT : silhouette, organes.
  - N2 (palier 2, investissement) = la BIOLOGIE : cycle, besoins, strate, famille.
  - N3 (palier ≥ 3, maîtrise)     = le RÔLE ÉCOSYSTÉMIQUE : compagnonnage,
                                     succession, sol, faune.

Voix « naturaliste qui observe » (3ᵉ personne, descriptive et factuelle, ≠ le
« je » du carnet). Les CLÉS sont les clés du catalogue moteur (`plants.catalogue`)
— l'alignement est VÉRIFIÉ par `tests/test_encyclopedie.py`. Texte hors expertise
de Nico (botanique réelle) : à relire/corriger côté éditorial, jamais à réinventer
côté code.
"""
from __future__ import annotations

# --- Les 32 fiches × 3 niveaux (doc §6 + sprint Grimpantes ⑤ + Luxuriance ④) --
FICHES: dict[str, dict[int, str]] = {

    # === Annuelles & potagères cultivées ===
    "tomate": {
        1: "Plante herbacée dressée, feuilles découpées odorantes, fruits charnus rouges.",
        2: "Annuelle gélive, thermophile — ne démarre qu'au-dessus de ~12 °C, "
           "fructifie tout l'été. Sa graine ne lève que lorsque le sol est franchement "
           "chaud au toucher : semée tôt en terre froide, elle attend, parfois en vain. "
           "Gourmande en eau et en azote. Sensible au mildiou (familial Solanaceae).",
        3: "S'associe au basilic et aux Astéracées qui attirent ses auxiliaires ; à "
           "éloigner des autres Solanaceae (partage les mêmes maladies). Gros "
           "consommateur → épuise le sol, à faire suivre d'une légumineuse.",
    },
    "poivron": {
        1: "Buisson compact, feuilles lisses, fruits creux verts puis colorés.",
        2: "Annuelle très thermophile, encore plus frileuse que la tomate ; cycle long, "
           "a besoin d'une saison chaude pleine pour mûrir. Sa levée est la plus "
           "tardive du potager : il lui faut un sol durablement chaud, sinon la graine "
           "patiente sans germer. Même fragilité fongique familiale.",
        3: "Même clan que tomate/aubergine — rotation et distance de rigueur. Profite "
           "des fleurs compagnes qui soutiennent prédateurs de pucerons. Levant après "
           "les rustiques, elle s'inscrit dans la deuxième vague de la saison, quand la "
           "chaleur est bien installée.",
    },
    "haricot": {
        1: "Tige volubile ou naine, feuilles trifoliées, gousses pendantes.",
        2: "Annuelle fixatrice d'azote — ses racines hébergent des rhizobiums en "
           "nodules qui captent l'azote de l'air. Autofertile en azote, peu exigeante.",
        3: "Pilier des « trois sœurs » (maïs-tuteur, courge-couvre-sol) ; laisse le sol "
           "plus riche en azote qu'elle ne l'a trouvé. Grimpante, elle cherche un "
           "support (cf. tuteurs).",
    },
    "trefle": {
        1: "Tapis bas de feuilles à trois folioles, fleurs en pompons.",
        2: "Légumineuse fixatrice d'azote, vivace ou annuelle ; couvre-sol dense, "
           "fleurs très mellifères.",
        3: "Engrais vert et paillis vivant par excellence : enrichit en azote, protège "
           "le sol nu, nourrit abeilles et bourdons. Base d'une prairie fertile.",
    },
    "tournesol": {
        1: "Grande tige unique, large capitule jaune tourné vers le soleil.",
        2: "Annuelle héliotrope géante, croissance très rapide ; racine pivotante "
           "profonde. Graines riches recherchées des oiseaux.",
        3: "Brise-vent éphémère et perchoir ; capitule = garde-manger pollinisateurs "
           "puis oiseaux. Légèrement allélopathique — espace ses voisines sensibles.",
    },

    # === Aromatiques & compagnes ===
    "basilic": {
        1: "Petit buisson de feuilles tendres très parfumées.",
        2: "Annuelle gélive thermophile ; floraison en épis à supprimer pour prolonger "
           "le feuillage. Aime chaleur et arrosages réguliers. Sa levée réclame un sol "
           "chaud : il ne sert à rien de le semer tant que la terre reste fraîche.",
        3: "Compagnon classique de la tomate (brouille les ravageurs par son parfum, "
           "partage le même microclimat chaud) ; ses fleurs nourrissent les petits "
           "pollinisateurs.",
    },
    "achillee": {
        1: "Feuillage finement découpé en plumes, corymbes blancs plats.",
        2: "Vivace rustique, racine traçante, très résistante à la sécheresse ; "
           "floraison estivale longue.",
        3: "Aimant à auxiliaires (syrphes, coccinelles, micro-guêpes) grâce à ses "
           "ombelles accessibles ; accumulatrice dynamique, activatrice de compost. "
           "Médicinale.",
    },
    "phacelie": {
        1: "Tiges souples, feuilles crénelées, fleurs bleu-mauve enroulées en crosse.",
        2: "Annuelle à croissance ultra-rapide, non apparentée aux cultures courantes "
           "(idéale en rotation). Floraison mellifère exceptionnelle.",
        3: "Un des meilleurs engrais verts : couvre vite le sol nu, étouffe les "
           "adventices, nourrit massivement abeilles et syrphes, puis se fauche avant "
           "graine.",
    },
    "thym": {
        1: "Sous-arbrisseau rampant ligneux, minuscules feuilles aromatiques.",
        2: "Vivace méditerranéenne, xérophile, aime le sec, le drainant et le calcaire ; "
           "floraison estivale.",
        3: "Couvre-sol pérenne anti-érosion ; ses essences déroutent certains ravageurs "
           "et son tapis fleuri nourrit les pollinisateurs en pleine chaleur.",
    },
    "lavande": {
        1: "Touffe gris-vert ligneuse, épis floraux mauves dressés très parfumés.",
        2: "Vivace méditerranéenne, xérophile et calcicole ; déteste l'excès d'eau et "
           "l'ombre.",
        3: "Bordure mellifère majeure (abeilles, papillons) ; réputée éloigner mites et "
           "pucerons des voisines. Structure pérenne du jardin sec.",
    },
    "menthe": {
        1: "Touffe dressée de feuilles gaufrées très odorantes, petites fleurs en épis.",
        2: "Aromatique vivace qui disparaît en surface l'hiver et repart au printemps. "
           "Sous terre, elle file des RHIZOMES traçants au bout desquels lèvent des "
           "pousses-filles : elle gagne du terrain sans faire de graine, et tolère "
           "l'ombre — d'où sa réputation d'envahissante.",
        3: "Couvre-sol mellifère mais accapareur : ses rhizomes courent vite et loin, "
           "y compris sous une canopée où d'autres couvre-sols caleraient. À contenir "
           "(bordure enterrée, bac) sous peine de coloniser toute une planche. Ses "
           "fleurs nourrissent abeilles et syrphes ; son parfum déroute certains "
           "ravageurs au voisinage (répulsion familiale des Lamiacées).",
    },
    "bourrache": {
        1: "Plante velue rude, fleurs bleues en étoile retombantes.",
        2: "Annuelle vigoureuse qui se ressème seule ; accumulatrice de potassium ; "
           "fleurs et jeunes feuilles comestibles (goût de concombre).",
        3: "Aimant à abeilles parmi les plus puissants ; excellente compagne "
           "tomate/fraisier ; sa biomasse tendre fait un paillis riche. Pionnière "
           "auto-entretenue.",
    },
    "consoude": {
        1: "Grosse touffe de feuilles rêches, clochettes mauve-rosé.",
        2: "Vivace robuste à racine pivot profonde qui puise les minéraux du sous-sol ; "
           "repousse vite après coupe.",
        3: "Accumulatrice dynamique reine (potassium) → purin et paillis fertilisants ; "
           "barrière vivace ; fleurs très mellifères. Outil de fertilité du "
           "permaculteur.",
    },
    "moutarde": {
        1: "Tige dressée, feuilles lobées, grappes de fleurs jaunes vives.",
        2: "Annuelle à cycle éclair, piquante (glucosinolates) ; monte vite à fleur.",
        3: "Engrais vert biofumigant (assainit le sol en se décomposant) ; couvre-sol "
           "rapide et nectarifère. À ne pas enchaîner avec d'autres Brassicaceae "
           "(mêmes parasites).",
    },

    # === Potagères & sauvages ===
    "carotte": {
        1: "Rosette de feuilles plumeuses finement divisées, racine pivot orange.",
        2: "Bisannuelle cultivée en annuelle ; la 2ᵉ année monte en ombelle blanche. "
           "Aime un sol meuble et frais. Rustique, sa graine lève dès que le sol s'est "
           "un peu radouci, sans attendre les fortes chaleurs.",
        3: "En fleur, son ombelle nourrit syrphes et micro-guêpes ; associée à "
           "l'oignon/poireau qui déroutent mutuellement leurs mouches respectives.",
    },
    "courgette": {
        1: "Grosses feuilles larges sur tige étalée, grandes fleurs jaunes, fruits "
           "allongés.",
        2: "Annuelle thermophile, monoïque (fleurs mâles et femelles séparées) → dépend "
           "des pollinisateurs pour nouer. Très gourmande en eau et matière organique. "
           "Sa graine attend un sol bien réchauffé pour lever — semée trop tôt, elle "
           "pourrit plus qu'elle ne germe.",
        3: "Son feuillage couvre et ombre le sol (couvre-sol des « trois sœurs ») ; pas "
           "de butineurs = pas de courgettes — indicateur vivant de la santé "
           "pollinisatrice.",
    },
    "fraisier": {
        1: "Rosette basse de folioles dentées par trois, fleurs blanches à cœur jaune, "
           "puis fruits rouges parfumés.",
        2: "Couvre-sol vivace qui se multiplie par STOLONS : de longs coulants rampent "
           "au sol et s'enracinent au bout en une plante-fille identique à la mère. "
           "Mais le stolon n'ancre sa fille qu'à la lumière du sol — sous une canopée "
           "fermée, il ne prend pas. Fleurs mellifères, fruits appréciés de la faune.",
        3: "Tapis vivant qui protège le sol nu et se densifie de lui-même par ses "
           "coulants, tant que la lumière parvient au sol — un couvre-sol qui "
           "s'auto-limite là où l'ombre gagne. Ses fleurs nourrissent les butineurs, "
           "ses fraises attirent oiseaux et petits mammifères qui dispersent ses "
           "graines. Bonne compagne de la bourrache, qui appelle ses pollinisateurs.",
    },
    "mache": {
        1: "Petites rosettes tendres au ras du sol.",
        2: "Annuelle très rustique au froid, cycle d'hiver ; se ressème spontanément. "
           "Sa graine lève en sol seulement frais, bien avant les frileuses du potager.",
        3: "Couvre-sol hivernal qui occupe le terrain quand tout dort, limite le sol nu "
           "et le lessivage ; salade de soudure entre deux saisons. Levant au frais, "
           "elle fait partie des premières à ouvrir la saison, avant la grande vague de "
           "chaleur.",
    },
    "ortie": {
        1: "Tige carrée, feuilles dentées urticantes, fleurs verdâtres en grappes.",
        2: "Vivace traçante, indicatrice de sol riche en azote et en vie ; accumulatrice "
           "de fer et d'azote.",
        3: "Plante-hôte de nombreux papillons ; purin fertilisant et stimulant ; "
           "réservoir d'auxiliaires en lisière. Sa présence raconte la fertilité du "
           "lieu.",
    },
    "ail": {
        1: "Touffe de feuilles linéaires dressées, bulbe en gousses.",
        2: "Vivace cultivée en annuelle, riche en composés soufrés ; plantation "
           "d'automne, récolte d'été.",
        3: "Compagnon répulsif (pucerons, certains champignons) près des rosiers et "
           "fruitiers ; à éloigner des légumineuses. Assainit son voisinage.",
    },
    "myrtille": {
        1: "Petit arbrisseau buissonnant, feuilles ovales, baies bleu sombre pruineuses.",
        2: "Vivace acidophile stricte (n'aime que les sols acides, pH bas) ; symbiose "
           "avec des mycorhizes éricoïdes spécifiques.",
        3: "Indicatrice/exigeante de terre de bruyère ; ses baies nourrissent les "
           "oiseaux (dispersion). Hors de son pH, elle dépérit — révèle l'acidité du "
           "sol.",
    },

    # === Grimpantes (sprint Grimpantes ⑤) ===
    "lierre": {
        1: "Liane à feuilles luisantes palmées, tiges hérissées de crampons, baies "
           "noires en boules.",
        2: "Vivace ligneuse sempervirente, sciaphile — prospère à l'ombre où les "
           "autres calent. Ses crampons adhésifs lui font escalader murs et troncs "
           "sans qu'on l'y aide. Floraison très tardive, à l'automne. Sans appui, "
           "elle rampe au sol.",
        3: "Tapisse le sol nu et les parois au nord ; son feuillage d'hiver et son "
           "ombre dense abritent oiseaux et insectes. Sa floraison d'arrière-saison "
           "est l'une des dernières tables des abeilles ; ses baies nourrissent la "
           "faune quand tout est fané.",
    },
    "jasmin": {
        1: "Grimpante aux tiges souples arquées, feuilles composées, fleurs blanches "
           "étoilées très parfumées.",
        2: "Vivace sarmenteuse : ses tiges ne s'agrippent pas seules — il faut les "
           "palisser sur un support, sinon elles s'étalent sans monter. Floraison "
           "estivale abondante, embaumant surtout le soir. Semi-caduque, elle dort "
           "l'hiver.",
        3: "Sur un treillis ou une pergola, elle habille et parfume l'espace ; son "
           "nectar nourrit abeilles et papillons, en particulier au crépuscule. Se "
           "conduit par palissage — c'est la main du jardinier qui l'élève.",
    },

    # === Adventices pionnières & indicatrices ===
    "bourse_pasteur": {
        1: "Petite rosette, hampe fine à fruits triangulaires en cœur.",
        2: "Annuelle pionnière à cycle ultra-court, plusieurs générations par an ; "
           "comestible.",
        3: "Indicatrice de sol remué/cultivé ; couvre fugace le sol nu. Tête de pont de "
           "la succession après une perturbation. Rustique, elle lève dès le sol à "
           "peine radouci — souvent la première levée de l'année, bien avant les "
           "cultures frileuses.",
    },
    "minette": {
        1: "Petit trèfle rampant à fleurs jaunes en têtes serrées.",
        2: "Légumineuse annuelle fixatrice d'azote, frugale ; indicatrice de sol pauvre "
           "et sec.",
        3: "Colonise et réamorce les sols maigres en y fixant de l'azote ; fourrage et "
           "nectar discrets. Premier maillon vers une prairie plus riche.",
    },
    "paturin": {
        1: "Petite graminée touffue, épillets verts clairs.",
        2: "Graminée annuelle ultra-pionnière, germe et grenaille en continu ; colonise "
           "tout sol nu. Fenêtre de levée très large : dès que le sol n'est plus gelé, "
           "elle lève, du frais du printemps jusqu'à l'automne.",
        3: "Premier tapis qui fixe la surface après mise à nu ; transition vers un gazon "
           "pérenne. Omniprésent, indicateur de sol travaillé/piétiné.",
    },
    "pissenlit": {
        1: "Rosette de feuilles dentées, capitule jaune unique, aigrette ronde.",
        2: "Vivace à racine pivot profonde, accumulatrice dynamique ; floraison très "
           "précoce.",
        3: "Sa racine décompacte le sol et remonte les minéraux ; une des premières "
           "ressources de nectar pour les abeilles au sortir de l'hiver. Indicatrice de "
           "sol tassé.",
    },

    # === Arbres pérennes ===
    "figuier": {
        1: "Petit arbre à grandes feuilles lobées, écorce grise lisse, figues "
           "vertes/violettes.",
        2: "Pérenne caduc méditerranéen, résistant à la sécheresse une fois établi ; "
           "aime la chaleur réverbérée d'un mur. Méridional, il ne lève spontanément de "
           "graine que sur sol bien chaud — contrairement aux ligneux tempérés qui "
           "germent au frais du printemps.",
        3: "Idéal en espalier sud (microclimat chaud, albédo du mur) ; figues = manne "
           "pour oiseaux et insectes en fin d'été. Ombre dense estivale.",
    },
    "pommier": {
        1: "Arbre à houppier arrondi, floraison blanche-rosée au printemps, pommes.",
        2: "Pérenne caduc nécessitant du froid hivernal (vernalisation) et une "
           "pollinisation croisée (deux variétés). Longévité de plusieurs décennies.",
        3: "Cœur du verger : fleurs = ressource pollinisatrice majeure du printemps ; "
           "sensible au carpocapse (guetter les auxiliaires/mésanges). Porte tout un "
           "cortège d'espèces.",
    },
    "cerisier": {
        1: "Arbre élancé, écorce annelée brillante, floraison blanche abondante, "
           "cerises.",
        2: "Pérenne caduc à floraison très précoce, sensible aux gelées tardives ; "
           "croissance rapide.",
        3: "Sa floraison hâtive est une des premières grandes tables des "
           "pollinisateurs ; cerises = aimant à oiseaux (dispersion des noyaux).",
    },
    "noyer": {
        1: "Grand arbre à large couronne, feuilles composées aromatiques, noix en brou.",
        2: "Pérenne caduc de grande taille, croissance lente, longévité séculaire ; "
           "émet de la juglone.",
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
}


# --- Concepts TRANSVERSAUX × 3 niveaux (sprint météo→champs ⑤, §6) ------------
# La rosée / la gelée blanche ne sont pas des ESPÈCES : ce sont des PHÉNOMÈNES
# climatiques. Elles ont leur entrée d'encyclopédie dans un dictionnaire SÉPARÉ
# de `FICHES` (qui reste strictement les 28 espèces, alignées au catalogue et
# verrouillées par `test_encyclopedie`). Même structure 3 niveaux, même voix
# « naturaliste qui observe ». DONNÉE PURE : aucun import moteur, read-only, golden
# NEUTRE. Clés = un identifiant de concept (≠ clé de catalogue, pas de collision).
#   N1 = ce qu'on VOIT ; N2 = le MÉCANISME physique ; N3 = le RÔLE écosystémique.
CONCEPTS: dict[str, dict[int, str]] = {
    "rosee": {
        1: "Au petit matin, des gouttes d'eau perlent sur les feuilles et les toiles "
           "d'araignées, scintillant au premier soleil.",
        2: "Condensation de la vapeur de l'air sur les surfaces refroidies pendant une "
           "nuit claire : le sol et le feuillage, en rayonnant leur chaleur vers un ciel "
           "dégagé, descendent sous le point de rosée et l'humidité de l'air s'y dépose "
           "en eau liquide. Maximale sur sol nu, frais et découvert.",
        3: "Micro-cycle de l'eau du jardinier sec : la rosée freine la spirale de "
           "dessèchement d'un sol vivant, hydrate le feuillage qui l'intercepte et "
           "abreuve la petite faune du matin (limaces, détritivores). Un paillis isole "
           "le sol et réduit la rosée — mais il retenait déjà son eau : pas de double "
           "peine. Lire la rosée, c'est lire le terrain.",
    },
    "gelee_blanche": {
        1: "Un matin d'hiver, une fine pellicule de cristaux blancs givre l'herbe et le "
           "sol nu, là où la nuit a été la plus claire.",
        2: "Même phénomène que la rosée, mais sous 0 °C : la vapeur se dépose "
           "directement en givre au lieu d'eau liquide. Le sol découvert, qui rayonne "
           "le plus, gèle quand un coin paillé ou couvert reste au-dessus de zéro.",
        3: "L'eau gelée du matin n'est pas perdue : le givre fond au réchauffement et "
           "restitue son eau au sol (fonte différée). C'est le visage hivernal de la "
           "rosée — un dépôt nocturne d'eau, simplement passé par la phase solide.",
    },
    # Germination thermique (sprint germination thermique ⑦) : la levée n'est pas
    # déclenchée par le calendrier mais par la CHALEUR DU SOL. PHÉNOMÈNE écologique
    # transversal (≠ espèce) → entrée dans `CONCEPTS`, même structure 3 niveaux,
    # même voix naturaliste. C'est la voix qui rend lisible la succession TEMPORELLE
    # émergente (pionnières au frais → frileuses à la chaleur) et la sélection
    # darwinienne (lignées qui lèvent un peu plus tôt chaque année). Aucun chiffre en
    # HUD primaire (philo #5) : la fenêtre est décrite au toucher, pas mesurée.
    "germination_thermique": {
        1: "Au sortir de l'hiver, rien ne lève encore. Puis, le sol se réchauffant, "
           "les premières pousses percent — d'abord les sauvages, plus tard les "
           "cultures frileuses, chacune à son heure.",
        2: "Une graine ne germe pas à une date : elle attend que la terre atteigne sa "
           "chaleur de réveil. Sous un plancher de froid, aucune ne bouge, quelle que "
           "soit l'espèce. Chaque plante a sa fenêtre : les rustiques (mâche, carotte, "
           "adventices) lèvent dès que le sol est seulement frais ; les thermophiles "
           "(tomate, poivron, courgette, basilic, figuier) exigent un sol franchement "
           "chaud au toucher et tardent d'autant.",
        3: "De ces fenêtres décalées naît la VAGUE DE PRINTEMPS, sans aucun calendrier : "
           "les pionnières ouvrent la saison sur sol encore frais, occupent l'espace, "
           "puis les frileuses prennent le relais quand la chaleur s'installe — une "
           "succession qui s'organise toute seule au fil du réchauffement. Et le sol "
           "garde mémoire : génération après génération, les lignées qui lèvent un peu "
           "plus tôt prennent l'avantage et essaiment ; insensiblement, le jardin "
           "apprend à démarrer plus vite.",
    },
    # Succession (sprint bugs d'émergence, S3) : le sol nu ne reste jamais nu. La
    # bascule pionnier → prairie est une TRAJECTOIRE dans le temps, pas un état ; sa
    # voix rend lisible pourquoi une friche de bourse-à-pasteur finit par céder la
    # place aux légumineuses et graminées. N3 dévoile le moteur caché : la FACILITATION
    # (les pionnières bâtissent l'humus qui amorce les tardives dans la banque-sol).
    "succession": {
        1: "Sur une terre remuée et nue, une même herbe menue lève partout et couvre "
           "vite le sol. Les saisons passant, d'autres plantes plus denses, plus hautes, "
           "s'installent parmi elles, puis les débordent.",
        2: "Un sol dénudé se recolonise par vagues successives. Les PIONNIÈRES (bourse-"
           "à-pasteur, pâturin, minette) germent d'abord : à cycle éclair, tolérant le "
           "sol pauvre et remué, elles verdissent la surface en une saison. Mais leur "
           "règne est provisoire — elles préparent le terrain sans l'occuper durablement.",
        3: "Chaque vague FACILITE la suivante : en poussant, en mourant, les pionnières "
           "laissent litière et racines qui bâtissent l'humus. C'est cet humus, et non "
           "le calendrier, qui réveille dans la banque-sol les graines des tardives — "
           "légumineuses fixatrices d'azote, graminées, puis les plus exigeantes. Quand "
           "le sol est assez riche, elles lèvent, dépassent les pionnières et les "
           "brident. La friche bascule alors en prairie. Un sol nu qui reste nu, ou une "
           "seule espèce qui verrouille tout, signale une succession bloquée : il manque "
           "le pont d'humus qui ouvre la porte aux suivantes.",
    },
    # Phénologie florale (sprint bugs d'émergence, S2) : pourquoi les fleurs d'une même
    # espèce ne s'ouvrent pas toutes la même semaine. La voix qui rend lisible l'ÉTALEMENT
    # des dates de floraison et sa cause génétique (variabilité de lignée, sélection). N3
    # relie l'étalement à la ressource pollinisatrice (nectar soutenu vs pic unique).
    "phenologie_florale": {
        1: "Dans un même massif d'une même plante, les fleurs ne s'ouvrent pas toutes "
           "ensemble : quelques-unes en avance, la plupart au cœur de la vague, quelques "
           "traînardes après. La floraison s'étale sur plusieurs semaines.",
        2: "Une fleur n'ouvre pas à une date, mais quand la plante a cumulé assez de "
           "chaleur ET que les jours sont assez longs. Or, au sein d'une espèce, chaque "
           "lignée porte un seuil de chaleur florale un peu différent, hérité de ses "
           "parents : certaines fleurissent tôt, d'autres tard. De cette variabilité "
           "naît l'étalement — jamais un créneau unique.",
        3: "Cet étalement n'est pas un défaut : c'est la santé du jardin. Un pic "
           "synchrone unique gorge les pollinisateurs un instant puis les affame ; une "
           "floraison ÉTALÉE tient une table de nectar soutenue sur des semaines, "
           "nourrissant abeilles et syrphes sans à-coup — d'où plus de brassage, plus de "
           "graines. Et le sol trie : les lignées dont la date de floraison colle le "
           "mieux à la saison et aux butineurs essaiment davantage. Génération après "
           "génération, la phénologie du massif s'ajuste toute seule au climat du lieu.",
    },
}
