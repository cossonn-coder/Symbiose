// SYMBIOSE — LightField.cs
// Champ lumière : projection directionnelle d'ombres (pas de diffusion).
// Extrait de GridField.cs au refactor SS⑦.

using System.Collections.Generic;

namespace Symbiose
{
	// ---------------------------------------------------------------------------
	// LIGHTFIELD — projection directionnelle (pas de diffusion)
	// ---------------------------------------------------------------------------

	public class LightField : GridField
	{
		// Longueur d'ombre par strate
		private static readonly Dictionary<string, int> ShadowLength = new()
		{
			{ "haute",     3 },
			{ "moyenne",   1 },
			{ "basse",     0 },
			{ "sol",       0 },
			{ "grimpante", 1 },
		};

		// Densité d'ombre par saison
		private static readonly Dictionary<string, float> ShadowDensity = new()
		{
			{ "printemps", 0.6f },
			{ "ete",       0.4f },
			{ "automne",   0.65f },
			{ "hiver",     0.85f },
		};

		// Vecteurs d'ombre (colonne paire, colonne impaire)
		private static readonly Dictionary<string, ((int dr, int dc) pair, (int dr, int dc) odd)>
		ShadowVector = new()
		{
			{ "printemps", ((-1,-1), (-1, 0)) },
			{ "ete",       ((-1, 0), (-1, 1)) },
			{ "automne",   ((-1, 0), (-1, 1)) },
			{ "hiver",     ((-1, 0), (-1, 0)) },
		};

		public LightField(int rows, int cols) : base(rows, cols, 1f, 1f) { }

		public void Reset()
		{
			for (int r = 0; r < Rows; r++)
				for (int c = 0; c < Cols; c++)
					_data[r, c] = 1f;
		}

		private List<(int r, int c)> ShadowPlots(
			int originR, int originC, string saison, int length)
		{
			var plots = new List<(int, int)>();
			if (!ShadowVector.TryGetValue(saison, out var vec)) return plots;

			int r = originR, c = originC;
			for (int i = 0; i < length; i++)
			{
				var (dr, dc) = (c % 2 == 0) ? vec.pair : vec.odd;
				r += dr; c += dc;
				if (r >= 0 && r < Rows && c >= 0 && c < Cols)
					plots.Add((r, c));
				else
					break;
			}
			return plots;
		}

		public List<(int r, int c)> CastShadow(
			int originR, int originC, string strate, string saison)
		{
			if (!ShadowLength.TryGetValue(strate, out int length) || length == 0)
				return new List<(int, int)>();

			float density = ShadowDensity.GetValueOrDefault(saison, 0.6f);
			var plots = ShadowPlots(originR, originC, saison, length);
			foreach (var (r, c) in plots)
				_data[r, c] *= (1f - density);
			return plots;
		}

		// Recalcule le champ lumière complet pour un tick
		public void Compute(List<PlantInstance> plants, string saison)
		{
			Reset();
			foreach (var plant in plants)
			{
				if (!plant.IsAlive) continue;
				if (plant.CurrentStage < 2) continue; // adulte/mature seulement
				string strate = plant.Stage.Strate;
				if (!ShadowLength.TryGetValue(strate, out int len) || len == 0) continue;
				CastShadow(plant.Position.Row, plant.Position.Col, strate, saison);
			}
		}
	}
}
