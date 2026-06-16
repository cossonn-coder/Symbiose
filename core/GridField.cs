// SYMBIOSE — GridField.cs
// Grille 2D de floats avec voisinage hexagonal et diffusion isotrope.
// Équivalent C# de GridField (fields.py). LightField et EcoFields, jadis dans
// ce même fichier, sont désormais dans LightField.cs / EcoFields.cs (SS⑦).

using System;
using System.Collections.Generic;
using System.Text;

namespace Symbiose
{
	// ---------------------------------------------------------------------------
	// GRIDFIELD — grille 2D de floats
	// ---------------------------------------------------------------------------

	public class GridField
	{
		public readonly int   Rows;
		public readonly int   Cols;
		public readonly float MaxVal;

		protected float[,] _data;

		public GridField(int rows, int cols, float initial = 0f, float maxVal = 3f)
		{
			Rows   = rows;
			Cols   = cols;
			MaxVal = maxVal;
			_data  = new float[rows, cols];
			Fill(initial);
		}

		// --- Accès de base ---

		public float Get(int r, int c) => _data[r, c];

		public void Set(int r, int c, float v)
		{
			_data[r, c] = Math.Clamp(v, 0f, MaxVal);
		}

		public void Add(int r, int c, float delta)
		{
			Set(r, c, _data[r, c] + delta);
		}

		public float AtPlot(int r, int c)
		{
			if (r >= 0 && r < Rows && c >= 0 && c < Cols)
				return _data[r, c];
			return 0f;
		}

		public void Fill(float value)
		{
			for (int r = 0; r < Rows; r++)
				for (int c = 0; c < Cols; c++)
					_data[r, c] = Math.Clamp(value, 0f, MaxVal);
		}

		// --- Statistiques ---

		public float Total()
		{
			float sum = 0f;
			for (int r = 0; r < Rows; r++)
				for (int c = 0; c < Cols; c++)
					sum += _data[r, c];
			return sum;
		}

		public float Average() => Total() / (Rows * Cols);

		// --- Voisinage hexagonal (grille quinconce) ---

		public List<(int r, int c)> HexNeighbors(int r, int c)
		{
			// Décalage selon parité de la ligne (même logique que fields.py)
			(int dr, int dc)[] deltas = (r % 2 == 0)
				? new[] { (-1,-1),(-1,0),(0,-1),(0,1),(1,-1),(1,0) }
				: new[] { (-1, 0),(-1,1),(0,-1),(0,1),(1, 0),(1,1) };

			var result = new List<(int, int)>();
			foreach (var (dr, dc) in deltas)
			{
				int nr = r + dr, nc = c + dc;
				if (nr >= 0 && nr < Rows && nc >= 0 && nc < Cols)
					result.Add((nr, nc));
			}
			return result;
		}

		// --- Diffusion isotrope (double buffer) ---
		// Identique à GridField.diffuse() en Python.
		// inertia=1.0 → pas de diffusion / inertia=0.0 → moyenne pure

		public void Diffuse(float inertia = 0.7f)
		{
			// Copie de sécurité (double buffer)
			float[,] old = (float[,])_data.Clone();

			for (int r = 0; r < Rows; r++)
			{
				for (int c = 0; c < Cols; c++)
				{
					var nb = HexNeighbors(r, c);
					float avg = 0f;
					if (nb.Count > 0)
					{
						foreach (var (nr, nc) in nb)
							avg += old[nr, nc];
						avg /= nb.Count;
					}
					else
					{
						avg = old[r, c];
					}
					_data[r, c] = Math.Clamp(
						old[r, c] * inertia + avg * (1f - inertia),
						0f, MaxVal
					);
				}
			}
		}

		// --- Debug ASCII ---

		public string AsciiMap(int precision = 2)
		{
			var sb = new StringBuilder();
			for (int r = 0; r < Rows; r++)
			{
				if (r % 2 == 1) sb.Append("  ");
				for (int c = 0; c < Cols; c++)
				{
					sb.Append(_data[r, c].ToString($"F{precision}"));
					if (c < Cols - 1) sb.Append(' ');
				}
				sb.AppendLine();
			}
			return sb.ToString();
		}

		public override string ToString() =>
			$"GridField({Rows}×{Cols}) avg={Average():F3}";
	}
}
