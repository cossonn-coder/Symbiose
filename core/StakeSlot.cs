// SYMBIOSE — StakeSlot.cs
// Tige avec rondelles empilées (max 3 du même type). Extrait de TileData.cs (SS⑦).

using System;
using System.Collections.Generic;

namespace Symbiose
{
	// ---------------------------------------------------------------------------
	// STAKESLOT — tige avec rondelles empilées
	// ---------------------------------------------------------------------------

	public class StakeSlot
	{
		public int          SlotId;
		public List<string> Rondelles = new(); // max 3 du même type

		public string Variable => Rondelles.Count > 0 ? Rondelles[0] : null;
		public int    Count    => Rondelles.Count;
		public bool   IsBonus  => Count == 3;

		public bool Add(string rondelleType)
		{
			if (!RondelleRules.ValidTypes.Contains(rondelleType))
				throw new ArgumentException($"Type inconnu : {rondelleType}");
			if (Count >= 3) return false;
			if (Rondelles.Count > 0 && Rondelles[0] != rondelleType) return false;
			Rondelles.Add(rondelleType);
			return true;
		}

		public string RemoveTop()
		{
			if (Rondelles.Count == 0) return null;
			string top = Rondelles[^1];
			Rondelles.RemoveAt(Rondelles.Count - 1);
			return top;
		}

		public override string ToString() =>
			$"Tige#{SlotId} [{Variable ?? "—"} ×{Count}]";
	}
}
