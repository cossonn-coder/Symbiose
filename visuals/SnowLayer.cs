// SYMBIOSE — SnowLayer.cs (tronçon ⑨, vue pure)
// LE MANTEAU NEIGEUX au sol, PAR TUILE : un voile blanc semi-transparent couvrant
// l'emprise d'une tuile, dont l'opacité suit `temperature[tile].snow ∈ [0,1]`
// (état scalaire calculé au tronçon ⑦, exposé au pont au ⑧, protocole 0.5.0).
// LECTURE SEULE — golden NEUTRE : Godot ne fait que teinter le sol en blanc.
//
// 📖 MÊME patron que LitterLayer : un seul Node2D en coordonnées MONDE (ZIndex
// bas, SOUS les plantes qui dépassent de la neige) qui REPROJETTE tout au _Draw
// via WorldToScreen → la rotation de vue (D35) est gratuite (les 4 coins de la
// tuile re-projetés tournent avec le monde). Le manteau ne s'anime pas (matière
// inerte) : on ne QueueRedraw qu'à l'arrivée d'un snapshot. RebuildWorld (quart
// de tour) ré-appelle ApplySnapshot → SetSnow → QueueRedraw, donc le voile suit.
//
// Choix « un grand losange par tuile » (et non un par plot comme la litière) :
// `snow` est UN scalaire par tuile → l'emprise entière a la même opacité ; un
// seul quadrilatère (les 4 coins projetés) suffit, ~8 polygones pour le monde.

using Godot;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class SnowLayer : Node2D
	{
		// En-deçà, le manteau est invisible : on ne dessine rien (cas nominal hors
		// hiver enneigé — pas de voile fantôme au printemps).
		private const float SnowEps = 0.02f;
		// Opacité max du voile (à snow = 1) : on lit « le sol blanchit », le sol
		// reste deviné dessous — pas un aplat opaque.
		private const float AlphaMax = 0.6f;

		// Une tuile enneigée : origine MONDE (cm) + dimensions (plots) + opacité.
		// On garde les coins en MONDE et on projette au _Draw (rotation gratuite).
		private struct TileSnow
		{
			public float Ox, Oy;
			public int Rows, Cols;
			public float Alpha;
		}

		private readonly List<TileSnow> _tiles = new();

		/// <summary>
		/// Applique le bloc `temperature` du snapshot (0.5.0). Pour chaque tuile :
		/// `snow` (scalaire) → opacité ; les dimensions rows×cols sont DÉDUITES de
		/// la grille `t_sol` (pas besoin de cacher rows/cols à part). `origins` =
		/// origin_cm par tuile (le même cache que plantes/litière).
		/// Lecture tolérante : champs absents → tuile ignorée, jamais de crash.
		/// </summary>
		public void SetSnow(GDict temperature, Dictionary<string, Vector2> origins)
		{
			_tiles.Clear();
			foreach (var tileKv in temperature)
			{
				if (!origins.TryGetValue(tileKv.Key.AsString(), out Vector2 o))
					continue;   // tuile inconnue du init
				var td = tileKv.Value.AsGodotDictionary();
				float snow = td.ContainsKey("snow") ? (float)td["snow"].AsDouble() : 0f;
				if (snow <= SnowEps) continue;   // pas de manteau → rien

				// Dimensions de la tuile = forme de la grille t_sol (rows × cols).
				if (!td.ContainsKey("t_sol")) continue;
				var tsol = td["t_sol"].AsGodotArray();
				int rows = tsol.Count;
				int cols = rows > 0 ? tsol[0].AsGodotArray().Count : 0;
				if (rows == 0 || cols == 0) continue;

				_tiles.Add(new TileSnow
				{
					Ox = o.X, Oy = o.Y, Rows = rows, Cols = cols,
					Alpha = Mathf.Min(snow * AlphaMax, AlphaMax),
				});
			}
			QueueRedraw();
		}

		public override void _Draw()
		{
			foreach (var t in _tiles)
			{
				float x1 = t.Ox + t.Cols * WorldView.PlotCm;
				float y1 = t.Oy + t.Rows * WorldView.PlotCm;
				// Les 4 coins de l'emprise, projetés → un quadrilatère iso (le
				// losange de la tuile). WorldToScreen applique l'orientation D35.
				var quad = new[]
				{
					WorldView.WorldToScreen(t.Ox, t.Oy),
					WorldView.WorldToScreen(x1, t.Oy),
					WorldView.WorldToScreen(x1, y1),
					WorldView.WorldToScreen(t.Ox, y1),
				};
				DrawColoredPolygon(quad, new Color(1f, 1f, 1f, t.Alpha));
			}
		}
	}
}
