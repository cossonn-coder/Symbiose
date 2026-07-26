"""
SYMBIOSE — sim/encyclopedie_corpus/potager.py
Fiches du POTAGER : annuelles & potagères cultivées, aromatiques &
compagnes, potagères et sauvages comestibles (doc §6).
DONNÉE éditoriale pure — aucune logique, aucun import moteur. Éclaté de
l'ex-monolithe `sim/encyclopedie_corpus.py` (402 LDC, zone rouge) au refactor de
clôture du sprint PÉRIPHÉRIE ; `__init__.py` réassemble `FICHES` dans le MÊME
ordre, l'API publique lue par les appelants est inchangée.

Voix « naturaliste qui observe » (3ᵉ personne, descriptive et factuelle), 3 niveaux
par entrée — cf. le docstring du paquet pour le contrat complet.
"""
from __future__ import annotations

FICHES_POTAGER: dict[str, dict[int, str]] = {
    # === Annuelles & potagères cultivées ===
    "tomate": {
        1: "Plante herbacée dressée, feuilles découpées odorantes, fruits charnus rouges.",
        2: "Annuelle gélive, thermophile — ne démarre qu'au-dessus de ~12 °C, "
           "fructifie tout l'été. Sa graine ne lève que lorsque le sol est franchement "
           "chaud au toucher : semée tôt en terre froide, elle attend, parfois en vain. "
           "Gourmande en eau et en azote. Sensible au mildiou (familial Solanaceae).",
        3: "S'associe au basilic et aux Astéracées qui attirent ses auxiliaires ; à "
           "éloigner des autres Solanaceae (partage les mêmes maladies). Gros "
           "consommateur → épuise le sol, à faire suivre d'une légumineuse. TRÈS "
           "sensible à la juglone : dépérit sous un noyer ou à son voisinage — le cas "
           "d'école du poison racinaire.",
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
           "puis oiseaux. Allélopathique modéré — ses racines chargent le sol de "
           "composés qui espacent les voisines sensibles (à ne pas serrer contre un "
           "semis délicat) ; en monoculture répétée, il finit par fatiguer son propre sol.",
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
}
