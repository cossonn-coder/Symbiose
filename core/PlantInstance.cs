using System.Collections.Generic;

namespace Symbiose
{
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
