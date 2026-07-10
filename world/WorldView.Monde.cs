// SYMBIOSE — WorldView.Monde.cs (partial de WorldView, SS⑥ refactor global)
// Les PLACEHOLDERS PROCÉDURAUX du décor : le SOL (un losange Polygon2D par
// plot, coloré par type de sol) et la MAISON (empreinte iso + 2 façades + toit
// pyramidal). Décision Nico 2026-06-10 : les PNG tuiles actuels sont opaques
// et de tailles incohérentes — inutilisables pour une grille jointive ; les
// sprites définitifs reviendront ré-exportés (D34/D4). Les couleurs reprennent
// la teinte DOMINANTE mesurée sur chaque PNG.

using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Palette placeholder — teintes centralisées dans Palette16 (T1),
		// dominantes MESURÉES sur les PNG tuiles.
		private static readonly Color TerreColor  = Palette16.SolTerre;
		private static readonly Color ArgileColor = Palette16.SolArgile;
		private static readonly Color SableColor  = Palette16.SolSable;
		private static readonly Color SolInconnu  = Palette16.SolInconnu;
		// Chemins ENHERBÉS (T4 RENDU AMBIANCE) : le FOND de la fenêtre fait office
		// de bandes entre tuiles ; il bascule du gris pierre au vert gazon (le jardin
		// est ourlé d'herbe, pas de dalles), gratuit et suffisant.
		private static readonly Color FondChemin  = Palette16.GazonChemin;
		// 📖 La MAISON (état, géométrie, ombre portée) est extraite dans le partial
		// WorldView.Maison.cs (T3 RENDU AMBIANCE) — Monde.cs ne garde que le SOL.

		// Cache des textures de sol cuites (T2) : clé = (type de sol, orientation
		// D35). Rempli paresseusement par GroundTexture et réutilisé par tous les
		// plots ⇒ ≤ 4 sols × 4 orient = 16 cuissons au total sur toute la session,
		// jamais une par plot ni par rotation. Persiste à travers RebuildWorld
		// (champ d'instance, non re-créé par la reconstruction du sol).
		private readonly System.Collections.Generic.Dictionary<(string, int), ImageTexture>
			_soilTexCache = new();

		// -------------------------------------------------------------------
		// SOL — un losange placeholder par plot
		// -------------------------------------------------------------------

		private void BuildGround(GDict world)
		{
			_ground = new Node2D { Name = "Ground", ZIndex = 0 };
			AddWorld(_ground);
			var ground = _ground;
			ResetRelief();   // D57 ② : le sol est reconstruit (rotation) → repartir à vide

			int nPlots = 0;
			foreach (var tv in world["tiles"].AsGodotArray())
			{
				var t = tv.AsGodotDictionary();
				string tileId = t["id"].AsString();   // pour lire l'épaisseur au plot
				float ox = (float)t["origin_x_cm"].AsDouble();
				float oy = (float)t["origin_y_cm"].AsDouble();
				int rows = t["rows"].AsInt32();
				int cols = t["cols"].AsInt32();
				string soilName = t["soil"].AsString();
				// Texture cuite (relief sud + grain), PARTAGÉE par tous les plots
				// de ce type sous l'orientation courante (T2). Cuisson paresseuse
				// et CACHÉE : ≤ 4 sols × 4 orient = 16 textures au total, jamais
				// recuites à chaque rotation (cf. GroundTexture).
				ImageTexture tex = GroundTexture(soilName);

				for (int r = 0; r < rows; r++)
					for (int c = 0; c < cols; c++)
					{
						// Centre du plot en cm monde → centre du sprite écran.
						float cx = ox + (c + 0.5f) * PlotCm;
						float cy = oy + (r + 0.5f) * PlotCm;
						Vector2 screenCenter = WorldToScreen(cx, cy);
						// Sprite2D plutôt que Polygon2D texturé (T2) : centrage
						// automatique sur la Position, pas d'UV à mapper sur le
						// losange — le plus direct pour poser la texture cuite.
						var sp = new Sprite2D
						{
							Texture = tex,
							TextureFilter = CanvasItem.TextureFilterEnum.Nearest,
							Position = screenCenter,
							// Damier subtil (±5 %) appliqué par plot via Modulate :
							// la texture reste partagée (pixel art sobre, sans
							// bordures). L'effet d'avant (Darkened 0.05) conservé.
							Modulate = (r + c) % 2 == 0
								? Colors.White
								: new Color(0.95f, 0.95f, 0.95f, 1f),
						};
						// D57 ② : le FLANC du relief (ajouté à `ground` ici) doit
						// passer SOUS le dessus → on l'enregistre AVANT d'ajouter sp.
						RegisterReliefPlot(ground, soilName, tileId, r, c, screenCenter, sp);
						ground.AddChild(sp);
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

		// Texture de sol cuite (relief sud + grain) pour un type de sol sous
		// l'orientation D35 COURANTE (_orientation). Cachée par (sol, orient) :
		// la 1ʳᵉ demande d'un couple cuit l'image, les suivantes la réutilisent —
		// la rotation rappelle BuildGround mais ne recuit que les couples encore
		// absents du cache. La direction « sud » du relief dépend de l'orientation
		// (cf. SolTexture.SouthDir) : le bombé suit le sud du jardin, pas l'écran.
		private ImageTexture GroundTexture(string soil)
		{
			var key = (soil, _orientation);
			if (!_soilTexCache.TryGetValue(key, out var tex))
			{
				tex = SolTexture.BakeLozenge(SoilColor(soil), _orientation);
				_soilTexCache[key] = tex;
			}
			return tex;
		}

		// Losange iso 2:1 d'un plot, centré sur (0,0) : ±TileWPx/2 px en x,
		// ±TileHPx/2 en y (sommets nord/est/sud/ouest).
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
	}
}
