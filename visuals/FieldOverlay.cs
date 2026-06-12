// SYMBIOSE — FieldOverlay.cs
// Heatmap des champs écologiques (tranche 6·C — le « mode debug champs
// écologiques » de la conception, étiqueté debug, philo #5 : autorisé hors
// HUD primaire). Touche F6 dans WorldView ; ce nœud ne fait que DESSINER la
// dernière grille reçue du serveur (commande `fields`) — zéro requête ici,
// la machine maître/esclave vit dans WorldView.
//
// 📖 Pédagogie — pourquoi des losanges en _Draw et pas une ImageTexture
// (le kickoff §9 laissait le choix) : une texture rows×cols en Nearest
// étirée sur la tuile ferait moins de primitives, MAIS il faudrait gérer
// Image/ImageTexture/Transform2D oblique (le losange iso est l'image affine
// du rectangle monde) et la re-projeter à chaque rotation D35. Le _Draw
// batch fait tout ça gratuitement : on re-projette par WorldToScreen au
// moment du dessin, et le redraw est RARE (1×/semaine quand la grille
// arrive, toggle, rotation) — 1 188 DrawColoredPolygon une fois par minute
// n'est pas un coût (BuildGround en pose autant en permanence). C'est le
// même patron qu'un seul CanvasItem que MacroLife — et l'inverse de son
// problème : lui redessine souvent peu de points, ici rarement tout le sol.

using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class FieldOverlay : Node2D
	{
		// Semi-transparent : la heatmap se lit PAR-DESSUS le terrain sans
		// l'effacer (l'œil garde les plantes et la maison pour se repérer).
		private const float Alpha = 0.7f;

		/// <summary>Nom du champ affiché (HUD) ; null si aucune grille.</summary>
		public string FieldName { get; private set; }
		/// <summary>Bornes de la normalisation (HUD min/max).</summary>
		public float Min { get; private set; }
		public float Max { get; private set; }

		// Dernière réponse `fields` du serveur (grilles par tuile) + origins.
		private GDict _tiles;
		private System.Collections.Generic.Dictionary<string, Vector2> _origins;

		/// <summary>
		/// Nouvelle grille reçue : mémorise, calcule min/max (normalisation
		/// AUTO par champ — un microbiome 0..3 et une humidité 0..1 se lisent
		/// pareil), redessine. La projection se fait au _Draw : la rotation
		/// D35 n'a besoin que d'un QueueRedraw.
		/// </summary>
		public void SetGrid(string fieldName, GDict tiles,
							System.Collections.Generic.Dictionary<string, Vector2> origins)
		{
			FieldName = fieldName;
			_tiles = tiles;
			_origins = origins;
			float mn = float.MaxValue, mx = float.MinValue;
			foreach (var kv in tiles)
			{
				var vals = kv.Value.AsGodotDictionary()["values"].AsGodotArray();
				foreach (var v in vals)
				{
					float f = (float)v.AsDouble();
					if (f < mn) mn = f;
					if (f > mx) mx = f;
				}
			}
			Min = mn; Max = mx;
			QueueRedraw();
		}

		public override void _Draw()
		{
			if (!Visible || _tiles == null) return;
			// Le losange d'un plot, en offsets écran constants (la projection
			// iso d'un carré de 50 cm — mêmes cotes que MakeLozenge du sol).
			Vector2 n = new(0f, -WorldView.TileHPx / 2f);
			Vector2 e = new(WorldView.TileWPx / 2f, 0f);
			Vector2 s = new(0f, WorldView.TileHPx / 2f);
			Vector2 o = new(-WorldView.TileWPx / 2f, 0f);
			float span = Max - Min;
			foreach (var kv in _tiles)
			{
				if (!_origins.TryGetValue(kv.Key.AsString(), out Vector2 org))
					continue;
				var t = kv.Value.AsGodotDictionary();
				int rows = t["rows"].AsInt32(), cols = t["cols"].AsInt32();
				var vals = t["values"].AsGodotArray();
				for (int r = 0; r < rows; r++)
					for (int c = 0; c < cols; c++)
					{
						// row-major : l'index recompose (r, c) — l'ordre du
						// serveur (boucle rows puis cols), pas un 2e contrat.
						float v = (float)vals[r * cols + c].AsDouble();
						float tt = span > 1e-6f ? (v - Min) / span : 0.5f;
						// Dégradé bleu → rouge par la teinte HSV (240° → 0°) :
						// froid = pauvre, chaud = riche — le code couleur météo.
						Color col = Color.FromHsv((1f - tt) * 2f / 3f, 0.85f, 0.95f, Alpha);
						Vector2 ctr = WorldView.WorldToScreen(
							org.X + (c + 0.5f) * WorldView.PlotCm,
							org.Y + (r + 0.5f) * WorldView.PlotCm);
						DrawColoredPolygon(
							new[] { ctr + n, ctr + e, ctr + s, ctr + o }, col);
					}
			}
		}
	}
}
