// SYMBIOSE — EcoFields.cs
// Conteneur complet des champs écologiques d'une tuile (hydrologie, OM
// tri-compartiment, lumière, pathogènes, uptake). Extrait de GridField.cs (SS⑦).

using System;
using System.Collections.Generic;

namespace Symbiose
{
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
