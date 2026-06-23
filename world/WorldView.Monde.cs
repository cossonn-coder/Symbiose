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

		private Node2D _house;     // pour le mode transparent (touche H)
		// Ombre maison ANIMÉE (volet C) : le polygone est recalculé quand le
		// soleil bouge — paramètres gardés en champs pour ne pas relire le GDict.
		private Polygon2D _houseShadow;
		private float _hx0, _hy0, _hx1, _hy1, _hWallCm, _hHeightCm;

		// -------------------------------------------------------------------
		// SOL — un losange placeholder par plot
		// -------------------------------------------------------------------

		private void BuildGround(GDict world)
		{
			_ground = new Node2D { Name = "Ground", ZIndex = 0 };
			AddWorld(_ground);
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
	}
}
