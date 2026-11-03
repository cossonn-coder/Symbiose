"""
SYMBIOSE — sim/encyclopedie_corpus/adventices.py
Fiches des ADVENTICES pionnières & indicatrices — les plantes que le jardinier
ne sème pas et qui lui parlent de son sol.
DONNÉE éditoriale pure — aucune logique, aucun import moteur. Éclaté de
l'ex-monolithe `sim/encyclopedie_corpus.py` (402 LDC, zone rouge) au refactor de
clôture du sprint PÉRIPHÉRIE ; `__init__.py` réassemble `FICHES` dans le MÊME
ordre, l'API publique lue par les appelants est inchangée.

Voix « naturaliste qui observe » (3ᵉ personne, descriptive et factuelle), 3 niveaux
par entrée — cf. le docstring du paquet pour le contrat complet.
"""
from __future__ import annotations

FICHES_ADVENTICES: dict[str, dict[int, str]] = {
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
    "dactyle": {
        1: "Haute graminée en touffe serrée, épis en petits paquets denses au bout des "
           "tiges.",
        2: "Vivace nitrophile : elle lève sur les terres riches, souvent là où des "
           "légumineuses ont fixé de l'azote. Sa touffe dense et ses racines fibreuses "
           "prennent la lumière et l'eau à son pied.",
        3: "Elle fait tourner la prairie. L'azote laissé par le trèfle la nourrit, son "
           "ombre arrête les stolons qui avançaient, et le trèfle se retire là où il l'a "
           "fait venir. Quand elle a vidé le sol, le trèfle revient. Bon fourrage, "
           "grande productrice de litière.",
    },
    "fetuque": {
        1: "Gazon fin aux feuilles filiformes, épillets teintés de rouge.",
        2: "Vivace sobre des sols moyens et pauvres ; elle talle sous le pied et supporte "
           "la fauche. Elle lève mal là où la terre est grasse, laissée aux grandes "
           "graminées.",
        3: "Elle tient les terres maigres sans les épuiser : peu d'ombre, peu de soif, et "
           "le trèfle cohabite à son pied. Sa présence dit un sol encore modeste en azote.",
    },
    "plantain": {
        1: "Rosette plaquée de feuilles étroites à nervures saillantes, épi brun et court "
           "au bout d'une tige nue.",
        2: "Vivace à souche courte, indifférente à la richesse du sol ; pollinisée par le "
           "vent. Elle encaisse le piétinement et la fauche.",
        3: "Compagne des chemins et des prairies usées : ses feuilles restent sous la lame "
           "et sous le pas, et elle garde sa place quand les grandes herbes reculent. "
           "Ancienne plante de soin des plaies et des piqûres.",
    },
    "molene": {
        1: "Grande rosette de feuilles épaisses couvertes d'un duvet blanc laineux ; "
           "l'an suivant, une haute hampe dressée constellée de fleurs jaunes.",
        2: "Bisannuelle pionnière (rosette l'an 1, hampe florale et graines l'an 2, puis "
           "elle meurt) ; frugale, elle s'installe sur les sols nus, remués ou fatigués. "
           "Feuilles pectorales autrefois récoltées.",
        3: "Indicatrice de terre viciée : elle colonise les plots que des maladies "
           "passées ont chargés, là où les cultures peinent — sa venue signale un sol à "
           "laisser reposer ou à tourner. Peu sujette aux pathogènes du sol, elle tient "
           "où d'autres tombent ; sa hampe nourrit fort les butineurs.",
    },
}
