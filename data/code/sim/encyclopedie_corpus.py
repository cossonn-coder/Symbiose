"""
SYMBIOSE — sim/encyclopedie_corpus.py
CORPUS de l'ENCYCLOPÉDIE — DONNÉE éditoriale pure (sprint Voix narratives,
tronçon ④, dette « 4ᵉ voix »).
Spec de référence : `docs/conception/CONCEPTION_VOIX_NARRATIVES.md` §6.

Ce module ne contient QUE de la donnée (aucune logique, aucun import du moteur).
Il est séparé de `sim/encyclopedie.py` (la logique) pour respecter la règle « un
fichier = une responsabilité » : ici, c'est l'OUVRAGE ; là-bas, le LECTEUR. Le
corpus dépasse forcément le seuil ~350 ldc de code pur (28 fiches × 3 niveaux),
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

# --- Les 28 fiches × 3 niveaux (doc §6, VERBATIM) ----------------------------
FICHES: dict[str, dict[int, str]] = {

    # === Annuelles & potagères cultivées ===
    "tomate": {
        1: "Plante herbacée dressée, feuilles découpées odorantes, fruits charnus rouges.",
        2: "Annuelle gélive, thermophile — ne démarre qu'au-dessus de ~12 °C, "
           "fructifie tout l'été. Gourmande en eau et en azote. Sensible au mildiou "
           "(familial Solanaceae).",
        3: "S'associe au basilic et aux Astéracées qui attirent ses auxiliaires ; à "
           "éloigner des autres Solanaceae (partage les mêmes maladies). Gros "
           "consommateur → épuise le sol, à faire suivre d'une légumineuse.",
    },
    "poivron": {
        1: "Buisson compact, feuilles lisses, fruits creux verts puis colorés.",
        2: "Annuelle très thermophile, encore plus frileuse que la tomate ; cycle long, "
           "a besoin d'une saison chaude pleine pour mûrir. Même fragilité fongique "
           "familiale.",
        3: "Même clan que tomate/aubergine — rotation et distance de rigueur. Profite "
           "des fleurs compagnes qui soutiennent prédateurs de pucerons.",
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
           "le feuillage. Aime chaleur et arrosages réguliers.",
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
           "Aime un sol meuble et frais.",
        3: "En fleur, son ombelle nourrit syrphes et micro-guêpes ; associée à "
           "l'oignon/poireau qui déroutent mutuellement leurs mouches respectives.",
    },
    "courgette": {
        1: "Grosses feuilles larges sur tige étalée, grandes fleurs jaunes, fruits "
           "allongés.",
        2: "Annuelle thermophile, monoïque (fleurs mâles et femelles séparées) → dépend "
           "des pollinisateurs pour nouer. Très gourmande en eau et matière organique.",
        3: "Son feuillage couvre et ombre le sol (couvre-sol des « trois sœurs ») ; pas "
           "de butineurs = pas de courgettes — indicateur vivant de la santé "
           "pollinisatrice.",
    },
    "mache": {
        1: "Petites rosettes tendres au ras du sol.",
        2: "Annuelle très rustique au froid, cycle d'hiver ; se ressème spontanément.",
        3: "Couvre-sol hivernal qui occupe le terrain quand tout dort, limite le sol nu "
           "et le lessivage ; salade de soudure entre deux saisons.",
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

    # === Adventices pionnières & indicatrices ===
    "bourse_pasteur": {
        1: "Petite rosette, hampe fine à fruits triangulaires en cœur.",
        2: "Annuelle pionnière à cycle ultra-court, plusieurs générations par an ; "
           "comestible.",
        3: "Indicatrice de sol remué/cultivé ; couvre fugace le sol nu. Tête de pont de "
           "la succession après une perturbation.",
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
           "tout sol nu.",
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
           "aime la chaleur réverbérée d'un mur.",
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
