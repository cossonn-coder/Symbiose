// SYMBIOSE — WorldView.cs
// LA VUE DU MONDE (sprint Intégration, tranches 2-4 — Option B : Python =
// moteur, Godot = vue). Au lancement : démarre le pont (SimBridge), initialise
// le monde COMPLET 20×20 m (init config="full" → 8 tuiles SECTORS + maison),
// avance quelques semaines pour que les branches poussent, puis DESSINE le
// snapshot. Depuis la tranche 3, le monde VIT : boucle hybride Planification
// (temps figé) ↔ Saison (temps réel, 1 semaine = SecondsPerWeek s), bascule à
// la touche Espace. Depuis la tranche 4, la caméra est JOUABLE (D35) : pan aux
// flèches, zoom molette par paliers, rotation de la vue par quarts de tour —
// et le joueur AGIT (volet B) : touches 1..8 = geste, clic gauche = exécuter.
// Aucune logique écologique ici : Godot est « bête », il projette et affiche.
//
// 📖 Pédagogie — le protocole d'action (volet B, kickoff t4 §3) :
// Python possède les RÈGLES (validité, coût Vigueur × maîtrise × urgence,
// effet), Godot transmet l'INTENTION : verbe + désignation non-ambiguë de la
// cible (plante par position, plot (tile,r,c), tuile, rien). Aucune
// pré-validation côté C# — un refus métier revient en `applied:false` + message
// et la vue l'AFFICHE, c'est tout. Analogie embarqué : le maître SPI envoie une
// commande structurée, l'esclave répond ACK/NAK + données — jamais le maître
// n'écrit dans les registres internes de l'esclave. Et comme le pipe est
// maître/esclave 1↔1 : UNE requête en vol, step OU action, jamais les deux.
//
// 📖 Pédagogie — le tick bloque, l'écran non (tranche 3) :
// SimBridge.StepWeek() est SYNCHRONE (~150-300 ms le tick complet). L'appeler
// dans _Process gèlerait l'affichage à chaque semaine — l'équivalent d'une
// transaction UART bloquante dans l'ISR d'affichage. À la place : on LANCE la
// requête dans une Task (thread du pool .NET), on continue à afficher, et on
// RÉCUPÈRE le résultat au prochain tour de _Process quand IsCompleted. Deux
// règles absolues, garanties par construction ici :
//  (a) la Task ne touche JAMAIS l'arbre de scène — elle ne fait que parler au
//      pipe ; le snapshot est consommé dans _Process, sur le thread principal ;
//  (b) UNE seule requête en vol à la fois — le pont est maître/esclave 1↔1,
//      deux écritures concurrentes corrompraient le pipe.
//
// 📖 Pédagogie — sim discrète, temps continu (tranche 3) :
// le moteur avance par pas d'UNE semaine ; le joueur voit un temps continu.
// La vue tient un ACCUMULATEUR : t += delta chaque frame ; quand t dépasse
// SecondsPerWeek et qu'aucun step n'est en vol, on lance le suivant.
// L'interpolation fine de croissance (tweens sur segments) est différée — à
// 60 s/semaine un swap sec suffit ; seul un FONDU marque naissances et morts.
//
// 📖 Pédagogie — le pipeline de projection :
// le moteur vit en coordonnées MONDE top-down (cm, x = est-ouest, y = nord-sud,
// 0..2000 cm). L'écran veut de l'isométrique 2:1. TOUTE la tranche tient dans
// UNE transformation : WorldToScreen(x_cm, y_cm), écrite UNE fois ci-dessous et
// utilisée pour les 3 familles d'objets (plots, maison, collets des plantes).
// C'est la leçon du bug D2 : deux projections « presque pareilles » (grille
// 96×48 codée vs sprites 78×57 réels) ne coïncident jamais.
//
// 📖 Pédagogie — l'ordre de dessin (qui cache qui) :
// en iso, un objet « plus bas à l'écran » est PLUS PROCHE de la caméra et doit
// passer DEVANT. Deux mécanismes Godot ici :
//  · ZIndex : couche explicite — le SOL (plots plats, jamais de chevauchement
//    vertical) est en ZIndex 0, les OBJETS (maison, plantes) en ZIndex 10.
//  · YSortEnabled sur le nœud "Objects" : Godot trie ses ENFANTS par Position.Y
//    croissant (= profondeur croissante en iso) à chaque frame. L'ancrage de
//    chaque objet doit donc être son point de CONTACT AU SOL le plus proche de
//    la caméra (collet pour une plante, coin sud-est pour la maison).
//
// Tuiles = PLACEHOLDERS PROCÉDURAUX (Polygon2D losanges colorés par sol),
// décision Nico 2026-06-10 : les PNG actuels sont opaques (fond gris cuit) et
// de tailles incohérentes (78×57 vs 32×23) — inutilisables pour une grille
// jointive. Les couleurs reprennent la teinte DOMINANTE mesurée sur chaque PNG.
// Les sprites définitifs reviendront une fois ré-exportés (cf. DETTE.md).

using Godot;
using System.Collections.Generic;
using System.Threading.Tasks;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// TÉMOIN DE BUILD — incrémenté à CHAQUE volet livré. Affiché en haut à
		// droite de l'écran + imprimé en console au lancement : si la version à
		// l'écran n'est pas celle annoncée par Claude, le circuit VM → sync
		// Nextcloud → build Godot n'est pas passé (piège connu depuis t3).
		public const string Build = "t6·C2 légendes heatmap — 2026-06-12";

		// -------------------------------------------------------------------
		// CALIBRATION (mesurée sur assets/sprites/tiles/tile_terre.png — D2)
		// Le losange UTILE du sprite fait 78×39 px (iso 2:1 exact) + un socle
		// d'épaisseur ~15 px que le placeholder ignore. 1 plot = 50 cm.
		// -------------------------------------------------------------------
		public const float PlotCm = 50f;                       // = constants.PLOT_CM
		public const float TileWPx = 78f;                      // largeur losange
		public const float TileHPx = 39f;                      // hauteur losange (2:1)
		public const float PxPerCmX = TileWPx / 2f / PlotCm;   // 0.78 px/cm
		public const float PxPerCmY = TileHPx / 2f / PlotCm;   // 0.39 px/cm
		// Échelle verticale (hauteurs dz) : = PxPerCmX, le standard iso 2:1 qui
		// ne « tasse » pas les verticales. Un pommier de 350 cm fait ~273 px.
		public const float PxPerCmZ = PxPerCmX;
		// Côté du monde : 20 m (échelle actée, cf. CLAUDE.md).
		public const float WorldCm = 2000f;

		// --- Orientation de la vue (D35, tranche 4) -------------------------
		// 📖 Pédagogie — pivoter une vue iso n'est PAS tourner le canvas (un
		// canvas tourné donnerait des losanges penchés). On garde la MÊME
		// projection 2:1 et on tourne le MONDE dessous : un quart de tour
		// anti-horaire autour du centre (1000,1000) cm = (x,y) → (y, 2000−x),
		// appliqué Orientation fois AVANT la projection. Conséquence : tout ce
		// qui a été positionné via WorldToScreen garde une Position figée →
		// chaque changement d'orientation passe par RebuildWorld().
		private static int _orientation;   // 0..3 quarts de tour anti-horaires

		/// <summary>
		/// LA projection monde → écran (kickoff t2 : une seule, partout).
		/// x augmente vers l'est (droite-bas du losange), y vers le sud.
		/// Depuis la tranche 4, applique d'abord l'orientation de la vue.
		/// </summary>
		public static Vector2 WorldToScreen(float xCm, float yCm)
		{
			for (int i = 0; i < _orientation; i++)
				(xCm, yCm) = (yCm, WorldCm - xCm);
			return new Vector2((xCm - yCm) * PxPerCmX, (xCm + yCm) * PxPerCmY);
		}

		/// <summary>
		/// Sœur de WorldToScreen pour les OFFSETS (vecteurs, pas points) :
		/// un déplacement relatif (segment − collet d'une plante) ne subit que
		/// la partie LINÉAIRE du quart de tour — (dx,dy) → (dy, −dx) — jamais
		/// la translation WorldCm−x, qui téléporterait l'offset de 20 m.
		/// 📖 C'est la distinction point/vecteur des transformations affines
		/// (le « w=0 » des coordonnées homogènes). Pas une 2ᵉ projection
		/// (leçon D2) : la MÊME, déclinée point/vecteur côte à côte.
		/// </summary>
		public static Vector2 WorldToScreenOffset(float dxCm, float dyCm)
		{
			for (int i = 0; i < _orientation; i++)
				(dxCm, dyCm) = (dyCm, -dxCm);
			return new Vector2((dxCm - dyCm) * PxPerCmX, (dxCm + dyCm) * PxPerCmY);
		}

		// --- Soleil de la vue (volet C) --------------------------------------
		// 📖 Pédagogie — la MÊME formule que le moteur, pas une invention :
		// fields/light.py:solar_slice (astronomie : latitude 49°N, déclinaison
		// saisonnière ±23,4°, angle horaire → azimut + élévation → direction et
		// longueur d'ombre). Le moteur n'échantillonne que 3 tranches horaires
		// pour l'INTÉGRALE écologique hebdo ; la vue, elle, balaye l'angle
		// horaire CONTINÛMENT pendant la semaine vécue : 1 semaine (60 s) ≈ 1
		// journée visuelle, du lever au coucher (le moteur n'a pas de notion de
		// jour — c'est un éclairage de vue, fidèle au modèle, jamais une règle).
		// Ces statiques sont LUES par PlantRenderer (capsules d'ombre).
		public static Vector2 SunShadowDir { get; private set; } = new Vector2(0f, -1f);
		public static float SunInvTan { get; private set; } = 1.0f;   // longueur = h × invTan
		public static float SunStrength { get; private set; } = 1.0f; // sin(élévation)
		// Touche O (volet C2, retour perf Nico) : coupe TOUTES les ombres
		// (plantes + maison) — PlantShadow._Draw devient un no-op, UpdateSun
		// s'endort. Lu par PlantShadow.
		public static bool ShadowsOn { get; private set; } = true;
		// Saison courante du snapshot (t6·A) — lue par PlantRenderer pour la
		// COULEUR des feuilles (printemps clair, automne chaud…). Les hints
		// foliage_density/organ arrivent déjà saisonnés du serveur ; seule la
		// teinte se décide côté vue. Mise à jour dans ApplySnapshot AVANT les
		// SetStructure : les redraws qui suivent voient la bonne saison.
		public static string CurrentSeason { get; private set; } = "ete";
		// Palier de zoom courant (t6·B2) — lu par MacroLife pour son LOD
		// (les bestioles n'apparaissent qu'en zoomant). Mis à jour par
		// FrameCamera et StepZoom, les deux seuls écrivains du zoom.
		public static float CurrentZoom { get; private set; } = 0.5f;
		private const float LatitudeDeg = 49.0f;    // = fields/light.py LATITUDE_DEG
		// Ombre bornée à 3,5× la hauteur : au ras de l'horizon 1/tan(élév) → ∞,
		// l'écran n'a pas besoin d'ombres kilométriques pour dire « soir ».
		private const float MaxInvTan = 3.5f;
		// Marge au lever/coucher (°) : on ne balaye pas jusqu'à l'horizon exact.
		private const float SunriseMarginDeg = 8f;
		private float _lastSunH = float.NaN;        // dernier angle horaire appliqué
		private string _lastSunSeason;

		// = SOLAR_DECLINATION de fields/light.py (clés sans accent du moteur).
		private static float DeclinationOf(string season) => season switch
		{
			"ete"   => 23.4f,
			"hiver" => -23.4f,
			_       => 0.0f,    // printemps / automne : équinoxes
		};

		/// <summary>
		/// L'INVERSE de WorldToScreen (picking, volet B) : canvas → monde (cm).
		/// 📖 La projection est linéaire (matrice 2×2, déterminant non nul) →
		/// inversible analytiquement : sx=(x−y)·a, sy=(x+y)·b donne
		/// x = sx/2a + sy/2b et y = −sx/2a + sy/2b. Puis on défait l'orientation
		/// — transformations inverses DANS L'ORDRE INVERSE : l'inverse du quart
		/// de tour (x,y)→(y, W−x) est (u,v)→(W−v, u). GetGlobalMousePosition
		/// rend la souris déjà en canvas (pan/zoom caméra défaits par Godot) —
		/// cette fonction est donc le SEUL maillon manquant. Écrite ici, à côté
		/// de l'aller (leçon D2 : jamais deux projections « presque pareilles »).
		/// </summary>
		public static Vector2 ScreenToWorld(Vector2 scr)
		{
			float x = scr.X / (2f * PxPerCmX) + scr.Y / (2f * PxPerCmY);
			float y = -scr.X / (2f * PxPerCmX) + scr.Y / (2f * PxPerCmY);
			for (int i = 0; i < _orientation; i++)
				(x, y) = (WorldCm - y, x);
			return new Vector2(x, y);
		}

		// -------------------------------------------------------------------
		// RÉGLAGES (exportés : ajustables dans l'inspecteur sans recompiler)
		// -------------------------------------------------------------------
		[Export] public int Seed = 42;
		[Export] public string Config = "full";
		// Semaines simulées au lancement, pour voir des branches (semaine 13 =
		// fin de printemps). Mesuré : ~1.8 s pour 12 ticks du monde complet —
		// acceptable en t2 ; la progression temps réel arrive en tranche 3.
		[Export] public int WarmupWeeks = 12;
		// Zoom caméra INITIAL, snappé au palier le plus proche au lancement.
		// 0.5 cadre le monde entier (~3120×2050 px) en 1920×1080.
		[Export] public float CameraZoom = 0.5f;
		// Vitesse du déplacement caméra (flèches), en px ÉCRAN par seconde :
		// ressenti identique à tous les zooms (divisée par le zoom en canvas).
		[Export] public float PanSpeedPx = 700f;
		// Cadence de la phase saison : 1 semaine simulée = N secondes réelles.
		// 60 = réglage design (plage Options prévue 30-180 s).
		[Export] public float SecondsPerWeek = 60f;
		// Si > 0, REMPLACE SecondsPerWeek — sans ça, valider une saison = 13 min
		// de patience. Défaut 3 s pour la validation t3 ; remettre à 0 ensuite.
		[Export] public float DebugSecondsPerWeek = 3f;
		// Durées des fondus d'apparition (naissance) / disparition (mort).
		[Export] public float FadeInSec = 0.6f;
		[Export] public float FadeOutSec = 0.9f;

		// Palette placeholder — teintes dominantes MESURÉES sur les PNG tuiles.
		private static readonly Color TerreColor  = new Color("967a64");
		private static readonly Color ArgileColor = new Color("cd7434");
		private static readonly Color SableColor  = new Color("f1e9bb");
		private static readonly Color SolInconnu  = new Color("777777");
		// Chemins en pierre : pas dessinés en t2 — le FOND de la fenêtre fait
		// office de bandes entre tuiles (gris pierre), gratuit et suffisant.
		private static readonly Color FondPierre  = new Color("8d8881");
		// Maison placeholder : gris calcaire. 📖 Les nuances sont attachées aux
		// murs du MONDE, pas à l'écran (fix du 1er F5 t4 : peintes « droite
		// sombre / gauche claire », la maison était identique sous les 4
		// orientations et semblait clouée pendant que le jardin tournait).
		// Le soleil est au SUD (modèle solaire symétrique E-O du moteur) :
		// sud = la plus claire, nord = la plus sombre, est/ouest intermédiaires
		// et légèrement distinctes (sinon 0° et 180° se confondent).
		// Index = mur monde, cycle horaire : 0 nord, 1 est, 2 sud, 3 ouest.
		private static readonly Color[] FacadeColors =
		{
			new Color("837c6f"),   // 0 nord (jamais éclairée)
			new Color("978f7d"),   // 1 est
			new Color("b5ac99"),   // 2 sud (plein soleil)
			new Color("a49b88"),   // 3 ouest
		};
		// Toit pyramidal (demande Nico F5 t4) : 4 pans, même éclairement monde.
		private static readonly Color[] ToitColors =
		{
			new Color("a8a294"),   // pan nord
			new Color("c2bcab"),   // pan est
			new Color("d6cfbe"),   // pan sud
			new Color("c9c2b1"),   // pan ouest
		};
		// Ombre portée placeholder (maison → nord, pied des plantes : cf.
		// PlantRenderer). L'ombre EXACTE vit dans le champ lumière Python —
		// elle arrivera en overlay heatmap (tranche 5), on ne la réinvente pas.
		private static readonly Color OmbreColor = new Color(0f, 0f, 0f, 0.16f);

		// Paliers de zoom (molette). Les paliers < 4 sont PROVISOIRES (vue
		// d'ensemble sur placeholders vectoriels, aucun artefact possible) ;
		// la règle projet « ×4-×32, jamais de fraction » redeviendra stricte
		// quand les sprites pixel art remplaceront les Polygon2D (D34).
		private static readonly float[] ZoomSteps = { 0.5f, 1f, 2f, 4f, 8f, 16f, 32f };
		private int _zoomIndex;

		private SimBridge _bridge;
		private Node2D _objects;   // maison + plantes, YSort (cf. en-tête)
		private Node2D _ground;    // sol — reconstruit à chaque rotation
		// Vie macro (t6·B) : UN nœud pour tous les points (cf. MacroLife.cs).
		// ZIndex 5 = entre sol (0) et objets (10) — les bestioles vivent au ras
		// du sol, sous les plantes. Enfant direct de WorldView : il survit à
		// RebuildWorld (il se re-projette seul à chaque dessin d'animation).
		private MacroLife _macroLife;

		// --- Overlay debug champs écologiques (t6·C, touche F6) -------------
		// ZIndex 3 : par-dessus le sol et l'ombre maison, sous la vie macro et
		// les objets. La MACHINE de requêtes vit ici (maître/esclave : la même
		// file qu'un step/action — UNE requête en vol, leçon t4·B) ; le nœud
		// FieldOverlay ne fait que dessiner la dernière grille reçue.
		private FieldOverlay _fieldOverlay;
		private bool _overlayOn;
		private string[] _fieldNames;          // registre du serveur (1 requête)
		private int _fieldIndex;
		private bool _fieldsStale;             // snapshot reçu depuis la grille
		private Task<GDict> _pendingFields;    // requête fields en vol (ou null)
		// Légende de la heatmap (correctif C2) : RichTextLabel — le BBCode
		// [color] permet les PAVÉS colorés du dégradé, un Label ne sait pas.
		private RichTextLabel _fieldLabel;
		private Node2D _house;     // pour le mode transparent (touche H)
		// Ombre maison ANIMÉE (volet C) : le polygone est recalculé quand le
		// soleil bouge — paramètres gardés en champs pour ne pas relire le GDict.
		private Polygon2D _houseShadow;
		private float _hx0, _hy0, _hx1, _hy1, _hWallCm, _hHeightCm;
		private Camera2D _camera;
		private GDict _world;      // réponse de init (tuiles + maison) — pour RebuildWorld
		private GDict _lastSnap;   // dernier snapshot appliqué — pour RebuildWorld

		// --- Boucle hybride (tranche 3) -------------------------------------
		// Planification = temps figé (défaut), Saison = temps réel, Pause =
		// saison suspendue. Espace fait Planification→Saison→Pause→Saison…
		private enum Phase { Planification, Saison, Pause }
		private Phase _phase = Phase.Planification;
		// Mode de déroulement (touche M, demande Nico F5 t4) :
		//  · Saison  = boucle hybride normale (arrêt en planification à chaque
		//              passage de saison) ;
		//  · Continu = les saisons s'enchaînent sans arrêt, cadence inchangée ;
		//  · Turbo   = continu + semaine suivante dès que la précédente répond
		//              (vitesse max du pont — observation longue durée, debug).
		private enum SimMode { Saison, Continu, Turbo }
		private SimMode _simMode = SimMode.Saison;
		// Étiquettes espèce·stade (F3 cycle) : Survol = seule l'étiquette sous
		// la souris (demande Nico 2e F5 t4, défaut), Toutes, Aucune.
		private enum LabelMode { Survol, Toutes, Aucune }
		private LabelMode _labelMode = LabelMode.Survol;
		private bool _houseGhost;             // maison transparente (H)
		private float _timeAccum;                  // secondes réelles écoulées
		private Task<GDict> _pendingStep;          // step en vol (ou null)

		// --- Actions joueur (tranche 4, volet B) ----------------------------
		// Les 8 gestes, dans l'ORDRE de la table COUTS de sim/actions.py
		// (kickoff B·10). Kind = famille de cible : p = plante (par position),
		// q = plot (tile,r,c), t = tuile, '-' = sans cible.
		private static readonly (string Verb, string Nom, char Kind)[] Gestes =
		{
			("recolter",             "récolter",       'p'),
			("deraciner",            "déraciner",      'p'),
			("ecraser",              "écraser",        'q'),
			("favoriser_auxiliaire", "favoriser aux.", 't'),
			("becher",               "bêcher",         'q'),
			("grelinette",           "grelinette",     '-'),
			("tailler",              "tailler",        'p'),
			("manger",               "manger",         'p'),
		};
		private int _gesteIndex = -1;              // aucun geste sélectionné
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
		// Rayon du survol (étiquette) : un peu plus généreux que le clic.
		private const float HoverRadiusCm = 40f;
		// Tolérance du hit-test de segment (tranche 5), en px ÉCRAN — divisée
		// par le zoom pour travailler en canvas : le ressenti au pixel près est
		// le même à tous les paliers (comme PanSpeedPx).
		private const float SegmentPickPx = 8f;
		// Plante dont un segment est surligné (mode tailler) — pour éteindre
		// l'ancienne quand la souris change de plante.
		private PlantRenderer _highlightNode;
		// Le pipe est maître/esclave 1↔1 : libre = AUCUNE requête en vol
		// (step, action ou fields). LA condition de toute écriture sur le tube.
		private bool PipeFree =>
			_pendingStep == null && _pendingAction == null && _pendingFields == null;
		private double _vigueur = -1.0, _vigueurMax;   // bloc player du snapshot
		private string _lastActionMsg = "";
		private Label _actionLabel;                // 2e ligne HUD (Vigueur+geste)
		// Plantes affichées, indexées par clé stable (tile|species|x|y) — base
		// du diff naissance/mort entre deux snapshots.
		private readonly Dictionary<string, PlantRenderer> _plantNodes = new();
		private Dictionary<string, Vector2> _origins;   // origin_cm par tuile
		private int _plantSeq;                     // noms de nœuds uniques
		// Horloge du dernier snapshot appliqué (pour le Label + fin de saison).
		private string _season;
		private int _year, _weekInSeason;
		private Label _clockLabel;

		// --- Overlay de perfs (F4, volet C2 — demande Nico) -----------------
		// Mesuré dans la vue, sans instrumenter le moteur : durée du dernier
		// tick COMPLET (pipe + sim + parse, côté joueur c'est ça la vérité),
		// cadence réelle entre deux semaines, et volumes du dernier snapshot.
		private Label _perfLabel;
		private bool _perfVisible;
		private ulong _stepStartMs;            // départ du step en vol
		private ulong _lastStepEndMs;          // fin du step précédent
		private double _lastTickMs = -1;       // durée du dernier tick (ms)
		private double _lastWeekGapSec = -1;   // s réelles entre 2 semaines
		private int _nSegments;                // segments dessinés (snapshot)
		private int _nPousses;                 // plantes sans segments

		// -------------------------------------------------------------------
		// CYCLE DE VIE
		// -------------------------------------------------------------------

		public override void _Ready()
		{
			GD.Print($"[WorldView] build : {Build}");
			RenderingServer.SetDefaultClearColor(FondPierre);
			// Champ STATIQUE (partagé avec PlantRenderer via WorldToScreen) :
			// toujours repartir « nord en haut » à l'ouverture de la scène.
			_orientation = 0;

			_bridge = new SimBridge();
			if (!_bridge.Start())
				return;

			var world = _bridge.Init(Seed, Config);
			if (world == null) { _bridge.Quit(); return; }
			_world = world;

			ulong t0 = Time.GetTicksMsec();
			GDict snap = null;
			for (int i = 0; i < WarmupWeeks; i++)
				snap = _bridge.StepWeek();
			if (snap == null) snap = _bridge.GetSnapshot();
			if (snap == null) { _bridge.Quit(); return; }
			GD.Print($"[WorldView] warmup {WarmupWeeks} semaines en "
					 + $"{Time.GetTicksMsec() - t0} ms — semaine {snap["week"].AsInt32()}, "
					 + $"{snap["season"].AsString()}.");

			BuildGround(world);

			_objects = new Node2D { Name = "Objects", ZIndex = 10, YSortEnabled = true };
			AddChild(_objects);
			BuildHouse(world);

			// Origins des tuiles en cache : le snapshot donne des positions
			// LOCALES à la tuile, on en aura besoin à chaque semaine.
			_origins = new Dictionary<string, Vector2>();
			foreach (var tv in world["tiles"].AsGodotArray())
			{
				var t = tv.AsGodotDictionary();
				_origins[t["id"].AsString()] = new Vector2(
					(float)t["origin_x_cm"].AsDouble(),
					(float)t["origin_y_cm"].AsDouble());
			}

			_macroLife = new MacroLife { Name = "MacroLife", ZIndex = 5 };
			AddChild(_macroLife);

			_fieldOverlay = new FieldOverlay
			{
				Name = "FieldOverlay", ZIndex = 3, Visible = false,
			};
			AddChild(_fieldOverlay);

			BuildHud();
			ApplySnapshot(snap, fade: false);   // monde initial : pas de fondu

			FrameCamera();
			// Le process Python reste OUVERT, au repos en Planification : c'est
			// le mapping de la boucle hybride. Fermé à _ExitTree.
		}

		public override void _ExitTree()
		{
			// Une requête encore en vol (step OU action) occupe le pipe : on
			// l'attend avant d'écrire "quit" (sinon deux écritures concurrentes
			// — règle (b) de l'en-tête).
			try { _pendingStep?.Wait(2000); } catch { /* moteur déjà mort : Quit gère */ }
			try { _pendingAction?.Wait(2000); } catch { /* idem */ }
			try { _pendingFields?.Wait(2000); } catch { /* idem */ }
			_bridge?.Quit();
		}

		// -------------------------------------------------------------------
		// BOUCLE HYBRIDE — entrées + horloge temps réel (tranche 3)
		// -------------------------------------------------------------------

		public override void _UnhandledInput(InputEvent ev)
		{
			// Clavier provisoire (les vrais bindings/boutons = sprint UI) :
			// Espace = saison/pause ; PageUp/PageDown = pivoter la vue (touches
			// univoques en AZERTY).
			if (ev is InputEventKey k && k.Pressed && !k.Echo)
			{
				// Gestes 1..8 en PhysicalKeycode (POSITION de la touche, pas son
				// étiquette) : en AZERTY la rangée des chiffres non-shiftée émet
				// &é"'(-è_ comme Keycode — le code physique, lui, reste Key1..8
				// quel que soit le layout. 📖 C'est la différence scancode/keysym.
				if (k.PhysicalKeycode >= Key.Key1 && k.PhysicalKeycode <= Key.Key8)
				{
					SelectGeste((int)(k.PhysicalKeycode - Key.Key1));
					return;
				}
				switch (k.Keycode)
				{
					case Key.Space:    TogglePhase();  break;
					// Monde anti-horaire = la CAMÉRA orbite vers la droite
					// (ressenti validé par Nico au 1er F5 t4).
					case Key.Pageup:   RotateView(+1); break;
					case Key.Pagedown: RotateView(-1); break;
					case Key.M:        CycleSimMode();    break;
					case Key.F3:       ToggleLabels();    break;
					case Key.F4:       TogglePerf();      break;
					case Key.H:        ToggleHouseGhost(); break;
					case Key.O:        ToggleShadows();   break;
					case Key.I:        ToggleMacroLife(); break;
					case Key.F6:
						if (k.ShiftPressed) CycleField();
						else ToggleFieldOverlay();
						break;
				}
			}
			// Molette = paliers de zoom (décision Nico 2026-06-10 : molette,
			// pas de touches). Clic gauche = exécuter le geste courant (volet B).
			else if (ev is InputEventMouseButton mb && mb.Pressed)
			{
				if (mb.ButtonIndex == MouseButton.WheelUp)   StepZoom(+1);
				if (mb.ButtonIndex == MouseButton.WheelDown) StepZoom(-1);
				if (mb.ButtonIndex == MouseButton.Left)
					TryAction(GetGlobalMousePosition(), mb.ShiftPressed);
			}
		}

		private void TogglePhase()
		{
			// Un print par appui : si RIEN n'apparaît en console en tapant
			// Espace, c'est que l'input ne parvient pas au jeu (focus).
			switch (_phase)
			{
				case Phase.Planification:
					_timeAccum = 0f;
					SetPhase(Phase.Saison);
					GD.Print("[WorldView] Espace → saison lancée.");
					break;
				case Phase.Saison:
					SetPhase(Phase.Pause);
					GD.Print("[WorldView] Espace → pause.");
					break;
				case Phase.Pause:
					SetPhase(Phase.Saison);
					GD.Print("[WorldView] Espace → reprise.");
					break;
			}
		}

		private void SetPhase(Phase phase)
		{
			_phase = phase;
			UpdateClock();
		}

		private void CycleSimMode()
		{
			_simMode = (SimMode)(((int)_simMode + 1) % 3);
			GD.Print($"[WorldView] M → mode simulation : {_simMode}.");
			UpdateClock();
		}

		private void ToggleLabels()
		{
			// Cycle Survol → Toutes → Aucune. En Survol, c'est UpdateHoverTag
			// (chaque frame) qui allume la seule étiquette sous la souris.
			_labelMode = (LabelMode)(((int)_labelMode + 1) % 3);
			bool all = _labelMode == LabelMode.Toutes;
			foreach (var node in _plantNodes.Values)
			{
				var tag = node.GetNodeOrNull<Label>("Tag");
				if (tag != null) tag.Visible = all;
			}
			GD.Print($"[WorldView] F3 → étiquettes : {_labelMode}.");
		}

		private void ToggleHouseGhost()
		{
			_houseGhost = !_houseGhost;
			ApplyHouseGhost();
			GD.Print($"[WorldView] H → maison {(_houseGhost ? "transparente" : "opaque")}.");
		}

		private void ToggleShadows()
		{
			ShadowsOn = !ShadowsOn;
			if (_houseShadow != null) _houseShadow.Visible = ShadowsOn;
			// Re-dessiner les nœuds d'ombre : OFF → _Draw vide les efface ;
			// ON → repartir d'un soleil « sale » force le recalcul immédiat.
			_lastSunH = float.NaN;
			foreach (var node in _plantNodes.Values)
				node.GetNodeOrNull<Node2D>("Shadow")?.QueueRedraw();
			GD.Print($"[WorldView] O → ombres {(ShadowsOn ? "ON" : "OFF")}.");
		}

		// Touche F6 (t6·C) : heatmap ON/OFF. OFF = coût STRICTEMENT nul
		// (critère kickoff) : nœud caché, _fieldsStale ignoré, plus AUCUNE
		// requête `fields` ne part — le serveur n'est même pas au courant.
		private void ToggleFieldOverlay()
		{
			_overlayOn = !_overlayOn;
			if (_fieldOverlay != null) _fieldOverlay.Visible = _overlayOn;
			if (_overlayOn) _fieldsStale = true;   // (re)fetch au prochain tour
			UpdateFieldHud();
			GD.Print($"[WorldView] F6 → heatmap {(_overlayOn ? "ON" : "OFF")}.");
		}

		// Maj+F6 : champ suivant (cycle sur le registre du serveur).
		private void CycleField()
		{
			if (!_overlayOn || _fieldNames == null || _fieldNames.Length == 0)
			{
				GD.Print("[WorldView] Maj+F6 : ouvrir d'abord l'overlay (F6).");
				return;
			}
			_fieldIndex = (_fieldIndex + 1) % _fieldNames.Length;
			_fieldsStale = true;   // la grille du nouveau champ part au prochain tour
			UpdateFieldHud();
			GD.Print($"[WorldView] Maj+F6 → champ : {_fieldNames[_fieldIndex]}.");
		}

		// Légende de la heatmap (correctif C2, demande Nico) : les DEUX pôles
		// du dégradé du champ affiché, en pavés colorés + libellés + bornes
		// réelles — exactement les couleurs que FieldOverlay interpole.
		// Affichée UNIQUEMENT quand son champ est à l'écran.
		private void UpdateFieldHud()
		{
			if (_fieldLabel == null) return;
			if (!_overlayOn)
			{
				_fieldLabel.Visible = false;
				return;
			}
			_fieldLabel.Visible = true;
			string nom = _fieldNames != null && _fieldNames.Length > 0
				? _fieldNames[_fieldIndex] : "…";
			var (lo, hi, labLo, labHi) = FieldOverlay.PaletteOf(nom);
			string bornes = _fieldOverlay?.FieldName == nom
				? $"[color=#{lo.ToHtml(false)}]██[/color] {labLo} ({_fieldOverlay.Min:F2})"
				  + $"  →  [color=#{hi.ToHtml(false)}]██[/color] {labHi} ({_fieldOverlay.Max:F2})"
				: "chargement…";
			_fieldLabel.Text =
				$"heatmap (debug) — {nom} : {bornes}   ·   Maj+F6 champ suivant";
		}

		// Touche I (correctif t6·B2, demande Nico F5) : montre/cache la vie
		// macro. Visible=false court-circuite _Process ET le dessin (coût nul) ;
		// les données continuent de suivre les snapshots — rallumer est gratuit.
		private void ToggleMacroLife()
		{
			if (_macroLife == null) return;
			_macroLife.Visible = !_macroLife.Visible;
			GD.Print($"[WorldView] I → vie macro {(_macroLife.Visible ? "ON" : "OFF")}.");
		}

		private void TogglePerf()
		{
			_perfVisible = !_perfVisible;
			if (_perfLabel != null) _perfLabel.Visible = _perfVisible;
			GD.Print($"[WorldView] F4 → perfs {(_perfVisible ? "ON" : "OFF")}.");
		}

		// Modulate = teinte × alpha appliquée au nœud ET ses enfants : un seul
		// réglage rend les 5 polygones de la maison fantomatiques. L'ombre
		// portée n'est PAS affectée (elle vit dans _ground) : une maison
		// transparente ombre toujours — c'est le moteur qui décide, pas la vue.
		private void ApplyHouseGhost()
		{
			if (_house != null)
				_house.Modulate = new Color(1f, 1f, 1f, _houseGhost ? 0.15f : 1f);
		}

		public override void _Process(double delta)
		{
			// 0) Caméra : pan aux flèches — actif dans TOUTES les phases (la
			//    caméra n'interagit jamais avec la machine à états).
			UpdateCameraPan((float)delta);
			// 0b) Étiquette au survol (volet B) — chaque frame, ~170 distances :
			//     trivial, pas de cache à inventer.
			UpdateHoverTag();
			// 0b') Surbrillance de la branche sous la souris (mode tailler, t5).
			//      Chaque frame aussi, mais le redraw ne part qu'au CHANGEMENT.
			UpdateTailleHighlight();
			// 0c) Soleil (volet C) : la jauge intra-semaine est l'heure du jour.
			//     Early-out interne si le soleil a bougé de moins de 2°.
			UpdateSun();
			// 0d) Overlay de perfs (F4) — toutes phases.
			if (_perfVisible) UpdatePerf();

			// 1) Consommer un step terminé — TOUJOURS, même en pause : la
			//    semaine était déjà engagée côté moteur, son résultat est dû.
			if (_pendingStep != null && _pendingStep.IsCompleted)
			{
				var step = _pendingStep;
				_pendingStep = null;
				ulong now = Time.GetTicksMsec();
				_lastTickMs = now - _stepStartMs;
				if (_lastStepEndMs > 0) _lastWeekGapSec = (now - _lastStepEndMs) / 1000.0;
				_lastStepEndMs = now;
				if (step.IsFaulted || step.Result == null)
				{
					// Moteur mort ou réponse invalide (SimBridge a déjà loggé le
					// détail) : on fige le jeu plutôt que de marteler un pipe HS.
					GD.PrintErr("[WorldView] step_week en échec — retour en planification.");
					SetPhase(Phase.Planification);
					return;
				}
				ApplySnapshot(step.Result);
			}

			// 1b) Consommer une action terminée (volet B) : afficher l'ACK/NAK
			//     métier et appliquer le snapshot frais joint (un déracinement
			//     s'efface par le fondu t3, sans step).
			if (_pendingAction != null && _pendingAction.IsCompleted)
			{
				var act = _pendingAction;
				var targetNode = _actionTargetNode;
				_pendingAction = null;
				_actionTargetNode = null;
				if (act.IsFaulted || act.Result == null)
					GD.PrintErr("[WorldView] action en échec de PROTOCOLE (cf. SimBridge).");
				else
				{
					var res = act.Result["result"].AsGodotDictionary();
					bool applied = res["applied"].AsBool();
					_lastActionMsg = res["message"].AsString();
					GD.Print($"[WorldView] action {(applied ? "OK" : "REFUSÉE")} : "
							 + $"{_lastActionMsg} (coût {res["cost"].AsDouble():F1}, "
							 + $"Vigueur {res["vigueur"].AsDouble():F1}).");
					if (!applied) FlashActionLabel();
					ApplySnapshot(act.Result["snapshot"].AsGodotDictionary());
					// Flash de la plante ciblée — APRÈS ApplySnapshot : si elle
					// vient de mourir (déraciner), son fondu de sortie anime
					// déjà modulate, on ne lui dispute pas la propriété.
					if (applied && targetNode != null && IsInstanceValid(targetNode)
						&& _plantNodes.ContainsValue(targetNode))
					{
						targetNode.Modulate = new Color(1.7f, 1.7f, 1.1f);
						targetNode.CreateTween().TweenProperty(
							targetNode, "modulate", Colors.White, 0.5f);
					}
				}
			}

			// 1c) File d'une intention : le pipe vient de se libérer → l'action
			//     mémorisée part EN PRIORITÉ sur la semaine suivante (sinon, en
			//     Turbo, le step relancé immédiatement affamerait les clics).
			if (_queuedIntent != null && PipeFree)
			{
				var it = _queuedIntent.Value;
				_queuedIntent = null;
				LaunchAction(it.Verb, it.Target, it.Prms, it.Node);
			}

			// 1d) Consommer une réponse `fields` (t6·C) : registre (liste de
			//     noms) ou grilles — distingués par la clé présente.
			if (_pendingFields != null && _pendingFields.IsCompleted)
			{
				var f = _pendingFields;
				_pendingFields = null;
				if (f.IsFaulted || f.Result == null)
					GD.PrintErr("[WorldView] requête fields en échec (cf. SimBridge).");
				else if (f.Result.ContainsKey("fields"))
				{
					var arr = f.Result["fields"].AsGodotArray();
					_fieldNames = new string[arr.Count];
					for (int i = 0; i < arr.Count; i++)
						_fieldNames[i] = arr[i].AsString();
					GD.Print($"[WorldView] fields : {_fieldNames.Length} champs au registre.");
					// la grille du champ courant part au prochain tour (stale).
				}
				else
				{
					_fieldOverlay.SetGrid(f.Result["field"].AsString(),
										  f.Result["tiles"].AsGodotDictionary(),
										  _origins);
					_fieldsStale = false;
					// Témoin console (diag F5) : la grille est bien arrivée.
					GD.Print($"[WorldView] heatmap {_fieldOverlay.FieldName} : "
							 + $"min {_fieldOverlay.Min:F2}, max {_fieldOverlay.Max:F2}.");
				}
				UpdateFieldHud();
			}

			// 1e) Lancer la requête fields suivante — UNIQUEMENT overlay ON et
			//     pipe libre (priorité : action en file > fields > step — un
			//     instrument ne double jamais un geste). D'abord le registre
			//     (une fois), puis la grille du champ courant si périmée.
			if (_overlayOn && PipeFree && _queuedIntent == null)
			{
				if (_fieldNames == null)
					_pendingFields = Task.Run(() => _bridge.Fields());
				else if (_fieldsStale && _fieldNames.Length > 0)
				{
					string nom = _fieldNames[_fieldIndex];
					_pendingFields = Task.Run(() => _bridge.Fields(nom));
				}
			}

			// 2) Accumulateur temps réel (seulement quand la saison court).
			if (_phase != Phase.Saison) return;
			_timeAccum += (float)delta;
			float spw = DebugSecondsPerWeek > 0f ? DebugSecondsPerWeek : SecondsPerWeek;
			if (_simMode == SimMode.Turbo) spw = 0f;   // step dès que le pont répond
			// Le step ne part que si le PIPE est libre : ni step, ni action,
			// ni fields en vol (maître/esclave 1↔1 — une requête d'instrument
			// retarde la semaine d'une frame ou deux, jamais elle ne corrompt
			// le tube).
			if (_timeAccum >= spw && PipeFree)
			{
				_timeAccum = 0f;
				_stepStartMs = Time.GetTicksMsec();
				// Task.Run : la requête part sur un thread du pool ; on ne
				// touche à RIEN d'autre qu'au pipe depuis ce thread (règle (a)).
				_pendingStep = Task.Run(() => _bridge.StepWeek());
			}
			UpdateClock();   // anime la jauge intra-semaine (fige en pause)
		}

		/// <summary>
		/// Hook de fin de saison (le `season` du snapshot a changé).
		/// TODO (sprint save global) : déclencher l'auto-save ici — le
		/// protocole v0 n'a pas de commande `save`, on ne l'invente pas en t3.
		/// </summary>
		private void OnSeasonEnd() { }

		// -------------------------------------------------------------------
		// SOLEIL (volet C) — portage de fields/light.py:solar_slice, balayé
		// continûment sur la semaine vécue. Appelé chaque frame, mais ne
		// REDESSINE que si l'angle horaire a bougé de ≥ 2° (à 60 s/semaine
		// c'est ~1 redraw/s ; à 3 s debug, ~15/s — toujours trivial).
		// -------------------------------------------------------------------

		private void UpdateSun()
		{
			if (!ShadowsOn) return;        // ombres coupées (O) : zéro travail
			if (_season == null) return;   // pas encore de snapshot
			float spw = DebugSecondsPerWeek > 0f ? DebugSecondsPerWeek : SecondsPerWeek;

			// Lever/coucher astronomiques : cos H_set = −tan φ · tan δ. C'est
			// LUI qui fait les jours longs d'été (±120° à 49°N) et courts
			// d'hiver (±60°) — aucune table à écrire, la formule décide.
			float phi = Mathf.DegToRad(LatitudeDeg);
			float dec = Mathf.DegToRad(DeclinationOf(_season));
			float hSet = Mathf.RadToDeg(Mathf.Acos(
				Mathf.Clamp(-Mathf.Tan(phi) * Mathf.Tan(dec), -1f, 1f)));

			// Angle horaire courant : la jauge intra-semaine devient l'heure du
			// jour. Temps figé (Planification), plein régime (Turbo) → midi.
			float h;
			if (_phase == Phase.Planification || _simMode == SimMode.Turbo || spw <= 0f)
				h = 0f;
			else
				h = Mathf.Lerp(-hSet + SunriseMarginDeg, hSet - SunriseMarginDeg,
							   Mathf.Clamp(_timeAccum / spw, 0f, 1f));
			// En Pause, _timeAccum est figé → h ne bouge plus : l'ombre attend.

			if (_season == _lastSunSeason && !float.IsNaN(_lastSunH)
				&& Mathf.Abs(h - _lastSunH) < 2f)
				return;   // soleil quasi immobile : rien à redessiner
			_lastSunH = h;
			_lastSunSeason = _season;

			// --- solar_slice (fields/light.py), au degré près -----------------
			float H = Mathf.DegToRad(h);
			float sinElev = Mathf.Sin(phi) * Mathf.Sin(dec)
				+ Mathf.Cos(phi) * Mathf.Cos(dec) * Mathf.Cos(H);
			if (sinElev <= 1e-3f) return;   // sous l'horizon (marge le rend rare)
			float elev = Mathf.Asin(Mathf.Clamp(sinElev, -1f, 1f));
			float cosElev = Mathf.Cos(elev);
			float cosAz = (Mathf.Sin(dec) - sinElev * Mathf.Sin(phi))
				/ (cosElev * Mathf.Cos(phi));
			float az = Mathf.Acos(Mathf.Clamp(cosAz, -1f, 1f));
			if (h > 0f) az = Mathf.Tau - az;   // après-midi → soleil à l'Ouest

			// L'ombre pointe à l'OPPOSÉ du soleil. Monde : x = Est, y = Sud →
			// midi (az = 180°) donne (0, −1) = plein Nord, comme le moteur.
			SunShadowDir = new Vector2(-Mathf.Sin(az), Mathf.Cos(az));
			SunInvTan = Mathf.Min(cosElev / sinElev, MaxInvTan);
			SunStrength = sinElev;

			// Re-projeter les ombres : maison (polygone) + nœuds PlantShadow
			// SEULS (volet C2 : jamais les segments des plantes — le balayage
			// ne coûte plus ∝ taille des plantes).
			UpdateHouseShadow();
			foreach (var node in _plantNodes.Values)
				node.GetNodeOrNull<Node2D>("Shadow")?.QueueRedraw();
		}

		// Ombre de la maison = enveloppe convexe, EN COORDONNÉES MONDE, de
		// l'empreinte au sol + des coins hauts-de-mur projetés au sol le long
		// de la direction d'ombre + du faîte projeté — puis projection écran
		// point à point (une enveloppe convexe reste convexe par application
		// affine : l'ordre des sommets survit à la projection ET à la rotation).
		private void UpdateHouseShadow()
		{
			if (_houseShadow == null) return;
			Vector2 d = SunShadowDir;
			float lWall = _hWallCm * SunInvTan;
			float lApex = _hHeightCm * SunInvTan;
			var w = new Vector2[]
			{
				new(_hx0, _hy0), new(_hx1, _hy0), new(_hx1, _hy1), new(_hx0, _hy1),
				new Vector2(_hx0, _hy0) + d * lWall, new Vector2(_hx1, _hy0) + d * lWall,
				new Vector2(_hx1, _hy1) + d * lWall, new Vector2(_hx0, _hy1) + d * lWall,
				new Vector2((_hx0 + _hx1) / 2f, (_hy0 + _hy1) / 2f) + d * lApex,
			};
			var hull = Geometry2D.ConvexHull(w);
			var scr = new Vector2[hull.Length];
			for (int i = 0; i < hull.Length; i++)
				scr[i] = WorldToScreen(hull[i].X, hull[i].Y);
			_houseShadow.Polygon = scr;
			// Soleil bas = lumière faible = ombre plus pâle (et plus longue).
			var col = OmbreColor;
			col.A = OmbreColor.A * Mathf.Clamp(SunStrength * 1.4f, 0.3f, 1f);
			_houseShadow.Color = col;
		}

		// -------------------------------------------------------------------
		// SOL — un losange placeholder par plot
		// -------------------------------------------------------------------

		private void BuildGround(GDict world)
		{
			_ground = new Node2D { Name = "Ground", ZIndex = 0 };
			AddChild(_ground);
			var ground = _ground;

			int nPlots = 0;
			foreach (var tv in world["tiles"].AsGodotArray())
			{
				var t = tv.AsGodotDictionary();
				float ox = (float)t["origin_x_cm"].AsDouble();
				float oy = (float)t["origin_y_cm"].AsDouble();
				int rows = t["rows"].AsInt32();
				int cols = t["cols"].AsInt32();
				Color soil = SoilColor(t["soil"].AsString());

				for (int r = 0; r < rows; r++)
					for (int c = 0; c < cols; c++)
					{
						// Centre du plot en cm monde → centre du losange écran.
						float cx = ox + (c + 0.5f) * PlotCm;
						float cy = oy + (r + 0.5f) * PlotCm;
						// Damier subtil (±5 %) : rend la grille lisible sans
						// dessiner de bordures (pixel art sobre).
						var poly = MakeLozenge((r + c) % 2 == 0
							? soil : soil.Darkened(0.05f));
						poly.Position = WorldToScreen(cx, cy);
						ground.AddChild(poly);
						nPlots++;
					}
			}
			// Boussole posée AU SOL (demande Nico F5 t4 : « j'ai perdu le
			// nord ») : les 4 points cardinaux aux bords du monde. Enfants de
			// _ground → reconstruits à chaque rotation, ils suivent le MONDE :
			// le N reste au nord du jardin, où qu'il parte à l'écran.
			AddCardinal("N", WorldCm / 2f, -90f);
			AddCardinal("S", WorldCm / 2f, WorldCm + 40f);
			AddCardinal("E", WorldCm + 70f, WorldCm / 2f);
			AddCardinal("O", -70f, WorldCm / 2f);

			GD.Print($"[WorldView] sol : {nPlots} plots placeholder dessinés.");
		}

		private void AddCardinal(string text, float xCm, float yCm)
		{
			var l = new Label { Text = text };
			l.AddThemeFontSizeOverride("font_size", 44);
			l.AddThemeColorOverride("font_color", new Color(1f, 1f, 1f, 0.7f));
			l.AddThemeColorOverride("font_outline_color", Colors.Black);
			l.AddThemeConstantOverride("outline_size", 8);
			// Position d'un Label = son coin haut-gauche → recentrage à la
			// louche sur le point projeté (instrument debug, pas de la typo).
			l.Position = WorldToScreen(xCm, yCm) - new Vector2(14f, 30f);
			_ground.AddChild(l);
		}

		private static Color SoilColor(string soil) => soil switch
		{
			"terre"  => TerreColor,
			"argile" => ArgileColor,
			"sable"  => SableColor,
			_        => SolInconnu,
		};

		// Losange iso 2:1 d'un plot, centré sur (0,0) : ±39 px en x, ±19.5 en y.
		private static Polygon2D MakeLozenge(Color color) => new Polygon2D
		{
			Polygon = new[]
			{
				new Vector2(0f, -TileHPx / 2f),   // sommet nord
				new Vector2(TileWPx / 2f, 0f),    // est
				new Vector2(0f, TileHPx / 2f),    // sud
				new Vector2(-TileWPx / 2f, 0f),   // ouest
			},
			Color = color,
		};

		// -------------------------------------------------------------------
		// MAISON — placeholder procédural (D4 reste ouverte : sprite normand à
		// venir ; ici on donne l'OCCUPATION et l'ÉCHELLE). Empreinte iso au sol
		// + 2 façades visibles (est, sud) extrudées de height_cm + toit plat.
		// -------------------------------------------------------------------

		private void BuildHouse(GDict world)
		{
			var h = world["house"].AsGodotDictionary();
			var fp = h["footprint_cm"].AsGodotArray();   // [x0, y0, x1, y1]
			float x0 = (float)fp[0].AsDouble(), y0 = (float)fp[1].AsDouble();
			float x1 = (float)fp[2].AsDouble(), y1 = (float)fp[3].AsDouble();
			float heightCm = (float)h["height_cm"].AsDouble();
			float hPx = heightCm * PxPerCmZ;

			// Murs aux 2/3 de la hauteur, faîte pyramidal au sommet.
			float wallCm = heightCm * 0.66f;

			// Les 4 coins au sol, cycle HORAIRE monde nw→ne→se→sw, projetés
			// AVEC l'orientation courante. Mur i = entre les coins i et i+1 :
			// 0 = nord, 1 = est, 2 = sud, 3 = ouest — le MÊME index lit les
			// couleurs monde (FacadeColors/ToitColors) : c'est ce qui fait
			// visiblement tourner la maison. Le coin « avant » = le plus BAS à
			// l'écran (le plus proche caméra) : ancrage YSort ; les 2 murs
			// visibles sont ceux qui le touchent. En orientation 0, front = se
			// → murs est + sud, comme en t2.
			Vector2[] scr =
			{
				WorldToScreen(x0, y0), WorldToScreen(x1, y0),
				WorldToScreen(x1, y1), WorldToScreen(x0, y1),
			};
			int front = 0;
			for (int i = 1; i < 4; i++)
				if (scr[i].Y > scr[front].Y) front = i;

			Vector2 anchor = scr[front];
			_house = new Node2D { Name = "House", Position = anchor };

			// Coins locaux au nœud + montants : haut de mur, faîte central.
			var c = new Vector2[4];
			for (int i = 0; i < 4; i++) c[i] = scr[i] - anchor;
			Vector2 upWall = new Vector2(0f, -wallCm * PxPerCmZ);
			Vector2 apex = WorldToScreen((x0 + x1) / 2f, (y0 + y1) / 2f)
				- anchor - new Vector2(0f, hPx);

			int rightWall = (front + 3) % 4;   // mur côté droit écran
			int leftWall  = front;             // mur côté gauche écran
			// Ordre peintre : pans de toit ARRIÈRE d'abord (leur pointe dépasse
			// au-dessus des pans avant), puis murs visibles, puis pans avant.
			foreach (int w in new[] { (front + 1) % 4, (front + 2) % 4 })
				_house.AddChild(RoofPane(c, w, upWall, apex));
			foreach (int w in new[] { rightWall, leftWall })
				_house.AddChild(new Polygon2D
				{
					Polygon = new[] { c[w], c[(w + 1) % 4],
									  c[(w + 1) % 4] + upWall, c[w] + upWall },
					Color = FacadeColors[w],
				});
			foreach (int w in new[] { rightWall, leftWall })
				_house.AddChild(RoofPane(c, w, upWall, apex));

			_objects.AddChild(_house);
			ApplyHouseGhost();   // ré-applique la transparence après un rebuild

			// Ombre portée ANIMÉE (volet C) : polygone recalculé par
			// UpdateHouseShadow quand le soleil bouge. Posée dans _ground :
			// sous tous les objets, par-dessus les plots (ordre d'ajout), et
			// reconstruite avec la rotation (BuildHouse rappelée).
			_houseShadow = new Polygon2D { Color = OmbreColor };
			_ground.AddChild(_houseShadow);
			(_hx0, _hy0, _hx1, _hy1) = (x0, y0, x1, y1);
			(_hWallCm, _hHeightCm) = (wallCm, heightCm);
			UpdateHouseShadow();

			GD.Print($"[WorldView] maison placeholder : empreinte "
					 + $"[{x0},{y0}]→[{x1},{y1}] cm, h={heightCm} cm (murs {wallCm} cm).");
		}

		// Un pan du toit pyramidal : du haut du mur w au faîte central.
		private static Polygon2D RoofPane(Vector2[] c, int w, Vector2 upWall, Vector2 apex)
			=> new Polygon2D
			{
				Polygon = new[] { c[w] + upWall, c[(w + 1) % 4] + upWall, apex },
				Color = ToitColors[w],
			};

		// -------------------------------------------------------------------
		// PLANTES — appliquer un snapshot = DIFF avec l'affiché (tranche 3).
		// Clé stable d'une plante : tuile + espèce + position (une plante ne
		// bouge jamais ; le moteur n'expose pas d'id, la position en tient lieu).
		//  · clé connue   → SetStructure (swap sec : la plante a grandi)
		//  · clé nouvelle → créer + fondu d'apparition (naissance)
		//  · clé disparue → fondu de disparition puis QueueFree (mort)
		// Sol et maison ne bougent pas. ~150 nœuds à 1 fois/60 s : trivial.
		// -------------------------------------------------------------------

		private static string PlantKey(GDict p) =>
			$"{p["tile"].AsString()}|{p["species"].AsString()}"
			+ $"|{p["x_cm"].AsDouble():F1}|{p["y_cm"].AsDouble():F1}";

		// Étiquette debug « espèce · stade » sous la plante (demande Nico F5
		// t4), toggle F3. Enfant du PlantRenderer : elle suit position,
		// rotation de vue et fondu (Modulate) gratuitement. Elle zoome avec le
		// monde — assumé, c'est un instrument de debug, pas l'UI finale.
		private Label MakeTag(GDict p)
		{
			var tag = new Label { Name = "Tag", Visible = _labelMode == LabelMode.Toutes };
			tag.AddThemeFontSizeOverride("font_size", 11);
			tag.AddThemeColorOverride("font_color", new Color(1f, 1f, 1f, 0.85f));
			tag.AddThemeColorOverride("font_outline_color", Colors.Black);
			tag.AddThemeConstantOverride("outline_size", 4);
			tag.Text = TagText(p);
			tag.Position = new Vector2(-30f, 6f);   // sous le collet, centré à la louche
			return tag;
		}

		private static string TagText(GDict p) =>
			$"{p["species"].AsString()} · {p["stage_name"].AsString()}";

		private void ApplySnapshot(GDict snap, bool fade = true)
		{
			_lastSnap = snap;   // gardé pour RebuildWorld (rotation)

			// Horloge (52 sem/an, saisons de 13 — sim/engine.py saison_de).
			_year = snap["year"].AsInt32();
			int weekInYear = snap["week_in_year"].AsInt32();
			_weekInSeason = ((weekInYear - 1) % 13) + 1;
			string season = snap["season"].AsString();
			CurrentSeason = season;   // AVANT les SetStructure (couleur feuilles t6·A)

			int born = 0, grown = 0, empty = 0, nSegs = 0;
			var seen = new HashSet<string>();
			foreach (var pv in snap["plants"].AsGodotArray())
			{
				var p = pv.AsGodotDictionary();
				var structure = StructureLoader.FromSnapshot(p);
				if (structure.Segments.Count == 0)
				{
					empty++;   // germination sans bois : rien à dessiner encore
					continue;
				}
				nSegs += structure.Segments.Count;
				string key = PlantKey(p);
				seen.Add(key);

				if (_plantNodes.TryGetValue(key, out var node))
				{
					node.SetStructure(structure);   // la plante a poussé
					var t = node.GetNodeOrNull<Label>("Tag");
					if (t != null) t.Text = TagText(p);   // le stade évolue
					grown++;
					continue;
				}
				Vector2 o = _origins[p["tile"].AsString()];
				float wx = o.X + (float)p["x_cm"].AsDouble();
				float wy = o.Y + (float)p["y_cm"].AsDouble();
				var renderer = new PlantRenderer
				{
					Position = WorldToScreen(wx, wy),
					Name = $"{p["tile"].AsString()}_{p["species"].AsString()}_{_plantSeq++}",
				};
				// Métadonnées de picking (volet B) : position MONDE pour la
				// distance au clic/survol, et la désignation EXACTE du snapshot
				// (tile + x/y locaux) renvoyée telle quelle au serveur — la
				// position est l'identité, on n'invente pas d'id (kickoff §8).
				renderer.SetMeta("wx", wx);
				renderer.SetMeta("wy", wy);
				renderer.SetMeta("tile", p["tile"]);
				renderer.SetMeta("lx", p["x_cm"]);
				renderer.SetMeta("ly", p["y_cm"]);
				if (fade) renderer.Modulate = new Color(1f, 1f, 1f, 0f);
				_objects.AddChild(renderer);
				renderer.SetStructure(structure);
				renderer.AddChild(MakeTag(p));
				if (fade)
					renderer.CreateTween()
						.TweenProperty(renderer, "modulate:a", 1f, FadeInSec);
				_plantNodes[key] = renderer;
				born++;
			}

			// Plantes affichées absentes du snapshot = mortes → fondu sortant.
			var dead = new List<string>();
			foreach (var kv in _plantNodes)
				if (!seen.Contains(kv.Key)) dead.Add(kv.Key);
			foreach (string key in dead)
			{
				var node = _plantNodes[key];
				_plantNodes.Remove(key);   // hors index : le fondu finit seul
				if (fade)
				{
					var tw = node.CreateTween();
					tw.TweenProperty(node, "modulate:a", 0f, FadeOutSec);
					tw.TweenCallback(Callable.From(node.QueueFree));
				}
				else node.QueueFree();
			}

			_nSegments = nSegs;
			_nPousses = empty;
			GD.Print($"[WorldView] {season} an {_year}, semaine {_weekInSeason}/13 : "
					 + $"{_plantNodes.Count} plantes (+{born} −{dead.Count}, "
					 + $"{grown} maj, {empty} sans segments).");

			// Vie macro (t6·B) : même diff doux que les plantes, délégué au
			// nœud MacroLife. Lecture TOLÉRANTE : un snapshot pré-0.2.3 n'a
			// pas le bloc — la vue affiche simplement un jardin sans bestioles.
			if (snap.ContainsKey("sprites"))
				_macroLife?.SetSprites(snap["sprites"].AsGodotDictionary(),
									   _origins, fade);

			// Heatmap (t6·C) : la grille affichée date de la semaine d'avant →
			// périmée. Si l'overlay est ON, _Process relancera UNE requête
			// `fields` dès que le pipe sera libre ; OFF, le flag dort.
			_fieldsStale = true;

			// Bloc joueur (volet B, lecture seule) → 2e ligne du HUD.
			if (snap.ContainsKey("player"))
			{
				var pl = snap["player"].AsGodotDictionary();
				_vigueur = pl["vigueur"].AsDouble();
				_vigueurMax = pl["vigueur_max"].AsDouble();
			}
			UpdateActionHud();

			// Fin de saison : retour AUTOMATIQUE en planification (boucle
			// hybride) + hook auto-save. Détection = le nom de saison change.
			// En mode Continu/Turbo, on n'arrête PAS (demande Nico F5 t4) —
			// le hook auto-save reste appelé à chaque passage, lui.
			if (_season != null && season != _season)
			{
				OnSeasonEnd();
				if (_simMode == SimMode.Saison)
				{
					GD.Print($"[WorldView] passage de saison : {season}, an {_year} "
							 + "— retour en planification.");
					_phase = Phase.Planification;
				}
				else
					GD.Print($"[WorldView] passage de saison : {season}, an {_year} "
							 + $"— mode {_simMode}, on enchaîne.");
			}
			_season = season;
			UpdateClock();
		}

		// -------------------------------------------------------------------
		// HUD PROVISOIRE — horloge + état, instrument de validation de la
		// tranche 3. Le HUD définitif (philo #5 : pas de chiffres en HUD
		// primaire) viendra au sprint UI ; celui-ci sautera.
		// -------------------------------------------------------------------

		private void BuildHud()
		{
			// CanvasLayer : se dessine en coordonnées ÉCRAN, ignore la Camera2D
			// (sinon le label serait projeté/zoomé avec le monde).
			var hud = new CanvasLayer { Name = "Hud" };
			_clockLabel = new Label { Position = new Vector2(16f, 10f) };
			// Gros + contour noir : lisible sur le fond gris pierre clair (le
			// label t3 v1 était blanc/petit → invisible). Overrides de thème =
			// le mécanisme Godot pour styler UN Control sans thème global.
			_clockLabel.AddThemeFontSizeOverride("font_size", 28);
			_clockLabel.AddThemeColorOverride("font_color", Colors.White);
			_clockLabel.AddThemeColorOverride("font_outline_color", Colors.Black);
			_clockLabel.AddThemeConstantOverride("outline_size", 8);
			// Témoin de build : visible dès _Ready, AVANT le premier snapshot.
			// Si ce texte n'apparaît pas, c'est que ce code ne tourne pas
			// (sync Nextcloud ou build) — pas un bug d'horloge.
			_clockLabel.Text = "t4 — chargement du monde…";
			hud.AddChild(_clockLabel);

			// 2e ligne (volet B) : Vigueur + geste sélectionné + dernier ACK/NAK
			// du serveur. Chiffres au HUD = assumé PROVISOIRE (philo #5 : le HUD
			// final passera par des indices visuels, ceci est l'instrument de
			// validation de la tranche).
			_actionLabel = new Label { Position = new Vector2(16f, 52f) };
			_actionLabel.AddThemeFontSizeOverride("font_size", 20);
			_actionLabel.AddThemeColorOverride("font_color", Colors.White);
			_actionLabel.AddThemeColorOverride("font_outline_color", Colors.Black);
			_actionLabel.AddThemeConstantOverride("outline_size", 6);
			hud.AddChild(_actionLabel);

			// Légende heatmap (t6·C2, demande Nico) : SOUS la ligne Vigueur,
			// AU-DESSUS du FPS. RichTextLabel pour les pavés colorés du
			// dégradé ; visible seulement quand le champ est affiché.
			_fieldLabel = new RichTextLabel
			{
				Position = new Vector2(16f, 80f),
				CustomMinimumSize = new Vector2(1300f, 30f),
				BbcodeEnabled = true, FitContent = true,
				ScrollActive = false, Visible = false,
				AutowrapMode = TextServer.AutowrapMode.Off,
			};
			_fieldLabel.AddThemeFontSizeOverride("normal_font_size", 16);
			_fieldLabel.AddThemeColorOverride("default_color", new Color(0.85f, 0.92f, 1f));
			_fieldLabel.AddThemeColorOverride("font_outline_color", Colors.Black);
			_fieldLabel.AddThemeConstantOverride("outline_size", 5);
			hud.AddChild(_fieldLabel);

			// Overlay de perfs (F4, volet C2) : sous la légende heatmap, caché
			// par défaut. Instrument debug (philo #5 : autorisé, hors HUD final).
			_perfLabel = new Label { Position = new Vector2(16f, 112f), Visible = false };
			_perfLabel.AddThemeFontSizeOverride("font_size", 16);
			_perfLabel.AddThemeColorOverride("font_color", new Color(1f, 1f, 0.8f));
			_perfLabel.AddThemeColorOverride("font_outline_color", Colors.Black);
			_perfLabel.AddThemeConstantOverride("outline_size", 5);
			hud.AddChild(_perfLabel);

			// Témoin de build (coin haut-droit) : LA réponse à « est-ce que je
			// fais tourner la bonne version ? ». Discret mais toujours visible.
			var build = new Label
			{
				Text = Build,
				Position = new Vector2(1920f - 16f, 10f),
				// Ancré à droite : on aligne la FIN du texte sur x=1904 en
				// décalant de sa largeur estimée — un Label n'a pas d'ancrage
				// droit sans Container ; à 14 px, ~7 px/caractère suffit.
			};
			build.Position -= new Vector2(Build.Length * 7f, 0f);
			build.AddThemeFontSizeOverride("font_size", 14);
			build.AddThemeColorOverride("font_color", new Color(1f, 1f, 1f, 0.65f));
			build.AddThemeColorOverride("font_outline_color", Colors.Black);
			build.AddThemeConstantOverride("outline_size", 4);
			hud.AddChild(build);

			// Légende des commandes (décision Nico 2026-06-10) : ce que le
			// joueur PEUT faire, coin bas-gauche, petite police. PROVISOIRE
			// (philo #5/#6 : pas de tutoriel imposé — la v1 aura la page
			// d'accueil pictogrammes ; ici c'est l'instrument de validation).
			// Position fixe : la résolution projet est 1920×1080.
			var legend = new Label { Position = new Vector2(16f, 1080f - 90f) };
			legend.AddThemeFontSizeOverride("font_size", 18);
			legend.AddThemeColorOverride("font_color", Colors.White);
			legend.AddThemeColorOverride("font_outline_color", Colors.Black);
			legend.AddThemeConstantOverride("outline_size", 6);
			legend.Text = "Espace lancer/pause · flèches déplacer"
				+ " · molette zoom · PageUp/PageDown pivoter\n"
				+ "M mode simu · F3 étiquettes · F4 perfs · H maison transparente · O ombres · I vie macro · F6 heatmap debug (Maj+F6 champ)\n"
				+ "gestes : 1 récolter · 2 déraciner · 3 écraser · 4 favoriser aux. · "
				+ "5 bêcher · 6 grelinette · 7 tailler (survolez la branche, Maj = latéral auto) · 8 manger"
				+ " — clic gauche = agir";
			hud.AddChild(legend);
			AddChild(hud);
			UpdateActionHud();
		}

		private void UpdateClock()
		{
			if (_clockLabel == null) return;
			string etat = _phase switch
			{
				Phase.Saison => "saison en cours",
				Phase.Pause  => "pause (Espace pour reprendre)",
				_            => "planification — Espace pour lancer la saison",
			};
			// Jauge intra-semaine : se remplit en SecondsPerWeek s, retombe au
			// départ du step, FIGE en pause — le « temps qui coule » est visible
			// même quand rien ne change à l'écran. ASCII pur (pas de glyphe
			// exotique : la police par défaut les remplacerait par des carrés).
			if (_simMode != SimMode.Saison)
				etat += _simMode == SimMode.Turbo ? " · TURBO" : " · continu";
			string jauge = "";
			if (_phase != Phase.Planification)
			{
				if (_simMode == SimMode.Turbo)
					jauge = "  [>>>>>>>>>>]";   // pas de cadence : plein régime
				else
				{
					float spw = DebugSecondsPerWeek > 0f ? DebugSecondsPerWeek : SecondsPerWeek;
					int n = Mathf.Clamp((int)(_timeAccum / spw * 10f), 0, 10);
					jauge = "  [" + new string('=', n) + new string('-', 10 - n) + "]";
				}
			}
			_clockLabel.Text =
				$"{_season} · an {_year} — semaine {_weekInSeason}/13{jauge}   {etat}";
		}

		// -------------------------------------------------------------------
		// ACTIONS JOUEUR (tranche 4, volet B) — touches 1..8 = geste, clic
		// gauche = exécuter. La vue RÉSOUT la désignation (plante/plot/tuile)
		// et TRANSMET ; Python valide, applique, répond ACK/NAK + snapshot.
		// -------------------------------------------------------------------

		private void SelectGeste(int idx)
		{
			_gesteIndex = idx;
			_lastActionMsg = "";
			GD.Print($"[WorldView] geste : {Gestes[idx].Nom} [{idx + 1}].");
			UpdateActionHud();
		}

		private void TryAction(Vector2 canvasPos, bool shift)
		{
			if (_world == null || _lastSnap == null) return;   // monde pas prêt
			if (_gesteIndex < 0)
			{
				_lastActionMsg = "aucun geste sélectionné (touches 1..8)";
				UpdateActionHud();
				FlashActionLabel();
				return;
			}

			var (verb, nom, kind) = Gestes[_gesteIndex];
			Vector2 w = ScreenToWorld(canvasPos);
			GDict target = null;
			var prms = new GDict();
			PlantRenderer node = null;

			switch (kind)
			{
				case 'p':   // plante la plus proche dans le rayon de tolérance
					// Taille (tranche 5, correctif t5·B) : la plante se résout
					// par LA BRANCHE sous la souris (toutes plantes, couronnes
					// débordantes comprises) ; sans branche sous le curseur,
					// repli sur le collet à 30 cm = comportement t4 inchangé.
					int segIdx = -1;
					if (verb == "tailler")
						node = FindSegmentGlobal(canvasPos, out segIdx);
					if (node == null)
						node = FindPlant(w, PickRadiusCm);
					if (node == null)
					{
						_lastActionMsg = $"{nom} : aucune plante à portée du clic";
						UpdateActionHud(); FlashActionLabel();
						return;
					}
					target = new GDict
					{
						["tile"] = node.GetMeta("tile"),
						["x_cm"] = node.GetMeta("lx"),
						["y_cm"] = node.GetMeta("ly"),
					};
					// params.cible reste TOUJOURS envoyé : repli serveur si
					// target.segment est absent (clic au pied).
					if (verb == "tailler")
					{
						prms["cible"] = shift ? "branche" : "apex";
						if (segIdx >= 0) target["segment"] = segIdx;
					}
					break;

				case 'q':   // plot (tile, r, c) sous le clic
				case 't':   // tuile sous le clic
					if (!FindPlot(w, out string tileId, out int r, out int c))
					{
						_lastActionMsg = $"{nom} : aucune tuile ici (chemin/maison)";
						UpdateActionHud(); FlashActionLabel();
						return;
					}
					target = new GDict { ["tile"] = tileId };
					if (kind == 'q') { target["r"] = r; target["c"] = c; }
					// La couture préparation/réaction (§3.1, déjà codée moteur) :
					// en phase Saison le geste est une RÉACTION → urgence (×1.5).
					// En Pause on réfléchit : temps figé = tarif planification.
					if (verb == "ecraser")
						prms["urgence"] = _phase == Phase.Saison;
					break;

				// '-' : grelinette, pas de cible.
			}

			// Pipe occupé (step, action ou fields en vol) → l'intention est
			// MÉMORISÉE (une seule, la dernière gagne) et partira dès que le
			// tube se libère — indispensable en Turbo où le pipe ne dort jamais.
			if (!PipeFree)
			{
				_queuedIntent = (verb, target, prms, node);
				GD.Print($"[WorldView] pipe occupé — intention {verb} mémorisée.");
				return;
			}
			LaunchAction(verb, target, prms, node);
		}

		private void LaunchAction(string verb, GDict target, GDict prms, PlantRenderer node)
		{
			GD.Print($"[WorldView] → action {verb} "
					 + (target != null ? Json.Stringify(target) : "(sans cible)")
					 + (prms != null && prms.Count > 0 ? $" params {Json.Stringify(prms)}" : "") + ".");
			_actionTargetNode = node;
			var prmsArg = prms != null && prms.Count > 0 ? prms : null;
			_pendingAction = Task.Run(() => _bridge.Action(verb, target, prmsArg));
		}

		/// <summary>Plante affichée la plus proche du point MONDE (cm), dans
		/// `radiusCm`, ou null. ~170 nœuds : recherche linéaire, pas de quadtree
		/// à inventer (leçon perf : mesurer avant d'optimiser).</summary>
		private PlantRenderer FindPlant(Vector2 w, float radiusCm)
		{
			PlantRenderer best = null;
			float bestD = radiusCm * radiusCm;
			foreach (var node in _plantNodes.Values)
			{
				float dx = (float)node.GetMeta("wx").AsDouble() - w.X;
				float dy = (float)node.GetMeta("wy").AsDouble() - w.Y;
				float d = dx * dx + dy * dy;
				if (d < bestD) { bestD = d; best = node; }
			}
			return best;
		}

		/// <summary>Tuile + plot contenant le point MONDE (cm). False si le
		/// point tombe entre les tuiles (chemins) ou sur la maison.</summary>
		private bool FindPlot(Vector2 w, out string tileId, out int r, out int c)
		{
			foreach (var tv in _world["tiles"].AsGodotArray())
			{
				var t = tv.AsGodotDictionary();
				float ox = (float)t["origin_x_cm"].AsDouble();
				float oy = (float)t["origin_y_cm"].AsDouble();
				int rows = t["rows"].AsInt32(), cols = t["cols"].AsInt32();
				if (w.X >= ox && w.X < ox + cols * PlotCm
					&& w.Y >= oy && w.Y < oy + rows * PlotCm)
				{
					tileId = t["id"].AsString();
					c = (int)((w.X - ox) / PlotCm);
					r = (int)((w.Y - oy) / PlotCm);
					return true;
				}
			}
			tileId = null; r = c = 0;
			return false;
		}

		// Tolérance du hit-test de segment en px CANVAS : 8 px ÉCRAN quel que
		// soit le palier de zoom (le canvas est multiplié par Zoom à l'écran).
		private float SegmentPickTolPx() =>
			SegmentPickPx / (_camera != null ? _camera.Zoom.X : 1f);

		/// <summary>
		/// LA branche sous la souris, toutes plantes confondues (correctif
		/// t5·B) : le segment le plus proche du curseur sous la tolérance,
		/// cherché chez TOUTES les plantes dont la portée (PickExtentCm,
		/// étalement + hauteur) atteint le point souris — plus de filtre par
		/// collet à 30 cm, qui excluait la couronne des arbres. Préfiltre
		/// monde au carré (pas de racine), puis hit-test exact par segment ;
		/// ~170 plantes dont une poignée passent le préfiltre : trivial.
		/// Survol ET clic passent ici : ce qui est surligné = ce qui part.
		/// </summary>
		private PlantRenderer FindSegmentGlobal(Vector2 canvasMouse, out int segIndex)
		{
			segIndex = -1;
			PlantRenderer best = null;
			float bestD = SegmentPickTolPx();
			Vector2 w = ScreenToWorld(canvasMouse);
			foreach (var node in _plantNodes.Values)
			{
				float dx = (float)node.GetMeta("wx").AsDouble() - w.X;
				float dy = (float)node.GetMeta("wy").AsDouble() - w.Y;
				float ext = node.PickExtentCm;
				if (dx * dx + dy * dy > ext * ext) continue;
				int seg = node.FindSegmentNear(canvasMouse, bestD, out float d);
				if (seg >= 0 && d < bestD) { bestD = d; best = node; segIndex = seg; }
			}
			return best;
		}

		// Surbrillance de la branche sous la souris en mode tailler (tranche
		// 5) : MÊME résolution que le clic (FindSegmentGlobal) — ce qui est
		// surligné est EXACTEMENT ce qui partira en target.segment. Appelée
		// chaque frame ; les setters HighlightSegment font early-out, le
		// redraw ne part qu'au changement.
		private void UpdateTailleHighlight()
		{
			PlantRenderer node = null;
			int seg = -1;
			if (_gesteIndex >= 0 && Gestes[_gesteIndex].Verb == "tailler"
				&& _plantNodes.Count > 0)
				node = FindSegmentGlobal(GetGlobalMousePosition(), out seg);
			if (_highlightNode != null && _highlightNode != node
				&& IsInstanceValid(_highlightNode))
				_highlightNode.HighlightSegment = -1;
			_highlightNode = node;
			if (node != null) node.HighlightSegment = seg;
		}

		// Étiquette au survol (demande Nico 2e F5 t4) : seule la plante la plus
		// proche de la souris montre la sienne. Premier consommateur du picking
		// ScreenToWorld — le clic réutilise exactement la même résolution.
		private void UpdateHoverTag()
		{
			if (_labelMode != LabelMode.Survol || _plantNodes.Count == 0) return;
			var best = FindPlant(ScreenToWorld(GetGlobalMousePosition()), HoverRadiusCm);
			foreach (var node in _plantNodes.Values)
			{
				var tag = node.GetNodeOrNull<Label>("Tag");
				if (tag != null) tag.Visible = node == best;
			}
		}

		private void UpdateActionHud()
		{
			if (_actionLabel == null) return;
			string vig = _vigueur < 0 ? "Vigueur —"
				: $"Vigueur {_vigueur:F0}/{_vigueurMax:F0}";
			string geste = _gesteIndex < 0 ? "aucun (1..8)"
				: $"{Gestes[_gesteIndex].Nom} [{_gesteIndex + 1}]";
			string msg = string.IsNullOrEmpty(_lastActionMsg) ? ""
				: $"   ·   {_lastActionMsg}";
			_actionLabel.Text = $"{vig} — geste : {geste}{msg}";
		}

		// Overlay de perfs (F4) — mesures côté VUE, le moteur n'est pas
		// instrumenté : tick complet (pipe+sim+parse — la vérité du joueur),
		// cadence réelle entre 2 semaines (→ jours simulés/seconde), volumes.
		private void UpdatePerf()
		{
			if (_perfLabel == null) return;
			string tick = _lastTickMs < 0 ? "—" : $"{_lastTickMs:F0} ms";
			string cad = _lastWeekGapSec <= 0 ? "—"
				: $"{_lastWeekGapSec:F1} s/sem ({7.0 / _lastWeekGapSec:F1} j/s)";
			_perfLabel.Text =
				$"FPS {Engine.GetFramesPerSecond():F0} · tick {tick} · cadence {cad}\n"
				+ $"plantes {_plantNodes.Count} (+{_nPousses} pousses) · "
				+ $"segments {_nSegments} · vie macro "
				+ (_macroLife == null ? "—"
					: !_macroLife.Visible ? "OFF"
					: CurrentZoom < 4f ? $"{_macroLife.Count} (LOD : zoomez ×4)"
					: _macroLife.Count.ToString()) + " · "
				+ $"ombres {(ShadowsOn ? "ON" : "OFF")} · "
				+ $"zoom ×{ZoomSteps[_zoomIndex]}";
		}

		// Refus métier → flash rouge de la 2e ligne (kickoff B·12 : pas de
		// popup ; le détail est en console).
		private void FlashActionLabel()
		{
			if (_actionLabel == null) return;
			_actionLabel.Modulate = new Color(1f, 0.35f, 0.35f);
			_actionLabel.CreateTween()
				.TweenProperty(_actionLabel, "modulate", Colors.White, 0.6f);
		}

		// -------------------------------------------------------------------
		// CAMÉRA — jouable depuis la tranche 4 (D35) : pan flèches, zoom
		// molette par paliers, rotation par quarts de tour (re-projection).
		// -------------------------------------------------------------------

		private void FrameCamera()
		{
			_camera = GetNodeOrNull<Camera2D>("Camera");
			if (_camera == null) return;
			// Palier initial = le plus proche du CameraZoom exporté (0.5 cadre
			// le monde entier) — _zoomIndex et Zoom ne divergent jamais.
			_zoomIndex = 0;
			for (int i = 1; i < ZoomSteps.Length; i++)
				if (Mathf.Abs(ZoomSteps[i] - CameraZoom)
					< Mathf.Abs(ZoomSteps[_zoomIndex] - CameraZoom))
					_zoomIndex = i;
			// Centre du monde (1000,1000) cm → écran ; remonté de l'équivalent
			// d'un demi-toit pour que la maison ne tasse pas le cadrage.
			_camera.Position = WorldToScreen(WorldCm / 2f, WorldCm / 2f)
				- new Vector2(0f, 100f);
			_camera.Zoom = Vector2.One * ZoomSteps[_zoomIndex];
			CurrentZoom = ZoomSteps[_zoomIndex];
			_camera.MakeCurrent();
		}

		private void UpdateCameraPan(float delta)
		{
			if (_camera == null) return;
			// Polling (Input.IsKeyPressed) et non événement : un MAINTIEN de
			// touche est un état continu, échantillonné chaque frame — comme
			// lire un GPIO dans la boucle plutôt que compter les IRQ de front.
			var dir = Vector2.Zero;
			if (Input.IsKeyPressed(Key.Left))  dir.X -= 1f;
			if (Input.IsKeyPressed(Key.Right)) dir.X += 1f;
			if (Input.IsKeyPressed(Key.Up))    dir.Y -= 1f;
			if (Input.IsKeyPressed(Key.Down))  dir.Y += 1f;
			if (dir == Vector2.Zero) return;
			// PanSpeedPx est en px ÉCRAN/s ; la Position caméra vit en canvas
			// → diviser par le zoom donne un ressenti identique à tout palier.
			_camera.Position = ClampToWorld(_camera.Position
				+ dir.Normalized() * (PanSpeedPx / _camera.Zoom.X) * delta);
		}

		// Borne la caméra à la boîte englobante du monde projeté + marge 10 %
		// (kickoff A·1 : on ne se perd pas dans le gris). Les 4 coins du carré
		// 0..2000 cm projettent x ∈ [−1560, 1560], y ∈ [0, 1560] — IDENTIQUE à
		// toute orientation : le quart de tour remappe le carré sur lui-même.
		private static Vector2 ClampToWorld(Vector2 pos)
		{
			float halfW = WorldCm * PxPerCmX;        // 1560 px
			float h     = WorldCm * PxPerCmY * 2f;   // 1560 px
			float margin = 0.1f * h;
			pos.X = Mathf.Clamp(pos.X, -halfW - margin, halfW + margin);
			pos.Y = Mathf.Clamp(pos.Y, -margin, h + margin);
			return pos;
		}

		private void StepZoom(int dir)
		{
			if (_camera == null) return;
			int idx = Mathf.Clamp(_zoomIndex + dir, 0, ZoomSteps.Length - 1);
			if (idx == _zoomIndex) return;   // déjà au palier extrême
			float oldZ = ZoomSteps[_zoomIndex];
			float newZ = ZoomSteps[idx];
			_zoomIndex = idx;
			// Zoom centré souris (kickoff A·2) : le point canvas sous le
			// curseur doit y RESTER. GetGlobalMousePosition rend la souris déjà
			// en canvas (pan/zoom défaits par Godot) ; il suffit de glisser la
			// caméra vers/depuis ce point au ratio des zooms :
			// m = cam + d/oldZ = cam' + d/newZ  ⇒  cam' = m + (cam−m)·oldZ/newZ.
			Vector2 mouse = GetGlobalMousePosition();
			_camera.Position = ClampToWorld(
				mouse + (_camera.Position - mouse) * (oldZ / newZ));
			_camera.Zoom = Vector2.One * newZ;
			CurrentZoom = newZ;
			GD.Print($"[WorldView] zoom ×{newZ}.");
		}

		private void RotateView(int dir)
		{
			if (_lastSnap == null) return;   // monde pas encore construit
			_orientation = (_orientation + dir + 4) % 4;
			GD.Print($"[WorldView] rotation vue → orientation {_orientation} "
					 + $"({_orientation * 90}° anti-horaire).");
			RebuildWorld();
		}

		// Reconstruit sol + maison + plantes avec l'orientation courante : tout
		// ce qui a été posé via WorldToScreen a une Position FIGÉE, la
		// re-projection passe donc par une reconstruction (kickoff, pédagogie 2).
		// 1188 polygones + ~170 plantes = instantané, pas d'optimisation.
		// SANS fondu : même semaine vue d'un autre coin, pas des naissances.
		// La caméra ne bouge pas (défaut sobre) : la boîte du monde projeté est
		// la même à toute orientation — suivre le MÊME point monde pendant la
		// rotation (ScreenToWorld existe depuis le volet B) reste une finition
		// pour le sprint UI si le besoin se confirme à l'usage.
		private void RebuildWorld()
		{
			_ground.QueueFree();
			_objects.QueueFree();   // emporte maison, plantes et fondus en cours
			_plantNodes.Clear();

			BuildGround(_world);
			_objects = new Node2D { Name = "Objects", ZIndex = 10, YSortEnabled = true };
			AddChild(_objects);
			BuildHouse(_world);
			ApplySnapshot(_lastSnap, fade: false);
			// La heatmap se re-projette au _Draw : un redraw suffit (t6·C).
			_fieldOverlay?.QueueRedraw();
		}
	}
}
