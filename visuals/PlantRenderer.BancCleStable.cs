// SYMBIOSE — PlantRenderer.BancCleStable.cs (partial, sprint HOUPPIER ④)
// Le côté PLANTE du banc de la clé stable (WorldView.BancCleStable.cs) : la liste de ce que le
// feuillage pose au palier courant, en passant par le code du vrai dessin. Banc VM seulement.

using Godot;
using System.Collections.Generic;
using System.Globalization;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		internal int NombreSegments => _structure?.Segments.Count ?? 0;

		/// <summary>Milieu du segment `i`, en canvas : là où cliquer pour le tailler.</summary>
		internal Vector2 MilieuSegmentCanvas(int i)
		{
			var s = _structure.Segments[i];
			Vector3 c = _structure.ColletCm, m = s.Base + s.Dir * (s.LengthCm * 0.5f);
			return ToGlobal(Iso(m.X - c.X, m.Y - c.Y, m.Z));
		}

		/// <summary>Le segment du milieu d'une branche : assez de bois au-dessus pour que la coupe
		/// retire du feuillage, sans toucher le tronc.</summary>
		internal int SegmentACouper()
		{
			var segs = _structure.Segments;
			for (int i = segs.Count / 2; i < segs.Count; i++)
				if (!segs[i].IsApex && IsLeafy(segs[i])) return i;
			return segs.Count - 1;
		}

		/// <summary>Chaque élément de feuillage du palier courant, sous forme de texte : position
		/// à 1/100 px, taille, variante. Deux relevés se comparent comme deux ensembles.</summary>
		internal HashSet<string> EmpreinteFeuillage()
		{
			var e = new HashSet<string>();
			float z = WorldView.CurrentZoom;
			string P(Vector2 v) => string.Create(CultureInfo.InvariantCulture, $"{v.X:F2},{v.Y:F2}");
			if (LianeDeLaPlante is { } l)
			{
				_lotPrairie ??= new LotTriangles();
				_lotPrairie.Vider();
				_axesTige.Clear();
				_feuillesPort.Clear();
				CollecterLiane(l, _structure.ColletCm, TeintePrairie());
				foreach (var (_, f) in _feuillesPort)
					e.Add($"{P(f.Org)} {f.U.X:F3} {f.Long:F2} {f.K}");
			}
			else if (z < PaliersHautsMinZoom)
				foreach (var t in PlacerTouffes(z, TailleTouffe(z)))
					e.Add($"{P(t.Pos)} {t.Taille} {t.Variante}");
			else
			{
				Vector3 collet = _structure.ColletCm;
				float density = _structure.DensiteVisible;
				foreach (var s in _structure.Segments)
				{
					if (!IsLeafy(s)) continue;
					int i = CleSegment(s), n = NbFeuilles(s);
					Vector2 perp = PerpFeuilles(s);
					for (int j = 0; j < n; j++)
						if (Hash01(17, i, j) < density)
							e.Add(P(PlaceFeuille(s, i, j, n, perp, collet, LeafGrowthFactor(s), out _, out _)));
				}
			}
			return e;
		}
	}
}
