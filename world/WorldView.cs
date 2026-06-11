// SYMBIOSE — WorldView.cs
// LA VUE DU MONDE (sprint Intégration, tranches 2-4 — Option B : Python =
// moteur, Godot = vue). Au lancement : démarre le pont (SimBridge), initialise
// le monde COMPLET 20×20 m (init config="full" → 8 tuiles SECTORS + maison),
// avance quelques semaines pour que les branches poussent, puis DESSINE le
// snapshot. Depuis la tranche 3, le monde VIT : boucle hybride Planification
// (temps figé) ↔ Saison (temps réel, 1 semaine = SecondsPerWeek s), bascule à
// la touche Espace. Depuis la tranche 4, la caméra est JOUABLE (D35) : pan aux
// flèches, zoom molette par paliers, rotation de la vue par quarts de tour.
// Aucune logique écologique ici : Godot est « bête », il projette et affiche.
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
		private Node2D _house;     // pour le mode transparent (touche H)
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
		private bool _labelsVisible = true;   // étiquettes espèce·stade (F3)
		private bool _houseGhost;             // maison transparente (H)
		private float _timeAccum;                  // secondes réelles écoulées
		private Task<GDict> _pendingStep;          // LA requête en vol (ou null)
		// Plantes affichées, indexées par clé stable (tile|species|x|y) — base
		// du diff naissance/mort entre deux snapshots.
		private readonly Dictionary<string, PlantRenderer> _plantNodes = new();
		private Dictionary<string, Vector2> _origins;   // origin_cm par tuile
		private int _plantSeq;                     // noms de nœuds uniques
		// Horloge du dernier snapshot appliqué (pour le Label + fin de saison).
		private string _season;
		private int _year, _weekInSeason;
		private Label _clockLabel;

		// -------------------------------------------------------------------
		// CYCLE DE VIE
		// -------------------------------------------------------------------

		public override void _Ready()
		{
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

			BuildHud();
			ApplySnapshot(snap, fade: false);   // monde initial : pas de fondu

			FrameCamera();
			// Le process Python reste OUVERT, au repos en Planification : c'est
			// le mapping de la boucle hybride. Fermé à _ExitTree.
		}

		public override void _ExitTree()
		{
			// Un step encore en vol occupe le pipe : on l'attend avant d'écrire
			// "quit" (sinon deux écritures concurrentes — règle (b) de l'en-tête).
			try { _pendingStep?.Wait(2000); } catch { /* moteur déjà mort : Quit gère */ }
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
				switch (k.Keycode)
				{
					case Key.Space:    TogglePhase();  break;
					// Monde anti-horaire = la CAMÉRA orbite vers la droite
					// (ressenti validé par Nico au 1er F5 t4).
					case Key.Pageup:   RotateView(+1); break;
					case Key.Pagedown: RotateView(-1); break;
					case Key.M:        CycleSimMode();    break;
					case Key.F3:       ToggleLabels();    break;
					case Key.H:        ToggleHouseGhost(); break;
				}
			}
			// Molette = paliers de zoom (décision Nico 2026-06-10 : molette,
			// pas de touches).
			else if (ev is InputEventMouseButton mb && mb.Pressed)
			{
				if (mb.ButtonIndex == MouseButton.WheelUp)   StepZoom(+1);
				if (mb.ButtonIndex == MouseButton.WheelDown) StepZoom(-1);
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
			_labelsVisible = !_labelsVisible;
			foreach (var node in _plantNodes.Values)
			{
				var tag = node.GetNodeOrNull<Label>("Tag");
				if (tag != null) tag.Visible = _labelsVisible;
			}
			GD.Print($"[WorldView] F3 → étiquettes : {(_labelsVisible ? "ON" : "OFF")}.");
		}

		private void ToggleHouseGhost()
		{
			_houseGhost = !_houseGhost;
			ApplyHouseGhost();
			GD.Print($"[WorldView] H → maison {(_houseGhost ? "transparente" : "opaque")}.");
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

			// 1) Consommer un step terminé — TOUJOURS, même en pause : la
			//    semaine était déjà engagée côté moteur, son résultat est dû.
			if (_pendingStep != null && _pendingStep.IsCompleted)
			{
				var step = _pendingStep;
				_pendingStep = null;
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

			// 2) Accumulateur temps réel (seulement quand la saison court).
			if (_phase != Phase.Saison) return;
			_timeAccum += (float)delta;
			float spw = DebugSecondsPerWeek > 0f ? DebugSecondsPerWeek : SecondsPerWeek;
			if (_simMode == SimMode.Turbo) spw = 0f;   // step dès que le pont répond
			if (_timeAccum >= spw && _pendingStep == null)
			{
				_timeAccum = 0f;
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

			// Ombre portée PLACEHOLDER : soleil au sud → ombre vers le NORD.
			// Rectangle (ombre des murs) + pointe (ombre du faîte), longueur ≈
			// hauteur. Posée dans _ground : sous tous les objets, par-dessus
			// les plots (ordre d'ajout), et reconstruite avec la rotation.
			_ground.AddChild(new Polygon2D
			{
				Polygon = new[]
				{
					WorldToScreen(x0, y0), WorldToScreen(x1, y0),
					WorldToScreen(x1, y0 - wallCm),
					WorldToScreen((x0 + x1) / 2f, y0 - heightCm),
					WorldToScreen(x0, y0 - wallCm),
				},
				Color = OmbreColor,
			});

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
			var tag = new Label { Name = "Tag", Visible = _labelsVisible };
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

			int born = 0, grown = 0, empty = 0;
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
				var renderer = new PlantRenderer
				{
					Position = WorldToScreen(o.X + (float)p["x_cm"].AsDouble(),
											 o.Y + (float)p["y_cm"].AsDouble()),
					Name = $"{p["tile"].AsString()}_{p["species"].AsString()}_{_plantSeq++}",
				};
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

			GD.Print($"[WorldView] {season} an {_year}, semaine {_weekInSeason}/13 : "
					 + $"{_plantNodes.Count} plantes (+{born} −{dead.Count}, "
					 + $"{grown} maj, {empty} sans segments).");

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

			// Légende des commandes (décision Nico 2026-06-10) : ce que le
			// joueur PEUT faire, coin bas-gauche, petite police. PROVISOIRE
			// (philo #5/#6 : pas de tutoriel imposé — la v1 aura la page
			// d'accueil pictogrammes ; ici c'est l'instrument de validation).
			// Le volet B y ajoutera les gestes 1..8. Position fixe : la
			// résolution projet est 1920×1080.
			var legend = new Label { Position = new Vector2(16f, 1080f - 66f) };
			legend.AddThemeFontSizeOverride("font_size", 18);
			legend.AddThemeColorOverride("font_color", Colors.White);
			legend.AddThemeColorOverride("font_outline_color", Colors.Black);
			legend.AddThemeConstantOverride("outline_size", 6);
			legend.Text = "Espace lancer/pause · flèches déplacer"
				+ " · molette zoom · PageUp/PageDown pivoter\n"
				+ "M mode simu · F3 étiquettes · H maison transparente";
			hud.AddChild(legend);
			AddChild(hud);
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
		// la même à toute orientation — recentrer sur le MÊME point monde
		// demanderait ScreenToWorld, qui arrive au volet B (picking).
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
		}
	}
}
