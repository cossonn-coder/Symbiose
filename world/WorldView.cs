// SYMBIOSE — WorldView.cs
// LA VUE DU MONDE (sprint Intégration, tranche 2 — Option B : Python = moteur,
// Godot = vue). Au lancement : démarre le pont (SimBridge), initialise le monde
// COMPLET 20×20 m (init config="full" → 8 tuiles SECTORS + maison), avance
// quelques semaines pour que les branches poussent, puis DESSINE le snapshot.
// Aucune logique écologique ici : Godot est « bête », il projette et affiche.
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

		/// <summary>
		/// LA projection monde → écran (kickoff t2 : une seule, partout).
		/// x augmente vers l'est (droite-bas du losange), y vers le sud.
		/// </summary>
		public static Vector2 WorldToScreen(float xCm, float yCm) =>
			new Vector2((xCm - yCm) * PxPerCmX, (xCm + yCm) * PxPerCmY);

		// -------------------------------------------------------------------
		// RÉGLAGES (exportés : ajustables dans l'inspecteur sans recompiler)
		// -------------------------------------------------------------------
		[Export] public int Seed = 42;
		[Export] public string Config = "full";
		// Semaines simulées au lancement, pour voir des branches (semaine 13 =
		// fin de printemps). Mesuré : ~1.8 s pour 12 ticks du monde complet —
		// acceptable en t2 ; la progression temps réel arrive en tranche 3.
		[Export] public int WarmupWeeks = 12;
		// Zoom caméra : 0.5 cadre le monde entier (~3120×2050 px) en 1920×1080.
		// Les paliers entiers ×4/×8/×16/×32 = hors tranche (caméra de cadrage).
		[Export] public float CameraZoom = 0.5f;

		// Palette placeholder — teintes dominantes MESURÉES sur les PNG tuiles.
		private static readonly Color TerreColor  = new Color("967a64");
		private static readonly Color ArgileColor = new Color("cd7434");
		private static readonly Color SableColor  = new Color("f1e9bb");
		private static readonly Color SolInconnu  = new Color("777777");
		// Chemins en pierre : pas dessinés en t2 — le FOND de la fenêtre fait
		// office de bandes entre tuiles (gris pierre), gratuit et suffisant.
		private static readonly Color FondPierre  = new Color("8d8881");
		// Maison placeholder : gris calcaire, 3 faces nuancées (toit éclairé).
		private static readonly Color ToitColor   = new Color("cfc8b8");
		private static readonly Color FacadeSud   = new Color("b5ac99");
		private static readonly Color FacadeEst   = new Color("978f7d");

		private SimBridge _bridge;
		private Node2D _objects;   // maison + plantes, YSort (cf. en-tête)

		// -------------------------------------------------------------------
		// CYCLE DE VIE
		// -------------------------------------------------------------------

		public override void _Ready()
		{
			RenderingServer.SetDefaultClearColor(FondPierre);

			_bridge = new SimBridge();
			if (!_bridge.Start())
				return;

			var world = _bridge.Init(Seed, Config);
			if (world == null) { _bridge.Quit(); return; }

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
			SpawnPlants(world, snap);

			FrameCamera();
			// Le process Python reste OUVERT : les tranches 3-4 (saison animée,
			// actions joueur) continueront de lui parler. Fermé à _ExitTree.
		}

		public override void _ExitTree() => _bridge?.Quit();

		// -------------------------------------------------------------------
		// SOL — un losange placeholder par plot
		// -------------------------------------------------------------------

		private void BuildGround(GDict world)
		{
			var ground = new Node2D { Name = "Ground", ZIndex = 0 };
			AddChild(ground);

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
			GD.Print($"[WorldView] sol : {nPlots} plots placeholder dessinés.");
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

			// Ancrage YSort = coin (x1,y1), le point au sol le plus PROCHE de la
			// caméra : tout l'édifice est « derrière » ce point.
			Vector2 anchor = WorldToScreen(x1, y1);
			var house = new Node2D { Name = "House", Position = anchor };

			// Les 4 coins au sol, en coordonnées LOCALES au nœud (relatifs à
			// l'ancrage), puis leurs jumeaux « toit » décalés de hPx vers le haut.
			Vector2 nw = WorldToScreen(x0, y0) - anchor;
			Vector2 ne = WorldToScreen(x1, y0) - anchor;
			Vector2 se = Vector2.Zero;                       // = l'ancrage
			Vector2 sw = WorldToScreen(x0, y1) - anchor;
			Vector2 up = new Vector2(0f, -hPx);

			// Faces visibles avec une caméra iso « depuis le sud-est » : la
			// façade EST (entre ne et se) et la façade SUD (entre se et sw).
			house.AddChild(new Polygon2D
			{ Polygon = new[] { ne, se, se + up, ne + up }, Color = FacadeEst });
			house.AddChild(new Polygon2D
			{ Polygon = new[] { se, sw, sw + up, se + up }, Color = FacadeSud });
			house.AddChild(new Polygon2D
			{ Polygon = new[] { nw + up, ne + up, se + up, sw + up }, Color = ToitColor });

			_objects.AddChild(house);
			GD.Print($"[WorldView] maison placeholder : empreinte "
					 + $"[{x0},{y0}]→[{x1},{y1}] cm, h={heightCm} cm.");
		}

		// -------------------------------------------------------------------
		// PLANTES — un PlantRenderer par plante du snapshot, posé au collet.
		// Position monde = origin de SA tuile + position locale (x_cm, y_cm).
		// -------------------------------------------------------------------

		private void SpawnPlants(GDict world, GDict snap)
		{
			// Index origin par tuile (le snapshot donne des positions LOCALES).
			var origins = new Dictionary<string, Vector2>();
			foreach (var tv in world["tiles"].AsGodotArray())
			{
				var t = tv.AsGodotDictionary();
				origins[t["id"].AsString()] = new Vector2(
					(float)t["origin_x_cm"].AsDouble(),
					(float)t["origin_y_cm"].AsDouble());
			}

			int shown = 0, empty = 0;
			foreach (var pv in snap["plants"].AsGodotArray())
			{
				var p = pv.AsGodotDictionary();
				var structure = StructureLoader.FromSnapshot(p);
				if (structure.Segments.Count == 0)
				{
					empty++;   // germination sans bois : rien à dessiner encore
					continue;
				}

				Vector2 o = origins[p["tile"].AsString()];
				var renderer = new PlantRenderer
				{
					Position = WorldToScreen(o.X + (float)p["x_cm"].AsDouble(),
											 o.Y + (float)p["y_cm"].AsDouble()),
					Name = $"{p["tile"].AsString()}_{p["species"].AsString()}_{shown}",
				};
				_objects.AddChild(renderer);
				renderer.SetStructure(structure);
				shown++;
			}
			GD.Print($"[WorldView] plantes : {shown} affichées, "
					 + $"{empty} sans segments (ignorées).");
		}

		// -------------------------------------------------------------------
		// CAMÉRA — simple cadrage du monde entier (paliers de zoom = plus tard)
		// -------------------------------------------------------------------

		private void FrameCamera()
		{
			var cam = GetNodeOrNull<Camera2D>("Camera");
			if (cam == null) return;
			// Centre du monde (1000,1000) cm → écran ; remonté de l'équivalent
			// d'un demi-toit pour que la maison ne tasse pas le cadrage.
			cam.Position = WorldToScreen(1000f, 1000f) - new Vector2(0f, 100f);
			cam.Zoom = Vector2.One * CameraZoom;
			cam.MakeCurrent();
		}
	}
}
