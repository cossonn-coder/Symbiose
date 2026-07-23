# SYMBIOSE — tools/jardinier_auto (paquet)
# Le JARDINIER AUTOMATE : un agent DÉTERMINISTE qui joue le jardin à la place du
# testeur pendant les phases de test accélérées (2,5 J/s). Ce n'est PAS une IA
# (ni apprentissage, ni RNG — philo #3) et PAS une fonctionnalité de jeu (ni PNJ,
# ni tutoriel — philo #6) : c'est un INSTRUMENT DE DÉVELOPPEMENT, du même statut
# que l'overlay debug F6. Conception : docs/joueur/automate/conception_jardinier_automate.md.
#
# Invariant central (H2) : l'automate s'intercale ENTRE deux ticks, côté appelant,
# jamais dans `tick_semaine`. Le moteur ne change pas d'une ligne → golden INTACT.
#
# Découpage (un fichier = une responsabilité) :
#   - profil       : ProfilAutomate (dataclass gelée) + presets LIBRE/BRIDE
#   - perception   : « que sais-je de cette plante ? » (omniscient câblé)
#   - diagnostic   : facteur limitant dominant (loi de Liebig)
#   - regles       : table facteur→geste priorisée
#   - execution    : traduction geste → appel sim.actions
#   - trace        : journal déterministe structuré (game_state["automate_journal"])
#   - filtre       : vues LECTURE SEULE du journal (filtrer/trier/rendre, D87 ①)
#   - objectifs    : objectifs (geste, quantité, cible) + biais/comptage (④)
#   - onglet       : projection scopée du journal + log sur un objectif (④)
#   - boucle       : JardinierAutomate.jouer_tick (5 étapes)
#
# L'API publique est ré-exportée ici → `from tools.jardinier_auto import
# JardinierAutomate, LIBRE`.

from .profil import ProfilAutomate, LIBRE, BRIDE
from .boucle import JardinierAutomate
from .tutelle import marquer_jardin_cultive
from .objectifs import Objectif, ajouter_objectif, objectifs_actifs
from .onglet import onglet
from .rapport import rapport_impasses
from .filtre import filtrer, trier, rendre

__all__ = ["ProfilAutomate", "LIBRE", "BRIDE", "JardinierAutomate",
           "marquer_jardin_cultive", "Objectif", "ajouter_objectif",
           "objectifs_actifs", "onglet", "rapport_impasses",
           "filtrer", "trier", "rendre"]
