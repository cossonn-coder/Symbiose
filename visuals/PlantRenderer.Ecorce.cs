// SYMBIOSE — PlantRenderer.Ecorce.cs (partial, sprint BOIS & ARBRES ② — écorces cuites)
// L'ÉCORCE CUITE plaquée sur le tube de ① : par-dessus l'âme et les flancs orientés (le modelé
// du cylindre, côté soleil), la bande de l'essence (Ecorces.cs) pose ses MARQUES — crevasses,
// plaques, lenticelles — en continu le long de l'axe (v = longueur d'arc en cm, une phase par
// axe au hash pour que deux branches ne montrent pas le même morceau de motif).
//
// ÂGE PAR L'ÉPAISSEUR (conception B2) : rameau lisse < 3,5 cm < branche < 10 cm < tronc à
// rhytidome — dans la continuité d'`EcorcePleineCm` (Arbres.cs : l'écorce est pleine à 5 cm).
// FONDU : autour de chaque seuil, sur ±1 cm (rameau/branche) et ±2,5 cm (branche/tronc)
// d'épaisseur, les deux motifs se superposent puis l'un s'efface — jamais de marche.
// Plante sans essence : écorce « Generique » sur le bois franchement lignifié ; une tige tendre
// n'a pas d'écorce. Le squelette garde son bois mort uni (Tube.cs).
//
// Pinceau (codes de palette) et repli (dessin direct, littéral) passent par le même appel : la
// texture porte les deux moitiés, seul le rectangle lu change.
//
// Déterministe (hash), purement visuel : golden non concerné.

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		private const float SeuilBrancheCm = 3.5f, FonduBrancheCm = 1f;   // rameau → branche
		private const float SeuilTroncCm = 10f, FonduTroncCm = 2.5f;      // branche → tronc
		private const float EcorceMinPx = 4f;      // largeur interne sous laquelle la bande ne se lit plus
		private const float EcorcePoidsMin = 0.25f;   // poids d'un âge en dessous duquel il ne se pose pas
		private const float EcorceLigMin = 0.5f;      // générique : bois franchement lignifié seulement

		// Âge continu d'un point du bois (0 rameau · 1 branche · 2 tronc), fondus compris.
		private static float AgeEcorce(float cm) =>
			Mathf.Clamp((cm - SeuilBrancheCm) / (2f * FonduBrancheCm) + 0.5f, 0f, 1f)
			+ Mathf.Clamp((cm - SeuilTroncCm) / (2f * FonduTroncCm) + 0.5f, 0f, 1f);

		private float[] _agesEcorce = new float[16];

		/// <summary>Pose l'écorce cuite du morceau `m` (déjà projeté : `pts`, `demi`, `nrm`) dans la
		/// palette de `col`. Faux si rien n'est posé (bois trop fin, tige tendre, écorce non cuite) :
		/// l'appelant garde alors les stries de ①.</summary>
		private bool PeindreEcorceCuite(BoisAxes.Morceau m, Vector2[] pts, float[] demi, Vector2[] nrm,
			Color col, float wi, float lig)
		{
			if (wi < EcorceMinPx) return false;
			string essence = RecetteDeLaPlante(out _) ? _structure.SpeciesName
				: lig >= EcorceLigMin ? Ecorces.Generique : null;
			if (essence == null) return false;
			int n = m.LargeurCm.Length;
			if (_agesEcorce.Length < n) _agesEcorce = new float[n];
			for (int k = 0; k < n; k++) _agesEcorce[k] = AgeEcorce(m.LargeurCm[k]);
			bool idx = Indexe, pose = false;
			Color mod = idx ? PaletteIndexee.ModulatePiece(PaletteIndexee.Palette(col)) : TeinteLitterale(col);
			Texture2D tex = null;
			for (int age = Ecorces.Rameau; age <= Ecorces.Tronc; age++)
			{
				if (!Ecorces.Trouver(essence, age, WorldView.CurrentZoom, out var b)) continue;
				int a = age;
				bool Garder(int k) => Mathf.Max(1f - Mathf.Abs(_agesEcorce[k] - a), 1f - Mathf.Abs(_agesEcorce[k + 1] - a)) >= EcorcePoidsMin;
				// Phase par axe ET par individu : deux troncs voisins ne se ressemblent pas.
				float dec = Hash01(183, m.Axe + 31 * GraineIndividu, age) * b.PeriodeCm;
				RubanTexture.PoserBandePeriodique(pts, demi, nrm, m.V, -1f, 1f, b.Tex,
					idx ? b.Codes : b.Litteral, b.PeriodeCm, dec, mod, Garder);
				tex = b.Tex;   // un palier = une texture pour toutes les bandes
				pose = true;
			}
			if (pose) RubanTexture.Envoyer(this, tex);
			return pose;
		}
	}
}
