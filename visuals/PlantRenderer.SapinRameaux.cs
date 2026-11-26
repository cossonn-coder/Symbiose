// SYMBIOSE — PlantRenderer.SapinRameaux.cs (partial, sprint LISIÈRE & CHARGEMENT ②, décision L4)
// ×8-×32 : les aiguilles du SAPIN en RAMEAUX APLATIS (recette `rameau_aplati`, cuite au ① : un
// rameau et deux ramilles garnis d'aiguilles en peigne, dessous argenté en couche « stomates »).
// Ferme le reste de S2 : jusqu'ici le sapin du jardin posait, à ces paliers, douze aiguilles-
// rubans isolées par brindille (feuille_ruban de 4 cm) — un poteau hérissé de tirets, pas un sapin.
//
// Un rameau cuit fait ~9 cm : on en pose un tous les `RameauAplatiCm` le long de chaque brindille et
// rameau du petit bois (Rameaux.cs, étages du cône compris, Sapin.cs), alternés de part et d'autre
// du brin, orientés par sa direction (lacet cuit le plus proche à l'écran, inclinaison de sa pente).
// Même tri du fond vers l'avant, même densité de feuillage, mêmes tons que les feuilles d'avant.
//
// 📖 Pédagogie (botanique) : chez le sapin, l'unité qui se lit n'est pas l'aiguille mais le rameau
// aplati — les aiguilles se tordent à la base pour se ranger à plat, à la lumière. Poser la
// bonne unité, c'est ce qui fait reconnaître l'arbre, à n'importe quelle distance.
//
// Interrupteur Maj+F11 / SYMBIOSE_SPLATS=0, recette absente : faux → les aiguilles d'avant.
// Déterministe (hash de la clé stable du bois), purement visuel : golden non concerné.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		private const string RecetteRameauAplati = "rameau_aplati";
		private const float RameauAplatiCm = 8f;        // un rameau cuit ~9 cm : léger recouvrement [choix, F5]
		private const float RameauAplatiEcart = 0.45f;  // azimut (rad) de part et d'autre du brin [choix]
		private const float RameauAplatiPas = 5f;       // cm : pas qui donne la direction à l'écran

		private readonly List<(float Prof, Vector2 Ancre, int Inc, int Lacet, int K)> _rameauxAplatis = new();

		/// <summary>Pose les aiguilles d'un port conique en rameaux aplatis (palier ×8 et plus) ;
		/// faux = rien posé (autre espèce, interrupteur, recette absente) → aiguilles d'avant.</summary>
		private bool PoserRameauxAplatis(Vector3 pied, Color[] tons, float density)
		{
			if (!OrganesSplatIci || !PortsConiques.Contains(_structure.SpeciesName)
				|| !SplatPlanches.Vues(RecetteRameauAplati, out int[] incs, out int lacets, out int variantes)) return false;
			_rameauxAplatis.Clear();
			foreach (var e in BoisDuHouppier())
			{
				Vector3 d = e.B - e.A;
				float l = d.Length();
				if (l < 1f) continue;
				d /= l;
				int i = Melange(e.Cle, e.Rang) & 0xFFFFF;   // borné : `k` reste positif
				int n = Mathf.Max(1, Mathf.RoundToInt(l / RameauAplatiCm));
				for (int j = 0; j < n; j++)
				{
					if (Hash01(17, i, j) >= density * GainDensite) continue;
					Vector3 a = e.A.Lerp(e.B, 0.15f + 0.8f * (j + Hash01(547, i, j)) / n) - pied;
					a.Z = Mathf.Max(a.Z - LeafDropCm(a.Z), 0.5f);
					// Alternés de part et d'autre du brin (rotation autour de la verticale).
					float az = (j % 2 == 0 ? 1f : -1f) * RameauAplatiEcart * Mathf.Lerp(0.6f, 1.2f, Hash01(549, i, j));
					var dr = new Vector3(d.X * Mathf.Cos(az) - d.Y * Mathf.Sin(az), d.X * Mathf.Sin(az) + d.Y * Mathf.Cos(az), d.Z);
					float sol = new Vector2(dr.X, dr.Y).Length();
					int inc = PlusProche(incs, Mathf.RadToDeg(Mathf.Atan2(dr.Z, Mathf.Max(sol, 1e-3f))));
					int lacet = LacetEcran(WorldView.WorldToScreenOffset(dr.X * RameauAplatiPas, dr.Y * RameauAplatiPas), lacets);
					float prof = WorldView.WorldToScreenOffset(a.X, a.Y).Y + a.Z * 1e-3f;
					_rameauxAplatis.Add((prof, Iso(a.X, a.Y, a.Z), inc, lacet, i * 41 + j));
				}
			}
			_rameauxAplatis.Sort(static (x, y) => x.Prof.CompareTo(y.Prof));
			bool pose = false;
			foreach (var (_, ancre, inc, lacet, k) in _rameauxAplatis)
				pose |= PoserCouches(RecetteRameauAplati, ancre, inc, lacet, Variante(k, variantes), tons[k % tons.Length], true, 0f);
			return pose;
		}
	}
}
