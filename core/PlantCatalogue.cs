// SYMBIOSE — PlantCatalogue.cs
// Catalogue complet des espèces v1 — types, registre et helpers.
// Équivalent C# de PLANT_CATALOGUE + WEED_CATALOGUE + INDICATOR_SPECIES (models.py)
//
// Trois catégories, une par fichier partial (SS⑦) :
//   Cultivées       — plantées par le joueur        → PlantCatalogue.Cultivees.cs
//   Succession      — adventices via _succession     → PlantCatalogue.Succession.cs
//   Indicatrices    — lisent l'état du sol           → PlantCatalogue.Indicatrices.cs

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
	// CATALOGUE PRINCIPAL — registre + helpers (construction : fichiers partials)
	// ---------------------------------------------------------------------------

	public static partial class PlantCatalogue
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
		// CONSTRUCTION DU CATALOGUE — déléguée aux partials par catégorie
		// -----------------------------------------------------------------------

		private static void Build()
		{
			BuildCultivated();   // PlantCatalogue.Cultivees.cs
			BuildSuccession();   // PlantCatalogue.Succession.cs
			BuildIndicators();   // PlantCatalogue.Indicatrices.cs
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
