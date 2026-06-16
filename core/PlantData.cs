using System.Collections.Generic;

namespace Symbiose
{
	// ---------------------------------------------------------------------------
	// DONNÉES ESPÈCE (statique — partagé entre toutes les instances)
	// ---------------------------------------------------------------------------

	public class PlantData
	{
		public string Name;
		public string Family;         // "Solanaceae", "Fabaceae"...
		public string LifeCycle;      // "annual" | "biennial" | "perennial"
		public string WinterStrategy; // "die" | "dormant" | "evergreen"
		public string Archetype;      // "pioneer" | "nitrogen_fixer" | "grass" | "competitor"
		public float  ReproductionRate = 0.02f;
		public int    SpaceTolerance   = 3;    // semaines avant régression conflit

		public List<GrowthStage> Stages = new();

		// Mémoire physiologique — limites uptake racinaire par stade
		public Dictionary<string, float[]> UptakeByStage = new()
		{
			{ "humidite",  new[] { 0.05f, 0.10f, 0.18f, 0.12f } },
			{ "fertilite", new[] { 0.02f, 0.05f, 0.08f, 0.05f } },
			{ "microbiome",new[] { 0.00f, 0.01f, 0.02f, 0.01f } },
		};
	}
}
