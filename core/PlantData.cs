using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	// ---------------------------------------------------------------------------
	// STADE DE CROISSANCE
	// ---------------------------------------------------------------------------

	public class GrowthStage
	{
		public string Name;           // "semis", "jeune", "adulte", "mature"
		public int    DurationWeeks;  // 0 = vivace (reste indéfiniment)
		public string Strate;         // "haute","moyenne","basse","sol","grimpante"

		// Empreintes spatiales — (Δrow, Δcol) depuis le plot central
		public List<(int dr, int dc)> FoliarOffsets = new();
		public List<(int dr, int dc)> RootOffsets   = new();

		public int    VigueurCost;
		public string SpriteName;     // clé dans sprites.json ex: "tomato_3_adulte"
	}

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

	// ---------------------------------------------------------------------------
	// INSTANCE DE PLANTE (une par plante vivante sur le terrain)
	// ---------------------------------------------------------------------------

	public class PlantInstance
	{
		public PlantData Data;
		public (int Row, int Col) Position;
		public int   CurrentStage = 0;
		public int   AgeWeeks     = 0;
		public int   Health       = 3;   // 3=sain 2=affaibli 1=malade 0=mort

		// Mémoire physiologique [0–1]
		public float ShadeMemory   = 0f;
		public float DroughtMemory = 0f;
		public float StressMemory  = 0f;

		public bool IsAlive => Health > 0;

		public GrowthStage Stage => Data.Stages[CurrentStage];

		public string SpriteName => Stage.SpriteName;

		// Plots aériens et racinaires depuis la position courante
		public List<(int Row, int Col)> FoliarPlots
		{
			get
			{
				var list = new List<(int, int)>();
				foreach (var (dr, dc) in Stage.FoliarOffsets)
					list.Add((Position.Row + dr, Position.Col + dc));
				return list;
			}
		}

		public List<(int Row, int Col)> RootPlots
		{
			get
			{
				var list = new List<(int, int)>();
				foreach (var (dr, dc) in Stage.RootOffsets)
					list.Add((Position.Row + dr, Position.Col + dc));
				return list;
			}
		}

		public bool AdvanceStage()
		{
			if (CurrentStage < Data.Stages.Count - 1)
			{
				CurrentStage++;
				AgeWeeks = 0;
				return true;
			}
			return false;
		}

		public bool Regress()
		{
			if (CurrentStage > 0)
			{
				CurrentStage--;
				AgeWeeks = 0;
				return false;
			}
			Health = 0;
			return true; // mort
		}

		public override string ToString() =>
			$"{Data.Name}@{Position} [{Stage.Name}] santé={Health}/3";
	}
}
