// SYMBIOSE — PlantCatalogue.Cultivees.cs
// Espèces CULTIVÉES (plantées par le joueur). Partial de PlantCatalogue,
// extrait de Build() au refactor SS⑦. Pur data — voir PlantCatalogue.cs pour
// le registre et les helpers.

using System.Collections.Generic;

namespace Symbiose
{
	public static partial class PlantCatalogue
	{
		private static void BuildCultivated()
		{
			// --- Tomate ---
			Register("tomate", new SpeciesDefinition
			{
				Category = PlantCategory.Cultivated,
				Data = new PlantData
				{
					Name           = "Tomate",
					Family         = "Solanaceae",
					LifeCycle      = "annual",
					WinterStrategy = "die",
					Archetype      = null,
					ReproductionRate = 0.01f,
					SpaceTolerance   = 2,
					Stages = new List<GrowthStage>
					{
						new() {
							Name = "semis", DurationWeeks = 3, Strate = "sol",
							FoliarOffsets = new() { (0,0) },
							RootOffsets   = new() { (0,0) },
							VigueurCost = 1,
							SpriteName  = "tomato_1_semis",
						},
						new() {
							Name = "jeune", DurationWeeks = 4, Strate = "basse",
							FoliarOffsets = new() { (0,0), (0,1) },
							RootOffsets   = new() { (0,0) },
							VigueurCost = 1,
							SpriteName  = "tomato_2_jeune",
						},
						new() {
							Name = "adulte", DurationWeeks = 6, Strate = "moyenne",
							FoliarOffsets = new() { (0,0), (-1,0), (0,1) },
							RootOffsets   = new() { (0,0), (0,-1), (1,0) },
							VigueurCost = 2,
							SpriteName  = "tomato_3_adulte",
						},
						new() {
							Name = "mature", DurationWeeks = 0, Strate = "moyenne",
							FoliarOffsets = new() { (0,0), (-1,0), (0,1), (-1,1) },
							RootOffsets   = new() { (0,0), (0,-1), (1,0), (0,1) },
							VigueurCost = 2,
							SpriteName  = "tomato_4_mature",
						},
					}
				}
			});

			// --- Basilic ---
			Register("basilic", new SpeciesDefinition
			{
				Category = PlantCategory.Cultivated,
				Data = new PlantData
				{
					Name           = "Basilic",
					Family         = "Lamiaceae",
					LifeCycle      = "annual",
					WinterStrategy = "die",
					ReproductionRate = 0.02f,
					SpaceTolerance   = 4,
					Stages = new List<GrowthStage>
					{
						new() {
							Name = "semis", DurationWeeks = 2, Strate = "sol",
							FoliarOffsets = new() { (0,0) },
							RootOffsets   = new() { (0,0) },
							VigueurCost = 1,
							SpriteName  = "basil_1_semis",
						},
						new() {
							Name = "adulte", DurationWeeks = 5, Strate = "basse",
							FoliarOffsets = new() { (0,0), (0,1) },
							RootOffsets   = new() { (0,0) },
							VigueurCost = 1,
							SpriteName  = "basil_2_adulte",
						},
						new() {
							Name = "mature", DurationWeeks = 0, Strate = "basse",
							FoliarOffsets = new() { (0,0), (0,1) },
							RootOffsets   = new() { (0,0) },
							VigueurCost = 1,
							SpriteName  = "basil_3_mature",
						},
					}
				}
			});

			// --- Haricot ---
			Register("haricot", new SpeciesDefinition
			{
				Category = PlantCategory.Cultivated,
				Data = new PlantData
				{
					Name           = "Haricot",
					Family         = "Fabaceae",
					LifeCycle      = "annual",
					WinterStrategy = "die",
					ReproductionRate = 0.03f,
					SpaceTolerance   = 4,
					Stages = new List<GrowthStage>
					{
						new() {
							Name = "semis", DurationWeeks = 2, Strate = "sol",
							FoliarOffsets = new() { (0,0) },
							RootOffsets   = new() { (0,0) },
							VigueurCost = 1,
							SpriteName  = "bean_1_semis",
						},
						new() {
							Name = "jeune", DurationWeeks = 3, Strate = "basse",
							FoliarOffsets = new() { (0,0) },
							RootOffsets   = new() { (0,0) },
							VigueurCost = 1,
							SpriteName  = "bean_2_jeune",
						},
						new() {
							Name = "adulte", DurationWeeks = 5, Strate = "moyenne",
							FoliarOffsets = new() { (0,0), (-1,0) },
							RootOffsets   = new() { (0,0), (1,0) },
							VigueurCost = 1,
							SpriteName  = "bean_3_adulte",
						},
						new() {
							Name = "mature", DurationWeeks = 0, Strate = "moyenne",
							FoliarOffsets = new() { (0,0), (-1,0) },
							RootOffsets   = new() { (0,0), (1,0) },
							VigueurCost = 1,
							SpriteName  = "bean_4_mature",
						},
					}
				}
			});

			// --- Trèfle ---
			Register("trefle", new SpeciesDefinition
			{
				Category = PlantCategory.Cultivated,
				Data = new PlantData
				{
					Name           = "Trèfle",
					Family         = "Fabaceae",
					LifeCycle      = "perennial",
					WinterStrategy = "dormant",
					ReproductionRate = 0.04f,
					SpaceTolerance   = 5,
					Stages = new List<GrowthStage>
					{
						new() {
							Name = "semis", DurationWeeks = 2, Strate = "sol",
							FoliarOffsets = new() { (0,0) },
							RootOffsets   = new() { (0,0) },
							VigueurCost = 0,
							SpriteName  = "clover_1_semis",
						},
						new() {
							Name = "adulte", DurationWeeks = 0, Strate = "sol",
							// S'étale sur 3 plots (96×32 px)
							FoliarOffsets = new() { (0,-1), (0,0), (0,1) },
							RootOffsets   = new() { (0,0), (0,1) },
							VigueurCost = 0,
							SpriteName  = "clover_2_adulte",
						},
					}
				}
			});

			// --- Tournesol ---
			Register("tournesol", new SpeciesDefinition
			{
				Category = PlantCategory.Cultivated,
				Data = new PlantData
				{
					Name           = "Tournesol",
					Family         = "Asteraceae",
					LifeCycle      = "annual",
					WinterStrategy = "die",
					ReproductionRate = 0.03f,
					SpaceTolerance   = 3,
					Stages = new List<GrowthStage>
					{
						new() {
							Name = "semis", DurationWeeks = 2, Strate = "sol",
							FoliarOffsets = new() { (0,0) },
							RootOffsets   = new() { (0,0) },
							VigueurCost = 0,
							SpriteName  = "sunflower_1_semis",
						},
						new() {
							Name = "jeune", DurationWeeks = 3, Strate = "basse",
							FoliarOffsets = new() { (0,0) },
							RootOffsets   = new() { (0,0) },
							VigueurCost = 1,
							SpriteName  = "sunflower_2_jeune",
						},
						new() {
							Name = "adulte", DurationWeeks = 6, Strate = "haute",
							FoliarOffsets = new() { (0,0), (-1,0), (-1,-1) },
							RootOffsets   = new() { (0,0), (1,0) },
							VigueurCost = 2,
							SpriteName  = "sunflower_3_adulte",
						},
						new() {
							Name = "mature", DurationWeeks = 0, Strate = "haute",
							FoliarOffsets = new() { (0,0), (-1,0), (-1,-1), (-1,1) },
							RootOffsets   = new() { (0,0), (1,0), (0,1) },
							VigueurCost = 2,
							SpriteName  = "sunflower_4_mature",
						},
					}
				}
			});

			// --- Poivron ---
			Register("poivron", new SpeciesDefinition
			{
				Category = PlantCategory.Cultivated,
				Data = new PlantData
				{
					Name           = "Poivron",
					Family         = "Solanaceae",
					LifeCycle      = "annual",
					WinterStrategy = "die",
					ReproductionRate = 0.01f,
					SpaceTolerance   = 2,
					Stages = new List<GrowthStage>
					{
						new() {
							Name = "semis", DurationWeeks = 3, Strate = "sol",
							FoliarOffsets = new() { (0,0) },
							RootOffsets   = new() { (0,0) },
							VigueurCost = 1,
							SpriteName  = "pepper_1_semis",
						},
						new() {
							Name = "adulte", DurationWeeks = 6, Strate = "moyenne",
							FoliarOffsets = new() { (0,0), (0,1) },
							RootOffsets   = new() { (0,0) },
							VigueurCost = 2,
							SpriteName  = "pepper_2_adulte",
						},
						new() {
							Name = "mature", DurationWeeks = 0, Strate = "moyenne",
							FoliarOffsets = new() { (0,0), (0,1) },
							RootOffsets   = new() { (0,0), (1,0) },
							VigueurCost = 2,
							SpriteName  = "pepper_3_mature",
						},
					}
				}
			});
		}
	}
}
