"""
SYMBIOSE — sim/voix_etres_corpus.py
Corpus des VOIX DES ÊTRES sous vision (sprint « le sol qui respire » ⑥, D111 §4).
Donnée pure : gabarits à la 1ʳᵉ personne, choisis par hash déterministe dans
`sim/voix_etres.py`. Distinct de `signes_corpus` (lui décrit ce qu'on VOIT, de
l'extérieur ; ici l'être dit ce dont il a BESOIN, de l'intérieur).

📖 Pédagogie — le gabarit ne décide RIEN : chaque thème n'est prononcé que si le
moteur mesure ce besoin (mémoires de sécheresse/ombre/asphyxie, Liebig N/P/K, pH,
allélopathie, racines voisines, rongeurs, vent ; ressource/abri/prédation des bêtes).
Les noms de plantes s'insèrent SANS article (genre inconnu) : en tête de phrase
ou après un point-virgule. Les champs `{…}` sont remplis par les vraies valeurs (le voisin qui fait de l'ombre,
le nutriment qui manque, la famille de fleurs préférée…). Voix écrites à la main par
espèce = dette lointaine (finition, cf. DETTE.md D113).
"""
from __future__ import annotations

# --- Plantes : thème → variantes (au moins 2, le hash choisit) ---------------
PLANTE: dict[str, tuple[str, ...]] = {
    "soif": ("J'ai soif. Mes racines cherchent l'eau et ne trouvent que de la poussière.",
             "La terre s'est refermée sur moi, sèche. Je ferme mes feuilles pour tenir."),
    "noyade": ("Mes racines étouffent : l'eau ne s'en va plus, l'air manque en bas.",
               "Trop d'eau. Je pourris par les pieds, lentement."),
    "ombre": ("{voisin} me prend la lumière. Je m'étire vers le peu qui reste.",
              "Je vis à l'ombre ; {voisin} me la porte. Mes feuilles pâlissent."),
    "ombre_anonyme": ("Quelque chose me cache le soleil. Je file, je m'épuise.",
                      "La lumière ne m'arrive qu'en miettes. J'en voudrais plus."),
    "faim": ("Il me manque {nutriment}. Le reste du sol ne sert à rien sans lui.",
             "Je cherche {nutriment} sous moi, il n'y en a presque plus."),
    "ph": ("Ce sol est trop {sens} pour moi ; ce que j'y bois me nourrit mal.",
           "Je n'aime pas ce sol {sens}. Mes racines s'y refusent."),
    "allelopathie": ("Le sol a un goût amer ici : quelqu'un y laisse des poisons qui me freinent.",
                     "Ce que les racines voisines ont rejeté me ralentit."),
    "concurrence": ("Trop de racines autour des miennes. {voisin} boit ce que je voudrais boire.",
                    "On se bat sous terre, et {voisin} y a le dessus."),
    "campagnol": ("Quelque chose ronge mes racines la nuit. Je tiens mal debout.",
                  "On me mange par en dessous. J'ai peur pour mon collet."),
    "parasite": ("Une pourriture monte dans mes racines. Je l'ai laissée entrer quand j'étais faible.",
                 "Un champignon me dévore de l'intérieur, par les racines."),
    "ravageurs": ("On mange mes feuilles. Si seulement quelqu'un mangeait ceux qui me mangent.",
                  "Mes feuilles sont criblées. J'attends mes alliés."),
    "vent": ("Le vent me secoue sans répit, ici, à découvert.",
             "Rien ne m'abrite du vent. Je dépense tout à rester droite."),
    "bien": ("Je suis bien ici. L'eau, la lumière, le sol : tout me va.",
             "Ne change rien. Je pousse."),
}

# --- Bêtes ---------------------------------------------------------------------
BETE: dict[str, tuple[str, ...]] = {
    "faim_fleurs": ("Je cherche des fleurs de {famille}. Il n'y en a pas assez ici.",
                    "Peu de nectar par ici ; ce que j'aime, ce sont les {famille}."),
    "faim_proies": ("J'ai faim. {proie} se fait rare dans ce coin.",
                    "Je chasse {proie}, et je n'en trouve presque pas."),
    "faim": ("Il n'y a pas assez à manger pour moi, ici.",
             "Je tourne en rond : rien à me mettre sous la dent."),
    "abri": ("Je ne trouve pas où me cacher. Le sol est trop nu, trop remué.",
             "Il me faudrait un abri : un tas de bois, des herbes hautes, un coin tranquille."),
    "predation": ("{predateur} rôde. Je ne reste pas longtemps à découvert.",
                  "J'ai senti {predateur}. Il faut que je me terre."),
    "sec": ("Tout est sec. Je m'enfonce sous la litière pour garder ma peau humide.",
            "Je me dessèche ici. Il me faut de l'ombre et de l'humidité."),
    "bien": ("Il y a de quoi vivre ici. Je reste.",
             "Ce coin de jardin me convient."),
}

# --- Champignons (rôle local du réseau, codes de `sim/champignon_role`) ----------
CHAMPIGNON: dict[str, tuple[str, ...]] = {
    "b": ("Je défais ce bois mort, fibre à fibre. Rendez-moi encore du bois.",
          "Je mange ce qui est tombé, et je le rends au sol."),
    "r": ("Je tiens les racines entre elles. Ce qui passe par moi nourrit tout le monde.",
          "Je parle aux racines ; elles me paient en sucre."),
    "h": ("Je colle les grains de terre ensemble. Ne me retournez pas.",
          "Je vis dans l'humus ; chaque coup de bêche me déchire."),
}

# Noms d'affichage des éléments nutritifs (thème `faim`).
NUTRIMENTS = {"n": "l'azote", "p": "le phosphore", "k": "le potassium"}

# Familles botaniques en français (thème `faim_fleurs`) ; repli = nom latin.
FAMILLES_FR = {
    "Lamiaceae": "labiées", "Boraginaceae": "bourraches", "Fabaceae": "légumineuses",
    "Rosaceae": "rosacées", "Asteraceae": "composées", "Apiaceae": "ombellifères",
    "Brassicaceae": "crucifères", "Cucurbitaceae": "cucurbitacées",
    "Solanaceae": "solanacées", "Oleaceae": "jasmins", "Araliaceae": "lierres",
}

# Noms d'affichage des bêtes (proie / prédateur cités), en MINUSCULE : ils s'insèrent
# aussi en milieu de phrase ; `voix_etres._majuscule` capitalise la tête de phrase.
NOMS_BETES = {
    "puceron": "le puceron", "limace": "la limace", "doryphore": "le doryphore",
    "lombric": "le ver de terre", "cloporte": "le cloporte", "campagnol": "le campagnol",
    "coccinelle": "la coccinelle", "chrysope": "la chrysope", "carabe": "le carabe",
    "merle": "le merle", "herisson": "le hérisson", "rapace": "le rapace",
    "couleuvre": "la couleuvre", "moustique": "le moustique", "libellule": "la libellule",
    "abeille": "l'abeille", "syrphe": "le syrphe", "papillon": "le papillon",
    "bourdon": "le bourdon", "osmie": "l'osmie",
}

# Bêtes dont la vie dépend de l'humidité du sol (peau perméable, larve aquatique).
BETES_HYGROPHILES = ("limace", "cloporte", "lombric", "moustique")
