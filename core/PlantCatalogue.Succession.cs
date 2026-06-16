// SYMBIOSE — PlantCatalogue.Succession.cs
// Espèces de SUCCESSION (adventices automatiques via _succession). Partial de
// PlantCatalogue, extrait de Build() au refactor SS⑦. Pur data.

using System.Collections.Generic;

namespace Symbiose
{
	public static partial class PlantCatalogue
	{
		private static void BuildSuccession()
		{
			// --- Bourse-à-pasteur (pioneer) ---
			Register("bourse_pasteur", new SpeciesDefinition
			{
				Category  = PlantCategory.Succession,
				Archetype = "pioneer",
				Data = new PlantData
				{
					Name           = "Bourse-à-pasteur",
					Family         = "Brassicaceae",
					LifeCycle      = "annual",
					WinterStrategy = "die",
					Archetype      = "pioneer",
					ReproductionRate = 0.08f,
					SpaceTolerance   = 5,
					Stages = new List<GrowthStage>
					{
						new() {
							Name = "semis", DurationWeeks = 2, Strate = "sol",
							FoliarOffsets = new() { (0,0) },
							RootOffsets   = new() { (0,0) },
							VigueurCost = 0,
							SpriteName  = "bursa_1_semis",
						},
						new() {
							Name = "adulte", DurationWeeks = 4, Strate = "basse",
							FoliarOffsets = new() { (0,0), (0,1) },
							RootOffsets   = new() { (0,0) },
							VigueurCost = 0,
							SpriteName  = "bursa_2_adulte",
						},
						new() {
							Name = "mature", DurationWeeks = 3, Strate = "basse",
							FoliarOffsets = new() { (0,0), (0,1) },
							RootOffsets   = new() { (0,0) },
							VigueurCost = 0,
							SpriteName  = "bursa_3_mature",
						},
					}
				}
			});

			// --- Minette (nitrogen_fixer) ---
			Register("minette", new SpeciesDefinition
			{
				Category  = PlantCategory.Succession,
				Archetype = "nitrogen_fixer",
				Data = new PlantData
				{
					Name           = "Minette",
					Family         = "Fabaceae",
					LifeCycle      = "perennial",
					WinterStrategy = "dormant",
					Archetype      = "nitrogen_fixer",
					ReproductionRate = 0.05f,
					SpaceTolerance   = 5,
					Stages = new List<GrowthStage>
					{
						new() {
							Name = "semis", DurationWeeks = 2, Strate = "sol",
							FoliarOffsets = new() { (0,0) },
							RootOffsets   = new() { (0,0) },
							VigueurCost = 0,
							SpriteName  = "minette_1_semis",
						},
						new() {
							Name = "adulte", DurationWeeks = 0, Strate = "sol",
							FoliarOffsets = new() { (0,0), (0,1), (1,0) },
							RootOffsets   = new() { (0,0), (1,0) },
							VigueurCost = 0,
							SpriteName  = "minette_2_adulte",
						},
					}
				}
			});

			// --- Pâturin annuel (grass) ---
			Register("paturin", new SpeciesDefinition
			{
				Category  = PlantCategory.Succession,
				Archetype = "grass",
				Data = new PlantData
				{
					Name           = "Pâturin annuel",
					Family         = "Poaceae",
					LifeCycle      = "perennial",
					WinterStrategy = "dormant",
					Archetype      = "grass",
					ReproductionRate = 0.06f,
					SpaceTolerance   = 7,
					Stages = new List<GrowthStage>
					{
						new() {
							Name = "semis", DurationWeeks = 2, Strate = "sol",
							FoliarOffsets = new() { (0,0) },
							RootOffsets   = new() { (0,0) },
							VigueurCost = 0,
							SpriteName  = "paturin_1_semis",
						},
						new() {
							Name = "adulte", DurationWeeks = 0, Strate = "basse",
							FoliarOffsets = new() { (0,0), (0,1), (-1,0) },
							RootOffsets   = new() { (0,0), (0,1), (1,0), (0,-1) },
							VigueurCost = 0,
							SpriteName  = "paturin_2_adulte",
						},
					}
				}
			});

			// --- Pissenlit (competitor) ---
			Register("pissenlit", new SpeciesDefinition
			{
				Category  = PlantCategory.Succession,
				Archetype = "competitor",
				Data = new PlantData
				{
					Name           = "Pissenlit",
					Family         = "Asteraceae",
					LifeCycle      = "perennial",
					WinterStrategy = "dormant",
					Archetype      = "competitor",
					ReproductionRate = 0.04f,
					SpaceTolerance   = 6,
					Stages = new List<GrowthStage>
					{
						new() {
							Name = "semis", DurationWeeks = 2, Strate = "sol",
							FoliarOffsets = new() { (0,0) },
							RootOffsets   = new() { (0,0) },
							VigueurCost = 0,
							SpriteName  = "pissenlit_1_semis",
						},
						new() {
							Name = "rosette", DurationWeeks = 4, Strate = "sol",
							FoliarOffsets = new() { (0,0), (0,1), (0,-1) },
							RootOffsets   = new() { (0,0), (1,0) },
							VigueurCost = 0,
							SpriteName  = "pissenlit_2_rosette",
						},
						new() {
							Name = "adulte", DurationWeeks = 0, Strate = "basse",
							FoliarOffsets = new() { (0,0), (0,1), (0,-1), (-1,0) },
							RootOffsets   = new() { (0,0), (1,0), (2,0) }, // pivot profond
							VigueurCost = 0,
							SpriteName  = "pissenlit_3_adulte",
						},
					}
				}
			});
		}
	}
}
