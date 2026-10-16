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
// 📂 Classe étalée en `partial` (SS⑥ refactor global, 2026-06-16) : une même
// classe WorldView répartie par CONCEPT sur plusieurs fichiers (le compilateur
// les recolle ; la scène WorldView.tscn pointe la même classe). Ce fichier-ci
// tient le cœur : cycle de vie + boucle hybride. Les autres tranches :
//   · WorldView.Projection.cs — WorldToScreen / ScreenToWorld (la projection)
//   · WorldView.Controls.cs   — entrées clavier/souris + bascules d'état
//   · WorldView.Monde.cs      — placeholders sol + maison
//   · WorldView.Soleil.cs     — ombre solaire animée
//   · WorldView.Snapshot.cs   — diff des plantes (ApplySnapshot)
//   · WorldView.Actions.cs    — gestes joueur + picking
//   · WorldView.Hud.cs        — HUD provisoire + overlay heatmap
//   · WorldView.Camera.cs     — caméra D35 + RebuildWorld
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
// UNE transformation : WorldToScreen(x_cm, y_cm), écrite UNE fois (cf.
// WorldView.Projection.cs) et utilisée pour les 3 familles d'objets (plots,
// maison, collets des plantes). C'est la leçon du bug D2 : deux projections
// « presque pareilles » (grille 96×48 codée vs sprites 78×57 réels) ne
// coïncident jamais.
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
		public const string Build = "Jardinier automate F5 (A brancher · Maj+A objectif démo) — pont 0.5.30 — 2026-07-18";

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
		// de patience. Remis à 0 à la clôture de la tranche 6 (2026-06-12) :
		// le rythme design (60 s/semaine) redevient le défaut. Pour valider
		// vite en debug : remettre 3 ici ou via l'inspecteur (c'est un Export).
		[Export] public float DebugSecondsPerWeek = 1f;
		// Durées des fondus d'apparition (naissance) / disparition (mort).
		[Export] public float FadeInSec = 0.6f;
		[Export] public float FadeOutSec = 0.9f;

		private SimBridge _bridge;
		// SubViewport basse-réso (SS① pixel-art) : TOUT le contenu MONDE (sol,
		// objets, plantes, faune, overlays, caméra) y vit, dessiné à 480×270 puis
		// agrandi ×4 en Nearest par le SubViewportContainer → grain pixel SNES
		// unifié. Les CanvasLayer (HUD, sélecteur, ambiance météo) restent, eux,
		// dans le viewport PRINCIPAL (plein 1920×1080) : le HUD de debug doit
		// rester lisible pour la validation F5 (l'UI rejoindra la grille au sprint
		// UI). AddWorld() est le SEUL point d'ajout de contenu monde.
		private SubViewport _worldVp;
		private Node2D _objects;   // maison + plantes, YSort (cf. en-tête)
		private Node2D _ground;    // sol — reconstruit à chaque rotation
		// Vie macro (t6·B) : UN nœud pour tous les points (cf. MacroLife.cs).
		// ZIndex 5 = entre sol (0) et objets (10) — les bestioles vivent au ras
		// du sol, sous les plantes. Enfant direct de WorldView : il survit à
		// RebuildWorld (il se re-projette seul à chaque dessin d'animation).
		private MacroLife _macroLife;
		// Eau de surface + marécage (hydrologie ⑧) : UN nœud pour flaques + voile de
		// tourbe (cf. PuddleLayer.cs). ZIndex 2 = au ras du sol, sous la macro/plantes.
		// Recalé sur le relief via la vue. Survit à RebuildWorld (se re-projette seul).
		private PuddleLayer _puddleLayer;
		// Butineurs (arc pollinisation) : agents fleur-en-fleur, distincts du nuage
		// MacroLife. ZIndex 11 = AU-DESSUS des plantes/objets (10) — l'abeille se
		// pose sur la corolle, on doit la voir par-dessus. Survit à RebuildWorld.
		private ForagerLayer _foragerLayer;
		// Carpophores (mycélium ④/⑥) : champignons VISIBLES échantillonnés du champ
		// `mycelium` (perception pure). ZIndex 4 = au ras du sol, sous la macro (5)
		// et les plantes (10) — ils poussent au sol. Survit à RebuildWorld.
		private CarpophoreLayer _carpophoreLayer;
		// Décor d'ambiance (T4 RENDU AMBIANCE) : le backdrop cosmétique AUTOUR du
		// jardin (forêt/rivière/falaise/prairie par seed). ZIndex négatif = DERRIÈRE
		// le sol (0). Enfant direct du SubViewport (AddWorld) → il SURVIT à
		// RebuildWorld ; on le re-Build à la rotation pour re-projeter au nouvel
		// orient. Node2D inerte, sans input → hors picking (le jardin garde ses clics).
		private DecorLayer _decorLayer;
		// Index plantes-par-NOM-FR (Phacélie…) → positions MONDE (cm), reconstruit
		// à chaque snapshot. Sert les fleurs de saut des butineurs (le `target` est
		// le nom FR, qui matche `name`, pas `species`/anglais).
		private readonly Dictionary<string, List<Vector2>> _plantsByName = new();

		private GDict _world;      // réponse de init (tuiles + maison) — pour RebuildWorld
		private GDict _lastSnap;   // dernier snapshot appliqué — pour RebuildWorld
		// Faux tant que l'écran de sélection (⑤) n'a pas lancé StartSimulation :
		// le monde (couches, _objects, _origins…) n'existe pas encore, _Process et
		// _UnhandledInput court-circuitent pour ne pas déréférencer du vide.
		private bool _started;

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
		private float _timeAccum;                  // secondes réelles écoulées
		private Task<GDict> _pendingStep;          // step en vol (ou null)

		// Le pipe est maître/esclave 1↔1 : libre = AUCUNE requête en vol
		// (step, action ou fields). LA condition de toute écriture sur le tube.
		private bool PipeFree =>
			_pendingStep == null && _pendingAction == null && _pendingFields == null;
		private Dictionary<string, Vector2> _origins;   // origin_cm par tuile

		// -------------------------------------------------------------------
		// CYCLE DE VIE
		// -------------------------------------------------------------------

		public override void _Ready()
		{
			GD.Print($"[WorldView] build : {Build}");
			// Le viewport PRINCIPAL s'efface en vert gazon ; le SubViewport monde
			// est en transparent_bg → ce vert transparaît entre les tuiles (les
			// chemins enherbés, gratuits, T4). Cf. WorldView.tscn.
			RenderingServer.SetDefaultClearColor(FondChemin);
			// Le SubViewport basse-réso et sa caméra (déclarés dans la scène).
			_worldVp = GetNode<SubViewport>("WorldViewport/World");
			// 📖 Pédagogie — forcer la taille du conteneur À LA MAIN : un
			// SubViewportContainer est un Control, mais son PARENT ici est WorldView
			// (un Node2D, pas un Control). Les ancrages « plein cadre » d'un Control
			// ne valent que sous un parent Control/Viewport → sinon il retombe à sa
			// taille MINIMALE (on a mesuré SubViewport = 2×2, monde invisible). On le
			// dimensionne donc explicitement à la fenêtre, et on suit ses
			// redimensionnements. stretch_shrink=4 → le SubViewport fait fenêtre/4
			// = 480×270 (la résolution interne pixel-art).
			var container = GetNode<SubViewportContainer>("WorldViewport");
			container.Size = GetViewport().GetVisibleRect().Size;
			GetViewport().SizeChanged += () =>
				container.Size = GetViewport().GetVisibleRect().Size;
			// Palette SNES ~32 couleurs + tramage Bayer sur TOUT le monde affiché
			// (jardin vivant T1, F11 bascule) ; curseur + losange de survol.
			PaletteSnes.Appliquer(container);
			InitCurseur();
			// Pré-cuisson des plantes (jardin vivant T2) : la file qui recuit au plus
			// quelques plantes par frame, seulement près de l'écran (BakeQueue.cs).
			AddChild(new BakeQueue { Name = "BakeQueue" });
			// Onde de vent (jardin vivant T3) : choisit chaque frame la pose de
			// flexion des plantes près de l'écran (WindWave.cs).
			AddChild(new WindWave { Name = "WindWave" });
			// Variante météo des plantes (jardin vivant T4) : canicule, pluie qui
			// sèche en quelques secondes de jeu (MeteoPlantes.cs).
			AddChild(new MeteoPlantes { Name = "MeteoPlantes" });
			// Champ STATIQUE (partagé avec PlantRenderer via WorldToScreen) :
			// toujours repartir « nord en haut » à l'ouverture de la scène.
			_orientation = 0;

			_bridge = new SimBridge();
			if (!_bridge.Start())
				return;

			// Sélecteur de monde (sprint bancs d'essai ⑤) : au lieu de lancer
			// directement la `config` de l'Export, on présente un menu — Nico
			// choisit full / smoke / un banc d'essai À L'ÉCRAN, sans éditer
			// d'argument. Le moteur ne démarre (StartSimulation) qu'au clic
			// « Lancer ». Le pont EST déjà ouvert ici (Start ci-dessus) : le menu
			// peut demander la liste des bancs au serveur (list_bancs) AVANT init.
			// Tout le reste de la machine (_Process, _UnhandledInput) reste gardé
			// par `_started` tant qu'on n'a pas lancé. Voir WorldView.Selecteur.cs.
			// Mode capture VM (T0 jardin vivant) : monde imposé par argument, pas
			// de menu. Inactif sans `--capture-banc=` (cf. WorldView.Capture.cs).
			if (CaptureActive) { PreparerCapture(); StartSimulation(CaptureBanc); return; }
			BuildSelecteur();
		}

		// Ajoute un nœud de contenu MONDE dans le SubViewport basse-réso (et non
		// directement sous WorldView, qui vit dans le viewport principal). Les
		// CanvasLayer (HUD, sélecteur, ambiance météo) NE passent PAS par ici.
		private void AddWorld(Node n) => _worldVp.AddChild(n);

		// La souris en coordonnées CANVAS du monde (espace de la caméra du
		// SubViewport), équivalent de l'ancien GetGlobalMousePosition() d'avant le
		// SubViewport. 📖 Pédagogie — le picking traverse maintenant DEUX échelles :
		//  1) fenêtre → px internes du SubViewport : la souris est en px écran
		//     (1920×1080) ; le SubViewport ne fait que 480×270 (stretch_shrink=4),
		//     d'où le facteur Size/ContainerSize (= 1/4) ;
		//  2) px internes → canvas monde : on défait la transform de la caméra
		//     (zoom + pan) via GetCanvasTransform().AffineInverse().
		// ScreenToWorld (projection) finit le travail canvas → cm monde. Une seule
		// fonction, cinq appelants (leçon D2 : jamais deux conversions divergentes).
		// (T3 : _Process lit la souris UNE fois par frame via LireSourisFrame,
		// WorldView.Survol.cs ; cette lecture directe reste pour clic et zoom.)
		private Vector2 WorldMouseCanvas() => SourisVersCanvas(
			GetViewport().GetMousePosition(), _worldVp.GetCanvasTransform());

		// px fenêtre → canvas monde, la caméra donnée (partagé avec le cache T3).
		private Vector2 SourisVersCanvas(Vector2 px, Transform2D camera)
		{
			var container = _worldVp.GetParent<SubViewportContainer>();
			Vector2 scale = (Vector2)_worldVp.Size / container.Size;
			Vector2 internalPx = (px - container.GlobalPosition) * scale;
			return camera.AffineInverse() * internalPx;
		}

		// Démarrage EFFECTIF de la simulation, déclenché par le sélecteur (⑤) au
		// choix d'un monde. Extrait de l'ancien _Ready (sans changer la séquence) :
		// init → warmup → construction des couches → 1er snapshot → caméra.
		private void StartSimulation(string config)
		{
			// Options d'init du panneau Paramètres (T2) : mémorisées avant « Lancer »,
			// transmises au montage du monde (encyclopédie de départ + carnet anticipé).
			var world = _bridge.Init(Seed, config, _encycloDemarrage, _carnetAnticipe);
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

			// Décor AVANT le sol : ZIndex -5 le pose derrière tout, mais on l'ajoute
			// tôt pour qu'il existe au 1er dessin. Build depuis le SEED du terrain.
			_decorLayer = new DecorLayer { Name = "Decor", ZIndex = -5 };
			AddWorld(_decorLayer);
			_decorLayer.Build(Seed);

			BuildGround(world);

			_objects = new Node2D { Name = "Objects", ZIndex = 10, YSortEnabled = true };
			AddWorld(_objects);
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

			// Tapis de COUVERTURE au sol (luxuriance ⑥, D65) — ZIndex 0 (juste
			// au ras du sol), SOUS la litière (1), la macro (5) et les plantes (10) :
			// le couvre-sol tapisse la terre, tout se dessine par-dessus. Enfant
			// direct de WorldView (survit à RebuildWorld, il se re-projette seul).
			_couvertureLayer = new CouvertureLayer { Name = "Couverture", ZIndex = 0 };
			AddWorld(_couvertureLayer);

			// Halo de SOL PELÉ de l'allélopathie (⑥) — ZIndex 0 comme la couverture
			// (au ras du sol), son pendant NÉGATIF : là où le champ `allelopathie` est
			// chargé, la terre reste nue. Enfant direct de WorldView (survit à
			// RebuildWorld, se re-projette seul). Lit le bloc `allelopathie` (0.5.29).
			_allelopathieLayer = new AllelopathieLayer { Name = "Allelopathie", ZIndex = 0 };
			AddWorld(_allelopathieLayer);

			BuildLitterLayer();   // litière au sol (③·B) — ZIndex 1, sous la macro

			// Tapis de MULCH au sol (équilibre invasion ⑧, D69) — ZIndex 1 comme la
			// litière (au-dessus du sol/couverture, sous la macro/plantes). Ajouté
			// APRÈS la litière → le mulch DÉLIBÉRÉ (geste) se pose par-dessus la
			// nécromasse spontanée. Lit le bloc `paillage` (0.5.20).
			_mulchLayer = new MulchLayer { Name = "Mulch", ZIndex = 1 };
			AddWorld(_mulchLayer);

			// Eau de surface + marécage (hydrologie ⑧) — ZIndex 2 : le marais
			// « noircit » le sol par-dessus la couverture/litière, la flaque brille
			// au-dessus, le tout SOUS la macro (5) et les plantes (10). Enfant direct
			// de WorldView (survit à RebuildWorld). Recalé sur le relief via la vue
			// (ReliefRiseAtPlot) → il faut lui passer `this`. Lit `eau_surface`/`marais`.
			_puddleLayer = new PuddleLayer { Name = "Puddle", ZIndex = 2 };
			_puddleLayer.Init(this);
			AddWorld(_puddleLayer);

			_macroLife = new MacroLife { Name = "MacroLife", ZIndex = 5 };
			AddWorld(_macroLife);

			_foragerLayer = new ForagerLayer { Name = "ForagerLayer", ZIndex = 11 };
			AddWorld(_foragerLayer);

			// Carpophores (mycélium ④/⑥) : champignons au ras du sol (ZIndex 4,
			// sous la macro 5 et les plantes 10). Lit le bloc `carpophores` (0.5.8).
			_carpophoreLayer = new CarpophoreLayer { Name = "Carpophores", ZIndex = 4 };
			AddWorld(_carpophoreLayer);

			_fieldOverlay = new FieldOverlay
			{
				Name = "FieldOverlay", ZIndex = 3, Visible = false,
			};
			AddWorld(_fieldOverlay);

			BuildMeteoLayers();   // ambiance écran + manteau neigeux (⑨) — avant le HUD
			BuildCielView();      // placeholders couvertures (monde) — avant le HUD

			BuildHud();
			BuildSkyPanel();      // encart « état du ciel » (CanvasLayer, APRÈS le HUD)
			// (T3) Plus de panneau automate à construire d'avance : l'onglet Automate
			// naît à la demande (touche A) dans le conteneur de consultation.
			BuildPalette();       // palette de gestes en colonne gauche (④, D11)
			BuildPlantLabels();   // couche d'étiquettes NETTE (hors SubViewport, SS①)
			ApplySnapshot(snap, fade: false);   // monde initial : pas de fondu

			FrameCamera();
			AppliquerCapture();   // no-op hors mode capture (WorldView.Capture.cs)
			// Monde construit → on débloque la boucle (_Process) et les entrées
			// (_UnhandledInput), gardées par `_started` pendant l'écran de sélection.
			_started = true;
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
			LibererCurseur();   // rend le curseur système, libère ses textures (T1)
		}

		// -------------------------------------------------------------------
		// BOUCLE HYBRIDE — horloge temps réel (tranche 3). Les entrées qui la
		// pilotent vivent dans WorldView.Controls.cs.
		// -------------------------------------------------------------------

		public override void _Process(double delta)
		{
			// Écran de sélection (⑤) : rien à animer tant que le monde n'est pas
			// construit (StartSimulation pose _started).
			if (!_started) return;

			// 0) Caméra : pan aux flèches — actif dans TOUTES les phases (la
			//    caméra n'interagit jamais avec la machine à états).
			UpdateCameraPan((float)delta);
			// 0a) Souris lue UNE fois + clé de survol (T3, WorldView.Survol.cs) :
			//     les étapes 0b-0d·bis ci-dessous ne recalculent que si elle a changé.
			LireSourisFrame();
			// 0b) Étiquettes des plantes (nettes, hors SubViewport) — reprojetées
			//     chaque frame selon le mode (Aucune/Survol/Toutes). Cf.
			//     WorldView.Etiquettes.cs.
			UpdatePlantLabels();
			// 0b·bis) Observation par SURVOL (0.5.12) : regarder une plante = l'apprendre
			//     (fiche encyclopédie N1). Dédupliqué par espèce. Cf. Observation.cs.
			ObserveHoveredPlant();
			// 0b·ter) Observation de la VIE MACRO au survol (D60 ②) : animal (nuage
			//     ou butineur) / carpophore → champignon. Gaté au zoom ≥ ×4 (visible).
			ObserveHoveredMacroLife();
			// 0b'') Étiquette de survol d'un CONTENEUR (substrat/volume + état
			//       qualitatif du mini-sol, ⑥c) — même couche nette, mots seuls.
			UpdateContainerLabel();
			// 0b') Surbrillance de la branche sous la souris (mode tailler, t5).
			//      Chaque frame aussi, mais le redraw ne part qu'au CHANGEMENT.
			UpdateTailleHighlight();
			// 0b'·bis) Curseur vivant + losange du plot survolé (jardin vivant T1).
			UpdateCurseur();
			// 0c) Soleil (volet C) : la jauge intra-semaine est l'heure du jour.
			//     Early-out interne si le soleil a bougé de moins de 2°.
			UpdateSun();
			// 0d) Overlay de perfs (F4) — toutes phases.
			MesurerPerfRendu();     // draw calls/temps de frame (PerfMesure.cs, coût nul)
			if (_perfVisible) UpdatePerf();
			// 0d·bis) Survol gènes debug (diversité fondatrice ③, touche G) : affiche
			//     les gènes de rythme de la plante pointée. Early-out interne si OFF.
			UpdateGenesHover();

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
				ApplySnapshotEtale(step.Result);   // 7 familles sur plusieurs frames
			}
			// 1·bis) Une famille (ou une tranche de plantes) de la semaine en cours
			//        d'application — jamais tout le jardin dans la même frame.
			AvancerEtalement();

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

			// 1c-bis) Rejeu de macro (⑤) : dépile le sous-geste suivant AU MÊME
			//     point cliqué dès que le pipe est libre (chaque geste paie sa
			//     Vigueur, philo #1). No-op si aucune macro n'est en cours de rejeu.
			DrainMacro();

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
					// Mode instrument (t6·C3) : si la grille AFFICHÉE est
					// une espèce, ses points MacroLife se resserrent sur
					// leur ancre (un nom non-espèce est sans effet là-bas).
					if (_macroLife != null)
						_macroLife.FocusGuild = _fieldOverlay.FieldName;
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
			// 2a) Piqûre temps réel (⑦ §J) : réaction au curseur pilotée par
			//     l'état moteur (alarme + densité abeille). Coût nul hors foyer.
			TickPiqure((float)delta);
			_timeAccum += (float)delta;
			float spw = DebugSecondsPerWeek > 0f ? DebugSecondsPerWeek : SecondsPerWeek;
			if (_simMode == SimMode.Turbo) spw = 0f;   // step dès que le pont répond
			// Le step ne part que si le PIPE est libre : ni step, ni action,
			// ni fields en vol (maître/esclave 1↔1 — une requête d'instrument
			// retarde la semaine d'une frame ou deux, jamais elle ne corrompt
			// le tube).
			if (_timeAccum >= spw && PipeFree && _etale == null)
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
		private void OnSeasonEnd()
		{
			// Le pollen déposé sur les fleurs s'accumule PAR SAISON (décision Nico) :
			// on repart d'une ardoise vierge à chaque bascule de saison.
			_foragerLayer?.ClearPollen();
		}
	}
}
