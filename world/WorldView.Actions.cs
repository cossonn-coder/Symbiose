// SYMBIOSE — WorldView.Actions.cs (partial de WorldView, SS⑥ refactor global)
// Les ACTIONS JOUEUR (tranche 4, volet B + taille au segment, tranche 5) :
// touches 1..8 = geste, clic gauche = exécuter. La vue RÉSOUT la désignation
// (plante par position / plot / tuile) et la TRANSMET ; Python valide,
// applique, répond ACK/NAK + snapshot. Aucune pré-validation côté C#. Inclut
// le picking (collet / branche sous la souris) et la surbrillance de taille.

using Godot;
using System.Collections.Generic;
using System.Threading.Tasks;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// --- Actions joueur (tranche 4, volet B ; +3 gestes vue·rattrapage 01) -
		// Les gestes, dans l'ORDRE de la table COUTS de sim/actions.py
		// (kickoff B·10). Kind = famille de cible : p = plante (par position),
		// q = plot (tile,r,c), t = tuile, m = point de MILIEU sur une tuile
		// (x_cm/y_cm LOCAUX — planter/arroser, protocole 0.3.3), '-' = sans cible.
		// Au-delà de 9 entrées les touches 1..9 ne couvrent plus tout : la
		// sélection cyclique Tab (cf. Controls) parcourt TOUTE la palette — c'est
		// par elle qu'on atteint les 6 gestes compost (03). Kinds compost :
		// q = poser une structure au plot (planification) ; s = agir sur la
		// structure EXISTANTE du plot cliqué (composter/empiler/retourner/épandre).
		private static readonly (string Verb, string Nom, char Kind)[] Gestes =
		{
			("recolter",             "récolter",       'p'),
			("deraciner",            "déraciner",      'p'),
			("ecraser",              "écraser",        'x'),   // plante OU nuisible
			("favoriser_auxiliaire", "favoriser aux.", 't'),
			("becher",               "ameublir",       'a'),   // bêcher / Maj grelinette
			// Gestes structurels sur plante (acquisition des moyens d'agir ①④), tous
			// désignés par POSITION comme tailler (kind 'p'). `pincer`/`arracher` sont
			// de BASE (mains nues, gradient doux→net, GESTES_BASE) → toujours ouverts.
			// `couper`/`tailler` restent GATÉS par la chaîne sécateur (GESTE_UNLOCK) :
			// la palette les grise tant que `posseder_secateur`→`couper` n'est pas
			// acquis (④). Un clic simple envoie la cible par défaut (apex) côté serveur.
			("pincer",               "pincer",         'p'),   // DOUX (main, débourrement)
			("arracher",             "arracher",       'p'),   // NET déchiré (main, érode)
			("couper",               "couper",         'p'),   // NET propre (sécateur), gaté
			("tailler",              "tailler",        'p'),
			("manger",               "manger",         'p'),
			("planter",              "planter",        'm'),
			("arroser",              "arroser",        'm'),
			// Terrassement hydrologique (hydrologie ⑦, gestes sur le MILIEU, philo #1,
			// coûteux Vigueur). Kind 'q' = plot {tile, r, c} SANS params (comme
			// poser_bac/glaner) : le serveur route les verbes au plot cliqué et répond
			// un message diagnostic (avant/après) qu'on relaie tel quel (ACK générique).
			//  · creuser = abaisse `altitude` d'un cran → cuvette qui capte l'eau ② ;
			//  · drainer = vide `eau_surface` + fait reculer `marais_memory` (assèche).
			// `creuser` a DEUX cibles pour UN verbe (périphérie ⑤/⑦) : un plot du
			// jardin (cuvette) si le clic tombe sur une tuile, un SECTEUR de
			// périphérie (mare de bordure) s'il tombe dans le décor. Le kind reste
			// 'q' : c'est le dispatch qui route sur la position du clic, comme le
			// serveur route sur la forme du target — pas de `creuser_mare` en double.
			("creuser",              "creuser",        'q'),
			("drainer",              "drainer",        'q'),
			// GESTES DE PAYSAGE (périphérie D73 ④⑤, protocole 0.5.41). Kind 'L' =
			// un SECTEUR de la ceinture, désigné en cliquant le décor HORS du jardin
			// (granularité D-1 : un geste vaut pour un bord entier). Tous gatés par
			// `GESTE_UNLOCK` côté moteur — la palette les grise tant que la hache /
			// la serpe / la pioche ne sont pas à l'Atelier, ou que l'expérience
			// requise manque (étêter s'apprend après avoir recépé).
			//  · abattre = la trouée franche (30 ans de structure perdue) ;
			//  · receper = le taillis (10 ans… sauf hêtre/bouleau, où c'est abattre) ;
			//  · eteter  = la trogne (5 ans, densité conservée) ;
			//  · endiguer/deriver = déplacer la ligne d'eau d'un bord (un OUVRAGE :
			//    il rompt sans entretien) ; entailler = retirer de la roche, le seul
			//    geste du jeu dont on ne revient JAMAIS.
			("abattre",              "abattre",        'L'),
			("receper",              "recéper",        'L'),
			("eteter",               "étêter",         'L'),
			("endiguer",             "endiguer",       'L'),
			("deriver",              "dériver",        'L'),
			("entailler",            "entailler",      'L'),
			("poser_bac",            "poser bac",      'q'),   // compost ⑤ (planification)
			("poser_pile",           "poser pile",     'q'),
			("composter",            "composter",      's'),   // litière tendre → bac
			("empiler_bois",         "empiler bois",   's'),   // bois → pile
			("retourner",            "retourner",      's'),   // accélère la maturation
			// Épandre = geste à 2 temps (mycélium ⑥, §3.2) : 1er clic sur le BAC
			// (source) → 2e clic sur le PLOT cible. Kind 'E' (≠ 's', qui clique
			// la structure et épand sur son propre plot). Patron `deplacer_pot`.
			("epandre",              "épandre",        'E'),   // compost mûr → sol (2 clics)
			// Conteneurs (pots/bacs ⑥b, protocole 0.5.7). Kind P = POSER un
			// conteneur au point MONDE du clic (le serveur lit target.x_cm/y_cm
			// comme position monde absolue, cf. conteneurs_route.py) ; le substrat
			// vient du cycle B, volume/grille de knobs. Kind C = désigner un
			// conteneur EXISTANT par index (déplacer = 2 temps ; planter = graine S).
			("poser_pot",          "poser pot",      'P'),
			("poser_bac_culture",  "poser bac",      'P'),
			("deplacer_pot",       "déplacer pot",   'C'),
			("planter_conteneur",  "planter (pot)",  'C'),
			// Paillage (équilibre invasion ⑧, protocole 0.5.20). Kind U = pailler un
			// PLOT {tile, r, c} avec la NATURE courante (cycle touche N) — dépose du
			// mulch, consomme le stock de cette nature (le serveur refuse si vide).
			// Kind D = broyer un SQUELETTE par POSITION (comme un geste plante) : son
			// bois → BRF au stock. Approvisionner (broyer / récolter) précède pailler.
			("pailler",            "pailler",        'U'),   // mulch au plot (nature N)
			("broyer",             "broyer bois",    'D'),   // squelette → BRF
			// Glaner (acquisition des moyens d'agir ③, canal 1) : ramasse la litière
			// tendre du PLOT cliqué → stock nature `feuilles`. Kind 'q' = plot {tile, r,
			// c} SANS params (comme poser_bac), exactement ce qu'attend le verbe `glaner`
			// côté serveur. Geste de BASE (GESTES_BASE) → toujours ouvert dans la palette,
			// amorce le mulch sans outil ni culture (lève l'impasse RAVITAILLEMENT).
			("glaner",             "glaner",         'q'),   // litière tendre → mulch feuilles
			// Gestes savants de la palette (tronçons ②③) — 2 TEMPS côté vue, le
			// serveur reste STATELESS (patron `epandre`/`deplacer_pot`) :
			//  · Kind 'b' BOUTURER : 1er clic = la MÈRE (position continue), 2e clic
			//    = le PLOT cible {r,c} de la MÊME tuile → params.r/c (cf. actions.py).
			//  · Kind 'g' GREFFER : 1er clic = le GREFFON (position continue) mémorisé
			//    en params.scion_x_cm/y_cm, 2e clic = le PORTE-GREFFE (cible primaire
			//    target.x_cm/y_cm), MÊME tuile. La façade Python fait foi (gates).
			("bouturer",           "bouturer",       'b'),   // mère → plot (2 clics)
			("greffer",            "greffer",        'g'),   // greffon → porte-greffe (2 clics)
			// Perchoir à oiseaux (zoochorie ④⑧, protocole 0.6.11) : un POINT de milieu
			// {tile, x_cm, y_cm} LOCAL, exactement la cible de `planter`/`arroser` → kind
			// 'm', sans params. Agir sur le milieu (philo #1) : le merle s'y pose et sème
			// dessous. Gaté côté moteur (après `poser_tuteur` ou maîtrise `perchoir`).
			("poser_perchoir",     "perchoir",       'm'),
			// Les NEUF gestes que la vue ignorait (accès aux gestes ④, protocole
			// 0.6.12). Aucun kind neuf : chacun réemploie la désignation qu'attend sa
			// route au pont (`supports_route.py`, `structures_route.py`).
			//  · supports = un POINT de la tuile, comme le perchoir → 'm' ;
			//  · palisser = une PLANTE par position (un sarmenteux, à nouer au support
			//    le plus proche — le moteur le cherche) → 'p' ;
			//  · couvertures et ruche = un PLOT {tile, r, c} → 'q' ;
			//  · récolter le miel = la STRUCTURE du plot cliqué → 's' (la branche
			//    « retourner » du dispatch : on clique la ruche elle-même).
			("poser_tuteur",       "tuteur",         'm'),
			("poser_treillis",     "treillis",       'm'),
			("poser_pergola",      "pergola",        'm'),
			("palisser",           "palisser",       'p'),
			("poser_voile",        "voile",          'q'),
			("poser_cloche",       "cloche",         'q'),
			("poser_ombriere",     "ombrière",       'q'),
			("poser_ruche",        "poser ruche",    'q'),
			("recolter_miel",      "récolter miel",  's'),
		};
		// Nature de mulch courante pour `pailler` (touche N). Cycle sur les 4 natures
		// du moteur (NATURES_MULCH) — le stock de la nature choisie doit être alimenté
		// (glaner → feuilles ; broyer → brf ; récolter blé/chanvre ou Atelier → paille ;
		// sapin → aiguilles). Les FEUILLES viennent en tête : c'est le seul mulch qu'un
		// débutant possède (accès aux gestes ④ — elles manquaient ici, et le paillis
		// glané restait inutilisable).
		private static readonly string[] Natures = { "feuilles", "paille", "brf", "aiguilles" };
		private int _natureIndex;
		private int _gesteIndex = -1;              // aucun geste sélectionné
		// Graines plantables du snapshot (player.seeds, lots non vides), triées
		// par nom affiché pour un ordre de cycle STABLE ; l'espèce courante (S cycle) sert
		// de params.species à `planter`. Le serveur reste juge (catalogue + banque).
		private readonly List<(string Key, int Count)> _seeds = new();
		private int _seedIndex;

		// --- Conteneurs (pots/bacs ⑥b) -------------------------------------
		// Substrat choisi à la POSE (cycle touche B), modèle exact = CycleSeed.
		// Les 5 substrats POSABLES PAR LE PONT (registre world/substrat.py) :
		// `terre_jardin` est EXCLU car le pont le refuse (il faut pointer un plot
		// source de tuile, non désignable en ④ — cf. conteneurs_route.py). On NE
		// re-substrate PAS un conteneur existant (décision sprint) : le choix ne
		// sert qu'à poser_pot / poser_bac_culture.
		private static readonly string[] Substrats =
			{ "terreau", "compost", "drainant_mineral", "lasagnes", "mycelium_use" };
		private int _substratIndex;
		// Knobs de pose (placeholders, calibrage F5). Volume pot = VOLUME_REF du
		// moteur (75 L → confinement neutre). Bac 2×2 fond ouvert, volume large
		// (peu/pas de nain, couplé à la tuile dessous).
		private const float PotVolumeL = 75f;
		private const float BacVolumeL = 200f;
		private const int BacRows = 2, BacCols = 2;
		private const bool BacFondOuvert = true;
		// Geste DÉPLACER à 2 temps (décision Nico : outil + clic, pas de drag) :
		// 1er clic = SAISIR le pot le plus proche (mémorise son index), 2e clic =
		// le POSER au nouveau point monde. -1 = aucun pot saisi (en attente du 1er
		// clic). Réinitialisé si on change de geste.
		private int _grabbedContainer = -1;
		// Geste ÉPANDRE à 2 temps (mycélium ⑥, §3.2), même modèle : 1er clic =
		// SAISIR le bac/pile source (mémorise son index DANS sa tuile + l'id de
		// tuile, car `epandre` écrit le sol de CETTE tuile) ; 2e clic = le plot
		// cible. -1 = aucun tas saisi. Réinitialisé si on change de geste.
		private int _grabbedBac = -1;
		private string _grabbedBacTile;
		// Bouturer/greffer à 2 temps (tronçons ②③, palette ④), même patron : le 1er
		// clic MÉMORISE la plante-mère / le greffon (position monde + tuile), le 2e
		// clic la CIBLE. -1 = aucune saisie en cours. Réinitialisés au changement de
		// geste (SelectGeste). La mémoire des 2 clics vit ici, le serveur est stateless.
		private PlantRenderer _grabbedMother;      // bouturer : plante-mère saisie
		private PlantRenderer _grabbedScion;       // greffer : greffon saisi
		private string _grabbedScionTile;          // tuile du greffon (greffe = même tuile)
		// Rayon de désignation d'un conteneur au clic (cm MONDE) : un peu large,
		// un pot occupe ~1 plot (50 cm) et son centre peut être loin du bord cliqué.
		private const float ContainerPickRadiusCm = 60f;

		private Task<GDict> _pendingAction;        // action en vol (ou null)
		// File d'UNE intention (retour F5 Nico : en Turbo le pipe ne désemplit
		// jamais → tout clic était ignoré). Si une requête est en vol, le clic
		// est MÉMORISÉ (un seul) et part en PRIORITÉ dès que le pipe se libère
		// — avant la semaine suivante. Un 2e clic pendant l'attente l'écrase.
		private (string Verb, GDict Target, GDict Prms, PlantRenderer Node)? _queuedIntent;
		// Plante visée par l'action en vol → flash de feedback si appliquée
		// (retour F5 Nico : « tailler ne montre rien » — la coupe de quelques
		// cm sur un jeune sujet est invisible sans surlignage).
		private PlantRenderer _actionTargetNode;
		// Rayon de tolérance du clic sur une plante, en cm MONDE (kickoff B·11).
		private const float PickRadiusCm = 30f;
		// Rayon (cm MONDE) du test « quel sprite macro sous le curseur » pour
		// l'écrasement ciblé (⑥b) : plus large que PickRadiusCm car le point
		// errant peut être à ~20 cm de son ancre (merle/hérisson).
		private const float MacroPickRadiusCm = 50f;
		// Rayon du survol (étiquette) : un peu plus généreux que le clic.
		private const float HoverRadiusCm = 40f;
		// Tolérance du hit-test de segment (tranche 5), en px ÉCRAN — divisée
		// par le zoom pour travailler en canvas : le ressenti au pixel près est
		// le même à tous les paliers (comme PanSpeedPx).
		private const float SegmentPickPx = 8f;
		// Plante dont un segment est surligné (mode tailler) — pour éteindre
		// l'ancienne quand la souris change de plante.
		private PlantRenderer _highlightNode;
		private double _vigueur = -1.0, _vigueurMax;   // bloc player du snapshot
		private string _lastActionMsg = "";

		// -------------------------------------------------------------------
		// ACTIONS JOUEUR (tranche 4, volet B) — touches 1..8 = geste, clic
		// gauche = exécuter. La vue RÉSOUT la désignation (plante/plot/tuile)
		// et TRANSMET ; Python valide, applique, répond ACK/NAK + snapshot.
		// -------------------------------------------------------------------

		private void SelectGeste(int idx)
		{
			// Macro en enregistrement (⑤) : sélectionner un geste l'AJOUTE à la
			// séquence au lieu de l'activer. RecordGesteSiEnCours consomme l'appel.
			if (RecordGesteSiEnCours(idx)) return;
			ResetMacroState();   // choisir un geste normal annule un rejeu armé
			_gesteIndex = idx;
			_lastActionMsg = "";
			// Changer de geste ANNULE une saisie en cours (gestes à 2 temps :
			// déplacer pot, épandre) — sinon un 1er clic « saisir » resterait actif
			// sous un autre outil, source de confusion.
			_grabbedContainer = -1;
			_grabbedBac = -1;
			_grabbedMother = null;
			_grabbedScion = null;
			GD.Print($"[WorldView] geste : {Gestes[idx].Nom} [{idx + 1}].");
			UpdateActionHud();
			UpdatePaletteSelection();   // met à jour l'entrée active de la palette gauche
		}

		// (Le cycle Tab vit désormais dans CycleSlots — WorldView.Palette.cs — car
		// il parcourt les SLOTS occupés, pas Gestes[] brut, depuis le modèle de
		// palette gérable T1.)

		// NB (PALETTE & TIROIR ②) : les trois `Cycle*` ci-dessous ne sont plus liés à
		// une touche — le choix se fait en cliquant la rangée de réglages
		// (WorldView.Reglages.cs). Code conservé (règle : on ne jette rien).
		// Espèce courante pour `planter` (touche S). Cycle sur les lots non vides
		// du snapshot ; rien à faire si la banque est vide.
		private void CycleSeed()
		{
			if (_seeds.Count == 0)
			{
				GD.Print("[WorldView] aucune graine en banque (récoltez en automne).");
				return;
			}
			_seedIndex = (_seedIndex + 1) % _seeds.Count;
			GD.Print($"[WorldView] graine : {_seeds[_seedIndex].Key} (×{_seeds[_seedIndex].Count}).");
			UpdateActionHud();
		}

		// Substrat courant pour poser_pot / poser_bac_culture (touche B). Cycle
		// sur la liste fixe des substrats posables — modèle exact de CycleSeed.
		private void CycleSubstrat()
		{
			_substratIndex = (_substratIndex + 1) % Substrats.Length;
			GD.Print($"[WorldView] substrat : {Substrats[_substratIndex]}.");
			UpdateActionHud();
		}

		// Nature courante pour `pailler` (touche N). Cycle sur la liste fixe des
		// natures de mulch — modèle exact de CycleSubstrat/CycleSeed.
		private void CycleNature()
		{
			_natureIndex = (_natureIndex + 1) % Natures.Length;
			GD.Print($"[WorldView] nature de mulch : {Natures[_natureIndex]}.");
			UpdateActionHud();
		}

		// Met à jour la liste des graines plantables depuis player.seeds (appelé
		// par ApplySnapshot). Tri par clé = ordre de cycle STABLE d'un snapshot à
		// l'autre ; l'index est borné si un lot a disparu (tout planté).
		private void ApplySeeds(GDict seeds)
		{
			_seeds.Clear();
			foreach (var k in seeds.Keys)
				_seeds.Add((k.AsString(), seeds[k].AsInt32()));
			_seeds.Sort((a, b) => OrdreGraines(a.Key, b.Key));   // alphabétique affiché (Reglages, ④)
			if (_seedIndex >= _seeds.Count) _seedIndex = 0;
			SynchroniserReglages();   // la rangée de graines suit la banque (WorldView.Reglages.cs)
		}
	}
}
