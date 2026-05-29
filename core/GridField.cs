// SYMBIOSE — GridField.cs
// Équivalent C# de GridField + EcoFields (fields.py)
// Grille 2D de floats avec voisinage hexagonal et diffusion isotrope.

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

	// ---------------------------------------------------------------------------
	// ECOFIELDS — conteneur complet des champs écologiques d'une tuile
	// ---------------------------------------------------------------------------

	public class EcoFields
	{
		public readonly string TileId;
		public readonly int    Rows;
		public readonly int    Cols;

		// Champs principaux
		public GridField  Humidite;
		public GridField  Fertilite;
		public GridField  Microbiome;
		public LightField Lumiere;

		// Mémoire du sol
		public GridField SoilMemory;
		public GridField SoilMemoryFast;
		public GridField SoilMemoryDeep;

		// OM tri-compartiment (v4)
		public GridField OmFresh;
		public GridField OmActive;
		public GridField OmStable;

		// Perturbation
		public GridField Disturbance;

		// Pression pathogène scalaire par tuile [0–1]
		public float PathogenPressure = 0f;

		// Constantes hydrologiques
		public const float BaseRain         = 0.015f;
		public const float RainVegFeedback  = 0.020f;
		public const float RainMicroPulse   = 0.30f;
		public const float Evaporation      = 0.997f;
		public const float Drainage         = 0.993f;
		public const float SoilRetention    = 0.010f;

		// Constantes OM
		public const float OmFreshToActive  = 0.15f;
		public const float OmActiveToStable = 0.02f;
		public const float OmActiveToFert   = 0.012f;
		public const float OmFreshCo2Loss   = 0.995f;
		public const float OmActiveCo2Loss  = 0.998f;
		public const float LeachingLoss     = 0.999f;

		// Inertie diffusion
		public const float HumidityInertia  = 0.55f;
		public const float FertilityInertia = 0.85f;
		public const float MicrobeInertia   = 0.92f;

		public EcoFields(string tileId, int rows, int cols)
		{
			TileId = tileId;
			Rows   = rows;
			Cols   = cols;

			Humidite       = new GridField(rows, cols, 0f, 3f);
			Fertilite      = new GridField(rows, cols, 0f, 3f);
			Microbiome     = new GridField(rows, cols, 0f, 3f);
			Lumiere        = new LightField(rows, cols);
			SoilMemory     = new GridField(rows, cols, 0f, 1f);
			SoilMemoryFast = new GridField(rows, cols, 0f, 1f);
			SoilMemoryDeep = new GridField(rows, cols, 0f, 1f);
			OmFresh        = new GridField(rows, cols, 0f, 8f);
			OmActive       = new GridField(rows, cols, 0f, 5f);
			OmStable       = new GridField(rows, cols, 0f, 15f);
			Disturbance    = new GridField(rows, cols, 0.05f, 1f);
		}

		// --- Initialisation ---

		public void InitValues(float humidite, float fertilite, float microbiome)
		{
			Humidite.Fill(humidite);
			Fertilite.Fill(fertilite);
			Microbiome.Fill(microbiome);
		}

		// --- Densité végétale (pour rain feedback) ---

		public float VegetationDensity(List<PlantInstance> plants)
		{
			if (plants == null || plants.Count == 0) return 0f;
			var occupied = new HashSet<(int, int)>();
			foreach (var p in plants)
			{
				if (!p.IsAlive || p.CurrentStage < 1) continue;
				occupied.Add(p.Position);
				foreach (var rp in p.RootPlots)
					occupied.Add(rp);
			}
			return (float)occupied.Count / (Rows * Cols);
		}

		// --- Tick hydrologie ---

		public void TickHydrology(List<PlantInstance> plants = null)
		{
			float vegDensity   = plants != null ? VegetationDensity(plants) : 0f;
			float rainFeedback = vegDensity * RainVegFeedback;
			float weeklyRain   = BaseRain + rainFeedback;
			bool  pulse        = rainFeedback > 0.004f;

			for (int r = 0; r < Rows; r++)
			{
				for (int c = 0; c < Cols; c++)
				{
					float h = Humidite.Get(r, c);
					h *= Evaporation;
					h += weeklyRain;
					h += SoilMemory.AtPlot(r, c) * SoilRetention;
					h *= Drainage;
					Humidite.Set(r, c, h);

					if (pulse)
					{
						Microbiome.Add(r, c, rainFeedback * RainMicroPulse);
						float active   = OmActive.AtPlot(r, c);
						float fertPulse = active * 0.002f * rainFeedback * 10f;
						Fertilite.Add(r, c, fertPulse);
					}
				}
			}
		}

		// --- Tick décomposition OM tri-compartiment ---

		public void TickDecomposition()
		{
			for (int r = 0; r < Rows; r++)
			{
				for (int c = 0; c < Cols; c++)
				{
					float micro  = Microbiome.AtPlot(r, c) / 3f;
					float fresh  = OmFresh.Get(r, c);

					// fresh → active
					float f2a = fresh * OmFreshToActive;
					OmFresh.Add(r, c, -f2a);
					OmActive.Add(r, c,  f2a);
					OmFresh.Set(r, c, OmFresh.Get(r, c) * OmFreshCo2Loss);

					float active = OmActive.Get(r, c);

					// active → stable
					float a2s = active * OmActiveToStable;
					OmActive.Add(r, c, -a2s);
					OmStable.Add(r, c,  a2s);

					// active → fertilite (minéralisation)
					float decomp   = OmActiveToFert * (0.5f + micro * 0.5f);
					float released = OmActive.Get(r, c) * decomp;
					OmActive.Add(r, c,   -released);
					Fertilite.Add(r, c,   released);

					OmActive.Set(r, c, OmActive.Get(r, c) * OmActiveCo2Loss);
					Fertilite.Set(r, c, Fertilite.Get(r, c) * LeachingLoss);
				}
			}
		}

		// --- Tick diffusion ---

		public void TickDiffusion()
		{
			Humidite.Diffuse(HumidityInertia);
			Fertilite.Diffuse(FertilityInertia);
			Microbiome.Diffuse(MicrobeInertia);
		}

		// --- Tick lumière ---

		public void TickLight(List<PlantInstance> plants, string saison)
		{
			Lumiere.Compute(plants, saison);
		}

		// --- Nécromasse ---

		private static readonly Dictionary<string, (float f, float a, float s)>
		OmPartition = new()
		{
			{ "feuillage",   (0.80f, 0.20f, 0.00f) },
			{ "herbacee",    (0.60f, 0.30f, 0.10f) },
			{ "racine_sup",  (0.40f, 0.50f, 0.10f) },
			{ "racine_prof", (0.20f, 0.60f, 0.20f) },
			{ "ligneux",     (0.30f, 0.20f, 0.50f) },
		};

		public float AddNecromass(int r, int c, float biomass,
								  bool harvested = false,
								  string originLayer = "herbacee")
		{
			float exportFraction = harvested ? 0.20f : 0f;
			float deposited      = biomass * (1f - exportFraction);

			if (!OmPartition.TryGetValue(originLayer, out var part))
				part = OmPartition["herbacee"];

			OmFresh.Add(r, c,  deposited * part.f);
			OmActive.Add(r, c, deposited * part.a);
			OmStable.Add(r, c, deposited * part.s);
			return deposited;
		}

		// --- Uptake racinaire ---

		private static readonly Dictionary<string, float[]> Uptake = new()
		{
			{ "humidite",   new[] { 0.05f, 0.10f, 0.18f, 0.12f } },
			{ "fertilite",  new[] { 0.02f, 0.05f, 0.08f, 0.05f } },
			{ "microbiome", new[] { 0.00f, 0.01f, 0.02f, 0.01f } },
		};

		public Dictionary<string, float> PlantUptake(
			int r, int c, int stageIndex,
			float shadeMemory = 0f, float droughtMemory = 0f)
		{
			var consumed = new Dictionary<string, float>();
			foreach (var (varName, byStage) in Uptake)
			{
				if (stageIndex >= byStage.Length) continue;
				float amount = byStage[stageIndex];
				if (amount <= 0f) continue;

				if (varName == "humidite")
				{
					float light       = Lumiere.AtPlot(r, c);
					float shadeFactor = 1f - shadeMemory * 0.2f;
					amount *= (0.5f + light * 0.5f) * shadeFactor;
					amount *= Math.Max(0.5f, 1f - droughtMemory * 0.3f);
				}

				GridField field = varName switch
				{
					"humidite"   => Humidite,
					"fertilite"  => Fertilite,
					"microbiome" => Microbiome,
					_            => null
				};
				if (field == null) continue;

				float real = Math.Min(amount, field.AtPlot(r, c));
				if (real > 0f)
				{
					field.Add(r, c, -real);
					consumed[varName] = real;
				}
			}
			return consumed;
		}

		// --- Pathogènes ---

		public void TickPathogen(List<PlantInstance> plants)
		{
			float humAvg     = Humidite.Average();
			float microAvg   = Microbiome.Average() / 3f;
			float distAvg    = Disturbance.Average();
			float omFreshAvg = OmFresh.Average();

			var families = new HashSet<string>();
			foreach (var p in plants)
				if (p.IsAlive) families.Add(p.Data.Family);
			float biodiv  = Math.Min(1f, families.Count / 4f);

			float humRisk  = Math.Max(0f, (humAvg - 0.4f) / 0.6f);
			float monoRisk = Math.Max(0f, 1f - biodiv);
			float omRisk   = Math.Min(1f, omFreshAvg / 3f);

			float infection = humRisk * monoRisk * 0.05f + omRisk * 0.02f;
			PathogenPressure += infection;
			PathogenPressure -= microAvg * 0.04f;
			PathogenPressure -= distAvg  * 0.01f;
			PathogenPressure *= 0.97f;
			PathogenPressure  = Math.Clamp(PathogenPressure, 0f, 1f);
		}

		// --- Probabilité maladie ---

		public float DiseaseProbability(int r, int c, float baseRate = 0.3f)
		{
			float microNorm  = Math.Min(1f, Microbiome.AtPlot(r, c) / 3f);
			float protection = 1f / (1f + MathF.Exp(-6f * (microNorm - 0.5f)));
			float effectiveRate = baseRate * (1f + PathogenPressure * 0.5f);
			return effectiveRate * Math.Max(0.02f, 1f - protection);
		}

		// --- Résumé ---

		public Dictionary<string, float> Summary() => new()
		{
			{ "humidite",    Humidite.Average()       },
			{ "fertilite",   Fertilite.Average()      },
			{ "microbiome",  Microbiome.Average()     },
			{ "om_fresh",    OmFresh.Average()        },
			{ "om_active",   OmActive.Average()       },
			{ "om_stable",   OmStable.Average()       },
			{ "lumiere",     Lumiere.Average()        },
			{ "soil_memory", SoilMemory.Average()     },
			{ "disturbance", Disturbance.Average()    },
			{ "pathogen",    PathogenPressure         },
		};

		public override string ToString()
		{
			var s = Summary();
			return $"EcoFields[{TileId}] " +
				   $"hum={s["humidite"]:F2} fert={s["fertilite"]:F2} " +
				   $"micro={s["microbiome"]:F2} " +
				   $"omF/A/S={s["om_fresh"]:F2}/{s["om_active"]:F2}/{s["om_stable"]:F2} " +
				   $"path={s["pathogen"]:F3}";
		}
	}
}
