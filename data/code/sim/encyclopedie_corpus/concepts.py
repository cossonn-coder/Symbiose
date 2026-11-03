"""
SYMBIOSE — sim/encyclopedie_corpus/concepts.py
Fiches des PHÉNOMÈNES climatiques et écologiques transversaux (≠ espèces).
DONNÉE éditoriale pure — aucune logique, aucun import moteur. Éclaté de
l'ex-monolithe `sim/encyclopedie_corpus.py` (402 LDC, zone rouge) au refactor de
clôture du sprint PÉRIPHÉRIE ; `__init__.py` réassemble `FICHES` dans le MÊME
ordre, l'API publique lue par les appelants est inchangée.

Voix « naturaliste qui observe » (3ᵉ personne, descriptive et factuelle), 3 niveaux
par entrée — cf. le docstring du paquet pour le contrat complet.
"""
from __future__ import annotations

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
           "le pont d'humus qui ouvre la porte aux suivantes. Et la prairie ne s'arrête "
           "pas là : le trèfle enrichit le sol en azote, les grandes graminées y lèvent "
           "et l'ombrent, il recule, le sol s'appauvrit, il revient.",
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
