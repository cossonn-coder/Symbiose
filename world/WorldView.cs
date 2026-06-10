// SYMBIOSE — WorldView.cs
// LA VUE DU MONDE (sprint Intégration, tranches 2-3 — Option B : Python =
// moteur, Godot = vue). Au lancement : démarre le pont (SimBridge), initialise
// le monde COMPLET 20×20 m (init config="full" → 8 tuiles SECTORS + maison),
// avance quelques semaines pour que les branches poussent, puis DESSINE le
// snapshot. Depuis la tranche 3, le monde VIT : boucle hybride Planification
// (temps figé) ↔ Saison (temps réel, 1 semaine = SecondsPerWeek s), bascule à
// la touche Espace. Aucune logique écologique ici : Godot est « bête », il
// projette et affiche.
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
		// Maison placeholder : gris calcaire, 3 faces nuancées (toit éclairé).
		private static readonly Color ToitColor   = new Color("cfc8b8");
		private static readonly Color FacadeSud   = new Color("b5ac99");
		private static readonly Color FacadeEst   = new Color("978f7d");

		private SimBridge _bridge;
		private Node2D _objects;   // maison + plantes, YSort (cf. en-tête)

		// --- Boucle hybride (tranche 3) -------------------------------------
		// Planification = temps figé (défaut), Saison = temps réel, Pause =
		// saison suspendue. Espace fait Planification→Saison→Pause→Saison…
		private enum Phase { Planification, Saison, Pause }
		private Phase _phase = Phase.Planification;
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
			// Espace = lancer la saison / pause / reprise. Les vrais boutons UI
			// viendront au sprint UI ; le clavier suffit pour valider la boucle.
			if (ev is InputEventKey k && k.Pressed && !k.Echo && k.Keycode == Key.Space)
				TogglePhase();
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

		public override void _Process(double delta)
		{
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

		private void ApplySnapshot(GDict snap, bool fade = true)
		{
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
			if (_season != null && season != _season)
			{
				GD.Print($"[WorldView] passage de saison : {season}, an {_year} "
						 + "— retour en planification.");
				OnSeasonEnd();
				_phase = Phase.Planification;
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
			_clockLabel.Text = "t3 — chargement du monde…";
			hud.AddChild(_clockLabel);
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
			string jauge = "";
			if (_phase != Phase.Planification)
			{
				float spw = DebugSecondsPerWeek > 0f ? DebugSecondsPerWeek : SecondsPerWeek;
				int n = Mathf.Clamp((int)(_timeAccum / spw * 10f), 0, 10);
				jauge = "  [" + new string('=', n) + new string('-', 10 - n) + "]";
			}
			_clockLabel.Text =
				$"{_season} · an {_year} — semaine {_weekInSeason}/13{jauge}   {etat}";
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
