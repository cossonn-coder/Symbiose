// SYMBIOSE — ConflictNotification.cs
// Conflit spatial entre plantes (foliaire ou racinaire). Extrait de TileData.cs (SS⑦).

using System.Collections.Generic;
using System.Linq;

namespace Symbiose
{
	// ---------------------------------------------------------------------------
	// CONFLICT NOTIFICATION — conflit spatial entre plantes
	// ---------------------------------------------------------------------------

	public class ConflictNotification
	{
		public List<PlantInstance> Plants;
		public List<(int r, int c)> Plots;
		public string ConflictType;   // "foliar" | "root"
		public int    WeeksActive = 0;
		public bool   Resolved    = false;

		public void Tick()
		{
			if (!Resolved) WeeksActive++;
		}

		// La plante la plus jeune (AgeWeeks le plus bas) perd
		public PlantInstance Loser() =>
			Plants.OrderBy(p => p.AgeWeeks).First();

		public override string ToString()
		{
			string noms = string.Join(" vs ", Plants.Select(p => p.Data.Name));
			return $"CONFLIT [{ConflictType}] {noms} semaines={WeeksActive}";
		}
	}
}
