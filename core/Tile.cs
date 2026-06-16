// SYMBIOSE — Tile.cs
// Tuile complète : plantes, tiges/rondelles, conflits spatiaux, géométrie
// quinconce. Équivalent C# de Tile (models.py). Extrait de TileData.cs (SS⑦).

using System;
using System.Collections.Generic;
using System.Linq;

namespace Symbiose
{
	// ---------------------------------------------------------------------------
	// TILE — tuile complète
	// ---------------------------------------------------------------------------

	public class Tile
	{
		public string TileId;
		public string SoilType;           // "terre" | "argile" | "sable" | "roche"
		public int    GridRows = 6;
		public int    GridCols = 8;       // 48 plots quinconce

		public List<PlantInstance>       Plants    = new();
		public List<StakeSlot>           Stakes    = new();
		public List<ConflictNotification> Conflicts = new();

		public Tile(string tileId, string soilType)
		{
			TileId   = tileId;
			SoilType = soilType;

			// 10 tiges initialisées
			for (int i = 0; i < 10; i++)
				Stakes.Add(new StakeSlot { SlotId = i });
		}

		// --- Rondelles ---

		public int GetRondelleCount(string variable) =>
			Stakes.Where(s => s.Variable == variable).Sum(s => s.Count);

		public List<string> GetBonusVariables() =>
			Stakes.Where(s => s.IsBonus && s.Variable != null)
				  .Select(s => s.Variable).ToList();

		public int AddRondelle(string variable, int amount = 1)
		{
			int cap     = RondelleRules.TypeCap.GetValueOrDefault(variable, 9);
			int current = GetRondelleCount(variable);
			if (current >= cap) return 0;

			int toAdd = Math.Min(amount, cap - current);
			int added = 0;
			foreach (var stake in Stakes)
			{
				if (added >= toAdd) break;
				if (stake.Variable == null || stake.Variable == variable)
					if (stake.Add(variable)) added++;
			}
			return added;
		}

		public int RemoveRondelle(string variable, int amount = 1)
		{
			int removed = 0;
			foreach (var stake in Stakes.AsEnumerable().Reverse())
			{
				if (removed >= amount) break;
				while (stake.Variable == variable && removed < amount)
				{
					stake.RemoveTop();
					removed++;
				}
			}
			return removed;
		}

		public List<string> CheckRondelleIntegrity()
		{
			var corrections = new List<string>();
			foreach (var variable in RondelleRules.ValidTypes)
			{
				int cap     = RondelleRules.TypeCap.GetValueOrDefault(variable, 9);
				int current = GetRondelleCount(variable);
				int excess  = current - cap;
				if (excess > 0)
				{
					RemoveRondelle(variable, excess);
					corrections.Add(
						$"⚠ Intégrité [{TileId}] : {variable} {current}→{cap} (−{excess})"
					);
				}
			}
			return corrections;
		}

		// --- Géométrie quinconce ---

		public bool IsValidPlot(int r, int c) =>
			r >= 0 && r < GridRows && c >= 0 && c < GridCols;

		public List<(int r, int c)> Neighbors(int r, int c)
		{
			(int dr, int dc)[] deltas = (r % 2 == 0)
				? new[] { (-1,-1),(-1,0),(0,-1),(0,1),(1,-1),(1,0) }
				: new[] { (-1, 0),(-1,1),(0,-1),(0,1),(1, 0),(1,1) };

			var result = new List<(int, int)>();
			foreach (var (dr, dc) in deltas)
			{
				int nr = r + dr, nc = c + dc;
				if (IsValidPlot(nr, nc)) result.Add((nr, nc));
			}
			return result;
		}

		public List<(int r, int c)> PlotsWithinRadius(int row, int col, int radius)
		{
			var visited  = new HashSet<(int, int)>();
			var frontier = new HashSet<(int, int)> { (row, col) };

			for (int i = 0; i < radius; i++)
			{
				var next = new HashSet<(int, int)>();
				foreach (var (r, c) in frontier)
					foreach (var nb in Neighbors(r, c))
						if (!visited.Contains(nb)) next.Add(nb);
				visited.UnionWith(frontier);
				frontier = next;
			}
			visited.UnionWith(frontier);
			visited.Remove((row, col));
			return visited.ToList();
		}

		// Conversion coordonnées hex → écran (pour Godot)
		// Retourne position en pixels depuis (0,0) du monde
		public static (float x, float y) HexToScreen(
			int row, int col,
			float tileWidth = 96f, float tileHeight = 48f)
		{
			float x = col * tileWidth * 0.75f;
			float y = row * tileHeight * 0.5f;
			if (col % 2 == 1) y += tileHeight * 0.25f;
			return (x, y);
		}

		// --- Plantes ---

		public PlantInstance AddPlant(PlantData data, int row, int col)
		{
			if (!IsValidPlot(row, col)) return null;
			var instance = new PlantInstance
			{
				Data     = data,
				Position = (row, col)
			};
			Plants.Add(instance);
			return instance;
		}

		public void RemovePlant(PlantInstance instance) =>
			Plants.Remove(instance);

		public List<PlantInstance> AlivePlants =>
			Plants.Where(p => p.IsAlive).ToList();

		// --- Conflits spatiaux ---

		public List<ConflictNotification> DetectConflicts()
		{
			var newConflicts = new List<ConflictNotification>();
			var alive        = AlivePlants;

			foreach (var (layer, getPlots) in new (string, Func<PlantInstance, List<(int,int)>>)[]
			{
				("foliar", p => p.FoliarPlots),
				("root",   p => p.RootPlots),
			})
			{
				// Index plot → plantes qui l'occupent
				var plotMap = new Dictionary<(int,int), List<PlantInstance>>();
				foreach (var p in alive)
					foreach (var (pr, pc) in getPlots(p))
						if (IsValidPlot(pr, pc))
						{
							var key = (pr, pc);
							if (!plotMap.ContainsKey(key))
								plotMap[key] = new List<PlantInstance>();
							plotMap[key].Add(p);
						}

				// Plots avec 2+ plantes
				foreach (var (plot, occupants) in plotMap)
				{
					if (occupants.Count < 2) continue;

					bool already = Conflicts.Any(existing =>
						!existing.Resolved &&
						existing.ConflictType == layer &&
						existing.Plants.Count == occupants.Count &&
						occupants.All(p => existing.Plants.Contains(p)));

					if (!already)
					{
						var nc = new ConflictNotification
						{
							Plants       = new List<PlantInstance>(occupants),
							Plots        = new List<(int,int)> { plot },
							ConflictType = layer,
						};
						newConflicts.Add(nc);
						Conflicts.Add(nc);
					}
				}
			}
			return newConflicts;
		}

		public override string ToString()
		{
			int alive    = AlivePlants.Count;
			int active   = Conflicts.Count(c => !c.Resolved);
			return $"Tuile[{TileId}] sol={SoilType} " +
				   $"plantes={alive} conflits={active}";
		}
	}
}
