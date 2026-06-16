// SYMBIOSE — PlantCatalogue.Indicatrices.cs
// Espèces INDICATRICES (apparaissent sur conditions de sol, via UnlockCondition).
// Partial de PlantCatalogue, extrait de Build() au refactor SS⑦. Pur data.

using System.Collections.Generic;

namespace Symbiose
{
	public static partial class PlantCatalogue
	{
		private static void BuildIndicators()
		{
			// --- Ortie — sol riche en azote ---
			Register("ortie", new SpeciesDefinition
			{
				Category  = PlantCategory.Indicator,
				Archetype = "competitor",
				UnlockCondition = new UnlockCondition
				{
					Description = "Le sol s'est enrichi en azote. Une plante vigoureuse " +
								  "pourrait en profiter.",
					Check = eco =>
						eco.Fertilite.Average()  > 2.5f &&
						eco.OmActive.Average()   > 1.2f,
				},
				Data = new PlantData
				{
					Name           = "Ortie",
					Family         = "Urticaceae",
					LifeCycle      = "perennial",
					WinterStrategy = "dormant",
					Archetype      = "competitor",
					ReproductionRate = 0.04f,
					SpaceTolerance   = 4,
					Stages = new List<GrowthStage>
					{
						new() {
							Name = "semis", DurationWeeks = 3, Strate = "sol",
							FoliarOffsets = new() { (0,0) },
							RootOffsets   = new() { (0,0) },
							VigueurCost = 0,
							SpriteName  = "ortie_1_semis",
						},
						new() {
							Name = "adulte", DurationWeeks = 0, Strate = "moyenne",
							FoliarOffsets = new() { (0,0), (-1,0), (-1,1) },
							RootOffsets   = new() { (0,0), (1,0), (0,1) },
							VigueurCost = 0,
							SpriteName  = "ortie_2_adulte",
						},
					}
				}
			});

			// --- Prêle — sol compacté et humide ---
			Register("prele", new SpeciesDefinition
			{
				Category  = PlantCategory.Indicator,
				Archetype = "pioneer",
				UnlockCondition = new UnlockCondition
				{
					Description = "Le sol retient l'eau en profondeur. " +
								  "Une plante ancienne pourrait s'y installer.",
					Check = eco =>
						eco.Humidite.Average()       > 0.7f &&
						eco.SoilMemoryDeep.Average() > 0.4f,
				},
				Data = new PlantData
				{
					Name           = "Prêle",
					Family         = "Equisetaceae",
					LifeCycle      = "perennial",
					WinterStrategy = "dormant",
					Archetype      = "pioneer",
					ReproductionRate = 0.02f,
					SpaceTolerance   = 6,
					Stages = new List<GrowthStage>
					{
						new() {
							Name = "semis", DurationWeeks = 4, Strate = "sol",
							FoliarOffsets = new() { (0,0) },
							RootOffsets   = new() { (0,0) },
							VigueurCost = 0,
							SpriteName  = "prele_1_semis",
						},
						new() {
							Name = "adulte", DurationWeeks = 0, Strate = "moyenne",
							FoliarOffsets = new() { (0,0), (-1,0) },
							RootOffsets   = new() { (0,0), (1,0), (2,0) },
							VigueurCost = 0,
							SpriteName  = "prele_2_adulte",
						},
					}
				}
			});

			// --- Plantain — sol perturbé et piétiné ---
			Register("plantain", new SpeciesDefinition
			{
				Category  = PlantCategory.Indicator,
				Archetype = "pioneer",
				UnlockCondition = new UnlockCondition
				{
					Description = "Le sol a été fortement perturbé. " +
								  "Une plante résistante au piétinement s'y adapte.",
					Check = eco =>
						eco.Disturbance.Average() > 0.4f,
				},
				Data = new PlantData
				{
					Name           = "Plantain",
					Family         = "Plantaginaceae",
					LifeCycle      = "perennial",
					WinterStrategy = "dormant",
					Archetype      = "pioneer",
					ReproductionRate = 0.03f,
					SpaceTolerance   = 6,
					Stages = new List<GrowthStage>
					{
						new() {
							Name = "semis", DurationWeeks = 2, Strate = "sol",
							FoliarOffsets = new() { (0,0) },
							RootOffsets   = new() { (0,0) },
							VigueurCost = 0,
							SpriteName  = "plantain_1_semis",
						},
						new() {
							Name = "adulte", DurationWeeks = 0, Strate = "sol",
							FoliarOffsets = new() { (0,0), (0,1), (0,-1) },
							RootOffsets   = new() { (0,0), (1,0) },
							VigueurCost = 0,
							SpriteName  = "plantain_2_adulte",
						},
					}
				}
			});

			// --- Molène — pression pathogène élevée ---
			Register("molene", new SpeciesDefinition
			{
				Category  = PlantCategory.Indicator,
				Archetype = "pioneer",
				UnlockCondition = new UnlockCondition
				{
					Description = "Une pression pathogène persistante fragilise le jardin. " +
								  "Une plante médicinale ancienne y trouve sa place.",
					Check = eco =>
						eco.PathogenPressure > 0.6f,
				},
				Data = new PlantData
				{
					Name           = "Molène",
					Family         = "Scrophulariaceae",
					LifeCycle      = "biennial",
					WinterStrategy = "dormant",
					Archetype      = "pioneer",
					ReproductionRate = 0.03f,
					SpaceTolerance   = 5,
					Stages = new List<GrowthStage>
					{
						new() {
							Name = "semis", DurationWeeks = 3, Strate = "sol",
							FoliarOffsets = new() { (0,0) },
							RootOffsets   = new() { (0,0) },
							VigueurCost = 0,
							SpriteName  = "molene_1_semis",
						},
						new() {
							Name = "adulte", DurationWeeks = 0, Strate = "haute",
							FoliarOffsets = new() { (0,0), (-1,0), (-2,0) },
							RootOffsets   = new() { (0,0) },
							VigueurCost = 0,
							SpriteName  = "molene_2_adulte",
						},
					}
				}
			});
		}
	}
}
