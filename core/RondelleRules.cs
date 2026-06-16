// SYMBIOSE — RondelleRules.cs
// Constantes des rondelles (types valides + caps structurels par type).
// Extrait de TileData.cs au refactor SS⑦ — utilisé par StakeSlot et Tile.

using System.Collections.Generic;

namespace Symbiose
{
	// ---------------------------------------------------------------------------
	// CONSTANTES RONDELLES
	// ---------------------------------------------------------------------------

	public static class RondelleRules
	{
		public static readonly HashSet<string> ValidTypes = new()
		{
			"fertilite", "humidite", "lombric",
			"maladie", "pollinisateur", "paillage"
		};

		// Cap structurel par type — maladie volontairement limité à 6
		public static readonly Dictionary<string, int> TypeCap = new()
		{
			{ "maladie",       6 },
			{ "pollinisateur", 9 },
			{ "paillage",      9 },
			{ "fertilite",     9 },
			{ "humidite",      9 },
			{ "lombric",       9 },
		};
	}
}
