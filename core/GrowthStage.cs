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
}
