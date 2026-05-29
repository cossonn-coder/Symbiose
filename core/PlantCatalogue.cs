// SYMBIOSE — PlantCatalogue.cs
// Catalogue complet des espèces v1.
// Équivalent C# de PLANT_CATALOGUE + WEED_CATALOGUE + INDICATOR_SPECIES (models.py)
//
// Trois catégories :
//   Cultivées       — plantées par le joueur
//   Succession      — adventices apparaissant via _succession
//   Indicatrices    — lisent l'état du sol, apparaissent sur conditions écologiques

using System;
using System.Collections.Generic;

namespace Symbiose
{
	// ---------------------------------------------------------------------------
	// CATÉGORIE D'ESPÈCE
	// ---------------------------------------------------------------------------

	public enum PlantCategory
	{
		Cultivated,   // plantée par le joueur
		Succession,   // adventice de succession automatique
		Indicator,    // plante indicatrice — lit l'état du sol
	}

	// ---------------------------------------------------------------------------
	// CONDITION DE DÉBLOCAGE (shop + indicatrices)
	// ---------------------------------------------------------------------------

	public class UnlockCondition
	{
		public string Description;  // texte narratif affiché au joueur
		public Func<EcoFields, bool> Check;  // lambda sur EcoFields
	}

	// ---------------------------------------------------------------------------
	// DÉFINITION COMPLÈTE D'UNE ESPÈCE
	// ---------------------------------------------------------------------------

	public class SpeciesDefinition
	{
		public PlantData      Data;
		public PlantCategory  Category;
		public string         Archetype;       // pour WEED_CATALOGUE
		public UnlockCondition UnlockCondition; // null = disponible dès le départ
	}

	// ---------------------------------------------------------------------------
	// CATALOGUE PRINCIPAL
	// ---------------------------------------------------------------------------

	public static class PlantCatalogue
	{
		// Accès par clé string (ex: "tomate", "ortie")
		public static readonly Dictionary<string, SpeciesDefinition> All = new();

		// Sous-catalogues rapides
		public static readonly Dictionary<string, PlantData> Cultivated   = new();
		public static readonly Dictionary<string, PlantData> WeedCatalogue = new();
		public static readonly Dictionary<string, SpeciesDefinition> Indicators = new();

		// Archétype → espèce de succession
		public static readonly Dictionary<string, PlantData> ByArchetype = new();

		static PlantCatalogue() { Build(); }

		// -----------------------------------------------------------------------
		// REGISTRATION
		// -----------------------------------------------------------------------

		private static void Register(string key, SpeciesDefinition def)
		{
			All[key] = def;

			switch (def.Category)
			{
				case PlantCategory.Cultivated:
					Cultivated[key] = def.Data;
					break;

				case PlantCategory.Succession:
					WeedCatalogue[key] = def.Data;
					if (def.Archetype != null)
						ByArchetype[def.Archetype] = def.Data;
					break;

				case PlantCategory.Indicator:
					Indicators[key] = def;
					break;
			}
		}

		// -----------------------------------------------------------------------
		// CONSTRUCTION DU CATALOGUE
		// -----------------------------------------------------------------------

		private static void Build()
		{
			// ===================================================================
			// CULTIVÉES
			// ===================================================================

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

			// ===================================================================
			// SUCCESSION — adventices automatiques
			// ===================================================================

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

			// ===================================================================
			// INDICATRICES — apparaissent sur conditions de sol
			// ===================================================================

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

		// -----------------------------------------------------------------------
		// HELPERS
		// -----------------------------------------------------------------------

		/// <summary>
		/// Retourne les indicatrices dont les conditions sont remplies
		/// sur le terrain courant. Appelé en fin de run pour alimenter le shop.
		/// </summary>
		public static List<string> EvaluateIndicators(EcoFields eco)
		{
			var available = new List<string>();
			foreach (var (key, def) in Indicators)
			{
				if (def.UnlockCondition?.Check(eco) == true)
					available.Add(key);
			}
			return available;
		}

		/// <summary>
		/// Retourne la PlantData depuis une clé, ou null si inconnue.
		/// </summary>
		public static PlantData Get(string key) =>
			All.TryGetValue(key, out var def) ? def.Data : null;

		/// <summary>
		/// Retourne la PlantData de succession pour un archétype donné.
		/// </summary>
		public static PlantData GetByArchetype(string archetype) =>
			ByArchetype.TryGetValue(archetype, out var data) ? data : null;
	}
}
