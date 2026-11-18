"""
SYMBIOSE — sim/concept_corpus.py
CORPUS de l'ENCYCLOPÉDIE, onglet CONCEPT — DONNÉE éditoriale pure (D60, ④).
Spec : `docs/faune/vie_macro/conception_vie_macro_identifiable.md` §5 + kickoff
`sprints/faune/vie_macro/sprint_vie_macro_identifiable/04_corpus_concept_technique.md`.

Miroir structurel de `sim/encyclopedie_corpus.py` (plantes) mais pour les CONCEPTS
transversaux — les grandes causes écologiques que la maîtrise crédite au fil des
événements (eau, lumière, météo, pollinisation). Ces clés NE sont PAS des espèces :
ce sont des idées que le jardinier finit par nommer. Elles ont donc leur corpus à
part, aligné SUR `sim/encyclopedie_types.CONCEPTS` (vérifié par le test).

`FICHES_CONCEPT[concept] = {1: "…N1…", 2: "…N2…", 3: "…N3…"}`
  - N1 (palier 1, découverte)     = ce qu'on OBSERVE : le phénomène visible.
  - N2 (palier 2, investissement) = le MÉCANISME : ce qui le produit, ses lois.
  - N3 (palier ≥ 3, maîtrise)     = le RÔLE ÉCOSYSTÉMIQUE : couplages, acteurs
                                     reliés, comment le milieu répond.

Voix « naturaliste qui observe » (3ᵉ personne, factuelle, descriptive — jamais
impérative, philo #6 ; aucun chiffre de gameplay, philo #5). Les interconnexions
sont TISSÉES dans le texte (eau↔stagnation/dessèchement, pollinisation↔butineurs↔
floraison↔fruits…). DONNÉE PURE : aucun import moteur, read-only, golden NEUTRE.
"""
from __future__ import annotations

# --- Les 4 concepts transversaux × 3 niveaux ---------------------------------
FICHES_CONCEPT: dict[str, dict[int, str]] = {

    "eau": {
        1: "L'eau va et vient dans le jardin : la terre fonce et luit après la "
           "pluie ou l'arrosage, puis s'éclaircit et se craquelle en séchant. Les "
           "plantes se dressent quand elle abonde, s'affaissent quand elle manque.",
        2: "L'eau du sol n'est pas un stock immobile. Elle s'infiltre, remonte par "
           "capillarité, s'évapore à la surface nue et repart par les feuilles "
           "(transpiration). Une terre couverte — paillis, feuillage — la retient ; "
           "une terre nue la perd. Chaque plante puise dans la réserve à portée de "
           "ses racines : les pivots plongent au frais du sous-sol, les racines "
           "traçantes dépendent de la pluie récente.",
        3: "L'eau est le premier chef d'orchestre du vivant. Ni trop, ni trop peu : "
           "un sol détrempé chasse l'air des racines et les asphyxie, un sol qui "
           "sèche trop longtemps installe un STRESS chronique qui finit par tuer. "
           "Entre les deux, une plante bien alimentée résiste mieux au froid, à la "
           "maladie, aux ravageurs. La rosée du matin, un paillis, un sol vivant et "
           "grumeleux qui fait éponge : autant de manières dont le milieu tempère "
           "lui-même la soif, sans intervention.",
    },

    "lumière": {
        1: "Certaines plantes poussent en plein soleil, dressées et trapues ; "
           "d'autres, à l'ombre d'un mur ou d'un grand voisin, s'étirent, pâlissent "
           "et penchent leur cime vers la clarté.",
        2: "La lumière est la nourriture première : par les feuilles, la plante la "
           "transforme en matière (photosynthèse). Là où elle manque, la tige "
           "s'allonge en cherchant le jour et son sommet se courbe vers le gradient "
           "le plus lumineux (phototropisme). L'ombre se projette et se déplace au "
           "fil des heures et des saisons — celle de la maison, celle des grands "
           "arbres, et l'ombre que chaque plante se fait à elle-même en s'épaississant.",
        3: "La lumière sculpte l'étagement du jardin : des strates hautes qui "
           "captent le plein soleil aux couvre-sols d'ombre, chacun sa place. Un "
           "voisin trop dense prive les autres de jour et déclenche chez eux "
           "l'étirement, puis, s'il dure, un stress d'ombre qui les épuise. À "
           "l'inverse, une ombre bienvenue protège du dessèchement les plantes "
           "fraîches. Lire la course de l'ombre, c'est composer qui va où.",
    },

    "météo": {
        1: "Le temps change et le jardin le sent : une pluie, un coup de chaud, une "
           "nuit froide, un grand vent. Des signes précèdent parfois : un halo "
           "autour de la lune, une brume au ras du sol, l'agitation des oiseaux, la "
           "terre qui craquelle.",
        2: "La météo est la somme des flux qui traversent le jardin — pluie, "
           "chaleur, froid, vent, humidité de l'air. Elle commande la température du "
           "sol (donc les levées), l'évaporation (donc la soif), les gelées (donc "
           "les dégâts). Ses signes ne sont pas magiques : la brume dit un air "
           "saturé, l'anneau lunaire une couche de nuages hauts, la fuite des "
           "oiseaux une chute de pression. Qui apprend à les lire anticipe.",
        3: "La météo est le grand aléa que le jardinier ne maîtrise pas mais peut "
           "amortir. Se préparer par le milieu — paillage profond avant le gel, "
           "brise-vent, voiles, structures persistantes — coûte moins que réagir "
           "dans l'urgence. Un écosystème mûr encaisse mieux : sol couvert, "
           "diversité, strates qui se protègent. Plus la compréhension du climat "
           "s'affine, plus les surprises se raréfient — jusqu'à ce que presque tout "
           "devienne lisible d'avance.",
    },

    "pollinisation": {
        1: "Aux beaux jours, des insectes vont de fleur en fleur : abeilles, "
           "bourdons, syrphes, papillons. Là où ils passent, les fleurs se fanent et "
           "des fruits se forment ; là où ils manquent, les fleurs tombent sans rien "
           "nouer.",
        2: "Beaucoup de plantes ne peuvent faire graine ou fruit sans transporter "
           "leur pollen d'une fleur à l'autre. Les butineurs s'en chargent en "
           "cherchant le nectar : ce faisant, ils fécondent. Certaines cultures — la "
           "courgette, monoïque, aux fleurs mâles et femelles séparées — en dépendent "
           "entièrement. Chaque fleur a ses visiteurs de prédilection, selon sa "
           "forme, sa couleur, son parfum.",
        3: "La pollinisation relie tout un cortège : des fleurs ÉTALÉES dans le temps "
           "tiennent une table de nectar soutenue qui nourrit les butineurs sans "
           "à-coup ; des butineurs nombreux et divers assurent en retour la "
           "fructification. Nectarifères (phacélie, bourrache, trèfle, lavande) et "
           "ombellifères accessibles (achillée, carotte en fleur) sont les piliers de "
           "ce réseau. Pas de fleurs, pas de butineurs ; pas de butineurs, pas de "
           "fruits ni de graines : la floraison du jardin est l'indicateur vivant de "
           "sa fertilité future.",
    },

    # Lignée (D139 ④) : pourquoi des graines récoltées donnent des frères identiques
    # (autogames) ou une descendance bigarrée (allogames). Ni chiffre ni F (philo #5) :
    # le mécanisme est dit en mots, le chiffre reste au survol de debug.
    "lignée": {
        1: "Des graines tirées d'une même plante ne donnent pas toujours la même "
           "chose. Ressemées, celles de la tomate ou du haricot lèvent en pieds "
           "presque identiques ; celles de la courgette ou du maïs donnent des "
           "frères qui ne se ressemblent guère.",
        2: "Chaque graine reçoit la moitié de son héritage de chacun de ses parents. "
           "Une fleur qui se féconde elle-même — la tomate, le haricot, le blé — "
           "n'a qu'un seul parent : génération après génération, ses descendants "
           "deviennent des copies les uns des autres, la lignée se fixe. Une fleur "
           "qui reçoit le pollen d'un autre pied — courges, ortie, la plupart des "
           "arbres — rebat les cartes à chaque génération : la lignée reste mêlée.",
        3: "Une lignée fixée est fiable : on sait ce qu'on sèmera. Mais elle a perdu "
           "sa réserve de différences, et si le climat ou le sol changent, rien en "
           "elle ne peut s'ajuster. Une lignée mêlée, au contraire, offre au milieu "
           "de quoi trier : chaque année le sol, le froid et les butineurs gardent "
           "un peu plus les pieds qui leur conviennent. Chez les plantes qui se "
           "croisent, trop de consanguinité affaiblit la descendance ; un pollen "
           "venu d'ailleurs lui rend sa vigueur. Garder ses graines, c'est choisir "
           "entre la constance et l'adaptation.",
    },
}
