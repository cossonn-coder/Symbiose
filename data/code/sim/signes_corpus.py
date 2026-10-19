"""
SYMBIOSE — sim/signes_corpus.py
CORPUS de la LÉGENDE DES SIGNES (sprint PLANTE ASSEMBLÉE ⑥, décision 4).
Spec : `docs/rendu/pixelart/conception_plante_assemblee.md` §3 (décision 4) + §4.4.

DONNÉE ÉDITORIALE PURE (aucun import, aucun état) : ce que le joueur VOIT d'un
signe ou d'une bête AVANT de l'avoir appris, et ce qu'il en comprend APRÈS. Lu par
`sim/signes.py` (observation, « appris »), `sim/carnet.py` (gabarits de la note) et
`sim/encyclopedie.py` (fiche « signe »). Jamais lu par le tick → golden NEUTRE.

Pour chacun des 11 signes de `sim/semiologie.py` (8 détecteurs chroniques +
3 marques événementielles maladie/gel/grele) :
  - `vu`      : ce qu'on VOIT, sans la cause (info-bulle descriptive, philo #5).
                Doit coller à ce que DESSINE la vue (`PlantRenderer.cs` teintes de
                symptôme ; `PlantRenderer.PaliersHauts.cs` marques ×16 : bord
                brun-noir = gel, bord beige-brun = sécheresse, petits trous sombres =
                ravageurs ou grêle, taches brun foncé = maladie) ;
  - `concept` : le concept de maîtrise EXISTANT qui « gate » l'apprentissage — le
                même que le carnet emploie déjà pour la cause (`carnet.CONCEPT_DE`) :
                on n'invente aucun concept (chlorose → `sol`, concept des pages ;
                acclimatation → `adaptation`, D43) ;
  - `carnet`  : gabarits D (descriptif) / I (interprétatif), voix « je » ; slots du
                carnet {e} espèce, {l} lieu, {s} semaine ;
  - `fiche`   : 3 niveaux de l'encyclopédie, voix naturaliste — 1 le signe décrit,
                2 sa cause biologique, 3 ce que le jardin peut y faire par le MILIEU
                (philo #1 : jamais un remède appliqué à la plante).
`FAUNE_VU` : description visible de chaque espèce de la vie macro (`FAUNE_ENCYCLO`),
sans son nom (« visible dès le début, non identifiable sans maîtrise »).
"""
from __future__ import annotations

_D = "descriptif"
_I = "interprétatif"

SIGNES: dict[str, dict] = {
    "chlorose": {
        "vu": "feuilles jaunies entre les nervures restées vertes",
        "concept": "sol",
        "carnet": {
            _D: "J'ai vu des feuilles jaunies entre les nervures restées vertes sur {e} {l}, semaine {s}.",
            _I: "{e} {l} jaunit entre ses nervures : ce sol trop calcaire bloque son fer, ce n'est pas la faim, c'est la serrure.",
        },
        "fiche": {
            1: "Le limbe pâlit puis jaunit entre les nervures, qui gardent leur vert : un réseau vert sur fond jaune.",
            2: "Chlorose ferrique : dans un sol au pH trop élevé, le fer devient insoluble ; la plante en manque pour fabriquer sa chlorophylle, d'abord sur les jeunes feuilles. Les acidophiles y sont les plus sensibles.",
            3: "On n'acidifie pas une plante : on fait évoluer le sol. Litière d'aiguilles, compost mûr et matière organique abaissent lentement le pH ; ailleurs, on laisse la place aux espèces qui aiment la chaux.",
        },
    },
    "secheresse": {
        "vu": "feuilles ternes et molles, au bord sec, beige-brun",
        "concept": "eau",
        "carnet": {
            _D: "J'ai vu des feuilles ternes et molles, au bord sec et beige-brun, sur {e} {l}, semaine {s}.",
            _I: "{e} {l} a soif : le bord de ses feuilles sèche en premier, ce sol ne garde pas l'eau assez longtemps.",
        },
        "fiche": {
            1: "Le feuillage se ternit et se ramollit ; le bord du limbe brunit en un liseré beige, sec au toucher.",
            2: "Stress hydrique : quand l'eau du sol manque, la plante ferme ses stomates et laisse mourir d'abord les marges, les plus éloignées de la sève. Prolongé, le stress use la plante jusqu'à la mort.",
            3: "Un sol couvert garde son eau : paillage, couvre-sol vivant, humus qui retient comme une éponge, ombre légère d'un voisin. L'arrosage d'urgence sauve une plante, le milieu sauve la saison.",
        },
    },
    "asphyxie": {
        "vu": "feuillage d'un vert brunâtre, terne, sans éclat",
        "concept": "eau",
        "carnet": {
            _D: "J'ai vu un feuillage d'un vert brunâtre, terne, sur {e} {l}, semaine {s} — pourtant l'eau ne manque pas.",
            _I: "{e} {l} étouffe par le pied : trop d'eau qui stagne, ses racines manquent d'air.",
        },
        "fiche": {
            1: "Le feuillage perd son éclat et tire vers un vert brunâtre, sans flétrir de soif.",
            2: "Asphyxie racinaire : dans un sol gorgé d'eau, l'air chassé des pores n'arrive plus aux racines ; elles cessent de respirer, puis pourrissent.",
            3: "On rend l'air au sol : ne plus arroser, drainer ou creuser une mare qui recueille l'excès, ameublir sans retourner, installer des espèces de sol frais qui boivent beaucoup.",
        },
    },
    "ravageurs": {
        "vu": "feuilles criblées de petits trous sombres",
        "concept": "ravageurs",
        "carnet": {
            _D: "J'ai vu des feuilles criblées de petits trous sombres sur {e} {l}, semaine {s}.",
            _I: "On mange {e} {l} : ce sont des morsures, et s'il en reste tant, c'est que ceux qui mangent les mangeurs manquent ici.",
        },
        "fiche": {
            1: "Le limbe est percé de petits trous sombres, plus nombreux à mesure que l'attaque dure.",
            2: "Herbivorie : pucerons, limaces, doryphores et chenilles prélèvent le tissu foliaire. La plante perd de la surface qui capte la lumière, et sa vigueur avec.",
            3: "Le jardin se défend par ses habitants : fleurs nectarifères pour les auxiliaires, tas de bois et coins non remués pour carabes et hérissons, voisins répulsifs. Un équilibre, pas une éradication.",
        },
    },
    "rongeur_racinaire": {
        "vu": "plante qui se fane par le pied, d'un jaune-brun sale",
        "concept": "ravageurs",
        "carnet": {
            _D: "J'ai vu {e} {l} se faner par le pied, d'un jaune-brun sale, semaine {s} — et pas une feuille mordue.",
            _I: "{e} {l} est rongée au collet : sous terre, on lui a coupé la sève — un campagnol chasse là où personne ne le chasse.",
        },
        "fiche": {
            1: "La plante jaunit et se fane depuis le pied, d'une teinte jaune-brun sale, alors que son feuillage n'est pas mordu.",
            2: "Herbivorie racinaire : un rongeur des galeries écorce le collet et coupe les racines. La sève ne monte plus ; la cause reste cachée sous terre.",
            3: "On rappelle les chasseurs : perchoirs pour les rapaces, abris de pierres et de bois pour couleuvres et hérissons. La régulation vient d'en haut de la chaîne.",
        },
    },
    "ombre": {
        "vu": "feuillage pâle et délavé, tiges qui s'étirent",
        "concept": "lumière",
        "carnet": {
            _D: "J'ai vu un feuillage pâle et délavé, des tiges qui s'étirent, sur {e} {l}, semaine {s}.",
            _I: "{e} {l} s'étiole : l'ombre lui vole la lumière, elle s'allonge pour la chercher et s'épuise.",
        },
        "fiche": {
            1: "Les feuilles pâlissent en un vert délavé ; les tiges s'allongent, grêles.",
            2: "Étiolement : à l'ombre, la plante produit moins de chlorophylle et investit dans l'élongation pour atteindre la lumière. Trop longtemps privée, elle dépérit.",
            3: "On rend la lumière par le milieu : éclaircir ce qui fait écran, étêter un rideau au lieu de l'abattre, réserver l'ombre aux espèces qui l'aiment.",
        },
    },
    "senescence": {
        "vu": "feuillage qui vire au jaune-rouge",
        "concept": "sénescence",
        "carnet": {
            _D: "J'ai vu le feuillage de {e} {l} virer au jaune-rouge, semaine {s}.",
            _I: "{e} {l} arrive au bout de son cycle : ce n'est pas un mal, c'est l'âge ; sa matière retournera au sol.",
        },
        "fiche": {
            1: "Le feuillage passe du vert au jaune puis au rouge, sans morsure ni tache.",
            2: "Sénescence : la plante âgée démonte sa chlorophylle et rapatrie ses nutriments avant de s'éteindre. C'est un programme, pas une maladie.",
            3: "Rien à combattre : laisser la plante finir sur place nourrit le sol et la litière. Les graines tombées et la succession prennent la relève.",
        },
    },
    "acclimatation": {
        "vu": "feuilles couvertes d'un voile cireux bleu-gris",
        "concept": "adaptation",
        "carnet": {
            _D: "J'ai vu un voile cireux bleu-gris sur les feuilles de {e} {l}, semaine {s}.",
            _I: "{e} {l} s'est endurcie : ce voile de cire, c'est sa réponse au stress — et ses graines naîtront pré-armées.",
        },
        "fiche": {
            1: "Le limbe se couvre d'un voile cireux qui le teinte de bleu-gris, plus coriace au toucher.",
            2: "Acclimatation : sous un stress répété, la plante exprime ses gènes de défense — cuticule épaissie, cire, tissus plus durs. Elle pousse moins vite, mais tient mieux.",
            3: "Un signe de résilience, pas de souffrance : un milieu modérément exigeant forge des lignées robustes. Garder ses propres graines garde cette mémoire.",
        },
    },
    "maladie": {
        "vu": "feuilles piquées de taches brun foncé",
        "concept": "maladie",
        "carnet": {
            _D: "J'ai vu des taches brun foncé sur les feuilles de {e} {l}, semaine {s}.",
            _I: "{e} {l} est malade : ces taches, c'est un champignon qui court de feuille en feuille, et la terre d'ici en garde la mémoire.",
        },
        "fiche": {
            1: "Le limbe se pique de petites taches brun foncé, qui s'étendent sur un fond terni.",
            2: "Maladie cryptogamique : un champignon parasite colonise les tissus, favorisé par l'humidité et la répétition d'une même famille au même endroit. Son inoculum reste dans le sol.",
            3: "On prive la maladie de son terrain : faire tourner les familles, aérer les plantations, laisser reposer une terre lasse, diversifier les voisins.",
        },
    },
    "gel": {
        "vu": "liseré brun-noir au bord des feuilles",
        "concept": "météo",
        "carnet": {
            _D: "J'ai vu un liseré brun-noir au bord des feuilles de {e} {l}, semaine {s}.",
            _I: "Le gel a mordu {e} {l} : les cellules du bord ont éclaté sous la glace, il faudra la protéger ou choisir plus rustique.",
        },
        "fiche": {
            1: "Le bord des feuilles noircit en un liseré brun-noir, net, après une nuit froide.",
            2: "Dégât de gel : l'eau des tissus gèle, les cristaux crèvent les cellules ; les marges, plus exposées, meurent les premières. Au-delà de sa rusticité, la plante y passe.",
            3: "On tempère le froid par le milieu : voile ou cloche avant la nuit annoncée, paillage profond, abri d'un mur ou d'une haie. Lire les signes du ciel donne le temps de préparer.",
        },
    },
    "grele": {
        "vu": "feuilles criblées de petits trous sombres et d'encoches",
        "concept": "météo",
        "carnet": {
            _D: "J'ai vu des feuilles criblées de petits trous et d'encoches sur {e} {l}, semaine {s} — d'un coup.",
            _I: "La grêle est passée sur {e} {l} : ces trous sont tombés du ciel, pas d'une bête — le même jour, partout à découvert.",
        },
        "fiche": {
            1: "Le limbe est criblé de petits trous sombres et entaillé d'encoches, apparus d'un seul coup.",
            2: "Dégât de grêle : les grêlons déchirent mécaniquement les feuilles. À la différence d'une morsure, tout le couvert exposé est touché à la fois, l'abrité non.",
            3: "On abrite plutôt qu'on ne soigne : filet ou cloche à l'approche d'un ciel de plomb, couvert d'arbres, lisière qui casse l'averse.",
        },
    },
}

# Description VISIBLE de chaque bête de la vie macro (clés de `FAUNE_ENCYCLO`), sans
# son nom : ce que voit le naturaliste débutant. Le nom vient avec l'apprentissage.
FAUNE_VU: dict[str, str] = {
    "puceron":    "minuscules insectes verts agglutinés sous les jeunes pousses",
    "limace":     "mollusque gris et luisant, sans coquille",
    "doryphore":  "coléoptère bombé, jaune rayé de noir",
    "coccinelle": "petit coléoptère rouge à points noirs",
    "chrysope":   "insecte frêle aux ailes vertes translucides",
    "carabe":     "grand coléoptère noir à reflets métalliques, qui court au ras du sol",
    "merle":      "oiseau noir au bec jaune qui fouille la litière",
    "herisson":   "petit mammifère couvert de piquants, de sortie au crépuscule",
    "lombric":    "long ver rose qui affleure la terre humide",
    "cloporte":   "petite bête grise en armure, sous le bois mort",
    "campagnol":  "petit rongeur brun aux oreilles courtes, qui file entre deux trous",
    "rapace":     "oiseau de proie qui tourne en cercles au-dessus du jardin",
    "couleuvre":  "serpent long et lisse qui glisse vers l'eau",
    "moustique":  "nuée de petits insectes piqueurs au-dessus de l'eau dormante",
    "libellule":  "insecte aux longues ailes de verre qui patrouille au-dessus de l'eau",
    "abeille":    "insecte doré rayé de brun, qui va de fleur en fleur",
    "syrphe":     "petite mouche rayée jaune et noir, immobile en plein vol",
    "papillon":   "insecte aux grandes ailes colorées, au vol hésitant",
    "bourdon":    "gros insecte velu et ronflant, rayé de jaune",
    "osmie":      "petite abeille rousse et solitaire, qui niche dans les tiges creuses",
}
