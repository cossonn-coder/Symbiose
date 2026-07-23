# BRIEF — Amorce de conception : « Automate dirigé par le but » (D87)

> Brief autosuffisant destiné à **rédiger l'amorce de conception sur Claude web**
> (aucun accès au repo). L'amorce produite sera ensuite durcie et figée via
> `/conception` sur le dépôt. Écrit le 2026-07-23.

## Le projet en deux phrases
SYMBIOSE est une **sandbox écologique déterministe** (permaculture, « jardin
éternel » à un seul run persistant). Le moteur de simulation est en **Python**
(source de vérité) ; Godot 4 / C# n'est qu'une **vue**. La simulation avance par
**ticks de semaine** ; 52 semaines = une saison.

## Philosophie de design — garde-fous NON négociables
1. Le joueur agit **principalement sur le MILIEU**, pas directement sur les êtres
   vivants. L'action directe existe mais coûte cher en « Vigueur » et perturbe.
2. Jamais de bonus/malus direct sur les plantes — toujours flux → contrainte
   écologique → réponse biologique **émergente**.
3. **Simulation strictement déterministe** (seed global, hash de bruit spatial).
   **Aucune IA, aucun RNG** dans la logique de décision.
6. Pas de tutoriel imposé — l'apprentissage est diffus (action → conséquence →
   consultation → hypothèse). Un système d'objectifs ne doit pas se muer en
   tutoriel dirigiste.

## Ce qui existe déjà : le « jardinier automate » (fait, D78)
Un **agent déterministe** joue le jardin « de son mieux », **au-dessus du moteur,
entre deux ticks** (jamais dans le tick → la simulation de référence reste
intacte par construction). Il sert de **pilote de test** (un humain ne peut pas
soigner 50–600 plantes à la vitesse de test).

Son cerveau actuel = **loi du minimum de Liebig, purement RÉACTIVE**, une passe
par tick, cinq étapes :
1. **Percevoir** l'état des plantes sous tutelle (les cultivées).
2. **Diagnostiquer** le *facteur limitant* dominant de chaque plante.
3. **Proposer** le geste le moins cher qui relâche ce facteur (table de règles
   ordonnées `facteur limitant → geste`).
4. **Prioriser** (biais par les objectifs actifs) et couper au budget de Vigueur.
5. **Exécuter** via les mêmes fonctions de geste que le joueur, puis tracer.

Gestes disponibles (aucun n'est nouveau) : planter, arroser, pailler (consomme un
stock de mulch → exige de broyer du bois / récolter de la paille avant),
récolter, déraciner une adventice, tailler un voisin ombrageant, grelinette
(aérer le sol), favoriser les auxiliaires, manger, écraser, bêcher.

**Objectifs** — germe de quêtes déjà en place mais MINIMAL :
- Structure : `Objectif(geste, quantité, cible)`, ex. `("recolter", 10, "tomate")`.
- Effet actuel : **biaise seulement la priorisation** vers la cible + **compte la
  progression**. RIEN d'autre.
- **Limite dure** : si la cible n'est même pas plantée, l'automate ne fait rien
  pour elle (au mieux il signale « objectif inatteignable »). Il ne sait pas
  *fabriquer* les conditions du but.

## Le problème à concevoir (D87)
Rendre l'automate **dirigé par le but** : qu'il **comprenne la chaîne d'étapes**
menant à un objectif et la **planifie à rebours** (raisonnement moyens-fins),
tout en restant **déterministe, sans IA ni RNG**.

Exemple : objectif « récolter des tomates », alors qu'aucune tomate n'est plantée.
L'automate devrait dérouler :
planter un semis de tomate (si graine en banque) → l'amener à l'âge adulte →
favoriser les auxiliaires (pollinisation + réduction des ravageurs) → arroser →
pailler → récolter à maturité.

Le planificateur pose des **sous-buts** ; le cœur réactif de Liebig existant les
**sert** tick par tick. Gestion des prérequis manquants : pas de graine →
sous-but « obtenir la graine » (banque de graines / magazine de botanique) →
sinon **impasse** explicite (pas de triche).

## Axes de conception à explorer dans l'amorce (questions ouvertes)
- **Représentation de la chaîne de prérequis** : table déclarative « recette » par
  type d'objectif ? ou graphe de besoins émergent dérivé du modèle biologique ?
  Compromis lisibilité / généralité / risque de dupliquer la connaissance déjà
  encodée dans le moteur.
- **Articulation planificateur ↔ cœur Liebig réactif** : le planificateur
  pose-t-il des sous-buts que la boucle réactive consomme ? Qui arbitre quand un
  sous-but de planification entre en conflit avec un facteur limitant urgent
  d'une autre plante ?
- **Prérequis manquants & impasses** : arbre de résolution (graine absente →
  magazine → sinon impasse), et comment tracer une impasse « honnête ».
- **Déterminisme** : ordre de résolution des sous-buts stable, aucune heuristique
  dépendante d'un hasard.
- **Respect de la philo** : le planificateur agit toujours *via le milieu*
  (garde-fou #1) ; il ne doit pas devenir un script dirigiste qui court-circuite
  l'émergence (#2) ni un tutoriel (#6).

## Dépendances / limites connues
- D87 suppose que les **dépendances biologiques dures** fonctionnent pour l'espèce
  visée : floraison/pollinisation correctes et **survie de l'espèce** (la tomate,
  par ex., meurt tôt dans certains scénarios — froid de démarrage + maladie
  familiale). Un planificateur parfait échoue si la biologie ne suit pas ; le
  concevoir en le supposant résolu, mais l'expliciter.
- Couplé au **futur système de quêtes** (une quête = un objectif + sa chaîne de
  prérequis). Le brief ici ne traite QUE le moteur de planification, pas
  l'habillage narratif des quêtes.

## Contraintes d'implémentation (à garder en tête)
- Le planificateur vit **au-dessus du moteur** (comme l'automate), jamais dans le
  tick → il ne doit pas altérer la simulation de référence.
- **Déterministe** : mêmes entrées → même plan, à l'ordre des gestes près.
- N'introduire **aucun geste nouveau** si possible ; réutiliser les gestes
  existants.

## Livrable attendu de Claude web
Une **amorce de conception** : le cadrage du problème, 2–3 architectures
candidates pour la représentation de la chaîne de prérequis (avec leurs
compromis), les points durs à trancher formulés en questions, et une esquisse de
découpage. Pas de code. Cette amorce sera ensuite **durcie et figée** dans une
session `/conception` sur le repo (challenge des hypothèses, chiffrage perf,
découpage en tronçons préservant la simulation de référence).
